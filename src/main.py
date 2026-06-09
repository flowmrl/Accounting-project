import sys
from pathlib import Path
from datetime import date

import click

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loader import load_config, load_transactions
from src.processor import (
    load_categories, add_categories, filter_month,
    monthly_summary, expenses_by_category, monthly_trend, top_expenses,
)
from src.reporter import generate_pdf


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--year", "-y", default=None, type=int, help="Year (default: current year)")
@click.option("--month", "-m", default=None, type=int, help="Month 1-12 (default: previous month)")
@click.option("--config", "-c", default="config.yaml", show_default=True, help="Path to config.yaml")
@click.option("--categories", default="categories.yaml", show_default=True, help="Path to categories.yaml")
@click.option("--output", "-o", default=None, help="Output directory (default: from config or 'reports')")
def main(input_file, year, month, config, categories, output):
    """Generate a monthly financial PDF report from a CSV/Excel transactions file."""
    today = date.today()
    if month is None:
        month = today.month - 1 if today.month > 1 else 12
    if year is None:
        year = today.year if today.month > 1 else today.year - 1

    click.echo(f"Loading config from {config}...")
    cfg = load_config(config)
    cats = load_categories(categories)

    output_dir = output or cfg.get("output_dir", "reports")

    click.echo(f"Loading transactions from {input_file}...")
    df = load_transactions(input_file, cfg)
    df = add_categories(df, cats)

    click.echo(f"Generating report for {year}-{month:02d}...")
    month_df = filter_month(df, year, month)

    if month_df.empty:
        click.echo(f"No transactions found for {year}-{month:02d}.", err=True)
        raise SystemExit(1)

    summary = monthly_summary(month_df)
    by_category = expenses_by_category(month_df)
    trend = monthly_trend(df)
    top_exp = top_expenses(month_df, n=10)

    click.echo(f"\nSummary for {year}-{month:02d}:")
    click.echo(f"  Income:    {cfg.get('currency', '€')} {summary['income']:>10,.2f}")
    click.echo(f"  Expenses:  {cfg.get('currency', '€')} {summary['expenses']:>10,.2f}")
    click.echo(f"  Net:       {cfg.get('currency', '€')} {summary['net']:>10,.2f}")
    click.echo(f"  Savings:   {summary['savings_rate']}%")

    filepath = generate_pdf(summary, by_category, trend, top_exp, year, month, cfg, output_dir)
    click.echo(f"\nReport saved to: {filepath}")


if __name__ == "__main__":
    main()
