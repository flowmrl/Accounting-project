"""Écriture comptable et ses lignes (Journal Entry / Ligne d'écriture)."""
from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class EntryStatus(StrEnum):
    BROUILLON = "BROUILLON"     # Non validé, modifiable
    VALIDE = "VALIDE"           # Validé, non modifiable (lettrage possible)
    LETTREE = "LETTREE"         # Lettrée (rapprochement tiers)
    EXTOURNEE = "EXTOURNEE"     # Fait l'objet d'une extourne


class JournalEntry(Base, UUIDMixin, TimestampMixin):
    """
    Écriture comptable (pièce comptable).

    Une écriture est équilibrée : ∑ débit = ∑ crédit.
    Elle est composée d'au moins deux lignes (JournalEntryLine).
    """
    __tablename__ = "journal_entries"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    journal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("journals.id", ondelete="RESTRICT"), nullable=False
    )
    fiscal_year_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fiscal_years.id", ondelete="RESTRICT"), nullable=False
    )

    # Numérotation automatique par journal (ex: HA2024/0001)
    entry_number: Mapped[str] = mapped_column(String(30), nullable=False)

    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    accounting_date: Mapped[date] = mapped_column(Date, nullable=False)  # Date comptable (peut différer)
    due_date: Mapped[date | None] = mapped_column(Date)  # Échéance

    label: Mapped[str] = mapped_column(String(500), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))  # N° facture, chèque…
    narration: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(20), default=EntryStatus.BROUILLON, nullable=False
    )

    # Devise de saisie (peut différer de EUR)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), default=Decimal("1.000000"), nullable=False
    )

    # Pièce jointe (chemin ou URL)
    attachment_url: Mapped[str | None] = mapped_column(String(500))

    # Écriture générée automatiquement (extourne, TVA…)
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reversed_entry_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("journal_entries.id", ondelete="SET NULL")
    )

    # Relations
    journal: Mapped["Journal"] = relationship(back_populates="entries")  # type: ignore[name-defined]  # noqa: F821
    fiscal_year: Mapped["FiscalYear"] = relationship(back_populates="journal_entries")  # type: ignore[name-defined]  # noqa: F821
    lines: Mapped[list["JournalEntryLine"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", order_by="JournalEntryLine.sequence"
    )
    reversed_entry: Mapped["JournalEntry | None"] = relationship(
        remote_side="JournalEntry.id"
    )

    @property
    def total_debit(self) -> Decimal:
        return sum((line.debit for line in self.lines), Decimal("0.00"))

    @property
    def total_credit(self) -> Decimal:
        return sum((line.credit for line in self.lines), Decimal("0.00"))

    @property
    def is_balanced(self) -> bool:
        return self.total_debit == self.total_credit

    @property
    def is_editable(self) -> bool:
        return self.status == EntryStatus.BROUILLON

    def __repr__(self) -> str:
        return f"<JournalEntry {self.entry_number} — {self.label} [{self.entry_date}]>"


class JournalEntryLine(Base, UUIDMixin, TimestampMixin):
    """
    Ligne d'écriture comptable.
    Chaque ligne impute un compte en débit ou en crédit.
    """
    __tablename__ = "journal_entry_lines"

    entry_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )

    sequence: Mapped[int] = mapped_column(default=0, nullable=False)

    label: Mapped[str] = mapped_column(String(500), nullable=False)

    debit: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), default=Decimal("0.00"), nullable=False
    )
    credit: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), default=Decimal("0.00"), nullable=False
    )

    # Devise d'origine si multi-devises
    amount_currency: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    currency: Mapped[str | None] = mapped_column(String(3))

    # Lettrage (rapprochement tiers)
    matching_code: Mapped[str | None] = mapped_column(String(20))
    is_matched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Analytique
    analytic_account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="SET NULL")
    )
    analytic_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))

    # TVA
    vat_code: Mapped[str | None] = mapped_column(String(10))
    vat_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))

    # Relations
    entry: Mapped["JournalEntry"] = relationship(back_populates="lines")
    account: Mapped["Account"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="journal_lines", foreign_keys=[account_id]
    )

    @property
    def net_amount(self) -> Decimal:
        return self.debit - self.credit

    def __repr__(self) -> str:
        return f"<Line {self.account_id} D:{self.debit} C:{self.credit} — {self.label}>"
