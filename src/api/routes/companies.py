"""Sociétés — CRUD + chargement PCG."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.core.models.company import Company, LegalForm, VATRegime, TaxRegime
from src.db.session import get_session

router = APIRouter(prefix="/companies", tags=["Sociétés"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CompanyCreate(BaseModel):
    name: str
    siren: str | None = None
    siret: str | None = None
    tva_intracom: str | None = None
    legal_form: str = LegalForm.SARL
    naf_code: str | None = None
    accounting_standard: str = "PCG"
    default_currency: str = "EUR"
    address: str | None = None
    zip_code: str | None = None
    city: str | None = None
    country: str = "FR"
    vat_regime: str = VATRegime.NORMAL
    tax_regime: str = TaxRegime.IS
    fiscal_year_start_month: int = 1


class CompanyUpdate(BaseModel):
    name: str | None = None
    siren: str | None = None
    siret: str | None = None
    tva_intracom: str | None = None
    address: str | None = None
    zip_code: str | None = None
    city: str | None = None
    naf_code: str | None = None


class CompanyOut(BaseModel):
    id: str
    name: str
    siren: str | None
    siret: str | None
    tva_intracom: str | None
    legal_form: str
    naf_code: str | None
    accounting_standard: str
    default_currency: str
    address: str | None
    zip_code: str | None
    city: str | None
    country: str
    vat_regime: str
    tax_regime: str
    fiscal_year_start_month: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=CompanyOut, status_code=201)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> Company:
    company = Company(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/", response_model=list[CompanyOut])
def list_companies(
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> list[Company]:
    return db.query(Company).all()


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Société introuvable")
    return company


@router.patch("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: str,
    payload: CompanyUpdate,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Société introuvable")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204)
def delete_company(
    company_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> None:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Société introuvable")
    db.delete(company)
    db.commit()


@router.post("/{company_id}/load-pcg", status_code=200)
def load_pcg(
    company_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> dict:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Société introuvable")
    from src.core.services.pcg_loader import PCGLoader
    count = PCGLoader.load_for_company(company_id, db)
    return {"message": f"{count} comptes PCG chargés", "company_id": company_id, "count": count}
