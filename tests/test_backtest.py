"""Tests du backtesting glissant de la prévision."""

import pandas as pd

from railinsight.analysis.backtest import backtest_summary, walk_forward_backtest
from test_forecast_intervals import prepared


def test_walk_forward_backtest_shape_and_counts():
    backtest = walk_forward_backtest(prepared(months=20, routes=2), n_months=4)

    assert list(backtest.columns) == ["date", "mae_model", "mae_baseline", "n"]
    assert len(backtest) <= 4
    assert (backtest["n"] > 0).all()
    assert (backtest["mae_model"] >= 0).all()


def test_backtest_summary_weights_by_month_volume():
    backtest = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-01", "2025-02-01"]),
            "mae_model": [0.10, 0.20],
            "mae_baseline": [0.15, 0.25],
            "n": [10, 30],
        }
    )
    summary = backtest_summary(backtest)

    assert summary["n_months"] == 2
    assert summary["mae_model"] == (0.10 * 10 + 0.20 * 30) / 40
    assert summary["mae_baseline"] == (0.15 * 10 + 0.25 * 30) / 40


def test_backtest_summary_empty_is_unavailable():
    summary = backtest_summary(pd.DataFrame(columns=["date", "mae_model", "mae_baseline", "n"]))

    assert summary["n_months"] == 0
    assert summary["mae_model"] is None
