"""US GAAP — Generally Accepted Accounting Principles (ASC — FASB)."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountingStandard,
    AccountTemplate,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class USGAAPStandard(AccountingStandard):

    @property
    def code(self) -> str:
        return "US_GAAP"

    @property
    def name(self) -> str:
        return "US Generally Accepted Accounting Principles (ASC / FASB)"

    @property
    def country_codes(self) -> list[str]:
        return ["US"]

    @property
    def currency_default(self) -> str:
        return "USD"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        return []

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """US GAAP — Classified Balance Sheet (current / non-current, decreasing liquidity)."""
        assets = FinancialStatement(code="USGAAP_BS_ASSETS", name="Balance Sheet — Assets", standard="US_GAAP", lines=[
            FinancialStatementLine("A1",  "Cash and cash equivalents (ASC 305)",         ["51","53"],          indent_level=1),
            FinancialStatementLine("A2",  "Marketable securities — current (ASC 320)",   ["50"],               indent_level=1),
            FinancialStatementLine("A3",  "Accounts receivable, net (ASC 310)",          ["411","416"],        indent_level=1),
            FinancialStatementLine("A4",  "Inventories (ASC 330)",                       ["3","39"],           indent_level=1),
            FinancialStatementLine("A5",  "Prepaid expenses and other current assets",   ["486","409"],        indent_level=1),
            FinancialStatementLine("A6",  "TOTAL CURRENT ASSETS",                        ["3","4","5","486"],  is_subtotal=True),
            FinancialStatementLine("A7",  "Property, plant and equipment, net (ASC 360)",["21","281"],         indent_level=1),
            FinancialStatementLine("A8",  "Operating lease right-of-use assets (ASC 842)",["218"],             indent_level=1),
            FinancialStatementLine("A9",  "Goodwill (ASC 350)",                          ["207"],              indent_level=1),
            FinancialStatementLine("A10", "Intangible assets, net (ASC 350)",            ["20","280"],         indent_level=1),
            FinancialStatementLine("A11", "Long-term investments (ASC 323)",             ["26","27"],          indent_level=1),
            FinancialStatementLine("A12", "TOTAL NON-CURRENT ASSETS",                   ["2","28","29"],      is_subtotal=True),
            FinancialStatementLine("A0",  "TOTAL ASSETS",                                ["2","3","4","5","28","29","39","49","59","486"], is_total=True),
        ])

        liabilities = FinancialStatement(code="USGAAP_BS_LEQ", name="Balance Sheet — Liabilities & Equity", standard="US_GAAP", lines=[
            FinancialStatementLine("L1",  "Accounts payable (ASC 405)",                  ["401","402","404"],  indent_level=1),
            FinancialStatementLine("L2",  "Accrued liabilities",                         ["428","438","448"],  indent_level=1),
            FinancialStatementLine("L3",  "Current portion of long-term debt",           ["519","164"],        indent_level=1),
            FinancialStatementLine("L4",  "Income taxes payable",                        ["444"],              indent_level=1),
            FinancialStatementLine("L5",  "Deferred revenue",                            ["487","4191"],       indent_level=1),
            FinancialStatementLine("L6",  "TOTAL CURRENT LIABILITIES",                  ["40","42","43","44","487","519"], is_subtotal=True),
            FinancialStatementLine("L7",  "Long-term debt (ASC 470)",                    ["161","162","163"],  indent_level=1),
            FinancialStatementLine("L8",  "Operating lease liabilities — non-current",   ["167"],              indent_level=1),
            FinancialStatementLine("L9",  "Deferred tax liabilities (ASC 740)",          [""],                 indent_level=1),
            FinancialStatementLine("L10", "Other non-current liabilities",               ["15","168"],         indent_level=1),
            FinancialStatementLine("L11", "TOTAL NON-CURRENT LIABILITIES",              ["15","16"],          is_subtotal=True),
            FinancialStatementLine("E1",  "Common stock and additional paid-in capital", ["101","104"],        indent_level=1),
            FinancialStatementLine("E2",  "Retained earnings",                           ["106","110","119","12"], indent_level=1),
            FinancialStatementLine("E3",  "Accumulated other comprehensive income",      ["105","107"],        indent_level=1),
            FinancialStatementLine("E0",  "TOTAL STOCKHOLDERS' EQUITY",                 ["10","11","12","13","14"], is_subtotal=True),
            FinancialStatementLine("T0",  "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", ["1","15","16","40","42","43","44","45","46","47","487","519"], is_total=True),
        ])
        return assets, liabilities

    def get_income_statement_structure(self) -> FinancialStatement:
        """US GAAP — Income Statement (single-step or multi-step)."""
        return FinancialStatement(code="USGAAP_IS", name="Income Statement (US GAAP)", standard="US_GAAP", lines=[
            FinancialStatementLine("IS1",  "Net revenues (ASC 606)",                     ["70","71","72"],     indent_level=1),
            FinancialStatementLine("IS2",  "Cost of revenues",                           ["60","61"],          indent_level=1, negate=True),
            FinancialStatementLine("IS3",  "GROSS PROFIT",                               ["70","71","72","60","61"], is_subtotal=True),
            FinancialStatementLine("IS4",  "Research and development",                   ["617","203"],        indent_level=1, negate=True),
            FinancialStatementLine("IS5",  "Selling, general and administrative",        ["62","63","65"],     indent_level=1, negate=True),
            FinancialStatementLine("IS6",  "Depreciation and amortization",              ["681"],              indent_level=1, negate=True),
            FinancialStatementLine("IS7",  "OPERATING INCOME (EBIT)",                   ["7","6"],            is_subtotal=True),
            FinancialStatementLine("IS8",  "Interest income",                            ["76"],               indent_level=1),
            FinancialStatementLine("IS9",  "Interest expense",                           ["661"],              indent_level=1, negate=True),
            FinancialStatementLine("IS10", "Other non-operating income / (expense)",     ["767","666"],        indent_level=1),
            FinancialStatementLine("IS11", "INCOME BEFORE INCOME TAXES",                ["7","6","76","66"],  is_subtotal=True),
            FinancialStatementLine("IS12", "Income tax expense (ASC 740)",               ["695"],              indent_level=1, negate=True),
            FinancialStatementLine("IS13", "NET INCOME",                                 ["7","6","69"],       is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {}   # Pas de TVA aux États-Unis (Sales Tax par État, non centralisée)


StandardRegistry.register(USGAAPStandard())
