"""Tax — IS, impôts différés, export FEC."""
from __future__ import annotations

import io
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.modules.tax.fec_export import export_fec
from src.modules.tax.is_engine import compute_is, compute_deferred_taxes
from src.db.session import get_session

router = APIRouter(prefix="/tax", tags=["Fiscalité"])


class ISInput(BaseModel):
    fiscal_year_id: str
    resultat_comptable: Decimal
    reintegrations: Decimal = Decimal("0")
    deductions: Decimal = Decimal("0")
    is_pme: bool = True
    ca_exercice: Decimal = Decimal("0")


class ISOut(BaseModel):
    resultat_fiscal: Decimal
    base_is: Decimal
    is_taux_reduit: Decimal
    is_taux_normal: Decimal
    is_total: Decimal
    taux_effectif: Decimal


class DeferredTaxOut(BaseModel):
    ida_total: Decimal
    idp_total: Decimal
    position_nette: Decimal


@router.post("/is/compute", response_model=ISOut)
def compute_corporate_tax(
    body: ISInput,
    current_user: dict = Depends(get_current_user),
) -> ISOut:
    """Calcule l'impôt sur les sociétés (PME ou taux plein)."""
    result = compute_is(
        resultat_comptable=body.resultat_comptable,
        reintegrations=body.reintegrations,
        deductions=body.deductions,
        is_pme=body.is_pme,
        ca_exercice=body.ca_exercice,
    )
    return ISOut(
        resultat_fiscal=result["resultat_fiscal"],
        base_is=result["base_is"],
        is_taux_reduit=result["is_taux_reduit"],
        is_taux_normal=result["is_taux_normal"],
        is_total=result["is_total"],
        taux_effectif=result["taux_effectif"],
    )


@router.post("/deferred/compute", response_model=DeferredTaxOut)
def compute_deferred(
    fiscal_year_id: str = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> DeferredTaxOut:
    """Calcule les impôts différés actifs (IDA) et passifs (IDP)."""
    company_id = current_user["company_id"]
    result = compute_deferred_taxes(company_id, fiscal_year_id, db)
    return DeferredTaxOut(
        ida_total=result["ida_total"],
        idp_total=result["idp_total"],
        position_nette=result["position_nette"],
    )


@router.get("/fec/export")
def fec_export(
    fiscal_year_id: str = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """Exporte le Fichier des Écritures Comptables (FEC) — format DGFiP."""
    company_id = current_user["company_id"]
    try:
        content = export_fec(company_id, fiscal_year_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    filename = f"FEC_{company_id}_{fiscal_year_id}.txt"
    return StreamingResponse(
        io.StringIO(content),
        media_type="text/plain; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
