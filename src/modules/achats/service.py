"""Services Achats — validation, approbation, comptabilisation."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.modules.achats.models import (
    PaymentStatus,
    SupplierInvoice,
    SupplierInvoiceStatus,
    SupplierPayment,
    PurchaseOrder,
    PurchaseOrderStatus,
)


def approve_supplier_invoice(invoice: SupplierInvoice, approver_user_id: str, db: Session) -> SupplierInvoice:
    """Valide une facture fournisseur (workflow approbation)."""
    if invoice.status not in (
        SupplierInvoiceStatus.RECUE,
        SupplierInvoiceStatus.EN_ATTENTE_VALIDATION,
    ):
        raise ValueError(f"Impossible de valider une facture au statut {invoice.status}")

    invoice.status = SupplierInvoiceStatus.EN_ATTENTE_PAIEMENT
    invoice.approved_by = approver_user_id
    invoice.approved_at = date.today()
    db.commit()
    return invoice


def reject_supplier_invoice(invoice: SupplierInvoice, db: Session) -> SupplierInvoice:
    if invoice.status not in (
        SupplierInvoiceStatus.RECUE,
        SupplierInvoiceStatus.EN_ATTENTE_VALIDATION,
    ):
        raise ValueError(f"Impossible de refuser une facture au statut {invoice.status}")
    invoice.status = SupplierInvoiceStatus.REFUSEE
    db.commit()
    return invoice


def record_payment(
    invoice: SupplierInvoice,
    amount: Decimal,
    payment_date: date,
    payment_method: str,
    reference: str | None,
    db: Session,
) -> SupplierPayment:
    """Enregistre un paiement fournisseur et met à jour le statut de la facture."""
    if invoice.status not in (
        SupplierInvoiceStatus.EN_ATTENTE_PAIEMENT,
        SupplierInvoiceStatus.PARTIELLEMENT_PAYEE,
        SupplierInvoiceStatus.VALIDEE,
    ):
        raise ValueError(f"Facture non payable au statut {invoice.status}")

    if amount <= 0:
        raise ValueError("Le montant du paiement doit être positif")

    if amount > invoice.balance_due:
        raise ValueError(f"Montant {amount} supérieur au solde restant {invoice.balance_due}")

    payment = SupplierPayment(
        id=str(uuid.uuid4()),
        invoice_id=invoice.id,
        amount=amount,
        payment_date=payment_date,
        payment_method=payment_method,
        reference=reference,
        status=PaymentStatus.EXECUTE,
    )
    db.add(payment)

    invoice.amount_paid += amount
    if invoice.amount_paid >= invoice.total_ttc:
        invoice.status = SupplierInvoiceStatus.PAYEE
    else:
        invoice.status = SupplierInvoiceStatus.PARTIELLEMENT_PAYEE

    db.commit()
    return payment


def confirm_purchase_order(order: PurchaseOrder, db: Session) -> PurchaseOrder:
    """Confirme un bon de commande (envoyé au fournisseur)."""
    if order.status != PurchaseOrderStatus.BROUILLON:
        raise ValueError(f"Commande déjà au statut {order.status}")
    order.status = PurchaseOrderStatus.ENVOYE
    db.commit()
    return order


def compute_invoice_totals(invoice: SupplierInvoice) -> tuple[Decimal, Decimal, Decimal]:
    """Recalcule subtotal_ht, total_tva, total_ttc depuis les lignes."""
    ht = sum(ln.line_ht for ln in invoice.lines)
    tva = sum(ln.line_tva for ln in invoice.lines)
    return ht, tva, ht + tva


def get_aged_payables(company_id: str, as_of: date, db: Session) -> list[dict]:
    """Balance âgée fournisseurs."""
    invoices = (
        db.query(SupplierInvoice)
        .filter(
            SupplierInvoice.company_id == company_id,
            SupplierInvoice.status.in_([
                SupplierInvoiceStatus.EN_ATTENTE_PAIEMENT,
                SupplierInvoiceStatus.PARTIELLEMENT_PAYEE,
            ]),
        )
        .all()
    )

    buckets: dict[str, dict] = {}
    for inv in invoices:
        sid = inv.supplier_id
        if sid not in buckets:
            buckets[sid] = {"supplier_id": sid, "current": Decimal(0),
                            "30": Decimal(0), "60": Decimal(0),
                            "90": Decimal(0), "over_90": Decimal(0), "total": Decimal(0)}
        bal = inv.balance_due
        if inv.due_date is None or inv.due_date >= as_of:
            buckets[sid]["current"] += bal
        else:
            days_late = (as_of - inv.due_date).days
            if days_late <= 30:
                buckets[sid]["30"] += bal
            elif days_late <= 60:
                buckets[sid]["60"] += bal
            elif days_late <= 90:
                buckets[sid]["90"] += bal
            else:
                buckets[sid]["over_90"] += bal
        buckets[sid]["total"] += bal

    return list(buckets.values())
