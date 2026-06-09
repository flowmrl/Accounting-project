import yaml
import pandas as pd
from pathlib import Path


def load_categories(categories_path: str = "categories.yaml") -> dict:
    with open(categories_path, "r") as f:
        return yaml.safe_load(f)


def categorize(description: str, categories: dict) -> str:
    desc_lower = str(description).lower()
    for category, keywords in categories.items():
        if category == "other":
            continue
        for kw in keywords or []:
            if kw.lower() in desc_lower:
                return category
    return "other"


def add_categories(df: pd.DataFrame, categories: dict) -> pd.DataFrame:
    df = df.copy()
    df["category"] = df["description"].apply(lambda d: categorize(d, categories))
    return df


def filter_month(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    return df[(df["date"].dt.year == year) & (df["date"].dt.month == month)].copy()


def monthly_summary(df: pd.DataFrame) -> dict:
    income = df[df["amount"] > 0]["amount"].sum()
    expenses = df[df["amount"] < 0]["amount"].sum()
    net = income + expenses
    return {
        "income": round(income, 2),
        "expenses": round(abs(expenses), 2),
        "net": round(net, 2),
        "savings_rate": round((net / income * 100) if income > 0 else 0, 1),
        "n_transactions": len(df),
    }


def expenses_by_category(df: pd.DataFrame) -> pd.Series:
    expenses = df[df["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()
    return expenses.groupby("category")["amount"].sum().sort_values(ascending=False)


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    income = df[df["amount"] > 0].groupby("month")["amount"].sum().rename("income")
    expenses = df[df["amount"] < 0].groupby("month")["amount"].sum().abs().rename("expenses")
    trend = pd.concat([income, expenses], axis=1).fillna(0)
    trend["net"] = trend["income"] - trend["expenses"]
    return trend.sort_index().tail(12)


def top_expenses(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (
        df[df["amount"] < 0]
        .assign(amount=lambda x: x["amount"].abs())
        .nlargest(n, "amount")[["date", "description", "category", "amount"]]
        .reset_index(drop=True)
    )
