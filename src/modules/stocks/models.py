"""Gestion des stocks — articles, mouvements, valorisation FIFO/CMUP."""
from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class ValuationMethod(StrEnum):
    FIFO = "FIFO"
    CMUP = "CMUP"
    LIFO = "LIFO"


class StockMoveType(StrEnum):
    ENTREE = "ENTREE"           # Achat, production, retour client
    SORTIE = "SORTIE"           # Vente, consommation, perte
    TRANSFERT = "TRANSFERT"     # Transfert entre dépôts
    INVENTAIRE = "INVENTAIRE"   # Ajustement inventaire
    RETOUR = "RETOUR"           # Retour fournisseur


class Article(Base, UUIDMixin, TimestampMixin):
    """Article stocké."""
    __tablename__ = "articles"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    reference: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(20), default="unité")
    valuation_method: Mapped[str] = mapped_column(String(10), default=ValuationMethod.CMUP)
    account_stock: Mapped[str] = mapped_column(String(20), default="37")       # PCG: Marchandises
    account_variation: Mapped[str] = mapped_column(String(20), default="6037") # Variation stocks marchandises
    stock_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    stock_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    min_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    movements: Mapped[list["StockMovement"]] = relationship(back_populates="article")

    @property
    def unit_cost(self) -> Decimal:
        if self.stock_qty == 0:
            return Decimal("0")
        return (self.stock_value / self.stock_qty).quantize(Decimal("0.0001"))


class StockMovement(Base, UUIDMixin, TimestampMixin):
    """Mouvement de stock (entrée / sortie / transfert)."""
    __tablename__ = "stock_movements"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    article_id: Mapped[str] = mapped_column(String(36), ForeignKey("articles.id"), nullable=False)
    move_date: Mapped[object] = mapped_column(Date, nullable=False)
    move_type: Mapped[str] = mapped_column(String(20), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("journal_entries.id"))
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)

    article: Mapped[Article] = relationship(back_populates="movements")


class Depot(Base, UUIDMixin, TimestampMixin):
    """Dépôt / entrepôt."""
    __tablename__ = "depots"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class InventoryLine(Base, UUIDMixin, TimestampMixin):
    """Ligne d'inventaire physique."""
    __tablename__ = "inventory_lines"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"), nullable=False)
    article_id: Mapped[str] = mapped_column(String(36), ForeignKey("articles.id"), nullable=False)
    inventory_date: Mapped[object] = mapped_column(Date, nullable=False)
    qty_theoretical: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    qty_physical: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    @property
    def variance_qty(self) -> Decimal:
        return self.qty_physical - self.qty_theoretical

    @property
    def variance_value(self) -> Decimal:
        return self.variance_qty * self.unit_cost
