"""Prévision avec intervalles de confiance et mesure de calibration.

Au lieu d'une prévision ponctuelle (« taux de retard = 14 % »), on fournit une
fourchette (« 14 % [10 % – 19 %] ») via une régression par quantiles, puis on
vérifie que cette incertitude est honnête (calibration sur une période de test).

Construit au-dessus de la préparation des données commune (`prepare_prediction`)
et des mêmes variables que le modèle ponctuel (`prediction_model.FEATURES`).
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from railinsight.analysis.prediction_model import FEATURES

# Quantiles de l'intervalle : médiane encadrée par un intervalle central à 80 %.
QUANTILES = {"low": 0.1, "median": 0.5, "high": 0.9}
INTERVAL_LEVEL = 0.8
BOUND_COLUMNS = ["low", "median", "high"]


def create_quantile_models() -> dict[str, GradientBoostingRegressor]:
    """Crée un modèle de gradient boosting par quantile (10 %, 50 %, 90 %).

    Returns:
        Dictionnaire {nom: modèle} avec une graine fixe pour la reproductibilité.
    """
    return {
        name: GradientBoostingRegressor(loss="quantile", alpha=alpha, n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42)
        for name, alpha in QUANTILES.items()
    }


def fit_quantile_models(train: pd.DataFrame) -> dict[str, GradientBoostingRegressor]:
    """Entraîne les trois modèles de quantiles sur les données fournies.

    Args:
        train: Données préparées contenant FEATURES et la cible ``late_rate``.

    Returns:
        Dictionnaire des modèles entraînés.
    """
    models = create_quantile_models()
    for model in models.values():
        model.fit(train[FEATURES], train["late_rate"])
    return models


def predict_with_interval(models: dict[str, GradientBoostingRegressor], features: pd.DataFrame) -> pd.DataFrame:
    """Prédit la fourchette basse / médiane / haute pour chaque observation.

    Les trois quantiles sont triés par ligne pour garantir ``low <= median <= high``
    (les modèles de quantiles ne sont pas monotones par construction), et bornés à [0, 1].

    Args:
        models: Modèles de quantiles entraînés.
        features: Table des variables explicatives (colonnes FEATURES).

    Returns:
        Tableau avec les colonnes low, median et high, aligné sur l'index d'entrée.
    """
    predictions = pd.DataFrame({name: model.predict(features[FEATURES]).clip(0, 1) for name, model in models.items()}, index=features.index)
    ordered = np.sort(predictions[BOUND_COLUMNS].to_numpy(), axis=1)
    return pd.DataFrame(ordered, columns=BOUND_COLUMNS, index=features.index)


def interval_coverage(df: pd.DataFrame, cutoff: str = "2025-01-01") -> dict[str, object]:
    """Mesure la calibration de l'intervalle sur une période de test chronologique.

    On entraîne avant le ``cutoff`` et on observe, après, la part des vraies valeurs
    tombant dans l'intervalle à 80 %. Une couverture proche de 0,8 indique une
    incertitude honnête ; nettement en dessous = intervalles trop étroits (trop confiants).

    Args:
        df: Données préparées complètes.
        cutoff: Date de séparation entraînement / test (aucune donnée future à l'entraînement).

    Returns:
        Dictionnaire coverage (fraction observée), target (0,8) et n (taille du test).
    """
    train = df[df["date"] < cutoff]
    test = df[df["date"] >= cutoff]
    if train.empty or test.empty:
        return {"coverage": None, "target": INTERVAL_LEVEL, "n": 0}

    bounds = predict_with_interval(fit_quantile_models(train), test)
    truth = test["late_rate"].to_numpy()
    inside = (truth >= bounds["low"].to_numpy()) & (truth <= bounds["high"].to_numpy())
    return {"coverage": float(inside.mean()), "target": INTERVAL_LEVEL, "n": int(len(test))}
