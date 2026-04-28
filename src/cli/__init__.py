"""CLI Compta PME — Typer application."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Typer/Rich not installed. Run: pip install typer rich")
    sys.exit(1)

app = typer.Typer(
    name="compta-pme",
    help="Compta PME — logiciel de comptabilité tout-en-un pour les PME françaises.",
    add_completion=False,
)
console = Console()


# ---------------------------------------------------------------------------
# DB sub-app
# ---------------------------------------------------------------------------

db_app = typer.Typer(help="Gestion de la base de données.")
app.add_typer(db_app, name="db")


@db_app.command("migrate")
def db_migrate(
    revision: str = typer.Argument("head", help="Révision cible (ex: head, 001, base)"),
) -> None:
    """Applique les migrations Alembic."""
    import subprocess
    result = subprocess.run(
        ["alembic", "upgrade", revision], capture_output=True, text=True
    )
    if result.returncode == 0:
        console.print(f"[green]✓ Migration appliquée : {revision}[/green]")
        console.print(result.stdout)
    else:
        console.print(f"[red]✗ Erreur migration[/red]\n{result.stderr}", err=True)
        raise typer.Exit(1)


@db_app.command("init")
def db_init() -> None:
    """Crée toutes les tables (sans Alembic — dev uniquement)."""
    from src.db.session import create_all_tables
    create_all_tables()
    console.print("[green]✓ Tables créées.[/green]")


# ---------------------------------------------------------------------------
# Company sub-app
# ---------------------------------------------------------------------------

company_app = typer.Typer(help="Gestion des sociétés.")
app.add_typer(company_app, name="company")


@company_app.command("create")
def company_create(
    name: str = typer.Option(..., "--name", "-n", help="Raison sociale"),
    siren: Optional[str] = typer.Option(None, "--siren"),
    standard: str = typer.Option("PCG", "--standard", help="Référentiel comptable"),
    currency: str = typer.Option("EUR", "--currency"),
) -> None:
    """Crée une nouvelle société et charge le plan de comptes."""
    import uuid

    from src.core.models.company import Company
    from src.db.session import get_session

    company_id = str(uuid.uuid4())
    db = next(get_session())
    try:
        company = Company(
            id=company_id,
            name=name,
            siren=siren,
            accounting_standard=standard,
            currency=currency,
        )
        db.add(company)
        db.commit()
        console.print(f"[green]✓ Société créée : {name} (id={company_id})[/green]")

        # Auto-chargement PCG
        if standard == "PCG":
            _load_pcg(company_id, db)
    except Exception as exc:
        db.rollback()
        console.print(f"[red]✗ Erreur : {exc}[/red]", err=True)
        raise typer.Exit(1)
    finally:
        db.close()


@company_app.command("list")
def company_list() -> None:
    """Liste toutes les sociétés."""
    from src.core.models.company import Company
    from src.db.session import get_session

    db = next(get_session())
    try:
        companies = db.query(Company).all()
        table = Table("ID", "Nom", "SIREN", "Référentiel", "Devise")
        for c in companies:
            table.add_row(str(c.id)[:8] + "…", c.name, c.siren or "-", c.accounting_standard, c.currency)
        console.print(table)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# PCG sub-app
# ---------------------------------------------------------------------------

pcg_app = typer.Typer(help="Plan de comptes PCG.")
app.add_typer(pcg_app, name="pcg")


def _load_pcg(company_id: str, db) -> int:
    from src.core.services.pcg_loader import PCGLoader
    count = PCGLoader.load_for_company(company_id, db)
    console.print(f"[green]✓ {count} comptes PCG chargés pour {company_id[:8]}…[/green]")
    return count


@pcg_app.command("load")
def pcg_load(
    company_id: str = typer.Argument(..., help="UUID de la société"),
) -> None:
    """Charge le plan de comptes PCG pour une société."""
    from src.db.session import get_session

    db = next(get_session())
    try:
        _load_pcg(company_id, db)
    except Exception as exc:
        console.print(f"[red]✗ {exc}[/red]", err=True)
        raise typer.Exit(1)
    finally:
        db.close()


@pcg_app.command("stats")
def pcg_stats() -> None:
    """Affiche les statistiques du plan de comptes PCG."""
    from src.core.standards.pcg_france import PCGFrance
    pcg = PCGFrance()
    accounts = pcg.get_chart_of_accounts()
    by_class = {}
    for a in accounts:
        by_class.setdefault(a.account_class, []).append(a)

    table = Table("Classe", "Comptes", "Détail", "Regroupement")
    for cls in sorted(by_class):
        accts = by_class[cls]
        detail = sum(1 for a in accts if a.is_detail)
        table.add_row(cls, str(len(accts)), str(detail), str(len(accts) - detail))

    console.print(table)
    console.print(f"\n[bold]Total : {len(accounts)} comptes PCG[/bold]")


# ---------------------------------------------------------------------------
# Standards sub-app
# ---------------------------------------------------------------------------

std_app = typer.Typer(help="Référentiels comptables disponibles.")
app.add_typer(std_app, name="standards")


@std_app.command("list")
def standards_list() -> None:
    """Liste tous les référentiels comptables enregistrés."""
    # Import all addons
    import src.addons.be_gaap.standard
    import src.addons.dutch_bw2.standard
    import src.addons.german_hgb.standard
    import src.addons.ifrs.standard
    import src.addons.italian_oic.standard
    import src.addons.luxembourg_gaap.standard
    import src.addons.polish_psr.standard
    import src.addons.spanish_pgc.standard
    import src.addons.swiss_fer.standard
    import src.addons.uk_frs.standard
    import src.addons.us_gaap.standard
    from src.core.standards.base import StandardRegistry
    standards = StandardRegistry.list_all()
    table = Table("Code", "Nom", "Pays")
    for s in sorted(standards, key=lambda x: x["code"]):
        table.add_row(s["code"], s["name"][:55], s["countries"])
    console.print(table)


# ---------------------------------------------------------------------------
# Tax sub-app
# ---------------------------------------------------------------------------

tax_app = typer.Typer(help="Outils fiscaux.")
app.add_typer(tax_app, name="tax")


@tax_app.command("fec")
def fec_export(
    company_id: str = typer.Argument(...),
    fiscal_year_id: str = typer.Argument(...),
    output: Path = typer.Option(Path("FEC.txt"), "--output", "-o"),
) -> None:
    """Exporte le Fichier des Écritures Comptables (FEC) — format DGFiP."""
    from src.db.session import get_session
    from src.modules.tax.fec_export import write_fec_file

    db = next(get_session())
    try:
        write_fec_file(company_id, fiscal_year_id, str(output), db)
        console.print(f"[green]✓ FEC exporté : {output}[/green]")
    except Exception as exc:
        console.print(f"[red]✗ {exc}[/red]", err=True)
        raise typer.Exit(1)
    finally:
        db.close()


@tax_app.command("is-simulate")
def is_simulate(
    profit: float = typer.Argument(..., help="Résultat fiscal (€)"),
    ca: float = typer.Option(5_000_000, "--ca", help="Chiffre d'affaires (€)"),
    pme: bool = typer.Option(True, "--pme/--no-pme"),
) -> None:
    """Simule l'impôt sur les sociétés."""
    from decimal import Decimal

    from src.modules.tax.is_engine import compute_is

    result = compute_is(
        resultat_fiscal=Decimal(str(profit)),
        chiffre_affaires=Decimal(str(ca)),
        is_pme=pme,
    )
    table = Table("Poste", "Montant")
    table.add_row("Résultat fiscal", f"{result.resultat_fiscal:,.2f} €")
    table.add_row("IS taux réduit (15%)", f"{result.is_taux_reduit:,.2f} €")
    table.add_row("IS taux normal (25%)", f"{result.is_taux_normal:,.2f} €")
    table.add_row("[bold]IS total[/bold]", f"[bold]{result.is_total:,.2f} €[/bold]")
    table.add_row("PME éligible", "Oui" if result.is_pme_eligible else "Non")
    console.print(table)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

@app.command("serve")
def serve(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Lance le serveur FastAPI."""
    try:
        import uvicorn
    except ImportError:
        console.print("[red]uvicorn non installé. Lancez : pip install uvicorn[/red]", err=True)
        raise typer.Exit(1)
    console.print(f"[green]Serveur Compta PME sur http://{host}:{port}[/green]")
    uvicorn.run("src.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
