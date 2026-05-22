"""TVA — déclarations CA3/CA12."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.core.engine.tva_engine import compute_tva_declaration
from src.db.session import get_session

router = APIRouter(prefix="/tva", tags=["TVA"])


class TVALineOut(BaseModel):
    vat_code: str
    base_ht: Decimal
    tva_amount: Decimal
    rate: Decimal


class TVADeclarationOut(BaseModel):
    period_start: date
    period_end: date
    total_collectee: Decimal
    total_deductible: Decimal
    solde_tva: Decimal
    lines_collectee: list[TVALineOut]
    lines_deductible: list[TVALineOut]
    a_payer: bool


@router.get("/declaration", response_model=TVADeclarationOut)
def tva_declaration(
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> TVADeclarationOut:
    """Calcule la déclaration TVA (CA3) pour une période."""
    company_id = current_user["company_id"]
    result = compute_tva_declaration(company_id, period_start, period_end, db)
    return TVADeclarationOut(
        period_start=period_start,
        period_end=period_end,
        total_collectee=result.total_collectee,
        total_deductible=result.total_deductible,
        solde_tva=result.solde_tva,
        lines_collectee=[
            TVALineOut(vat_code=l.vat_code, base_ht=l.base_ht, tva_amount=l.tva_amount, rate=l.rate)
            for l in result.lines_collectee
        ],
        lines_deductible=[
            TVALineOut(vat_code=l.vat_code, base_ht=l.base_ht, tva_amount=l.tva_amount, rate=l.rate)
            for l in result.lines_deductible
        ],
        a_payer=result.solde_tva > 0,
    )
