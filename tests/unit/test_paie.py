"""Tests — Moteur de paie (cotisations sociales)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.modules.paie.engine import BulletinCalcule, LigneCotisation, compute_bulletin


def test_compute_bulletin_basic():
    calc = compute_bulletin(Decimal("3000.00"))
    assert isinstance(calc, BulletinCalcule)
    assert calc.salaire_brut == Decimal("3000.00")
    assert len(calc.lignes) > 0


def test_net_a_payer_less_than_brut():
    calc = compute_bulletin(Decimal("3000.00"))
    assert calc.net_a_payer < calc.salaire_brut


def test_cotisations_salariales_positive():
    calc = compute_bulletin(Decimal("2500.00"))
    assert calc.total_salarial > Decimal("0")


def test_cotisations_patronales_positive():
    calc = compute_bulletin(Decimal("2500.00"))
    assert calc.total_patronal > Decimal("0")


def test_cout_total_employeur_greater_than_brut():
    calc = compute_bulletin(Decimal("3000.00"))
    assert calc.cout_total_employeur > calc.salaire_brut
    assert calc.cout_total_employeur == calc.salaire_brut + calc.total_patronal


def test_cadre_has_more_lines():
    calc_nc = compute_bulletin(Decimal("4000.00"), is_cadre=False)
    calc_c = compute_bulletin(Decimal("4000.00"), is_cadre=True)
    assert len(calc_c.lignes) > len(calc_nc.lignes)


def test_cadre_has_prevoyance_line():
    calc = compute_bulletin(Decimal("4000.00"), is_cadre=True)
    labels = [ln.libelle for ln in calc.lignes]
    assert any("Prévoyance" in l for l in labels)
    assert any("CET" in l for l in labels)


def test_tranche2_for_high_salary():
    # Salaire > 1 PASS → T2 doit apparaître
    calc = compute_bulletin(Decimal("5000.00"))
    labels = [ln.libelle for ln in calc.lignes]
    assert any("T2" in l for l in labels)


def test_no_tranche2_for_low_salary():
    # Salaire < PASS → pas de T2
    calc = compute_bulletin(Decimal("2000.00"))
    labels = [ln.libelle for ln in calc.lignes]
    assert not any("T2" in l for l in labels)


def test_csg_line_present():
    calc = compute_bulletin(Decimal("3000.00"))
    labels = [ln.libelle for ln in calc.lignes]
    assert any("CSG" in l for l in labels)


def test_vieillesse_plafonnee_capped():
    # La base vieillesse plafonnée ne peut dépasser 1 PASS
    from src.modules.paie.engine import PASS_MENSUEL
    calc = compute_bulletin(Decimal("8000.00"))
    for ln in calc.lignes:
        if "plafonnée" in ln.libelle and "dé" not in ln.libelle:
            assert ln.base <= PASS_MENSUEL


def test_ligne_cotisation_montants():
    ln = LigneCotisation("Test", Decimal("1000.00"), Decimal("6.9"), Decimal("8.55"))
    assert ln.montant_salarial == Decimal("69.00")
    assert ln.montant_patronal == Decimal("85.50")


def test_bulletin_net_imposable():
    calc = compute_bulletin(Decimal("3000.00"))
    assert calc.net_imposable == calc.salaire_brut - calc.total_salarial
