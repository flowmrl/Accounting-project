"""Modèles du module Facturation Clients (devis → facture → avoir)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin, UUIDMixin


class DocumentType(StrEnum):
    DEVIS = "DEVIS"
    BON_COMMANDE = "BON_COMMANDE"
    FACTURE = "FACTURE"
    AVOIR = "AVOIR"
    FACTURE_ACOMPTE = "FACTURE_ACOMPTE"


class DocumentStatus(StrEnum):
    BROUILLON = "BROUILLON"
    ENVOYE = "ENVOYE"
    ACCEPTE = "ACCEPTE"          # Devis accepté
    REFUSE = "REFUSE"            # Devis refusé
    PARTIELLEMENT_PAYE = "PARTIELLEMENT_PAYE"
    PAYE = "PAYE"
    EN_RETARD = "EN_RETARD"
    ANNULE = "ANNULE"


class EInvoicingFormat(StrEnum):
    """Formats facture électronique (obligation 2026 France)."""
    NONE = "NONE"
    FACTUR_X = "FACTUR_X"        # PDF/A-3 embarquant XML (norme EN 16931)
    UBL = "UBL"                  # Universal Business Language
    CII = "CII"                  # Cross Industry Invoice
    CHORUS_PRO = "CHORUS_PRO"    # Portail public Chorus Pro (commandes publiques)


class Invoice(Base, UUIDMixin, TimestampMixin):
    """Document commercial (devis, facture, avoir)."""
    __tablename__ = "invoices"

    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=DocumentStatus.BROUILLON)

    number: Mapped[str | None] = mapped_column(String(50))        # Numéro attribué à la validation
    reference: Mapped[str | None] = mapped_column(String(100))    # Référence interne / commande client

    # Client
    customer_id: Mapped[str | None] = mapped_column(String(36))   # FK vers future table Contact
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_address: Mapped[str | None] = mapped_column(Text)
    customer_siren: Mapped[str | None] = mapped_column(String(9))
    customer_tva_intracom: Mapped[str | None] = mapped_column(String(20))

    # Dates
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    delivery_date: Mapped[date | None] = mapped_column(Date)
    validity_date: Mapped[date | None] = mapped_column(Date)      # Pour devis

    # Montants (calculés depuis les lignes)
    subtotal_ht: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    total_tva: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    total_ttc: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"))

    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("1.000000"))

    # Conditions de paiement
    payment_terms: Mapped[str | None] = mapped_column(String(100))  # ex: "30 jours nets"
    payment_method: Mapped[str | None] = mapped_column(String(50))  # virement, chèque, CB…
    iban: Mapped[str | None] = mapped_column(String(34))

    # Avoir : lien vers facture d'origine
    credited_invoice_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="SET NULL")
    )
    # Facture : lien vers le devis accepté
    source_quote_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="SET NULL")
    )

    # Écriture comptable générée
    journal_entry_id: Mapped[str | None] = mapped_column(String(36))

    # Facture électronique
    einvoicing_format: Mapped[str] = mapped_column(String(20), default=EInvoicingFormat.NONE)
    einvoicing_sent_at: Mapped[date | None] = mapped_column(Date)
    einvoicing_status: Mapped[str | None] = mapped_column(String(50))

    notes: Mapped[str | None] = mapped_column(Text)
    footer_text: Mapped[str | None] = mapped_column(Text)

    lines: Mapped[list["InvoiceLine"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan",
        order_by="InvoiceLine.sequence"
    )
    reminders: Mapped[list["PaymentReminder"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    @property
    def balance_due(self) -> Decimal:
        return self.total_ttc - self.amount_paid

    @property
    def is_overdue(self) -> bool:
        from datetime import date as d
        return bool(self.due_date and self.due_date < d.today() and self.balance_due > 0)

    def __repr__(self) -> str:
        return f"<Invoice {self.number or 'DRAFT'} {self.customer_name} {self.total_ttc}>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """Ligne d'une facture / devis."""
    __tablename__ = "invoice_lines"

    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(default=0)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))

    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("1.0000"))
    unit: Mapped[str | None] = mapped_column(String(20))           # h, jour, unité…
    unit_price_ht: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"))

    vat_rate: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("20.00"))
    vat_code: Mapped[str] = mapped_column(String(10), default="TVA_20")

    # Compte de produit (ex: "706")
    account_code: Mapped[str] = mapped_column(String(20), default="706")

    @property
    def line_ht(self) -> Decimal:
        base = self.quantity * self.unit_price_ht
        return base * (1 - self.discount_pct / Decimal("100"))

    @property
    def line_tva(self) -> Decimal:
        return self.line_ht * self.vat_rate / Decimal("100")

    @property
    def line_ttc(self) -> Decimal:
        return self.line_ht + self.line_tva

    invoice: Mapped["Invoice"] = relationship(back_populates="lines")


class PaymentReminder(Base, UUIDMixin, TimestampMixin):
    """Relance de paiement envoyée au client."""
    __tablename__ = "payment_reminders"

    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    level: Mapped[int] = mapped_column(default=1)  # 1=amiable, 2=ferme, 3=mise en demeure
    sent_at: Mapped[date] = mapped_column(Date, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="EMAIL")  # EMAIL | COURRIER | SMS
    notes: Mapped[str | None] = mapped_column(Text)

    invoice: Mapped["Invoice"] = relationship(back_populates="reminders")
