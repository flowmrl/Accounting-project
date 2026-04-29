"""Facturation — devis, factures, avoirs, relances, balance âgée, Factur-X."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.core.models.company import Company
from src.db.session import get_session
from src.modules.facturation.models import DocumentStatus as InvoiceStatus
from src.modules.facturation.models import DocumentType as InvoiceType
from src.modules.facturation.models import Invoice, InvoiceLine
from src.modules.facturation.service import create_credit_note, get_aged_balance, validate_invoice

router = APIRouter(prefix="/invoices", tags=["Facturation"])


class InvoiceLineIn(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal
    vat_rate: Decimal = Decimal("20.00")
    account_code: str = "706"


class InvoiceCreate(BaseModel):
    invoice_type: InvoiceType = InvoiceType.FACTURE
    customer_id: str
    issue_date: date
    due_date: date
    fiscal_year_id: str
    currency: str = "EUR"
    lines: list[InvoiceLineIn]
    notes: str | None = None


class InvoiceLineOut(BaseModel):
    id: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    vat_rate: Decimal
    line_ht: Decimal
    line_tva: Decimal
    line_ttc: Decimal


class InvoiceOut(BaseModel):
    id: str
    number: str | None
    invoice_type: str
    status: str
    customer_id: str
    issue_date: date
    due_date: date
    total_ht: Decimal
    total_tva: Decimal
    total_ttc: Decimal
    currency: str
    lines: list[InvoiceLineOut] = []

    class Config:
        from_attributes = True


class AgedBalanceOut(BaseModel):
    customer_id: str
    current: Decimal
    days_30: Decimal
    days_60: Decimal
    days_90: Decimal
    over_90: Decimal
    total: Decimal


@router.post("/", response_model=InvoiceOut, status_code=201)
def create_invoice(
    body: InvoiceCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Invoice:
    company_id = current_user["company_id"]
    invoice = Invoice(
        id=str(uuid.uuid4()),
        company_id=company_id,
        invoice_type=body.invoice_type,
        customer_id=body.customer_id,
        issue_date=body.issue_date,
        due_date=body.due_date,
        fiscal_year_id=body.fiscal_year_id,
        currency=body.currency,
        status=InvoiceStatus.BROUILLON,
        notes=body.notes,
    )
    for l in body.lines:
        invoice.lines.append(InvoiceLine(
            id=str(uuid.uuid4()),
            invoice_id=invoice.id,
            description=l.description,
            quantity=l.quantity,
            unit_price=l.unit_price,
            vat_rate=l.vat_rate,
            account_code=l.account_code,
        ))
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/validate", response_model=InvoiceOut)
def validate(
    invoice_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Invoice:
    company_id = current_user["company_id"]
    invoice = db.query(Invoice).filter_by(id=invoice_id, company_id=company_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    try:
        invoice = validate_invoice(invoice, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return invoice


@router.post("/{invoice_id}/credit-note", response_model=InvoiceOut, status_code=201)
def credit_note(
    invoice_id: str,
    reason: str = Query("Avoir sur facture"),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Invoice:
    company_id = current_user["company_id"]
    invoice = db.query(Invoice).filter_by(id=invoice_id, company_id=company_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    avoir = create_credit_note(invoice, reason, db)
    return avoir


@router.get("/aged-balance", response_model=list[AgedBalanceOut])
def aged_balance(
    as_of: date = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[AgedBalanceOut]:
    company_id = current_user["company_id"]
    rows = get_aged_balance(company_id, as_of, db)
    return [
        AgedBalanceOut(
            customer_id=r["customer_id"],
            current=r["current"],
            days_30=r["30"],
            days_60=r["60"],
            days_90=r["90"],
            over_90=r["over_90"],
            total=r["total"],
        )
        for r in rows
    ]


@router.get(
    "/{invoice_id}/facturx",
    summary="Télécharger la facture au format Factur-X (PDF/A-3 + XML EN 16931)",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def download_facturx(
    invoice_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Génère et retourne le fichier PDF/A-3 Factur-X pour une facture validée."""
    company_id = current_user["company_id"]

    invoice = db.query(Invoice).filter_by(id=invoice_id, company_id=company_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    if invoice.document_type not in (InvoiceType.FACTURE, InvoiceType.AVOIR):
        raise HTTPException(status_code=422, detail="Factur-X disponible uniquement pour les factures et avoirs")

    if invoice.status == InvoiceStatus.BROUILLON:
        raise HTTPException(status_code=422, detail="Validez la facture avant de générer le Factur-X")

    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Société introuvable")

    lines = [
        {
            "description": ln.description,
            "quantity": ln.quantity,
            "unit_price_ht": ln.unit_price_ht,
            "vat_rate": ln.vat_rate,
            "line_ht": ln.line_ht,
            "line_tva": ln.line_tva,
            "line_ttc": ln.line_ttc,
            "unit_code": "C62",
        }
        for ln in invoice.lines
    ]

    from src.modules.facturation.facturx_pdf import generate_facturx

    try:
        pdf_bytes = generate_facturx(
            invoice_number=invoice.number or invoice_id[:8],
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            seller_name=company.name,
            seller_address=company.address or "",
            seller_city=company.city or "",
            seller_postal=company.zip_code or "",
            seller_siret=company.siret or "",
            seller_tva_intracom=company.tva_intracom,
            buyer_name=invoice.customer_name,
            buyer_address=invoice.customer_address,
            buyer_city=None,
            buyer_postal=None,
            buyer_siren=invoice.customer_siren,
            buyer_tva_intracom=invoice.customer_tva_intracom,
            lines=lines,
            currency=invoice.currency,
            notes=invoice.notes,
            is_credit_note=(invoice.document_type == InvoiceType.AVOIR),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur génération Factur-X : {exc}") from exc

    filename = f"factur-x-{invoice.number or invoice_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{invoice_id}/facturx/xml",
    summary="Télécharger uniquement le XML Factur-X EN 16931",
    response_class=Response,
    responses={200: {"content": {"application/xml": {}}}},
)
def download_facturx_xml(
    invoice_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Retourne le XML CII Factur-X seul (sans le PDF) pour intégration EDI."""
    company_id = current_user["company_id"]

    invoice = db.query(Invoice).filter_by(id=invoice_id, company_id=company_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Société introuvable")

    lines = [
        {
            "description": ln.description,
            "quantity": ln.quantity,
            "unit_price_ht": ln.unit_price_ht,
            "vat_rate": ln.vat_rate,
            "line_ht": ln.line_ht,
            "line_tva": ln.line_tva,
            "line_ttc": ln.line_ttc,
        }
        for ln in invoice.lines
    ]

    from src.modules.facturation.facturx_xml import build_facturx_xml

    xml_bytes = build_facturx_xml(
        invoice_number=invoice.number or invoice_id[:8],
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        seller_name=company.name,
        seller_siret=company.siret or "",
        seller_address=company.address or "",
        seller_city=company.city or "",
        seller_postal=company.zip_code or "",
        seller_tva_intracom=company.tva_intracom,
        buyer_name=invoice.customer_name,
        buyer_address=invoice.customer_address,
        buyer_city=None,
        buyer_postal=None,
        buyer_siren=invoice.customer_siren,
        buyer_tva_intracom=invoice.customer_tva_intracom,
        lines=lines,
        currency=invoice.currency,
        notes=invoice.notes,
        is_credit_note=(invoice.document_type == InvoiceType.AVOIR),
    )

    return Response(
        content=xml_bytes,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="factur-x-{invoice.number or invoice_id[:8]}.xml"'},
    )
