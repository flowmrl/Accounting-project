"""Modules analytique, stocks et notes de frais.

Revision ID: 003
Revises: 002
Create Date: 2026-04-26 00:02:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Comptabilité analytique
    # ------------------------------------------------------------------
    op.create_table(
        "analytic_axes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("axis_type", sa.String(30), nullable=False, server_default="LIBRE"),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "analytic_sections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("axis_id", sa.String(36), sa.ForeignKey("analytic_axes.id"), nullable=False),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("analytic_sections.id")),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("manager_id", sa.String(36)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "analytic_distributions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("journal_line_id", sa.String(36), sa.ForeignKey("journal_entry_lines.id"), nullable=False),
        sa.Column("section_id", sa.String(36), sa.ForeignKey("analytic_sections.id"), nullable=False),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("fiscal_year_id", sa.String(36), sa.ForeignKey("fiscal_years.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "analytic_budgets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("fiscal_year_id", sa.String(36), sa.ForeignKey("fiscal_years.id"), nullable=False),
        sa.Column("section_id", sa.String(36), sa.ForeignKey("analytic_sections.id"), nullable=False),
        sa.Column("account_code", sa.String(20), nullable=False),
        sa.Column("period_month", sa.Integer, nullable=False),
        sa.Column("budget_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("realized_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ------------------------------------------------------------------
    # Stocks
    # ------------------------------------------------------------------
    op.create_table(
        "articles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("reference", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("unit", sa.String(20), nullable=False, server_default="unité"),
        sa.Column("valuation_method", sa.String(10), nullable=False, server_default="CMUP"),
        sa.Column("account_stock", sa.String(20), nullable=False, server_default="37"),
        sa.Column("account_variation", sa.String(20), nullable=False, server_default="6037"),
        sa.Column("stock_qty", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("stock_value", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("min_qty", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "depots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("article_id", sa.String(36), sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("move_date", sa.Date, nullable=False),
        sa.Column("move_type", sa.String(20), nullable=False),
        sa.Column("qty", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("total_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("reference", sa.String(100)),
        sa.Column("notes", sa.Text),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("journal_entries.id")),
        sa.Column("is_posted", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "inventory_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("article_id", sa.String(36), sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("inventory_date", sa.Date, nullable=False),
        sa.Column("qty_theoretical", sa.Numeric(18, 4), nullable=False),
        sa.Column("qty_physical", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ------------------------------------------------------------------
    # Notes de frais
    # ------------------------------------------------------------------
    op.create_table(
        "notes_frais",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="BROUILLON"),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("approved_by", sa.String(36)),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("journal_entries.id")),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "lignes_frais",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_id", sa.String(36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("note_id", sa.String(36), sa.ForeignKey("notes_frais.id"), nullable=False),
        sa.Column("expense_date", sa.Date, nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("vat_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("vehicle_cv", sa.Integer),
        sa.Column("km_distance", sa.Integer),
        sa.Column("account_code", sa.String(20), nullable=False, server_default="625"),
        sa.Column("has_receipt", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("lignes_frais")
    op.drop_table("notes_frais")
    op.drop_table("inventory_lines")
    op.drop_table("stock_movements")
    op.drop_table("depots")
    op.drop_table("articles")
    op.drop_table("analytic_budgets")
    op.drop_table("analytic_distributions")
    op.drop_table("analytic_sections")
    op.drop_table("analytic_axes")
