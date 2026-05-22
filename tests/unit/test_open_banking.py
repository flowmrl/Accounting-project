"""Tests — Open Banking + Rapprochement bancaire."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.modules.tresorerie.open_banking import BridgeAPIClient, import_transactions
from src.modules.tresorerie.reconciliation import (
    MatchResult,
    ReconciliationReport,
    match_transaction,
    reconcile_bank_account,
)


# ---------------------------------------------------------------------------
# BridgeAPIClient — mock mode
# ---------------------------------------------------------------------------

def test_bridge_mock_returns_transactions():
    client = BridgeAPIClient()  # no credentials → mock
    txs = client.get_transactions("any-id")
    assert len(txs) > 0
    assert "label" in txs[0]
    assert "amount" in txs[0]
    assert "date" in txs[0]


def test_bridge_mock_respects_limit():
    client = BridgeAPIClient()
    txs = client.get_transactions("any-id", limit=5)
    assert len(txs) <= 5


def test_bridge_is_not_configured():
    client = BridgeAPIClient()
    assert not client._is_configured


def test_bridge_is_configured():
    client = BridgeAPIClient(client_id="abc", access_token="tok")
    assert client._is_configured


# ---------------------------------------------------------------------------
# import_transactions
# ---------------------------------------------------------------------------

def test_import_transactions_new():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    txs = [
        {"date": "2026-05-01", "label": "Virement client", "amount": 1500.0, "balance_after": 16500.0},
        {"date": "2026-05-02", "label": "PRLV EDF", "amount": -320.0, "balance_after": 16180.0},
    ]
    result = import_transactions("acct-1", txs, mock_db)
    assert result["imported"] == 2
    assert result["skipped"] == 0
    assert mock_db.add.call_count == 2


def test_import_transactions_deduplicate():
    from src.modules.tresorerie.models import BankTransaction
    mock_db = MagicMock()
    existing = BankTransaction(
        id="existing",
        bank_account_id="acct-1",
        transaction_date=date(2026, 5, 1),
        label="Virement client",
        amount=Decimal("1500.00"),
    )
    mock_db.query.return_value.filter.return_value.first.return_value = existing

    txs = [{"date": "2026-05-01", "label": "Virement client", "amount": 1500.0}]
    result = import_transactions("acct-1", txs, mock_db)
    assert result["imported"] == 0
    assert result["skipped"] == 1


# ---------------------------------------------------------------------------
# match_transaction
# ---------------------------------------------------------------------------

def _make_tx(tx_date: date, amount: Decimal, label: str) -> object:
    tx = MagicMock()
    tx.id = "tx-1"
    tx.transaction_date = tx_date
    tx.amount = amount
    tx.label = label
    return tx


def test_match_exact():
    tx = _make_tx(date(2026, 5, 1), Decimal("1500.00"), "Virement SARL Martin FAC-2026-042")
    entries = [{
        "id": "entry-1",
        "date": date(2026, 5, 1),
        "amount": Decimal("1500.00"),
        "reference": "FAC-2026-042",
        "label": "Facture SARL Martin",
    }]
    result = match_transaction(tx, entries)
    assert result.match_type == "EXACT"
    assert result.journal_entry_id == "entry-1"
    assert result.score >= 0.9


def test_match_fuzzy_date_tolerance():
    tx = _make_tx(date(2026, 5, 3), Decimal("1500.00"), "Virement client Martin")
    entries = [{
        "id": "entry-1",
        "date": date(2026, 5, 1),
        "amount": Decimal("1500.00"),
        "reference": "Martin",
        "label": "",
    }]
    result = match_transaction(tx, entries)
    assert result.match_type in ("FUZZY", "AMOUNT_ONLY", "EXACT")
    assert result.journal_entry_id == "entry-1"


def test_no_match_wrong_amount():
    tx = _make_tx(date(2026, 5, 1), Decimal("999.00"), "Random transaction")
    entries = [{
        "id": "entry-1",
        "date": date(2026, 5, 1),
        "amount": Decimal("1500.00"),
        "reference": "FAC-001",
        "label": "",
    }]
    result = match_transaction(tx, entries)
    assert result.match_type == "UNMATCHED"
    assert result.journal_entry_id is None


def test_no_match_empty_entries():
    tx = _make_tx(date(2026, 5, 1), Decimal("500.00"), "CB Monoprix")
    result = match_transaction(tx, [])
    assert result.match_type == "UNMATCHED"


# ---------------------------------------------------------------------------
# reconcile_bank_account
# ---------------------------------------------------------------------------

def test_reconcile_report_structure():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

    report = reconcile_bank_account(
        bank_account_id="acct-1",
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 31),
        journal_entries=[],
        db=mock_db,
        auto_apply=False,
    )
    assert isinstance(report, ReconciliationReport)
    assert report.total_transactions == 0
    assert report.match_rate == 0.0
