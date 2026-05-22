"""Achats Fournisseurs — fournisseurs, commandes, factures, paiements, balance âgée."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.db.session import get_session
from src.modules.achats.models import (
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus,
    Supplier, SupplierInvoice, SupplierInvoiceLine, SupplierInvoiceStatus,
)
from src.modules.achats.service import (
    approve_supplier_invoice, compute_invoice_totals,
    get_aged_payables, record_payment, reject_supplier_invoice,
)

router = APIRouter(prefix="/purchases", tags=["Achats Fournisseurs"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SupplierCreate(BaseModel):
    name: str
    siren: str | None = None
    tva_intracom: str | None = None
    address: str | None = None
    city: str | None = None
    zip_code: str | None = None
    country: str = "FR"
    email: str | None = None
    iban: str | None = None
    payment_terms_days: int = 30


class SupplierOut(BaseModel):
    id: str
    name: str
    siren: str | None
    email: str | None
    status: str
    payment_terms_days: int
    model_config = {"from_attributes": True}


class POLineIn(BaseModel):
    description: str
    quantity: Decimal
    unit_price_ht: Decimal
    vat_rate: Decimal = Decimal("20.00")
    account_code: str = "607"


class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    order_date: date
    expected_delivery_date: date | None = None
    currency: str = "EUR"
    notes: str | None = None
    lines: list[POLineIn]


class PurchaseOrderOut(BaseModel):
    id: str
    number: str | None
    supplier_id: str
    status: str
    order_date: date
    total_ttc: Decimal
    currency: str
    model_config = {"from_attributes": True}


class SILineIn(BaseModel):
    description: str
    quantity: Decimal
    unit_price_ht: Decimal
    vat_rate: Decimal = Decimal("20.00")
    account_code: str = "607"


class SupplierInvoiceCreate(BaseModel):
    supplier_id: str
    supplier_ref: str | None = None
    invoice_date: date
    due_date: date | None = None
    currency: str = "EUR"
    notes: str | None = None
    lines: list[SILineIn]


class SupplierInvoiceOut(BaseModel):
    id: str
    supplier_id: str
    supplier_ref: str | None
    status: str
    invoice_date: date
    due_date: date | None
    subtotal_ht: Decimal
    total_tva: Decimal
    total_ttc: Decimal
    amount_paid: Decimal
    currency: str
    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    amount: Decimal
    payment_date: date
    payment_method: str = "VIREMENT"
    reference: str | None = None


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

@router.post("/suppliers", response_model=SupplierOut, status_code=201)
def create_supplier(
    body: SupplierCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Supplier:
    company_id = current_user["company_id"]
    s = Supplier(id=str(uuid.uuid4()), company_id=company_id, **body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[Supplier]:
    return db.query(Supplier).filter_by(company_id=current_user["company_id"]).all()


@router.get("/suppliers/{supplier_id}", response_model=SupplierOut)
def get_supplier(
    supplier_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Supplier:
    s = db.query(Supplier).filter_by(id=supplier_id, company_id=current_user["company_id"]).first()
    if not s:
        raise HTTPException(status_code=404, detail="Fournisseur introuvable")
    return s


# ---------------------------------------------------------------------------
# Purchase Orders
# ---------------------------------------------------------------------------

@router.post("/orders", response_model=PurchaseOrderOut, status_code=201)
def create_order(
    body: PurchaseOrderCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> PurchaseOrder:
    company_id = current_user["company_id"]
    order = PurchaseOrder(
        id=str(uuid.uuid4()),
        company_id=company_id,
        supplier_id=body.supplier_id,
        order_date=body.order_date,
        expected_delivery_date=body.expected_delivery_date,
        currency=body.currency,
        notes=body.notes,
    )
    ht = tva = Decimal("0")
    for ln in body.lines:
        line = PurchaseOrderLine(
            id=str(uuid.uuid4()),
            order_id=order.id,
            description=ln.description,
            quantity=ln.quantity,
            unit_price_ht=ln.unit_price_ht,
            vat_rate=ln.vat_rate,
            account_code=ln.account_code,
        )
        order.lines.append(line)
        ht += line.line_ht
        tva += line.line_ht * ln.vat_rate / Decimal("100")
    order.subtotal_ht, order.total_tva, order.total_ttc = ht, tva, ht + tva
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/orders", response_model=list[PurchaseOrderOut])
def list_orders(
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[PurchaseOrder]:
    return db.query(PurchaseOrder).filter_by(company_id=current_user["company_id"]).all()


@router.post("/orders/{order_id}/confirm", response_model=PurchaseOrderOut)
def confirm_order(
    order_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> PurchaseOrder:
    order = db.query(PurchaseOrder).filter_by(id=order_id, company_id=current_user["company_id"]).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    from src.modules.achats.service import confirm_purchase_order
    try:
        return confirm_purchase_order(order, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Supplier Invoices
# ---------------------------------------------------------------------------

@router.post("/invoices", response_model=SupplierInvoiceOut, status_code=201)
def create_supplier_invoice(
    body: SupplierInvoiceCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> SupplierInvoice:
    company_id = current_user["company_id"]
    inv = SupplierInvoice(
        id=str(uuid.uuid4()),
        company_id=company_id,
        supplier_id=body.supplier_id,
        supplier_ref=body.supplier_ref,
        invoice_date=body.invoice_date,
        due_date=body.due_date,
        currency=body.currency,
        notes=body.notes,
        status=SupplierInvoiceStatus.RECUE,
    )
    for ln in body.lines:
        inv.lines.append(SupplierInvoiceLine(
            id=str(uuid.uuid4()),
            invoice_id=inv.id,
            description=ln.description,
            quantity=ln.quantity,
            unit_price_ht=ln.unit_price_ht,
            vat_rate=ln.vat_rate,
            account_code=ln.account_code,
        ))
    inv.subtotal_ht, inv.total_tva, inv.total_ttc = compute_invoice_totals(inv)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.get("/invoices", response_model=list[SupplierInvoiceOut])
def list_supplier_invoices(
    status: str | None = Query(None),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[SupplierInvoice]:
    q = db.query(SupplierInvoice).filter_by(company_id=current_user["company_id"])
    if status:
        q = q.filter(SupplierInvoice.status == status)
    return q.all()


@router.post("/invoices/{invoice_id}/approve", response_model=SupplierInvoiceOut)
def approve_invoice(
    invoice_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> SupplierInvoice:
    inv = db.query(SupplierInvoice).filter_by(id=invoice_id, company_id=current_user["company_id"]).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    try:
        return approve_supplier_invoice(inv, current_user["user_id"], db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/invoices/{invoice_id}/reject", response_model=SupplierInvoiceOut)
def reject_invoice(
    invoice_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> SupplierInvoice:
    inv = db.query(SupplierInvoice).filter_by(id=invoice_id, company_id=current_user["company_id"]).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    try:
        return reject_supplier_invoice(inv, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/invoices/{invoice_id}/pay", response_model=SupplierInvoiceOut)
def pay_invoice(
    invoice_id: str,
    body: PaymentCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> SupplierInvoice:
    inv = db.query(SupplierInvoice).filter_by(id=invoice_id, company_id=current_user["company_id"]).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    try:
        record_payment(inv, body.amount, body.payment_date, body.payment_method, body.reference, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.refresh(inv)
    return inv


@router.get("/aged-payables")
def aged_payables(
    as_of: date = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Balance âgée fournisseurs."""
    return get_aged_payables(current_user["company_id"], as_of, db)
