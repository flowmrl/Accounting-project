"""Reporting — bilan, compte de résultat, ratios financiers."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.core.engine.reports import generate_balance_sheet, generate_income_statement, compute_key_ratios
from src.db.session import get_session

router = APIRouter(prefix="/reports", tags=["Reporting financier"])


class ReportLineOut(BaseModel):
    code: str
    label: str
    amount: Decimal
    is_subtotal: bool
    is_total: bool
    indent_level: int


class FinancialReportOut(BaseModel):
    name: str
    standard: str
    fiscal_year_id: str
    lines: list[ReportLineOut]
    generated_at: str


class BalanceSheetOut(BaseModel):
    actif: FinancialReportOut
    passif: FinancialReportOut


class RatiosOut(BaseModel):
    autonomie_financiere: Decimal | None
    endettement: Decimal | None
    rentabilite_nette: Decimal | None
    roe: Decimal | None


def _convert_report(report) -> FinancialReportOut:
    from datetime import datetime
    return FinancialReportOut(
        name=report.name,
        standard=report.standard,
        fiscal_year_id=report.fiscal_year_id,
        lines=[
            ReportLineOut(
                code=l.code, label=l.label, amount=l.amount,
                is_subtotal=l.is_subtotal, is_total=l.is_total,
                indent_level=l.indent_level,
            )
            for l in report.lines
        ],
        generated_at=datetime.now().isoformat(),
    )


@router.get("/balance-sheet", response_model=BalanceSheetOut)
def balance_sheet(
    fiscal_year_id: str = Query(...),
    standard: str = Query("PCG"),
    closing_date: date | None = Query(None),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> BalanceSheetOut:
    """Bilan actif + passif selon le référentiel choisi."""
    company_id = current_user["company_id"]
    actif, passif = generate_balance_sheet(company_id, fiscal_year_id, standard, db, closing_date=closing_date)
    return BalanceSheetOut(actif=_convert_report(actif), passif=_convert_report(passif))


@router.get("/income-statement", response_model=FinancialReportOut)
def income_statement(
    fiscal_year_id: str = Query(...),
    standard: str = Query("PCG"),
    closing_date: date | None = Query(None),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> FinancialReportOut:
    """Compte de résultat selon le référentiel choisi."""
    company_id = current_user["company_id"]
    report = generate_income_statement(company_id, fiscal_year_id, standard, db, closing_date=closing_date)
    return _convert_report(report)


@router.get("/ratios", response_model=RatiosOut)
def key_ratios(
    fiscal_year_id: str = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> RatiosOut:
    """Ratios financiers clés (autonomie, endettement, rentabilité, ROE)."""
    company_id = current_user["company_id"]
    ratios = compute_key_ratios(company_id, fiscal_year_id, db)
    return RatiosOut(
        autonomie_financiere=ratios.get("autonomie_financiere"),
        endettement=ratios.get("endettement"),
        rentabilite_nette=ratios.get("rentabilite_nette"),
        roe=ratios.get("roe"),
    )
