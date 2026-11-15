"""Tests des métriques des pages Overview (tâche 3) et Mon trajet (tâche 6)."""

import pandas as pd

from railinsight.analysis.history import CAUSE_COLUMNS
from railinsight.analysis.overview import global_kpis
from railinsight.analysis.trip import average_causes, trip_summary


def _sample() -> pd.DataFrame:
    base = {c: 0.0 for c in CAUSE_COLUMNS}
    return pd.DataFrame(
        [
            {**base, "route": "A", "date": "2026-01-01", "scheduled": 100, "cancelled": 2, "late_arrival": 10, "avg_delay_arrival": 12.0, "cause_infra": 100.0},
            {**base, "route": "A", "date": "2026-02-01", "scheduled": 100, "cancelled": 0, "late_arrival": 30, "avg_delay_arrival": 8.0, "cause_external": 100.0},
            {**base, "route": "B", "date": "2026-01-01", "scheduled": 50, "cancelled": 5, "late_arrival": 5, "avg_delay_arrival": 20.0, "cause_infra": 100.0},
        ]
    )


def test_global_kpis():
    kpis = global_kpis(_sample())

    assert kpis["n_routes"] == 2
    assert kpis["scheduled"] == 250
    # retard : 45 / (250 - 7) ; annulation : 7 / 250
    assert kpis["late_rate"] == 45 / 243
    assert kpis["cancellation_rate"] == 7 / 250


def test_trip_summary_for_one_route():
    sub = _sample()
    sub = sub[sub["route"] == "A"]
    resume = trip_summary(sub)

    assert resume["n_months"] == 2
    assert resume["cancellation_probability"] == 2 / 200
    assert resume["late_rate"] == 40 / 198
    # retard moyen pondéré par les trains en retard : (12*10 + 8*30) / 40
    assert resume["avg_delay_arrival"] == (12 * 10 + 8 * 30) / 40


def test_average_causes_weighted():
    sub = _sample()
    sub = sub[sub["route"] == "A"]
    causes = average_causes(sub)

    assert round(causes["cause_external"], 2) == round(100 * 30 / 40, 2)
    assert round(causes["cause_infra"], 2) == round(100 * 10 / 40, 2)
