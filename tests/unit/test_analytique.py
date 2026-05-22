"""Tests — moteur analytique (budget vs réalisé, distribution)."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.analytique.engine import distribute_line, get_budget_vs_realise
from src.modules.analytique.models import AnalyticBudget


def make_budget(month: int, budget: float, realized: float) -> AnalyticBudget:
    b = MagicMock(spec=AnalyticBudget)
    b.period_month = month
    b.account_code = "60"
    b.budget_amount = Decimal(str(budget))
    b.realized_amount = Decimal(str(realized))
    return b


class TestBudgetVsRealise:
    def _mock_db(self, budgets):
        db = MagicMock()
        mock_q = db.query.return_value.filter.return_value.order_by.return_value
        mock_q.all.return_value = budgets
        return db

    def test_returns_all_months(self):
        budgets = [make_budget(m, 1000, 900) for m in range(1, 4)]
        db = self._mock_db(budgets)
        result = get_budget_vs_realise("sec-001", "fy-001", db)
        assert len(result) == 3

    def test_variance_calculation(self):
        db = self._mock_db([make_budget(1, 1000, 1200)])
        result = get_budget_vs_realise("sec-001", "fy-001", db)
        assert result[0]["variance"] == Decimal("200")

    def test_variance_pct_calculation(self):
        db = self._mock_db([make_budget(1, 1000, 1100)])
        result = get_budget_vs_realise("sec-001", "fy-001", db)
        assert result[0]["variance_pct"] == Decimal("10.00")

    def test_variance_pct_none_when_budget_zero(self):
        db = self._mock_db([make_budget(1, 0, 500)])
        result = get_budget_vs_realise("sec-001", "fy-001", db)
        assert result[0]["variance_pct"] is None

    def test_empty_result(self):
        db = self._mock_db([])
        result = get_budget_vs_realise("sec-001", "fy-001", db)
        assert result == []


class TestDistributeLine:
    def test_valid_100_pct(self):
        db = MagicMock()
        items = [
            {"section_id": "s1", "percentage": Decimal("60"), "amount": Decimal("600")},
            {"section_id": "s2", "percentage": Decimal("40"), "amount": Decimal("400")},
        ]
        dists = distribute_line("line-001", items, "fy-001", "co-001", db)
        assert len(dists) == 2

    def test_invalid_pct_raises(self):
        db = MagicMock()
        items = [
            {"section_id": "s1", "percentage": Decimal("60"), "amount": Decimal("600")},
        ]
        with pytest.raises(ValueError, match="100"):
            distribute_line("line-001", items, "fy-001", "co-001", db)
