"""Paie — bulletins de salaire, moteur de calcul cotisations, DSN stub."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.db.session import get_session
from src.modules.paie.models import Bulletin, BulletinStatus, LigneBulletin

router = APIRouter(prefix="/payslips", tags=["Paie"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SimulerPaieRequest(BaseModel):
    salaire_brut: Decimal
    is_cadre: bool = False


class LigneCotisationOut(BaseModel):
    libelle: str
    base: Decimal
    taux_salarial: Decimal
    taux_patronal: Decimal
    montant_salarial: Decimal
    montant_patronal: Decimal


class SimulerPaieResult(BaseModel):
    salaire_brut: Decimal
    total_salarial: Decimal
    total_patronal: Decimal
    net_imposable: Decimal
    net_a_payer: Decimal
    cout_total_employeur: Decimal
    lignes: list[LigneCotisationOut]


class BulletinCreate(BaseModel):
    employee_id: str
    period_start: date
    period_end: date
    salaire_brut: Decimal
    is_cadre: bool = False


class LigneBulletinOut(BaseModel):
    libelle: str
    base: Decimal
    taux_salarial: Decimal
    taux_patronal: Decimal
    montant_salarial: Decimal
    montant_patronal: Decimal
    model_config = {"from_attributes": True}


class BulletinOut(BaseModel):
    id: str
    employee_id: str
    period_start: date
    period_end: date
    status: str
    salaire_brut: Decimal
    cotisations_salariales: Decimal
    cotisations_patronales: Decimal
    net_a_payer: Decimal
    lines: list[LigneBulletinOut] = []
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/simulate", response_model=SimulerPaieResult)
def simulate_paie(body: SimulerPaieRequest) -> SimulerPaieResult:
    """Simule le calcul de bulletin de paie (cotisations + net) sans persistance."""
    from src.modules.paie.engine import compute_bulletin

    calc = compute_bulletin(body.salaire_brut, is_cadre=body.is_cadre)
    return SimulerPaieResult(
        salaire_brut=calc.salaire_brut,
        total_salarial=calc.total_salarial,
        total_patronal=calc.total_patronal,
        net_imposable=calc.net_imposable,
        net_a_payer=calc.net_a_payer,
        cout_total_employeur=calc.cout_total_employeur,
        lignes=[
            LigneCotisationOut(
                libelle=ln.libelle,
                base=ln.base,
                taux_salarial=ln.taux_salarial,
                taux_patronal=ln.taux_patronal,
                montant_salarial=ln.montant_salarial,
                montant_patronal=ln.montant_patronal,
            )
            for ln in calc.lignes
        ],
    )


@router.post("/", response_model=BulletinOut, status_code=201)
def create_bulletin(
    body: BulletinCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Bulletin:
    """Crée et calcule un bulletin de paie."""
    from src.modules.paie.engine import compute_bulletin

    company_id = current_user["company_id"]
    calc = compute_bulletin(body.salaire_brut, is_cadre=body.is_cadre)

    bulletin = Bulletin(
        id=str(uuid.uuid4()),
        company_id=company_id,
        employee_id=body.employee_id,
        period_start=body.period_start,
        period_end=body.period_end,
        salaire_brut=calc.salaire_brut,
        cotisations_salariales=calc.total_salarial,
        cotisations_patronales=calc.total_patronal,
        net_a_payer=calc.net_a_payer,
        status=BulletinStatus.BROUILLON,
    )

    for ln in calc.lignes:
        bulletin.lines.append(LigneBulletin(
            id=str(uuid.uuid4()),
            company_id=company_id,
            bulletin_id=bulletin.id,
            libelle=ln.libelle,
            base=ln.base,
            taux_salarial=ln.taux_salarial,
            taux_patronal=ln.taux_patronal,
            montant_salarial=ln.montant_salarial,
            montant_patronal=ln.montant_patronal,
        ))

    db.add(bulletin)
    db.commit()
    db.refresh(bulletin)
    return bulletin


@router.get("/", response_model=list[BulletinOut])
def list_bulletins(
    employee_id: str | None = Query(None),
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> list[Bulletin]:
    q = db.query(Bulletin).filter_by(company_id=current_user["company_id"])
    if employee_id:
        q = q.filter(Bulletin.employee_id == employee_id)
    return q.order_by(Bulletin.period_start.desc()).all()


@router.get("/{bulletin_id}", response_model=BulletinOut)
def get_bulletin(
    bulletin_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Bulletin:
    b = db.query(Bulletin).filter_by(id=bulletin_id, company_id=current_user["company_id"]).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bulletin introuvable")
    return b


@router.post("/{bulletin_id}/validate", response_model=BulletinOut)
def validate_bulletin(
    bulletin_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
) -> Bulletin:
    b = db.query(Bulletin).filter_by(id=bulletin_id, company_id=current_user["company_id"]).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bulletin introuvable")
    if b.status != BulletinStatus.BROUILLON:
        raise HTTPException(status_code=422, detail=f"Bulletin déjà au statut {b.status}")
    b.status = BulletinStatus.VALIDE
    db.commit()
    db.refresh(b)
    return b


@router.get("/dsn/preview")
def dsn_preview(
    period: str = Query(..., description="Période YYYY-MM"),
    _: dict = Depends(get_current_user),
) -> dict:
    """Génère un aperçu DSN (Déclaration Sociale Nominative) — stub."""
    return {
        "status": "preview",
        "period": period,
        "format": "DSN phase 3",
        "message": "Génération DSN complète disponible avec le module DSN (NEODES/Net-entreprises).",
        "fields": {
            "siren": "à compléter",
            "etablissement": "à compléter",
            "mois_principal": period,
            "nb_salaries": 0,
            "masse_salariale_brute": "0.00",
        },
    }
