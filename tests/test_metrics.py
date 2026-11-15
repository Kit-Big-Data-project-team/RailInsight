"""Tests des métriques communes de régularité (socle partagé par toutes les pages)."""

import pandas as pd

from railinsight.analysis.metrics import cancellation_rate, monthly_late_rate


def test_monthly_late_rate_aggregates_by_month():
    """Le taux est un rapport de sommes : on agrège d'abord, puis on divise."""
    df = pd.DataFrame(
        {
            "date": ["2026-01", "2026-01", "2026-02"],
            "scheduled": [100, 100, 50],
            "cancelled": [0, 0, 0],
            "late_arrival": [10, 10, 5],
        }
    )
    out = monthly_late_rate(df)

    assert out.loc[out["date"] == "2026-01", "late_rate"].iloc[0] == 20 / 200
    assert out.loc[out["date"] == "2026-02", "late_rate"].iloc[0] == 5 / 50


def test_monthly_late_rate_handles_fully_cancelled_month():
    """Un mois entièrement annulé (ex. grève) ne doit pas produire d'infini."""
    df = pd.DataFrame(
        {
            "date": ["2026-03"],
            "scheduled": [40],
            "cancelled": [40],  # tout annulé -> dénominateur = 0
            "late_arrival": [0],
        }
    )
    out = monthly_late_rate(df)

    assert pd.isna(out["late_rate"].iloc[0])


def test_cancellation_rate_aggregates_by_month():
    """Taux d'annulation = annulés / prévus, en rapport de sommes."""
    df = pd.DataFrame(
        {
            "date": ["2026-01", "2026-01"],
            "scheduled": [100, 100],
            "cancelled": [1, 3],
        }
    )
    out = cancellation_rate(df)

    assert out["cancellation_rate"].iloc[0] == 4 / 200
