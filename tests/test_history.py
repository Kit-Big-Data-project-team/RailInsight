"""Tests des métriques de la page Historique & évolution (tâche 4)."""

import pandas as pd

from railinsight.analysis.history import (
    CAUSE_COLUMNS,
    cause_breakdown_over_time,
    delay_severity_over_time,
    monthly_delays_cancellations,
    punctuality_by_service,
    seasonality,
)


def _row(**kw) -> dict:
    row = {c: 0.0 for c in CAUSE_COLUMNS}
    row.update(kw)
    return row


def _sample() -> pd.DataFrame:
    """Deux mois, deux services, avec les colonnes du contrat de données."""
    rows = [
        _row(date="2026-01-01", service="National", scheduled=100, cancelled=2, late_arrival=10, late_15=8, late_30=4, late_60=1, cause_infra=100.0),
        _row(date="2026-01-01", service="International", scheduled=100, cancelled=4, late_arrival=30, late_15=20, late_30=10, late_60=5, cause_external=100.0),
        _row(date="2026-02-01", service="National", scheduled=50, cancelled=0, late_arrival=5, late_15=3, late_30=1, late_60=0, cause_infra=100.0),
    ]
    return pd.DataFrame(rows)


def test_monthly_delays_cancellations_has_both_rates():
    out = monthly_delays_cancellations(_sample())

    assert set(out.columns) == {"date", "late_rate", "cancellation_rate"}
    janvier = out.loc[out["date"] == "2026-01-01"].iloc[0]
    assert janvier["late_rate"] == 40 / 194
    assert janvier["cancellation_rate"] == 6 / 200


def test_punctuality_by_service_splits_by_service():
    out = punctuality_by_service(_sample())

    national = out[(out["date"] == "2026-01-01") & (out["service"] == "National")].iloc[0]
    inter = out[(out["date"] == "2026-01-01") & (out["service"] == "International")].iloc[0]
    assert national["late_rate"] == 10 / 98
    assert inter["late_rate"] == 30 / 96


def test_delay_severity_over_time_is_share_of_scheduled():
    out = delay_severity_over_time(_sample())

    janvier = out[out["date"] == "2026-01-01"].iloc[0]
    assert janvier["late_15"] == 28 / 200
    assert janvier["late_30"] == 14 / 200
    assert janvier["late_60"] == 6 / 200


def test_cause_breakdown_is_weighted_by_late_trains():
    out = cause_breakdown_over_time(_sample())

    janvier = out.loc[out["date"] == pd.Timestamp("2026-01-01")].iloc[0]
    assert round(janvier["cause_external"], 2) == round(100 * 30 / 40, 2)
    assert round(janvier["cause_infra"], 2) == round(100 * 10 / 40, 2)


def test_seasonality_returns_one_row_per_month():
    out = seasonality(_sample())

    assert set(out["month"]) == {1, 2}
    assert list(out.columns) == ["month", "late_rate"]
