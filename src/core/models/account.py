"""Modèle Plan de Comptes (Chart of Accounts)."""
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class AccountType(StrEnum):
    """Classification comptable de haut niveau (PCG classes 1-8)."""
    # Comptes de bilan
    CAPITAUX = "CAPITAUX"               # Classe 1 — Capitaux
    IMMOBILISATIONS = "IMMOBILISATIONS" # Classe 2 — Immobilisations
    STOCKS = "STOCKS"                   # Classe 3 — Stocks et en-cours
    TIERS = "TIERS"                     # Classe 4 — Comptes de tiers
    FINANCIER = "FINANCIER"             # Classe 5 — Comptes financiers
    # Comptes de gestion
    CHARGES = "CHARGES"                 # Classe 6 — Charges
    PRODUITS = "PRODUITS"               # Classe 7 — Produits
    # Comptes spéciaux
    SPECIAUX = "SPECIAUX"               # Classe 8 — Comptes spéciaux


class AccountNature(StrEnum):
    """Nature du compte pour le bilan / CdR."""
    ASSET = "ASSET"             # Actif
    LIABILITY = "LIABILITY"     # Passif
    EQUITY = "EQUITY"           # Capitaux propres
    REVENUE = "REVENUE"         # Produits
    EXPENSE = "EXPENSE"         # Charges
    CONTRA_ASSET = "CONTRA_ASSET"       # Actif soustractif (amortissements, provisions)


class AccountClass(StrEnum):
    """Classes PCG 1-8."""
    C1 = "1"
    C2 = "2"
    C3 = "3"
    C4 = "4"
    C5 = "5"
    C6 = "6"
    C7 = "7"
    C8 = "8"


class Account(Base, UUIDMixin, TimestampMixin):
    """
    Compte du plan de comptes.

    Supporte le Plan Comptable Général (PCG) et les autres référentiels
    via le champ `standard`. Les comptes peuvent être hiérarchisés
    (parent → enfants) pour les sous-comptes analytiques.
    """
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("company_id", "code", "standard", name="uq_account_company_code_standard"),
    )

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="SET NULL")
    )

    # Identification
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Classification
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    account_nature: Mapped[str] = mapped_column(String(20), nullable=False)
    account_class: Mapped[str] = mapped_column(String(2), nullable=False)

    # Référentiel comptable auquel ce compte appartient
    standard: Mapped[str] = mapped_column(String(20), default="PCG", nullable=False)

    # Contrôle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_detail: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # False = compte de regroupement
    is_reconcilable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # TVA
    vat_code: Mapped[str | None] = mapped_column(String(10))  # Code TVA applicable

    # Devise
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    # Soldes courants (dénormalisés pour performance)
    balance_debit: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), default=Decimal("0.00"), nullable=False
    )
    balance_credit: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), default=Decimal("0.00"), nullable=False
    )

    # Relations
    company: Mapped["Company"] = relationship(back_populates="accounts")  # type: ignore[name-defined]  # noqa: F821
    parent: Mapped["Account | None"] = relationship(
        back_populates="children", remote_side="Account.id"
    )
    children: Mapped[list["Account"]] = relationship(back_populates="parent")
    journal_lines: Mapped[list["JournalEntryLine"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="account",
        foreign_keys="[JournalEntryLine.account_id]",
        primaryjoin="Account.id == JournalEntryLine.account_id",
    )

    @property
    def balance(self) -> Decimal:
        """Solde net (débit - crédit pour actif/charges, crédit - débit pour passif/produits)."""
        if self.account_nature in (AccountNature.ASSET, AccountNature.EXPENSE, AccountNature.CONTRA_ASSET):
            return self.balance_debit - self.balance_credit
        return self.balance_credit - self.balance_debit

    @property
    def pcg_class(self) -> str:
        """Classe PCG déduite du premier chiffre du code."""
        return self.code[0] if self.code else ""

    def __repr__(self) -> str:
        return f"<Account {self.code} — {self.name}>"
