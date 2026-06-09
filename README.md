# Accounting-project — Personal Financial Reporting Agent

A Python CLI agent that reads your bank's CSV/Excel exports and generates a clean monthly PDF report with charts, category breakdowns, and spending trends.

## Features

- Ingests CSV or Excel transaction exports (configurable column mapping)
- Auto-categorizes transactions by keyword rules (`categories.yaml`)
- Generates a PDF report including:
  - Monthly KPI cards (income, expenses, net savings, savings rate)
  - Expense breakdown pie chart + bar chart by category
  - 12-month income vs expenses trend chart
  - Category summary table
  - Top 10 expenses table

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m src.main data/sample/transactions_sample.csv --month 5 --year 2026
```

Options:
```
Arguments:
  INPUT_FILE          Path to your CSV or Excel transactions file

Options:
  -y, --year INT      Year (default: current year)
  -m, --month INT     Month 1-12 (default: previous month)
  -c, --config PATH   Path to config.yaml  [default: config.yaml]
  --categories PATH   Path to categories.yaml  [default: categories.yaml]
  -o, --output PATH   Output directory  [default: reports/]
```

The report is saved to `reports/report_YYYY_MM.pdf`.

## CSV format

The expected default format (configurable in `config.yaml`):

```csv
Date,Description,Amount
2026-05-01,Salary Deposit,3200.00
2026-05-03,Supermarket,-87.50
2026-05-05,Netflix,-15.99
```

- **Positive amounts** = income
- **Negative amounts** = expenses
- If your bank uses separate Debit/Credit columns, set `debit` and `credit` keys in `config.yaml` instead of `amount`

## Configuration

### `config.yaml` — column mapping and settings

```yaml
columns:
  date: "Date"
  description: "Description"
  amount: "Amount"
date_format: "%Y-%m-%d"
currency: "€"
output_dir: "reports"
```

### `categories.yaml` — keyword rules

Add keywords under each category. The first matching category wins. Keywords are case-insensitive and matched as substrings.

```yaml
food_groceries:
  - carrefour
  - lidl
  - supermarche

restaurants:
  - restaurant
  - uber eats
```

## Running tests

```bash
pytest tests/
```

## Project structure

```
├── src/
│   ├── loader.py       # CSV/Excel ingestion
│   ├── processor.py    # Categorization and aggregation
│   ├── reporter.py     # PDF generation (matplotlib + reportlab)
│   └── main.py         # CLI entry point
├── data/sample/        # Sample transaction files
├── reports/            # Generated PDF reports (git-ignored)
├── config.yaml         # Column mapping and settings
└── categories.yaml     # Category keyword rules
```
