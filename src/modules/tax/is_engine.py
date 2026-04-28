"""
Calcul de l'Impôt sur les Sociétés (IS).

Taux 2025 :
  - Taux réduit PME : 15 % sur les 42 500 premiers € de bénéfice
    (CA < 10 M€, capital libéré et détenu à 75 % par des personnes physiques)
  - Taux normal : 25 % au-delà
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0.00")
SEUIL_TAUX_REDUIT = Decimal("42500.00")
TAUX_REDUIT = Decimal("0.15")
TAUX_NORMAL = Decimal("0.25")
SEUIL_CA_PME = Decimal("10000000.00")


def _round2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class ISResult:
    resultat_fiscal: Decimal
    is_taux_reduit: Decimal
    is_taux_normal: Decimal
    is_total: Decimal
    is_pme_eligible: bool


def compute_is(
    resultat_fiscal: Decimal,
    chiffre_affaires: Decimal,
    is_pme: bool = True,
) -> ISResult:
    """
    Calcule l'IS dû sur le résultat fiscal.

    Args:
        resultat_fiscal: Résultat fiscal net (après réintégrations/déductions).
        chiffre_affaires: CA HT de l'exercice (pour vérification éligibilité PME).
        is_pme: True si la société remplit les conditions PME (capital, actionnariat).
    """
    if resultat_fiscal <= ZERO:
        return ISResult(
            resultat_fiscal=resultat_fiscal,
            is_taux_reduit=ZERO,
            is_taux_normal=ZERO,
            is_total=ZERO,
            is_pme_eligible=False,
        )

    pme_eligible = is_pme and chiffre_affaires < SEUIL_CA_PME

    if pme_eligible:
        base_reduite = min(resultat_fiscal, SEUIL_TAUX_REDUIT)
        base_normale = max(ZERO, resultat_fiscal - SEUIL_TAUX_REDUIT)
        is_reduit = _round2(base_reduite * TAUX_REDUIT)
        is_normal = _round2(base_normale * TAUX_NORMAL)
    else:
        is_reduit = ZERO
        is_normal = _round2(resultat_fiscal * TAUX_NORMAL)

    return ISResult(
        resultat_fiscal=resultat_fiscal,
        is_taux_reduit=is_reduit,
        is_taux_normal=is_normal,
        is_total=is_reduit + is_normal,
        is_pme_eligible=pme_eligible,
    )


def compute_resultat_fiscal(
    resultat_comptable: Decimal,
    reintegrations: list[tuple[str, Decimal]] | None = None,
    deductions: list[tuple[str, Decimal]] | None = None,
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Calcule le résultat fiscal depuis le résultat comptable.
    Retourne (resultat_fiscal, total_reintegrations, total_deductions).

    Réintégrations courantes : amendes (6711), quote-part sur VMP,
      amortissements excédentaires, provision non déductible…
    Déductions courantes : plus-values exonérées, dividendes régime mère-fille,
      amortissements dérogatoires repris…
    """
    total_reint = sum(m for _, m in (reintegrations or []))
    total_deduc = sum(m for _, m in (deductions or []))
    rf = resultat_comptable + total_reint - total_deduc
    return rf, total_reint, total_deduc


def compute_deferred_taxes(
    temporary_differences: list[tuple[str, str, Decimal]],
    taux_is: Decimal = TAUX_NORMAL,
) -> list[dict]:
    """
    Calcule les impôts différés actifs/passifs.

    Args:
        temporary_differences: liste de (label, nature, base_temporaire)
            nature ∈ {"IDA", "IDP"}
        taux_is: taux d'IS applicable (défaut 25 %)

    Retourne une liste de dicts avec montant calculé.
    """
    result = []
    for label, nature, base in temporary_differences:
        montant = _round2(abs(base) * taux_is)
        result.append({
            "label": label,
            "nature": nature,
            "base_temporaire": base,
            "taux_is": taux_is,
            "montant": montant if nature == "IDA" else -montant,
        })
    return result
