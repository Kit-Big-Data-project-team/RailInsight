"""Tests du modèle ponctuel et de son script d'évaluation (nécessitent scikit-learn)."""

from unittest.mock import patch

import numpy as np
import pandas as pd

from railinsight.analysis import train_prediction
from railinsight.analysis.prediction_model import FEATURES, create_model


def _prepared(n: int = 36) -> pd.DataFrame:
    """Jeu préparé synthétique couvrant 2023–2025 (entraînement < 2025, test ≥ 2025)."""
    dates = pd.period_range("2023-01", periods=n, freq="M").to_timestamp()
    rng = np.random.default_rng(0)
    series = np.clip(0.2 + rng.normal(0, 0.03, n + 3), 0, 1)
    rows = [
        {
            "date": dates[i],
            "late_rate": series[i + 3],
            "late_rate_lag1": series[i + 2],
            "late_rate_lag2": series[i + 1],
            "late_rate_lag3": series[i],
            "late_rate_mean3": series[i : i + 3].mean(),
            "month": dates[i].month,
        }
        for i in range(n)
    ]
    return pd.DataFrame(rows)


def test_create_model_is_a_configured_random_forest():
    model = create_model()
    assert model.n_estimators == 100
    assert model.max_depth == 8
    assert model.random_state == 42


def test_features_are_the_expected_predictors():
    assert FEATURES == ["late_rate_lag1", "late_rate_lag2", "late_rate_lag3", "late_rate_mean3", "month"]


def test_train_prediction_main_prints_an_evaluation(capsys):
    with patch.object(train_prediction, "prepare_prediction_data", return_value=_prepared()):
        train_prediction.main()

    output = capsys.readouterr().out
    assert "EVALUATION DU MODELE" in output
    assert "MAE" in output
