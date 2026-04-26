"""Italian OIC — Organismo Italiano di Contabilità (Italian Accounting Standards)."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountTemplate,
    AccountingStandard,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class ItalianOICStandard(AccountingStandard):
    """
    Principi Contabili OIC — Organismo Italiano di Contabilità.
    Codice Civile art. 2423-2435-ter + OIC standards.
    Piano dei Conti per PMI italiane.
    """

    @property
    def code(self) -> str:
        return "IT_OIC"

    @property
    def name(self) -> str:
        return "Italian GAAP — Principi Contabili OIC"

    @property
    def country_codes(self) -> list[str]:
        return ["IT"]

    @property
    def currency_default(self) -> str:
        return "EUR"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Piano dei Conti italiano — struttura tipica per PMI."""
        return [
            # Classe A — Patrimonio Netto
            AccountTemplate("A1",  "Capitale sociale",                 "CAPITAUX",        "EQUITY",    "A"),
            AccountTemplate("A2",  "Riserva legale",                   "CAPITAUX",        "EQUITY",    "A"),
            AccountTemplate("A3",  "Riserve statutarie",               "CAPITAUX",        "EQUITY",    "A"),
            AccountTemplate("A4",  "Riserva straordinaria",            "CAPITAUX",        "EQUITY",    "A"),
            AccountTemplate("A7",  "Utile / perdita esercizi precedenti","CAPITAUX",      "EQUITY",    "A"),
            AccountTemplate("A9",  "Utile / perdita d'esercizio",      "CAPITAUX",        "EQUITY",    "A"),
            # Classe B — Fondi e TFR
            AccountTemplate("B1",  "Fondi per rischi e oneri",         "CAPITAUX",        "LIABILITY", "B"),
            AccountTemplate("B2",  "Fondo TFR (Tratt. Fine Rapporto)", "CAPITAUX",        "LIABILITY", "B"),
            # Classe C — Debiti a lungo termine
            AccountTemplate("C1",  "Obbligazioni",                     "CAPITAUX",        "LIABILITY", "C"),
            AccountTemplate("C2",  "Debiti verso banche (oltre 12m)",  "CAPITAUX",        "LIABILITY", "C"),
            # Classe D — Immobilizzazioni immateriali
            AccountTemplate("D1",  "Costi di impianto e ampliamento",  "IMMOBILISATIONS", "ASSET",     "D"),
            AccountTemplate("D2",  "Costi di sviluppo",                "IMMOBILISATIONS", "ASSET",     "D"),
            AccountTemplate("D3",  "Diritti di brevetto industriale",  "IMMOBILISATIONS", "ASSET",     "D"),
            AccountTemplate("D4",  "Avviamento / Goodwill",            "IMMOBILISATIONS", "ASSET",     "D"),
            AccountTemplate("D5",  "Immobilizzazioni in corso (imm.)", "IMMOBILISATIONS", "ASSET",     "D"),
            # Classe E — Immobilizzazioni materiali
            AccountTemplate("E1",  "Terreni e fabbricati",             "IMMOBILISATIONS", "ASSET",     "E"),
            AccountTemplate("E2",  "Impianti e macchinario",           "IMMOBILISATIONS", "ASSET",     "E"),
            AccountTemplate("E3",  "Attrezzature industriali",         "IMMOBILISATIONS", "ASSET",     "E"),
            AccountTemplate("E4",  "Altri beni (mobili, veicoli)",     "IMMOBILISATIONS", "ASSET",     "E"),
            AccountTemplate("E5",  "Immobilizzazioni in corso (mat.)", "IMMOBILISATIONS", "ASSET",     "E"),
            # Classe F — Immobilizzazioni finanziarie
            AccountTemplate("F1",  "Partecipazioni in controllate",    "IMMOBILISATIONS", "ASSET",     "F"),
            AccountTemplate("F2",  "Crediti finanziari a lungo termine","IMMOBILISATIONS","ASSET",     "F"),
            # Classe G — Rimanenze
            AccountTemplate("G1",  "Materie prime e sussidiarie",      "STOCKS",          "ASSET",     "G"),
            AccountTemplate("G2",  "Prodotti in corso di lavorazione", "STOCKS",          "ASSET",     "G"),
            AccountTemplate("G4",  "Prodotti finiti e merci",          "STOCKS",          "ASSET",     "G"),
            # Classe H — Crediti a breve termine
            AccountTemplate("H1",  "Crediti verso clienti",            "TIERS",           "ASSET",     "H", is_reconcilable=True),
            AccountTemplate("H2",  "Crediti verso controllate",        "TIERS",           "ASSET",     "H"),
            AccountTemplate("H4",  "Crediti tributari",                "TIERS",           "ASSET",     "H"),
            AccountTemplate("H5",  "IVA a credito",                    "TIERS",           "ASSET",     "H"),
            # Classe I — Liquidità
            AccountTemplate("I1",  "Depositi bancari e postali",       "FINANCIER",       "ASSET",     "I", is_reconcilable=True),
            AccountTemplate("I3",  "Cassa",                            "FINANCIER",       "ASSET",     "I"),
            # Classe L — Debiti a breve termine
            AccountTemplate("L1",  "Obbligazioni in scadenza",         "TIERS",           "LIABILITY", "L"),
            AccountTemplate("L2",  "Debiti verso banche (entro 12m)",  "TIERS",           "LIABILITY", "L"),
            AccountTemplate("L4",  "Debiti verso fornitori",           "TIERS",           "LIABILITY", "L", is_reconcilable=True),
            AccountTemplate("L8",  "Debiti tributari",                 "TIERS",           "LIABILITY", "L"),
            AccountTemplate("L9",  "IVA a debito",                     "TIERS",           "LIABILITY", "L", vat_code="IVA_22"),
            AccountTemplate("L10", "Debiti verso istituti previdenziali","TIERS",         "LIABILITY", "L"),
            AccountTemplate("L11", "Debiti verso dipendenti",          "TIERS",           "LIABILITY", "L"),
            # Classe M — Ratei e risconti passivi
            AccountTemplate("M1",  "Ratei passivi",                    "TIERS",           "LIABILITY", "M"),
            AccountTemplate("M2",  "Risconti passivi",                 "TIERS",           "LIABILITY", "M"),
            # Costi (Conti economici)
            AccountTemplate("60",  "Acquisti di materie prime",        "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("61",  "Acquisti di merci",                "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("62",  "Servizi",                          "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("63",  "Godimento beni di terzi",          "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("64",  "Personale",                        "CHARGES",         "EXPENSE",   "6", is_detail=False),
            AccountTemplate("641", "Salari e stipendi",                "CHARGES",         "EXPENSE",   "6", parent_code="64"),
            AccountTemplate("642", "Oneri sociali",                    "CHARGES",         "EXPENSE",   "6", parent_code="64"),
            AccountTemplate("643", "TFR",                              "CHARGES",         "EXPENSE",   "6", parent_code="64"),
            AccountTemplate("65",  "Ammortamenti e svalutazioni",      "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("66",  "Variazione delle rimanenze",       "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("67",  "Oneri diversi di gestione",        "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("68",  "Oneri finanziari",                 "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("69",  "Imposte sul reddito",              "CHARGES",         "EXPENSE",   "6"),
            # Ricavi
            AccountTemplate("70",  "Ricavi delle vendite",             "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("71",  "Ricavi per prestazioni di servizi","PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("72",  "Variazione delle rimanenze (prod.)","PRODUITS",       "REVENUE",   "7"),
            AccountTemplate("74",  "Proventi diversi",                 "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("75",  "Proventi finanziari",              "PRODUITS",        "REVENUE",   "7"),
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """Codice Civile art. 2424 — Stato Patrimoniale (Attivo / Passivo)."""
        attivo = FinancialStatement(code="IT_SP_ATTIVO", name="Stato Patrimoniale — Attivo (OIC)", standard="IT_OIC", lines=[
            FinancialStatementLine("AI",   "Immobilizzazioni immateriali",       ["D"],               indent_level=1),
            FinancialStatementLine("AII",  "Immobilizzazioni materiali",         ["E"],               indent_level=1),
            FinancialStatementLine("AIII", "Immobilizzazioni finanziarie",       ["F"],               indent_level=1),
            FinancialStatementLine("A0",   "IMMOBILIZZAZIONI (B)",               ["D","E","F"],       is_subtotal=True),
            FinancialStatementLine("BI",   "Rimanenze",                          ["G"],               indent_level=1),
            FinancialStatementLine("BII",  "Crediti",                            ["H"],               indent_level=1),
            FinancialStatementLine("BIII", "Attività finanziarie",               ["I"],               indent_level=1),
            FinancialStatementLine("B0",   "ATTIVO CIRCOLANTE (C)",              ["G","H","I"],       is_subtotal=True),
            FinancialStatementLine("T",    "TOTALE ATTIVO",                      ["D","E","F","G","H","I"], is_total=True),
        ])
        passivo = FinancialStatement(code="IT_SP_PASSIVO", name="Stato Patrimoniale — Passivo (OIC)", standard="IT_OIC", lines=[
            FinancialStatementLine("A1p",  "Capitale e riserve",                 ["A"],               indent_level=1),
            FinancialStatementLine("A0p",  "PATRIMONIO NETTO (A)",               ["A"],               is_subtotal=True),
            FinancialStatementLine("B1p",  "Fondi per rischi e oneri",           ["B1"],              indent_level=1),
            FinancialStatementLine("B2p",  "Trattamento di fine rapporto",       ["B2"],              indent_level=1),
            FinancialStatementLine("B0p",  "FONDI E TFR (B)",                    ["B"],               is_subtotal=True),
            FinancialStatementLine("C0p",  "Debiti a lungo termine (D)",         ["C"],               is_subtotal=True),
            FinancialStatementLine("D1p",  "Debiti verso fornitori",             ["L4"],              indent_level=1),
            FinancialStatementLine("D2p",  "Debiti verso banche (breve)",        ["L2"],              indent_level=1),
            FinancialStatementLine("D3p",  "Debiti tributari e previdenziali",   ["L8","L9","L10"],   indent_level=1),
            FinancialStatementLine("D0p",  "DEBITI A BREVE TERMINE (D)",         ["L","M"],           is_subtotal=True),
            FinancialStatementLine("T",    "TOTALE PASSIVO",                     ["A","B","C","L","M"], is_total=True),
        ])
        return attivo, passivo

    def get_income_statement_structure(self) -> FinancialStatement:
        """Codice Civile art. 2425 — Conto Economico (scalare, per natura)."""
        return FinancialStatement(code="IT_CE", name="Conto Economico (OIC)", standard="IT_OIC", lines=[
            FinancialStatementLine("A1",   "Ricavi delle vendite",               ["70","71"],         indent_level=1),
            FinancialStatementLine("A2",   "Variazione delle rimanenze",         ["72"],              indent_level=1),
            FinancialStatementLine("A5",   "Altri ricavi",                       ["74"],              indent_level=1),
            FinancialStatementLine("A0",   "VALORE DELLA PRODUZIONE (A)",        ["7"],               is_subtotal=True),
            FinancialStatementLine("B1",   "Materie prime e merci",              ["60","61"],         indent_level=1, negate=True),
            FinancialStatementLine("B2",   "Servizi",                            ["62","63"],         indent_level=1, negate=True),
            FinancialStatementLine("B9",   "Personale",                          ["64"],              indent_level=1, negate=True),
            FinancialStatementLine("B10",  "Ammortamenti e svalutazioni",        ["65"],              indent_level=1, negate=True),
            FinancialStatementLine("B11",  "Variazione rimanenze (materie)",     ["66"],              indent_level=1, negate=True),
            FinancialStatementLine("B14",  "Oneri diversi di gestione",          ["67"],              indent_level=1, negate=True),
            FinancialStatementLine("B0",   "COSTI DELLA PRODUZIONE (B)",         ["6"],               is_subtotal=True),
            FinancialStatementLine("AB",   "RISULTATO OPERATIVO (A-B)",          ["7","6"],           is_subtotal=True),
            FinancialStatementLine("C1",   "Proventi finanziari",                ["75"],              indent_level=1),
            FinancialStatementLine("C2",   "Oneri finanziari",                   ["68"],              indent_level=1, negate=True),
            FinancialStatementLine("C0",   "PROVENTI / ONERI FINANZIARI (C)",    ["75","68"],         is_subtotal=True),
            FinancialStatementLine("EBT",  "RISULTATO PRIMA DELLE IMPOSTE",      ["7","6"],           is_subtotal=True),
            FinancialStatementLine("T22",  "Imposte sul reddito (IRES + IRAP)",  ["69"],              indent_level=1, negate=True),
            FinancialStatementLine("RN",   "RISULTATO D'ESERCIZIO",              ["7","6"],           is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {
            "IVA_22": {"rate": "22.00", "label": "IVA aliquota ordinaria 22%",  "account_collectee": "L9"},
            "IVA_10": {"rate": "10.00", "label": "IVA aliquota ridotta 10%",    "account_collectee": "L9"},
            "IVA_05": {"rate": "5.00",  "label": "IVA aliquota ridotta 5%",     "account_collectee": "L9"},
            "IVA_04": {"rate": "4.00",  "label": "IVA aliquota super ridotta 4%","account_collectee": "L9"},
            "IVA_00": {"rate": "0.00",  "label": "IVA esente / fuori campo",    "account_collectee": None},
        }


StandardRegistry.register(ItalianOICStandard())
