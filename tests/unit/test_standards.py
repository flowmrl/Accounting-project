"""Tests — référentiels comptables (StandardRegistry + 12 standards)."""
import pytest

import src.addons.be_gaap.standard
import src.addons.dutch_bw2.standard
import src.addons.german_hgb.standard

# Import all standards to trigger registration
import src.addons.ifrs.standard
import src.addons.italian_oic.standard
import src.addons.luxembourg_gaap.standard
import src.addons.polish_psr.standard
import src.addons.spanish_pgc.standard
import src.addons.swiss_fer.standard
import src.addons.uk_frs.standard
import src.addons.us_gaap.standard
from src.core.standards.base import StandardRegistry
from src.core.standards.pcg_france import PCGFrance


class TestStandardRegistry:
    def test_twelve_standards_registered(self):
        standards = StandardRegistry.list_all()
        codes = {s["code"] for s in standards}
        expected = {"PCG", "IFRS", "US_GAAP", "BE_GAAP", "DE_HGB", "UK_FRS102",
                    "CH_FER", "ES_PGC", "IT_OIC", "NL_BW2", "PL_PSR", "LU_GAAP"}
        assert expected.issubset(codes), f"Manquants: {expected - codes}"

    def test_get_known_standard(self):
        pcg = StandardRegistry.get("PCG")
        assert pcg.code == "PCG"

    def test_get_unknown_raises(self):
        with pytest.raises(ValueError, match="non trouvé"):
            StandardRegistry.get("UNKNOWN_XYZ")

    def test_is_registered(self):
        assert StandardRegistry.is_registered("PCG")
        assert not StandardRegistry.is_registered("NOT_EXISTS")


class TestPCGFrance:
    def setup_method(self):
        self.pcg = PCGFrance()

    def test_code_and_country(self):
        assert self.pcg.code == "PCG"
        assert "FR" in self.pcg.country_codes
        assert self.pcg.currency_default == "EUR"

    def test_chart_of_accounts_not_empty(self):
        accounts = self.pcg.get_chart_of_accounts()
        assert len(accounts) > 100, f"Attendu >100 comptes, got {len(accounts)}"

    def test_chart_has_required_accounts(self):
        accounts = self.pcg.get_chart_of_accounts()
        codes = {a.code for a in accounts}
        for code in ["512", "401", "411", "44566", "44571", "6811", "70"]:
            assert code in codes, f"Compte {code} manquant"

    def test_balance_sheet_structure(self):
        actif, passif = self.pcg.get_balance_sheet_structure()
        assert len(actif.lines) > 5
        assert len(passif.lines) > 5
        assert any(l.is_total for l in actif.lines)
        assert any(l.is_total for l in passif.lines)

    def test_income_statement_structure(self):
        cdr = self.pcg.get_income_statement_structure()
        assert len(cdr.lines) > 10
        assert any(l.is_total for l in cdr.lines)

    def test_vat_codes_five_rates(self):
        vat = self.pcg.get_vat_codes()
        assert len(vat) == 5
        rates = {float(v["rate"]) for v in vat.values()}
        assert 20.0 in rates
        assert 0.0 in rates


class TestAllStandardsStructure:
    """Smoke-test: each standard must return valid balance sheet + IS."""

    @pytest.mark.parametrize("code", [
        "IFRS", "US_GAAP", "BE_GAAP", "DE_HGB", "UK_FRS102",
        "CH_FER", "ES_PGC", "IT_OIC", "NL_BW2", "PL_PSR", "LU_GAAP",
    ])
    def test_balance_sheet_returns_two_statements(self, code):
        std = StandardRegistry.get(code)
        result = std.get_balance_sheet_structure()
        assert len(result) == 2
        actif, passif = result
        assert len(actif.lines) > 0
        assert len(passif.lines) > 0

    @pytest.mark.parametrize("code", [
        "IFRS", "US_GAAP", "BE_GAAP", "DE_HGB", "UK_FRS102",
        "CH_FER", "ES_PGC", "IT_OIC", "NL_BW2", "PL_PSR", "LU_GAAP",
    ])
    def test_income_statement_has_total(self, code):
        std = StandardRegistry.get(code)
        cdr = std.get_income_statement_structure()
        assert any(l.is_total for l in cdr.lines), f"{code}: pas de ligne total dans CdR"
