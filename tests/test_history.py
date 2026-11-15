"""Tests des métriques de la page Historique & évolution (tâche 4)."""

import pandas as pd

from railinsight.analysis.history import (
    CAUSE_COLUMNS,
    cause_breakdown_over_time,
    monthly_delays_cancellations,
    seasonality,
)


def _sample() -> pd.DataFrame:
    """Deux mois, deux liaisons, avec les colonnes du contrat de données."""
    base = {c: 0.0 for c in CAUSE_COLUMNS}
    rows = [
        {**base, "date": "2026-01-01", "scheduled": 100, "cancelled": 2, "late_arrival": 10, "cause_infra": 100.0},
        {**base, "date": "2026-01-01", "scheduled": 100, "cancelled": 4, "late_arrival": 30, "cause_external": 100.0},
        {**base, "date": "2026-02-01", "scheduled": 50, "cancelled": 0, "late_arrival": 5, "cause_infra": 100.0},
    ]
    return pd.DataFrame(rows)


def test_monthly_delays_cancellations_has_both_rates():
    out = monthly_delays_cancellations(_sample())

    assert set(out.columns) == {"date", "late_rate", "cancellation_rate"}
    janvier = out.loc[out["date"] == "2026-01-01"].iloc[0]
    # retard : (10 + 30) / ((200) - (6)) ; annulation : 6 / 200
    assert janvier["late_rate"] == 40 / 194
    assert janvier["cancellation_rate"] == 6 / 200


def test_cause_breakdown_is_weighted_by_late_trains():
    out = cause_breakdown_over_time(_sample())

    janvier = out.loc[out["date"] == pd.Timestamp("2026-01-01")].iloc[0]
    # 10 trains "infra" vs 30 trains "externe" -> externe pèse 3x plus
    assert round(janvier["cause_external"], 2) == round(100 * 30 / 40, 2)
    assert round(janvier["cause_infra"], 2) == round(100 * 10 / 40, 2)


def test_seasonality_returns_one_row_per_month():
    out = seasonality(_sample())

    assert set(out["month"]) == {1, 2}
    assert list(out.columns) == ["month", "late_rate"]
