"""Modèles Achats Fournisseurs — Fournisseurs, Commandes, Factures, Paiements."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class SupplierStatus(StrEnum):
    ACTIF = "ACTIF"
    INACTIF = "INACTIF"
    BLOQUE = "BLOQUE"


class PurchaseOrderStatus(StrEnum):
    BROUILLON = "BROUILLON"
    ENVOYE = "ENVOYE"
    CONFIRME = "CONFIRME"
    PARTIELLEMENT_RECU = "PARTIELLEMENT_RECU"
    RECEPTIONNE = "RECEPTIONNE"
    ANNULE = "ANNULE"


class SupplierInvoiceStatus(StrEnum):
    RECUE = "RECUE"
    EN_ATTENTE_VALIDATION = "EN_ATTENTE_VALIDATION"
    VALIDEE = "VALIDEE"
    REFUSEE = "REFUSEE"
    EN_ATTENTE_PAIEMENT = "EN_ATTENTE_PAIEMENT"
    PARTIELLEMENT_PAYEE = "PARTIELLEMENT_PAYEE"
    PAYEE = "PAYEE"


class PaymentStatus(StrEnum):
    PLANIFIE = "PLANIFIE"
    EXECUTE = "EXECUTE"
    ANNULE = "ANNULE"


class Supplier(Base, UUIDMixin, TimestampMixin):
    """Fournisseur."""
    __tablename__ = "suppliers"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    siren: Mapped[str | None] = mapped_column(String(9))
    siret: Mapped[str | None] = mapped_column(String(14))
    tva_intracom: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    zip_code: Mapped[str | None] = mapped_column(String(10))
    country: Mapped[str] = mapped_column(String(2), default="FR")
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    website: Mapped[str | None] = mapped_column(String(255))
    iban: Mapped[str | None] = mapped_column(String(34))
    bic: Mapped[str | None] = mapped_column(String(11))
    # Compte PCG (ex: "401001")
    account_code: Mapped[str] = mapped_column(String(20), default="401")
    payment_terms_days: Mapped[int] = mapped_column(default=30)
    status: Mapped[str] = mapped_column(String(20), default=SupplierStatus.ACTIF)
    notes: Mapped[str | None] = mapped_column(Text)

    invoices: Mapped[list["SupplierInvoice"]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    """Bon de commande fournisseur."""
    __tablename__ = "purchase_orders"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default=PurchaseOrderStatus.BROUILLON)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date)
    subtotal_ht: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    total_tva: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    total_ttc: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    notes: Mapped[str | None] = mapped_column(Text)

    supplier: Mapped["Supplier"] = relationship(back_populates="purchase_orders")
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Ligne de bon de commande."""
    __tablename__ = "purchase_order_lines"

    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("1.0000"))
    unit_price_ht: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("20.00"))
    account_code: Mapped[str] = mapped_column(String(20), default="607")
    received_qty: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0.0000"))

    @property
    def line_ht(self) -> Decimal:
        return self.quantity * self.unit_price_ht

    order: Mapped["PurchaseOrder"] = relationship(back_populates="lines")


class SupplierInvoice(Base, UUIDMixin, TimestampMixin):
    """Facture fournisseur reçue."""
    __tablename__ = "supplier_invoices"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    purchase_order_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("purchase_orders.id", ondelete="SET NULL")
    )
    supplier_ref: Mapped[str | None] = mapped_column(String(100))  # Numéro chez le fournisseur
    our_ref: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default=SupplierInvoiceStatus.RECUE)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    subtotal_ht: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    total_tva: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    total_ttc: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    journal_entry_id: Mapped[str | None] = mapped_column(String(36))
    approved_by: Mapped[str | None] = mapped_column(String(36))  # user_id
    approved_at: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    supplier: Mapped["Supplier"] = relationship(back_populates="invoices")
    lines: Mapped[list["SupplierInvoiceLine"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[list["SupplierPayment"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    @property
    def balance_due(self) -> Decimal:
        return self.total_ttc - self.amount_paid

    @property
    def is_overdue(self) -> bool:
        return bool(self.due_date and self.due_date < date.today() and self.balance_due > 0)


class SupplierInvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Ligne de facture fournisseur."""
    __tablename__ = "supplier_invoice_lines"

    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_invoices.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("1.0000"))
    unit_price_ht: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    vat_rate: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("20.00"))
    account_code: Mapped[str] = mapped_column(String(20), default="607")

    @property
    def line_ht(self) -> Decimal:
        return self.quantity * self.unit_price_ht

    @property
    def line_tva(self) -> Decimal:
        return self.line_ht * self.vat_rate / Decimal("100")

    invoice: Mapped["SupplierInvoice"] = relationship(back_populates="lines")


class SupplierPayment(Base, UUIDMixin, TimestampMixin):
    """Paiement d'une facture fournisseur."""
    __tablename__ = "supplier_payments"

    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("supplier_invoices.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), default="VIREMENT")
    reference: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PLANIFIE)
    bank_account_id: Mapped[str | None] = mapped_column(String(36))

    invoice: Mapped["SupplierInvoice"] = relationship(back_populates="payments")
