import pandas as pd
import yaml
from pathlib import Path


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def _read_csv_auto(path: Path) -> pd.DataFrame:
    """Try comma separator first, fall back to semicolon."""
    try:
        df = pd.read_csv(path, sep=",")
        if df.shape[1] > 1:
            return df
    except Exception:
        pass
    return pd.read_csv(path, sep=";")


def load_transactions(file_path: str, config: dict) -> pd.DataFrame:
    path = Path(file_path)
    cols = config["columns"]

    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = _read_csv_auto(path)

    df.columns = df.columns.str.strip()

    # Handle separate debit/credit columns
    if "debit" in cols and "credit" in cols:
        df["Amount"] = df[cols["credit"]].fillna(0) - df[cols["debit"]].fillna(0)
        cols = {**cols, "amount": "Amount"}

    required = [cols["date"], cols["description"], cols["amount"]]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in file: {missing}. Available: {list(df.columns)}")

    df = df.rename(columns={
        cols["date"]: "date",
        cols["description"]: "description",
        cols["amount"]: "amount",
    })

    df = df[["date", "description", "amount"]].copy()
    df["date"] = pd.to_datetime(
        df["date"],
        format=config.get("date_format", "%Y-%m-%d"),
        dayfirst=True,
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])
    df = df.sort_values("date").reset_index(drop=True)
    return df
