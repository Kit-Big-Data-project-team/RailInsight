"""Tests de vérification des historiques de prévision."""

import pandas as pd

from railinsight.analysis.forecast import get_recent_rates


def test_three_consecutive_months():
    df = pd.DataFrame({
        "date": pd.to_datetime([
            "2026-07-01",
            "2026-08-01",
            "2026-09-01",
        ]),
        "late_rate": [0.12, 0.15, 0.18],
    })

    rates = get_recent_rates(df, pd.Period("2026-09", freq="M"))

    assert rates == [0.12, 0.15, 0.18]


def test_missing_month():
    df = pd.DataFrame({
        "date": pd.to_datetime([
            "2026-06-01",
            "2026-07-01",
            "2026-09-01",
        ]),
        "late_rate": [0.12, 0.15, 0.18],
    })

    rates = get_recent_rates(df, pd.Period("2026-09", freq="M"))

    assert rates is None


def test_insufficient_history():
    df = pd.DataFrame({
        "date": pd.to_datetime([
            "2026-08-01",
            "2026-09-01",
        ]),
        "late_rate": [0.15, 0.18],
    })

    rates = get_recent_rates(df, pd.Period("2026-09", freq="M"))

    assert rates is None