"""
Génération des états financiers (Bilan, CdR, TFT) depuis la balance des comptes.

Le moteur calcule les montants en agrégeant les soldes par préfixe de compte
conformément à la structure définie dans le référentiel (PCGFrance ou autre).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.engine.balance import AccountBalance, compute_trial_balance
from src.core.standards.base import FinancialStatement, FinancialStatementLine, StandardRegistry

ZERO = Decimal("0.00")


@dataclass
class ReportLine:
    code: str
    label: str
    amount: Decimal
    is_subtotal: bool = False
    is_total: bool = False
    indent_level: int = 0
    note_ref: str | None = None


@dataclass
class FinancialReport:
    name: str
    standard: str
    as_of: date | None
    lines: list[ReportLine] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return next(
            (l.amount for l in reversed(self.lines) if l.is_total),
            ZERO,
        )


def _balance_index(balances: list[AccountBalance]) -> dict[str, Decimal]:
    """Construit un index code → solde_net pour recherche rapide par préfixe."""
    idx: dict[str, Decimal] = {}
    for b in balances:
        idx[b.code] = b.debit - b.credit
    return idx


def _sum_prefix(idx: dict[str, Decimal], prefixes: list[str], negate: bool = False) -> Decimal:
    """Somme tous les comptes dont le code commence par l'un des préfixes donnés."""
    total = ZERO
    for code, amount in idx.items():
        if any(code.startswith(p) for p in prefixes):
            total += amount
    return -total if negate else total


def _render_statement(
    statement: FinancialStatement,
    idx: dict[str, Decimal],
    as_of: date | None,
) -> FinancialReport:
    report = FinancialReport(name=statement.name, standard=statement.standard, as_of=as_of)

    for sl in statement.lines:
        amount = _sum_prefix(idx, sl.account_codes, negate=sl.negate)
        report.lines.append(ReportLine(
            code=sl.code,
            label=sl.label,
            amount=amount,
            is_subtotal=sl.is_subtotal,
            is_total=sl.is_total,
            indent_level=sl.indent_level,
            note_ref=sl.note_ref,
        ))

    return report


def generate_balance_sheet(
    session: Session,
    company_id: str,
    standard_code: str = "PCG",
    fiscal_year_id: str | None = None,
    as_of: date | None = None,
) -> tuple[FinancialReport, FinancialReport]:
    """Retourne (rapport_actif, rapport_passif)."""
    standard = StandardRegistry.get(standard_code)
    actif_stmt, passif_stmt = standard.get_balance_sheet_structure()

    balances = compute_trial_balance(
        session, company_id, fiscal_year_id=fiscal_year_id, date_to=as_of
    )
    idx = _balance_index(balances)

    return (
        _render_statement(actif_stmt, idx, as_of),
        _render_statement(passif_stmt, idx, as_of),
    )


def generate_income_statement(
    session: Session,
    company_id: str,
    standard_code: str = "PCG",
    fiscal_year_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> FinancialReport:
    """Retourne le compte de résultat sur la période demandée."""
    standard = StandardRegistry.get(standard_code)
    cdr_stmt = standard.get_income_statement_structure()

    balances = compute_trial_balance(
        session, company_id, fiscal_year_id=fiscal_year_id,
        date_from=date_from, date_to=date_to,
    )
    idx = _balance_index(balances)
    return _render_statement(cdr_stmt, idx, date_to)


def generate_cash_flow(
    session: Session,
    company_id: str,
    standard_code: str = "PCG",
    fiscal_year_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> FinancialReport | None:
    """Retourne le TFT si le référentiel en fournit une structure."""
    standard = StandardRegistry.get(standard_code)
    tft_stmt = standard.get_cash_flow_structure()
    if not tft_stmt:
        return None

    balances = compute_trial_balance(
        session, company_id, fiscal_year_id=fiscal_year_id,
        date_from=date_from, date_to=date_to,
    )
    idx = _balance_index(balances)
    return _render_statement(tft_stmt, idx, date_to)


def compute_key_ratios(actif: FinancialReport, passif: FinancialReport, cdr: FinancialReport) -> dict:
    """Ratios financiers clés calculés depuis les états produits."""
    def get(report: FinancialReport, code: str) -> Decimal:
        for l in report.lines:
            if l.code == code:
                return l.amount
        return ZERO

    total_actif = get(actif, "A29")
    capitaux_propres = get(passif, "P8")
    dettes_fin = get(passif, "P13")
    resultat_net = get(cdr, "R30")
    ca = get(cdr, "R9")  # total produits exploitation

    def safe_div(n: Decimal, d: Decimal) -> Decimal | None:
        return round(n / d, 4) if d else None

    return {
        "autonomie_financiere": safe_div(capitaux_propres, total_actif),
        "endettement_net_sur_cp": safe_div(dettes_fin, capitaux_propres),
        "rentabilite_nette": safe_div(resultat_net, ca),
        "return_on_equity": safe_div(resultat_net, capitaux_propres),
        "total_actif": total_actif,
        "capitaux_propres": capitaux_propres,
        "resultat_net": resultat_net,
        "chiffre_affaires": ca,
    }
