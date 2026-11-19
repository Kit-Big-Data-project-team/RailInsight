"""Backtesting glissant (walk-forward) de la prévision des retards.

Plutôt qu'une seule coupure entraînement/test, on rejoue la prévision mois par
mois : pour chaque mois récent, on entraîne sur TOUT l'historique antérieur et on
prédit ce mois. Cela donne une mesure de performance bien plus robuste (série
d'erreurs dans le temps) et évite de conclure sur un unique découpage favorable.

Aucune donnée future n'entre jamais dans l'entraînement d'un mois donné.
"""

import pandas as pd
from sklearn.metrics import mean_absolute_error

from railinsight.analysis.prediction_model import FEATURES, create_model


def walk_forward_backtest(df: pd.DataFrame, n_months: int = 12) -> pd.DataFrame:
    """Rejoue la prévision sur les ``n_months`` derniers mois disponibles.

    Pour chaque mois retenu : entraînement sur les observations strictement
    antérieures, prédiction du mois, puis erreur absolue moyenne comparée à la
    référence « reprendre le taux du mois précédent » (late_rate_lag1).

    Args:
        df: Données préparées (FEATURES, late_rate, date, late_rate_lag1).
        n_months: Nombre de derniers mois à évaluer.

    Returns:
        Tableau date, mae_model, mae_baseline, n (observations du mois).
        Les mois sans historique d'entraînement suffisant sont ignorés.
    """
    months = sorted(pd.to_datetime(df["date"]).unique())
    cutoffs = months[-n_months:]
    rows = []
    for month in cutoffs:
        train = df[df["date"] < month]
        test = df[df["date"] == month]
        if train.empty or test.empty:
            continue
        model = create_model()
        model.fit(train[FEATURES], train["late_rate"])
        predictions = model.predict(test[FEATURES]).clip(0, 1)
        rows.append(
            {
                "date": month,
                "mae_model": mean_absolute_error(test["late_rate"], predictions),
                "mae_baseline": mean_absolute_error(test["late_rate"], test["late_rate_lag1"]),
                "n": int(len(test)),
            }
        )
    return pd.DataFrame(rows, columns=["date", "mae_model", "mae_baseline", "n"])


def backtest_summary(backtest: pd.DataFrame) -> dict[str, object]:
    """Agrège un backtest en erreurs globales pondérées par le volume de chaque mois.

    Args:
        backtest: Sortie de :func:`walk_forward_backtest`.

    Returns:
        Dictionnaire mae_model, mae_baseline (pondérées) et n_months. Valeurs None
        si le backtest est vide.
    """
    if backtest.empty:
        return {"mae_model": None, "mae_baseline": None, "n_months": 0}
    weights = backtest["n"]
    return {
        "mae_model": float((backtest["mae_model"] * weights).sum() / weights.sum()),
        "mae_baseline": float((backtest["mae_baseline"] * weights).sum() / weights.sum()),
        "n_months": int(len(backtest)),
    }
