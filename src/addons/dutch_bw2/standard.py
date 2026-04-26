"""Dutch GAAP — Burgerlijk Wetboek Boek 2 (BW2) / RJ-Richtlijnen voor de Jaarverslaggeving."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountTemplate,
    AccountingStandard,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class DutchBW2Standard(AccountingStandard):
    """
    Dutch GAAP — BW2 Titel 9 + RJ (Raad voor de Jaarverslaggeving).
    Grootboekschema gebaseerd op het Standaard Rekeningschema (SRS).
    """

    @property
    def code(self) -> str:
        return "NL_BW2"

    @property
    def name(self) -> str:
        return "Dutch GAAP — BW2 / RJ (Raad voor de Jaarverslaggeving)"

    @property
    def country_codes(self) -> list[str]:
        return ["NL"]

    @property
    def currency_default(self) -> str:
        return "EUR"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Standaard Rekeningschema Nederland (SRS) — vereenvoudigd."""
        return [
            # Klasse 0 — Vaste activa
            AccountTemplate("020", "Immateriële vaste activa",         "IMMOBILISATIONS", "ASSET",     "0"),
            AccountTemplate("030", "Materiële vaste activa",           "IMMOBILISATIONS", "ASSET",     "0", is_detail=False),
            AccountTemplate("031", "Bedrijfsgebouwen en -terreinen",   "IMMOBILISATIONS", "ASSET",     "0", parent_code="030"),
            AccountTemplate("032", "Machines en installaties",         "IMMOBILISATIONS", "ASSET",     "0", parent_code="030"),
            AccountTemplate("033", "Inventaris en computers",          "IMMOBILISATIONS", "ASSET",     "0", parent_code="030"),
            AccountTemplate("040", "Financiële vaste activa",          "IMMOBILISATIONS", "ASSET",     "0"),
            AccountTemplate("090", "Cumulatieve afschrijvingen",       "IMMOBILISATIONS", "CONTRA_ASSET","0"),
            # Klasse 1 — Vlottende activa
            AccountTemplate("100", "Voorraden",                        "STOCKS",          "ASSET",     "1"),
            AccountTemplate("110", "Debiteuren",                       "TIERS",           "ASSET",     "1", is_reconcilable=True),
            AccountTemplate("120", "Overige vorderingen",              "TIERS",           "ASSET",     "1"),
            AccountTemplate("130", "Te vorderen BTW",                  "TIERS",           "ASSET",     "1"),
            AccountTemplate("140", "Overlopende activa",               "TIERS",           "ASSET",     "1"),
            AccountTemplate("150", "Liquide middelen",                 "FINANCIER",       "ASSET",     "1", is_reconcilable=True),
            AccountTemplate("151", "Bank",                             "FINANCIER",       "ASSET",     "1", parent_code="150", is_reconcilable=True),
            AccountTemplate("152", "Kas",                              "FINANCIER",       "ASSET",     "1", parent_code="150"),
            # Klasse 2 — Eigen vermogen
            AccountTemplate("200", "Geplaatst kapitaal",               "CAPITAUX",        "EQUITY",    "2"),
            AccountTemplate("210", "Agio",                             "CAPITAUX",        "EQUITY",    "2"),
            AccountTemplate("220", "Wettelijke reserves",              "CAPITAUX",        "EQUITY",    "2"),
            AccountTemplate("230", "Overige reserves",                 "CAPITAUX",        "EQUITY",    "2"),
            AccountTemplate("240", "Resultaat boekjaar",               "CAPITAUX",        "EQUITY",    "2"),
            # Klasse 3 — Langlopende schulden
            AccountTemplate("300", "Langlopende schulden aan banken",  "CAPITAUX",        "LIABILITY", "3"),
            AccountTemplate("310", "Overige langlopende schulden",     "CAPITAUX",        "LIABILITY", "3"),
            AccountTemplate("320", "Voorzieningen",                    "CAPITAUX",        "LIABILITY", "3"),
            # Klasse 4 — Kortlopende schulden
            AccountTemplate("400", "Crediteuren",                      "TIERS",           "LIABILITY", "4", is_reconcilable=True),
            AccountTemplate("410", "Kortlopende schulden aan banken",  "TIERS",           "LIABILITY", "4"),
            AccountTemplate("420", "Schulden aan personeel",           "TIERS",           "LIABILITY", "4"),
            AccountTemplate("430", "Belastingen en premies",           "TIERS",           "LIABILITY", "4"),
            AccountTemplate("431", "BTW te betalen",                   "TIERS",           "LIABILITY", "4", parent_code="430", vat_code="BTW_21"),
            AccountTemplate("432", "Vennootschapsbelasting",           "TIERS",           "LIABILITY", "4", parent_code="430"),
            AccountTemplate("440", "Overlopende passiva",              "TIERS",           "LIABILITY", "4"),
            # Klasse 7 — Kosten
            AccountTemplate("700", "Inkoopwaarde omzet",               "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("710", "Overige inkoopkosten",             "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("720", "Personeelskosten",                 "CHARGES",         "EXPENSE",   "7", is_detail=False),
            AccountTemplate("721", "Lonen en salarissen",              "CHARGES",         "EXPENSE",   "7", parent_code="720"),
            AccountTemplate("722", "Sociale lasten",                   "CHARGES",         "EXPENSE",   "7", parent_code="720"),
            AccountTemplate("730", "Huisvestingskosten",               "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("740", "Autokosten",                       "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("750", "Kantoorkosten",                    "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("760", "Afschrijvingen",                   "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("770", "Rentelasten",                      "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("780", "Vennootschapsbelasting",           "CHARGES",         "EXPENSE",   "7"),
            # Klasse 8 — Opbrengsten
            AccountTemplate("800", "Netto-omzet",                      "PRODUITS",        "REVENUE",   "8", is_detail=False),
            AccountTemplate("801", "Opbrengsten verkopen",             "PRODUITS",        "REVENUE",   "8", parent_code="800"),
            AccountTemplate("802", "Opbrengsten diensten",             "PRODUITS",        "REVENUE",   "8", parent_code="800"),
            AccountTemplate("810", "Mutatie voorraden",                "PRODUITS",        "REVENUE",   "8"),
            AccountTemplate("820", "Overige bedrijfsopbrengsten",      "PRODUITS",        "REVENUE",   "8"),
            AccountTemplate("830", "Rentebaten",                       "PRODUITS",        "REVENUE",   "8"),
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """BW2 art. 2:361 — Balans (Activa / Passiva)."""
        activa = FinancialStatement(code="NL_BALANS_ACTIVA", name="Balans — Activa (BW2)", standard="NL_BW2", lines=[
            FinancialStatementLine("VA1",  "Immateriële vaste activa",           ["020"],             indent_level=1),
            FinancialStatementLine("VA2",  "Materiële vaste activa",             ["030"],             indent_level=1),
            FinancialStatementLine("VA3",  "Financiële vaste activa",            ["040"],             indent_level=1),
            FinancialStatementLine("VA4",  "Cumulatieve afschrijvingen",         ["090"],             indent_level=1, negate=True),
            FinancialStatementLine("VA0",  "VASTE ACTIVA",                       ["0"],               is_subtotal=True),
            FinancialStatementLine("VL1",  "Voorraden",                          ["100"],             indent_level=1),
            FinancialStatementLine("VL2",  "Vorderingen",                        ["110","120","130","140"], indent_level=1),
            FinancialStatementLine("VL3",  "Liquide middelen",                   ["150","151","152"], indent_level=1),
            FinancialStatementLine("VL0",  "VLOTTENDE ACTIVA",                   ["1"],               is_subtotal=True),
            FinancialStatementLine("T",    "TOTAAL ACTIVA",                      ["0","1"],           is_total=True),
        ])
        passiva = FinancialStatement(code="NL_BALANS_PASSIVA", name="Balans — Passiva (BW2)", standard="NL_BW2", lines=[
            FinancialStatementLine("EV1",  "Geplaatst kapitaal",                 ["200"],             indent_level=1),
            FinancialStatementLine("EV2",  "Agio en reserves",                  ["210","220","230"], indent_level=1),
            FinancialStatementLine("EV3",  "Resultaat boekjaar",                 ["240"],             indent_level=1),
            FinancialStatementLine("EV0",  "EIGEN VERMOGEN",                     ["2"],               is_subtotal=True),
            FinancialStatementLine("LT1",  "Langlopende schulden",               ["300","310"],       indent_level=1),
            FinancialStatementLine("LT2",  "Voorzieningen",                      ["320"],             indent_level=1),
            FinancialStatementLine("LT0",  "LANGLOPENDE VERPLICHTINGEN",         ["3"],               is_subtotal=True),
            FinancialStatementLine("KT1",  "Crediteuren",                        ["400"],             indent_level=1),
            FinancialStatementLine("KT2",  "Schulden aan banken",                ["410"],             indent_level=1),
            FinancialStatementLine("KT3",  "Schulden personeel en belastingen",  ["420","430","431","432"], indent_level=1),
            FinancialStatementLine("KT4",  "Overlopende passiva",                ["440"],             indent_level=1),
            FinancialStatementLine("KT0",  "KORTLOPENDE VERPLICHTINGEN",         ["4"],               is_subtotal=True),
            FinancialStatementLine("T",    "TOTAAL PASSIVA",                     ["2","3","4"],       is_total=True),
        ])
        return activa, passiva

    def get_income_statement_structure(self) -> FinancialStatement:
        """BW2 art. 2:377 — Winst-en-verliesrekening (categoriale methode)."""
        return FinancialStatement(code="NL_WVR", name="Winst-en-verliesrekening (BW2)", standard="NL_BW2", lines=[
            FinancialStatementLine("W1",   "Netto-omzet",                        ["800","801","802"], indent_level=1),
            FinancialStatementLine("W2",   "Mutatie voorraden",                  ["810"],             indent_level=1),
            FinancialStatementLine("W3",   "Overige bedrijfsopbrengsten",        ["820"],             indent_level=1),
            FinancialStatementLine("W4",   "BEDRIJFSOPBRENGSTEN",                ["8"],               is_subtotal=True),
            FinancialStatementLine("W5",   "Inkoopwaarde omzet",                 ["700","710"],       indent_level=1, negate=True),
            FinancialStatementLine("W6",   "Personeelskosten",                   ["720","721","722"], indent_level=1, negate=True),
            FinancialStatementLine("W7",   "Afschrijvingen",                     ["760"],             indent_level=1, negate=True),
            FinancialStatementLine("W8",   "Overige bedrijfskosten",             ["730","740","750"], indent_level=1, negate=True),
            FinancialStatementLine("W9",   "BEDRIJFSRESULTAAT (EBIT)",           ["8","7"],           is_subtotal=True),
            FinancialStatementLine("W10",  "Rentebaten",                         ["830"],             indent_level=1),
            FinancialStatementLine("W11",  "Rentelasten",                        ["770"],             indent_level=1, negate=True),
            FinancialStatementLine("W12",  "RESULTAAT VOOR BELASTING",           ["8","7","83","77"], is_subtotal=True),
            FinancialStatementLine("W13",  "Vennootschapsbelasting",             ["780"],             indent_level=1, negate=True),
            FinancialStatementLine("W14",  "RESULTAAT NA BELASTING",             ["8","7"],           is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {
            "BTW_21": {"rate": "21.00", "label": "BTW hoog tarief 21%",         "account_collectee": "431"},
            "BTW_09": {"rate": "9.00",  "label": "BTW laag tarief 9%",          "account_collectee": "431"},
            "BTW_00": {"rate": "0.00",  "label": "BTW vrijgesteld / nultarief", "account_collectee": None},
        }


StandardRegistry.register(DutchBW2Standard())
