"""Plan de comptes — CRUD accounts."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.core.models.account import Account, AccountNature, AccountType
from src.db.session import get_session

router = APIRouter(prefix="/accounts", tags=["Plan de comptes"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AccountCreate(BaseModel):
    code: str
    name: str
    account_type: AccountType
    account_nature: AccountNature
    account_class: str
    parent_id: str | None = None
    is_detail: bool = True
    is_reconcilable: bool = False
    vat_code: str | None = None
    description: str | None = None
    tags: list[str] = []


class AccountUpdate(BaseModel):
    name: str | None = None
    is_detail: bool | None = None
    is_reconcilable: bool | None = None
    vat_code: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class AccountOut(BaseModel):
    id: str
    code: str
    name: str
    account_type: str
    account_nature: str
    account_class: str
    parent_id: str | None
    is_detail: bool
    is_reconcilable: bool
    vat_code: str | None
    balance_debit: Any
    balance_credit: Any

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[AccountOut])
def list_accounts(
    account_class: str | None = Query(None),
    nature: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[AccountOut]:
    company_id = current_user["company_id"]
    q = db.query(Account).filter(Account.company_id == company_id)
    if account_class:
        q = q.filter(Account.account_class == account_class)
    if nature:
        q = q.filter(Account.account_nature == nature)
    if search:
        q = q.filter(
            Account.code.ilike(f"{search}%") | Account.name.ilike(f"%{search}%")
        )
    return q.order_by(Account.code).all()


@router.post("/", response_model=AccountOut, status_code=201)
def create_account(
    body: AccountCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Account:
    company_id = current_user["company_id"]
    existing = db.query(Account).filter_by(company_id=company_id, code=body.code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Compte {body.code} déjà existant")
    acct = Account(
        id=str(uuid.uuid4()),
        company_id=company_id,
        **body.model_dump(),
    )
    db.add(acct)
    db.commit()
    db.refresh(acct)
    return acct


@router.get("/{code}", response_model=AccountOut)
def get_account(
    code: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Account:
    company_id = current_user["company_id"]
    acct = db.query(Account).filter_by(company_id=company_id, code=code).first()
    if not acct:
        raise HTTPException(status_code=404, detail=f"Compte {code} non trouvé")
    return acct


@router.patch("/{code}", response_model=AccountOut)
def update_account(
    code: str,
    body: AccountUpdate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Account:
    company_id = current_user["company_id"]
    acct = db.query(Account).filter_by(company_id=company_id, code=code).first()
    if not acct:
        raise HTTPException(status_code=404, detail=f"Compte {code} non trouvé")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(acct, field, value)
    db.commit()
    db.refresh(acct)
    return acct
