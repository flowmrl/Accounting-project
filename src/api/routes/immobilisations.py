"""Immobilisations — fiches actif, plans d'amortissement, dotations."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.modules.immobilisations.engine import compute_depreciation_plan, post_depreciation
from src.modules.immobilisations.models import (
    AssetCategory, AssetStatus, DepreciationMethod, FixedAsset,
)
from src.db.session import get_session
import uuid

router = APIRouter(prefix="/fixed-assets", tags=["Immobilisations"])


class FixedAssetCreate(BaseModel):
    name: str
    reference: str | None = None
    category: AssetCategory
    acquisition_date: date
    acquisition_cost: Decimal
    residual_value: Decimal = Decimal("0")
    useful_life_years: int
    depreciation_method: DepreciationMethod = DepreciationMethod.LINEAIRE
    account_code: str
    depreciation_account_code: str
    accumulated_depreciation_account_code: str
    journal_code: str = "IMMOBILISATIONS"
    location: str | None = None
    serial_number: str | None = None


class DepreciationLineOut(BaseModel):
    year: int
    accounting_amount: Decimal
    exceptional_amount: Decimal
    cumulative: Decimal
    net_book_value: Decimal


class FixedAssetOut(BaseModel):
    id: str
    name: str
    reference: str | None
    category: str
    status: str
    acquisition_date: date
    acquisition_cost: Decimal
    residual_value: Decimal
    useful_life_years: int
    depreciation_method: str
    account_code: str

    class Config:
        from_attributes = True


@router.get("/", response_model=list[FixedAssetOut])
def list_assets(
    category: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[FixedAssetOut]:
    company_id = current_user["company_id"]
    q = db.query(FixedAsset).filter(FixedAsset.company_id == company_id)
    if category:
        q = q.filter(FixedAsset.category == category)
    if status:
        q = q.filter(FixedAsset.status == status)
    return q.order_by(FixedAsset.acquisition_date).all()


@router.post("/", response_model=FixedAssetOut, status_code=201)
def create_asset(
    body: FixedAssetCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> FixedAsset:
    company_id = current_user["company_id"]
    asset = FixedAsset(
        id=str(uuid.uuid4()),
        company_id=company_id,
        status=AssetStatus.EN_SERVICE,
        **body.model_dump(),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{asset_id}/depreciation-plan", response_model=list[DepreciationLineOut])
def depreciation_plan(
    asset_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[DepreciationLineOut]:
    company_id = current_user["company_id"]
    asset = db.query(FixedAsset).filter_by(id=asset_id, company_id=company_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Immobilisation non trouvée")
    plan = compute_depreciation_plan(asset)
    return [
        DepreciationLineOut(
            year=line.year,
            accounting_amount=line.accounting_amount,
            exceptional_amount=line.exceptional_amount,
            cumulative=line.cumulative,
            net_book_value=line.net_book_value,
        )
        for line in plan
    ]


@router.post("/{asset_id}/post-depreciation")
def post_asset_depreciation(
    asset_id: str,
    fiscal_year_id: str = Query(...),
    period_date: date = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    company_id = current_user["company_id"]
    asset = db.query(FixedAsset).filter_by(id=asset_id, company_id=company_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Immobilisation non trouvée")
    entry = post_depreciation(asset, fiscal_year_id, period_date, db)
    return {"message": "Dotation comptabilisée", "entry_id": str(entry.id)}
