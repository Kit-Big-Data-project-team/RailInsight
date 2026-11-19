"""Tests des graphiques de la prévision avec intervalles (sans entraînement de modèle)."""

import pandas as pd
import pytest

from railinsight.viz.forecast_intervals import backtest_error_line, forecast_interval_chart


def test_backtest_error_line_has_two_series():
    backtest = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-02-01"]),
            "mae_model": [0.10, 0.12],
            "mae_baseline": [0.15, 0.14],
            "n": [10, 20],
        }
    )
    fig = backtest_error_line(backtest)

    assert len(fig.data) == 2


def test_forecast_interval_chart_has_history_and_forecast():
    history = pd.DataFrame({"date": pd.to_datetime(["2025-01-01", "2025-02-01"]), "late_rate": [0.14, 0.16]})
    forecast = {"date": pd.Timestamp("2025-03-01"), "low": 0.10, "median": 0.15, "high": 0.20}

    fig = forecast_interval_chart(history, forecast)

    assert len(fig.data) == 2
    # La prévision porte une barre d'incertitude asymétrique.
    assert fig.data[1].error_y.array[0] == pytest.approx(0.05)
