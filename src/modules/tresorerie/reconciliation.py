"""Rapprochement bancaire automatique — algorithme de matching transactions ↔ écritures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from src.modules.tresorerie.models import BankTransaction, ReconciliationStatus


@dataclass
class MatchResult:
    transaction_id: str
    journal_entry_id: str | None
    score: float          # 0.0–1.0
    match_type: str       # EXACT | FUZZY | AMOUNT_ONLY | UNMATCHED
    delta_days: int = 0
    amount_diff: Decimal = Decimal("0")


@dataclass
class ReconciliationReport:
    bank_account_id: str
    period_start: date
    period_end: date
    total_transactions: int = 0
    matched_exact: int = 0
    matched_fuzzy: int = 0
    unmatched: int = 0
    matches: list[MatchResult] = field(default_factory=list)

    @property
    def match_rate(self) -> float:
        if self.total_transactions == 0:
            return 0.0
        return (self.matched_exact + self.matched_fuzzy) / self.total_transactions


def _amount_score(tx_amount: Decimal, entry_amount: Decimal) -> float:
    if tx_amount == entry_amount:
        return 1.0
    diff = abs(tx_amount - entry_amount)
    if tx_amount != 0 and diff / abs(tx_amount) < Decimal("0.01"):
        return 0.9
    return 0.0


def _date_score(tx_date: date, entry_date: date, tolerance_days: int = 5) -> tuple[float, int]:
    delta = abs((tx_date - entry_date).days)
    if delta == 0:
        return 1.0, 0
    if delta <= tolerance_days:
        return 1.0 - delta / (tolerance_days * 2), delta
    return 0.0, delta


def _label_score(tx_label: str, entry_ref: str | None) -> float:
    if not entry_ref:
        return 0.0
    label_up = tx_label.upper()
    ref_up = entry_ref.upper()
    if ref_up in label_up or label_up in ref_up:
        return 1.0
    # Common tokens match
    tokens_ref = set(ref_up.split())
    tokens_lbl = set(label_up.split())
    common = tokens_ref & tokens_lbl
    if not tokens_ref:
        return 0.0
    return len(common) / len(tokens_ref)


def match_transaction(
    tx: BankTransaction,
    journal_entries: list[dict[str, Any]],
    tolerance_days: int = 5,
) -> MatchResult:
    """
    Tente de matcher une transaction bancaire avec une écriture comptable.
    journal_entries: list of dicts {id, date, amount, reference, label}
    """
    best: MatchResult | None = None

    for entry in journal_entries:
        entry_amount = Decimal(str(entry["amount"]))
        entry_date = entry["date"] if isinstance(entry["date"], date) else date.fromisoformat(str(entry["date"]))

        amt_score = _amount_score(tx.amount, entry_amount)
        if amt_score == 0:
            continue

        date_score, delta = _date_score(tx.transaction_date, entry_date, tolerance_days)
        lbl_score = _label_score(tx.label, entry.get("reference") or entry.get("label", ""))

        score = amt_score * 0.5 + date_score * 0.3 + lbl_score * 0.2

        match_type = "UNMATCHED"
        if amt_score == 1.0 and date_score == 1.0 and delta == 0:
            match_type = "EXACT"
        elif score >= 0.7:
            match_type = "FUZZY"
        elif amt_score >= 0.9 and score >= 0.5:
            match_type = "AMOUNT_ONLY"

        if match_type == "UNMATCHED":
            continue

        result = MatchResult(
            transaction_id=tx.id,
            journal_entry_id=entry["id"],
            score=score,
            match_type=match_type,
            delta_days=delta,
            amount_diff=abs(tx.amount - entry_amount),
        )
        if best is None or result.score > best.score:
            best = result

    return best or MatchResult(
        transaction_id=tx.id,
        journal_entry_id=None,
        score=0.0,
        match_type="UNMATCHED",
    )


def reconcile_bank_account(
    bank_account_id: str,
    period_start: date,
    period_end: date,
    journal_entries: list[dict[str, Any]],
    db: Session,
    auto_apply: bool = True,
) -> ReconciliationReport:
    """
    Rapproche toutes les transactions non rapprochées d'un compte sur la période.
    Si auto_apply=True, met à jour le statut en base pour les matches EXACT.
    """
    transactions = (
        db.query(BankTransaction)
        .filter(
            BankTransaction.bank_account_id == bank_account_id,
            BankTransaction.transaction_date >= period_start,
            BankTransaction.transaction_date <= period_end,
            BankTransaction.reconciliation_status == ReconciliationStatus.NON_RAPPROCHE,
        )
        .all()
    )

    report = ReconciliationReport(
        bank_account_id=bank_account_id,
        period_start=period_start,
        period_end=period_end,
        total_transactions=len(transactions),
    )

    used_entry_ids: set[str] = set()

    for tx in transactions:
        available = [e for e in journal_entries if e["id"] not in used_entry_ids]
        result = match_transaction(tx, available)
        report.matches.append(result)

        if result.match_type == "EXACT":
            report.matched_exact += 1
            if auto_apply and result.journal_entry_id:
                tx.reconciliation_status = ReconciliationStatus.RAPPROCHE
                tx.journal_entry_id = result.journal_entry_id
                tx.reconciled_at = date.today()
                used_entry_ids.add(result.journal_entry_id)
        elif result.match_type in ("FUZZY", "AMOUNT_ONLY"):
            report.matched_fuzzy += 1
            if auto_apply and result.journal_entry_id:
                tx.reconciliation_status = ReconciliationStatus.RAPPROCHE
                tx.journal_entry_id = result.journal_entry_id
                tx.reconciled_at = date.today()
                used_entry_ids.add(result.journal_entry_id)
        else:
            report.unmatched += 1

    if auto_apply:
        db.commit()

    return report
