"""Journal comptable."""
from enum import StrEnum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class JournalType(StrEnum):
    """Types de journaux comptables (PCG)."""
    ACHATS = "ACHATS"           # Journal des achats (HA)
    VENTES = "VENTES"           # Journal des ventes (VT)
    BANQUE = "BANQUE"           # Journal de banque (BQ)
    CAISSE = "CAISSE"           # Journal de caisse (CA)
    OD = "OD"                   # Opérations diverses / extourne
    PAIE = "PAIE"               # Journal de paie (PA)
    IMMOBILISATIONS = "IMMOBILISATIONS"  # Journal des immobilisations (IM)
    TVA = "TVA"                 # Journal de TVA
    OUVERTURE = "OUVERTURE"     # À-nouveaux / ouverture d'exercice
    CLOTURE = "CLOTURE"         # Écritures de clôture
    EXTOURNE = "EXTOURNE"       # Extournes


class Journal(Base, UUIDMixin, TimestampMixin):
    """
    Journal comptable d'une société pour un exercice donné.
    Chaque écriture est rattachée à un journal.
    """
    __tablename__ = "journals"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fiscal_years.id", ondelete="CASCADE"), nullable=False
    )

    code: Mapped[str] = mapped_column(String(10), nullable=False)   # Ex: "HA", "VT", "BQ"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    journal_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Compte de contrepartie automatique (ex: compte banque pour journal BQ)
    default_counterpart_account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="SET NULL")
    )

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relations
    fiscal_year: Mapped["FiscalYear"] = relationship(back_populates="journals")  # type: ignore[name-defined]  # noqa: F821
    entries: Mapped[list["JournalEntry"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="journal", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Journal {self.code} — {self.name}>"
