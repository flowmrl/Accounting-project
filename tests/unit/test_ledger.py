"""Tests — moteur d'écritures comptables (validation + équilibre)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.core.engine.ledger import LedgerError, LineInput, validate_lines


def make_line(code: str, debit: float = 0, credit: float = 0, label: str = "Test") -> LineInput:
    return LineInput(
        account_code=code,
        label=label,
        debit=Decimal(str(debit)),
        credit=Decimal(str(credit)),
    )


class TestValidateLines:
    def test_balanced_entry_passes(self):
        lines = [make_line("512", debit=1000), make_line("706", credit=1000)]
        validate_lines(lines)  # doit ne pas lever d'exception

    def test_unbalanced_raises(self):
        lines = [make_line("512", debit=1000), make_line("706", credit=900)]
        with pytest.raises(LedgerError, match="déséquilibrée|balance|équilibre"):
            validate_lines(lines)

    def test_single_line_fails(self):
        with pytest.raises(LedgerError):
            validate_lines([make_line("512", debit=500)])

    def test_negative_debit_fails(self):
        lines = [make_line("512", debit=-100), make_line("706", credit=-100)]
        with pytest.raises(LedgerError):
            validate_lines(lines)

    def test_debit_and_credit_on_same_line_fails(self):
        lines = [
            LineInput(account_code="512", label="both", debit=Decimal("100"), credit=Decimal("50")),
            make_line("706", credit=50),
        ]
        with pytest.raises(LedgerError):
            validate_lines(lines)

    def test_three_line_balanced(self):
        lines = [
            make_line("401", credit=1200),
            make_line("60", debit=1000),
            make_line("44566", debit=200),
        ]
        validate_lines(lines)  # doit passer

    def test_large_amount_balanced(self):
        lines = [make_line("512", debit=1_000_000), make_line("706", credit=1_000_000)]
        validate_lines(lines)


class TestLineInput:
    def test_default_values(self):
        line = LineInput(account_code="512", label="test")
        assert line.debit == Decimal("0")
        assert line.credit == Decimal("0")
        assert line.vat_code is None

    def test_with_analytic_account(self):
        line = LineInput(
            account_code="60", label="achat",
            debit=Decimal("500"), analytic_account_id="axis-001",
        )
        assert line.analytic_account_id == "axis-001"
