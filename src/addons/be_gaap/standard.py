"""BE GAAP — Plan Comptable Belge (PCB) / Belgisch Boekhoudplan."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountingStandard,
    AccountTemplate,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class BEGAAPStandard(AccountingStandard):
    """
    Plan Comptable Minimum Normalisé (PCMN) belge.
    AR du 30 janvier 2001 — plan en classes 1-7 (similaire PCG mais structuré différemment).
    """

    @property
    def code(self) -> str:
        return "BE_GAAP"

    @property
    def name(self) -> str:
        return "Belgian GAAP — Plan Comptable Minimum Normalisé (PCMN)"

    @property
    def country_codes(self) -> list[str]:
        return ["BE"]

    @property
    def currency_default(self) -> str:
        return "EUR"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Comptes PCMN belge (structure propre, non dérivée du PCG français)."""
        return [
            # Classe 1 — Fonds propres, provisions et impôts différés
            AccountTemplate("10", "Capital",                  "CAPITAUX", "EQUITY", "1", is_detail=False),
            AccountTemplate("100","Capital souscrit",         "CAPITAUX", "EQUITY", "1", parent_code="10"),
            AccountTemplate("11", "Primes d'émission",        "CAPITAUX", "EQUITY", "1"),
            AccountTemplate("12", "Plus-values de réévaluation","CAPITAUX","EQUITY","1"),
            AccountTemplate("13", "Réserves",                 "CAPITAUX", "EQUITY", "1", is_detail=False),
            AccountTemplate("130","Réserve légale",           "CAPITAUX", "EQUITY", "1", parent_code="13"),
            AccountTemplate("133","Réserves immunisées",      "CAPITAUX", "EQUITY", "1", parent_code="13"),
            AccountTemplate("14", "Bénéfice reporté",         "CAPITAUX", "EQUITY", "1"),
            AccountTemplate("15", "Provisions pour risques et charges","CAPITAUX","LIABILITY","1"),
            AccountTemplate("16", "Dettes à plus d'un an",   "CAPITAUX", "LIABILITY","1", is_detail=False),
            AccountTemplate("160","Emprunts subordonnés",     "CAPITAUX", "LIABILITY","1", parent_code="16"),
            AccountTemplate("163","Établissements de crédit", "CAPITAUX", "LIABILITY","1", parent_code="16"),
            # Classe 2 — Actifs immobilisés
            AccountTemplate("20", "Frais d'établissement",   "IMMOBILISATIONS","ASSET","2"),
            AccountTemplate("21", "Immobilisations incorporelles","IMMOBILISATIONS","ASSET","2"),
            AccountTemplate("22", "Goodwill",                "IMMOBILISATIONS","ASSET","2"),
            AccountTemplate("23", "Terrains et constructions","IMMOBILISATIONS","ASSET","2"),
            AccountTemplate("24", "Installations, machines, outillage","IMMOBILISATIONS","ASSET","2"),
            AccountTemplate("25", "Mobilier et matériel roulant","IMMOBILISATIONS","ASSET","2"),
            AccountTemplate("26", "Location-financement et droits similaires","IMMOBILISATIONS","ASSET","2"),
            AccountTemplate("27", "Autres immobilisations corporelles","IMMOBILISATIONS","ASSET","2"),
            AccountTemplate("28", "Immobilisations en cours","IMMOBILISATIONS","ASSET","2"),
            AccountTemplate("29", "Immobilisations financières","IMMOBILISATIONS","ASSET","2"),
            # Classe 3 — Stocks et commandes en cours d'exécution
            AccountTemplate("30", "Approvisionnements",      "STOCKS","ASSET","3"),
            AccountTemplate("31", "En-cours de fabrication", "STOCKS","ASSET","3"),
            AccountTemplate("32", "Produits finis",          "STOCKS","ASSET","3"),
            AccountTemplate("33", "Marchandises",            "STOCKS","ASSET","3"),
            AccountTemplate("37", "Commandes en cours",      "STOCKS","ASSET","3"),
            # Classe 4 — Créances et dettes à un an au plus
            AccountTemplate("40", "Créances commerciales",   "TIERS","ASSET","4", is_reconcilable=True),
            AccountTemplate("400","Clients",                 "TIERS","ASSET","4", parent_code="40", is_reconcilable=True),
            AccountTemplate("41", "Autres créances",         "TIERS","ASSET","4"),
            AccountTemplate("43", "Dettes commerciales",     "TIERS","LIABILITY","4", is_reconcilable=True),
            AccountTemplate("440","Fournisseurs",            "TIERS","LIABILITY","4", parent_code="43", is_reconcilable=True),
            AccountTemplate("45", "Dettes fiscales, salariales et sociales","TIERS","LIABILITY","4"),
            AccountTemplate("451","TVA à payer",             "TIERS","LIABILITY","4", parent_code="45", vat_code="TVA_COLL"),
            AccountTemplate("454","Impôts sur le résultat",  "TIERS","LIABILITY","4", parent_code="45"),
            # Classe 5 — Placements de trésorerie et valeurs disponibles
            AccountTemplate("50", "Actions propres",         "FINANCIER","ASSET","5"),
            AccountTemplate("51", "Actions et parts",        "FINANCIER","ASSET","5"),
            AccountTemplate("55", "Établissements de crédit","FINANCIER","ASSET","5", is_reconcilable=True),
            AccountTemplate("570","Caisse",                  "FINANCIER","ASSET","5"),
            # Classe 6 — Charges
            AccountTemplate("60", "Achats",                  "CHARGES","EXPENSE","6"),
            AccountTemplate("61", "Services et biens divers","CHARGES","EXPENSE","6"),
            AccountTemplate("62", "Rémunérations, charges sociales","CHARGES","EXPENSE","6"),
            AccountTemplate("63", "Amortissements et réductions de valeur","CHARGES","EXPENSE","6"),
            AccountTemplate("64", "Autres charges d'exploitation","CHARGES","EXPENSE","6"),
            AccountTemplate("65", "Charges financières",     "CHARGES","EXPENSE","6"),
            AccountTemplate("66", "Charges exceptionnelles", "CHARGES","EXPENSE","6"),
            AccountTemplate("67", "Impôts sur le résultat",  "CHARGES","EXPENSE","6"),
            # Classe 7 — Produits
            AccountTemplate("70", "Chiffre d'affaires",      "PRODUITS","REVENUE","7"),
            AccountTemplate("71", "Variation des stocks",    "PRODUITS","REVENUE","7"),
            AccountTemplate("72", "Production immobilisée",  "PRODUITS","REVENUE","7"),
            AccountTemplate("74", "Autres produits d'exploitation","PRODUITS","REVENUE","7"),
            AccountTemplate("75", "Produits financiers",     "PRODUITS","REVENUE","7"),
            AccountTemplate("76", "Produits exceptionnels",  "PRODUITS","REVENUE","7"),
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        actif = FinancialStatement(code="BE_BILAN_ACTIF", name="Bilan Actif (PCMN)", standard="BE_GAAP", lines=[
            FinancialStatementLine("A1", "Frais d'établissement",                   ["20"],        indent_level=1),
            FinancialStatementLine("A2", "Immobilisations incorporelles",           ["21","22"],   indent_level=1),
            FinancialStatementLine("A3", "Immobilisations corporelles",             ["23","24","25","26","27","28"], indent_level=1),
            FinancialStatementLine("A4", "Immobilisations financières",             ["29"],        indent_level=1),
            FinancialStatementLine("A5", "ACTIFS IMMOBILISÉS",                      ["2"],         is_subtotal=True),
            FinancialStatementLine("A6", "Stocks et commandes en cours",            ["3"],         indent_level=1),
            FinancialStatementLine("A7", "Créances à un an au plus",                ["40","41"],   indent_level=1),
            FinancialStatementLine("A8", "Placements de trésorerie",                ["50","51"],   indent_level=1),
            FinancialStatementLine("A9", "Valeurs disponibles",                     ["55","57"],   indent_level=1),
            FinancialStatementLine("A10","ACTIFS CIRCULANTS",                       ["3","4","5"], is_subtotal=True),
            FinancialStatementLine("A0", "TOTAL DE L'ACTIF",                        ["2","3","4","5"], is_total=True),
        ])
        passif = FinancialStatement(code="BE_BILAN_PASSIF", name="Bilan Passif (PCMN)", standard="BE_GAAP", lines=[
            FinancialStatementLine("P1", "Capital",                                 ["10"],        indent_level=1),
            FinancialStatementLine("P2", "Primes d'émission et plus-values",        ["11","12"],   indent_level=1),
            FinancialStatementLine("P3", "Réserves et bénéfice reporté",            ["13","14"],   indent_level=1),
            FinancialStatementLine("P4", "CAPITAUX PROPRES",                        ["10","11","12","13","14"], is_subtotal=True),
            FinancialStatementLine("P5", "Provisions et impôts différés",           ["15"],        indent_level=1),
            FinancialStatementLine("P6", "Dettes à plus d'un an",                  ["16"],        indent_level=1),
            FinancialStatementLine("P7", "Dettes à un an au plus",                 ["43","44","45"], indent_level=1),
            FinancialStatementLine("P8", "DETTES",                                  ["15","16","43","44","45"], is_subtotal=True),
            FinancialStatementLine("P0", "TOTAL DU PASSIF",                         ["1","15","16","43","44","45"], is_total=True),
        ])
        return actif, passif

    def get_income_statement_structure(self) -> FinancialStatement:
        return FinancialStatement(code="BE_COMPTE_RESULTAT", name="Compte de Résultats (PCMN)", standard="BE_GAAP", lines=[
            FinancialStatementLine("R1", "Chiffre d'affaires",                      ["70"],        indent_level=1),
            FinancialStatementLine("R2", "Variation des stocks et immo. prod.",     ["71","72"],   indent_level=1),
            FinancialStatementLine("R3", "Autres produits d'exploitation",          ["74"],        indent_level=1),
            FinancialStatementLine("R4", "PRODUITS D'EXPLOITATION",                 ["70","71","72","74"], is_subtotal=True),
            FinancialStatementLine("R5", "Achats et variations de stocks",          ["60","61"],   indent_level=1, negate=True),
            FinancialStatementLine("R6", "Services et biens divers",                ["61"],        indent_level=1, negate=True),
            FinancialStatementLine("R7", "Rémunérations et charges sociales",       ["62"],        indent_level=1, negate=True),
            FinancialStatementLine("R8", "Amortissements",                          ["63"],        indent_level=1, negate=True),
            FinancialStatementLine("R9", "Autres charges d'exploitation",           ["64"],        indent_level=1, negate=True),
            FinancialStatementLine("R10","RÉSULTAT D'EXPLOITATION",                 ["7","6"],     is_subtotal=True),
            FinancialStatementLine("R11","Produits financiers",                     ["75"],        indent_level=1),
            FinancialStatementLine("R12","Charges financières",                     ["65"],        indent_level=1, negate=True),
            FinancialStatementLine("R13","RÉSULTAT COURANT",                        ["7","6","75","65"], is_subtotal=True),
            FinancialStatementLine("R14","Produits exceptionnels",                  ["76"],        indent_level=1),
            FinancialStatementLine("R15","Charges exceptionnelles",                 ["66"],        indent_level=1, negate=True),
            FinancialStatementLine("R16","Impôts sur le résultat",                  ["67"],        indent_level=1, negate=True),
            FinancialStatementLine("R17","BÉNÉFICE / PERTE DE L'EXERCICE",         ["7","6"],     is_total=True),
        ])

    def get_vat_codes(self) -> dict:
        return {
            "TVA_21": {"rate": "21.00", "label": "TVA belge 21%", "account_collectee": "451"},
            "TVA_12": {"rate": "12.00", "label": "TVA belge 12%", "account_collectee": "451"},
            "TVA_06": {"rate": "6.00",  "label": "TVA belge 6%",  "account_collectee": "451"},
            "TVA_00": {"rate": "0.00",  "label": "TVA belge 0%",  "account_collectee": None},
        }


StandardRegistry.register(BEGAAPStandard())
