"""Paie — stub API (module en développement)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.middleware.auth import get_current_user

router = APIRouter(prefix="/payslips", tags=["Paie"])


@router.get("/")
def list_payslips(_: dict = Depends(get_current_user)) -> dict:
    return {
        "data": [],
        "message": "Module Paie en cours de développement. Disponible prochainement.",
        "status": "stub",
    }
