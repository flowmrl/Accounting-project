"""Générateur XBRL pour dépôt des comptes au greffe du Tribunal de Commerce.

Format : XBRL (eXtensible Business Reporting Language) — taxonomie FR-GAAP
conforme au portail INPI / greffe électronique (e-liasse).

Référence : taxonomie XBRL France https://xbrl.ifrs.org / SBR France
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, indent, tostring


_NS = {
    "xbrli": "http://www.xbrl.org/2003/instance",
    "xbrldi": "http://xbrl.org/2006/xbrldi",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xlink": "http://www.w3.org/1999/xlink",
    "iso4217": "http://www.xbrl.org/2003/iso4217",
    "fr-gaap": "http://www.xbrl.fr/taxonomy/fr-gaap/2022",
}

_SCHEMA_REF = "http://www.xbrl.fr/taxonomy/fr-gaap/2022/fr-gaap.xsd"


def _tag(ns_prefix: str, local: str) -> str:
    return f"{{{_NS[ns_prefix]}}}{local}"


def _fmt(v: Decimal) -> str:
    return f"{v:.2f}"


def build_xbrl(
    *,
    company_name: str,
    siren: str,
    siret: str | None,
    fiscal_year_start: date,
    fiscal_year_end: date,
    currency: str = "EUR",
    balance_sheet: dict[str, Decimal],
    income_statement: dict[str, Decimal],
) -> bytes:
    """
    Génère le fichier XBRL instance document pour dépôt au greffe.

    balance_sheet: {compte_code: montant} — ex: {"actif_immobilise": 150000, ...}
    income_statement: {compte_code: montant} — ex: {"chiffre_affaires": 500000, ...}
    """
    for prefix, uri in _NS.items():
        try:
            import xml.etree.ElementTree as ET
            ET.register_namespace(prefix, uri)
        except Exception:
            pass

    root = Element(_tag("xbrli", "xbrl"), {
        f'xmlns:{p}': u for p, u in _NS.items()
    })

    # Schema reference
    schema_ref = SubElement(root, _tag("link", "schemaRef"), {
        f'{{{_NS["xlink"]}}}type': "simple",
        f'{{{_NS["xlink"]}}}href': _SCHEMA_REF,
    })

    # Context: entity + period
    ctx = SubElement(root, _tag("xbrli", "context"), {"id": "ctx_fy"})
    entity = SubElement(ctx, _tag("xbrli", "entity"))
    identifier = SubElement(entity, _tag("xbrli", "identifier"), {"scheme": "http://www.insee.fr/siren"})
    identifier.text = siren
    period = SubElement(ctx, _tag("xbrli", "period"))
    SubElement(period, _tag("xbrli", "startDate")).text = fiscal_year_start.isoformat()
    SubElement(period, _tag("xbrli", "endDate")).text = fiscal_year_end.isoformat()

    # Context instant (end of period) for balance sheet
    ctx_inst = SubElement(root, _tag("xbrli", "context"), {"id": "ctx_instant"})
    entity2 = SubElement(ctx_inst, _tag("xbrli", "entity"))
    id2 = SubElement(entity2, _tag("xbrli", "identifier"), {"scheme": "http://www.insee.fr/siren"})
    id2.text = siren
    period2 = SubElement(ctx_inst, _tag("xbrli", "period"))
    SubElement(period2, _tag("xbrli", "instant")).text = fiscal_year_end.isoformat()

    # Unit
    unit = SubElement(root, _tag("xbrli", "unit"), {"id": "EUR"})
    SubElement(unit, _tag("xbrli", "measure")).text = f'iso4217:{currency}'

    # Company metadata
    SubElement(root, _tag("fr-gaap", "DenominationSociale"), {
        "contextRef": "ctx_fy", "decimals": "2",
    }).text = company_name

    if siret:
        SubElement(root, _tag("fr-gaap", "SIRET"), {
            "contextRef": "ctx_fy",
        }).text = siret

    SubElement(root, _tag("fr-gaap", "DateOuvertureExercice"), {
        "contextRef": "ctx_fy",
    }).text = fiscal_year_start.isoformat()

    SubElement(root, _tag("fr-gaap", "DateClotureExercice"), {
        "contextRef": "ctx_fy",
    }).text = fiscal_year_end.isoformat()

    # Balance sheet items (instant context)
    _BS_MAPPING = {
        "actif_immobilise": "ActifImmobilise",
        "actif_circulant": "ActifCirculant",
        "tresorerie_actif": "TresorerieActif",
        "total_actif": "TotalActif",
        "capitaux_propres": "CapitauxPropres",
        "provisions": "Provisions",
        "dettes": "Dettes",
        "total_passif": "TotalPassif",
    }
    for key, xbrl_tag in _BS_MAPPING.items():
        if key in balance_sheet:
            SubElement(root, _tag("fr-gaap", xbrl_tag), {
                "contextRef": "ctx_instant",
                "unitRef": "EUR",
                "decimals": "2",
            }).text = _fmt(balance_sheet[key])

    # Income statement items (period context)
    _IS_MAPPING = {
        "chiffre_affaires": "ChiffreAffairesNet",
        "production_exercice": "ProductionExercice",
        "valeur_ajoutee": "ValeurAjoutee",
        "excedent_brut_exploitation": "ExcedentBrutExploitation",
        "resultat_exploitation": "ResultatExploitation",
        "resultat_financier": "ResultatFinancier",
        "resultat_courant": "ResultatCourantAvantImpots",
        "resultat_exceptionnel": "ResultatExceptionnel",
        "impots_benefices": "ImpotsBenefices",
        "resultat_net": "ResultatNet",
    }
    for key, xbrl_tag in _IS_MAPPING.items():
        if key in income_statement:
            SubElement(root, _tag("fr-gaap", xbrl_tag), {
                "contextRef": "ctx_fy",
                "unitRef": "EUR",
                "decimals": "2",
            }).text = _fmt(income_statement[key])

    indent(root, space="  ")
    header = b'<?xml version="1.0" encoding="UTF-8"?>\n'
    return header + tostring(root, encoding="unicode").encode("utf-8")
