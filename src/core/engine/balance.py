"""
Balance des comptes et Grand Livre.

Toutes les valeurs sont calculées à la volée depuis les lignes d'écritures
(source de vérité unique). Les soldes dénormalisés sur Account sont
uniquement pour la performance des dashboards.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.core.models.account import Account, AccountNature
from src.core.models.journal_entry import EntryStatus, JournalEntry, JournalEntryLine

ZERO = Decimal("0.00")


@dataclass
class AccountBalance:
    code: str
    name: str
    account_class: str
    account_nature: str
    debit: Decimal = ZERO
    credit: Decimal = ZERO

    @property
    def solde_debiteur(self) -> Decimal:
        d = self.debit - self.credit
        return d if d > ZERO else ZERO

    @property
    def solde_crediteur(self) -> Decimal:
        c = self.credit - self.debit
        return c if c > ZERO else ZERO

    @property
    def solde_net(self) -> Decimal:
        """Positif = débiteur, négatif = créditeur."""
        return self.debit - self.credit


@dataclass
class GrandLivreLine:
    entry_number: str
    entry_date: date
    label: str
    reference: str | None
    debit: Decimal
    credit: Decimal
    running_balance: Decimal


@dataclass
class GrandLivreAccount:
    code: str
    name: str
    opening_balance: Decimal
    lines: list[GrandLivreLine] = field(default_factory=list)

    @property
    def closing_balance(self) -> Decimal:
        return self.opening_balance + sum(
            (l.debit - l.credit) for l in self.lines
        )


def _base_query(session: Session, company_id: str, fiscal_year_id: str | None,
                date_from: date | None, date_to: date | None):
    """Retourne une query sur JournalEntryLine filtrée."""
    q = (
        session.query(JournalEntryLine)
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .filter(
            JournalEntry.company_id == company_id,
            JournalEntry.status == EntryStatus.VALIDE,
        )
    )
    if fiscal_year_id:
        q = q.filter(JournalEntry.fiscal_year_id == fiscal_year_id)
    if date_from:
        q = q.filter(JournalEntry.accounting_date >= date_from)
    if date_to:
        q = q.filter(JournalEntry.accounting_date <= date_to)
    return q


def compute_trial_balance(
    session: Session,
    company_id: str,
    fiscal_year_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    account_class: str | None = None,
) -> list[AccountBalance]:
    """
    Balance générale des comptes (totaux débit/crédit + soldes).
    N'inclut que les comptes ayant au moins un mouvement.
    """
    q = (
        session.query(
            Account.code,
            Account.name,
            Account.account_class,
            Account.account_nature,
            func.coalesce(func.sum(JournalEntryLine.debit), ZERO).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), ZERO).label("total_credit"),
        )
        .join(JournalEntryLine, JournalEntryLine.account_id == Account.id)
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .filter(
            Account.company_id == company_id,
            JournalEntry.company_id == company_id,
            JournalEntry.status == EntryStatus.VALIDE,
        )
        .group_by(Account.code, Account.name, Account.account_class, Account.account_nature)
        .order_by(Account.code)
    )

    if fiscal_year_id:
        q = q.filter(JournalEntry.fiscal_year_id == fiscal_year_id)
    if date_from:
        q = q.filter(JournalEntry.accounting_date >= date_from)
    if date_to:
        q = q.filter(JournalEntry.accounting_date <= date_to)
    if account_class:
        q = q.filter(Account.account_class == account_class)

    return [
        AccountBalance(
            code=row.code,
            name=row.name,
            account_class=row.account_class,
            account_nature=row.account_nature,
            debit=Decimal(str(row.total_debit)),
            credit=Decimal(str(row.total_credit)),
        )
        for row in q.all()
    ]


def compute_grand_livre(
    session: Session,
    company_id: str,
    account_code: str,
    fiscal_year_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> GrandLivreAccount:
    """
    Grand livre d'un compte : liste chronologique de toutes les lignes
    avec solde progressif.
    """
    account = (
        session.query(Account)
        .filter(Account.company_id == company_id, Account.code == account_code)
        .first()
    )
    if not account:
        from src.core.engine.ledger import LedgerError
        raise LedgerError(f"Compte {account_code} introuvable.")

    rows = (
        session.query(
            JournalEntry.entry_number,
            JournalEntry.accounting_date,
            JournalEntryLine.label,
            JournalEntry.reference,
            JournalEntryLine.debit,
            JournalEntryLine.credit,
        )
        .join(JournalEntryLine, JournalEntryLine.entry_id == JournalEntry.id)
        .filter(
            JournalEntry.company_id == company_id,
            JournalEntry.status == EntryStatus.VALIDE,
            JournalEntryLine.account_id == account.id,
        )
        .order_by(JournalEntry.accounting_date, JournalEntry.entry_number)
    )

    if fiscal_year_id:
        rows = rows.filter(JournalEntry.fiscal_year_id == fiscal_year_id)
    if date_from:
        rows = rows.filter(JournalEntry.accounting_date >= date_from)
    if date_to:
        rows = rows.filter(JournalEntry.accounting_date <= date_to)

    gl = GrandLivreAccount(code=account.code, name=account.name, opening_balance=ZERO)
    running = ZERO

    for row in rows.all():
        debit = Decimal(str(row.debit))
        credit = Decimal(str(row.credit))
        running += debit - credit
        gl.lines.append(GrandLivreLine(
            entry_number=row.entry_number,
            entry_date=row.accounting_date,
            label=row.label,
            reference=row.reference,
            debit=debit,
            credit=credit,
            running_balance=running,
        ))

    return gl
