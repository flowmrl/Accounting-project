"""Luxembourg GAAP — Plan Comptable Normalisé (PCN) luxembourgeois."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountTemplate,
    AccountingStandard,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class LuxembourgGAAPStandard(AccountingStandard):
    """
    Plan Comptable Normalisé (PCN) luxembourgeois.
    Loi du 19 décembre 2002 concernant le registre de commerce et des sociétés.
    Règlement Grand-Ducal du 10 juin 2009 — plan comptable normalisé.
    Structure similaire au PCG français (classes 1-7) avec adaptations luxembourgeoises.
    """

    @property
    def code(self) -> str:
        return "LU_GAAP"

    @property
    def name(self) -> str:
        return "Luxembourg GAAP — Plan Comptable Normalisé (PCN)"

    @property
    def country_codes(self) -> list[str]:
        return ["LU"]

    @property
    def currency_default(self) -> str:
        return "EUR"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """PCN luxembourgeois — classes 1-7 (structure proche du PCG français)."""
        return [
            # Classe 1 — Capitaux propres, provisions et dettes financières
            AccountTemplate("10", "Capital souscrit",                  "CAPITAUX",        "EQUITY",    "1", is_detail=False),
            AccountTemplate("101","Capital souscrit appelé versé",     "CAPITAUX",        "EQUITY",    "1", parent_code="10"),
            AccountTemplate("11", "Primes d'émission et assimilées",   "CAPITAUX",        "EQUITY",    "1"),
            AccountTemplate("12", "Réserves",                          "CAPITAUX",        "EQUITY",    "1", is_detail=False),
            AccountTemplate("121","Réserve légale",                    "CAPITAUX",        "EQUITY",    "1", parent_code="12"),
            AccountTemplate("123","Réserves statutaires",              "CAPITAUX",        "EQUITY",    "1", parent_code="12"),
            AccountTemplate("13", "Résultats reportés",                "CAPITAUX",        "EQUITY",    "1"),
            AccountTemplate("14", "Résultat de l'exercice",            "CAPITAUX",        "EQUITY",    "1"),
            AccountTemplate("15", "Subventions d'investissement",      "CAPITAUX",        "EQUITY",    "1"),
            AccountTemplate("16", "Provisions pour risques et charges","CAPITAUX",        "LIABILITY", "1"),
            AccountTemplate("17", "Dettes financières à long terme",   "CAPITAUX",        "LIABILITY", "1", is_detail=False),
            AccountTemplate("170","Emprunts obligataires",             "CAPITAUX",        "LIABILITY", "1", parent_code="17"),
            AccountTemplate("173","Emprunts auprès d'établissements",  "CAPITAUX",        "LIABILITY", "1", parent_code="17"),
            AccountTemplate("175","Dettes envers entreprises liées",   "CAPITAUX",        "LIABILITY", "1", parent_code="17"),
            # Classe 2 — Immobilisations
            AccountTemplate("20", "Immobilisations incorporelles",     "IMMOBILISATIONS", "ASSET",     "2", is_detail=False),
            AccountTemplate("201","Frais de développement",            "IMMOBILISATIONS", "ASSET",     "2", parent_code="20"),
            AccountTemplate("203","Concessions, brevets, licences",    "IMMOBILISATIONS", "ASSET",     "2", parent_code="20"),
            AccountTemplate("205","Goodwill",                          "IMMOBILISATIONS", "ASSET",     "2", parent_code="20"),
            AccountTemplate("21", "Immobilisations corporelles",       "IMMOBILISATIONS", "ASSET",     "2", is_detail=False),
            AccountTemplate("211","Terrains",                          "IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("212","Constructions",                     "IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("214","Installations et agencements",      "IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("215","Matériel et mobilier",              "IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("218","Autres immobilisations corporelles","IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("23", "Immobilisations en cours",          "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("26", "Participations",                    "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("27", "Créances rattachées à des particip.","IMMOBILISATIONS","ASSET",     "2"),
            AccountTemplate("28", "Amortissements des immobilisations","IMMOBILISATIONS", "CONTRA_ASSET","2"),
            AccountTemplate("29", "Dépréciations des immobilisations", "IMMOBILISATIONS", "CONTRA_ASSET","2"),
            # Classe 3 — Stocks
            AccountTemplate("30", "Stocks de matières premières",      "STOCKS",          "ASSET",     "3"),
            AccountTemplate("31", "Stocks d'en-cours de production",   "STOCKS",          "ASSET",     "3"),
            AccountTemplate("35", "Stocks de produits finis",          "STOCKS",          "ASSET",     "3"),
            AccountTemplate("37", "Stocks de marchandises",            "STOCKS",          "ASSET",     "3"),
            # Classe 4 — Tiers
            AccountTemplate("40", "Fournisseurs",                      "TIERS",           "LIABILITY", "4", is_reconcilable=True),
            AccountTemplate("401","Fournisseurs",                      "TIERS",           "LIABILITY", "4", parent_code="40", is_reconcilable=True),
            AccountTemplate("41", "Clients",                           "TIERS",           "ASSET",     "4", is_reconcilable=True),
            AccountTemplate("411","Clients",                           "TIERS",           "ASSET",     "4", parent_code="41", is_reconcilable=True),
            AccountTemplate("42", "Personnel",                         "TIERS",           "LIABILITY", "4"),
            AccountTemplate("43", "Sécurité sociale et autres org.",   "TIERS",           "LIABILITY", "4"),
            AccountTemplate("44", "État et autres collectivités",      "TIERS",           "LIABILITY", "4", is_detail=False),
            AccountTemplate("441","TVA à décaisser",                   "TIERS",           "LIABILITY", "4", parent_code="44", vat_code="TVA_17"),
            AccountTemplate("445","TVA à récupérer",                   "TIERS",           "ASSET",     "4", parent_code="44"),
            AccountTemplate("446","Impôt sur le revenu des soc.",      "TIERS",           "LIABILITY", "4", parent_code="44"),
            # Classe 5 — Comptes financiers
            AccountTemplate("51", "Banques",                           "FINANCIER",       "ASSET",     "5", is_reconcilable=True),
            AccountTemplate("512","Banques — comptes courants",        "FINANCIER",       "ASSET",     "5", parent_code="51", is_reconcilable=True),
            AccountTemplate("53", "Caisse",                            "FINANCIER",       "ASSET",     "5"),
            AccountTemplate("59", "Dépréciations des comptes financ.","FINANCIER",        "CONTRA_ASSET","5"),
            # Classe 6 — Charges
            AccountTemplate("60", "Achats",                            "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("61", "Services extérieurs (1)",           "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("62", "Services extérieurs (2)",           "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("63", "Impôts, taxes et versements",       "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("64", "Charges de personnel",              "CHARGES",         "EXPENSE",   "6", is_detail=False),
            AccountTemplate("641","Rémunérations du personnel",        "CHARGES",         "EXPENSE",   "6", parent_code="64"),
            AccountTemplate("645","Charges sociales",                  "CHARGES",         "EXPENSE",   "6", parent_code="64"),
            AccountTemplate("65", "Autres charges de gestion",        "CHARGES",          "EXPENSE",   "6"),
            AccountTemplate("66", "Charges financières",               "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("68", "Dotations aux amort. et provisions","CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("69", "Impôt sur les bénéfices",          "CHARGES",         "EXPENSE",   "6"),
            # Classe 7 — Produits
            AccountTemplate("70", "Ventes de produits finis et marchandises","PRODUITS",  "REVENUE",   "7"),
            AccountTemplate("71", "Production stockée",                "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("72", "Production immobilisée",            "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("74", "Subventions d'exploitation",        "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("75", "Autres produits de gestion",       "PRODUITS",         "REVENUE",   "7"),
            AccountTemplate("76", "Produits financiers",               "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("78", "Reprises sur amort. et provisions", "PRODUITS",        "REVENUE",   "7"),
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """PCN luxembourgeois — Bilan (actif / passif) selon loi du 19/12/2002."""
        actif = FinancialStatement(code="LU_BILAN_ACTIF", name="Bilan Actif (PCN Lux.)", standard="LU_GAAP", lines=[
            FinancialStatementLine("A1",  "Immobilisations incorporelles",       ["20"],              indent_level=1),
            FinancialStatementLine("A2",  "Immobilisations corporelles",         ["21","23"],         indent_level=1),
            FinancialStatementLine("A3",  "Immobilisations financières",         ["26","27"],         indent_level=1),
            FinancialStatementLine("A4",  "Amortissements et dépréciations",     ["28","29"],         indent_level=1, negate=True),
            FinancialStatementLine("A5",  "ACTIFS IMMOBILISÉS",                  ["2"],               is_subtotal=True),
            FinancialStatementLine("A6",  "Stocks",                              ["3"],               indent_level=1),
            FinancialStatementLine("A7",  "Créances à un an au plus",            ["41","44","445"],   indent_level=1),
            FinancialStatementLine("A8",  "Avoirs en banques et caisses",        ["51","512","53"],   indent_level=1),
            FinancialStatementLine("A9",  "ACTIFS CIRCULANTS",                   ["3","4","5"],       is_subtotal=True),
            FinancialStatementLine("A0",  "TOTAL DE L'ACTIF",                    ["2","3","4","5"],   is_total=True),
        ])
        passif = FinancialStatement(code="LU_BILAN_PASSIF", name="Bilan Passif (PCN Lux.)", standard="LU_GAAP", lines=[
            FinancialStatementLine("P1",  "Capital souscrit",                    ["10","101"],        indent_level=1),
            FinancialStatementLine("P2",  "Primes et réserves",                  ["11","12"],         indent_level=1),
            FinancialStatementLine("P3",  "Résultat reporté et exercice",        ["13","14"],         indent_level=1),
            FinancialStatementLine("P4",  "Subventions d'investissement",        ["15"],              indent_level=1),
            FinancialStatementLine("P5",  "CAPITAUX PROPRES",                    ["10","11","12","13","14","15"], is_subtotal=True),
            FinancialStatementLine("P6",  "Provisions pour risques et charges",  ["16"],              indent_level=1),
            FinancialStatementLine("P7",  "Dettes financières à plus d'un an",   ["17"],              indent_level=1),
            FinancialStatementLine("P8",  "DETTES À PLUS D'UN AN",               ["16","17"],         is_subtotal=True),
            FinancialStatementLine("P9",  "Dettes fournisseurs",                 ["40","401"],        indent_level=1),
            FinancialStatementLine("P10", "Dettes fiscales et sociales",         ["42","43","44","441","446"], indent_level=1),
            FinancialStatementLine("P11", "DETTES À UN AN AU PLUS",              ["4"],               is_subtotal=True),
            FinancialStatementLine("P0",  "TOTAL DU PASSIF",                     ["1","4","16","17"], is_total=True),
        ])
        return actif, passif

    def get_income_statement_structure(self) -> FinancialStatement:
        """PCN luxembourgeois — Compte de profits et pertes (par nature)."""
        return FinancialStatement(code="LU_CPP", name="Compte de Profits et Pertes (PCN Lux.)", standard="LU_GAAP", lines=[
            FinancialStatementLine("R1",  "Chiffre d'affaires net",              ["70","71","72"],    indent_level=1),
            FinancialStatementLine("R2",  "Subventions d'exploitation",          ["74"],              indent_level=1),
            FinancialStatementLine("R3",  "Autres produits d'exploitation",      ["75"],              indent_level=1),
            FinancialStatementLine("R4",  "PRODUITS D'EXPLOITATION",             ["7"],               is_subtotal=True),
            FinancialStatementLine("R5",  "Coût des marchandises vendues",       ["60"],              indent_level=1, negate=True),
            FinancialStatementLine("R6",  "Services extérieurs",                 ["61","62"],         indent_level=1, negate=True),
            FinancialStatementLine("R7",  "Impôts et taxes",                     ["63"],              indent_level=1, negate=True),
            FinancialStatementLine("R8",  "Charges de personnel",                ["64","641","645"],  indent_level=1, negate=True),
            FinancialStatementLine("R9",  "Autres charges de gestion",           ["65"],              indent_level=1, negate=True),
            FinancialStatementLine("R10", "Dotations aux amortissements",        ["68"],              indent_level=1, negate=True),
            FinancialStatementLine("R11", "RÉSULTAT D'EXPLOITATION",             ["7","6"],           is_subtotal=True),
            FinancialStatementLine("R12", "Produits financiers",                 ["76"],              indent_level=1),
            FinancialStatementLine("R13", "Charges financières",                 ["66"],              indent_level=1, negate=True),
            FinancialStatementLine("R14", "RÉSULTAT COURANT",                    ["7","6"],           is_subtotal=True),
            FinancialStatementLine("R15", "Impôt sur le résultat",               ["69"],              indent_level=1, negate=True),
            FinancialStatementLine("R16", "RÉSULTAT DE L'EXERCICE",              ["7","6"],           is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {
            "TVA_17": {"rate": "17.00", "label": "TVA luxembourgeoise taux normal 17%", "account_collectee": "441"},
            "TVA_14": {"rate": "14.00", "label": "TVA taux intermédiaire 14%",          "account_collectee": "441"},
            "TVA_08": {"rate": "8.00",  "label": "TVA taux réduit 8%",                 "account_collectee": "441"},
            "TVA_03": {"rate": "3.00",  "label": "TVA taux super-réduit 3%",           "account_collectee": "441"},
            "TVA_00": {"rate": "0.00",  "label": "TVA exonérée",                       "account_collectee": None},
        }


StandardRegistry.register(LuxembourgGAAPStandard())
