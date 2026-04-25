"""Modèles du module Consolidation Groupe."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class IntegrationMethod(StrEnum):
    GLOBALE = "GLOBALE"                 # Intégration globale (> 50 %)
    PROPORTIONNELLE = "PROPORTIONNELLE" # Intégration proportionnelle (contrôle conjoint)
    EQUIVALENCE = "EQUIVALENCE"         # Mise en équivalence (20-50 %)


class EliminationType(StrEnum):
    VENTES_INTERNES = "VENTES_INTERNES"         # Élimination CA/charges intra-groupe
    CREANCES_DETTES = "CREANCES_DETTES"         # Élimination créances/dettes réciproques
    DIVIDENDES = "DIVIDENDES"                   # Élimination dividendes intra-groupe
    TITRES_CAPITAUX = "TITRES_CAPITAUX"         # Élimination titres de participation / CP


class Group(Base, UUIDMixin, TimestampMixin):
    """Entité groupe (tête de consolidation)."""
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    consolidation_standard: Mapped[str] = mapped_column(String(20), default="PCG")  # PCG | IFRS
    default_currency: Mapped[str] = mapped_column(String(3), default="EUR")
    notes: Mapped[str | None] = mapped_column(Text)

    entities: Mapped[list["GroupEntity"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    eliminations: Mapped[list["IntraGroupElimination"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Group {self.name}>"


class GroupEntity(Base, UUIDMixin, TimestampMixin):
    """
    Entité consolidée dans le périmètre du groupe.
    Associe une Company à un Group avec son pourcentage de contrôle/intérêt.
    """
    __tablename__ = "group_entities"

    group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    integration_method: Mapped[str] = mapped_column(String(20), nullable=False)

    # Pourcentages (ex: 75.00 = 75%)
    pct_controle: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    pct_interet: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    entry_date: Mapped[date | None] = mapped_column(Date)   # Date d'entrée dans le périmètre
    exit_date: Mapped[date | None] = mapped_column(Date)    # Date de sortie

    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    fx_rate: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("1.000000"))

    notes: Mapped[str | None] = mapped_column(Text)

    group: Mapped["Group"] = relationship(back_populates="entities")

    @property
    def is_full_consolidation(self) -> bool:
        return self.integration_method == IntegrationMethod.GLOBALE

    @property
    def minority_interest_pct(self) -> Decimal:
        return Decimal("100.00") - self.pct_interet

    def __repr__(self) -> str:
        return f"<GroupEntity {self.company_id} {self.pct_interet}% [{self.integration_method}]>"


class IntraGroupElimination(Base, UUIDMixin, TimestampMixin):
    """
    Élimination d'une opération intra-groupe (ventes, créances, dividendes…).
    Chaque élimination génère une écriture de retraitement dans la liasse consolidée.
    """
    __tablename__ = "intragroup_eliminations"

    group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fiscal_years.id", ondelete="CASCADE"), nullable=False
    )

    elimination_type: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)

    entity_debit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("group_entities.id"), nullable=False
    )
    entity_credit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("group_entities.id"), nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Comptes impactés (codes PCG ou IFRS selon le référentiel du groupe)
    account_debit: Mapped[str] = mapped_column(String(20), nullable=False)
    account_credit: Mapped[str] = mapped_column(String(20), nullable=False)

    is_posted: Mapped[bool] = mapped_column(default=False)
    detail_json: Mapped[dict | None] = mapped_column(JSON)

    group: Mapped["Group"] = relationship(back_populates="eliminations")

    def __repr__(self) -> str:
        return f"<Elimination {self.elimination_type} {self.amount}>"


class ConsolidatedPackage(Base, UUIDMixin, TimestampMixin):
    """
    Liasse de consolidation pour un exercice donné.
    Snapshot des états financiers consolidés après retraitements et éliminations.
    """
    __tablename__ = "consolidated_packages"

    group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fiscal_years.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), default="BROUILLON")
    closed_at: Mapped[date | None] = mapped_column(Date)

    # États financiers consolidés (JSON)
    bilan_actif_json: Mapped[dict | None] = mapped_column(JSON)
    bilan_passif_json: Mapped[dict | None] = mapped_column(JSON)
    compte_resultat_json: Mapped[dict | None] = mapped_column(JSON)
    tft_json: Mapped[dict | None] = mapped_column(JSON)

    # Intérêts minoritaires
    minority_interests: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))

    notes: Mapped[str | None] = mapped_column(Text)
