"""Tests — Achats Fournisseurs."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.achats.models import (
    SupplierInvoice, SupplierInvoiceLine, SupplierInvoiceStatus,
    PurchaseOrder, PurchaseOrderStatus,
)
from src.modules.achats.service import (
    approve_supplier_invoice, compute_invoice_totals,
    get_aged_payables, record_payment, reject_supplier_invoice,
)


def _make_invoice(status: str = SupplierInvoiceStatus.RECUE, total_ttc: Decimal = Decimal("2400.00")) -> SupplierInvoice:
    inv = MagicMock(spec=SupplierInvoice)
    inv.id = str(uuid.uuid4())
    inv.status = status
    inv.total_ttc = total_ttc
    inv.amount_paid = Decimal("0.00")
    inv.balance_due = total_ttc
    inv.lines = []
    inv.due_date = date(2026, 6, 1)
    return inv


def test_approve_invoice():
    mock_db = MagicMock()
    inv = _make_invoice(SupplierInvoiceStatus.RECUE)

    result = approve_supplier_invoice(inv, "user-1", mock_db)
    assert inv.status == SupplierInvoiceStatus.EN_ATTENTE_PAIEMENT
    assert inv.approved_by == "user-1"
    mock_db.commit.assert_called_once()


def test_approve_already_paid_raises():
    mock_db = MagicMock()
    inv = _make_invoice(SupplierInvoiceStatus.PAYEE)
    with pytest.raises(ValueError, match="Impossible"):
        approve_supplier_invoice(inv, "user-1", mock_db)


def test_reject_invoice():
    mock_db = MagicMock()
    inv = _make_invoice(SupplierInvoiceStatus.EN_ATTENTE_VALIDATION)
    reject_supplier_invoice(inv, mock_db)
    assert inv.status == SupplierInvoiceStatus.REFUSEE


def test_record_payment_full():
    mock_db = MagicMock()
    inv = _make_invoice(SupplierInvoiceStatus.EN_ATTENTE_PAIEMENT, Decimal("1200.00"))
    inv.balance_due = Decimal("1200.00")

    record_payment(inv, Decimal("1200.00"), date(2026, 5, 15), "VIREMENT", "REF-001", mock_db)
    assert inv.status == SupplierInvoiceStatus.PAYEE
    assert inv.amount_paid == Decimal("1200.00")


def test_record_payment_partial():
    mock_db = MagicMock()
    inv = _make_invoice(SupplierInvoiceStatus.EN_ATTENTE_PAIEMENT, Decimal("1200.00"))
    inv.balance_due = Decimal("1200.00")

    record_payment(inv, Decimal("600.00"), date(2026, 5, 15), "VIREMENT", None, mock_db)
    assert inv.status == SupplierInvoiceStatus.PARTIELLEMENT_PAYEE
    assert inv.amount_paid == Decimal("600.00")


def test_record_payment_exceeds_balance():
    mock_db = MagicMock()
    inv = _make_invoice(SupplierInvoiceStatus.EN_ATTENTE_PAIEMENT, Decimal("1200.00"))
    inv.balance_due = Decimal("500.00")
    with pytest.raises(ValueError, match="supérieur au solde"):
        record_payment(inv, Decimal("600.00"), date(2026, 5, 15), "VIREMENT", None, mock_db)


def test_record_payment_negative():
    mock_db = MagicMock()
    inv = _make_invoice(SupplierInvoiceStatus.EN_ATTENTE_PAIEMENT)
    inv.balance_due = Decimal("1200.00")
    with pytest.raises(ValueError, match="positif"):
        record_payment(inv, Decimal("-100.00"), date(2026, 5, 15), "VIREMENT", None, mock_db)


def test_compute_invoice_totals():
    inv = MagicMock(spec=SupplierInvoice)
    line1 = MagicMock(spec=SupplierInvoiceLine)
    line1.line_ht = Decimal("1000.00")
    line1.line_tva = Decimal("200.00")
    line2 = MagicMock(spec=SupplierInvoiceLine)
    line2.line_ht = Decimal("500.00")
    line2.line_tva = Decimal("100.00")
    inv.lines = [line1, line2]

    ht, tva, ttc = compute_invoice_totals(inv)
    assert ht == Decimal("1500.00")
    assert tva == Decimal("300.00")
    assert ttc == Decimal("1800.00")


def test_aged_payables_buckets():
    inv1 = MagicMock(spec=SupplierInvoice)
    inv1.supplier_id = "sup-1"
    inv1.balance_due = Decimal("1000.00")
    inv1.due_date = date(2026, 4, 1)  # 28 days ago from 2026-04-29 → 30-day bucket

    inv2 = MagicMock(spec=SupplierInvoice)
    inv2.supplier_id = "sup-1"
    inv2.balance_due = Decimal("500.00")
    inv2.due_date = date(2026, 4, 29)  # today → current

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [inv1, inv2]

    rows = get_aged_payables("company-1", date(2026, 4, 29), mock_db)
    assert len(rows) == 1
    assert rows[0]["supplier_id"] == "sup-1"
    assert rows[0]["total"] == Decimal("1500.00")
