"""Tests des métriques de synthèse de la page Overview."""

import pandas as pd

from railinsight.analysis.history import CAUSE_COLUMNS
from railinsight.analysis.overview import (
    latest_month_kpis,
    overall_cause_distribution,
    overview_highlights,
)


def _row(date: str, scheduled: int, cancelled: int, late: int, cause: str = "cause_external") -> dict:
    row = {column: 0.0 for column in CAUSE_COLUMNS}
    row.update(
        {
            "date": date,
            "route": "Paris → Lyon",
            "scheduled": scheduled,
            "cancelled": cancelled,
            "late_arrival": late,
        }
    )
    row[cause] = 100.0
    return row


def test_latest_month_kpis_compare_with_previous_calendar_month():
    df = pd.DataFrame(
        [
            _row("2026-01-01", scheduled=100, cancelled=10, late=9),
            _row("2026-02-01", scheduled=100, cancelled=0, late=20),
        ]
    )

    result = latest_month_kpis(df)

    assert result["late_rate"] == 20 / 100
    assert result["late_delta"] == 20 / 100 - 9 / 90
    assert result["cancellation_rate"] == 0
    assert result["cancellation_delta"] == -0.10


def test_overall_causes_are_weighted_by_number_of_late_trains():
    df = pd.DataFrame(
        [
            _row("2026-01-01", scheduled=100, cancelled=0, late=10, cause="cause_infra"),
            _row("2026-01-01", scheduled=100, cancelled=0, late=30, cause="cause_external"),
        ]
    )

    result = overall_cause_distribution(df).set_index("cause")

    assert result.loc["Causes externes", "share"] == 75.0
    assert result.loc["Infrastructure", "share"] == 25.0


def test_overall_causes_expose_the_unallocated_share():
    """Le complément à 100 apparaît comme part non ventilée, sans renormalisation (RI-013)."""
    row = {column: 0.0 for column in CAUSE_COLUMNS}
    row.update({"date": "2026-01-01", "route": "Paris → Lyon", "scheduled": 100, "cancelled": 0, "late_arrival": 10})
    # Deux causes déclarées = 60 % au total -> 40 % non ventilé.
    row["cause_external"] = 40.0
    row["cause_infra"] = 20.0

    result = overall_cause_distribution(pd.DataFrame([row])).set_index("cause")

    assert result.loc["Causes externes", "share"] == 40.0
    assert result.loc["Infrastructure", "share"] == 20.0
    assert result.loc["Part non ventilée dans les données", "share"] == 40.0


def test_overview_highlights_compare_the_latest_three_months_to_the_previous_three():
    rows = []
    for month in range(1, 7):
        late = 10 if month <= 3 else (20 if month <= 5 else 30)
        rows.append(_row(f"2026-{month:02d}-01", scheduled=100, cancelled=0, late=late))
    df = pd.DataFrame(rows)

    result = overview_highlights(df)

    assert result["trend"]["status"] == "bad"
    assert "10.0%" in result["trend"]["text"]
    assert "juin 2026" in result["worst_month"]["text"]
    assert result["dominant_cause"]["title"] == "Cause la plus représentée"
