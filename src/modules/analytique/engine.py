"""Moteur analytique — budget vs réalisé, ventilation des écritures."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.modules.analytique.models import AnalyticBudget, AnalyticDistribution


def get_budget_vs_realise(
    section_id: str,
    fiscal_year_id: str,
    db: Session,
) -> list[dict]:
    """
    Retourne le budget vs réalisé par mois pour une section analytique.
    Chaque entrée : {month, budget, realized, variance, variance_pct}.
    """
    budgets = (
        db.query(AnalyticBudget)
        .filter(
            AnalyticBudget.section_id == section_id,
            AnalyticBudget.fiscal_year_id == fiscal_year_id,
        )
        .order_by(AnalyticBudget.period_month)
        .all()
    )

    result = []
    for b in budgets:
        variance = b.realized_amount - b.budget_amount
        if b.budget_amount != 0:
            pct = (variance / b.budget_amount * 100).quantize(Decimal("0.01"))
        else:
            pct = None
        result.append({
            "month": b.period_month,
            "account_code": b.account_code,
            "budget": b.budget_amount,
            "realized": b.realized_amount,
            "variance": variance,
            "variance_pct": pct,
        })
    return result


def distribute_line(
    journal_line_id: str,
    section_percentages: list[dict],  # [{"section_id": ..., "percentage": Decimal, "amount": Decimal}]
    fiscal_year_id: str,
    company_id: str,
    db: Session,
) -> list[AnalyticDistribution]:
    """
    Crée les AnalyticDistribution pour une ligne d'écriture.
    Vérifie que la somme des pourcentages = 100.
    """
    total_pct = sum(Decimal(str(d["percentage"])) for d in section_percentages)
    if abs(total_pct - Decimal("100")) > Decimal("0.01"):
        raise ValueError(f"La somme des pourcentages doit être 100, reçu {total_pct}")

    distributions = []
    for item in section_percentages:
        dist = AnalyticDistribution(
            company_id=company_id,
            journal_line_id=journal_line_id,
            section_id=item["section_id"],
            percentage=Decimal(str(item["percentage"])),
            amount=Decimal(str(item["amount"])),
            fiscal_year_id=fiscal_year_id,
        )
        db.add(dist)
        distributions.append(dist)

    db.flush()
    return distributions
