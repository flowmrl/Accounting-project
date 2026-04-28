"""Trésorerie — TFT dynamique, prévisions, données graphiques."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.db.session import get_session
from src.modules.tresorerie.models import BankAccount, BankTransaction, CashForecast
from src.modules.tresorerie.tft_engine import build_forecast_from_invoices, compute_daily_tft

router = APIRouter(prefix="/treasury", tags=["Trésorerie"])


class DailyBalanceOut(BaseModel):
    date: date
    opening: Decimal
    inflows: Decimal
    outflows: Decimal
    forecast_inflows: Decimal
    forecast_outflows: Decimal
    closing_actual: Decimal
    closing_forecast: Decimal


class TFTChartData(BaseModel):
    labels: list[str]
    actual: list[float]
    forecast: list[float]
    inflows: list[float]
    outflows: list[float]
    waterfall: list[dict]


class TFTResult(BaseModel):
    period_start: date
    period_end: date
    daily_balances: list[DailyBalanceOut]
    chart_data: TFTChartData
    summary: dict


class BankAccountOut(BaseModel):
    id: str
    name: str
    iban: str | None
    currency: str
    account_code: str
    current_balance: Decimal

    class Config:
        from_attributes = True


@router.get("/tft", response_model=TFTResult)
def get_tft(
    date_from: date = Query(...),
    date_to: date = Query(...),
    bank_account_id: str | None = Query(None),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> TFTResult:
    """Tableau de Flux de Trésorerie dynamique avec données graphiques."""
    company_id = current_user["company_id"]
    result = compute_daily_tft(company_id, date_from, date_to, db, bank_account_id=bank_account_id)
    chart = result.to_chart_data()

    daily = [
        DailyBalanceOut(
            date=d.date,
            opening=d.opening,
            inflows=d.inflows,
            outflows=d.outflows,
            forecast_inflows=d.forecast_inflows,
            forecast_outflows=d.forecast_outflows,
            closing_actual=d.closing_actual,
            closing_forecast=d.closing_forecast,
        )
        for d in result.daily_balances
    ]

    return TFTResult(
        period_start=date_from,
        period_end=date_to,
        daily_balances=daily,
        chart_data=TFTChartData(
            labels=chart["labels"],
            actual=chart["actual"],
            forecast=chart["forecast"],
            inflows=chart["inflows"],
            outflows=chart["outflows"],
            waterfall=chart["waterfall"],
        ),
        summary={
            "opening_balance": float(result.daily_balances[0].opening) if result.daily_balances else 0,
            "closing_actual": float(result.daily_balances[-1].closing_actual) if result.daily_balances else 0,
            "closing_forecast": float(result.daily_balances[-1].closing_forecast) if result.daily_balances else 0,
            "total_inflows": float(sum(d.inflows for d in result.daily_balances)),
            "total_outflows": float(sum(d.outflows for d in result.daily_balances)),
        },
    )


@router.get("/bank-accounts", response_model=list[BankAccountOut])
def list_bank_accounts(
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[BankAccountOut]:
    company_id = current_user["company_id"]
    return db.query(BankAccount).filter_by(company_id=company_id, is_active=True).all()


@router.post("/forecast/from-invoices")
def build_forecast(
    horizon_days: int = Query(90),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Génère des prévisions de trésorerie depuis les factures non payées."""
    company_id = current_user["company_id"]
    forecasts = build_forecast_from_invoices(company_id, horizon_days, db)
    db.add_all(forecasts)
    db.commit()
    return {"created": len(forecasts), "message": f"{len(forecasts)} prévisions générées"}
