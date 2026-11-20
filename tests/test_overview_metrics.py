"""Tests des métriques et observations de la page Vue d'ensemble (cas limites inclus)."""

import pandas as pd

from railinsight.analysis.history import CAUSE_COLUMNS
from railinsight.analysis.overview import (
    format_month_fr,
    global_kpis,
    latest_month_kpis,
    monthly_network_rates,
    overall_cause_distribution,
    overview_highlights,
)


def _row(date: str, scheduled: int, cancelled: int, late: int, cause: str | None = "cause_external") -> dict:
    row = {column: 0.0 for column in CAUSE_COLUMNS}
    row.update({"date": date, "route": "Paris → Lyon", "scheduled": scheduled, "cancelled": cancelled, "late_arrival": late})
    if cause is not None:
        row[cause] = 100.0
    return row


def _months(rates: list[int], cause: str | None = "cause_external") -> pd.DataFrame:
    return pd.DataFrame([_row(f"2026-{i + 1:02d}-01", scheduled=100, cancelled=0, late=late, cause=cause) for i, late in enumerate(rates)])


def test_global_kpis_summarise_the_whole_dataset():
    df = pd.DataFrame([_row("2026-01-01", 100, 10, 18), _row("2026-02-01", 100, 0, 12)])
    kpis = global_kpis(df)

    assert kpis["n_routes"] == 1
    assert kpis["scheduled"] == 200
    assert kpis["late_rate"] == 30 / 190
    assert kpis["cancellation_rate"] == 10 / 200


def test_monthly_network_rates_empty_is_blank():
    assert monthly_network_rates(pd.DataFrame()).empty


def test_latest_month_kpis_empty_returns_blank_fields():
    result = latest_month_kpis(pd.DataFrame())
    assert result["late_rate"] is None
    assert result["late_delta"] is None


def test_latest_month_kpis_without_previous_month_has_no_delta():
    df = pd.DataFrame([_row("2026-05-01", 100, 0, 15)])
    result = latest_month_kpis(df)

    assert result["late_rate"] == 15 / 100
    assert result["late_delta"] is None
    assert result["cancellation_delta"] is None


def test_overall_cause_distribution_empty_is_blank():
    assert overall_cause_distribution(pd.DataFrame()).empty


def test_overall_cause_distribution_without_late_trains_is_blank():
    df = _months([0, 0])  # aucun retard => poids total nul
    assert overall_cause_distribution(df).empty


def test_format_month_fr_handles_missing_value():
    assert format_month_fr(None) == "—"
    assert format_month_fr(pd.NaT) == "—"
    assert format_month_fr("2026-06-01") == "juin 2026"


def test_overview_highlights_empty_uses_defaults():
    highlights = overview_highlights(pd.DataFrame())
    assert highlights["trend"]["status"] == "neutral"
    assert highlights["dominant_cause"]["title"] == "Cause la plus représentée"


def test_overview_highlights_detects_an_improvement():
    df = _months([30, 30, 30, 10, 10, 10])
    highlights = overview_highlights(df)

    assert highlights["trend"]["status"] == "good"
    assert "worst_month" in highlights
    assert highlights["dominant_cause"]["text"].startswith("Causes externes")


def test_overview_highlights_reports_a_stable_trend():
    df = _months([12, 12, 12, 12, 12, 12])
    assert overview_highlights(df)["trend"]["status"] == "neutral"


def test_overview_highlights_without_declared_causes():
    # Des retards existent mais aucune cause n'est ventilée : pas de cause dominante.
    df = _months([10, 10, 10, 10, 10, 10], cause=None)
    highlights = overview_highlights(df)

    assert highlights["dominant_cause"]["title"] == "Causes des retards"
