"""Tests — Factur-X XML + PDF/A-3."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest


SELLER = dict(
    seller_name="Acme SAS",
    seller_siret="12345678901234",
    seller_address="12 rue de la Paix",
    seller_city="Paris",
    seller_postal="75001",
    seller_country="FR",
    seller_tva_intracom="FR12345678901",
)

BUYER = dict(
    buyer_name="Client SARL",
    buyer_address="5 avenue des Champs",
    buyer_city="Lyon",
    buyer_postal="69000",
    buyer_country="FR",
    buyer_siren="987654321",
    buyer_tva_intracom=None,
)

LINES = [
    {
        "description": "Prestation de conseil",
        "quantity": Decimal("10"),
        "unit_price_ht": Decimal("150.00"),
        "vat_rate": Decimal("20.00"),
        "line_ht": Decimal("1500.00"),
        "line_tva": Decimal("300.00"),
        "line_ttc": Decimal("1800.00"),
    },
    {
        "description": "Licence logiciel",
        "quantity": Decimal("1"),
        "unit_price_ht": Decimal("500.00"),
        "vat_rate": Decimal("20.00"),
        "line_ht": Decimal("500.00"),
        "line_tva": Decimal("100.00"),
        "line_ttc": Decimal("600.00"),
    },
]


# ---------------------------------------------------------------------------
# XML tests
# ---------------------------------------------------------------------------

def test_xml_basic_structure():
    from src.modules.facturation.facturx_xml import build_facturx_xml

    xml = build_facturx_xml(
        invoice_number="FAC-2026-001",
        issue_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        lines=LINES,
        **SELLER,
        **BUYER,
    )
    assert b"CrossIndustryInvoice" in xml
    assert b"FAC-2026-001" in xml
    assert b"Acme SAS" in xml
    assert b"Client SARL" in xml


def test_xml_invoice_typecode():
    from src.modules.facturation.facturx_xml import build_facturx_xml

    xml = build_facturx_xml(
        invoice_number="FAC-2026-001",
        issue_date=date(2026, 5, 1),
        due_date=None,
        lines=LINES,
        is_credit_note=False,
        **SELLER,
        **BUYER,
    )
    assert b"<ram:TypeCode>380</ram:TypeCode>" in xml


def test_xml_credit_note_typecode():
    from src.modules.facturation.facturx_xml import build_facturx_xml

    xml = build_facturx_xml(
        invoice_number="AV-2026-001",
        issue_date=date(2026, 5, 1),
        due_date=None,
        lines=LINES,
        is_credit_note=True,
        **SELLER,
        **BUYER,
    )
    assert b"<ram:TypeCode>381</ram:TypeCode>" in xml


def test_xml_totals():
    from src.modules.facturation.facturx_xml import build_facturx_xml

    xml = build_facturx_xml(
        invoice_number="FAC-001",
        issue_date=date(2026, 5, 1),
        due_date=None,
        lines=LINES,
        **SELLER,
        **BUYER,
    )
    # subtotal HT = 2000, TVA = 400, TTC = 2400
    assert b"2000.00" in xml
    assert b"400.00" in xml
    assert b"2400.00" in xml


def test_xml_contains_siret():
    from src.modules.facturation.facturx_xml import build_facturx_xml

    xml = build_facturx_xml(
        invoice_number="FAC-001",
        issue_date=date(2026, 5, 1),
        due_date=None,
        lines=LINES,
        **SELLER,
        **BUYER,
    )
    assert b"12345678901234" in xml


def test_xml_contains_tva_intracom():
    from src.modules.facturation.facturx_xml import build_facturx_xml

    xml = build_facturx_xml(
        invoice_number="FAC-001",
        issue_date=date(2026, 5, 1),
        due_date=None,
        lines=LINES,
        **SELLER,
        **BUYER,
    )
    assert b"FR12345678901" in xml


def test_xml_due_date():
    from src.modules.facturation.facturx_xml import build_facturx_xml

    xml = build_facturx_xml(
        invoice_number="FAC-001",
        issue_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        lines=LINES,
        **SELLER,
        **BUYER,
    )
    assert b"20260531" in xml


# ---------------------------------------------------------------------------
# PDF generation tests
# ---------------------------------------------------------------------------

def test_pdf_generated():
    from src.modules.facturation.facturx_pdf import _build_invoice_pdf

    pdf = _build_invoice_pdf(
        invoice_number="FAC-2026-001",
        issue_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        seller_name="Acme SAS",
        seller_address="12 rue de la Paix",
        seller_city="Paris",
        seller_postal="75001",
        seller_siret="12345678901234",
        seller_tva_intracom="FR12345678901",
        buyer_name="Client SARL",
        buyer_address="5 av. des Champs",
        buyer_city="Lyon",
        buyer_postal="69000",
        lines=LINES,
        currency="EUR",
        notes="Paiement par virement",
        subtotal_ht=Decimal("2000.00"),
        total_tva=Decimal("400.00"),
        total_ttc=Decimal("2400.00"),
    )
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_embed_xml_in_pdf():
    from src.modules.facturation.facturx_pdf import _build_invoice_pdf, embed_xml_in_pdf
    from src.modules.facturation.facturx_xml import build_facturx_xml

    xml = build_facturx_xml(
        invoice_number="FAC-001",
        issue_date=date(2026, 5, 1),
        due_date=None,
        lines=LINES,
        **SELLER,
        **BUYER,
    )
    pdf = _build_invoice_pdf(
        invoice_number="FAC-001",
        issue_date=date(2026, 5, 1),
        due_date=None,
        seller_name="Acme SAS",
        seller_address="12 rue de la Paix",
        seller_city="Paris",
        seller_postal="75001",
        seller_siret="12345678901234",
        seller_tva_intracom=None,
        buyer_name="Client SARL",
        buyer_address=None,
        buyer_city=None,
        buyer_postal=None,
        lines=LINES,
        currency="EUR",
        notes=None,
        subtotal_ht=Decimal("2000.00"),
        total_tva=Decimal("400.00"),
        total_ttc=Decimal("2400.00"),
    )
    result = embed_xml_in_pdf(pdf, xml, "FAC-001")
    assert result[:4] == b"%PDF"
    assert b"factur-x.xml" in result


def test_generate_facturx_full():
    from src.modules.facturation.facturx_pdf import generate_facturx

    pdf = generate_facturx(
        invoice_number="FAC-2026-001",
        issue_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        lines=LINES,
        **SELLER,
        **BUYER,
    )
    assert pdf[:4] == b"%PDF"
    assert b"factur-x.xml" in pdf
