"""
IFRS — International Financial Reporting Standards.

Mapping PCG → IFRS pour la transformation des états financiers.
Implémente get_balance_sheet_structure() selon IAS 1 (présentation par liquidité).
"""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountTemplate,
    AccountingStandard,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class IFRSStandard(AccountingStandard):
    """
    IFRS — référentiel international obligatoire pour les sociétés cotées
    et optionnel pour les groupes non cotés.
    """

    @property
    def code(self) -> str:
        return "IFRS"

    @property
    def name(self) -> str:
        return "International Financial Reporting Standards (IFRS)"

    @property
    def country_codes(self) -> list[str]:
        return ["EU", "GB", "AU", "CA", "BR", "ZA", "SG", "HK"]

    @property
    def currency_default(self) -> str:
        return "EUR"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Le PCG reste la base ; IFRS opère par retraitement sur les états."""
        return []

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """IAS 1 — présentation bilan par ordre de liquidité (format IFRS)."""
        actif = FinancialStatement(code="IFRS_BS_ASSET", name="Statement of Financial Position — Assets", standard="IFRS", lines=[
            # Actifs non courants
            FinancialStatementLine("NCA1", "Property, plant and equipment (IAS 16)",    ["21","281","291"],   indent_level=1),
            FinancialStatementLine("NCA2", "Investment property (IAS 40)",               ["211","212"],        indent_level=1),
            FinancialStatementLine("NCA3", "Intangible assets (IAS 38)",                 ["20","280","290"],   indent_level=1),
            FinancialStatementLine("NCA4", "Goodwill (IFRS 3)",                          ["207"],              indent_level=1),
            FinancialStatementLine("NCA5", "Financial assets — non-current (IFRS 9)",    ["26","27","296","297"], indent_level=1),
            FinancialStatementLine("NCA6", "Deferred tax assets (IAS 12)",               [""],                 indent_level=1),
            FinancialStatementLine("NCA0", "TOTAL NON-CURRENT ASSETS",                  ["2","28","29"],      is_subtotal=True),
            # Actifs courants
            FinancialStatementLine("CA1",  "Inventories (IAS 2)",                        ["3","39"],           indent_level=1),
            FinancialStatementLine("CA2",  "Trade and other receivables (IFRS 9)",       ["411","416","418","461"], indent_level=1),
            FinancialStatementLine("CA3",  "Cash and cash equivalents (IAS 7)",          ["51","53","50"],     indent_level=1),
            FinancialStatementLine("CA4",  "Other current assets",                       ["486","409"],        indent_level=1),
            FinancialStatementLine("CA0",  "TOTAL CURRENT ASSETS",                       ["3","4","5","486"],  is_subtotal=True),
            FinancialStatementLine("TA",   "TOTAL ASSETS",                               ["2","3","4","5","28","29","39","49","59","486"], is_total=True),
        ])

        passif = FinancialStatement(code="IFRS_BS_EQUITY", name="Statement of Financial Position — Equity & Liabilities", standard="IFRS", lines=[
            # Capitaux propres
            FinancialStatementLine("EQ1",  "Share capital",                              ["101","1013"],       indent_level=1),
            FinancialStatementLine("EQ2",  "Share premium",                              ["104"],              indent_level=1),
            FinancialStatementLine("EQ3",  "Retained earnings",                          ["106","110","119"],  indent_level=1),
            FinancialStatementLine("EQ4",  "Profit / (loss) for the year",               ["120","129"],        indent_level=1),
            FinancialStatementLine("EQ5",  "Other comprehensive income (OCI)",           ["105","107"],        indent_level=1),
            FinancialStatementLine("EQ0",  "TOTAL EQUITY",                               ["10","11","12","13","14"], is_subtotal=True),
            # Passifs non courants
            FinancialStatementLine("NCL1", "Borrowings — non-current (IFRS 9)",          ["161","162","163"],  indent_level=1),
            FinancialStatementLine("NCL2", "Provisions — non-current (IAS 37)",          ["15"],               indent_level=1),
            FinancialStatementLine("NCL3", "Deferred tax liabilities (IAS 12)",          [""],                 indent_level=1),
            FinancialStatementLine("NCL4", "Lease liabilities — non-current (IFRS 16)",  ["167"],              indent_level=1),
            FinancialStatementLine("NCL0", "TOTAL NON-CURRENT LIABILITIES",              ["15","16"],          is_subtotal=True),
            # Passifs courants
            FinancialStatementLine("CL1",  "Trade and other payables",                   ["401","402","404","408"], indent_level=1),
            FinancialStatementLine("CL2",  "Borrowings — current",                       ["519","164"],        indent_level=1),
            FinancialStatementLine("CL3",  "Current tax liabilities",                    ["444","695"],        indent_level=1),
            FinancialStatementLine("CL4",  "Other current liabilities",                  ["42","43","487"],    indent_level=1),
            FinancialStatementLine("CL0",  "TOTAL CURRENT LIABILITIES",                  ["40","42","43","44","45","46","487","519"], is_subtotal=True),
            FinancialStatementLine("TL",   "TOTAL EQUITY AND LIABILITIES",               ["1","15","16","40","42","43","44","45","46","47","487","519"], is_total=True),
        ])
        return actif, passif

    def get_income_statement_structure(self) -> FinancialStatement:
        """IAS 1 — Compte de résultat par nature (méthode la plus courante en France)."""
        return FinancialStatement(code="IFRS_PL", name="Statement of Profit or Loss (IFRS)", standard="IFRS", lines=[
            FinancialStatementLine("PL1",  "Revenue (IFRS 15)",                          ["70","71","72"],     indent_level=1),
            FinancialStatementLine("PL2",  "Other operating income",                     ["74","75","79"],     indent_level=1),
            FinancialStatementLine("PL3",  "Cost of sales",                              ["60","61"],          indent_level=1, negate=True),
            FinancialStatementLine("PL4",  "Employee benefits expense (IAS 19)",         ["64"],               indent_level=1, negate=True),
            FinancialStatementLine("PL5",  "Depreciation and amortisation",              ["681"],              indent_level=1, negate=True),
            FinancialStatementLine("PL6",  "Other operating expenses",                   ["62","63","65"],     indent_level=1, negate=True),
            FinancialStatementLine("PL7",  "OPERATING PROFIT (EBIT)",                   ["7","6"],            is_subtotal=True),
            FinancialStatementLine("PL8",  "Finance income",                             ["76"],               indent_level=1),
            FinancialStatementLine("PL9",  "Finance costs",                              ["66"],               indent_level=1, negate=True),
            FinancialStatementLine("PL10", "PROFIT BEFORE TAX (EBT)",                   ["7","6","76","66"],  is_subtotal=True),
            FinancialStatementLine("PL11", "Income tax expense (IAS 12)",                ["695"],              indent_level=1, negate=True),
            FinancialStatementLine("PL12", "PROFIT FOR THE YEAR",                        ["7","6","69"],       is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {}   # IFRS ne définit pas de codes TVA spécifiques


class IFRSRetraitement:
    """
    Retraitements courants PCG → IFRS.
    Chaque méthode retourne des ajustements à appliquer sur la balance.
    """

    @staticmethod
    def ifrs16_lease_restatement(lease_amount: float, rate: float, years: int) -> dict:
        """
        IFRS 16 — Capitalisation des contrats de location.
        Transforme les loyers (613x) en actif de droit d'utilisation + dette de loyer.
        """
        from decimal import Decimal
        import math
        pv = Decimal(str(lease_amount * (1 - (1 + rate) ** -years) / rate))
        return {
            "droit_utilisation": pv,           # Débit 213x ou 218x
            "dette_location": pv,              # Crédit 167x
            "retraitement": "IFRS 16 — Right-of-use asset",
        }

    @staticmethod
    def ias19_defined_benefit(obligation: float, plan_assets: float) -> dict:
        """IAS 19 — Engagement de retraite à prestations définies (DBO - Plan assets)."""
        from decimal import Decimal
        net_liability = Decimal(str(obligation - plan_assets))
        return {
            "provision_retraite": net_liability,   # Crédit 153x
            "retraitement": "IAS 19 — Defined benefit obligation",
        }

    @staticmethod
    def ias2_inventory_method_change(fifo_value: float, cmup_value: float) -> dict:
        """IAS 2 — Revalorisation des stocks (LIFO non autorisé en IFRS)."""
        from decimal import Decimal
        diff = Decimal(str(fifo_value - cmup_value))
        return {
            "ajustement_stocks": diff,
            "retraitement": "IAS 2 — FIFO vs CMUP adjustment",
        }


StandardRegistry.register(IFRSStandard())
