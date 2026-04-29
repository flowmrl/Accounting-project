"""Module Achats Fournisseurs — fournisseurs, commandes, factures, paiements.

Revision ID: 005
Revises: 004
Create Date: 2026-04-29 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suppliers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("siren", sa.String(9)),
        sa.Column("siret", sa.String(14)),
        sa.Column("tva_intracom", sa.String(20)),
        sa.Column("address", sa.Text),
        sa.Column("city", sa.String(100)),
        sa.Column("zip_code", sa.String(10)),
        sa.Column("country", sa.String(2), server_default="FR"),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(30)),
        sa.Column("website", sa.String(255)),
        sa.Column("iban", sa.String(34)),
        sa.Column("bic", sa.String(11)),
        sa.Column("account_code", sa.String(20), server_default="401"),
        sa.Column("payment_terms_days", sa.Integer, server_default="30"),
        sa.Column("status", sa.String(20), server_default="ACTIF"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", sa.String(36), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.String(50)),
        sa.Column("status", sa.String(30), server_default="BROUILLON"),
        sa.Column("order_date", sa.Date, nullable=False),
        sa.Column("expected_delivery_date", sa.Date),
        sa.Column("subtotal_ht", sa.Numeric(20, 2), server_default="0.00"),
        sa.Column("total_tva", sa.Numeric(20, 2), server_default="0.00"),
        sa.Column("total_ttc", sa.Numeric(20, 2), server_default="0.00"),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "purchase_order_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 4), server_default="1.0000"),
        sa.Column("unit_price_ht", sa.Numeric(20, 4), nullable=False),
        sa.Column("vat_rate", sa.Numeric(6, 2), server_default="20.00"),
        sa.Column("account_code", sa.String(20), server_default="607"),
        sa.Column("received_qty", sa.Numeric(12, 4), server_default="0.0000"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "supplier_invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", sa.String(36), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_order_id", sa.String(36), sa.ForeignKey("purchase_orders.id", ondelete="SET NULL")),
        sa.Column("supplier_ref", sa.String(100)),
        sa.Column("our_ref", sa.String(100)),
        sa.Column("status", sa.String(30), server_default="RECUE"),
        sa.Column("invoice_date", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date),
        sa.Column("subtotal_ht", sa.Numeric(20, 2), server_default="0.00"),
        sa.Column("total_tva", sa.Numeric(20, 2), server_default="0.00"),
        sa.Column("total_ttc", sa.Numeric(20, 2), server_default="0.00"),
        sa.Column("amount_paid", sa.Numeric(20, 2), server_default="0.00"),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("journal_entry_id", sa.String(36)),
        sa.Column("approved_by", sa.String(36)),
        sa.Column("approved_at", sa.Date),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "supplier_invoice_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("supplier_invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 4), server_default="1.0000"),
        sa.Column("unit_price_ht", sa.Numeric(20, 4), nullable=False),
        sa.Column("vat_rate", sa.Numeric(6, 2), server_default="20.00"),
        sa.Column("account_code", sa.String(20), server_default="607"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "supplier_payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("supplier_invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("payment_date", sa.Date, nullable=False),
        sa.Column("payment_method", sa.String(30), server_default="VIREMENT"),
        sa.Column("reference", sa.String(100)),
        sa.Column("status", sa.String(20), server_default="PLANIFIE"),
        sa.Column("bank_account_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("supplier_payments")
    op.drop_table("supplier_invoice_lines")
    op.drop_table("supplier_invoices")
    op.drop_table("purchase_order_lines")
    op.drop_table("purchase_orders")
    op.drop_table("suppliers")
