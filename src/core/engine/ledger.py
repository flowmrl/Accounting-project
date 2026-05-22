"""
Grand livre — moteur central de validation et de comptabilisation.

Règles invariantes :
  - Une écriture doit être équilibrée (∑débit = ∑crédit).
  - Une écriture validée est immuable : toute correction passe par extourne.
  - Un exercice clôturé définitivement est en lecture seule.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.core.models.account import Account
from src.core.models.fiscal_year import FiscalYearStatus
from src.core.models.journal_entry import EntryStatus, JournalEntry, JournalEntryLine

if TYPE_CHECKING:
    pass

ZERO = Decimal("0.00")


class LedgerError(Exception):
    """Erreur métier comptable."""


@dataclass
class LineInput:
    account_code: str
    label: str
    debit: Decimal = ZERO
    credit: Decimal = ZERO
    vat_code: str | None = None
    analytic_account_id: str | None = None
    currency: str | None = None
    amount_currency: Decimal | None = None


@dataclass
class EntryInput:
    company_id: str
    journal_id: str
    fiscal_year_id: str
    entry_date: object          # datetime.date
    label: str
    lines: list[LineInput] = field(default_factory=list)
    reference: str | None = None
    currency: str = "EUR"
    exchange_rate: Decimal = Decimal("1.000000")
    attachment_url: str | None = None


def _next_entry_number(session: Session, journal_id: str) -> str:
    from sqlalchemy import func
    count = (
        session.query(func.count(JournalEntry.id))
        .filter(JournalEntry.journal_id == journal_id)
        .scalar()
    ) or 0
    from src.core.models.journal import Journal
    journal = session.get(Journal, journal_id)
    code = journal.code if journal else "OD"
    from src.core.models.fiscal_year import FiscalYear
    fy = session.get(FiscalYear, journal.fiscal_year_id) if journal else None
    year = fy.start_date.year if fy else "????"
    return f"{code}{year}/{count + 1:05d}"


def validate_lines(lines: list[LineInput]) -> None:
    """Lève LedgerError si les lignes ne sont pas équilibrées ou invalides."""
    if len(lines) < 2:
        raise LedgerError("Une écriture doit comporter au moins 2 lignes.")

    total_debit = sum(l.debit for l in lines)
    total_credit = sum(l.credit for l in lines)

    if total_debit != total_credit:
        raise LedgerError(
            f"Écriture déséquilibrée : débit {total_debit} ≠ crédit {total_credit}."
        )

    for line in lines:
        if line.debit < ZERO or line.credit < ZERO:
            raise LedgerError("Les montants débit/crédit doivent être positifs ou nuls.")
        if line.debit > ZERO and line.credit > ZERO:
            raise LedgerError(
                f"Ligne '{line.label}' : débit et crédit ne peuvent être tous deux non nuls."
            )


def post_entry(session: Session, inp: EntryInput) -> JournalEntry:
    """
    Crée et valide une écriture comptable.

    1. Vérifie l'équilibre débit/crédit.
    2. Vérifie que l'exercice n'est pas clôturé définitivement.
    3. Résout les codes de comptes → Account.id.
    4. Crée JournalEntry + JournalEntryLine et les flush.
    5. Met à jour les soldes dénormalisés sur Account.
    """
    validate_lines(inp.lines)

    from src.core.models.fiscal_year import FiscalYear
    fy = session.get(FiscalYear, inp.fiscal_year_id)
    if fy and fy.status == FiscalYearStatus.CLOTURE_DEFINITIF:
        raise LedgerError("Impossible de saisir sur un exercice clôturé définitivement.")

    # Résoudre codes → Account
    codes = {line.account_code for line in inp.lines}
    accounts: dict[str, Account] = {
        a.code: a
        for a in session.query(Account).filter(
            Account.company_id == inp.company_id,
            Account.code.in_(codes),
            Account.standard == "PCG",
        ).all()
    }
    missing = codes - accounts.keys()
    if missing:
        raise LedgerError(f"Comptes introuvables : {sorted(missing)}")

    entry_number = _next_entry_number(session, inp.journal_id)

    entry = JournalEntry(
        company_id=inp.company_id,
        journal_id=inp.journal_id,
        fiscal_year_id=inp.fiscal_year_id,
        entry_number=entry_number,
        entry_date=inp.entry_date,
        accounting_date=inp.entry_date,
        label=inp.label,
        reference=inp.reference,
        status=EntryStatus.VALIDE,
        currency=inp.currency,
        exchange_rate=inp.exchange_rate,
        attachment_url=inp.attachment_url,
    )
    session.add(entry)
    session.flush()  # obtenir entry.id

    for seq, line in enumerate(inp.lines):
        account = accounts[line.account_code]
        jl = JournalEntryLine(
            entry_id=entry.id,
            account_id=account.id,
            sequence=seq,
            label=line.label,
            debit=line.debit,
            credit=line.credit,
            vat_code=line.vat_code,
            analytic_account_id=line.analytic_account_id,
            currency=line.currency,
            amount_currency=line.amount_currency,
        )
        session.add(jl)
        # Mise à jour des soldes dénormalisés
        account.balance_debit += line.debit
        account.balance_credit += line.credit

    session.flush()
    return entry


def reverse_entry(session: Session, entry_id: str, reverse_date: object) -> JournalEntry:
    """Crée une écriture de contrepassation (extourne) d'une écriture validée."""
    original = session.get(JournalEntry, entry_id)
    if not original:
        raise LedgerError(f"Écriture {entry_id} introuvable.")
    if original.status != EntryStatus.VALIDE:
        raise LedgerError("Seules les écritures validées peuvent être extournées.")

    reversed_lines = [
        LineInput(
            account_code=session.get(Account, line.account_id).code,
            label=f"[EXTOURNE] {line.label}",
            debit=line.credit,   # inversion
            credit=line.debit,
        )
        for line in original.lines
    ]

    inp = EntryInput(
        company_id=original.company_id,
        journal_id=original.journal_id,
        fiscal_year_id=original.fiscal_year_id,
        entry_date=reverse_date,
        label=f"[EXTOURNE] {original.label}",
        lines=reversed_lines,
        currency=original.currency,
    )
    reversal = post_entry(session, inp)
    reversal.reversed_entry_id = entry_id
    reversal.is_auto_generated = True
    session.flush()
    return reversal
