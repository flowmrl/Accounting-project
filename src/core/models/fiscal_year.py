"""Exercice comptable (Fiscal Year)."""
from datetime import date
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class FiscalYearStatus(StrEnum):
    OUVERT = "OUVERT"           # En cours de saisie
    CLOTURE_PROVISOIRE = "CLOTURE_PROVISOIRE"  # Pré-clôture (révision possible)
    CLOTURE_DEFINITIF = "CLOTURE_DEFINITIF"    # Clôturé définitivement (lecture seule)


class FiscalYear(Base, UUIDMixin, TimestampMixin):
    """
    Exercice comptable.
    Un exercice peut être inférieur ou supérieur à 12 mois
    (cas de création ou de changement de date de clôture).
    """
    __tablename__ = "fiscal_years"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_fiscal_year_company_code"),
    )

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    code: Mapped[str] = mapped_column(String(20), nullable=False)   # Ex: "2024", "2024-2025"
    label: Mapped[str] = mapped_column(String(100), nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(
        String(30), default=FiscalYearStatus.OUVERT, nullable=False
    )
    is_first_year: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relations
    company: Mapped["Company"] = relationship(back_populates="fiscal_years")  # type: ignore[name-defined]  # noqa: F821
    journals: Mapped[list["Journal"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="fiscal_year", cascade="all, delete-orphan"
    )
    journal_entries: Mapped[list["JournalEntry"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="fiscal_year"
    )

    @property
    def is_closed(self) -> bool:
        return self.status == FiscalYearStatus.CLOTURE_DEFINITIF

    @property
    def duration_months(self) -> int:
        delta = (self.end_date.year - self.start_date.year) * 12
        delta += self.end_date.month - self.start_date.month + 1
        return delta

    def __repr__(self) -> str:
        return f"<FiscalYear {self.code} [{self.start_date} → {self.end_date}] {self.status}>"
