"""Tests des graphiques de la page Vue d'ensemble (sans accès base)."""

import pandas as pd

from railinsight.viz.overview import causes_bar, network_trend_line, seasonality_heatmap


def _monthly() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-02-01"]),
            "late_rate": [0.14, 0.16],
            "cancellation_rate": [0.02, 0.03],
        }
    )


def test_network_trend_line_has_late_and_cancellation_series():
    fig = network_trend_line(_monthly())

    assert len(fig.data) == 2


def test_network_trend_line_empty_is_blank():
    assert len(network_trend_line(pd.DataFrame()).data) == 0


def test_causes_bar_has_one_trace_per_cause():
    df = pd.DataFrame({"cause": ["Infrastructure", "Causes externes"], "share": [25.0, 75.0]})
    fig = causes_bar(df)

    assert len(fig.data) == 2


def test_causes_bar_empty_is_blank():
    assert len(causes_bar(pd.DataFrame()).data) == 0


def test_seasonality_heatmap_has_one_trace():
    fig = seasonality_heatmap(_monthly())

    assert len(fig.data) == 1
    assert fig.data[0].type == "heatmap"


def test_seasonality_heatmap_empty_is_blank():
    assert len(seasonality_heatmap(pd.DataFrame()).data) == 0
