"""Comptabilité analytique — axes, sections, budget vs réalisé."""
from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Numeric, String, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class AxisType(StrEnum):
    CENTRE_COUT = "CENTRE_COUT"
    PROJET = "PROJET"
    GEOGRAPHIQUE = "GEOGRAPHIQUE"
    PRODUIT = "PRODUIT"
    LIBRE = "LIBRE"


class AnalyticAxis(Base, UUIDMixin, TimestampMixin):
    """Axe analytique (dimension d'analyse)."""
    __tablename__ = "analytic_axes"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    axis_type: Mapped[str] = mapped_column(String(30), default=AxisType.LIBRE)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sections: Mapped[list["AnalyticSection"]] = relationship(back_populates="axis", cascade="all, delete-orphan")


class AnalyticSection(Base, UUIDMixin, TimestampMixin):
    """Section analytique (centre de coût, projet, zone géographique…)."""
    __tablename__ = "analytic_sections"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    axis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analytic_axes.id"), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("analytic_sections.id"))
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_id: Mapped[str | None] = mapped_column(String(36))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    axis: Mapped[AnalyticAxis] = relationship(back_populates="sections")
    budget_lines: Mapped[list["AnalyticBudget"]] = relationship(back_populates="section")
    distributions: Mapped[list["AnalyticDistribution"]] = relationship(back_populates="section")


class AnalyticDistribution(Base, UUIDMixin, TimestampMixin):
    """
    Ventilation analytique d'une ligne d'écriture.
    Une ligne peut être répartie sur plusieurs sections (total des % = 100).
    """
    __tablename__ = "analytic_distributions"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    journal_line_id: Mapped[str] = mapped_column(String(36), ForeignKey("journal_entry_lines.id"), nullable=False)
    section_id: Mapped[str] = mapped_column(String(36), ForeignKey("analytic_sections.id"), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    fiscal_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("fiscal_years.id"), nullable=False)

    section: Mapped[AnalyticSection] = relationship(back_populates="distributions")


class AnalyticBudget(Base, UUIDMixin, TimestampMixin):
    """Budget analytique par section, compte et période."""
    __tablename__ = "analytic_budgets"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    fiscal_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("fiscal_years.id"), nullable=False)
    section_id: Mapped[str] = mapped_column(String(36), ForeignKey("analytic_sections.id"), nullable=False)
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    realized_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    section: Mapped[AnalyticSection] = relationship(back_populates="budget_lines")

    @property
    def variance(self) -> Decimal:
        return self.realized_amount - self.budget_amount

    @property
    def variance_pct(self) -> Decimal | None:
        if self.budget_amount == 0:
            return None
        return (self.variance / self.budget_amount * 100).quantize(Decimal("0.01"))
