"""Prépare les données mensuelles pour la prédiction des retards TGV."""

import pandas as pd

from railinsight.analysis.metrics import monthly_late_rate
from railinsight.data.loader import TGVDataset

LAG_COLUMNS = ["late_rate_lag1", "late_rate_lag2", "late_rate_lag3"]


def _load_raw(df: pd.DataFrame | None) -> pd.DataFrame:
    """Retourne les données brutes fournies, ou les charge depuis PostgreSQL."""
    return TGVDataset.from_db().df.copy() if df is None else df.copy()


def monthly_rate_table(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Série mensuelle du taux de retard par liaison et service.

    Contrairement à :func:`prepare_prediction_data`, cette table n'est **pas**
    filtrée sur la disponibilité des trois décalages : elle conserve toutes les
    liaisons, y compris celles qui ne comptent que trois mois d'historique. Elle
    sert à construire le vecteur de prévision du mois suivant (les trois derniers
    taux consécutifs), là où la table d'entraînement exige un quatrième mois.

    Les mois entièrement annulés (taux de retard indéfini) sont exclus : ils ne
    fournissent pas de taux exploitable comme observation récente.

    Args:
        df: Données brutes déjà chargées. Chargées depuis la base si ``None``.

    Returns:
        DataFrame trié par liaison, service et date, colonne ``late_rate`` renseignée.
    """
    raw = _load_raw(df)
    results = []
    for (liaison, service), group in raw.groupby(["liaison", "service"]):
        monthly = monthly_late_rate(group)
        monthly["liaison"] = liaison
        monthly["service"] = service
        results.append(monthly)

    table = pd.concat(results, ignore_index=True).sort_values(["liaison", "service", "date"]).reset_index(drop=True)
    return table.dropna(subset=["late_rate"]).reset_index(drop=True)


def prepare_prediction_data(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Prépare les données mensuelles pour entraîner le modèle.

    Charge les données TGV depuis PostgreSQL (ou réutilise ``df``), calcule le taux
    de retard par liaison et service, puis crée les taux des trois mois précédents.

    Écarte les observations sans trois mois consécutifs disponibles, ainsi que les
    mois entièrement annulés (taux cible indéfini, qui feraient échouer l'entraînement),
    et ajoute la moyenne historique ainsi que le numéro du mois.

    Args:
        df: Données brutes déjà chargées. Chargées depuis la base si ``None``.

    Returns:
        DataFrame contenant les observations et les variables nécessaires à l'entraînement.
    """
    prediction_data = monthly_rate_table(df)

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

    # On exige les trois décalages et une cible définie : un mois entièrement annulé
    # (late_rate manquant) ne doit pas servir d'exemple d'entraînement.
    prediction_data = prediction_data.dropna(subset=LAG_COLUMNS + ["late_rate"]).copy()

    prediction_data["late_rate_mean3"] = prediction_data[LAG_COLUMNS].mean(axis=1)

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
