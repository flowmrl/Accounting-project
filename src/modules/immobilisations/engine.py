"""
Calcul des plans d'amortissement.

Méthodes supportées : linéaire, dégressif fiscal (coefficients légaux),
unités d'œuvre, non amortissable.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from .models import DepreciationLine, DepreciationMethod, FixedAsset

ZERO = Decimal("0.00")

# Coefficients dégressifs légaux (art. 39 A CGI)
DEGRESSIVE_COEFF = {
    3: Decimal("1.25"),
    4: Decimal("1.25"),
    5: Decimal("1.75"),
    6: Decimal("1.75"),
    7: Decimal("2.25"),
    8: Decimal("2.25"),
    10: Decimal("2.25"),
}


def _coeff_degressif(years: int) -> Decimal:
    for limit in sorted(DEGRESSIVE_COEFF):
        if years <= limit:
            return DEGRESSIVE_COEFF[limit]
    return Decimal("2.25")


def _round2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_depreciation_plan(asset: FixedAsset) -> list[DepreciationLine]:
    """
    Calcule le plan d'amortissement complet d'une immobilisation.
    Retourne une liste de DepreciationLine (non persistées).
    """
    if asset.depreciation_method == DepreciationMethod.NON_AMORTISSABLE:
        return []

    start = asset.commissioning_date or asset.acquisition_date
    years = asset.useful_life_years or 5
    base = asset.acquisition_cost - asset.residual_value
    lines: list[DepreciationLine] = []

    if asset.depreciation_method == DepreciationMethod.LINEAIRE:
        lines = _plan_lineaire(asset, start, years, base)
    elif asset.depreciation_method == DepreciationMethod.DEGRESSIF:
        lines = _plan_degressif(asset, start, years, base)
    elif asset.depreciation_method == DepreciationMethod.UO:
        lines = []  # calculé dynamiquement selon production réelle

    return lines


def _plan_lineaire(asset: FixedAsset, start: date, years: int, base: Decimal) -> list[DepreciationLine]:
    annual = _round2(base / Decimal(years))
    lines = []
    cumul = ZERO

    for y in range(years):
        period = date(start.year + y, 12, 31)

        # Prorata temporis première année
        if y == 0:
            days_in_year = 360
            days_used = (date(start.year, 12, 31) - start).days + 1
            amount = _round2(annual * Decimal(days_used) / Decimal(days_in_year))
        elif y == years - 1:
            amount = base - cumul  # solde résiduel
        else:
            amount = annual

        cumul += amount
        lines.append(DepreciationLine(
            asset_id=asset.id,
            period_date=period,
            amount=amount,
            accounting_amount=amount,
            cumulative_at_start=cumul - amount,
            net_book_value_after=_round2(base - cumul + asset.residual_value),
        ))

    return lines


def _plan_degressif(asset: FixedAsset, start: date, years: int, base: Decimal) -> list[DepreciationLine]:
    coeff = asset.degressive_rate or _coeff_degressif(years)
    rate_degressif = _round2(Decimal("1") / Decimal(years) * coeff)
    rate_lineaire = _round2(Decimal("1") / Decimal(years))

    lines = []
    valeur_residuelle = base
    cumul = ZERO

    for y in range(years):
        period = date(start.year + y, 12, 31)
        remaining_years = years - y
        rate_lin_restant = _round2(Decimal("1") / Decimal(remaining_years)) if remaining_years else ZERO

        # Basculement linéaire si taux linéaire > taux dégressif
        rate = max(rate_degressif, rate_lin_restant)
        amount = _round2(valeur_residuelle * rate)

        if y == years - 1:
            amount = valeur_residuelle  # solde

        cumul += amount
        valeur_residuelle -= amount

        lines.append(DepreciationLine(
            asset_id=asset.id,
            period_date=period,
            amount=amount,
            accounting_amount=amount,
            cumulative_at_start=cumul - amount,
            net_book_value_after=_round2(valeur_residuelle + asset.residual_value),
        ))

    return lines


def post_depreciation(
    asset: FixedAsset,
    line: DepreciationLine,
    session: object,
) -> None:
    """
    Comptabilise une ligne d'amortissement dans le grand livre.
    Crée l'écriture : 681x / 28xx
    """
    from src.core.engine.ledger import EntryInput, LineInput, post_entry

    if line.is_posted:
        return

    depr_account = asset.depreciation_account_code or f"28{asset.account_code[1:]}"

    inp = EntryInput(
        company_id=asset.company_id,
        journal_id=_get_immo_journal(asset.company_id, session),
        fiscal_year_id=_get_fiscal_year(asset.company_id, line.period_date, session),
        entry_date=line.period_date,
        label=f"Amortissement {asset.reference} — {asset.name}",
        lines=[
            LineInput(account_code="6811", label=f"DAP {asset.name}", debit=line.accounting_amount),
            LineInput(account_code=depr_account, label=f"Amort. {asset.name}", credit=line.accounting_amount),
        ],
    )
    entry = post_entry(session, inp)
    line.journal_entry_id = entry.id
    line.is_posted = True
    session.flush()


def _get_immo_journal(company_id: str, session) -> str:
    from src.core.models.journal import Journal, JournalType
    j = session.query(Journal).filter(
        Journal.company_id == company_id,
        Journal.journal_type == JournalType.IMMOBILISATIONS,
    ).first()
    return j.id if j else ""


def _get_fiscal_year(company_id: str, d: date, session) -> str:
    from src.core.models.fiscal_year import FiscalYear
    fy = session.query(FiscalYear).filter(
        FiscalYear.company_id == company_id,
        FiscalYear.start_date <= d,
        FiscalYear.end_date >= d,
    ).first()
    return fy.id if fy else ""
