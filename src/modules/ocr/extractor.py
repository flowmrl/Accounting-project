"""OCR — extraction de données factures (stub simulé)."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal


def extract_invoice_data(file_bytes: bytes, filename: str = "") -> dict:
    """
    Simule l'extraction OCR d'une facture.
    En production : appel Mindee / Tesseract / AWS Textract.
    Retourne un dict normalisé avec les champs clés de la facture.
    """
    return {
        "status": "simulated",
        "filename": filename,
        "supplier": {
            "name": "Fournisseur Example SAS",
            "siren": "123456789",
            "address": "1 rue de la Paix, 75001 Paris",
        },
        "invoice_number": "FAC-2026-0001",
        "invoice_date": str(date.today()),
        "due_date": str(date.today() + timedelta(days=30)),
        "lines": [
            {
                "description": "Prestation de service",
                "quantity": 1,
                "unit_price": 1000.00,
                "vat_rate": 0.20,
                "total_ht": 1000.00,
                "total_ttc": 1200.00,
            }
        ],
        "total_ht": Decimal("1000.00"),
        "total_tva": Decimal("200.00"),
        "total_ttc": Decimal("1200.00"),
        "currency": "EUR",
        "confidence": 0.0,
        "note": "Module OCR en cours d'intégration. Données simulées.",
    }
