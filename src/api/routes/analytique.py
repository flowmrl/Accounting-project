"""Comptabilité analytique — axes, sections, budget vs réalisé."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.db.session import get_session
from src.modules.analytique.models import AnalyticAxis, AnalyticSection, AxisType
from src.modules.analytique.engine import get_budget_vs_realise, distribute_line

router = APIRouter(prefix="/analytic", tags=["Analytique"])


class AxisCreate(BaseModel):
    company_id: str
    code: str
    name: str
    axis_type: str = AxisType.LIBRE
    description: str | None = None


class SectionCreate(BaseModel):
    company_id: str
    axis_id: str
    code: str
    name: str
    parent_id: str | None = None
    manager_id: str | None = None


class DistributionItem(BaseModel):
    section_id: str
    percentage: float
    amount: float


class DistributeRequest(BaseModel):
    journal_line_id: str
    fiscal_year_id: str
    company_id: str
    distributions: list[DistributionItem]


class AxisOut(BaseModel):
    id: str
    company_id: str
    code: str
    name: str
    axis_type: str
    is_active: bool
    model_config = {"from_attributes": True}


class SectionOut(BaseModel):
    id: str
    company_id: str
    axis_id: str
    code: str
    name: str
    parent_id: str | None
    is_active: bool
    model_config = {"from_attributes": True}


@router.post("/axes", response_model=AxisOut, status_code=201)
def create_axis(
    payload: AxisCreate,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> AnalyticAxis:
    axis = AnalyticAxis(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(axis)
    db.commit()
    db.refresh(axis)
    return axis


@router.get("/axes", response_model=list[AxisOut])
def list_axes(
    company_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> list[AnalyticAxis]:
    return db.query(AnalyticAxis).filter(
        AnalyticAxis.company_id == company_id,
        AnalyticAxis.is_active.is_(True),
    ).all()


@router.post("/sections", response_model=SectionOut, status_code=201)
def create_section(
    payload: SectionCreate,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> AnalyticSection:
    section = AnalyticSection(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@router.get("/sections", response_model=list[SectionOut])
def list_sections(
    company_id: str,
    axis_id: str | None = None,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> list[AnalyticSection]:
    q = db.query(AnalyticSection).filter(
        AnalyticSection.company_id == company_id,
        AnalyticSection.is_active.is_(True),
    )
    if axis_id:
        q = q.filter(AnalyticSection.axis_id == axis_id)
    return q.all()


@router.get("/budget-vs-realise")
def budget_vs_realise(
    section_id: str,
    fiscal_year_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> list[dict]:
    return get_budget_vs_realise(section_id, fiscal_year_id, db)


@router.post("/distribute", status_code=201)
def distribute(
    payload: DistributeRequest,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> dict:
    from decimal import Decimal
    items = [
        {"section_id": d.section_id, "percentage": Decimal(str(d.percentage)), "amount": Decimal(str(d.amount))}
        for d in payload.distributions
    ]
    try:
        dists = distribute_line(
            payload.journal_line_id, items, payload.fiscal_year_id, payload.company_id, db
        )
        db.commit()
        return {"created": len(dists), "distributions": [d.id for d in dists]}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
