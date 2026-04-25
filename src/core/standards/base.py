"""
Interface de base pour les référentiels comptables.

Chaque référentiel (PCG, IFRS, US GAAP, OHADA…) implémente
cette interface pour fournir :
  - le plan de comptes de référence
  - les règles de présentation du bilan et du compte de résultat
  - les spécificités de consolidation / retraitement
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class AccountTemplate:
    """Modèle de compte dans un référentiel."""
    code: str
    name: str
    account_type: str
    account_nature: str
    account_class: str
    parent_code: str | None = None
    is_detail: bool = True
    vat_code: str | None = None
    notes: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class FinancialStatementLine:
    """Ligne d'un état financier (bilan, CdR)."""
    code: str
    label: str
    account_codes: list[str]          # Codes des comptes inclus
    negate: bool = False               # Inverser le signe (dettes, provisions…)
    is_subtotal: bool = False
    is_total: bool = False
    indent_level: int = 0
    note_ref: str | None = None       # Renvoi aux notes annexes


@dataclass
class FinancialStatement:
    """Définition structurelle d'un état financier."""
    code: str               # Ex: "BILAN_ACTIF", "COMPTE_RESULTAT"
    name: str
    standard: str
    lines: list[FinancialStatementLine] = field(default_factory=list)


class AccountingStandard(ABC):
    """
    Interface abstraite d'un référentiel comptable.

    Implémenter cette classe pour ajouter le support d'un nouveau référentiel.
    """

    @property
    @abstractmethod
    def code(self) -> str:
        """Identifiant court du référentiel (ex: 'PCG', 'IFRS', 'US_GAAP')."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom complet du référentiel."""

    @property
    @abstractmethod
    def country_codes(self) -> list[str]:
        """Codes ISO des pays où ce référentiel est utilisé en priorité."""

    @property
    @abstractmethod
    def currency_default(self) -> str:
        """Devise par défaut (code ISO 4217)."""

    @abstractmethod
    def get_chart_of_accounts(self) -> list[AccountTemplate]:
        """Retourne le plan de comptes de référence du référentiel."""

    @abstractmethod
    def get_balance_sheet_structure(self) -> tuple[FinancialStatement, FinancialStatement]:
        """Retourne la structure du bilan (actif, passif)."""

    @abstractmethod
    def get_income_statement_structure(self) -> FinancialStatement:
        """Retourne la structure du compte de résultat."""

    def get_cash_flow_structure(self) -> FinancialStatement | None:
        """Retourne la structure du tableau de flux de trésorerie (optionnel)."""
        return None

    def get_notes_structure(self) -> list[FinancialStatement]:
        """Retourne la structure des notes annexes (optionnel)."""
        return []

    def validate_entry(self, entry_data: dict[str, Any]) -> list[str]:
        """
        Valide une écriture selon les règles du référentiel.
        Retourne une liste d'erreurs (vide si OK).
        """
        return []

    def get_vat_codes(self) -> dict[str, dict[str, Any]]:
        """Retourne les codes TVA applicables (si pertinent pour le référentiel)."""
        return {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} [{self.code}]>"


class StandardRegistry:
    """Registre global des référentiels comptables disponibles."""

    _standards: dict[str, AccountingStandard] = {}

    @classmethod
    def register(cls, standard: AccountingStandard) -> None:
        cls._standards[standard.code] = standard

    @classmethod
    def get(cls, code: str) -> AccountingStandard:
        if code not in cls._standards:
            raise ValueError(f"Référentiel '{code}' non trouvé. Disponibles: {list(cls._standards)}")
        return cls._standards[code]

    @classmethod
    def list_all(cls) -> list[dict[str, str]]:
        return [
            {"code": s.code, "name": s.name, "countries": ", ".join(s.country_codes)}
            for s in cls._standards.values()
        ]

    @classmethod
    def is_registered(cls, code: str) -> bool:
        return code in cls._standards
