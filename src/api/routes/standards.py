"""Standards référentiels comptables — liste et plan de comptes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import src.addons.be_gaap.standard  # noqa: F401
import src.addons.dutch_bw2.standard  # noqa: F401
import src.addons.german_hgb.standard  # noqa: F401

# Import all add-ons to ensure they register
import src.addons.ifrs.standard  # noqa: F401
import src.addons.italian_oic.standard  # noqa: F401
import src.addons.luxembourg_gaap.standard  # noqa: F401
import src.addons.polish_psr.standard  # noqa: F401
import src.addons.spanish_pgc.standard  # noqa: F401
import src.addons.swiss_fer.standard  # noqa: F401
import src.addons.uk_frs.standard  # noqa: F401
import src.addons.us_gaap.standard  # noqa: F401
from src.core.standards.base import StandardRegistry

router = APIRouter(prefix="/standards", tags=["Référentiels"])


class StandardInfo(BaseModel):
    code: str
    name: str
    countries: str


class AccountTemplateOut(BaseModel):
    code: str
    name: str
    account_type: str
    account_nature: str
    account_class: str
    parent_code: str | None
    is_detail: bool
    is_reconcilable: bool
    vat_code: str | None


class FinancialLineOut(BaseModel):
    code: str
    label: str
    account_codes: list[str]
    is_subtotal: bool
    is_total: bool
    indent_level: int
    negate: bool


class FinancialStatementOut(BaseModel):
    code: str
    name: str
    lines: list[FinancialLineOut]


@router.get("/", response_model=list[StandardInfo])
async def list_standards() -> list[StandardInfo]:
    """Liste tous les référentiels disponibles."""
    return [StandardInfo(**s) for s in StandardRegistry.list_all()]


@router.get("/{standard_code}/accounts", response_model=list[AccountTemplateOut])
async def get_chart_of_accounts(standard_code: str) -> list[AccountTemplateOut]:
    """Retourne le plan de comptes d'un référentiel."""
    try:
        std = StandardRegistry.get(standard_code.upper())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        AccountTemplateOut(
            code=a.code, name=a.name, account_type=a.account_type,
            account_nature=a.account_nature, account_class=a.account_class,
            parent_code=a.parent_code, is_detail=a.is_detail,
            is_reconcilable=a.is_reconcilable, vat_code=a.vat_code,
        )
        for a in std.get_chart_of_accounts()
    ]


@router.get("/{standard_code}/balance-sheet", response_model=dict[str, FinancialStatementOut])
async def get_balance_sheet_structure(standard_code: str) -> dict:
    """Structure du bilan selon le référentiel."""
    try:
        std = StandardRegistry.get(standard_code.upper())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    actif, passif = std.get_balance_sheet_structure()

    def _convert(fs) -> FinancialStatementOut:
        return FinancialStatementOut(
            code=fs.code, name=fs.name,
            lines=[FinancialLineOut(
                code=l.code, label=l.label, account_codes=l.account_codes,
                is_subtotal=l.is_subtotal, is_total=l.is_total,
                indent_level=l.indent_level, negate=l.negate,
            ) for l in fs.lines],
        )
    return {"actif": _convert(actif), "passif": _convert(passif)}


@router.get("/{standard_code}/income-statement", response_model=FinancialStatementOut)
async def get_income_statement_structure(standard_code: str) -> FinancialStatementOut:
    """Structure du compte de résultat."""
    try:
        std = StandardRegistry.get(standard_code.upper())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    cdr = std.get_income_statement_structure()
    return FinancialStatementOut(
        code=cdr.code, name=cdr.name,
        lines=[FinancialLineOut(
            code=l.code, label=l.label, account_codes=l.account_codes,
            is_subtotal=l.is_subtotal, is_total=l.is_total,
            indent_level=l.indent_level, negate=l.negate,
        ) for l in cdr.lines],
    )


@router.get("/{standard_code}/vat-codes")
async def get_vat_codes(standard_code: str) -> dict:
    """Codes TVA du référentiel."""
    try:
        std = StandardRegistry.get(standard_code.upper())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return std.get_vat_codes()
