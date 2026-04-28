"""
Moteur de calcul de la TVA.

Calcule les montants CA3 / CA12 à partir des lignes d'écritures
portant un code TVA. Gère les 5 taux français.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.models.journal_entry import EntryStatus, JournalEntry, JournalEntryLine

ZERO = Decimal("0.00")

TVA_RATES = {
    "TVA_20": Decimal("20.00"),
    "TVA_10": Decimal("10.00"),
    "TVA_55": Decimal("5.50"),
    "TVA_21": Decimal("2.10"),
    "TVA_00": Decimal("0.00"),
}


@dataclass
class TVALine:
    vat_code: str
    taux: Decimal
    base_ht: Decimal = ZERO
    tva_collectee: Decimal = ZERO
    tva_deductible: Decimal = ZERO

    @property
    def tva_nette(self) -> Decimal:
        return self.tva_collectee - self.tva_deductible


@dataclass
class TVADeclarationResult:
    periode_debut: date
    periode_fin: date
    lines: list[TVALine] = field(default_factory=list)

    @property
    def total_collectee(self) -> Decimal:
        return sum(l.tva_collectee for l in self.lines)

    @property
    def total_deductible(self) -> Decimal:
        return sum(l.tva_deductible for l in self.lines)

    @property
    def solde_tva(self) -> Decimal:
        """Positif = TVA due ; négatif = crédit de TVA."""
        return self.total_collectee - self.total_deductible


# Comptes TVA collectée et déductible (PCG)
_TVA_COLLECTEE_PREFIXES = ("44571",)
_TVA_DEDUCTIBLE_PREFIXES = ("44566", "44562")


def compute_tva_declaration(
    session: Session,
    company_id: str,
    periode_debut: date,
    periode_fin: date,
) -> TVADeclarationResult:
    """
    Calcule la déclaration TVA pour la période demandée.

    Méthode : agrégation des lignes d'écritures par code TVA.
    - Lignes sur comptes 44571* → TVA collectée
    - Lignes sur comptes 44566*, 44562* → TVA déductible
    - Lignes avec vat_code renseigné → base HT
    """
    from sqlalchemy import func

    from src.core.models.account import Account

    result = TVADeclarationResult(periode_debut=periode_debut, periode_fin=periode_fin)
    lines_by_code: dict[str, TVALine] = {}

    # TVA collectée par code
    coll_rows = (
        session.query(
            JournalEntryLine.vat_code,
            func.sum(JournalEntryLine.credit - JournalEntryLine.debit).label("montant"),
        )
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .filter(
            JournalEntry.company_id == company_id,
            JournalEntry.status == EntryStatus.VALIDE,
            JournalEntry.accounting_date >= periode_debut,
            JournalEntry.accounting_date <= periode_fin,
            Account.code.like("44571%"),
        )
        .group_by(JournalEntryLine.vat_code)
        .all()
    )

    for row in coll_rows:
        code = row.vat_code or "TVA_20"
        if code not in lines_by_code:
            lines_by_code[code] = TVALine(vat_code=code, taux=TVA_RATES.get(code, ZERO))
        lines_by_code[code].tva_collectee += Decimal(str(row.montant or 0))

    # TVA déductible par code
    deduc_rows = (
        session.query(
            JournalEntryLine.vat_code,
            func.sum(JournalEntryLine.debit - JournalEntryLine.credit).label("montant"),
        )
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .filter(
            JournalEntry.company_id == company_id,
            JournalEntry.status == EntryStatus.VALIDE,
            JournalEntry.accounting_date >= periode_debut,
            JournalEntry.accounting_date <= periode_fin,
            Account.code.in_(["44566", "44562"]),
        )
        .group_by(JournalEntryLine.vat_code)
        .all()
    )

    for row in deduc_rows:
        code = row.vat_code or "TVA_20"
        if code not in lines_by_code:
            lines_by_code[code] = TVALine(vat_code=code, taux=TVA_RATES.get(code, ZERO))
        lines_by_code[code].tva_deductible += Decimal(str(row.montant or 0))

    result.lines = sorted(lines_by_code.values(), key=lambda l: l.taux, reverse=True)
    return result
