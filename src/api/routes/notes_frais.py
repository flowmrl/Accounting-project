"""Notes de frais — CRUD + calcul kilométrique."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.db.session import get_session
from src.modules.notes_frais.models import (
    NoteFrais, LigneFrais, ExpenseStatus, ExpenseCategory,
    compute_indemnite_kilometrique,
)

router = APIRouter(prefix="/expenses", tags=["Notes de frais"])


class NoteCreate(BaseModel):
    company_id: str
    employee_id: str
    period_start: date
    period_end: date
    title: str
    notes: str | None = None


class LineCreate(BaseModel):
    expense_date: date
    category: str
    description: str
    amount: float
    vat_amount: float = 0.0
    account_code: str = "625"
    has_receipt: bool = False


class KmLineCreate(BaseModel):
    expense_date: date
    description: str
    vehicle_cv: int
    km_distance: int


class NoteOut(BaseModel):
    id: str
    company_id: str
    employee_id: str
    period_start: date
    period_end: date
    title: str
    status: str
    total_amount: float
    model_config = {"from_attributes": True}


@router.post("/", response_model=NoteOut, status_code=201)
def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> NoteFrais:
    note = NoteFrais(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/", response_model=list[NoteOut])
def list_notes(
    company_id: str,
    employee_id: str | None = None,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> list[NoteFrais]:
    q = db.query(NoteFrais).filter(NoteFrais.company_id == company_id)
    if employee_id:
        q = q.filter(NoteFrais.employee_id == employee_id)
    return q.all()


@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> NoteFrais:
    note = db.query(NoteFrais).filter(NoteFrais.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note de frais introuvable")
    return note


@router.post("/{note_id}/lines", status_code=201)
def add_line(
    note_id: str,
    payload: LineCreate,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> dict:
    from decimal import Decimal
    note = db.query(NoteFrais).filter(NoteFrais.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note de frais introuvable")
    line = LigneFrais(
        id=str(uuid.uuid4()),
        company_id=note.company_id,
        note_id=note_id,
        amount=Decimal(str(payload.amount)),
        vat_amount=Decimal(str(payload.vat_amount)),
        **{k: v for k, v in payload.model_dump().items() if k not in ("amount", "vat_amount")},
    )
    db.add(line)
    note.recompute_total()
    db.commit()
    return {"line_id": line.id, "amount": float(line.amount), "total": float(note.total_amount)}


@router.post("/{note_id}/km-lines", status_code=201)
def add_km_line(
    note_id: str,
    payload: KmLineCreate,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> dict:
    note = db.query(NoteFrais).filter(NoteFrais.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note de frais introuvable")
    line = LigneFrais.from_kilometrique(
        company_id=note.company_id,
        note_id=note_id,
        expense_date=payload.expense_date,
        description=payload.description,
        cv=payload.vehicle_cv,
        km=payload.km_distance,
    )
    line.id = str(uuid.uuid4())
    db.add(line)
    note.recompute_total()
    db.commit()
    return {
        "line_id": line.id,
        "amount": float(line.amount),
        "km": payload.km_distance,
        "cv": payload.vehicle_cv,
        "total": float(note.total_amount),
    }


@router.post("/{note_id}/submit", status_code=200)
def submit_note(
    note_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> dict:
    note = db.query(NoteFrais).filter(NoteFrais.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note de frais introuvable")
    if note.status != ExpenseStatus.BROUILLON:
        raise HTTPException(status_code=409, detail=f"Statut actuel : {note.status}")
    note.status = ExpenseStatus.SOUMIS
    db.commit()
    return {"status": note.status, "total_amount": float(note.total_amount)}
