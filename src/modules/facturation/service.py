"""Service Facturation — validation, comptabilisation, numérotation."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from .models import DocumentStatus, DocumentType, Invoice, InvoiceLine

ZERO = Decimal("0.00")


def _next_invoice_number(session: Session, company_id: str, doc_type: str) -> str:
    from sqlalchemy import func
    prefix = {"FACTURE": "FA", "AVOIR": "AV", "DEVIS": "DV", "BON_COMMANDE": "BC"}.get(doc_type, "DO")
    year = date.today().year
    count = (
        session.query(func.count(Invoice.id))
        .filter(
            Invoice.company_id == company_id,
            Invoice.document_type == doc_type,
            Invoice.number.like(f"{prefix}{year}%"),
        )
        .scalar()
    ) or 0
    return f"{prefix}{year}{count + 1:05d}"


def recalculate_totals(invoice: Invoice) -> None:
    """Recalcule subtotal_ht, total_tva, total_ttc depuis les lignes."""
    invoice.subtotal_ht = sum(l.line_ht for l in invoice.lines) if invoice.lines else ZERO
    invoice.total_tva = sum(l.line_tva for l in invoice.lines) if invoice.lines else ZERO
    invoice.total_ttc = invoice.subtotal_ht + invoice.total_tva


def validate_invoice(session: Session, invoice: Invoice) -> Invoice:
    """
    Valide une facture brouillon :
    1. Attribue un numéro séquentiel.
    2. Recalcule les totaux.
    3. Comptabilise (crée l'écriture journal).
    4. Passe le statut à ENVOYE.
    """
    if invoice.status != DocumentStatus.BROUILLON:
        raise ValueError(f"Impossible de valider une facture en statut {invoice.status}.")

    recalculate_totals(invoice)
    invoice.number = _next_invoice_number(session, invoice.company_id, invoice.document_type)

    if invoice.document_type in (DocumentType.FACTURE, DocumentType.AVOIR):
        _post_accounting_entry(session, invoice)

    invoice.status = DocumentStatus.ENVOYE
    session.flush()
    return invoice


def _post_accounting_entry(session: Session, invoice: Invoice) -> None:
    """Crée l'écriture comptable liée à la facture."""
    from src.core.engine.ledger import EntryInput, LineInput, post_entry
    from src.core.models.journal import Journal, JournalType

    journal = session.query(Journal).filter(
        Journal.company_id == invoice.company_id,
        Journal.journal_type == JournalType.VENTES,
    ).first()
    if not journal:
        return

    from src.core.models.fiscal_year import FiscalYear
    fy = session.query(FiscalYear).filter(
        FiscalYear.company_id == invoice.company_id,
        FiscalYear.start_date <= invoice.issue_date,
        FiscalYear.end_date >= invoice.issue_date,
    ).first()
    if not fy:
        return

    is_avoir = invoice.document_type == DocumentType.AVOIR
    sign = Decimal("-1") if is_avoir else Decimal("1")

    lines: list[LineInput] = []

    # Débit 411 — Client
    lines.append(LineInput(
        account_code="411",
        label=f"{invoice.number} — {invoice.customer_name}",
        debit=invoice.total_ttc * sign if sign > 0 else ZERO,
        credit=abs(invoice.total_ttc * sign) if sign < 0 else ZERO,
    ))

    # Crédit par ligne de produit
    by_account: dict[str, Decimal] = {}
    for line in invoice.lines:
        by_account[line.account_code] = by_account.get(line.account_code, ZERO) + line.line_ht

    for acc_code, ht in by_account.items():
        lines.append(LineInput(
            account_code=acc_code,
            label=f"{invoice.number} — vente HT",
            debit=abs(ht * sign) if sign < 0 else ZERO,
            credit=ht * sign if sign > 0 else ZERO,
        ))

    # TVA collectée par taux
    by_vat: dict[str, Decimal] = {}
    for line in invoice.lines:
        by_vat[line.vat_code] = by_vat.get(line.vat_code, ZERO) + line.line_tva

    for vat_code, tva in by_vat.items():
        if tva == ZERO:
            continue
        lines.append(LineInput(
            account_code="44571",
            label=f"TVA {invoice.number}",
            debit=abs(tva * sign) if sign < 0 else ZERO,
            credit=tva * sign if sign > 0 else ZERO,
            vat_code=vat_code,
        ))

    entry = post_entry(session, EntryInput(
        company_id=invoice.company_id,
        journal_id=journal.id,
        fiscal_year_id=fy.id,
        entry_date=invoice.issue_date,
        label=f"{invoice.number} — {invoice.customer_name}",
        reference=invoice.number,
        lines=lines,
    ))
    invoice.journal_entry_id = entry.id


def create_credit_note(session: Session, invoice: Invoice) -> Invoice:
    """Crée un avoir à partir d'une facture validée (annulation totale)."""
    if invoice.document_type != DocumentType.FACTURE:
        raise ValueError("Un avoir ne peut être créé que depuis une facture.")

    avoir = Invoice(
        company_id=invoice.company_id,
        document_type=DocumentType.AVOIR,
        status=DocumentStatus.BROUILLON,
        customer_name=invoice.customer_name,
        customer_address=invoice.customer_address,
        issue_date=date.today(),
        due_date=date.today(),
        currency=invoice.currency,
        credited_invoice_id=invoice.id,
        notes=f"Avoir sur facture {invoice.number}",
    )

    for orig_line in invoice.lines:
        avoir.lines.append(InvoiceLine(
            sequence=orig_line.sequence,
            description=orig_line.description,
            quantity=orig_line.quantity,
            unit_price_ht=orig_line.unit_price_ht,
            discount_pct=orig_line.discount_pct,
            vat_rate=orig_line.vat_rate,
            vat_code=orig_line.vat_code,
            account_code=orig_line.account_code,
        ))

    session.add(avoir)
    session.flush()
    return validate_invoice(session, avoir)


def get_aged_balance(session: Session, company_id: str) -> list[dict]:
    """
    Balance âgée clients : créances par tranche d'ancienneté.
    Tranches : < 30j, 30-60j, 60-90j, > 90j.
    """
    from datetime import date as d
    today = d.today()

    invoices = session.query(Invoice).filter(
        Invoice.company_id == company_id,
        Invoice.document_type == DocumentType.FACTURE,
        Invoice.status.in_([DocumentStatus.ENVOYE, DocumentStatus.PARTIELLEMENT_PAYE, DocumentStatus.EN_RETARD]),
    ).all()

    buckets = {"current": ZERO, "30": ZERO, "60": ZERO, "90": ZERO, "over_90": ZERO}

    for inv in invoices:
        balance = inv.balance_due
        if balance <= ZERO:
            continue
        if not inv.due_date or inv.due_date >= today:
            buckets["current"] += balance
        else:
            days = (today - inv.due_date).days
            if days <= 30:
                buckets["30"] += balance
            elif days <= 60:
                buckets["60"] += balance
            elif days <= 90:
                buckets["90"] += balance
            else:
                buckets["over_90"] += balance

    return [{"bucket": k, "amount": v} for k, v in buckets.items()]
