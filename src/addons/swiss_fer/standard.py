"""Swiss GAAP FER — Fachempfehlungen zur Rechnungslegung (Swiss Accounting Standards)."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountingStandard,
    AccountTemplate,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class SwissGAAPFERStandard(AccountingStandard):
    """
    Swiss GAAP FER — KMU-Kontenrahmen (PME) basé sur le plan Käfer / Kontenrahmen KMU.
    Swiss Code of Obligations (OR) art. 957-963b pour les PME, Swiss GAAP FER pour groupes.
    """

    @property
    def code(self) -> str:
        return "CH_FER"

    @property
    def name(self) -> str:
        return "Swiss GAAP FER — Fachempfehlungen zur Rechnungslegung"

    @property
    def country_codes(self) -> list[str]:
        return ["CH", "LI"]

    @property
    def currency_default(self) -> str:
        return "CHF"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Kontenrahmen KMU (Swiss SME chart of accounts) — structure en classes 1-9."""
        return [
            # Classe 1 — Actifs circulants (Umlaufvermögen)
            AccountTemplate("100", "Kasse / Caisse",                "FINANCIER",       "ASSET",     "1"),
            AccountTemplate("102", "Postcheck / CCP",               "FINANCIER",       "ASSET",     "1", is_reconcilable=True),
            AccountTemplate("104", "Bank",                          "FINANCIER",       "ASSET",     "1", is_reconcilable=True),
            AccountTemplate("110", "Wertschriften / Titres",        "FINANCIER",       "ASSET",     "1"),
            AccountTemplate("120", "Forderungen LL / Débiteurs",    "TIERS",           "ASSET",     "1", is_reconcilable=True),
            AccountTemplate("130", "Vorräte / Stocks",              "STOCKS",          "ASSET",     "1"),
            AccountTemplate("140", "Aktive Rechnungsabgr.",         "TIERS",           "ASSET",     "1"),
            AccountTemplate("170", "Vorsteuer MWST",                "TIERS",           "ASSET",     "1"),
            # Classe 2 — Actifs immobilisés (Anlagevermögen)
            AccountTemplate("200", "Finanzanlagen",                 "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("210", "Beteiligungen",                 "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("220", "Sachanlagen (mobil)",           "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("230", "Sachanlagen (immobil)",         "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("240", "Immaterielle Anlagen",          "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("250", "Nicht einbezahltes Kapital",    "IMMOBILISATIONS", "ASSET",     "2"),
            # Classe 2 — Passifs (Fremdkapital / Eigenkapital)
            AccountTemplate("200", "Verbindlichkeiten LL / Kreditoren","TIERS",        "LIABILITY", "2", is_reconcilable=True),
            AccountTemplate("201", "Kreditoren",                    "TIERS",           "LIABILITY", "2", parent_code="200", is_reconcilable=True),
            AccountTemplate("210", "Kurzfristige Bankschulden",     "TIERS",           "LIABILITY", "2"),
            AccountTemplate("220", "Sonstige kurzfristige Schulden","TIERS",           "LIABILITY", "2"),
            AccountTemplate("230", "Passive Rechnungsabgr.",        "TIERS",           "LIABILITY", "2"),
            AccountTemplate("240", "Geschuldete MWST",              "TIERS",           "LIABILITY", "2", vat_code="MWST_81"),
            AccountTemplate("260", "Langfristige Bankschulden",     "CAPITAUX",        "LIABILITY", "2"),
            AccountTemplate("270", "Rückstellungen",                "CAPITAUX",        "LIABILITY", "2"),
            AccountTemplate("280", "Eigenkapital",                  "CAPITAUX",        "EQUITY",    "2", is_detail=False),
            AccountTemplate("281", "Aktienkapital / Capital-actions","CAPITAUX",       "EQUITY",    "2", parent_code="280"),
            AccountTemplate("283", "Gesetzliche Reserven",          "CAPITAUX",        "EQUITY",    "2", parent_code="280"),
            AccountTemplate("286", "Gewinnvortrag / Report bénéfice","CAPITAUX",       "EQUITY",    "2", parent_code="280"),
            AccountTemplate("289", "Jahresgewinn / Bénéfice annuel","CAPITAUX",        "EQUITY",    "2", parent_code="280"),
            # Classe 3 — Produits (Ertrag)
            AccountTemplate("300", "Warenertrag / Chiffre d'affaires","PRODUITS",      "REVENUE",   "3"),
            AccountTemplate("320", "Dienstleistungsertrag",         "PRODUITS",        "REVENUE",   "3"),
            AccountTemplate("340", "Finanzertrag",                  "PRODUITS",        "REVENUE",   "3"),
            AccountTemplate("360", "Übrige betriebliche Erträge",   "PRODUITS",        "REVENUE",   "3"),
            # Classe 4 — Charges variables (Aufwand Waren)
            AccountTemplate("400", "Warenaufwand / Achats",         "CHARGES",         "EXPENSE",   "4"),
            AccountTemplate("420", "Produktionsaufwand",            "CHARGES",         "EXPENSE",   "4"),
            # Classe 5 — Personnel
            AccountTemplate("500", "Lohnaufwand / Salaires",        "CHARGES",         "EXPENSE",   "5"),
            AccountTemplate("510", "Sozialversicherungen",          "CHARGES",         "EXPENSE",   "5"),
            AccountTemplate("520", "Übriger Personalaufwand",       "CHARGES",         "EXPENSE",   "5"),
            # Classe 6 — Charges générales
            AccountTemplate("600", "Raumaufwand / Loyers",          "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("610", "Unterhalt / Entretien",         "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("620", "Fahrzeugaufwand / Véhicules",   "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("630", "Sachversicherungen",            "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("640", "Energie und Entsorgung",        "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("650", "Verwaltung / Administration",   "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("660", "Werbung / Marketing",           "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("670", "Abschreibungen",                "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("680", "Finanzaufwand / Charges fin.",  "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("690", "Steuern / Impôts",              "CHARGES",         "EXPENSE",   "6"),
            # Classe 9 — Comptes de clôture
            AccountTemplate("900", "Eröffnungsbilanz",              "SPECIAUX",        "EQUITY",    "9"),
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """Swiss GAAP FER 3 — Bilanz / Bilan."""
        aktiva = FinancialStatement(code="CH_BILAN_ACTIF", name="Bilan — Actif (Swiss GAAP FER)", standard="CH_FER", lines=[
            FinancialStatementLine("A1",  "Flüssige Mittel / Liquidités",        ["100","102","104"], indent_level=1),
            FinancialStatementLine("A2",  "Wertschriften / Titres",              ["110"],             indent_level=1),
            FinancialStatementLine("A3",  "Forderungen LL / Débiteurs",          ["120"],             indent_level=1),
            FinancialStatementLine("A4",  "Vorräte / Stocks",                    ["130"],             indent_level=1),
            FinancialStatementLine("A5",  "Aktive Abgrenzungen",                 ["140","170"],       indent_level=1),
            FinancialStatementLine("A6",  "UMLAUFVERMÖGEN / ACTIFS CIRCULANTS", ["1"],               is_subtotal=True),
            FinancialStatementLine("A7",  "Finanzanlagen / Placements fin.",     ["200","210"],       indent_level=1),
            FinancialStatementLine("A8",  "Sachanlagen / Immobilisations corp.", ["220","230"],       indent_level=1),
            FinancialStatementLine("A9",  "Immaterielle Anlagen",                ["240"],             indent_level=1),
            FinancialStatementLine("A10", "ANLAGEVERMÖGEN / ACTIFS IMMOBILISÉS",["2"],               is_subtotal=True),
            FinancialStatementLine("A0",  "BILANZSUMME AKTIVA / TOTAL ACTIF",   ["1","2"],           is_total=True),
        ])
        passiva = FinancialStatement(code="CH_BILAN_PASSIF", name="Bilan — Passif (Swiss GAAP FER)", standard="CH_FER", lines=[
            FinancialStatementLine("P1",  "Verbindlichkeiten LL / Créanciers",   ["200","201"],       indent_level=1),
            FinancialStatementLine("P2",  "Kurzfristige Bankschulden",           ["210"],             indent_level=1),
            FinancialStatementLine("P3",  "Sonstige kurzfristige Schulden",      ["220","230","240"], indent_level=1),
            FinancialStatementLine("P4",  "KURZFRISTIGES FK / PASSIFS À CT",    ["2"],               is_subtotal=True),
            FinancialStatementLine("P5",  "Langfristige Bankschulden",           ["260"],             indent_level=1),
            FinancialStatementLine("P6",  "Rückstellungen / Provisions",         ["270"],             indent_level=1),
            FinancialStatementLine("P7",  "LANGFRISTIGES FK / PASSIFS À LT",    ["26","27"],         is_subtotal=True),
            FinancialStatementLine("P8",  "Aktienkapital / Capital-actions",     ["281"],             indent_level=1),
            FinancialStatementLine("P9",  "Reserven / Réserves",                 ["283"],             indent_level=1),
            FinancialStatementLine("P10", "Gewinnvortrag / Report",              ["286"],             indent_level=1),
            FinancialStatementLine("P11", "Jahresgewinn / Bénéfice",             ["289"],             indent_level=1),
            FinancialStatementLine("P12", "EIGENKAPITAL / FONDS PROPRES",       ["28"],              is_subtotal=True),
            FinancialStatementLine("P0",  "BILANZSUMME PASSIVA / TOTAL PASSIF", ["2","26","27","28"], is_total=True),
        ])
        return aktiva, passiva

    def get_income_statement_structure(self) -> FinancialStatement:
        """Swiss GAAP FER 3 — Erfolgsrechnung / Compte de résultat (méthode des charges par nature)."""
        return FinancialStatement(code="CH_ER", name="Erfolgsrechnung (Swiss GAAP FER)", standard="CH_FER", lines=[
            FinancialStatementLine("E1",  "Warenertrag / Chiffre d'affaires",    ["300","320"],       indent_level=1),
            FinancialStatementLine("E2",  "Übriger Ertrag",                      ["360"],             indent_level=1),
            FinancialStatementLine("E3",  "BETRIEBSERTRAG / PRODUITS D'EXPL.",  ["3"],               is_subtotal=True),
            FinancialStatementLine("E4",  "Warenaufwand / Coût d'achat",         ["400","420"],       indent_level=1, negate=True),
            FinancialStatementLine("E5",  "Personalaufwand / Charges personnel", ["500","510","520"], indent_level=1, negate=True),
            FinancialStatementLine("E6",  "Übriger betrieblicher Aufwand",       ["600","610","620","630","640","650","660"], indent_level=1, negate=True),
            FinancialStatementLine("E7",  "Abschreibungen",                      ["670"],             indent_level=1, negate=True),
            FinancialStatementLine("E8",  "BETRIEBSERGEBNIS (EBIT)",            ["3","4","5","6"],   is_subtotal=True),
            FinancialStatementLine("E9",  "Finanzertrag",                        ["340"],             indent_level=1),
            FinancialStatementLine("E10", "Finanzaufwand",                       ["680"],             indent_level=1, negate=True),
            FinancialStatementLine("E11", "ERGEBNIS VOR STEUERN",               ["3","4","5","6","34","68"], is_subtotal=True),
            FinancialStatementLine("E12", "Steuern",                             ["690"],             indent_level=1, negate=True),
            FinancialStatementLine("E13", "JAHRESERGEBNIS / RÉSULTAT ANNUEL",   ["3","4","5","6"],   is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {
            "MWST_81": {"rate": "8.10",  "label": "MWST Normalsatz 8.1%",      "account_collectee": "240"},
            "MWST_38": {"rate": "3.80",  "label": "MWST Sondersatz Beherb. 3.8%","account_collectee": "240"},
            "MWST_25": {"rate": "2.50",  "label": "MWST reduzierter Satz 2.5%","account_collectee": "240"},
            "MWST_00": {"rate": "0.00",  "label": "MWST befreit / ausgenommen","account_collectee": None},
        }


StandardRegistry.register(SwissGAAPFERStandard())
