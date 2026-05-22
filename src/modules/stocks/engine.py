"""Moteur de valorisation des stocks — CMUP et FIFO."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.modules.stocks.models import Article, StockMovement, StockMoveType, ValuationMethod


def compute_cmup(article: Article, qty_in: Decimal, cost_in: Decimal) -> Decimal:
    """Calcule le nouveau Coût Moyen Unitaire Pondéré après une entrée."""
    total_qty = article.stock_qty + qty_in
    if total_qty == 0:
        return Decimal("0")
    total_value = article.stock_value + (qty_in * cost_in)
    return (total_value / total_qty).quantize(Decimal("0.0001"))


def fifo_value_out(article: Article, qty_out: Decimal, db: Session) -> Decimal:
    """
    Calcule le coût d'une sortie en méthode FIFO.
    Lit les lots d'entrée ordonnés par date (les plus anciens d'abord).
    Retourne le coût total de la sortie.
    """
    entries = (
        db.query(StockMovement)
        .filter(
            StockMovement.article_id == article.id,
            StockMovement.move_type == StockMoveType.ENTREE,
        )
        .order_by(StockMovement.move_date, StockMovement.created_at)
        .all()
    )

    remaining = qty_out
    total_cost = Decimal("0")

    for lot in entries:
        if remaining <= 0:
            break
        consumed = min(remaining, lot.qty)
        total_cost += consumed * lot.unit_cost
        remaining -= consumed

    if remaining > 0:
        # Lot insuffisant — utiliser le dernier coût connu
        fallback = article.unit_cost
        total_cost += remaining * fallback

    return total_cost.quantize(Decimal("0.01"))


def apply_movement(article: Article, movement: StockMovement, db: Session) -> None:
    """
    Applique un mouvement de stock sur l'article :
    - Met à jour stock_qty et stock_value selon la méthode de valorisation.
    - Calcule total_cost si non déjà renseigné.
    """
    qty = movement.qty
    unit_cost = movement.unit_cost

    if movement.move_type in (StockMoveType.ENTREE, StockMoveType.INVENTAIRE):
        if movement.move_type == StockMoveType.ENTREE:
            if article.valuation_method == ValuationMethod.CMUP:
                new_cmup = compute_cmup(article, qty, unit_cost)
                article.stock_qty += qty
                article.stock_value = article.stock_qty * new_cmup
            else:
                # FIFO ou LIFO : on empile simplement le lot, le coût de sortie sera calculé à la sortie
                article.stock_qty += qty
                article.stock_value += qty * unit_cost

        elif movement.move_type == StockMoveType.INVENTAIRE:
            # Ajustement : forcer la quantité et recalculer la valeur au coût actuel
            article.stock_qty = qty
            article.stock_value = qty * unit_cost

        movement.total_cost = qty * unit_cost

    elif movement.move_type in (StockMoveType.SORTIE, StockMoveType.RETOUR):
        if article.valuation_method == ValuationMethod.FIFO:
            total_cost = fifo_value_out(article, qty, db)
        else:
            total_cost = qty * article.unit_cost

        movement.unit_cost = (total_cost / qty).quantize(Decimal("0.0001")) if qty else Decimal("0")
        movement.total_cost = total_cost
        article.stock_qty -= qty
        article.stock_value = max(Decimal("0"), article.stock_value - total_cost)

    elif movement.move_type == StockMoveType.TRANSFERT:
        # Transfert neutre en valorisation (juste un changement de dépôt)
        movement.total_cost = qty * unit_cost
