"""Générateur XML Factur-X — profil EN 16931 (COMFORT), norme CII D16B."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, indent, tostring


_NS = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
    "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

_PROFILE = "urn:factur-x.eu:1p0:en16931"
_CONTEXT = "urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:en16931"


def _el(parent: Element, tag: str, text: str | None = None, **attrib) -> Element:
    e = SubElement(parent, tag, attrib)
    if text is not None:
        e.text = text
    return e


def _fmt_date(d: date) -> str:
    return d.strftime("%Y%m%d")


def _amt(v: Decimal, currency: str = "EUR") -> dict:
    return {"currencyID": currency, "text": f"{v:.2f}"}


def build_facturx_xml(
    *,
    invoice_number: str,
    issue_date: date,
    due_date: date | None,
    seller_name: str,
    seller_siret: str,
    seller_address: str,
    seller_city: str,
    seller_postal: str,
    seller_country: str = "FR",
    seller_tva_intracom: str | None = None,
    buyer_name: str,
    buyer_address: str | None,
    buyer_city: str | None,
    buyer_postal: str | None,
    buyer_country: str = "FR",
    buyer_siren: str | None = None,
    buyer_tva_intracom: str | None = None,
    lines: list[dict],
    currency: str = "EUR",
    notes: str | None = None,
    is_credit_note: bool = False,
) -> bytes:
    """Génère le XML Factur-X EN 16931 (CII) pour une facture ou un avoir."""

    # Totals
    subtotal_ht = sum(Decimal(str(ln["line_ht"])) for ln in lines)
    total_tva = sum(Decimal(str(ln["line_tva"])) for ln in lines)
    total_ttc = subtotal_ht + total_tva

    # Register namespaces
    for prefix, uri in _NS.items():
        try:
            import xml.etree.ElementTree as ET
            ET.register_namespace(prefix, uri)
        except Exception:
            pass

    root = Element(f'{{{_NS["rsm"]}}}CrossIndustryInvoice', {
        f'xmlns:{p}': u for p, u in _NS.items()
    })

    # --- ExchangedDocumentContext ---
    ctx = SubElement(root, f'{{{_NS["rsm"]}}}ExchangedDocumentContext')
    gpid = SubElement(ctx, f'{{{_NS["ram"]}}}GuidelineSpecifiedDocumentContextParameter')
    SubElement(gpid, f'{{{_NS["ram"]}}}ID').text = _CONTEXT

    # --- ExchangedDocument ---
    doc = SubElement(root, f'{{{_NS["rsm"]}}}ExchangedDocument')
    SubElement(doc, f'{{{_NS["ram"]}}}ID').text = invoice_number
    SubElement(doc, f'{{{_NS["ram"]}}}TypeCode').text = "381" if is_credit_note else "380"
    issued = SubElement(doc, f'{{{_NS["ram"]}}}IssueDateTime')
    dts = SubElement(issued, f'{{{_NS["udt"]}}}DateTimeString', {"format": "102"})
    dts.text = _fmt_date(issue_date)
    if notes:
        note_el = SubElement(doc, f'{{{_NS["ram"]}}}IncludedNote')
        SubElement(note_el, f'{{{_NS["ram"]}}}Content').text = notes

    # --- SupplyChainTradeTransaction ---
    tx = SubElement(root, f'{{{_NS["rsm"]}}}SupplyChainTradeTransaction')

    # Lines
    for i, ln in enumerate(lines, start=1):
        item = SubElement(tx, f'{{{_NS["ram"]}}}IncludedSupplyChainTradeLineItem')
        doc_el = SubElement(item, f'{{{_NS["ram"]}}}AssociatedDocumentLineDocument')
        SubElement(doc_el, f'{{{_NS["ram"]}}}LineID').text = str(i)
        prod = SubElement(item, f'{{{_NS["ram"]}}}SpecifiedTradeProduct')
        SubElement(prod, f'{{{_NS["ram"]}}}Name').text = ln["description"]
        trade_agrm = SubElement(item, f'{{{_NS["ram"]}}}SpecifiedLineTradeAgreement')
        net_price = SubElement(trade_agrm, f'{{{_NS["ram"]}}}NetPriceProductTradePrice')
        SubElement(net_price, f'{{{_NS["ram"]}}}ChargeAmount',
                   {"currencyID": currency}).text = f'{Decimal(str(ln["unit_price_ht"])):.4f}'
        trade_del = SubElement(item, f'{{{_NS["ram"]}}}SpecifiedLineTradeDelivery')
        billed_qty = SubElement(trade_del, f'{{{_NS["ram"]}}}BilledQuantity',
                                {"unitCode": ln.get("unit_code", "C62")})
        billed_qty.text = f'{Decimal(str(ln["quantity"])):.4f}'
        trade_sett = SubElement(item, f'{{{_NS["ram"]}}}SpecifiedLineTradeSettlement')
        tax_el = SubElement(trade_sett, f'{{{_NS["ram"]}}}ApplicableTradeTax')
        SubElement(tax_el, f'{{{_NS["ram"]}}}TypeCode').text = "VAT"
        SubElement(tax_el, f'{{{_NS["ram"]}}}CategoryCode').text = "S"
        SubElement(tax_el, f'{{{_NS["ram"]}}}RateApplicablePercent').text = f'{Decimal(str(ln["vat_rate"])):.2f}'
        line_sum = SubElement(trade_sett, f'{{{_NS["ram"]}}}SpecifiedTradeSettlementLineMonetarySummation')
        SubElement(line_sum, f'{{{_NS["ram"]}}}LineTotalAmount',
                   {"currencyID": currency}).text = f'{Decimal(str(ln["line_ht"])):.2f}'

    # Header trade agreement
    agrm = SubElement(tx, f'{{{_NS["ram"]}}}ApplicableHeaderTradeAgreement')

    # Seller
    seller = SubElement(agrm, f'{{{_NS["ram"]}}}SellerTradeParty')
    SubElement(seller, f'{{{_NS["ram"]}}}Name').text = seller_name
    if seller_tva_intracom:
        tax_reg = SubElement(seller, f'{{{_NS["ram"]}}}SpecifiedTaxRegistration')
        SubElement(tax_reg, f'{{{_NS["ram"]}}}ID', {"schemeID": "VA"}).text = seller_tva_intracom
    saddr = SubElement(seller, f'{{{_NS["ram"]}}}PostalTradeAddress')
    SubElement(saddr, f'{{{_NS["ram"]}}}PostcodeCode').text = seller_postal
    SubElement(saddr, f'{{{_NS["ram"]}}}LineOne').text = seller_address
    SubElement(saddr, f'{{{_NS["ram"]}}}CityName').text = seller_city
    SubElement(saddr, f'{{{_NS["ram"]}}}CountryID').text = seller_country
    s_siret = SubElement(seller, f'{{{_NS["ram"]}}}SpecifiedLegalOrganization')
    SubElement(s_siret, f'{{{_NS["ram"]}}}ID', {"schemeID": "0002"}).text = seller_siret

    # Buyer
    buyer = SubElement(agrm, f'{{{_NS["ram"]}}}BuyerTradeParty')
    SubElement(buyer, f'{{{_NS["ram"]}}}Name').text = buyer_name
    if buyer_tva_intracom:
        tax_reg = SubElement(buyer, f'{{{_NS["ram"]}}}SpecifiedTaxRegistration')
        SubElement(tax_reg, f'{{{_NS["ram"]}}}ID', {"schemeID": "VA"}).text = buyer_tva_intracom
    if buyer_siren:
        b_siret = SubElement(buyer, f'{{{_NS["ram"]}}}SpecifiedLegalOrganization')
        SubElement(b_siret, f'{{{_NS["ram"]}}}ID', {"schemeID": "0002"}).text = buyer_siren
    if buyer_address:
        baddr = SubElement(buyer, f'{{{_NS["ram"]}}}PostalTradeAddress')
        SubElement(baddr, f'{{{_NS["ram"]}}}PostcodeCode').text = buyer_postal or ""
        SubElement(baddr, f'{{{_NS["ram"]}}}LineOne').text = buyer_address
        SubElement(baddr, f'{{{_NS["ram"]}}}CityName').text = buyer_city or ""
        SubElement(baddr, f'{{{_NS["ram"]}}}CountryID').text = buyer_country

    # Delivery
    deliv = SubElement(tx, f'{{{_NS["ram"]}}}ApplicableHeaderTradeDelivery')
    SubElement(deliv, f'{{{_NS["ram"]}}}ShipToTradeParty')

    # Settlement
    sett = SubElement(tx, f'{{{_NS["ram"]}}}ApplicableHeaderTradeSettlement')
    SubElement(sett, f'{{{_NS["ram"]}}}InvoiceCurrencyCode').text = currency

    # VAT breakdown (grouped by rate)
    vat_groups: dict[str, Decimal] = {}
    for ln in lines:
        rate = str(ln["vat_rate"])
        vat_groups[rate] = vat_groups.get(rate, Decimal("0")) + Decimal(str(ln["line_tva"]))

    for rate_str, tva_amt in vat_groups.items():
        tax_el = SubElement(sett, f'{{{_NS["ram"]}}}ApplicableTradeTax')
        SubElement(tax_el, f'{{{_NS["ram"]}}}CalculatedAmount', {"currencyID": currency}).text = f"{tva_amt:.2f}"
        SubElement(tax_el, f'{{{_NS["ram"]}}}TypeCode').text = "VAT"
        base_for_rate = sum(
            Decimal(str(ln["line_ht"])) for ln in lines if str(ln["vat_rate"]) == rate_str
        )
        SubElement(tax_el, f'{{{_NS["ram"]}}}BasisAmount', {"currencyID": currency}).text = f"{base_for_rate:.2f}"
        SubElement(tax_el, f'{{{_NS["ram"]}}}CategoryCode').text = "S"
        SubElement(tax_el, f'{{{_NS["ram"]}}}RateApplicablePercent').text = f"{Decimal(rate_str):.2f}"

    # Payment terms
    if due_date:
        terms = SubElement(sett, f'{{{_NS["ram"]}}}SpecifiedTradePaymentTerms')
        due_el = SubElement(terms, f'{{{_NS["ram"]}}}DueDateDateTime')
        due_dts = SubElement(due_el, f'{{{_NS["udt"]}}}DateTimeString', {"format": "102"})
        due_dts.text = _fmt_date(due_date)

    # Monetary summary
    summ = SubElement(sett, f'{{{_NS["ram"]}}}SpecifiedTradeSettlementHeaderMonetarySummation')
    SubElement(summ, f'{{{_NS["ram"]}}}LineTotalAmount', {"currencyID": currency}).text = f"{subtotal_ht:.2f}"
    SubElement(summ, f'{{{_NS["ram"]}}}TaxBasisTotalAmount', {"currencyID": currency}).text = f"{subtotal_ht:.2f}"
    SubElement(summ, f'{{{_NS["ram"]}}}TaxTotalAmount', {"currencyID": currency}).text = f"{total_tva:.2f}"
    SubElement(summ, f'{{{_NS["ram"]}}}GrandTotalAmount', {"currencyID": currency}).text = f"{total_ttc:.2f}"
    SubElement(summ, f'{{{_NS["ram"]}}}DuePayableAmount', {"currencyID": currency}).text = f"{total_ttc:.2f}"

    indent(root, space="  ")
    xml_header = b'<?xml version="1.0" encoding="UTF-8"?>\n'
    return xml_header + tostring(root, encoding="unicode").encode("utf-8")
