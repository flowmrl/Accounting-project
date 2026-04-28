"""Stocks — articles, mouvements, inventaire."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import get_current_user
from src.db.session import get_session
from src.modules.stocks.engine import apply_movement
from src.modules.stocks.models import Article, StockMovement, StockMoveType, ValuationMethod

router = APIRouter(prefix="/stocks", tags=["Stocks"])


class ArticleCreate(BaseModel):
    company_id: str
    reference: str
    name: str
    description: str | None = None
    unit: str = "unité"
    valuation_method: str = ValuationMethod.CMUP
    account_stock: str = "37"
    account_variation: str = "6037"
    min_qty: float = 0.0


class MovementCreate(BaseModel):
    move_date: date
    move_type: str
    qty: float
    unit_cost: float
    reference: str | None = None
    notes: str | None = None


class ArticleOut(BaseModel):
    id: str
    company_id: str
    reference: str
    name: str
    unit: str
    valuation_method: str
    stock_qty: float
    stock_value: float
    unit_cost: float
    is_active: bool
    model_config = {"from_attributes": True}


@router.post("/articles", response_model=ArticleOut, status_code=201)
def create_article(
    payload: ArticleCreate,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> Article:
    from decimal import Decimal
    article = Article(id=str(uuid.uuid4()), **{
        **payload.model_dump(),
        "min_qty": Decimal(str(payload.min_qty)),
    })
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    company_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> list[Article]:
    return db.query(Article).filter(Article.company_id == company_id, Article.is_active.is_(True)).all()


@router.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(
    article_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> Article:
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return article


@router.post("/articles/{article_id}/movements", status_code=201)
def add_movement(
    article_id: str,
    payload: MovementCreate,
    company_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> dict:
    from decimal import Decimal
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")

    qty = Decimal(str(payload.qty))
    unit_cost = Decimal(str(payload.unit_cost))
    movement = StockMovement(
        id=str(uuid.uuid4()),
        company_id=company_id,
        article_id=article_id,
        move_date=payload.move_date,
        move_type=payload.move_type,
        qty=qty,
        unit_cost=unit_cost,
        total_cost=qty * unit_cost,
        reference=payload.reference,
        notes=payload.notes,
    )
    db.add(movement)
    apply_movement(article, movement, db)
    db.commit()
    return {
        "movement_id": movement.id,
        "stock_qty": float(article.stock_qty),
        "stock_value": float(article.stock_value),
        "unit_cost": float(article.unit_cost),
    }


@router.get("/articles/{article_id}/movements")
def list_movements(
    article_id: str,
    db: Session = Depends(get_session),
    _: dict = Depends(get_current_user),
) -> list[dict]:
    movements = (
        db.query(StockMovement)
        .filter(StockMovement.article_id == article_id)
        .order_by(StockMovement.move_date)
        .all()
    )
    return [
        {
            "id": m.id,
            "move_date": str(m.move_date),
            "move_type": m.move_type,
            "qty": float(m.qty),
            "unit_cost": float(m.unit_cost),
            "total_cost": float(m.total_cost),
            "reference": m.reference,
        }
        for m in movements
    ]
