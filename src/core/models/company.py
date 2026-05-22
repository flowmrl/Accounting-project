"""Modèle Société / Entreprise."""
from enum import StrEnum

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class LegalForm(StrEnum):
    """Formes juridiques françaises."""
    SARL = "SARL"
    SAS = "SAS"
    SASU = "SASU"
    EURL = "EURL"
    SA = "SA"
    SNC = "SNC"
    EI = "EI"          # Entreprise Individuelle
    EIRL = "EIRL"
    AUTO_ENTREPRENEUR = "AUTO_ENTREPRENEUR"
    ASSOCIATION = "ASSOCIATION"
    SCI = "SCI"
    OTHER = "OTHER"


class VATRegime(StrEnum):
    """Régimes de TVA."""
    NORMAL = "NORMAL"               # Régime réel normal
    SIMPLIFIE = "SIMPLIFIE"         # Régime réel simplifié
    FRANCHISE = "FRANCHISE"         # Franchise en base de TVA
    MINI_REEL = "MINI_REEL"         # Mini-réel
    NON_ASSUJETTI = "NON_ASSUJETTI"


class TaxRegime(StrEnum):
    """Régimes fiscaux."""
    IS = "IS"           # Impôt sur les sociétés
    IR = "IR"           # Impôt sur le revenu
    MICRO_BIC = "MICRO_BIC"
    MICRO_BNC = "MICRO_BNC"


class Company(Base, UUIDMixin, TimestampMixin):
    """Représente une société/entreprise cliente."""
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    siren: Mapped[str | None] = mapped_column(String(9))
    siret: Mapped[str | None] = mapped_column(String(14))
    tva_intracom: Mapped[str | None] = mapped_column(String(20))

    legal_form: Mapped[str] = mapped_column(
        String(30), default=LegalForm.SARL, nullable=False
    )
    naf_code: Mapped[str | None] = mapped_column(String(6))  # Code APE/NAF

    address: Mapped[str | None] = mapped_column(Text)
    zip_code: Mapped[str | None] = mapped_column(String(10))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(2), default="FR", nullable=False)

    vat_regime: Mapped[str] = mapped_column(
        String(20), default=VATRegime.NORMAL, nullable=False
    )
    tax_regime: Mapped[str] = mapped_column(
        String(20), default=TaxRegime.IS, nullable=False
    )

    # Référentiel comptable actif
    accounting_standard: Mapped[str] = mapped_column(
        String(20), default="PCG", nullable=False
    )  # PCG | IFRS | US_GAAP | OHADA | ...

    default_currency: Mapped[str] = mapped_column(
        String(3), default="EUR", nullable=False
    )

    fiscal_year_start_month: Mapped[int] = mapped_column(default=1)  # Janvier = 1

    # Relations
    fiscal_years: Mapped[list["FiscalYear"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="company", cascade="all, delete-orphan"
    )
    accounts: Mapped[list["Account"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Company {self.name} ({self.siren})>"
