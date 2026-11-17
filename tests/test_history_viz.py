"""Tests de lisibilité des trois indicateurs historiques."""

import pandas as pd
import pytest

from railinsight.analysis.history import CAUSE_COLUMNS, cause_breakdown_over_time, monthly_delays_cancellations
from railinsight.viz.history import cause_area, delays_cancellations_line, seasonality_bar, service_line, severity_area


def test_three_rates_use_percentages_and_explicit_populations():
    """Vérifie les valeurs tracées et empêche une présentation additive trompeuse."""
    df = pd.DataFrame({"date": pd.to_datetime(["2026-01-01"]), "scheduled": [100], "cancelled": [10], "late_arrival": [18]})
    fig = delays_cancellations_line(monthly_delays_cancellations(df))
    traces = {trace.name: trace for trace in fig.data}
    assert len(traces) == 3
    assert traces["Retards / trains ayant circulé"].y[0] == pytest.approx(0.20)
    assert traces["Annulations / trains prévus"].y[0] == pytest.approx(0.10)
    assert traces["Perturbations / trains prévus"].y[0] == pytest.approx(0.28)
    assert fig.layout.yaxis.tickformat == ".0%"
    assert len({trace.line.dash for trace in fig.data}) == 3
    assert all(not trace.stackgroup for trace in fig.data)
    assert all(".1%" in trace.hovertemplate for trace in fig.data)


def test_unallocated_cause_is_grey_and_zero_delay_month_is_explicit():
    """La part non ventilée reste visible et les mois sans retard sont identifiés."""
    df = pd.DataFrame({"date": ["2026-01-01", "2026-02-01"], "late_arrival": [10, 0], **{c: [0.0, 0.0] for c in CAUSE_COLUMNS}})
    fig = cause_area(cause_breakdown_over_time(df))
    grey = next(trace for trace in fig.data if trace.name == "Part non ventilée dans les données")
    assert grey.line.color == "#B4BFCD"
    assert grey.y[0] == 100.0
    assert pd.isna(grey.y[1])
    assert any(annotation.text == "Aucun retard enregistré" for annotation in fig.layout.annotations)
    assert all(not trace.groupnorm for trace in fig.data)


def test_seasonal_bars_are_grouped_and_display_year_counts():
    """Les trois taux restent distincts et les années contributrices sont visibles."""
    df = pd.DataFrame({"month": [1], "late_rate": [0.2], "cancellation_rate": [0.1], "disruption_rate": [0.28], "n_years": [8]})
    fig = seasonality_bar(df)
    assert len(fig.data) == 3
    assert fig.layout.barmode == "group"
    assert fig.data[0].x[0] == "Jan"
    assert fig.data[0].customdata[0][0] == 8
    assert "Années contributrices" in fig.data[0].hovertemplate


def test_severity_preserves_gaps_and_services_format_percentages():
    """Les courbes de sévérité ne relient pas les résultats invalides."""
    df = pd.DataFrame({"date": pd.to_datetime(["2025-01-01", "2025-02-01"]), "late_15": [0.2, 0.1], "late_30": [float("nan"), 0.05], "late_60": [0.01, 0.0]})
    fig = severity_area(df)
    assert all(trace.connectgaps is False for trace in fig.data)
    assert all(not trace.stackgroup for trace in fig.data)
    assert pd.isna(next(trace for trace in fig.data if trace.name == "> 30 min").y[0])
    services = pd.DataFrame({"date": pd.to_datetime(["2025-01-01"]), "service": ["National"], "late_rate": [0.1]})
    assert service_line(services).layout.yaxis.tickformat == ".0%"
