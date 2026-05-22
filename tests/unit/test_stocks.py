"""Tests — moteur de valorisation des stocks (CMUP + FIFO)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.modules.stocks.engine import apply_movement, compute_cmup, fifo_value_out
from src.modules.stocks.models import Article, StockMovement, StockMoveType, ValuationMethod


def make_article(method: str = ValuationMethod.CMUP, qty: float = 0.0, value: float = 0.0) -> Article:
    a = MagicMock(spec=Article)
    a.id = "art-001"
    a.valuation_method = method
    a.stock_qty = Decimal(str(qty))
    a.stock_value = Decimal(str(value))
    a.unit_cost = (Decimal(str(value)) / Decimal(str(qty))).quantize(Decimal("0.0001")) if qty else Decimal("0")
    return a


def make_movement(move_type: str, qty: float, unit_cost: float) -> StockMovement:
    m = MagicMock(spec=StockMovement)
    m.id = "mov-001"
    m.article_id = "art-001"
    m.move_type = move_type
    m.qty = Decimal(str(qty))
    m.unit_cost = Decimal(str(unit_cost))
    m.total_cost = Decimal(str(qty)) * Decimal(str(unit_cost))
    m.move_date = date(2024, 1, 1)
    m.created_at = date(2024, 1, 1)
    return m


class TestComputeCmup:
    def test_first_entry_empty_stock(self):
        article = make_article(qty=0, value=0)
        new_cmup = compute_cmup(article, Decimal("10"), Decimal("100"))
        assert new_cmup == Decimal("100.0000")

    def test_average_two_batches(self):
        # Stock existant : 10 unités à 100 € → value = 1000
        article = make_article(qty=10, value=1000)
        # Entrée : 10 unités à 200 €
        new_cmup = compute_cmup(article, Decimal("10"), Decimal("200"))
        # Attendu : (1000 + 2000) / 20 = 150
        assert new_cmup == Decimal("150.0000")

    def test_zero_total_qty(self):
        article = make_article(qty=0, value=0)
        # qty_in = 0 → CMUP = 0
        result = compute_cmup(article, Decimal("0"), Decimal("100"))
        assert result == Decimal("0")


class TestApplyMovementCmup:
    def test_entree_updates_qty_and_value(self):
        article = make_article(ValuationMethod.CMUP, qty=0, value=0)
        movement = make_movement(StockMoveType.ENTREE, qty=10, unit_cost=50)
        apply_movement(article, movement, db=None)
        assert article.stock_qty == Decimal("10")
        assert article.stock_value == Decimal("500")

    def test_sortie_reduces_stock(self):
        article = make_article(ValuationMethod.CMUP, qty=10, value=500)
        movement = make_movement(StockMoveType.SORTIE, qty=4, unit_cost=50)
        apply_movement(article, movement, db=None)
        assert article.stock_qty == Decimal("6")
        assert article.stock_value == Decimal("300")

    def test_inventaire_forces_qty(self):
        article = make_article(ValuationMethod.CMUP, qty=100, value=5000)
        movement = make_movement(StockMoveType.INVENTAIRE, qty=90, unit_cost=50)
        apply_movement(article, movement, db=None)
        assert article.stock_qty == Decimal("90")
        assert article.stock_value == Decimal("4500")

    def test_stock_value_not_negative_after_sortie(self):
        article = make_article(ValuationMethod.CMUP, qty=5, value=250)
        movement = make_movement(StockMoveType.SORTIE, qty=5, unit_cost=50)
        apply_movement(article, movement, db=None)
        assert article.stock_value >= Decimal("0")


class TestFifoValueOut:
    def test_fifo_single_lot(self):
        article = make_article(ValuationMethod.FIFO, qty=10, value=1000)
        lot = make_movement(StockMoveType.ENTREE, qty=10, unit_cost=100)
        lot.article_id = "art-001"

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value.filter.return_value.order_by.return_value
        mock_query.all.return_value = [lot]

        cost = fifo_value_out(article, Decimal("5"), mock_db)
        assert cost == Decimal("500.00")

    def test_fifo_fallback_on_insufficient_lots(self):
        article = make_article(ValuationMethod.FIFO, qty=5, value=500)
        article.unit_cost = Decimal("100.0000")

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value.filter.return_value.order_by.return_value
        mock_query.all.return_value = []

        cost = fifo_value_out(article, Decimal("3"), mock_db)
        assert cost == Decimal("300.00")
