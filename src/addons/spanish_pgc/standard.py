"""Spanish PGC — Plan General de Contabilidad (Real Decreto 1514/2007)."""
from __future__ import annotations

from typing import Any

from src.core.standards.base import (
    AccountingStandard,
    AccountTemplate,
    FinancialStatement,
    FinancialStatementLine,
    StandardRegistry,
)


class SpanishPGCStandard(AccountingStandard):
    """
    Plan General de Contabilidad español — RD 1514/2007 (ICAC).
    Structure en 9 groupes (grupos), similar au PCG français.
    PGC PYMES: RD 1515/2007 pour les petites entreprises.
    """

    @property
    def code(self) -> str:
        return "ES_PGC"

    @property
    def name(self) -> str:
        return "Spanish PGC — Plan General de Contabilidad (RD 1514/2007)"

    @property
    def country_codes(self) -> list[str]:
        return ["ES"]

    @property
    def currency_default(self) -> str:
        return "EUR"

    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Cuentas del PGC español — grupos 1-7 y 8-9 (operaciones de patrimonio neto)."""
        return [
            # Grupo 1 — Financiación básica
            AccountTemplate("10", "Capital",                        "CAPITAUX",        "EQUITY",    "1", is_detail=False),
            AccountTemplate("100","Capital social",                 "CAPITAUX",        "EQUITY",    "1", parent_code="10"),
            AccountTemplate("11", "Reservas y otros instrumentos", "CAPITAUX",        "EQUITY",    "1", is_detail=False),
            AccountTemplate("112","Reserva legal",                  "CAPITAUX",        "EQUITY",    "1", parent_code="11"),
            AccountTemplate("113","Reservas voluntarias",           "CAPITAUX",        "EQUITY",    "1", parent_code="11"),
            AccountTemplate("12", "Resultados pendientes de aplic.","CAPITAUX",        "EQUITY",    "1", is_detail=False),
            AccountTemplate("120","Remanente",                      "CAPITAUX",        "EQUITY",    "1", parent_code="12"),
            AccountTemplate("129","Resultado del ejercicio",        "CAPITAUX",        "EQUITY",    "1", parent_code="12"),
            AccountTemplate("14", "Provisiones",                    "CAPITAUX",        "LIABILITY", "1"),
            AccountTemplate("15", "Deudas a largo plazo (entid.)",  "CAPITAUX",        "LIABILITY", "1"),
            AccountTemplate("170","Deudas a LP con entid. crédito", "CAPITAUX",        "LIABILITY", "1", parent_code="15"),
            AccountTemplate("17", "Deudas a largo plazo",          "CAPITAUX",        "LIABILITY", "1"),
            # Grupo 2 — Activo no corriente
            AccountTemplate("20", "Inmovilizaciones intangibles",  "IMMOBILISATIONS", "ASSET",     "2", is_detail=False),
            AccountTemplate("200","Investigación",                  "IMMOBILISATIONS", "ASSET",     "2", parent_code="20"),
            AccountTemplate("201","Desarrollo",                     "IMMOBILISATIONS", "ASSET",     "2", parent_code="20"),
            AccountTemplate("202","Concesiones administrativas",    "IMMOBILISATIONS", "ASSET",     "2", parent_code="20"),
            AccountTemplate("203","Propiedad industrial",           "IMMOBILISATIONS", "ASSET",     "2", parent_code="20"),
            AccountTemplate("206","Aplicaciones informáticas",      "IMMOBILISATIONS", "ASSET",     "2", parent_code="20"),
            AccountTemplate("207","Fondo de comercio",              "IMMOBILISATIONS", "ASSET",     "2", parent_code="20"),
            AccountTemplate("21", "Inmovilizaciones materiales",   "IMMOBILISATIONS", "ASSET",     "2", is_detail=False),
            AccountTemplate("210","Terrenos y bienes naturales",    "IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("211","Construcciones",                 "IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("213","Maquinaria",                     "IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("216","Mobiliario",                     "IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("217","Equipos para procesos de info.", "IMMOBILISATIONS", "ASSET",     "2", parent_code="21"),
            AccountTemplate("22", "Inversiones inmobiliarias",     "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("23", "Inmovilizaciones en curso",     "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("24", "Inversiones financieras LP",    "IMMOBILISATIONS", "ASSET",     "2"),
            AccountTemplate("28", "Amortización acumulada",        "IMMOBILISATIONS", "CONTRA_ASSET","2"),
            AccountTemplate("29", "Deterioro de valor (activo nc.)","IMMOBILISATIONS","CONTRA_ASSET","2"),
            # Grupo 3 — Existencias
            AccountTemplate("30", "Comerciales",                   "STOCKS",          "ASSET",     "3"),
            AccountTemplate("31", "Materias primas",               "STOCKS",          "ASSET",     "3"),
            AccountTemplate("33", "Productos en curso",            "STOCKS",          "ASSET",     "3"),
            AccountTemplate("35", "Productos terminados",          "STOCKS",          "ASSET",     "3"),
            # Grupo 4 — Acreedores y deudores
            AccountTemplate("40", "Proveedores",                   "TIERS",           "LIABILITY", "4", is_reconcilable=True),
            AccountTemplate("400","Proveedores",                   "TIERS",           "LIABILITY", "4", parent_code="40", is_reconcilable=True),
            AccountTemplate("41", "Acreedores varios",             "TIERS",           "LIABILITY", "4"),
            AccountTemplate("43", "Clientes",                      "TIERS",           "ASSET",     "4", is_reconcilable=True),
            AccountTemplate("430","Clientes",                      "TIERS",           "ASSET",     "4", parent_code="43", is_reconcilable=True),
            AccountTemplate("44", "Deudores varios",               "TIERS",           "ASSET",     "4"),
            AccountTemplate("47", "Administraciones públicas",     "TIERS",           "LIABILITY", "4", is_detail=False),
            AccountTemplate("472","H.P. IVA soportado",            "TIERS",           "ASSET",     "4", parent_code="47"),
            AccountTemplate("477","H.P. IVA repercutido",          "TIERS",           "LIABILITY", "4", parent_code="47", vat_code="IVA_21"),
            AccountTemplate("473","H.P. retenciones y pagos a cuenta","TIERS",        "ASSET",     "4", parent_code="47"),
            AccountTemplate("475","H.P. acreedora por impuestos",  "TIERS",           "LIABILITY", "4", parent_code="47"),
            # Grupo 5 — Cuentas financieras
            AccountTemplate("52", "Deudas a CP con entid. crédito","TIERS",           "LIABILITY", "5"),
            AccountTemplate("57", "Tesorería",                     "FINANCIER",       "ASSET",     "5", is_detail=False),
            AccountTemplate("570","Caja, euros",                   "FINANCIER",       "ASSET",     "5", parent_code="57"),
            AccountTemplate("572","Bancos e inst. de crédito",     "FINANCIER",       "ASSET",     "5", parent_code="57", is_reconcilable=True),
            AccountTemplate("58", "Activos financieros a CP",      "FINANCIER",       "ASSET",     "5"),
            # Grupo 6 — Compras y gastos
            AccountTemplate("60", "Compras",                       "CHARGES",         "EXPENSE",   "6", is_detail=False),
            AccountTemplate("600","Compras de mercaderías",        "CHARGES",         "EXPENSE",   "6", parent_code="60"),
            AccountTemplate("601","Compras de materias primas",    "CHARGES",         "EXPENSE",   "6", parent_code="60"),
            AccountTemplate("62", "Servicios exteriores",          "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("63", "Tributos",                      "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("64", "Gastos de personal",            "CHARGES",         "EXPENSE",   "6", is_detail=False),
            AccountTemplate("640","Sueldos y salarios",            "CHARGES",         "EXPENSE",   "6", parent_code="64"),
            AccountTemplate("642","Seguridad Social a cargo empresa","CHARGES",        "EXPENSE",   "6", parent_code="64"),
            AccountTemplate("65", "Otros gastos de gestión",       "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("66", "Gastos financieros",            "CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("67", "Pérdidas procedentes de activos","CHARGES",        "EXPENSE",   "6"),
            AccountTemplate("68", "Dotaciones para amortizaciones","CHARGES",         "EXPENSE",   "6"),
            AccountTemplate("69", "Pérdidas por deterioro y otras","CHARGES",         "EXPENSE",   "6"),
            # Grupo 7 — Ventas e ingresos
            AccountTemplate("70", "Ventas de mercaderías",         "PRODUITS",        "REVENUE",   "7", is_detail=False),
            AccountTemplate("700","Ventas de mercaderías",         "PRODUITS",        "REVENUE",   "7", parent_code="70"),
            AccountTemplate("705","Prestaciones de servicios",     "PRODUITS",        "REVENUE",   "7", parent_code="70"),
            AccountTemplate("71", "Variación de existencias",      "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("73", "Trabajos realizados para la empresa","PRODUITS",   "REVENUE",   "7"),
            AccountTemplate("74", "Subvenciones",                  "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("75", "Otros ingresos de gestión",     "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("76", "Ingresos financieros",          "PRODUITS",        "REVENUE",   "7"),
            AccountTemplate("77", "Beneficios procedentes de activos","PRODUITS",     "REVENUE",   "7"),
        ]

    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """PGC — Balance de Situación (activo/pasivo y patrimonio neto)."""
        activo = FinancialStatement(code="ES_BALANCE_ACTIVO", name="Balance de Situación — Activo (PGC)", standard="ES_PGC", lines=[
            FinancialStatementLine("A1",  "Inmovilizado intangible",             ["20"],              indent_level=1),
            FinancialStatementLine("A2",  "Inmovilizado material",               ["21","22"],         indent_level=1),
            FinancialStatementLine("A3",  "Inmovilizado en curso",               ["23"],              indent_level=1),
            FinancialStatementLine("A4",  "Inversiones financieras a largo plazo",["24"],             indent_level=1),
            FinancialStatementLine("A5",  "Amortización acumulada",              ["28","29"],         indent_level=1, negate=True),
            FinancialStatementLine("A6",  "ACTIVO NO CORRIENTE",                 ["2"],               is_subtotal=True),
            FinancialStatementLine("A7",  "Existencias",                         ["3"],               indent_level=1),
            FinancialStatementLine("A8",  "Deudores comerciales",                ["43","44","47"],    indent_level=1),
            FinancialStatementLine("A9",  "Inversiones financieras a corto plazo",["58"],             indent_level=1),
            FinancialStatementLine("A10", "Tesorería",                           ["57"],              indent_level=1),
            FinancialStatementLine("A11", "ACTIVO CORRIENTE",                    ["3","4","5","58"],  is_subtotal=True),
            FinancialStatementLine("A0",  "TOTAL ACTIVO",                        ["2","3","4","5"],   is_total=True),
        ])
        pasivo = FinancialStatement(code="ES_BALANCE_PASIVO", name="Balance de Situación — Pasivo (PGC)", standard="ES_PGC", lines=[
            FinancialStatementLine("P1",  "Capital",                             ["10"],              indent_level=1),
            FinancialStatementLine("P2",  "Reservas",                            ["11"],              indent_level=1),
            FinancialStatementLine("P3",  "Resultado del ejercicio",             ["129"],             indent_level=1),
            FinancialStatementLine("P4",  "PATRIMONIO NETO",                     ["10","11","12"],    is_subtotal=True),
            FinancialStatementLine("P5",  "Provisiones a largo plazo",           ["14"],              indent_level=1),
            FinancialStatementLine("P6",  "Deudas a largo plazo",                ["15","17"],         indent_level=1),
            FinancialStatementLine("P7",  "PASIVO NO CORRIENTE",                 ["14","15","17"],    is_subtotal=True),
            FinancialStatementLine("P8",  "Deudas a corto plazo",                ["52"],              indent_level=1),
            FinancialStatementLine("P9",  "Acreedores comerciales",              ["40","41"],         indent_level=1),
            FinancialStatementLine("P10", "Administraciones públicas",            ["475","477"],       indent_level=1),
            FinancialStatementLine("P11", "PASIVO CORRIENTE",                    ["4","5","52"],      is_subtotal=True),
            FinancialStatementLine("P0",  "TOTAL PASIVO Y PATRIMONIO NETO",      ["1","2","3","4","5"], is_total=True),
        ])
        return activo, pasivo

    def get_income_statement_structure(self) -> FinancialStatement:
        """PGC — Cuenta de Pérdidas y Ganancias (por naturaleza)."""
        return FinancialStatement(code="ES_PYEG", name="Cuenta de Pérdidas y Ganancias (PGC)", standard="ES_PGC", lines=[
            FinancialStatementLine("R1",  "Importe neto de la cifra de negocios",["70","71"],         indent_level=1),
            FinancialStatementLine("R2",  "Variación de existencias",            ["71"],              indent_level=1),
            FinancialStatementLine("R3",  "Trabajos realizados por la empresa",  ["73"],              indent_level=1),
            FinancialStatementLine("R4",  "Subvenciones de explotación",         ["74"],              indent_level=1),
            FinancialStatementLine("R5",  "Otros ingresos de explotación",       ["75"],              indent_level=1),
            FinancialStatementLine("R6",  "INGRESOS DE EXPLOTACIÓN",             ["7"],               is_subtotal=True),
            FinancialStatementLine("R7",  "Aprovisionamientos",                  ["60"],              indent_level=1, negate=True),
            FinancialStatementLine("R8",  "Gastos de personal",                  ["64"],              indent_level=1, negate=True),
            FinancialStatementLine("R9",  "Otros gastos de explotación",         ["62","63","65"],    indent_level=1, negate=True),
            FinancialStatementLine("R10", "Amortización del inmovilizado",       ["68"],              indent_level=1, negate=True),
            FinancialStatementLine("R11", "Deterioros y resultados por enajenaciones",["67","69"],    indent_level=1, negate=True),
            FinancialStatementLine("R12", "RESULTADO DE EXPLOTACIÓN (EBIT)",    ["7","6"],           is_subtotal=True),
            FinancialStatementLine("R13", "Ingresos financieros",                ["76"],              indent_level=1),
            FinancialStatementLine("R14", "Gastos financieros",                  ["66"],              indent_level=1, negate=True),
            FinancialStatementLine("R15", "RESULTADO FINANCIERO",                ["76","66"],         is_subtotal=True),
            FinancialStatementLine("R16", "RESULTADO ANTES DE IMPUESTOS (EBT)", ["7","6"],           is_subtotal=True),
            FinancialStatementLine("R17", "Impuesto sobre beneficios",           ["63"],              indent_level=1, negate=True),
            FinancialStatementLine("R18", "RESULTADO DEL EJERCICIO",            ["7","6"],           is_total=True),
        ])

    def get_vat_codes(self) -> dict[str, Any]:
        return {
            "IVA_21": {"rate": "21.00", "label": "IVA tipo general 21%",        "account_collectee": "477"},
            "IVA_10": {"rate": "10.00", "label": "IVA tipo reducido 10%",       "account_collectee": "477"},
            "IVA_04": {"rate": "4.00",  "label": "IVA tipo superreducido 4%",   "account_collectee": "477"},
            "IVA_00": {"rate": "0.00",  "label": "IVA exento",                  "account_collectee": None},
        }


StandardRegistry.register(SpanishPGCStandard())
