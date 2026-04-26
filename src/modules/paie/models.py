"""Paie — bulletins de salaire (stub)."""
from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Numeric, String, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class BulletinStatus(StrEnum):
    BROUILLON = "BROUILLON"
    VALIDE = "VALIDE"
    PAYE = "PAYE"


class Bulletin(Base, UUIDMixin, TimestampMixin):
    """Bulletin de paie."""
    __tablename__ = "bulletins"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), nullable=False)
    period_start: Mapped[object] = mapped_column(Date, nullable=False)
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=BulletinStatus.BROUILLON)
    salaire_brut: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    cotisations_salariales: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    cotisations_patronales: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    net_a_payer: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("journal_entries.id"))

    lines: Mapped[list["LigneBulletin"]] = relationship(back_populates="bulletin", cascade="all, delete-orphan")


class LigneBulletin(Base, UUIDMixin, TimestampMixin):
    """Ligne d'un bulletin de paie."""
    __tablename__ = "lignes_bulletin"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    bulletin_id: Mapped[str] = mapped_column(String(36), ForeignKey("bulletins.id"), nullable=False)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    base: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    taux_salarial: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0"))
    taux_patronal: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0"))
    montant_salarial: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    montant_patronal: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    bulletin: Mapped[Bulletin] = relationship(back_populates="lines")
