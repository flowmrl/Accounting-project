"""Génération PDF/A-3 avec XML Factur-X embarqué (pièce jointe conforme EN 16931)."""
from __future__ import annotations

import hashlib
import io
from datetime import date, datetime, timezone
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

W, H = A4
MARGIN = 20 * mm


def _fmt_decimal(v: Decimal) -> str:
    return f"{v:,.2f} €".replace(",", " ")


def _build_invoice_pdf(
    *,
    invoice_number: str,
    issue_date: date,
    due_date: date | None,
    seller_name: str,
    seller_address: str,
    seller_city: str,
    seller_postal: str,
    seller_siret: str,
    seller_tva_intracom: str | None,
    buyer_name: str,
    buyer_address: str | None,
    buyer_city: str | None,
    buyer_postal: str | None,
    lines: list[dict],
    currency: str,
    notes: str | None,
    subtotal_ht: Decimal,
    total_tva: Decimal,
    total_ttc: Decimal,
    is_credit_note: bool = False,
) -> bytes:
    """Génère le PDF de la facture (corps seulement, sans embedding XML)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    styles = getSampleStyleSheet()
    story = []

    title_text = "AVOIR" if is_credit_note else "FACTURE"
    story.append(Paragraph(f"<b>{title_text} N° {invoice_number}</b>", styles["Title"]))
    story.append(Spacer(1, 6 * mm))

    # Header: seller / buyer
    header_data = [
        [
            Paragraph(f"<b>{seller_name}</b><br/>{seller_address}<br/>{seller_postal} {seller_city}<br/>"
                      f"SIRET : {seller_siret}" +
                      (f"<br/>TVA intracommunautaire : {seller_tva_intracom}" if seller_tva_intracom else ""),
                      styles["Normal"]),
            Paragraph(
                f"<b>Client :</b> {buyer_name}" +
                (f"<br/>{buyer_address}" if buyer_address else "") +
                (f"<br/>{buyer_postal} {buyer_city}" if buyer_postal else ""),
                styles["Normal"],
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[(W - 2 * MARGIN) / 2, (W - 2 * MARGIN) / 2])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6 * mm))

    # Dates
    dates_txt = f"Date d'émission : {issue_date.strftime('%d/%m/%Y')}"
    if due_date:
        dates_txt += f"   —   Échéance : {due_date.strftime('%d/%m/%Y')}"
    story.append(Paragraph(dates_txt, styles["Normal"]))
    story.append(Spacer(1, 6 * mm))

    # Lines table
    col_w = [(W - 2 * MARGIN) * p for p in (0.40, 0.10, 0.15, 0.10, 0.12, 0.13)]
    lines_data = [["Description", "Qté", "P.U. HT", "TVA %", "HT", "TTC"]]
    for ln in lines:
        lines_data.append([
            ln["description"],
            f'{Decimal(str(ln["quantity"])):g}',
            _fmt_decimal(Decimal(str(ln["unit_price_ht"]))),
            f'{Decimal(str(ln["vat_rate"])):g} %',
            _fmt_decimal(Decimal(str(ln["line_ht"]))),
            _fmt_decimal(Decimal(str(ln["line_ttc"]))),
        ])

    lines_table = Table(lines_data, colWidths=col_w)
    lines_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(lines_table)
    story.append(Spacer(1, 4 * mm))

    # Totals
    total_data = [
        ["", "Sous-total HT :", _fmt_decimal(subtotal_ht)],
        ["", "TVA :", _fmt_decimal(total_tva)],
        ["", Paragraph("<b>Total TTC :</b>", styles["Normal"]),
         Paragraph(f"<b>{_fmt_decimal(total_ttc)}</b>", styles["Normal"])],
    ]
    total_col_w = [(W - 2 * MARGIN) * p for p in (0.55, 0.25, 0.20)]
    total_table = Table(total_data, colWidths=total_col_w)
    total_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEABOVE", (1, 2), (-1, 2), 1, colors.HexColor("#1a3c5e")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(total_table)

    if notes:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(f"<i>{notes}</i>", styles["Normal"]))

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "<font size=7 color='grey'>Document généré par Compta PME — "
        "conforme Factur-X EN 16931 (obligation légale sept. 2026)</font>",
        styles["Normal"],
    ))

    doc.build(story)
    return buf.getvalue()


def embed_xml_in_pdf(pdf_bytes: bytes, xml_bytes: bytes, invoice_number: str) -> bytes:
    """
    Embarque le XML Factur-X dans le PDF en tant que pièce jointe PDF/A-3.
    Utilise pypdf pour ajouter l'attachment au dictionnaire PDF.
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (
        ArrayObject,
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
        NumberObject,
        TextStringObject,
        create_string_object,
    )

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # Build embedded file stream
    xml_stream = DecodedStreamObject()
    xml_stream.set_data(xml_bytes)
    md5_hash = hashlib.md5(xml_bytes).hexdigest()
    now = datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%S+00'00'")

    xml_stream.update({
        NameObject("/Type"): NameObject("/EmbeddedFile"),
        NameObject("/Subtype"): NameObject("/text/xml"),
        NameObject("/Params"): DictionaryObject({
            NameObject("/Size"): NumberObject(len(xml_bytes)),
            NameObject("/CheckSum"): create_string_object(md5_hash),
            NameObject("/CreationDate"): create_string_object(now),
            NameObject("/ModDate"): create_string_object(now),
        }),
    })

    xml_stream_obj = writer._add_object(xml_stream)

    # Filespec dictionary
    filename = "factur-x.xml"
    filespec = DictionaryObject({
        NameObject("/Type"): NameObject("/Filespec"),
        NameObject("/F"): create_string_object(filename),
        NameObject("/UF"): create_string_object(filename),
        NameObject("/Desc"): TextStringObject("Factur-X XML EN 16931"),
        NameObject("/AFRelationship"): NameObject("/Data"),
        NameObject("/EF"): DictionaryObject({
            NameObject("/F"): xml_stream_obj,
            NameObject("/UF"): xml_stream_obj,
        }),
    })
    filespec_obj = writer._add_object(filespec)

    # Add to document catalog
    if "/Names" not in writer._root_object:
        writer._root_object[NameObject("/Names")] = DictionaryObject()
    names = writer._root_object["/Names"]
    if "/EmbeddedFiles" not in names:
        names[NameObject("/EmbeddedFiles")] = DictionaryObject()
    ef_names = names["/EmbeddedFiles"]
    if "/Names" not in ef_names:
        ef_names[NameObject("/Names")] = ArrayObject()
    ef_names["/Names"].extend([
        create_string_object(filename),
        filespec_obj,
    ])

    # AF array (PDF/A-3 associated files)
    writer._root_object[NameObject("/AF")] = ArrayObject([filespec_obj])

    # XMP metadata patch for PDF/A-3 + Factur-X
    xmp = (
        '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">'
        '<pdfaid:part>3</pdfaid:part><pdfaid:conformance>B</pdfaid:conformance>'
        '</rdf:Description>'
        '<rdf:Description rdf:about="" xmlns:fx="urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#">'
        f'<fx:DocumentFileName>{filename}</fx:DocumentFileName>'
        '<fx:DocumentType>INVOICE</fx:DocumentType>'
        '<fx:Version>1.0</fx:Version>'
        '<fx:ConformanceLevel>EN 16931</fx:ConformanceLevel>'
        '</rdf:Description>'
        '</rdf:RDF>'
        '</x:xmpmeta>'
        '<?xpacket end="w"?>'
    )
    xmp_stream = DecodedStreamObject()
    xmp_stream.set_data(xmp.encode("utf-8"))
    xmp_stream.update({
        NameObject("/Type"): NameObject("/Metadata"),
        NameObject("/Subtype"): NameObject("/XML"),
    })
    xmp_obj = writer._add_object(xmp_stream)
    writer._root_object[NameObject("/Metadata")] = xmp_obj

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def generate_facturx(
    *,
    invoice_number: str,
    issue_date: date,
    due_date: date | None,
    seller_name: str,
    seller_address: str,
    seller_city: str,
    seller_postal: str,
    seller_siret: str,
    seller_tva_intracom: str | None = None,
    seller_country: str = "FR",
    buyer_name: str,
    buyer_address: str | None = None,
    buyer_city: str | None = None,
    buyer_postal: str | None = None,
    buyer_country: str = "FR",
    buyer_siren: str | None = None,
    buyer_tva_intracom: str | None = None,
    lines: list[dict],
    currency: str = "EUR",
    notes: str | None = None,
    is_credit_note: bool = False,
) -> bytes:
    """Point d'entrée : retourne le PDF/A-3 avec XML Factur-X embarqué."""
    from src.modules.facturation.facturx_xml import build_facturx_xml

    subtotal_ht = sum(Decimal(str(ln["line_ht"])) for ln in lines)
    total_tva = sum(Decimal(str(ln["line_tva"])) for ln in lines)
    total_ttc = subtotal_ht + total_tva

    xml_bytes = build_facturx_xml(
        invoice_number=invoice_number,
        issue_date=issue_date,
        due_date=due_date,
        seller_name=seller_name,
        seller_siret=seller_siret,
        seller_address=seller_address,
        seller_city=seller_city,
        seller_postal=seller_postal,
        seller_country=seller_country,
        seller_tva_intracom=seller_tva_intracom,
        buyer_name=buyer_name,
        buyer_address=buyer_address,
        buyer_city=buyer_city,
        buyer_postal=buyer_postal,
        buyer_country=buyer_country,
        buyer_siren=buyer_siren,
        buyer_tva_intracom=buyer_tva_intracom,
        lines=lines,
        currency=currency,
        notes=notes,
        is_credit_note=is_credit_note,
    )

    pdf_bytes = _build_invoice_pdf(
        invoice_number=invoice_number,
        issue_date=issue_date,
        due_date=due_date,
        seller_name=seller_name,
        seller_address=seller_address,
        seller_city=seller_city,
        seller_postal=seller_postal,
        seller_siret=seller_siret,
        seller_tva_intracom=seller_tva_intracom,
        buyer_name=buyer_name,
        buyer_address=buyer_address,
        buyer_city=buyer_city,
        buyer_postal=buyer_postal,
        lines=lines,
        currency=currency,
        notes=notes,
        subtotal_ht=subtotal_ht,
        total_tva=total_tva,
        total_ttc=total_ttc,
        is_credit_note=is_credit_note,
    )

    return embed_xml_in_pdf(pdf_bytes, xml_bytes, invoice_number)
