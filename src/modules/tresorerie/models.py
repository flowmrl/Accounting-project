"""Modèles du module Trésorerie — comptes bancaires, rapprochement, prévisions."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class BankAccountType(StrEnum):
    COURANT = "COURANT"
    EPARGNE = "EPARGNE"
    DEPOT_TERME = "DEPOT_TERME"
    CARTE = "CARTE"


class ReconciliationStatus(StrEnum):
    NON_RAPPROCHE = "NON_RAPPROCHE"
    RAPPROCHE = "RAPPROCHE"
    ECART = "ECART"


class CashFlowCategory(StrEnum):
    """Catégorie pour le TFT dynamique."""
    EXPLOITATION = "EXPLOITATION"
    INVESTISSEMENT = "INVESTISSEMENT"
    FINANCEMENT = "FINANCEMENT"


class BankAccount(Base, UUIDMixin, TimestampMixin):
    """Compte bancaire d'une société."""
    __tablename__ = "bank_accounts"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    account_type: Mapped[str] = mapped_column(String(20), default=BankAccountType.COURANT)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(100))
    iban: Mapped[str | None] = mapped_column(String(34))
    bic: Mapped[str | None] = mapped_column(String(11))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Compte PCG associé (ex: "512001")
    account_code: Mapped[str] = mapped_column(String(20), default="512")

    # Solde selon le relevé bancaire (mis à jour lors du rapprochement)
    bank_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    bank_balance_date: Mapped[date | None] = mapped_column(Date)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    transactions: Mapped[list["BankTransaction"]] = relationship(
        back_populates="bank_account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<BankAccount {self.name} [{self.iban or 'no IBAN'}]>"


class BankTransaction(Base, UUIDMixin, TimestampMixin):
    """Transaction bancaire importée (relevé, Open Banking DSP2)."""
    __tablename__ = "bank_transactions"

    bank_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False
    )

    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[date | None] = mapped_column(Date)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))

    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)  # + crédit, - débit
    balance_after: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))

    # Rapprochement bancaire
    reconciliation_status: Mapped[str] = mapped_column(
        String(20), default=ReconciliationStatus.NON_RAPPROCHE
    )
    journal_entry_id: Mapped[str | None] = mapped_column(String(36))
    reconciled_at: Mapped[date | None] = mapped_column(Date)

    # Catégorie TFT (déterminée automatiquement ou manuellement)
    cash_flow_category: Mapped[str | None] = mapped_column(String(20))

    # Source d'import
    source: Mapped[str] = mapped_column(String(20), default="MANUAL")  # MANUAL | OFX | CAMT | API

    bank_account: Mapped["BankAccount"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<BankTransaction {self.transaction_date} {self.amount} — {self.label[:40]}>"


class CashForecast(Base, UUIDMixin, TimestampMixin):
    """
    Prévision de trésorerie quotidienne (J+30, J+60, J+90).
    Alimentée par les factures dues + échéances fournisseurs + paie.
    """
    __tablename__ = "cash_forecasts"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    bank_account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("bank_accounts.id", ondelete="SET NULL")
    )

    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    cash_flow_category: Mapped[str] = mapped_column(String(20), nullable=False)

    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str | None] = mapped_column(String(50))  # INVOICE | PAYROLL | MANUAL | LOAN
    source_id: Mapped[str | None] = mapped_column(String(36))  # ID de la source

    notes: Mapped[str | None] = mapped_column(Text)
