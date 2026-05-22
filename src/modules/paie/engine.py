"""Moteur de calcul de paie — cotisations sociales françaises 2024/2025.

Barèmes simplifiés régime général (URSSAF). Les taux exacts varient selon
la CCN, la tranche, et la situation de l'employé. Ce moteur couvre le cas
général (cadre/non-cadre, régime général).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Plafond Sécurité Sociale 2025
# ---------------------------------------------------------------------------
PASS_MENSUEL = Decimal("3925.00")   # Plafond Annuel SS / 12
PASS_ANNUEL = Decimal("47100.00")


# ---------------------------------------------------------------------------
# Barèmes cotisations (taux en %, base sur salaire brut sauf mention)
# ---------------------------------------------------------------------------

@dataclass
class LigneCotisation:
    libelle: str
    base: Decimal
    taux_salarial: Decimal   # %
    taux_patronal: Decimal   # %

    @property
    def montant_salarial(self) -> Decimal:
        return (self.base * self.taux_salarial / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)

    @property
    def montant_patronal(self) -> Decimal:
        return (self.base * self.taux_patronal / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)


@dataclass
class BulletinCalcule:
    salaire_brut: Decimal
    lignes: list[LigneCotisation] = field(default_factory=list)

    @property
    def total_salarial(self) -> Decimal:
        return sum(ln.montant_salarial for ln in self.lignes)

    @property
    def total_patronal(self) -> Decimal:
        return sum(ln.montant_patronal for ln in self.lignes)

    @property
    def net_imposable(self) -> Decimal:
        return self.salaire_brut - self.total_salarial

    @property
    def net_a_payer(self) -> Decimal:
        # PAS (Prélèvement à la source) non calculé ici — simplifié
        return self.net_imposable

    @property
    def cout_total_employeur(self) -> Decimal:
        return self.salaire_brut + self.total_patronal


def _tranche(salaire: Decimal, plafond_bas: Decimal, plafond_haut: Decimal | None) -> Decimal:
    """Portion du salaire dans une tranche SS."""
    if salaire <= plafond_bas:
        return Decimal("0")
    if plafond_haut is None:
        return salaire - plafond_bas
    return min(salaire, plafond_haut) - plafond_bas


def compute_bulletin(
    salaire_brut: Decimal,
    is_cadre: bool = False,
    pass_mensuel: Decimal = PASS_MENSUEL,
) -> BulletinCalcule:
    """
    Calcule les cotisations sociales pour un salaire brut mensuel.
    Barèmes régime général 2025.
    """
    S = salaire_brut
    P = pass_mensuel
    lignes: list[LigneCotisation] = []

    # --- Assurance maladie ---
    # Taux salarial 0% (supprimé en 2018), patronal 7% (+ 6% si S < 2.5 SMIC)
    lignes.append(LigneCotisation("Assurance maladie", S, Decimal("0"), Decimal("7.00")))

    # --- Allocations familiales ---
    # Patronal : 3.45% si S ≤ 3.5 SMIC, sinon 5.25%
    taux_af = Decimal("3.45") if S <= Decimal("5404.00") else Decimal("5.25")
    lignes.append(LigneCotisation("Allocations familiales", S, Decimal("0"), taux_af))

    # --- Assurance vieillesse plafonné (TA) ---
    ta = min(S, P)
    lignes.append(LigneCotisation("Vieillesse plafonnée (TA)", ta, Decimal("6.90"), Decimal("8.55")))

    # --- Assurance vieillesse déplafonnée ---
    lignes.append(LigneCotisation("Vieillesse déplafonnée", S, Decimal("0.40"), Decimal("1.90")))

    # --- Accidents du travail (estimation 2%) ---
    lignes.append(LigneCotisation("Accidents du travail", S, Decimal("0"), Decimal("2.00")))

    # --- FNAL ---
    fnal = Decimal("0.10") if S <= P else Decimal("0.50")
    lignes.append(LigneCotisation("FNAL", S, Decimal("0"), fnal))

    # --- CSG / CRDS ---
    assiette_csg = S * Decimal("0.9825")  # abattement 1.75%
    lignes.append(LigneCotisation("CSG déductible", assiette_csg, Decimal("6.80"), Decimal("0")))
    lignes.append(LigneCotisation("CSG/CRDS non déductible", assiette_csg, Decimal("2.90"), Decimal("0")))

    # --- Chômage (Unédic) ---
    lignes.append(LigneCotisation("Assurance chômage", S, Decimal("0"), Decimal("4.05")))

    # --- AGS (garantie salaires) ---
    lignes.append(LigneCotisation("AGS (garantie salaires)", S, Decimal("0"), Decimal("0.15")))

    # --- Retraite complémentaire AGIRC-ARRCO ---
    # Tranche 1 : jusqu'à 1 PASS
    t1 = min(S, P)
    lignes.append(LigneCotisation("AGIRC-ARRCO T1", t1, Decimal("3.15"), Decimal("4.72")))
    # Tranche 2 : 1–8 PASS (cadres et non-cadres depuis 2019)
    t2 = _tranche(S, P, P * 8)
    if t2 > 0:
        lignes.append(LigneCotisation("AGIRC-ARRCO T2", t2, Decimal("8.64"), Decimal("12.95")))

    if is_cadre:
        # CET (cotisation exceptionnelle temporaire)
        lignes.append(LigneCotisation("CET Cadres", S, Decimal("0.14"), Decimal("0.21")))
        # Prévoyance cadres (min légal)
        lignes.append(LigneCotisation("Prévoyance cadres (TA)", ta, Decimal("0"), Decimal("1.50")))

    return BulletinCalcule(salaire_brut=S, lignes=lignes)
