"""Polish PSR — Polskie Standardy Rachunkowości (Polish Accounting Standards)."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountingStandard,
    AccountTemplate,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class PolishPSRStandard(AccountingStandard):
    """
    Polskie Standardy Rachunkowości (PSR) — Ustawa o Rachunkowości z dnia 29.09.1994.
    Zakładowy Plan Kont (ZPK) — structure en classes 0-9.
    KSR (Krajowe Standardy Rachunkowości) complementing EU Directives.
    """

    @property
    def code(self) -> str:
        return "PL_PSR"

    @property
    def name(self) -> str:
        return "Polish GAAP — Polskie Standardy Rachunkowości (PSR)"

    @property
    def country_codes(self) -> list[str]:
        return ["PL"]

    @property
    def currency_default(self) -> str:
        return "PLN"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Zakładowy Plan Kont — klasy 0-8."""
        return [
            # Klasa 0 — Aktywa trwałe (Actifs immobilisés)
            AccountTemplate("010", "Środki trwałe",                    "IMMOBILISATIONS", "ASSET",     "0", is_detail=False),
            AccountTemplate("011", "Budynki i lokale",                 "IMMOBILISATIONS", "ASSET",     "0", parent_code="010"),
            AccountTemplate("013", "Maszyny i urządzenia",             "IMMOBILISATIONS", "ASSET",     "0", parent_code="010"),
            AccountTemplate("014", "Środki transportu",                "IMMOBILISATIONS", "ASSET",     "0", parent_code="010"),
            AccountTemplate("020", "Wartości niematerialne i prawne",  "IMMOBILISATIONS", "ASSET",     "0"),
            AccountTemplate("030", "Długoterminowe aktywa finansowe",  "IMMOBILISATIONS", "ASSET",     "0"),
            AccountTemplate("070", "Odpisy umorzeniowe",               "IMMOBILISATIONS", "CONTRA_ASSET","0"),
            # Klasa 1 — Środki pieniężne i rachunki bankowe
            AccountTemplate("100", "Kasa",                             "FINANCIER",       "ASSET",     "1"),
            AccountTemplate("130", "Rachunek bankowy",                 "FINANCIER",       "ASSET",     "1", is_reconcilable=True),
            AccountTemplate("131", "Rachunek bieżący",                 "FINANCIER",       "ASSET",     "1", parent_code="130", is_reconcilable=True),
            AccountTemplate("140", "Krótkoterminowe aktywa finansowe", "FINANCIER",       "ASSET",     "1"),
            # Klasa 2 — Rozrachunki i roszczenia
            AccountTemplate("200", "Rozrachunki z odbiorcami",         "TIERS",           "ASSET",     "2", is_reconcilable=True),
            AccountTemplate("210", "Rozrachunki z dostawcami",         "TIERS",           "LIABILITY", "2", is_reconcilable=True),
            AccountTemplate("220", "Rozrachunki z budżetem",           "TIERS",           "LIABILITY", "2", is_detail=False),
            AccountTemplate("221", "VAT należny",                      "TIERS",           "LIABILITY", "2", parent_code="220", vat_code="VAT_23"),
            AccountTemplate("222", "VAT naliczony",                    "TIERS",           "ASSET",     "2", parent_code="220"),
            AccountTemplate("223", "Podatek dochodowy",                "TIERS",           "LIABILITY", "2", parent_code="220"),
            AccountTemplate("230", "Rozrachunki z pracownikami",       "TIERS",           "LIABILITY", "2"),
            AccountTemplate("240", "Rozrachunki z ZUS",                "TIERS",           "LIABILITY", "2"),
            AccountTemplate("290", "Odpisy aktualizujące należności",  "TIERS",           "CONTRA_ASSET","2"),
            # Klasa 3 — Materiały i towary
            AccountTemplate("310", "Materiały",                        "STOCKS",          "ASSET",     "3"),
            AccountTemplate("330", "Towary",                           "STOCKS",          "ASSET",     "3"),
            AccountTemplate("340", "Opakowania",                       "STOCKS",          "ASSET",     "3"),
            # Klasa 4 — Koszty według rodzajów
            AccountTemplate("400", "Amortyzacja",                      "CHARGES",         "EXPENSE",   "4"),
            AccountTemplate("401", "Zużycie materiałów i energii",     "CHARGES",         "EXPENSE",   "4"),
            AccountTemplate("402", "Usługi obce",                      "CHARGES",         "EXPENSE",   "4"),
            AccountTemplate("403", "Podatki i opłaty",                 "CHARGES",         "EXPENSE",   "4"),
            AccountTemplate("404", "Wynagrodzenia",                    "CHARGES",         "EXPENSE",   "4"),
            AccountTemplate("405", "Ubezpieczenia społeczne i inne",   "CHARGES",         "EXPENSE",   "4"),
            AccountTemplate("406", "Pozostałe koszty rodzajowe",       "CHARGES",         "EXPENSE",   "4"),
            # Klasa 5 — Koszty według miejsca powstawania (analytique)
            AccountTemplate("500", "Koszty działalności podstawowej",  "CHARGES",         "EXPENSE",   "5"),
            AccountTemplate("550", "Koszty ogólnego zarządu",          "CHARGES",         "EXPENSE",   "5"),
            # Klasa 6 — Produkty i rozliczenia międzyokresowe
            AccountTemplate("601", "Produkty gotowe",                  "STOCKS",          "ASSET",     "6"),
            AccountTemplate("602", "Półfabrykaty",                     "STOCKS",          "ASSET",     "6"),
            AccountTemplate("640", "Czynne rozliczenia międzyokresowe","TIERS",           "ASSET",     "6"),
            AccountTemplate("650", "Bierne rozliczenia międzyokresowe","TIERS",           "LIABILITY", "6"),
            # Klasa 7 — Przychody i koszty ich uzyskania
            AccountTemplate("700", "Sprzedaż produktów",               "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("730", "Sprzedaż towarów",                 "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("740", "Sprzedaż materiałów",              "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("750", "Przychody finansowe",              "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("760", "Pozostałe przychody operacyjne",   "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("770", "Zyski nadzwyczajne",               "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("751", "Koszty finansowe",                 "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("761", "Pozostałe koszty operacyjne",      "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("771", "Straty nadzwyczajne",              "CHARGES",         "EXPENSE",   "7"),
            # Klasa 8 — Kapitały, fundusze i wynik finansowy
            AccountTemplate("800", "Kapitał zakładowy",                "CAPITAUX",        "EQUITY",    "8"),
            AccountTemplate("810", "Kapitał zapasowy",                 "CAPITAUX",        "EQUITY",    "8"),
            AccountTemplate("820", "Kapitał rezerwowy",                "CAPITAUX",        "EQUITY",    "8"),
            AccountTemplate("830", "Rezerwy",                          "CAPITAUX",        "LIABILITY", "8"),
            AccountTemplate("840", "Rozliczenia międzyokresowe (pasyw)","CAPITAUX",       "LIABILITY", "8"),
            AccountTemplate("860", "Wynik finansowy",                  "CAPITAUX",        "EQUITY",    "8"),
            AccountTemplate("870", "Podatek dochodowy",                "CHARGES",         "EXPENSE",   "8"),
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """Ustawa o rachunkowości załącznik nr 1 — Bilans (Aktywa / Pasywa)."""
        aktywa = FinancialStatement(code="PL_BILANS_AKTYWA", name="Bilans — Aktywa (PSR)", standard="PL_PSR", lines=[
            FinancialStatementLine("A1",  "Wartości niematerialne i prawne",     ["020"],             indent_level=1),
            FinancialStatementLine("A2",  "Środki trwałe",                       ["010","011","013","014"], indent_level=1),
            FinancialStatementLine("A3",  "Odpisy umorzeniowe",                  ["070"],             indent_level=1, negate=True),
            FinancialStatementLine("A4",  "Długoterm. aktywa finansowe",         ["030"],             indent_level=1),
            FinancialStatementLine("A0",  "AKTYWA TRWAŁE",                       ["0"],               is_subtotal=True),
            FinancialStatementLine("B1",  "Zapasy (materiały i towary)",         ["3","601","602"],   indent_level=1),
            FinancialStatementLine("B2",  "Należności krótkoterm.",              ["200","290"],       indent_level=1),
            FinancialStatementLine("B3",  "Inwestycje krótkoterm.",              ["140"],             indent_level=1),
            FinancialStatementLine("B4",  "Środki pieniężne",                    ["100","130","131"], indent_level=1),
            FinancialStatementLine("B5",  "Rozliczenia międzyokresowe",          ["640"],             indent_level=1),
            FinancialStatementLine("B0",  "AKTYWA OBROTOWE",                     ["1","2","3","6"],   is_subtotal=True),
            FinancialStatementLine("T",   "SUMA AKTYWÓW",                        ["0","1","2","3","6"], is_total=True),
        ])
        pasywa = FinancialStatement(code="PL_BILANS_PASYWA", name="Bilans — Pasywa (PSR)", standard="PL_PSR", lines=[
            FinancialStatementLine("A1p", "Kapitał zakładowy",                   ["800"],             indent_level=1),
            FinancialStatementLine("A2p", "Kapitał zapasowy i rezerwowy",        ["810","820"],       indent_level=1),
            FinancialStatementLine("A5p", "Wynik finansowy",                     ["860"],             indent_level=1),
            FinancialStatementLine("A0p", "KAPITAŁ WŁASNY",                      ["8"],               is_subtotal=True),
            FinancialStatementLine("B1p", "Rezerwy",                             ["830"],             indent_level=1),
            FinancialStatementLine("B0p", "REZERWY NA ZOBOWIĄZANIA",             ["83"],              is_subtotal=True),
            FinancialStatementLine("C1p", "Zobowiązania wobec dostawców",        ["210"],             indent_level=1),
            FinancialStatementLine("C2p", "Zobowiązania wobec pracowników",      ["230"],             indent_level=1),
            FinancialStatementLine("C3p", "Zobowiązania wobec ZUS i budżetu",    ["220","221","223","240"], indent_level=1),
            FinancialStatementLine("C4p", "Rozliczenia międzyokresowe (pas.)",   ["650","840"],       indent_level=1),
            FinancialStatementLine("C0p", "ZOBOWIĄZANIA KRÓTKOTERMINOWE",        ["2","6"],           is_subtotal=True),
            FinancialStatementLine("T",   "SUMA PASYWÓW",                        ["2","6","8"],       is_total=True),
        ])
        return aktywa, pasywa

    def get_income_statement_structure(self) -> FinancialStatement:
        """Ustawa o rachunkowości — Rachunek zysków i strat (wariant porównawczy)."""
        return FinancialStatement(code="PL_RZIS", name="Rachunek Zysków i Strat (PSR)", standard="PL_PSR", lines=[
            FinancialStatementLine("A",   "Przychody ze sprzedaży",              ["700","730","740"], indent_level=1),
            FinancialStatementLine("B",   "Koszty sprzedanych produktów",        ["4"],               indent_level=1, negate=True),
            FinancialStatementLine("C",   "ZYSK BRUTTO ZE SPRZEDAŻY",           ["7","4"],           is_subtotal=True),
            FinancialStatementLine("D",   "Koszty sprzedaży i ogólnego zarządu", ["5"],               indent_level=1, negate=True),
            FinancialStatementLine("E",   "ZYSK ZE SPRZEDAŻY",                  ["7","4","5"],       is_subtotal=True),
            FinancialStatementLine("F",   "Pozostałe przychody operacyjne",      ["760"],             indent_level=1),
            FinancialStatementLine("G",   "Pozostałe koszty operacyjne",         ["761"],             indent_level=1, negate=True),
            FinancialStatementLine("H",   "ZYSK Z DZIAŁALNOŚCI OPERACYJNEJ",    ["7","4","5"],       is_subtotal=True),
            FinancialStatementLine("I",   "Przychody finansowe",                 ["750"],             indent_level=1),
            FinancialStatementLine("J",   "Koszty finansowe",                    ["751"],             indent_level=1, negate=True),
            FinancialStatementLine("K",   "ZYSK BRUTTO",                         ["7","4","5","75"],  is_subtotal=True),
            FinancialStatementLine("L",   "Podatek dochodowy",                   ["870"],             indent_level=1, negate=True),
            FinancialStatementLine("M",   "ZYSK NETTO",                          ["7","4","5","75","87"], is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {
            "VAT_23": {"rate": "23.00", "label": "VAT stawka podstawowa 23%",   "account_collectee": "221"},
            "VAT_08": {"rate": "8.00",  "label": "VAT stawka obniżona 8%",      "account_collectee": "221"},
            "VAT_05": {"rate": "5.00",  "label": "VAT stawka obniżona 5%",      "account_collectee": "221"},
            "VAT_00": {"rate": "0.00",  "label": "VAT zwolniony / 0%",          "account_collectee": None},
        }


StandardRegistry.register(PolishPSRStandard())
