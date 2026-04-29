"""Trésorerie — TFT dynamique, prévisions, Open Banking, rapprochement bancaire."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.db.session import get_session
from src.modules.tresorerie.models import BankAccount, BankTransaction, CashForecast, ReconciliationStatus
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


# ---------------------------------------------------------------------------
# Open Banking — synchronisation DSP2
# ---------------------------------------------------------------------------

class TransactionOut(BaseModel):
    id: str
    transaction_date: date
    label: str
    amount: Decimal
    balance_after: Decimal | None
    reconciliation_status: str
    source: str

    class Config:
        from_attributes = True


@router.post("/bank-accounts/{account_id}/sync", summary="Synchroniser via Open Banking DSP2")
def sync_account(
    account_id: str,
    since: date | None = Query(None, description="Date de début (défaut : J-30)"),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Importe les transactions bancaires via Open Banking (Bridge/Powens).
    Sans credentials Bridge configurés, utilise des données de démonstration."""
    company_id = current_user["company_id"]
    account = db.query(BankAccount).filter_by(id=account_id, company_id=company_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire introuvable")

    from src.config import settings
    from src.modules.tresorerie.open_banking import BridgeAPIClient, sync_bank_account

    client = BridgeAPIClient(
        client_id=getattr(settings, "bridge_client_id", ""),
        client_secret=getattr(settings, "bridge_client_secret", ""),
        access_token=getattr(settings, "bridge_access_token", ""),
    )
    result = sync_bank_account(account, db, since=since, bridge_client=client)
    return result


@router.get("/bank-accounts/{account_id}/transactions", response_model=list[TransactionOut])
def list_transactions(
    account_id: str,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    status: str | None = Query(None, description="NON_RAPPROCHE | RAPPROCHE | ECART"),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[BankTransaction]:
    company_id = current_user["company_id"]
    account = db.query(BankAccount).filter_by(id=account_id, company_id=company_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire introuvable")

    q = db.query(BankTransaction).filter_by(bank_account_id=account_id)
    if date_from:
        q = q.filter(BankTransaction.transaction_date >= date_from)
    if date_to:
        q = q.filter(BankTransaction.transaction_date <= date_to)
    if status:
        q = q.filter(BankTransaction.reconciliation_status == status)
    return q.order_by(BankTransaction.transaction_date.desc()).all()


# ---------------------------------------------------------------------------
# Rapprochement bancaire
# ---------------------------------------------------------------------------

class ReconciliationReportOut(BaseModel):
    bank_account_id: str
    period_start: date
    period_end: date
    total_transactions: int
    matched_exact: int
    matched_fuzzy: int
    unmatched: int
    match_rate: float
    matches: list[dict]


@router.post("/bank-accounts/{account_id}/reconcile", response_model=ReconciliationReportOut)
def reconcile(
    account_id: str,
    period_start: date = Query(...),
    period_end: date = Query(...),
    auto_apply: bool = Query(True, description="Appliquer les matches automatiquement"),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> ReconciliationReportOut:
    """Rapprochement automatique transactions ↔ écritures comptables."""
    company_id = current_user["company_id"]
    account = db.query(BankAccount).filter_by(id=account_id, company_id=company_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire introuvable")

    from src.core.models.journal_entry import JournalEntry, JournalEntryLine
    from src.modules.tresorerie.reconciliation import reconcile_bank_account

    # Charger les écritures du compte 512 (banque) sur la période
    entries = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.company_id == company_id,
            JournalEntry.accounting_date >= period_start,
            JournalEntry.accounting_date <= period_end,
        )
        .all()
    )
    journal_entries_data = [
        {
            "id": e.id,
            "date": e.accounting_date,
            "amount": sum(
                ln.debit for ln in e.lines if str(ln.account_id).startswith("5")
            ) or sum(
                ln.credit for ln in e.lines if str(ln.account_id).startswith("5")
            ),
            "reference": e.entry_number,
            "label": e.description or "",
        }
        for e in entries
    ]

    report = reconcile_bank_account(
        bank_account_id=account_id,
        period_start=period_start,
        period_end=period_end,
        journal_entries=journal_entries_data,
        db=db,
        auto_apply=auto_apply,
    )

    return ReconciliationReportOut(
        bank_account_id=report.bank_account_id,
        period_start=report.period_start,
        period_end=report.period_end,
        total_transactions=report.total_transactions,
        matched_exact=report.matched_exact,
        matched_fuzzy=report.matched_fuzzy,
        unmatched=report.unmatched,
        match_rate=report.match_rate,
        matches=[
            {
                "transaction_id": m.transaction_id,
                "journal_entry_id": m.journal_entry_id,
                "score": round(m.score, 3),
                "match_type": m.match_type,
                "delta_days": m.delta_days,
            }
            for m in report.matches
        ],
    )
