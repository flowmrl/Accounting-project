"""FastAPI application — Compta PME (Pennylane competitor)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import (
    accounts,
    analytique,
    auth,
    companies,
    consolidation,
    facturation,
    immobilisations,
    journal_entries,
    notes_frais,
    ocr,
    paie,
    reports,
    standards,
    stocks,
    tax,
    tresorerie,
    tva,
)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="Compta PME — Logiciel de comptabilité tout-en-un",
        description=(
            "API REST pour la comptabilité des PME françaises. "
            "Multi-référentiels (PCG, IFRS, US GAAP, HGB, FRS 102…), "
            "consolidation groupe, TVA, immobilisations, facturation, trésorerie."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    prefix = "/api/v1"
    app.include_router(auth.router,             prefix=prefix)
    app.include_router(companies.router,        prefix=prefix)
    app.include_router(standards.router,        prefix=prefix)
    app.include_router(accounts.router,         prefix=prefix)
    app.include_router(journal_entries.router,  prefix=prefix)
    app.include_router(reports.router,          prefix=prefix)
    app.include_router(tva.router,              prefix=prefix)
    app.include_router(tax.router,              prefix=prefix)
    app.include_router(immobilisations.router,  prefix=prefix)
    app.include_router(facturation.router,      prefix=prefix)
    app.include_router(tresorerie.router,       prefix=prefix)
    app.include_router(consolidation.router,    prefix=prefix)
    app.include_router(analytique.router,       prefix=prefix)
    app.include_router(stocks.router,           prefix=prefix)
    app.include_router(notes_frais.router,      prefix=prefix)
    app.include_router(paie.router,             prefix=prefix)
    app.include_router(ocr.router,              prefix=prefix)

    @app.get("/", tags=["Health"])
    async def root() -> dict:
        return {"status": "ok", "service": "Compta PME API", "version": "1.0.0"}

    @app.get("/api/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "healthy"}

    return app


app = create_app()
