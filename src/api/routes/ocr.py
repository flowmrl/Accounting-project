"""OCR — extraction de données depuis fichiers facture."""
from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, File

from src.api.middleware.auth import get_current_user
from src.modules.ocr.extractor import extract_invoice_data

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/extract")
async def ocr_extract(
    file: UploadFile = File(...),
    _: dict = Depends(get_current_user),
) -> dict:
    """Extrait les données d'une facture uploadée (PDF ou image)."""
    file_bytes = await file.read()
    return extract_invoice_data(file_bytes, filename=file.filename or "")
