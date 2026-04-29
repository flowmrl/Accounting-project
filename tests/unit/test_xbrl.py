"""Tests — XBRL export (dépôt greffe)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.modules.reporting.xbrl import build_xbrl


COMPANY = dict(
    company_name="Acme SAS",
    siren="123456789",
    siret="12345678900015",
    fiscal_year_start=date(2025, 1, 1),
    fiscal_year_end=date(2025, 12, 31),
    currency="EUR",
)

BALANCE = {
    "actif_immobilise": Decimal("150000.00"),
    "actif_circulant": Decimal("80000.00"),
    "tresorerie_actif": Decimal("25000.00"),
    "total_actif": Decimal("255000.00"),
    "capitaux_propres": Decimal("120000.00"),
    "provisions": Decimal("10000.00"),
    "dettes": Decimal("125000.00"),
    "total_passif": Decimal("255000.00"),
}

INCOME = {
    "chiffre_affaires": Decimal("500000.00"),
    "valeur_ajoutee": Decimal("200000.00"),
    "resultat_exploitation": Decimal("45000.00"),
    "resultat_net": Decimal("32000.00"),
}


def test_xbrl_is_valid_xml():
    xml = build_xbrl(**COMPANY, balance_sheet=BALANCE, income_statement=INCOME)
    assert xml.startswith(b"<?xml")
    assert b"xbrl" in xml.lower()


def test_xbrl_contains_siren():
    xml = build_xbrl(**COMPANY, balance_sheet=BALANCE, income_statement=INCOME)
    assert b"123456789" in xml


def test_xbrl_contains_company_name():
    xml = build_xbrl(**COMPANY, balance_sheet=BALANCE, income_statement=INCOME)
    assert b"Acme SAS" in xml


def test_xbrl_contains_fiscal_dates():
    xml = build_xbrl(**COMPANY, balance_sheet=BALANCE, income_statement=INCOME)
    assert b"2025-01-01" in xml
    assert b"2025-12-31" in xml


def test_xbrl_contains_balance_sheet_totals():
    xml = build_xbrl(**COMPANY, balance_sheet=BALANCE, income_statement=INCOME)
    assert b"255000.00" in xml


def test_xbrl_contains_chiffre_affaires():
    xml = build_xbrl(**COMPANY, balance_sheet=BALANCE, income_statement=INCOME)
    assert b"500000.00" in xml


def test_xbrl_contains_resultat_net():
    xml = build_xbrl(**COMPANY, balance_sheet=BALANCE, income_statement=INCOME)
    assert b"32000.00" in xml


def test_xbrl_contains_fr_gaap_namespace():
    xml = build_xbrl(**COMPANY, balance_sheet=BALANCE, income_statement=INCOME)
    assert b"fr-gaap" in xml


def test_xbrl_empty_income():
    xml = build_xbrl(**COMPANY, balance_sheet=BALANCE, income_statement={})
    assert xml.startswith(b"<?xml")
    assert b"255000.00" in xml


def test_xbrl_no_siret():
    xml = build_xbrl(**{**COMPANY, "siret": None}, balance_sheet=BALANCE, income_statement=INCOME)
    assert b"123456789" in xml
    assert b"12345678900015" not in xml
