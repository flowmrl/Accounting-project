"""Modèles du module Immobilisations."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class AssetCategory(StrEnum):
    INCORPORELLE = "INCORPORELLE"       # Brevets, logiciels, fonds commercial
    CORPORELLE = "CORPORELLE"           # Terrains, constructions, matériel
    FINANCIERE = "FINANCIERE"           # Titres, prêts


class DepreciationMethod(StrEnum):
    LINEAIRE = "LINEAIRE"               # Amortissement linéaire
    DEGRESSIF = "DEGRESSIF"             # Amortissement dégressif fiscal
    UO = "UO"                           # Unités d'œuvre (production)
    COMPOSANTS = "COMPOSANTS"           # IAS 16 — approche par composants
    NON_AMORTISSABLE = "NON_AMORTISSABLE"  # Terrains, fonds commercial (PCG)


class AssetStatus(StrEnum):
    EN_SERVICE = "EN_SERVICE"
    EN_COURS = "EN_COURS"               # Immobilisation en cours (compte 23x)
    CEDE = "CEDE"                       # Cédé / mis au rebut
    RECLASSE = "RECLASSE"               # Reclassé dans une autre catégorie


class FixedAsset(Base, UUIDMixin, TimestampMixin):
    """Fiche d'immobilisation."""
    __tablename__ = "fixed_assets"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    # Identification
    reference: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=AssetStatus.EN_SERVICE, nullable=False)

    # Compte PCG d'immobilisation (ex: "2183") et d'amortissement (ex: "2818")
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    depreciation_account_code: Mapped[str | None] = mapped_column(String(20))

    # Valeurs
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    commissioning_date: Mapped[date | None] = mapped_column(Date)  # Date de mise en service
    acquisition_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    residual_value: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))

    # Amortissement
    depreciation_method: Mapped[str] = mapped_column(
        String(20), default=DepreciationMethod.LINEAIRE, nullable=False
    )
    useful_life_years: Mapped[int | None] = mapped_column()      # Durée en années
    useful_life_units: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))  # Pour méthode UO
    degressive_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))    # Coefficient dégressif

    # Amortissements dérogatoires (diff. fiscal/comptable)
    has_exceptional_depreciation: Mapped[bool] = mapped_column(Boolean, default=False)

    # Cession
    disposal_date: Mapped[date | None] = mapped_column(Date)
    disposal_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    disposal_journal_entry_id: Mapped[str | None] = mapped_column(String(36))

    # Fournisseur / référence
    supplier: Mapped[str | None] = mapped_column(String(255))
    invoice_reference: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255))

    # Relations
    depreciation_lines: Mapped[list["DepreciationLine"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", order_by="DepreciationLine.period_date"
    )

    @property
    def total_depreciated(self) -> Decimal:
        return sum(
            (d.amount for d in self.depreciation_lines if d.is_posted),
            Decimal("0.00"),
        )

    @property
    def net_book_value(self) -> Decimal:
        return self.acquisition_cost - self.total_depreciated

    def __repr__(self) -> str:
        return f"<FixedAsset {self.reference} — {self.name}>"


class DepreciationLine(Base, UUIDMixin, TimestampMixin):
    """Ligne du plan d'amortissement (une ligne = un exercice ou une période)."""
    __tablename__ = "depreciation_lines"

    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fixed_assets.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("fiscal_years.id", ondelete="SET NULL")
    )

    period_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)

    # Décomposition comptable / dérogatoire
    accounting_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    exceptional_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))

    cumulative_at_start: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    net_book_value_after: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)

    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)  # Écriture comptabilisée
    journal_entry_id: Mapped[str | None] = mapped_column(String(36))

    asset: Mapped["FixedAsset"] = relationship(back_populates="depreciation_lines")

    def __repr__(self) -> str:
        return f"<DepreciationLine {self.period_date} {self.amount}>"
