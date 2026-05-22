"""Modules métier — immobilisations, tax, facturation, trésorerie, consolidation.

Revision ID: 002
Revises: 001
Create Date: 2026-04-26 00:01:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- fixed_assets + depreciation_lines ---
    op.create_table(
        "fixed_assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("reference", sa.String(100)),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="EN_SERVICE"),
        sa.Column("acquisition_date", sa.Date, nullable=False),
        sa.Column("acquisition_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("residual_value", sa.Numeric(18, 2), server_default="0"),
        sa.Column("useful_life_years", sa.Integer, nullable=False),
        sa.Column("depreciation_method", sa.String(20), nullable=False),
        sa.Column("account_code", sa.String(20), nullable=False),
        sa.Column("depreciation_account_code", sa.String(20), nullable=False),
        sa.Column("accumulated_depreciation_account_code", sa.String(20), nullable=False),
        sa.Column("journal_code", sa.String(10), server_default="IMMOBILISATIONS"),
        sa.Column("location", sa.String(255)),
        sa.Column("serial_number", sa.String(100)),
        sa.Column("disposal_date", sa.Date),
        sa.Column("disposal_value", sa.Numeric(18, 2)),
    )
    op.create_table(
        "depreciation_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("fixed_assets.id"), nullable=False),
        sa.Column("fiscal_year_id", sa.String(36), nullable=False),
        sa.Column("period_date", sa.Date, nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("accounting_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("exceptional_amount", sa.Numeric(18, 2), server_default="0"),
        sa.Column("cumulative", sa.Numeric(18, 2), nullable=False),
        sa.Column("net_book_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("is_posted", sa.Boolean, server_default="false"),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("journal_entries.id")),
    )

    # --- tax: tva_declarations, is_declarations, deferred_taxes ---
    op.create_table(
        "tva_declarations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("declaration_type", sa.String(10), server_default="CA3"),
        sa.Column("total_collectee", sa.Numeric(18, 2), server_default="0"),
        sa.Column("total_deductible", sa.Numeric(18, 2), server_default="0"),
        sa.Column("solde_tva", sa.Numeric(18, 2), server_default="0"),
        sa.Column("status", sa.String(20), server_default="BROUILLON"),
        sa.Column("submitted_at", sa.DateTime),
        sa.Column("snapshot", sa.JSON),
    )
    op.create_table(
        "is_declarations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("fiscal_year_id", sa.String(36), sa.ForeignKey("fiscal_years.id"), nullable=False),
        sa.Column("resultat_comptable", sa.Numeric(18, 2), nullable=False),
        sa.Column("resultat_fiscal", sa.Numeric(18, 2), nullable=False),
        sa.Column("base_is", sa.Numeric(18, 2), nullable=False),
        sa.Column("is_taux_reduit", sa.Numeric(18, 2), server_default="0"),
        sa.Column("is_taux_normal", sa.Numeric(18, 2), server_default="0"),
        sa.Column("is_total", sa.Numeric(18, 2), server_default="0"),
        sa.Column("status", sa.String(20), server_default="BROUILLON"),
    )
    op.create_table(
        "deferred_taxes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("fiscal_year_id", sa.String(36), sa.ForeignKey("fiscal_years.id"), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("tax_type", sa.String(10), nullable=False),
        sa.Column("base_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), server_default="25.00"),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("origin", sa.String(50)),
    )

    # --- invoices + lines + reminders ---
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("number", sa.String(30)),
        sa.Column("invoice_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="BROUILLON"),
        sa.Column("customer_id", sa.String(36), nullable=False),
        sa.Column("issue_date", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("fiscal_year_id", sa.String(36), sa.ForeignKey("fiscal_years.id"), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("total_ht", sa.Numeric(18, 2), server_default="0"),
        sa.Column("total_tva", sa.Numeric(18, 2), server_default="0"),
        sa.Column("total_ttc", sa.Numeric(18, 2), server_default="0"),
        sa.Column("notes", sa.Text),
        sa.Column("einvoicing_format", sa.String(20)),
        sa.Column("einvoicing_payload", sa.JSON),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("journal_entries.id")),
        sa.Column("original_invoice_id", sa.String(36), sa.ForeignKey("invoices.id")),
    )
    op.create_index("ix_invoices_company", "invoices", ["company_id"])
    op.create_table(
        "invoice_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 4), server_default="1"),
        sa.Column("unit_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("vat_rate", sa.Numeric(5, 2), server_default="20.00"),
        sa.Column("account_code", sa.String(20)),
        sa.Column("line_order", sa.Integer, server_default="0"),
    )
    op.create_table(
        "payment_reminders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("reminder_level", sa.Integer, nullable=False),
        sa.Column("sent_at", sa.DateTime),
        sa.Column("method", sa.String(20)),
    )

    # --- tresorerie ---
    op.create_table(
        "bank_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("iban", sa.String(34)),
        sa.Column("bic", sa.String(11)),
        sa.Column("bank_name", sa.String(255)),
        sa.Column("account_code", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("current_balance", sa.Numeric(18, 2), server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
    )
    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("bank_account_id", sa.String(36), sa.ForeignKey("bank_accounts.id"), nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("transaction_date", sa.Date, nullable=False),
        sa.Column("value_date", sa.Date),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("label", sa.String(500)),
        sa.Column("reference", sa.String(100)),
        sa.Column("reconciliation_status", sa.String(20), server_default="NON_RAPPROCHE"),
        sa.Column("cash_flow_category", sa.String(30)),
        sa.Column("source", sa.String(20)),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("journal_entries.id")),
    )
    op.create_table(
        "cash_forecasts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("bank_account_id", sa.String(36), sa.ForeignKey("bank_accounts.id")),
        sa.Column("forecast_date", sa.Date, nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("label", sa.String(255)),
        sa.Column("source", sa.String(20), server_default="MANUAL"),
        sa.Column("source_document_id", sa.String(36)),
        sa.Column("is_realized", sa.Boolean, server_default="false"),
    )

    # --- consolidation ---
    op.create_table(
        "groups",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("consolidation_currency", sa.String(3), server_default="EUR"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
    )
    op.create_table(
        "group_entities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("pct_controle", sa.Numeric(5, 2), nullable=False),
        sa.Column("pct_interet", sa.Numeric(5, 2), nullable=False),
        sa.Column("integration_method", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
    )
    op.create_table(
        "intragroup_eliminations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("fiscal_year_id", sa.String(36)),
        sa.Column("entity_debit_id", sa.String(36), nullable=False),
        sa.Column("entity_credit_id", sa.String(36), nullable=False),
        sa.Column("elimination_type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("account_debit", sa.String(20), nullable=False),
        sa.Column("account_credit", sa.String(20), nullable=False),
        sa.Column("description", sa.Text),
    )
    op.create_table(
        "consolidated_packages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("fiscal_year_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT"),
        sa.Column("data", sa.JSON),
    )


def downgrade() -> None:
    op.drop_table("consolidated_packages")
    op.drop_table("intragroup_eliminations")
    op.drop_table("group_entities")
    op.drop_table("groups")
    op.drop_table("cash_forecasts")
    op.drop_table("bank_transactions")
    op.drop_table("bank_accounts")
    op.drop_table("payment_reminders")
    op.drop_table("invoice_lines")
    op.drop_table("invoices")
    op.drop_table("deferred_taxes")
    op.drop_table("is_declarations")
    op.drop_table("tva_declarations")
    op.drop_table("depreciation_lines")
    op.drop_table("fixed_assets")
