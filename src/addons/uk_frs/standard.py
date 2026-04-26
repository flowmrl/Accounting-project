"""UK FRS 102 — Financial Reporting Standard applicable in the UK and Republic of Ireland."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountTemplate,
    AccountingStandard,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class UKFRS102Standard(AccountingStandard):
    """
    UK FRS 102 — issued by the Financial Reporting Council (FRC).
    Applicable to non-publicly accountable entities in the UK and Ireland.
    Based on IFRS for SMEs with UK-specific modifications.
    """

    @property
    def code(self) -> str:
        return "UK_FRS102"

    @property
    def name(self) -> str:
        return "UK FRS 102 — Financial Reporting Standard (FRC)"

    @property
    def country_codes(self) -> list[str]:
        return ["GB", "IE"]

    @property
    def currency_default(self) -> str:
        return "GBP"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Standard UK nominal ledger codes (based on common practice / Sage / Xero mapping)."""
        return [
            # Fixed Assets
            AccountTemplate("010", "Freehold Property",             "IMMOBILISATIONS", "ASSET",     "0", is_detail=False),
            AccountTemplate("011", "Leasehold Property",            "IMMOBILISATIONS", "ASSET",     "0", parent_code="010"),
            AccountTemplate("020", "Plant and Machinery",           "IMMOBILISATIONS", "ASSET",     "0"),
            AccountTemplate("021", "Motor Vehicles",                "IMMOBILISATIONS", "ASSET",     "0"),
            AccountTemplate("030", "Office Equipment",              "IMMOBILISATIONS", "ASSET",     "0"),
            AccountTemplate("040", "Goodwill",                      "IMMOBILISATIONS", "ASSET",     "0"),
            AccountTemplate("050", "Other Intangible Assets",       "IMMOBILISATIONS", "ASSET",     "0"),
            AccountTemplate("080", "Accumulated Depreciation",      "IMMOBILISATIONS", "CONTRA_ASSET","0"),
            # Current Assets
            AccountTemplate("100", "Stock",                         "STOCKS",          "ASSET",     "1"),
            AccountTemplate("101", "Work in Progress",              "STOCKS",          "ASSET",     "1"),
            AccountTemplate("110", "Debtors",                       "TIERS",           "ASSET",     "1", is_reconcilable=True),
            AccountTemplate("111", "Trade Debtors",                 "TIERS",           "ASSET",     "1", parent_code="110", is_reconcilable=True),
            AccountTemplate("120", "Prepayments",                   "TIERS",           "ASSET",     "1"),
            AccountTemplate("130", "VAT Reclaim",                   "TIERS",           "ASSET",     "1"),
            AccountTemplate("140", "Bank Current Account",          "FINANCIER",       "ASSET",     "1", is_reconcilable=True),
            AccountTemplate("141", "Bank Savings Account",          "FINANCIER",       "ASSET",     "1"),
            AccountTemplate("150", "Cash in Hand",                  "FINANCIER",       "ASSET",     "1"),
            # Liabilities
            AccountTemplate("200", "Trade Creditors",               "TIERS",           "LIABILITY", "2", is_reconcilable=True),
            AccountTemplate("210", "Accruals",                      "TIERS",           "LIABILITY", "2"),
            AccountTemplate("220", "VAT Liability",                 "TIERS",           "LIABILITY", "2", vat_code="VAT_20"),
            AccountTemplate("230", "PAYE / NIC Liability",          "TIERS",           "LIABILITY", "2"),
            AccountTemplate("240", "Corporation Tax Payable",       "TIERS",           "LIABILITY", "2"),
            AccountTemplate("250", "Directors' Loan Account",       "TIERS",           "LIABILITY", "2"),
            AccountTemplate("260", "Deferred Income",               "TIERS",           "LIABILITY", "2"),
            AccountTemplate("300", "Bank Loans",                    "CAPITAUX",        "LIABILITY", "3"),
            AccountTemplate("310", "Hire Purchase Liabilities",     "CAPITAUX",        "LIABILITY", "3"),
            AccountTemplate("320", "Provisions",                    "CAPITAUX",        "LIABILITY", "3"),
            # Equity
            AccountTemplate("400", "Share Capital",                 "CAPITAUX",        "EQUITY",    "4"),
            AccountTemplate("410", "Share Premium",                 "CAPITAUX",        "EQUITY",    "4"),
            AccountTemplate("420", "Retained Earnings",             "CAPITAUX",        "EQUITY",    "4"),
            AccountTemplate("430", "Profit / Loss for the Year",    "CAPITAUX",        "EQUITY",    "4"),
            # Revenue
            AccountTemplate("500", "Sales — Goods",                 "PRODUITS",        "REVENUE",   "5"),
            AccountTemplate("501", "Sales — Services",              "PRODUITS",        "REVENUE",   "5"),
            AccountTemplate("510", "Other Income",                  "PRODUITS",        "REVENUE",   "5"),
            AccountTemplate("520", "Interest Received",             "PRODUITS",        "REVENUE",   "5"),
            # Direct Costs
            AccountTemplate("600", "Cost of Goods Sold",            "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("601", "Purchases",                     "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("610", "Direct Labour",                 "CHARGES",         "EXPENSE",   "6"),
            # Overheads
            AccountTemplate("700", "Wages and Salaries",            "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("701", "Employer NIC",                  "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("702", "Pension Contributions",         "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("710", "Rent and Rates",                "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("720", "Utilities",                     "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("730", "Telephone and Internet",        "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("740", "Motor Expenses",                "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("750", "Travel and Subsistence",        "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("760", "Advertising and Marketing",     "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("770", "Professional Fees",             "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("780", "Depreciation",                  "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("790", "Interest Expense",              "CHARGES",         "EXPENSE",   "7"),
            AccountTemplate("800", "Corporation Tax",               "CHARGES",         "EXPENSE",   "8"),
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """FRS 102 s.4 — Statement of Financial Position."""
        assets = FinancialStatement(code="UK_BS_ASSETS", name="Balance Sheet — Assets (FRS 102)", standard="UK_FRS102", lines=[
            FinancialStatementLine("FA1",  "Tangible fixed assets",              ["010","020","021","030","080"], indent_level=1),
            FinancialStatementLine("FA2",  "Intangible fixed assets",            ["040","050"],       indent_level=1),
            FinancialStatementLine("FA0",  "FIXED ASSETS",                       ["0"],               is_subtotal=True),
            FinancialStatementLine("CA1",  "Stock and work in progress",         ["100","101"],       indent_level=1),
            FinancialStatementLine("CA2",  "Debtors (due within one year)",      ["110","120","130"], indent_level=1),
            FinancialStatementLine("CA3",  "Cash at bank and in hand",           ["140","141","150"], indent_level=1),
            FinancialStatementLine("CA0",  "CURRENT ASSETS",                     ["1"],               is_subtotal=True),
            FinancialStatementLine("TA",   "TOTAL ASSETS",                       ["0","1"],           is_total=True),
        ])
        equity_liab = FinancialStatement(code="UK_BS_EL", name="Balance Sheet — Equity & Liabilities (FRS 102)", standard="UK_FRS102", lines=[
            FinancialStatementLine("E1",   "Share capital and premium",          ["400","410"],       indent_level=1),
            FinancialStatementLine("E2",   "Retained earnings",                  ["420","430"],       indent_level=1),
            FinancialStatementLine("E0",   "SHAREHOLDERS' FUNDS",                ["4"],               is_subtotal=True),
            FinancialStatementLine("CL1",  "Trade creditors",                    ["200"],             indent_level=1),
            FinancialStatementLine("CL2",  "Accruals and deferred income",       ["210","260"],       indent_level=1),
            FinancialStatementLine("CL3",  "Taxation and social security",       ["220","230","240"], indent_level=1),
            FinancialStatementLine("CL4",  "Directors' loan account",            ["250"],             indent_level=1),
            FinancialStatementLine("CL0",  "CREDITORS: DUE WITHIN ONE YEAR",    ["2"],               is_subtotal=True),
            FinancialStatementLine("LT1",  "Bank loans",                         ["300","310"],       indent_level=1),
            FinancialStatementLine("LT2",  "Provisions for liabilities",         ["320"],             indent_level=1),
            FinancialStatementLine("LT0",  "CREDITORS: DUE AFTER ONE YEAR",     ["3"],               is_subtotal=True),
            FinancialStatementLine("T0",   "TOTAL EQUITY AND LIABILITIES",       ["2","3","4"],       is_total=True),
        ])
        return assets, equity_liab

    def get_income_statement_structure(self) -> FinancialStatement:
        """FRS 102 s.5 — Statement of Comprehensive Income."""
        return FinancialStatement(code="UK_PL", name="Profit and Loss Account (FRS 102)", standard="UK_FRS102", lines=[
            FinancialStatementLine("PL1",  "Turnover",                           ["500","501","510"], indent_level=1),
            FinancialStatementLine("PL2",  "Cost of sales",                      ["600","601","610"], indent_level=1, negate=True),
            FinancialStatementLine("PL3",  "GROSS PROFIT",                       ["5","6"],           is_subtotal=True),
            FinancialStatementLine("PL4",  "Administrative expenses",            ["700","701","702","710","720","730"], indent_level=1, negate=True),
            FinancialStatementLine("PL5",  "Selling and distribution costs",     ["740","750","760"], indent_level=1, negate=True),
            FinancialStatementLine("PL6",  "Depreciation and amortisation",      ["780"],             indent_level=1, negate=True),
            FinancialStatementLine("PL7",  "OPERATING PROFIT",                   ["5","6","7"],       is_subtotal=True),
            FinancialStatementLine("PL8",  "Interest receivable",                ["520"],             indent_level=1),
            FinancialStatementLine("PL9",  "Interest payable",                   ["790"],             indent_level=1, negate=True),
            FinancialStatementLine("PL10", "PROFIT BEFORE TAXATION",             ["5","6","7","52","79"], is_subtotal=True),
            FinancialStatementLine("PL11", "Corporation tax",                    ["800"],             indent_level=1, negate=True),
            FinancialStatementLine("PL12", "PROFIT FOR THE YEAR",                ["5","6","7","8"],   is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {
            "VAT_20":  {"rate": "20.00", "label": "UK VAT standard rate 20%",  "account_collectee": "220"},
            "VAT_05":  {"rate": "5.00",  "label": "UK VAT reduced rate 5%",    "account_collectee": "220"},
            "VAT_00":  {"rate": "0.00",  "label": "UK VAT zero rate",          "account_collectee": None},
            "VAT_EX":  {"rate": "0.00",  "label": "UK VAT exempt",             "account_collectee": None},
        }


StandardRegistry.register(UKFRS102Standard())
