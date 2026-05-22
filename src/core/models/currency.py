"""Devises et taux de change."""
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class Currency(Base, UUIDMixin, TimestampMixin):
    """Devise supportée."""
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)  # ISO 4217
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    symbol: Mapped[str] = mapped_column(String(5), nullable=False)
    decimal_places: Mapped[int] = mapped_column(default=2, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Currency {self.code} ({self.symbol})>"


class ExchangeRate(Base, UUIDMixin, TimestampMixin):
    """Taux de change journalier (vs EUR par défaut)."""
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint("from_currency", "to_currency", "rate_date", name="uq_exchange_rate_date"),
    )

    from_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))  # BCE, BDF, manual…

    def __repr__(self) -> str:
        return f"<ExchangeRate {self.from_currency}/{self.to_currency} {self.rate_date}: {self.rate}>"
