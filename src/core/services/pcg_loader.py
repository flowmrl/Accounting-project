"""Charge le PCG France en base de données pour une société donnée."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from ..models.account import Account
from ..standards.pcg_france import PCGFrance

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class PCGLoader:
    """
    Installe le Plan Comptable Général pour une société.
    Idempotent : ne crée pas de doublons si appelé plusieurs fois.
    """

    _standard = PCGFrance()

    @classmethod
    def load_for_company(cls, company_id: str, session: "Session") -> int:
        """
        Crée tous les comptes PCG pour `company_id`.
        Retourne le nombre de comptes créés (0 si déjà chargés).
        """
        existing = {
            row.code
            for row in session.query(Account.code)
            .filter(Account.company_id == company_id, Account.standard == "PCG")
            .all()
        }

        templates = cls._standard.get_chart_of_accounts()
        code_to_id: dict[str, str] = {}

        # Pass 1 : résoudre les IDs existants
        for row in session.query(Account.code, Account.id).filter(
            Account.company_id == company_id, Account.standard == "PCG"
        ).all():
            code_to_id[row.code] = row.id

        created = 0
        # Pass 2 : créer dans l'ordre (parents avant enfants — JSON est déjà ordonné)
        for t in templates:
            if t.code in existing:
                continue

            account_id = str(uuid.uuid4())
            parent_id = code_to_id.get(t.parent_code) if t.parent_code else None

            account = Account(
                id=account_id,
                company_id=company_id,
                parent_id=parent_id,
                code=t.code,
                name=t.name,
                account_type=t.account_type,
                account_nature=t.account_nature,
                account_class=t.account_class,
                standard="PCG",
                is_detail=t.is_detail,
                is_reconcilable=getattr(t, "is_reconcilable", False),
                vat_code=t.vat_code,
            )
            session.add(account)
            code_to_id[t.code] = account_id
            created += 1

        if created:
            session.flush()

        return created
