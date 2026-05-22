"""Tests — moteur IS (Impôt sur les Sociétés)."""
from decimal import Decimal

import pytest

from src.modules.tax.is_engine import compute_is, compute_resultat_fiscal


class TestComputeIS:
    def test_pme_taux_reduit_seul(self):
        # Bénéfice < 42 500 € → uniquement taux réduit 15%
        result = compute_is(
            resultat_fiscal=Decimal("30000"),
            chiffre_affaires=Decimal("5_000_000"),
            is_pme=True,
        )
        assert result.is_taux_reduit == Decimal("30000") * Decimal("0.15")
        assert result.is_taux_normal == Decimal("0")
        assert result.is_total == result.is_taux_reduit

    def test_pme_tranche_mixte(self):
        # Bénéfice = 80 000 € → 15% sur 42 500 + 25% sur 37 500
        result = compute_is(
            resultat_fiscal=Decimal("80000"),
            chiffre_affaires=Decimal("5_000_000"),
            is_pme=True,
        )
        expected_reduit = Decimal("42500") * Decimal("0.15")  # 6 375
        expected_normal = Decimal("37500") * Decimal("0.25")  # 9 375
        assert result.is_taux_reduit == expected_reduit
        assert result.is_taux_normal == expected_normal
        assert result.is_total == expected_reduit + expected_normal  # 15 750

    def test_taux_plein_non_pme(self):
        result = compute_is(
            resultat_fiscal=Decimal("100000"),
            chiffre_affaires=Decimal("50_000_000"),
            is_pme=False,
        )
        assert result.is_taux_reduit == Decimal("0")
        assert result.is_taux_normal == Decimal("25000")
        assert result.is_total == Decimal("25000")

    def test_pme_ca_trop_eleve_pas_eligible(self):
        # CA >= 10M → pas éligible taux réduit
        result = compute_is(
            resultat_fiscal=Decimal("50000"),
            chiffre_affaires=Decimal("15_000_000"),
            is_pme=True,
        )
        assert result.is_taux_reduit == Decimal("0")
        assert result.is_total == Decimal("50000") * Decimal("0.25")

    def test_resultat_negatif_is_zero(self):
        result = compute_is(
            resultat_fiscal=Decimal("-10000"),
            chiffre_affaires=Decimal("1_000_000"),
        )
        assert result.is_total == Decimal("0")

    def test_pme_eligible_flag(self):
        result = compute_is(
            resultat_fiscal=Decimal("50000"),
            chiffre_affaires=Decimal("5_000_000"),
            is_pme=True,
        )
        assert result.is_pme_eligible is True

    def test_pme_not_eligible_large_ca(self):
        result = compute_is(
            resultat_fiscal=Decimal("50000"),
            chiffre_affaires=Decimal("20_000_000"),
            is_pme=True,
        )
        assert result.is_pme_eligible is False


class TestComputeResultatFiscal:
    def test_simple_no_adjustments(self):
        rf, total_reint, total_ded = compute_resultat_fiscal(
            resultat_comptable=Decimal("100000"),
        )
        assert rf == Decimal("100000")
        assert total_reint == Decimal("0")
        assert total_ded == Decimal("0")

    def test_with_reintegrations(self):
        rf, total_reint, total_ded = compute_resultat_fiscal(
            resultat_comptable=Decimal("100000"),
            reintegrations=[("Amende", Decimal("5000"))],
        )
        assert rf == Decimal("105000")
        assert total_reint == Decimal("5000")

    def test_with_deductions(self):
        rf, total_reint, total_ded = compute_resultat_fiscal(
            resultat_comptable=Decimal("100000"),
            deductions=[("Plus-value exo", Decimal("10000"))],
        )
        assert rf == Decimal("90000")
        assert total_ded == Decimal("10000")

    def test_mixed(self):
        rf, _, _ = compute_resultat_fiscal(
            resultat_comptable=Decimal("50000"),
            reintegrations=[("Charge non déductible", Decimal("10000"))],
            deductions=[("Abattement", Decimal("5000"))],
        )
        assert rf == Decimal("55000")
