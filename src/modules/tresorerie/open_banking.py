"""Open Banking DSP2 — client Bridge/Powens (mock + adaptateur réel).

En production, remplacer bridge_api_call() par de vraies requêtes HTTPS
avec les credentials Bridge API (client_id/secret + user access token).
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from src.modules.tresorerie.models import BankAccount, BankTransaction, ReconciliationStatus


# ---------------------------------------------------------------------------
# Bridge API client abstraction
# ---------------------------------------------------------------------------

class BridgeAPIClient:
    """Adaptateur Bridge API (Powens). Utilise des données simulées si pas de clé."""

    BASE_URL = "https://api.bridgeapi.io/v2"

    def __init__(self, client_id: str = "", client_secret: str = "", access_token: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token

    @property
    def _is_configured(self) -> bool:
        return bool(self.client_id and self.access_token)

    def get_transactions(
        self,
        bank_account_id: str,
        since: date | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        if self._is_configured:
            return self._fetch_live(bank_account_id, since, limit)
        return self._mock_transactions(since, limit)

    def _fetch_live(self, bank_account_id: str, since: date | None, limit: int) -> list[dict]:
        try:
            import httpx
        except ImportError:
            return self._mock_transactions(since, limit)

        params: dict[str, Any] = {"limit": limit}
        if since:
            params["since"] = since.isoformat()

        resp = httpx.get(
            f"{self.BASE_URL}/accounts/{bank_account_id}/transactions",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Bridge-Version": "2021-06-01",
            },
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("resources", [])

    def _mock_transactions(self, since: date | None, limit: int) -> list[dict]:
        """Transactions simulées réalistes pour démo/dev."""
        today = date.today()
        start = since or (today - timedelta(days=30))
        transactions = []
        mock_data = [
            ("Virement client SARL Martin", Decimal("4800.00")),
            ("SEPA BNP PARIBAS PRELEVEMENT LOYER", Decimal("-2200.00")),
            ("CB TOTAL ENERGIE CARBURANT", Decimal("-185.50")),
            ("Virement client Dupont & Fils", Decimal("12600.00")),
            ("PRLV URSSAF COTISATIONS", Decimal("-3420.00")),
            ("VIR SALAIRE JEAN DUPONT", Decimal("-2800.00")),
            ("VIR SALAIRE MARIE MARTIN", Decimal("-3100.00")),
            ("CB AMAZON MARKETPLACE", Decimal("-248.90")),
            ("Virement client Achat SAS", Decimal("7200.00")),
            ("FRAIS TENUE COMPTE BNP", Decimal("-18.00")),
            ("CB MONOPRIX ALIMENTATION", Decimal("-124.30")),
            ("CB SNCF BILLET TRAIN", Decimal("-89.00")),
            ("Virement fournisseur IMPRIMANTE PRO", Decimal("-1450.00")),
            ("PRLV EDF ELECTRICITE", Decimal("-320.00")),
            ("Virement client Laser Tech", Decimal("5500.00")),
        ]
        delta = (today - start).days
        step = max(1, delta // len(mock_data))
        balance = Decimal("15000.00")
        for i, (label, amount) in enumerate(mock_data[:limit]):
            tx_date = start + timedelta(days=i * step)
            if tx_date > today:
                break
            balance += amount
            transactions.append({
                "id": str(uuid.uuid4()),
                "date": tx_date.isoformat(),
                "label": label,
                "amount": float(amount),
                "balance_after": float(balance),
                "currency_code": "EUR",
            })
        return transactions


# ---------------------------------------------------------------------------
# Import service
# ---------------------------------------------------------------------------

def import_transactions(
    bank_account_db_id: str,
    transactions: list[dict[str, Any]],
    db: Session,
) -> dict[str, int]:
    """
    Importe les transactions dans bank_transactions, déduplique par (date + label + amount).
    Retourne {imported, skipped}.
    """
    imported = skipped = 0
    for tx in transactions:
        tx_date = date.fromisoformat(str(tx["date"])[:10])
        amount = Decimal(str(tx["amount"]))
        label = str(tx.get("label", ""))[:500]

        existing = db.query(BankTransaction).filter(
            BankTransaction.bank_account_id == bank_account_db_id,
            BankTransaction.transaction_date == tx_date,
            BankTransaction.amount == amount,
            BankTransaction.label == label,
        ).first()

        if existing:
            skipped += 1
            continue

        bt = BankTransaction(
            id=str(uuid.uuid4()),
            bank_account_id=bank_account_db_id,
            transaction_date=tx_date,
            label=label,
            amount=amount,
            balance_after=Decimal(str(tx["balance_after"])) if tx.get("balance_after") else None,
            source="API",
            reconciliation_status=ReconciliationStatus.NON_RAPPROCHE,
        )
        db.add(bt)
        imported += 1

    if imported:
        db.commit()
    return {"imported": imported, "skipped": skipped}


def sync_bank_account(
    bank_account: BankAccount,
    db: Session,
    since: date | None = None,
    bridge_client: BridgeAPIClient | None = None,
) -> dict[str, int]:
    """Synchronise un compte bancaire via Open Banking."""
    client = bridge_client or BridgeAPIClient()
    transactions = client.get_transactions(
        bank_account_id=bank_account.id,
        since=since or (date.today() - timedelta(days=30)),
    )
    return import_transactions(bank_account.id, transactions, db)
