"""Modèles du module Tax — TVA, IS, IDA/IDP, FEC."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class TVADeclarationType(StrEnum):
    CA3_MENSUEL = "CA3_MENSUEL"
    CA3_TRIMESTRIEL = "CA3_TRIMESTRIEL"
    CA12_ANNUEL = "CA12_ANNUEL"


class TVADeclarationStatus(StrEnum):
    BROUILLON = "BROUILLON"
    DEPOSE = "DEPOSE"
    ACQUITTE = "ACQUITTE"


class TVADeclaration(Base, UUIDMixin, TimestampMixin):
    """Déclaration TVA (CA3 ou CA12) — snapshot à la date de dépôt."""
    __tablename__ = "tva_declarations"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("fiscal_years.id", ondelete="SET NULL")
    )

    declaration_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=TVADeclarationStatus.BROUILLON)

    periode_debut: Mapped[date] = mapped_column(Date, nullable=False)
    periode_fin: Mapped[date] = mapped_column(Date, nullable=False)

    # Montants calculés
    tva_collectee: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    tva_deductible: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    tva_due: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    credit_tva: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))

    # Snapshot détaillé par taux (JSON)
    detail_json: Mapped[dict | None] = mapped_column(JSON)

    filed_at: Mapped[date | None] = mapped_column(Date)
    reference_depot: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)


class ISDeclaration(Base, UUIDMixin, TimestampMixin):
    """Déclaration IS (Impôt sur les Sociétés) — liasse 2065."""
    __tablename__ = "is_declarations"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fiscal_years.id", ondelete="CASCADE"), nullable=False
    )

    # Résultat fiscal
    resultat_comptable: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    reintegrations: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    deductions: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    resultat_fiscal: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))

    # IS calculé (taux normal 25%, taux réduit PME 15% jusqu'à 42 500 €)
    is_taux_normal: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    is_taux_reduit: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    is_total: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))

    # Impôts différés
    ida_total: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    idp_total: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))

    status: Mapped[str] = mapped_column(String(20), default="BROUILLON")
    filed_at: Mapped[date | None] = mapped_column(Date)
    detail_json: Mapped[dict | None] = mapped_column(JSON)


class DeferredTax(Base, UUIDMixin, TimestampMixin):
    """
    Impôts différés actifs (IDA) et passifs (IDP).
    Écart temporaire entre résultat comptable et fiscal.
    """
    __tablename__ = "deferred_taxes"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fiscal_years.id", ondelete="CASCADE"), nullable=False
    )

    label: Mapped[str] = mapped_column(String(255), nullable=False)
    nature: Mapped[str] = mapped_column(String(10), nullable=False)   # IDA | IDP
    base_temporaire: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    taux_is: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.2500"))
    montant: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    origine: Mapped[str | None] = mapped_column(String(100))  # ex: "Amortissements dérogatoires"
