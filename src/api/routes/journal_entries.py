"""Écritures comptables — saisie, validation, extourne, grand livre."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.core.engine.ledger import EntryInput, LineInput, post_entry, reverse_entry
from src.core.engine.balance import compute_grand_livre, compute_trial_balance
from src.core.models.journal_entry import EntryStatus, JournalEntry
from src.db.session import get_session

router = APIRouter(prefix="/journal-entries", tags=["Écritures comptables"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LineIn(BaseModel):
    account_code: str
    label: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    analytic_code: str | None = None


class EntryIn(BaseModel):
    journal_code: str
    date: date
    label: str
    fiscal_year_id: str
    lines: list[LineIn]
    reference: str | None = None


class EntryOut(BaseModel):
    id: str
    journal_code: str
    entry_date: date
    label: str
    reference: str | None
    status: str
    total_debit: Decimal
    total_credit: Decimal


class TrialBalanceLine(BaseModel):
    code: str
    name: str
    total_debit: Decimal
    total_credit: Decimal
    solde_debiteur: Decimal
    solde_crediteur: Decimal


class GrandLivreLine(BaseModel):
    date: date
    journal: str
    reference: str | None
    label: str
    debit: Decimal
    credit: Decimal
    running_balance: Decimal


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/", response_model=EntryOut, status_code=201)
def post_journal_entry(
    body: EntryIn,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> EntryOut:
    company_id = current_user["company_id"]
    entry_input = EntryInput(
        journal_code=body.journal_code,
        date=body.date,
        label=body.label,
        fiscal_year_id=body.fiscal_year_id,
        reference=body.reference,
        lines=[
            LineInput(
                account_code=l.account_code,
                label=l.label,
                debit=l.debit,
                credit=l.credit,
                analytic_code=l.analytic_code,
            )
            for l in body.lines
        ],
    )
    try:
        entry = post_entry(company_id, entry_input, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EntryOut(
        id=str(entry.id),
        journal_code=entry.journal_code,
        entry_date=entry.entry_date,
        label=entry.label,
        reference=entry.reference,
        status=entry.status.value,
        total_debit=entry.total_debit,
        total_credit=entry.total_credit,
    )


@router.post("/{entry_id}/reverse", response_model=EntryOut)
def reverse_journal_entry(
    entry_id: str,
    reversal_date: date = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> EntryOut:
    try:
        entry = reverse_entry(entry_id, reversal_date, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EntryOut(
        id=str(entry.id),
        journal_code=entry.journal_code,
        entry_date=entry.entry_date,
        label=entry.label,
        reference=entry.reference,
        status=entry.status.value,
        total_debit=entry.total_debit,
        total_credit=entry.total_credit,
    )


@router.get("/trial-balance", response_model=list[TrialBalanceLine])
def trial_balance(
    fiscal_year_id: str = Query(...),
    account_class: str | None = Query(None),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[TrialBalanceLine]:
    company_id = current_user["company_id"]
    rows = compute_trial_balance(company_id, fiscal_year_id, db, account_class=account_class)
    return [
        TrialBalanceLine(
            code=r.code, name=r.name,
            total_debit=r.total_debit, total_credit=r.total_credit,
            solde_debiteur=r.solde_debiteur, solde_crediteur=r.solde_crediteur,
        )
        for r in rows
    ]


@router.get("/grand-livre/{account_code}", response_model=list[GrandLivreLine])
def grand_livre(
    account_code: str,
    fiscal_year_id: str = Query(...),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[GrandLivreLine]:
    company_id = current_user["company_id"]
    lines = compute_grand_livre(company_id, account_code, fiscal_year_id, db, date_from=date_from, date_to=date_to)
    return [
        GrandLivreLine(
            date=l.date, journal=l.journal_code, reference=l.reference,
            label=l.label, debit=l.debit, credit=l.credit,
            running_balance=l.running_balance,
        )
        for l in lines
    ]
