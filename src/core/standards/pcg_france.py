"""Plan Comptable Général France 2025 — implémentation du référentiel."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .base import (
    AccountTemplate,
    AccountingStandard,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)

_PCG_JSON = Path(__file__).parent.parent.parent.parent / "data" / "charts_of_accounts" / "pcg_2025.json"


@lru_cache(maxsize=1)
def _load_pcg_json() -> list[dict[str, Any]]:
    with open(_PCG_JSON, encoding="utf-8") as f:
        return json.load(f)


class PCGFrance(AccountingStandard):
    """
    Plan Comptable Général — référentiel comptable français obligatoire.
    Conforme au décret du 29 novembre 1983, dernière mise à jour 2025.
    """

    @property
    def code(self) -> str:
        return "PCG"

    @property
    def name(self) -> str:
        return "Plan Comptable Général (France)"

    @property
    def country_codes(self) -> list[str]:
        return ["FR", "MC", "RE", "GP", "MQ", "GF", "PM", "MF"]

    @property
    def currency_default(self) -> str:
        return "EUR"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        return [
            AccountTemplate(
                code=a["code"],
                name=a["name"],
                account_type=a["account_type"],
                account_nature=a["account_nature"],
                account_class=a["account_class"],
                parent_code=a.get("parent_code"),
                is_detail=a.get("is_detail", True),
                vat_code=a.get("vat_code"),
            )
            for a in _load_pcg_json()
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        actif = FinancialStatement(code="BILAN_ACTIF", name="Bilan — Actif", standard="PCG", lines=[
            FinancialStatementLine("A1",  "Frais d'établissement",                        ["201"],         indent_level=1),
            FinancialStatementLine("A2",  "Frais de R&D",                                 ["203"],         indent_level=1),
            FinancialStatementLine("A3",  "Concessions, brevets, licences, logiciels",    ["205"],         indent_level=1),
            FinancialStatementLine("A4",  "Fonds commercial",                             ["207"],         indent_level=1),
            FinancialStatementLine("A5",  "Autres immobilisations incorporelles",         ["208", "232"],  indent_level=1),
            FinancialStatementLine("A6",  "Immobilisations incorporelles nettes",         ["20","280"],    is_subtotal=True, indent_level=0),
            FinancialStatementLine("A7",  "Terrains",                                     ["211"],         indent_level=1),
            FinancialStatementLine("A8",  "Constructions",                                ["213","214"],   indent_level=1),
            FinancialStatementLine("A9",  "Installations, matériel, outillage",           ["215"],         indent_level=1),
            FinancialStatementLine("A10", "Autres immobilisations corporelles",           ["218"],         indent_level=1),
            FinancialStatementLine("A11", "Immobilisations en cours",                     ["231","238"],   indent_level=1),
            FinancialStatementLine("A12", "Immobilisations corporelles nettes",           ["21","23","281","2812","2813","2815","2818"], is_subtotal=True, indent_level=0),
            FinancialStatementLine("A13", "Participations",                               ["261","266"],   indent_level=1),
            FinancialStatementLine("A14", "Créances rattachées à des participations",     ["267"],         indent_level=1),
            FinancialStatementLine("A15", "Autres immobilisations financières",           ["27"],          indent_level=1),
            FinancialStatementLine("A16", "Immobilisations financières nettes",           ["26","27","296","297"], is_subtotal=True, indent_level=0),
            FinancialStatementLine("A17", "TOTAL ACTIF IMMOBILISÉ",                       ["2","28","29"], is_total=True),
            FinancialStatementLine("A18", "Stocks matières premières",                    ["31","32"],     indent_level=1),
            FinancialStatementLine("A19", "En-cours de production",                       ["33","34"],     indent_level=1),
            FinancialStatementLine("A20", "Stocks produits finis et marchandises",        ["35","37"],     indent_level=1),
            FinancialStatementLine("A21", "Avances et acomptes versés",                   ["4091"],        indent_level=1),
            FinancialStatementLine("A22", "Créances clients et comptes rattachés",        ["411","412","416","418"], indent_level=1),
            FinancialStatementLine("A23", "Autres créances",                              ["441","461","467","471"], indent_level=1),
            FinancialStatementLine("A24", "Capital souscrit appelé non versé",            ["1012"],        indent_level=1),
            FinancialStatementLine("A25", "Valeurs mobilières de placement",              ["50"],          indent_level=1),
            FinancialStatementLine("A26", "Disponibilités",                               ["51","53"],     indent_level=1),
            FinancialStatementLine("A27", "Charges constatées d'avance",                  ["486"],         indent_level=1),
            FinancialStatementLine("A28", "TOTAL ACTIF CIRCULANT",                        ["3","4","5","486"], is_subtotal=True, indent_level=0),
            FinancialStatementLine("A29", "TOTAL GÉNÉRAL ACTIF",                          ["2","3","4","5","28","29","39","49","59","486"], is_total=True),
        ])

        passif = FinancialStatement(code="BILAN_PASSIF", name="Bilan — Passif", standard="PCG", lines=[
            FinancialStatementLine("P1",  "Capital social",                               ["101","1013"],  indent_level=1),
            FinancialStatementLine("P2",  "Primes d'émission, fusion, apport",           ["104"],         indent_level=1),
            FinancialStatementLine("P3",  "Réserves",                                     ["106"],         indent_level=1),
            FinancialStatementLine("P4",  "Report à nouveau",                             ["110","119"],   indent_level=1),
            FinancialStatementLine("P5",  "Résultat de l'exercice",                       ["120","129"],   indent_level=1),
            FinancialStatementLine("P6",  "Subventions d'investissement",                 ["13"],          indent_level=1),
            FinancialStatementLine("P7",  "Provisions réglementées",                      ["14"],          indent_level=1),
            FinancialStatementLine("P8",  "TOTAL CAPITAUX PROPRES",                       ["10","11","12","13","14"], is_subtotal=True, indent_level=0),
            FinancialStatementLine("P9",  "Provisions pour risques et charges",           ["15"],          indent_level=1),
            FinancialStatementLine("P10", "Emprunts obligataires",                        ["161","162"],   indent_level=1),
            FinancialStatementLine("P11", "Emprunts auprès des établissements de crédit", ["163"],         indent_level=1),
            FinancialStatementLine("P12", "Autres emprunts et dettes assimilées",         ["164","165","167","168"], indent_level=1),
            FinancialStatementLine("P13", "TOTAL DETTES FINANCIÈRES",                     ["16"],          is_subtotal=True, indent_level=0),
            FinancialStatementLine("P14", "Avances et acomptes reçus",                   ["4191"],        indent_level=1),
            FinancialStatementLine("P15", "Dettes fournisseurs et comptes rattachés",     ["401","402","404","408"], indent_level=1),
            FinancialStatementLine("P16", "Dettes fiscales et sociales",                  ["42","43","44","447","448"], indent_level=1),
            FinancialStatementLine("P17", "Autres dettes",                                ["462","487","519"], indent_level=1),
            FinancialStatementLine("P18", "TOTAL DETTES D'EXPLOITATION",                  ["40","42","43","44","45","46","487","519"], is_subtotal=True, indent_level=0),
            FinancialStatementLine("P19", "TOTAL GÉNÉRAL PASSIF",                         ["1","15","16","40","42","43","44","45","46","47","487","519"], is_total=True),
        ])

        return actif, passif

    def get_income_statement_structure(self) -> FinancialStatement:
        return FinancialStatement(code="COMPTE_RESULTAT", name="Compte de Résultat", standard="PCG", lines=[
            # Produits d'exploitation
            FinancialStatementLine("R1",  "Ventes de marchandises",                       ["707"],         indent_level=1),
            FinancialStatementLine("R2",  "Production vendue (biens)",                    ["701","702","703"], indent_level=1),
            FinancialStatementLine("R3",  "Production vendue (services)",                 ["704","705","706","708"], indent_level=1),
            FinancialStatementLine("R4",  "Production stockée",                           ["713"],         indent_level=1),
            FinancialStatementLine("R5",  "Production immobilisée",                       ["72"],          indent_level=1),
            FinancialStatementLine("R6",  "Subventions d'exploitation",                   ["74"],          indent_level=1),
            FinancialStatementLine("R7",  "Reprises sur provisions et dépréciations",     ["781"],         indent_level=1),
            FinancialStatementLine("R8",  "Autres produits",                              ["75","791"],    indent_level=1),
            FinancialStatementLine("R9",  "TOTAL PRODUITS D'EXPLOITATION",                ["7"],           is_subtotal=True),
            # Charges d'exploitation
            FinancialStatementLine("R10", "Achats de marchandises",                       ["607"],         indent_level=1),
            FinancialStatementLine("R11", "Variation de stocks marchandises",             ["6037"],        indent_level=1),
            FinancialStatementLine("R12", "Achats de matières premières",                 ["601","602"],   indent_level=1),
            FinancialStatementLine("R13", "Variation de stocks matières",                 ["603"],         indent_level=1),
            FinancialStatementLine("R14", "Autres achats et charges externes",            ["60","61","62"], indent_level=1),
            FinancialStatementLine("R15", "Impôts, taxes et versements assimilés",        ["63"],          indent_level=1),
            FinancialStatementLine("R16", "Charges de personnel",                         ["64"],          indent_level=1),
            FinancialStatementLine("R17", "Dotations aux amortissements et provisions",   ["681"],         indent_level=1),
            FinancialStatementLine("R18", "Autres charges",                               ["65"],          indent_level=1),
            FinancialStatementLine("R19", "TOTAL CHARGES D'EXPLOITATION",                 ["6"],           is_subtotal=True),
            FinancialStatementLine("R20", "RÉSULTAT D'EXPLOITATION",                      ["7","6"],       is_total=True),
            # Résultat financier
            FinancialStatementLine("R21", "Produits financiers",                          ["76"],          indent_level=1),
            FinancialStatementLine("R22", "Charges financières",                          ["66"],          indent_level=1),
            FinancialStatementLine("R23", "RÉSULTAT FINANCIER",                           ["76","66"],     is_subtotal=True),
            FinancialStatementLine("R24", "RÉSULTAT COURANT AVANT IMPÔTS",               ["7","6","76","66"], is_total=True),
            # Résultat exceptionnel
            FinancialStatementLine("R25", "Produits exceptionnels",                       ["77","787"],    indent_level=1),
            FinancialStatementLine("R26", "Charges exceptionnelles",                      ["67","687"],    indent_level=1),
            FinancialStatementLine("R27", "RÉSULTAT EXCEPTIONNEL",                        ["77","787","67","687"], is_subtotal=True),
            # Résultat net
            FinancialStatementLine("R28", "Participation des salariés",                   ["691"],         indent_level=1),
            FinancialStatementLine("R29", "Impôts sur les bénéfices",                     ["695"],         indent_level=1),
            FinancialStatementLine("R30", "RÉSULTAT NET",                                 ["7","6","69"],  is_total=True),
        ])

    def get_cash_flow_structure(self) -> FinancialStatement:
        return FinancialStatement(code="TFT", name="Tableau de Flux de Trésorerie (méthode indirecte)", standard="PCG", lines=[
            FinancialStatementLine("T1",  "Résultat net de l'exercice",                   ["120","129"],   indent_level=0),
            FinancialStatementLine("T2",  "Dotations aux amortissements et provisions",   ["681","686","687"], indent_level=1),
            FinancialStatementLine("T3",  "Reprises sur provisions et dépréciations",     ["781","786","787"], indent_level=1, negate=True),
            FinancialStatementLine("T4",  "Plus/moins-values de cessions",                ["675","775"],   indent_level=1),
            FinancialStatementLine("T5",  "Variation du BFR (stocks)",                    ["3","39"],      indent_level=1),
            FinancialStatementLine("T6",  "Variation du BFR (créances d'exploitation)",   ["411","416","418","486"], indent_level=1),
            FinancialStatementLine("T7",  "Variation du BFR (dettes d'exploitation)",     ["401","42","43","44","487"], indent_level=1),
            FinancialStatementLine("T8",  "FLUX DE TRÉSORERIE D'EXPLOITATION",            [],              is_subtotal=True),
            FinancialStatementLine("T9",  "Acquisitions d'immobilisations",               ["21","20","26","27"], indent_level=1, negate=True),
            FinancialStatementLine("T10", "Cessions d'immobilisations",                   ["775"],         indent_level=1),
            FinancialStatementLine("T11", "Variation des immobilisations financières",    ["26","27"],     indent_level=1),
            FinancialStatementLine("T12", "FLUX DE TRÉSORERIE D'INVESTISSEMENT",          [],              is_subtotal=True),
            FinancialStatementLine("T13", "Augmentation de capital",                      ["101","104"],   indent_level=1),
            FinancialStatementLine("T14", "Nouveaux emprunts",                            ["16"],          indent_level=1),
            FinancialStatementLine("T15", "Remboursements d'emprunts",                    ["16"],          indent_level=1, negate=True),
            FinancialStatementLine("T16", "Dividendes versés",                            ["457"],         indent_level=1, negate=True),
            FinancialStatementLine("T17", "FLUX DE TRÉSORERIE DE FINANCEMENT",            [],              is_subtotal=True),
            FinancialStatementLine("T18", "VARIATION NETTE DE TRÉSORERIE",                [],              is_total=True),
            FinancialStatementLine("T19", "Trésorerie ouverture",                         ["51","53","519"], indent_level=1),
            FinancialStatementLine("T20", "Trésorerie clôture",                           ["51","53","519"], indent_level=1),
        ])

    def get_vat_codes(self) -> dict[str, dict[str, Any]]:
        return {
            "TVA_20": {"rate": "20.00", "label": "TVA normale 20%",       "account_collectee": "44571", "account_deductible": "44566"},
            "TVA_10": {"rate": "10.00", "label": "TVA réduite 10%",       "account_collectee": "44571", "account_deductible": "44566"},
            "TVA_55": {"rate": "5.50",  "label": "TVA réduite 5,5%",      "account_collectee": "44571", "account_deductible": "44566"},
            "TVA_21": {"rate": "2.10",  "label": "TVA super-réduite 2,1%","account_collectee": "44571", "account_deductible": "44566"},
            "TVA_00": {"rate": "0.00",  "label": "TVA 0% / exonéré",      "account_collectee": None,    "account_deductible": None},
        }


# Auto-registration
StandardRegistry.register(PCGFrance())
