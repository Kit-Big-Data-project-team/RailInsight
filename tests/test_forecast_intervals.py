"""Tests de la prévision avec intervalles et de la calibration."""

import numpy as np
import pandas as pd

from railinsight.analysis.forecast_intervals import create_quantile_models, fit_quantile_models, interval_coverage, predict_with_interval


def prepared(months: int = 30, routes: int = 3, seed: int = 0) -> pd.DataFrame:
    """Jeu de données préparé synthétique (lags consécutifs, cible bornée)."""
    rng = np.random.default_rng(seed)
    dates = pd.period_range("2023-01", periods=months, freq="M").to_timestamp()
    rows = []
    for route in range(routes):
        series = np.clip(rng.uniform(0.1, 0.3) + rng.normal(0, 0.03, months), 0, 1)
        for i in range(3, months):
            rows.append(
                {
                    "date": dates[i],
                    "liaison": f"R{route}",
                    "service": "National",
                    "late_rate": series[i],
                    "late_rate_lag1": series[i - 1],
                    "late_rate_lag2": series[i - 2],
                    "late_rate_lag3": series[i - 3],
                    "late_rate_mean3": series[i - 3 : i].mean(),
                    "month": dates[i].month,
                }
            )
    return pd.DataFrame(rows)


def test_create_quantile_models_has_three_quantiles():
    assert set(create_quantile_models()) == {"low", "median", "high"}


def test_predict_with_interval_is_ordered_and_bounded():
    df = prepared()
    bounds = predict_with_interval(fit_quantile_models(df), df)

    assert (bounds["low"] <= bounds["median"]).all()
    assert (bounds["median"] <= bounds["high"]).all()
    assert (bounds["low"] >= 0).all()
    assert (bounds["high"] <= 1).all()


def test_interval_coverage_returns_a_valid_fraction():
    cov = interval_coverage(prepared(), cutoff="2024-07-01")

    assert cov["target"] == 0.8
    assert cov["n"] > 0
    assert 0.0 <= cov["coverage"] <= 1.0


def test_interval_coverage_without_test_period_is_unavailable():
    cov = interval_coverage(prepared(), cutoff="2030-01-01")

    assert cov["coverage"] is None
    assert cov["n"] == 0
