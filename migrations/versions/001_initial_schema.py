"""Initial schema — all tables.

Revision ID: 001
Revises:
Create Date: 2026-04-26 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- companies ---
    op.create_table(
        "companies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("siren", sa.String(9)),
        sa.Column("siret", sa.String(14)),
        sa.Column("legal_form", sa.String(20)),
        sa.Column("accounting_standard", sa.String(20), nullable=False, server_default="PCG"),
        sa.Column("tax_regime", sa.String(20)),
        sa.Column("vat_regime", sa.String(20)),
        sa.Column("fiscal_year_start_month", sa.Integer, server_default="1"),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("country_code", sa.String(2), server_default="FR"),
        sa.Column("address", sa.Text),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
    )

    # --- currencies ---
    op.create_table(
        "currencies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("code", sa.String(3), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("symbol", sa.String(5)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
    )
    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("from_currency", sa.String(3), nullable=False),
        sa.Column("to_currency", sa.String(3), nullable=False),
        sa.Column("rate", sa.Numeric(18, 6), nullable=False),
        sa.Column("rate_date", sa.Date, nullable=False),
    )

    # --- fiscal_years ---
    op.create_table(
        "fiscal_years",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("label", sa.String(100)),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="OUVERT"),
    )
    op.create_index("ix_fiscal_years_company", "fiscal_years", ["company_id"])

    # --- accounts ---
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(30), nullable=False),
        sa.Column("account_nature", sa.String(30), nullable=False),
        sa.Column("account_class", sa.String(5), nullable=False),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("accounts.id")),
        sa.Column("is_detail", sa.Boolean, server_default="true"),
        sa.Column("is_reconcilable", sa.Boolean, server_default="false"),
        sa.Column("vat_code", sa.String(20)),
        sa.Column("description", sa.Text),
        sa.Column("tags", sa.JSON),
        sa.Column("balance_debit", sa.Numeric(18, 2), server_default="0"),
        sa.Column("balance_credit", sa.Numeric(18, 2), server_default="0"),
        sa.UniqueConstraint("company_id", "code", name="uq_account_company_code"),
    )
    op.create_index("ix_accounts_company_code", "accounts", ["company_id", "code"])

    # --- journals ---
    op.create_table(
        "journals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("journal_type", sa.String(20), nullable=False),
        sa.Column("default_account_id", sa.String(36), sa.ForeignKey("accounts.id")),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.UniqueConstraint("company_id", "code", name="uq_journal_company_code"),
    )

    # --- journal_entries + lines ---
    op.create_table(
        "journal_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("journal_code", sa.String(10), nullable=False),
        sa.Column("fiscal_year_id", sa.String(36), sa.ForeignKey("fiscal_years.id"), nullable=False),
        sa.Column("entry_number", sa.String(30)),
        sa.Column("entry_date", sa.Date, nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("reference", sa.String(100)),
        sa.Column("status", sa.String(20), nullable=False, server_default="BROUILLON"),
        sa.Column("total_debit", sa.Numeric(18, 2), server_default="0"),
        sa.Column("total_credit", sa.Numeric(18, 2), server_default="0"),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("source_document_id", sa.String(36)),
        sa.Column("reversed_entry_id", sa.String(36), sa.ForeignKey("journal_entries.id")),
    )
    op.create_index("ix_je_company_date", "journal_entries", ["company_id", "entry_date"])
    op.create_table(
        "journal_entry_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("journal_entries.id"), nullable=False),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("analytic_account_id", sa.String(36), sa.ForeignKey("accounts.id")),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("debit", sa.Numeric(18, 2), server_default="0"),
        sa.Column("credit", sa.Numeric(18, 2), server_default="0"),
        sa.Column("currency_amount", sa.Numeric(18, 2)),
        sa.Column("currency_code", sa.String(3)),
        sa.Column("reconciliation_mark", sa.String(20)),
        sa.Column("due_date", sa.Date),
    )
    op.create_index("ix_jel_entry", "journal_entry_lines", ["entry_id"])
    op.create_index("ix_jel_account", "journal_entry_lines", ["account_id"])


def downgrade() -> None:
    op.drop_table("journal_entry_lines")
    op.drop_table("journal_entries")
    op.drop_table("journals")
    op.drop_table("accounts")
    op.drop_table("fiscal_years")
    op.drop_table("exchange_rates")
    op.drop_table("currencies")
    op.drop_table("companies")
