"""Reporting — bilan, compte de résultat, ratios financiers, XBRL greffe."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.core.engine.reports import compute_key_ratios, generate_balance_sheet, generate_income_statement
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


@router.get(
    "/xbrl",
    summary="Export XBRL pour dépôt au greffe (INPI / e-liasse)",
    response_class=Response,
    responses={200: {"content": {"application/xml": {}}}},
)
def export_xbrl(
    fiscal_year_id: str = Query(...),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Génère le fichier XBRL instance document (taxonomie FR-GAAP 2022) pour dépôt des comptes annuels."""
    from src.core.models.company import Company
    from src.core.models.fiscal_year import FiscalYear
    from src.modules.reporting.xbrl import build_xbrl

    company_id = current_user["company_id"]
    company = db.query(Company).filter_by(id=company_id).first()
    if not company:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Société introuvable")

    fy = db.query(FiscalYear).filter_by(id=fiscal_year_id, company_id=company_id).first()
    if not fy:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Exercice introuvable")

    # Génère bilan + CR depuis le moteur de rapports
    actif_report, passif_report = generate_balance_sheet(company_id, fiscal_year_id, "PCG", db)
    cr_report = generate_income_statement(company_id, fiscal_year_id, "PCG", db)

    def _sum_report(report, *codes) -> Decimal:
        return sum(
            ln.amount for ln in report.lines
            if any(ln.code.startswith(c) for c in codes)
        )

    balance_sheet_data = {
        "actif_immobilise": _sum_report(actif_report, "2"),
        "actif_circulant": _sum_report(actif_report, "3", "4"),
        "tresorerie_actif": _sum_report(actif_report, "5"),
        "total_actif": sum(ln.amount for ln in actif_report.lines if ln.is_total),
        "capitaux_propres": _sum_report(passif_report, "10", "11", "12"),
        "provisions": _sum_report(passif_report, "15"),
        "dettes": _sum_report(passif_report, "16", "17", "40", "42", "43", "44"),
        "total_passif": sum(ln.amount for ln in passif_report.lines if ln.is_total),
    }

    income_data = {
        "chiffre_affaires": _sum_report(cr_report, "70"),
        "valeur_ajoutee": _sum_report(cr_report, "75"),
        "resultat_exploitation": _sum_report(cr_report, "résultat", "76"),
        "resultat_net": sum(ln.amount for ln in cr_report.lines if ln.is_total),
    }

    xbrl_bytes = build_xbrl(
        company_name=company.name,
        siren=company.siren or "000000000",
        siret=company.siret,
        fiscal_year_start=fy.start_date,
        fiscal_year_end=fy.end_date,
        currency=company.currency,
        balance_sheet=balance_sheet_data,
        income_statement=income_data,
    )

    filename = f"xbrl-{company.siren or 'unknown'}-{fy.end_date.year}.xml"
    return Response(
        content=xbrl_bytes,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
