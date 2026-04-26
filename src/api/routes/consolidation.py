"""Consolidation groupe — périmètre, agrégation, éliminations."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.modules.consolidation.engine import build_consolidated_package
from src.modules.consolidation.models import (
    Group, GroupEntity, IntegrationMethod, IntraGroupElimination, EliminationType,
)
from src.db.session import get_session
import uuid

router = APIRouter(prefix="/consolidation", tags=["Consolidation Groupe"])


class GroupEntityIn(BaseModel):
    company_id: str
    pct_controle: Decimal
    pct_interet: Decimal
    integration_method: IntegrationMethod


class GroupCreate(BaseModel):
    name: str
    currency: str = "EUR"
    entities: list[GroupEntityIn]


class EliminationIn(BaseModel):
    entity_debit_id: str
    entity_credit_id: str
    elimination_type: EliminationType
    amount: Decimal
    account_debit: str
    account_credit: str
    description: str | None = None


class ConsolidatedPackageOut(BaseModel):
    group_id: str
    fiscal_year_id: str
    currency: str
    balances: dict
    eliminations_applied: int
    total_assets: Decimal
    total_equity: Decimal
    net_income: Decimal


@router.post("/groups", status_code=201)
def create_group(
    body: GroupCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    group = Group(
        id=str(uuid.uuid4()),
        name=body.name,
        parent_company_id=current_user["company_id"],
        consolidation_currency=body.currency,
    )
    db.add(group)
    for e in body.entities:
        entity = GroupEntity(
            id=str(uuid.uuid4()),
            group_id=group.id,
            company_id=e.company_id,
            pct_controle=e.pct_controle,
            pct_interet=e.pct_interet,
            integration_method=e.integration_method,
        )
        db.add(entity)
    db.commit()
    return {"id": group.id, "name": group.name}


@router.get("/groups")
def list_groups(
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    parent_company_id = current_user["company_id"]
    groups = db.query(Group).filter_by(parent_company_id=parent_company_id).all()
    return [{"id": str(g.id), "name": g.name, "currency": g.consolidation_currency} for g in groups]


@router.post("/groups/{group_id}/eliminations", status_code=201)
def add_elimination(
    group_id: str,
    body: EliminationIn,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    group = db.query(Group).filter_by(id=group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Groupe non trouvé")
    elim = IntraGroupElimination(
        id=str(uuid.uuid4()),
        group_id=group_id,
        **body.model_dump(),
    )
    db.add(elim)
    db.commit()
    return {"id": str(elim.id), "message": "Élimination ajoutée"}


@router.get("/groups/{group_id}/package", response_model=ConsolidatedPackageOut)
def consolidated_package(
    group_id: str,
    fiscal_year_id: str = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> ConsolidatedPackageOut:
    """Construit le package de consolidation pour un groupe et exercice."""
    group = db.query(Group).filter_by(id=group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Groupe non trouvé")
    try:
        package = build_consolidated_package(group_id, fiscal_year_id, db)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ConsolidatedPackageOut(
        group_id=group_id,
        fiscal_year_id=fiscal_year_id,
        currency=group.consolidation_currency,
        balances=package.get("balances", {}),
        eliminations_applied=package.get("eliminations_applied", 0),
        total_assets=package.get("total_assets", Decimal("0")),
        total_equity=package.get("total_equity", Decimal("0")),
        net_income=package.get("net_income", Decimal("0")),
    )
