"""Tests — moteur TVA."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.core.engine.tva_engine import TVALine, TVADeclarationResult


class TestTVALine:
    def test_creation(self):
        line = TVALine(vat_code="TVA_20", taux=Decimal("20"))
        assert line.vat_code == "TVA_20"
        assert line.base_ht == Decimal("0")
        assert line.tva_collectee == Decimal("0")

    def test_tva_nette(self):
        line = TVALine(
            vat_code="TVA_20",
            taux=Decimal("20"),
            tva_collectee=Decimal("500"),
            tva_deductible=Decimal("200"),
        )
        assert line.tva_nette == Decimal("300")


class TestTVADeclarationResult:
    def test_empty_result(self):
        result = TVADeclarationResult(
            periode_debut=date(2024, 1, 1),
            periode_fin=date(2024, 1, 31),
        )
        assert result.total_collectee == Decimal("0")
        assert result.total_deductible == Decimal("0")
        assert result.solde_tva == Decimal("0")

    def test_solde_positive_means_a_payer(self):
        line = TVALine(vat_code="TVA_20", taux=Decimal("20"),
                       tva_collectee=Decimal("500"), tva_deductible=Decimal("200"))
        result = TVADeclarationResult(
            periode_debut=date(2024, 1, 1),
            periode_fin=date(2024, 1, 31),
            lines=[line],
        )
        assert result.total_collectee == Decimal("500")
        assert result.total_deductible == Decimal("200")
        assert result.solde_tva == Decimal("300")

    def test_solde_negative_means_credit(self):
        line = TVALine(vat_code="TVA_20", taux=Decimal("20"),
                       tva_collectee=Decimal("100"), tva_deductible=Decimal("400"))
        result = TVADeclarationResult(
            periode_debut=date(2024, 1, 1),
            periode_fin=date(2024, 1, 31),
            lines=[line],
        )
        assert result.solde_tva == Decimal("-300")


class TestTVAVatCodes:
    def test_pcg_has_five_rates(self):
        from src.core.standards.pcg_france import PCGFrance
        pcg = PCGFrance()
        vat = pcg.get_vat_codes()
        assert len(vat) == 5

    def test_each_rate_has_required_keys(self):
        from src.core.standards.pcg_france import PCGFrance
        pcg = PCGFrance()
        for code, info in pcg.get_vat_codes().items():
            assert "rate" in info, f"{code}: clé 'rate' manquante"
            assert "label" in info, f"{code}: clé 'label' manquante"
            assert "account_collectee" in info, f"{code}: clé 'account_collectee' manquante"

    def test_rates_are_valid(self):
        from src.core.standards.pcg_france import PCGFrance
        pcg = PCGFrance()
        for code, info in pcg.get_vat_codes().items():
            rate = float(info["rate"])
            assert 0 <= rate <= 100, f"{code}: taux {rate} hors limite"

    @pytest.mark.parametrize("expected_code", ["TVA_20", "TVA_10", "TVA_55", "TVA_21", "TVA_00"])
    def test_specific_vat_codes_present(self, expected_code):
        from src.core.standards.pcg_france import PCGFrance
        pcg = PCGFrance()
        assert expected_code in pcg.get_vat_codes()
