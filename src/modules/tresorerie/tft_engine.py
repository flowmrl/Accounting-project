"""
TFT dynamique — Tableau de Flux de Trésorerie quotidien.

Calcule le TFT en temps réel depuis :
  - Les transactions bancaires rapprochées (flux réels)
  - Les factures à échoir (flux prévisionnels)
  - Les prévisions manuelles
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from .models import BankAccount, BankTransaction, CashFlowCategory, CashForecast, ReconciliationStatus

ZERO = Decimal("0.00")


@dataclass
class DailyBalance:
    day: date
    opening: Decimal
    inflows: Decimal = ZERO
    outflows: Decimal = ZERO
    forecast_inflows: Decimal = ZERO
    forecast_outflows: Decimal = ZERO

    @property
    def closing_actual(self) -> Decimal:
        return self.opening + self.inflows - self.outflows

    @property
    def closing_forecast(self) -> Decimal:
        return self.closing_actual + self.forecast_inflows - self.forecast_outflows


@dataclass
class TFTResult:
    """Résultat du TFT sur une période."""
    periode_debut: date
    periode_fin: date
    solde_ouverture: Decimal
    solde_cloture: Decimal

    flux_exploitation: Decimal = ZERO
    flux_investissement: Decimal = ZERO
    flux_financement: Decimal = ZERO

    daily_balances: list[DailyBalance] = field(default_factory=list)
    forecast_balances: list[DailyBalance] = field(default_factory=list)

    @property
    def variation_nette(self) -> Decimal:
        return self.flux_exploitation + self.flux_investissement + self.flux_financement

    def to_chart_data(self) -> dict:
        """
        Données formatées pour graphiques front-end (Chart.js / ApexCharts).
        Returns labels (dates) + datasets (actuel, prévisionnel, waterfall).
        """
        all_days = self.daily_balances + self.forecast_balances
        return {
            "labels": [str(d.day) for d in all_days],
            "actual": [float(d.closing_actual) for d in self.daily_balances],
            "forecast": [float(d.closing_forecast) for d in self.forecast_balances],
            "inflows": [float(d.inflows + d.forecast_inflows) for d in all_days],
            "outflows": [float(-(d.outflows + d.forecast_outflows)) for d in all_days],
            "waterfall": _build_waterfall(all_days),
            "flux": {
                "exploitation": float(self.flux_exploitation),
                "investissement": float(self.flux_investissement),
                "financement": float(self.flux_financement),
            },
        }


def _build_waterfall(days: list[DailyBalance]) -> list[dict]:
    result = []
    for d in days:
        net = (d.inflows + d.forecast_inflows) - (d.outflows + d.forecast_outflows)
        result.append({"date": str(d.day), "net": float(net), "cumulative": float(d.closing_forecast)})
    return result


def compute_daily_tft(
    session: Session,
    company_id: str,
    date_from: date,
    date_to: date,
    bank_account_id: str | None = None,
) -> TFTResult:
    """
    Calcule le TFT quotidien sur la période [date_from, date_to].
    Combine transactions réelles + prévisions.
    """
    # Solde d'ouverture
    opening = _get_opening_balance(session, company_id, date_from, bank_account_id)

    # Transactions réelles rapprochées
    tx_query = (
        session.query(BankTransaction)
        .join(BankAccount, BankTransaction.bank_account_id == BankAccount.id)
        .filter(
            BankAccount.company_id == company_id,
            BankTransaction.transaction_date >= date_from,
            BankTransaction.transaction_date <= date_to,
            BankTransaction.reconciliation_status == ReconciliationStatus.RAPPROCHE,
        )
    )
    if bank_account_id:
        tx_query = tx_query.filter(BankTransaction.bank_account_id == bank_account_id)

    transactions = tx_query.order_by(BankTransaction.transaction_date).all()

    # Prévisions
    forecast_query = (
        session.query(CashForecast)
        .filter(
            CashForecast.company_id == company_id,
            CashForecast.forecast_date >= date_from,
            CashForecast.forecast_date <= date_to,
        )
    )
    if bank_account_id:
        forecast_query = forecast_query.filter(CashForecast.bank_account_id == bank_account_id)

    forecasts = forecast_query.order_by(CashForecast.forecast_date).all()

    # Construction du TFT jour par jour
    result = TFTResult(
        periode_debut=date_from,
        periode_fin=date_to,
        solde_ouverture=opening,
        solde_cloture=opening,
    )

    # Indexer par date
    tx_by_day: dict[date, list[BankTransaction]] = {}
    for tx in transactions:
        tx_by_day.setdefault(tx.transaction_date, []).append(tx)

    fc_by_day: dict[date, list[CashForecast]] = {}
    for fc in forecasts:
        fc_by_day.setdefault(fc.forecast_date, []).append(fc)

    running = opening
    today = date.today()
    current = date_from

    while current <= date_to:
        day_txs = tx_by_day.get(current, [])
        day_fcs = fc_by_day.get(current, [])

        inflows = sum(tx.amount for tx in day_txs if tx.amount > ZERO)
        outflows = abs(sum(tx.amount for tx in day_txs if tx.amount < ZERO))
        fc_in = sum(fc.amount for fc in day_fcs if fc.amount > ZERO)
        fc_out = abs(sum(fc.amount for fc in day_fcs if fc.amount < ZERO))

        db = DailyBalance(
            day=current, opening=running,
            inflows=inflows, outflows=outflows,
            forecast_inflows=fc_in, forecast_outflows=fc_out,
        )

        if current <= today:
            result.daily_balances.append(db)
            running = db.closing_actual
        else:
            result.forecast_balances.append(db)

        # Agrégation par catégorie
        for tx in day_txs:
            cat = tx.cash_flow_category
            if cat == CashFlowCategory.EXPLOITATION:
                result.flux_exploitation += tx.amount
            elif cat == CashFlowCategory.INVESTISSEMENT:
                result.flux_investissement += tx.amount
            elif cat == CashFlowCategory.FINANCEMENT:
                result.flux_financement += tx.amount
            else:
                result.flux_exploitation += tx.amount  # Défaut

        current += timedelta(days=1)

    result.solde_cloture = running
    return result


def _get_opening_balance(
    session: Session,
    company_id: str,
    as_of: date,
    bank_account_id: str | None,
) -> Decimal:
    """Solde de trésorerie à la date d'ouverture depuis le dernier rapprochement."""
    q = (
        session.query(BankAccount)
        .filter(BankAccount.company_id == company_id, BankAccount.is_active.is_(True))
    )
    if bank_account_id:
        q = q.filter(BankAccount.id == bank_account_id)

    total = ZERO
    for ba in q.all():
        total += ba.bank_balance or ZERO
    return total


def build_forecast_from_invoices(
    session: Session,
    company_id: str,
    horizon_days: int = 90,
) -> list[CashForecast]:
    """
    Génère automatiquement les prévisions depuis les factures à échoir.
    Retourne des CashForecast non persistés.
    """
    from src.modules.facturation.models import DocumentStatus, DocumentType, Invoice

    today = date.today()
    horizon = today + timedelta(days=horizon_days)

    invoices = session.query(Invoice).filter(
        Invoice.company_id == company_id,
        Invoice.document_type.in_([DocumentType.FACTURE]),
        Invoice.status.in_([DocumentStatus.ENVOYE, DocumentStatus.PARTIELLEMENT_PAYE]),
        Invoice.due_date <= horizon,
        Invoice.due_date >= today,
    ).all()

    forecasts = []
    for inv in invoices:
        if inv.balance_due <= ZERO:
            continue
        forecasts.append(CashForecast(
            company_id=company_id,
            forecast_date=inv.due_date,
            label=f"Règlement {inv.number} — {inv.customer_name}",
            amount=inv.balance_due,
            cash_flow_category=CashFlowCategory.EXPLOITATION,
            is_confirmed=False,
            source="INVOICE",
            source_id=inv.id,
        ))

    return forecasts
