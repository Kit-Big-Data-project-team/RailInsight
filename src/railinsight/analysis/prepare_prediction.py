"""Prépare les données mensuelles pour la prédiction des retards TGV."""

import pandas as pd

from railinsight.analysis.metrics import monthly_late_rate
from railinsight.data.loader import TGVDataset


def get_monthly_prediction_data() -> pd.DataFrame:
    """Récupère les taux mensuels sans supprimer les premiers mois."""

    df = TGVDataset.from_db().df.copy()
    results = []

    for (liaison, service), group in df.groupby(["liaison", "service"]):
        monthly = monthly_late_rate(group)
        monthly["liaison"] = liaison
        monthly["service"] = service
        results.append(monthly)

    return pd.concat(results, ignore_index=True).sort_values(["liaison", "service", "date"]).reset_index(drop=True)


def prepare_prediction_data() -> pd.DataFrame:
    """Prépare les données mensuelles pour entraîner le modèle.

    Charge les données TGV depuis PostgreSQL, calcule le taux
    de retard par liaison et service, puis crée les taux des
    trois mois précédents.

    Écarte les observations sans trois mois consécutifs
    disponibles et ajoute la moyenne historique ainsi que
    le numéro du mois.

    Returns:
        DataFrame contenant les observations et les variables
        nécessaires à l'entraînement du modèle.
    """

    prediction_data = get_monthly_prediction_data()

    group = prediction_data.groupby(["liaison", "service"])["late_rate"]

    # Taux observés lors des trois mois précédents.
    for lag in (1, 2, 3):
        prediction_data[f"late_rate_lag{lag}"] = group.shift(lag)

    # Vérifier que les observations sont bien mensuelles et consécutives.
    periods = prediction_data["date"].dt.to_period("M")
    group_keys = [
        prediction_data["liaison"],
        prediction_data["service"],
    ]

    for lag in (1, 2, 3):
        previous_periods = periods.groupby(group_keys).shift(lag)
        valid = (periods.astype(int) - previous_periods.astype("int64")) == lag

        prediction_data.loc[~valid, f"late_rate_lag{lag}"] = float("nan")

    lag_columns = [
        "late_rate_lag1",
        "late_rate_lag2",
        "late_rate_lag3",
    ]

    prediction_data = prediction_data.dropna(subset=lag_columns).copy()
    prediction_data = prediction_data.dropna(subset=["late_rate"]).copy()

    prediction_data["late_rate_mean3"] = prediction_data[lag_columns].mean(axis=1)

    prediction_data["month"] = prediction_data["date"].dt.month

    return prediction_data


def main() -> None:
    """Affiche un résumé des données préparées."""

    prediction_data = prepare_prediction_data()

    print("\n===== DONNEES PRETES POUR LE MODELE =====")
    print("Dimensions :", prediction_data.shape)
    print(prediction_data.head(10))

    print("\nTaux de retard :")
    print(prediction_data["late_rate"].describe())


if __name__ == "__main__":
    main()
