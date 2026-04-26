"""German HGB — Handelsgesetzbuch (German Commercial Code)."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountTemplate,
    AccountingStandard,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class GermanHGBStandard(AccountingStandard):
    """
    Deutscher Kontenrahmen nach HGB — SKR 03 / SKR 04 (Prozessgliederungsprinzip).
    Référence : HGB §§ 238-339, GoB (Grundsätze ordnungsmäßiger Buchführung).
    """

    @property
    def code(self) -> str:
        return "DE_HGB"

    @property
    def name(self) -> str:
        return "German GAAP — Handelsgesetzbuch (HGB)"

    @property
    def country_codes(self) -> list[str]:
        return ["DE"]

    @property
    def currency_default(self) -> str:
        return "EUR"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Kontenrahmen SKR 03 (Abschlussgliederungsprinzip) — principales classes."""
        return [
            # Klasse 0 — Anlage- und Kapitalkonten
            AccountTemplate("00", "Sachanlagen",                    "IMMOBILISATIONS", "ASSET",     "0", is_detail=False),
            AccountTemplate("001","Grundstücke und Gebäude",        "IMMOBILISATIONS", "ASSET",     "0", parent_code="00"),
            AccountTemplate("004","Technische Anlagen und Maschinen","IMMOBILISATIONS","ASSET",     "0", parent_code="00"),
            AccountTemplate("008","Betriebs- und Geschäftsausstattung","IMMOBILISATIONS","ASSET",   "0", parent_code="00"),
            AccountTemplate("01", "Immaterielle Vermögensgegenstände","IMMOBILISATIONS","ASSET",    "0", is_detail=False),
            AccountTemplate("010","Selbst geschaffene Schutzrechte", "IMMOBILISATIONS","ASSET",     "0", parent_code="01"),
            AccountTemplate("013","Firmenwert",                     "IMMOBILISATIONS", "ASSET",     "0", parent_code="01"),
            AccountTemplate("02", "Finanzanlagen",                  "IMMOBILISATIONS", "ASSET",     "0", is_detail=False),
            AccountTemplate("021","Anteile an verbundenen Unternehmen","IMMOBILISATIONS","ASSET",   "0", parent_code="02"),
            AccountTemplate("03", "Eigenkapital",                   "CAPITAUX",        "EQUITY",    "0", is_detail=False),
            AccountTemplate("030","Gezeichnetes Kapital",           "CAPITAUX",        "EQUITY",    "0", parent_code="03"),
            AccountTemplate("031","Kapitalrücklage",                "CAPITAUX",        "EQUITY",    "0", parent_code="03"),
            AccountTemplate("032","Gewinnrücklagen",                "CAPITAUX",        "EQUITY",    "0", parent_code="03"),
            AccountTemplate("035","Jahresüberschuss / -fehlbetrag", "CAPITAUX",        "EQUITY",    "0", parent_code="03"),
            AccountTemplate("04", "Rückstellungen",                 "CAPITAUX",        "LIABILITY", "0", is_detail=False),
            AccountTemplate("040","Pensionsrückstellungen",         "CAPITAUX",        "LIABILITY", "0", parent_code="04"),
            AccountTemplate("044","Steuerrückstellungen",           "CAPITAUX",        "LIABILITY", "0", parent_code="04"),
            AccountTemplate("049","Sonstige Rückstellungen",        "CAPITAUX",        "LIABILITY", "0", parent_code="04"),
            AccountTemplate("05", "Verbindlichkeiten (langfristig)","CAPITAUX",        "LIABILITY", "0", is_detail=False),
            AccountTemplate("050","Anleihen",                       "CAPITAUX",        "LIABILITY", "0", parent_code="05"),
            AccountTemplate("053","Verbindlichkeiten ggü. Kreditinstituten","CAPITAUX","LIABILITY", "0", parent_code="05"),
            # Klasse 1 — Finanz- und Privatkonten
            AccountTemplate("10", "Kasse",                          "FINANCIER",       "ASSET",     "1"),
            AccountTemplate("12", "Bankkonten",                     "FINANCIER",       "ASSET",     "1", is_reconcilable=True),
            AccountTemplate("120","Bank",                           "FINANCIER",       "ASSET",     "1", parent_code="12", is_reconcilable=True),
            AccountTemplate("13", "Wertpapiere des Umlaufvermögens","FINANCIER",       "ASSET",     "1"),
            AccountTemplate("17", "Umsatzsteuer",                   "TIERS",           "LIABILITY", "1", is_detail=False),
            AccountTemplate("175","Umsatzsteuer 19%",               "TIERS",           "LIABILITY", "1", parent_code="17", vat_code="UST_19"),
            AccountTemplate("176","Umsatzsteuer 7%",                "TIERS",           "LIABILITY", "1", parent_code="17", vat_code="UST_07"),
            AccountTemplate("18", "Umsatzsteuer-Vorauszahlung",     "TIERS",           "ASSET",     "1"),
            AccountTemplate("19", "Vorsteuer",                      "TIERS",           "ASSET",     "1", is_detail=False),
            AccountTemplate("190","Vorsteuer 19%",                  "TIERS",           "ASSET",     "1", parent_code="19"),
            # Klasse 2 — Abgrenzungskonten
            AccountTemplate("20", "Aktive Rechnungsabgrenzung",     "TIERS",           "ASSET",     "2"),
            AccountTemplate("21", "Passive Rechnungsabgrenzung",    "TIERS",           "LIABILITY", "2"),
            # Klasse 3 — Warenvorrat und Erzeugnisse
            AccountTemplate("30", "Waren",                          "STOCKS",          "ASSET",     "3"),
            AccountTemplate("31", "Roh-, Hilfs- und Betriebsstoffe","STOCKS",          "ASSET",     "3"),
            AccountTemplate("32", "Unfertige Erzeugnisse",          "STOCKS",          "ASSET",     "3"),
            AccountTemplate("33", "Fertige Erzeugnisse",            "STOCKS",          "ASSET",     "3"),
            # Klasse 4 — Betriebliche Aufwendungen
            AccountTemplate("40", "Materialaufwand",                "CHARGES",         "EXPENSE",   "4", is_detail=False),
            AccountTemplate("400","Aufwendungen für Roh- u. Hilfsstoffe","CHARGES",    "EXPENSE",   "4", parent_code="40"),
            AccountTemplate("44", "Personalaufwand",                "CHARGES",         "EXPENSE",   "4", is_detail=False),
            AccountTemplate("440","Löhne und Gehälter",             "CHARGES",         "EXPENSE",   "4", parent_code="44"),
            AccountTemplate("441","Soziale Abgaben",                "CHARGES",         "EXPENSE",   "4", parent_code="44"),
            AccountTemplate("46", "Abschreibungen",                 "CHARGES",         "EXPENSE",   "4"),
            AccountTemplate("47", "Sonstige betriebliche Aufwendungen","CHARGES",      "EXPENSE",   "4"),
            AccountTemplate("48", "Zinsaufwendungen",               "CHARGES",         "EXPENSE",   "4"),
            AccountTemplate("49", "Steuern",                        "CHARGES",         "EXPENSE",   "4"),
            # Klasse 5 — Betriebliche Erträge
            AccountTemplate("50", "Umsatzerlöse",                   "PRODUITS",        "REVENUE",   "5"),
            AccountTemplate("51", "Bestandsveränderungen",          "PRODUITS",        "REVENUE",   "5"),
            AccountTemplate("52", "Sonstige betriebliche Erträge",  "PRODUITS",        "REVENUE",   "5"),
            AccountTemplate("54", "Zinserträge",                    "PRODUITS",        "REVENUE",   "5"),
            AccountTemplate("55", "Beteiligungserträge",            "PRODUITS",        "REVENUE",   "5"),
            # Klasse 6 — Debitoren und Kreditoren
            AccountTemplate("60", "Forderungen aus Lieferungen",    "TIERS",           "ASSET",     "6", is_reconcilable=True),
            AccountTemplate("600","Debitoren",                      "TIERS",           "ASSET",     "6", parent_code="60", is_reconcilable=True),
            AccountTemplate("62", "Sonstige Vermögensgegenstände",  "TIERS",           "ASSET",     "6"),
            AccountTemplate("65", "Verbindlichkeiten aus Lieferungen","TIERS",         "LIABILITY", "6", is_reconcilable=True),
            AccountTemplate("650","Kreditoren",                     "TIERS",           "LIABILITY", "6", parent_code="65", is_reconcilable=True),
            AccountTemplate("68", "Sonstige Verbindlichkeiten",     "TIERS",           "LIABILITY", "6"),
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """HGB § 266 — Bilanzgliederung (Aktiva / Passiva)."""
        aktiva = FinancialStatement(code="DE_BILANZ_AKTIVA", name="Bilanz Aktiva (HGB)", standard="DE_HGB", lines=[
            FinancialStatementLine("A1",  "Immaterielle Vermögensgegenstände",      ["01"],           indent_level=1),
            FinancialStatementLine("A2",  "Sachanlagen",                            ["00"],           indent_level=1),
            FinancialStatementLine("A3",  "Finanzanlagen",                          ["02"],           indent_level=1),
            FinancialStatementLine("A4",  "ANLAGEVERMÖGEN",                         ["0"],            is_subtotal=True),
            FinancialStatementLine("A5",  "Vorräte",                                ["3"],            indent_level=1),
            FinancialStatementLine("A6",  "Forderungen aus Lieferungen",            ["60","62"],      indent_level=1),
            FinancialStatementLine("A7",  "Wertpapiere",                            ["13"],           indent_level=1),
            FinancialStatementLine("A8",  "Kassenbestand, Bankguthaben",            ["10","12"],      indent_level=1),
            FinancialStatementLine("A9",  "UMLAUFVERMÖGEN",                         ["1","3","6","62"], is_subtotal=True),
            FinancialStatementLine("A10", "Aktive Rechnungsabgrenzung",             ["20"],           indent_level=1),
            FinancialStatementLine("A0",  "BILANZSUMME AKTIVA",                     ["0","1","2","3","6"], is_total=True),
        ])
        passiva = FinancialStatement(code="DE_BILANZ_PASSIVA", name="Bilanz Passiva (HGB)", standard="DE_HGB", lines=[
            FinancialStatementLine("P1",  "Gezeichnetes Kapital",                   ["030"],          indent_level=1),
            FinancialStatementLine("P2",  "Kapitalrücklage",                        ["031"],          indent_level=1),
            FinancialStatementLine("P3",  "Gewinnrücklagen",                        ["032"],          indent_level=1),
            FinancialStatementLine("P4",  "Jahresüberschuss / -fehlbetrag",         ["035"],          indent_level=1),
            FinancialStatementLine("P5",  "EIGENKAPITAL",                           ["03"],           is_subtotal=True),
            FinancialStatementLine("P6",  "Rückstellungen",                         ["04"],           indent_level=1),
            FinancialStatementLine("P7",  "Verbindlichkeiten (langfristig)",        ["05"],           indent_level=1),
            FinancialStatementLine("P8",  "Verbindlichkeiten (kurzfristig)",        ["65","68"],      indent_level=1),
            FinancialStatementLine("P9",  "FREMDKAPITAL",                           ["04","05","65","68"], is_subtotal=True),
            FinancialStatementLine("P10", "Passive Rechnungsabgrenzung",            ["21"],           indent_level=1),
            FinancialStatementLine("P0",  "BILANZSUMME PASSIVA",                    ["0","2","3","4","5","6"], is_total=True),
        ])
        return aktiva, passiva

    def get_income_statement_structure(self) -> FinancialStatement:
        """HGB § 275 — Gewinn- und Verlustrechnung (Gesamtkostenverfahren)."""
        return FinancialStatement(code="DE_GUV", name="Gewinn- und Verlustrechnung (HGB)", standard="DE_HGB", lines=[
            FinancialStatementLine("G1",  "Umsatzerlöse",                           ["50"],           indent_level=1),
            FinancialStatementLine("G2",  "Bestandsveränderungen",                  ["51"],           indent_level=1),
            FinancialStatementLine("G3",  "Sonstige betriebliche Erträge",          ["52"],           indent_level=1),
            FinancialStatementLine("G4",  "BETRIEBLICHE ERTRÄGE",                   ["5"],            is_subtotal=True),
            FinancialStatementLine("G5",  "Materialaufwand",                        ["40"],           indent_level=1, negate=True),
            FinancialStatementLine("G6",  "Personalaufwand",                        ["44"],           indent_level=1, negate=True),
            FinancialStatementLine("G7",  "Abschreibungen",                         ["46"],           indent_level=1, negate=True),
            FinancialStatementLine("G8",  "Sonstige betriebliche Aufwendungen",     ["47"],           indent_level=1, negate=True),
            FinancialStatementLine("G9",  "BETRIEBSERGEBNIS (EBIT)",               ["5","4"],        is_subtotal=True),
            FinancialStatementLine("G10", "Zinserträge",                            ["54"],           indent_level=1),
            FinancialStatementLine("G11", "Beteiligungserträge",                    ["55"],           indent_level=1),
            FinancialStatementLine("G12", "Zinsaufwendungen",                       ["48"],           indent_level=1, negate=True),
            FinancialStatementLine("G13", "ERGEBNIS DER GEWÖHNL. GESCHÄFTSTÄTIGKEIT",["5","4","48","54","55"], is_subtotal=True),
            FinancialStatementLine("G14", "Steuern",                                ["49"],           indent_level=1, negate=True),
            FinancialStatementLine("G15", "JAHRESÜBERSCHUSS / -FEHLBETRAG",         ["5","4"],        is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {
            "UST_19": {"rate": "19.00", "label": "Umsatzsteuer 19%",   "account_collectee": "175"},
            "UST_07": {"rate": "7.00",  "label": "Umsatzsteuer 7%",    "account_collectee": "176"},
            "UST_00": {"rate": "0.00",  "label": "Umsatzsteuer 0%",    "account_collectee": None},
        }


StandardRegistry.register(GermanHGBStandard())
