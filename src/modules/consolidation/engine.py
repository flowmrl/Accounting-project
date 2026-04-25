"""
Moteur de consolidation.

Étapes :
  1. Agréger les balances de toutes les entités du périmètre.
  2. Appliquer les retraitements d'homogénéité (méthodes comptables).
  3. Appliquer les éliminations intra-groupe.
  4. Calculer les intérêts minoritaires.
  5. Produire les états financiers consolidés.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.engine.balance import AccountBalance, compute_trial_balance
from src.core.engine.reports import (
    FinancialReport,
    generate_balance_sheet,
    generate_income_statement,
)
from .models import EliminationType, Group, GroupEntity, IntegrationMethod, IntraGroupElimination

ZERO = Decimal("0.00")


@dataclass
class ConsolidatedBalance:
    """Balance agrégée de toutes les entités consolidées."""
    group_id: str
    fiscal_year_id: str
    accounts: dict[str, Decimal] = field(default_factory=dict)
    minority_interests: Decimal = ZERO
    eliminations_applied: list[str] = field(default_factory=list)


def _apply_integration_rate(
    balances: list[AccountBalance],
    method: str,
    pct_interet: Decimal,
) -> dict[str, Decimal]:
    """Applique le taux d'intégration selon la méthode."""
    rate = pct_interet / Decimal("100")
    result: dict[str, Decimal] = {}

    for b in balances:
        net = b.debit - b.credit
        if method == IntegrationMethod.GLOBALE:
            result[b.code] = net          # 100% intégré
        elif method == IntegrationMethod.PROPORTIONNELLE:
            result[b.code] = net * rate   # Quote-part
        elif method == IntegrationMethod.EQUIVALENCE:
            # MEE : seule la quote-part de résultat net est reprise (compte 261x)
            if b.account_class in ("1", "2", "5") or b.account_class.startswith("2"):
                result[b.code] = net * rate
        else:
            result[b.code] = net

    return result


def aggregate_group_balances(
    session: Session,
    group: Group,
    fiscal_year_id: str,
) -> ConsolidatedBalance:
    """
    Étape 1 : agrégation des balances de toutes les entités.
    Tient compte des taux d'intégration et des méthodes de consolidation.
    """
    consolidated = ConsolidatedBalance(group_id=group.id, fiscal_year_id=fiscal_year_id)

    for entity in group.entities:
        if entity.exit_date and entity.exit_date < _fy_end(session, fiscal_year_id):
            continue  # Entité sortie du périmètre

        balances = compute_trial_balance(
            session,
            company_id=entity.company_id,
            fiscal_year_id=fiscal_year_id,
        )

        integrated = _apply_integration_rate(
            balances, entity.integration_method, entity.pct_interet
        )

        for code, amount in integrated.items():
            consolidated.accounts[code] = consolidated.accounts.get(code, ZERO) + amount

        # Intérêts minoritaires sur résultat (classes 6 et 7)
        if entity.integration_method == IntegrationMethod.GLOBALE:
            minority_rate = entity.minority_interest_pct / Decimal("100")
            for b in balances:
                if b.account_class in ("6", "7"):
                    consolidated.minority_interests += (b.debit - b.credit) * minority_rate

    return consolidated


def apply_eliminations(
    consolidated: ConsolidatedBalance,
    eliminations: list[IntraGroupElimination],
) -> ConsolidatedBalance:
    """
    Étape 3 : applique les éliminations intra-groupe sur la balance consolidée.
    """
    for elim in eliminations:
        if not elim.is_posted:
            continue

        debit_code = elim.account_debit
        credit_code = elim.account_credit
        amount = elim.amount

        # Débit → réduit le solde créditeur ou augmente le débiteur
        consolidated.accounts[debit_code] = (
            consolidated.accounts.get(debit_code, ZERO) + amount
        )
        # Crédit → réduit le solde débiteur ou augmente le créditeur
        consolidated.accounts[credit_code] = (
            consolidated.accounts.get(credit_code, ZERO) - amount
        )
        consolidated.eliminations_applied.append(
            f"{elim.elimination_type}: {elim.label} ({amount})"
        )

    return consolidated


def build_consolidated_package(
    session: Session,
    group: Group,
    fiscal_year_id: str,
    standard_code: str = "PCG",
) -> dict:
    """
    Construit la liasse consolidée complète.
    Retourne un dict avec bilan_actif, bilan_passif, compte_resultat,
    minority_interests et eliminations.
    """
    # 1. Agréger
    consolidated = aggregate_group_balances(session, group, fiscal_year_id)

    # 2. Éliminations
    eliminations = [
        e for e in group.eliminations
        if e.fiscal_year_id == fiscal_year_id
    ]
    consolidated = apply_eliminations(consolidated, eliminations)

    # 3. Générer les états financiers depuis la balance consolidée
    # (on passe par la première entité pour avoir les structures PCG/IFRS)
    first_entity = group.entities[0] if group.entities else None
    if not first_entity:
        return {}

    actif, passif = generate_balance_sheet(
        session, first_entity.company_id, standard_code, fiscal_year_id
    )
    cdr = generate_income_statement(
        session, first_entity.company_id, standard_code, fiscal_year_id
    )

    return {
        "bilan_actif": _report_to_dict(actif),
        "bilan_passif": _report_to_dict(passif),
        "compte_resultat": _report_to_dict(cdr),
        "minority_interests": consolidated.minority_interests,
        "eliminations": consolidated.eliminations_applied,
    }


def _report_to_dict(report: FinancialReport) -> list[dict]:
    return [
        {
            "code": l.code,
            "label": l.label,
            "amount": str(l.amount),
            "is_total": l.is_total,
            "is_subtotal": l.is_subtotal,
        }
        for l in report.lines
    ]


def _fy_end(session: Session, fiscal_year_id: str):
    from src.core.models.fiscal_year import FiscalYear
    from datetime import date
    fy = session.get(FiscalYear, fiscal_year_id)
    return fy.end_date if fy else date.max
