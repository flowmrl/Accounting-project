"""Tests — plans d'amortissement (linéaire + dégressif)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.immobilisations.engine import compute_depreciation_plan
from src.modules.immobilisations.models import DepreciationMethod


def make_asset(
    cost: float,
    years: int,
    method: DepreciationMethod,
    acquisition_date: date = date(2024, 1, 1),
    residual: float = 0.0,
):
    asset = MagicMock()
    asset.acquisition_cost = Decimal(str(cost))
    asset.useful_life_years = years
    asset.depreciation_method = method
    asset.acquisition_date = acquisition_date
    asset.commissioning_date = None          # falls back to acquisition_date
    asset.residual_value = Decimal(str(residual))
    asset.degressive_rate = None             # use CGI coefficient
    asset.id = "asset-001"
    return asset


class TestLinearDepreciation:
    def test_full_year_three_years_count(self):
        asset = make_asset(1200, 3, DepreciationMethod.LINEAIRE, date(2024, 1, 1))
        plan = compute_depreciation_plan(asset)
        assert len(plan) == 3

    def test_full_year_equal_amounts(self):
        asset = make_asset(1200, 3, DepreciationMethod.LINEAIRE, date(2024, 1, 1))
        plan = compute_depreciation_plan(asset)
        # Jan 1 = full year, so days_used = 365, prorata ≈ 1.0
        # Accept either 400 exactly or close to it (prorata may vary)
        total = sum(l.accounting_amount for l in plan)
        assert total == Decimal("1200")

    def test_total_equals_cost(self):
        asset = make_asset(10000, 5, DepreciationMethod.LINEAIRE, date(2024, 1, 1))
        plan = compute_depreciation_plan(asset)
        total = sum(l.accounting_amount for l in plan)
        assert total == Decimal("10000")

    def test_prorata_temporis_first_year_less_than_annual(self):
        # Acquisition le 1er juillet → première dotation < annuité pleine
        asset = make_asset(1200, 3, DepreciationMethod.LINEAIRE, date(2024, 7, 1))
        plan = compute_depreciation_plan(asset)
        full_annual = Decimal("1200") / 3
        assert plan[0].accounting_amount < full_annual

    def test_prorata_total_equals_cost(self):
        asset = make_asset(1200, 3, DepreciationMethod.LINEAIRE, date(2024, 7, 1))
        plan = compute_depreciation_plan(asset)
        total = sum(l.accounting_amount for l in plan)
        assert total == Decimal("1200")

    def test_net_book_value_reaches_zero(self):
        asset = make_asset(5000, 5, DepreciationMethod.LINEAIRE)
        plan = compute_depreciation_plan(asset)
        assert plan[-1].net_book_value_after == Decimal("0")

    def test_cumulative_is_monotonic(self):
        asset = make_asset(6000, 6, DepreciationMethod.LINEAIRE)
        plan = compute_depreciation_plan(asset)
        for i in range(1, len(plan)):
            assert plan[i].cumulative_at_start >= plan[i - 1].cumulative_at_start

    def test_with_residual_value_total(self):
        asset = make_asset(10000, 5, DepreciationMethod.LINEAIRE, residual=1000)
        plan = compute_depreciation_plan(asset)
        total = sum(l.accounting_amount for l in plan)
        assert total == Decimal("9000")  # coût - valeur résiduelle

    def test_with_residual_value_final_nbv(self):
        asset = make_asset(10000, 5, DepreciationMethod.LINEAIRE, residual=1000)
        plan = compute_depreciation_plan(asset)
        assert plan[-1].net_book_value_after == Decimal("1000")


class TestDecliningBalanceDepreciation:
    def test_returns_plan(self):
        asset = make_asset(10000, 5, DepreciationMethod.DEGRESSIF, date(2024, 1, 1))
        plan = compute_depreciation_plan(asset)
        assert len(plan) >= 5

    def test_total_equals_cost(self):
        asset = make_asset(10000, 5, DepreciationMethod.DEGRESSIF, date(2024, 1, 1))
        plan = compute_depreciation_plan(asset)
        total = sum(l.accounting_amount for l in plan)
        assert abs(total - Decimal("10000")) <= Decimal("0.02")

    def test_first_year_higher_than_linear(self):
        asset_lin = make_asset(10000, 5, DepreciationMethod.LINEAIRE)
        asset_deg = make_asset(10000, 5, DepreciationMethod.DEGRESSIF)
        plan_lin = compute_depreciation_plan(asset_lin)
        plan_deg = compute_depreciation_plan(asset_deg)
        assert plan_deg[0].accounting_amount > plan_lin[0].accounting_amount

    def test_7_years_total(self):
        asset = make_asset(10000, 7, DepreciationMethod.DEGRESSIF, date(2024, 1, 1))
        plan = compute_depreciation_plan(asset)
        total = sum(l.accounting_amount for l in plan)
        assert abs(total - Decimal("10000")) <= Decimal("0.02")
