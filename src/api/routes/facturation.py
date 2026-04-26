"""Facturation — devis, factures, avoirs, relances, balance âgée."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.modules.facturation.models import Invoice, InvoiceLine, DocumentStatus as InvoiceStatus, DocumentType as InvoiceType
from src.modules.facturation.service import validate_invoice, create_credit_note, get_aged_balance
from src.db.session import get_session
import uuid

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
