"""Notes de frais — remboursements salariés, barèmes kilométriques."""
from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Numeric, String, Text, Boolean, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class ExpenseStatus(StrEnum):
    BROUILLON = "BROUILLON"
    SOUMIS = "SOUMIS"
    APPROUVE = "APPROUVE"
    REJETE = "REJETE"
    REMBOURSE = "REMBOURSE"


class ExpenseCategory(StrEnum):
    DEPLACEMENT = "DEPLACEMENT"        # Transports (train, avion, taxi)
    KILOMETRIQUE = "KILOMETRIQUE"      # Indemnités kilométriques
    HEBERGEMENT = "HEBERGEMENT"        # Hôtel, logement
    REPAS = "REPAS"                    # Repas d'affaires
    MATERIEL = "MATERIEL"              # Matériel, fournitures
    REPRESENTATION = "REPRESENTATION"  # Cadeaux clients, réceptions
    COMMUNICATION = "COMMUNICATION"    # Téléphone, internet
    AUTRE = "AUTRE"


# Barèmes kilométriques DGFiP 2024 (puissance fiscale -> tranche -> taux)
# Format: {cv: [(jusqu_a_km, taux_par_km), ...]}  last entry = unlimited
BAREME_KILOMETRIQUE_2024: dict[int, list[tuple[int | None, Decimal]]] = {
    3: [(5000, Decimal("0.502")), (20000, Decimal("0.300")), (None, Decimal("0.350"))],
    4: [(5000, Decimal("0.575")), (20000, Decimal("0.344")), (None, Decimal("0.401"))],
    5: [(5000, Decimal("0.601")), (20000, Decimal("0.360")), (None, Decimal("0.421"))],
    6: [(5000, Decimal("0.634")), (20000, Decimal("0.380")), (None, Decimal("0.444"))],
    7: [(5000, Decimal("0.665")), (20000, Decimal("0.399")), (None, Decimal("0.466"))],
}


def compute_indemnite_kilometrique(cv: int, km: int) -> Decimal:
    """Calcule l'indemnité kilométrique selon le barème DGFiP 2024."""
    if cv < 3:
        cv = 3
    if cv > 7:
        cv = 7
    tranches = BAREME_KILOMETRIQUE_2024[cv]
    for (jusqu_a, taux) in tranches:
        if jusqu_a is None or km <= jusqu_a:
            return (Decimal(str(km)) * taux).quantize(Decimal("0.01"))
    return Decimal("0")


class NoteFrais(Base, UUIDMixin, TimestampMixin):
    """En-tête d'une note de frais."""
    __tablename__ = "notes_frais"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), nullable=False)
    period_start: Mapped[object] = mapped_column(Date, nullable=False)
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=ExpenseStatus.BROUILLON)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    approved_by: Mapped[str | None] = mapped_column(String(36))
    entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("journal_entries.id"))
    notes: Mapped[str | None] = mapped_column(Text)

    lines: Mapped[list["LigneFrais"]] = relationship(back_populates="note", cascade="all, delete-orphan")

    def recompute_total(self) -> None:
        self.total_amount = sum((l.amount for l in self.lines), Decimal("0"))


class LigneFrais(Base, UUIDMixin, TimestampMixin):
    """Ligne de frais dans une note de frais."""
    __tablename__ = "lignes_frais"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    note_id: Mapped[str] = mapped_column(String(36), ForeignKey("notes_frais.id"), nullable=False)
    expense_date: Mapped[object] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    vat_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    # Kilométrique
    vehicle_cv: Mapped[int | None] = mapped_column(Integer)
    km_distance: Mapped[int | None] = mapped_column(Integer)
    # Compta
    account_code: Mapped[str] = mapped_column(String(20), default="625")
    has_receipt: Mapped[bool] = mapped_column(Boolean, default=False)

    note: Mapped[NoteFrais] = relationship(back_populates="lines")

    @classmethod
    def from_kilometrique(
        cls,
        company_id: str,
        note_id: str,
        expense_date: object,
        description: str,
        cv: int,
        km: int,
    ) -> "LigneFrais":
        amount = compute_indemnite_kilometrique(cv, km)
        return cls(
            company_id=company_id,
            note_id=note_id,
            expense_date=expense_date,
            category=ExpenseCategory.KILOMETRIQUE,
            description=description,
            amount=amount,
            vehicle_cv=cv,
            km_distance=km,
            account_code="6251",  # PCG: Indemnités kilométriques
        )
