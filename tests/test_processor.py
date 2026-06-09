import pandas as pd
import pytest
from src.processor import (
    categorize,
    add_categories,
    filter_month,
    monthly_summary,
    expenses_by_category,
    top_expenses,
)

CATEGORIES = {
    "food_groceries": ["carrefour", "lidl", "supermarche"],
    "restaurants": ["restaurant", "uber eats"],
    "transport": ["ratp", "sncf"],
    "income": ["salaire", "freelance"],
    "other": [],
}


def make_df(rows):
    df = pd.DataFrame(rows, columns=["date", "description", "amount"])
    df["date"] = pd.to_datetime(df["date"])
    return df


class TestCategorize:
    def test_matches_keyword(self):
        assert categorize("Carrefour Market", CATEGORIES) == "food_groceries"

    def test_case_insensitive(self):
        assert categorize("LIDL COURSES", CATEGORIES) == "food_groceries"

    def test_partial_match(self):
        assert categorize("Restaurant Le Bistrot", CATEGORIES) == "restaurants"

    def test_falls_back_to_other(self):
        assert categorize("Unknown Merchant XYZ", CATEGORIES) == "other"

    def test_first_match_wins(self):
        cats = {"a": ["foo"], "b": ["foo bar"], "other": []}
        assert categorize("foo bar payment", cats) == "a"


class TestFilterMonth:
    def test_filters_correctly(self):
        df = make_df([
            ("2026-05-01", "A", 100),
            ("2026-05-15", "B", -50),
            ("2026-06-01", "C", 200),
            ("2026-04-30", "D", -30),
        ])
        result = filter_month(df, 2026, 5)
        assert len(result) == 2
        assert all(result["date"].dt.month == 5)

    def test_empty_when_no_match(self):
        df = make_df([("2026-05-01", "A", 100)])
        assert filter_month(df, 2025, 5).empty


class TestMonthlySummary:
    def test_basic_summary(self):
        df = make_df([
            ("2026-05-01", "Salary", 3000),
            ("2026-05-05", "Rent", -900),
            ("2026-05-10", "Food", -200),
        ])
        s = monthly_summary(df)
        assert s["income"] == 3000.0
        assert s["expenses"] == 1100.0
        assert s["net"] == 1900.0
        assert s["savings_rate"] == pytest.approx(63.3, abs=0.1)
        assert s["n_transactions"] == 3

    def test_zero_income(self):
        df = make_df([("2026-05-01", "Rent", -500)])
        s = monthly_summary(df)
        assert s["income"] == 0.0
        assert s["savings_rate"] == 0.0

    def test_rounding(self):
        df = make_df([("2026-05-01", "A", 1000.005)])
        s = monthly_summary(df)
        assert s["income"] == 1000.01


class TestExpensesByCategory:
    def test_sums_by_category(self):
        df = make_df([
            ("2026-05-01", "Salary", 3000),
            ("2026-05-05", "Carrefour", -100),
            ("2026-05-10", "Lidl", -50),
            ("2026-05-12", "Restaurant X", -80),
        ])
        df = add_categories(df, CATEGORIES)
        result = expenses_by_category(df)
        assert result["food_groceries"] == pytest.approx(150.0)
        assert result["restaurants"] == pytest.approx(80.0)
        assert "income" not in result

    def test_sorted_descending(self):
        df = make_df([
            ("2026-05-01", "Restaurant X", -200),
            ("2026-05-05", "Carrefour", -100),
        ])
        df = add_categories(df, CATEGORIES)
        result = expenses_by_category(df)
        values = list(result.values)
        assert values == sorted(values, reverse=True)


class TestTopExpenses:
    def test_returns_top_n(self):
        rows = [("2026-05-01", f"Merchant {i}", -float(i * 10)) for i in range(1, 16)]
        df = make_df(rows)
        result = top_expenses(df, n=5)
        assert len(result) == 5
        assert result["amount"].iloc[0] == 140.0

    def test_excludes_income(self):
        df = make_df([
            ("2026-05-01", "Salary", 3000),
            ("2026-05-05", "Rent", -900),
        ])
        result = top_expenses(df, n=10)
        assert len(result) == 1
        assert result["amount"].iloc[0] == 900.0
