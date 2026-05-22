"""
Export FEC — Fichier des Écritures Comptables.

Format défini par l'arrêté du 29 juillet 2013 (article A. 47 A-1 du LPF).
Obligatoire pour tout contrôle fiscal en France depuis le 1er janvier 2014.

Spécifications :
  - Séparateur : tabulation (\\t)
  - Encodage : UTF-8
  - 18 champs obligatoires dans l'ordre réglementaire
  - Montants : 2 décimales, séparateur décimal = virgule
  - Dates : YYYYMMDD
"""
from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.models.account import Account
from src.core.models.journal_entry import EntryStatus, JournalEntry, JournalEntryLine

FEC_HEADERS = [
    "JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
    "CompteNum", "CompteLib", "CompAuxNum", "CompAuxLib",
    "PieceRef", "PieceDate", "EcritureLib",
    "Debit", "Credit",
    "EcritureLet", "DateLet",
    "ValidDate",
    "Montantdevise", "Idevise",
]


def _fmt_date(d: date | None) -> str:
    return d.strftime("%Y%m%d") if d else ""


def _fmt_amount(v: Decimal | None) -> str:
    if v is None or v == 0:
        return "0,00"
    return str(v).replace(".", ",")


def export_fec(
    session: Session,
    company_id: str,
    fiscal_year_id: str,
    include_drafts: bool = False,
) -> str:
    """
    Génère le contenu du fichier FEC pour un exercice donné.
    Retourne une chaîne UTF-8 prête à écrire dans un fichier .txt.
    """
    statuses = [EntryStatus.VALIDE]
    if include_drafts:
        statuses.append(EntryStatus.BROUILLON)

    rows = (
        session.query(
            JournalEntry.entry_number,
            JournalEntry.entry_date,
            JournalEntry.accounting_date,
            JournalEntry.reference,
            JournalEntry.label.label("entry_label"),
            JournalEntry.status,
            JournalEntry.currency,
            JournalEntryLine.label.label("line_label"),
            JournalEntryLine.debit,
            JournalEntryLine.credit,
            JournalEntryLine.matching_code,
            JournalEntryLine.amount_currency,
            Account.code.label("account_code"),
            Account.name.label("account_name"),
        )
        .join(JournalEntryLine, JournalEntryLine.entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .filter(
            JournalEntry.company_id == company_id,
            JournalEntry.fiscal_year_id == fiscal_year_id,
            JournalEntry.status.in_(statuses),
        )
        .order_by(JournalEntry.accounting_date, JournalEntry.entry_number, JournalEntryLine.sequence)
        .all()
    )

    # Charger les journaux pour JournalCode / JournalLib
    from src.core.models.journal import Journal
    journals = {
        j.id: j
        for j in session.query(Journal).filter(Journal.company_id == company_id).all()
    }

    # Charger les entries pour retrouver journal_id
    entry_ids = {r.entry_number for r in rows}
    entries_map = {
        e.entry_number: e
        for e in session.query(JournalEntry)
        .filter(JournalEntry.company_id == company_id,
                JournalEntry.entry_number.in_(entry_ids))
        .all()
    }

    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\r\n")
    writer.writerow(FEC_HEADERS)

    for row in rows:
        entry = entries_map.get(row.entry_number)
        journal = journals.get(entry.journal_id) if entry else None

        journal_code = journal.code if journal else ""
        journal_lib = journal.name if journal else ""

        writer.writerow([
            journal_code,                          # JournalCode
            journal_lib,                           # JournalLib
            row.entry_number,                      # EcritureNum
            _fmt_date(row.accounting_date),        # EcritureDate
            row.account_code,                      # CompteNum
            row.account_name,                      # CompteLib
            "",                                    # CompAuxNum (compte auxiliaire)
            "",                                    # CompAuxLib
            row.reference or "",                   # PieceRef
            _fmt_date(row.entry_date),             # PieceDate
            row.line_label,                        # EcritureLib
            _fmt_amount(row.debit),                # Debit
            _fmt_amount(row.credit),               # Credit
            row.matching_code or "",               # EcritureLet
            "",                                    # DateLet
            _fmt_date(row.accounting_date),        # ValidDate
            _fmt_amount(row.amount_currency),      # Montantdevise
            row.currency if row.currency != "EUR" else "",  # Idevise
        ])

    return output.getvalue()


def write_fec_file(content: str, path: str) -> None:
    """Écrit le FEC sur disque en UTF-8 avec BOM (requis par certains logiciels DGFiP)."""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(content)
