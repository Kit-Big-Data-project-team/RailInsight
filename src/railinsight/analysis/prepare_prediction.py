"""Prépare les taux mensuels par liaison et par service."""

from railinsight.analysis.metrics import monthly_late_rate
from railinsight.data.loader import TGVDataset


def main() -> None:
    df = TGVDataset.from_db().df.copy()

    # Réutilisation de la fonction commune du projet.
    # Chaque groupe correspond à une liaison et à un service.
    results = []

    for (liaison, service), group in df.groupby(
        ["liaison", "service"]
    ):
        monthly = monthly_late_rate(group)
        monthly["liaison"] = liaison
        monthly["service"] = service
        results.append(monthly)

    prediction_data = (
        __import__("pandas").concat(results, ignore_index=True)
        .sort_values(["liaison", "service", "date"])
    )

    # Préparation des variables historiques pour la prédiction
    group = prediction_data.groupby(["liaison", "service"])["late_rate"]

    prediction_data["late_rate_lag1"] = group.shift(1)
    prediction_data["late_rate_lag2"] = group.shift(2)
    prediction_data["late_rate_lag3"] = group.shift(3)

    # Moyenne des trois mois précédents
    prediction_data["late_rate_mean3"] = (
    prediction_data[
        ["late_rate_lag1", "late_rate_lag2", "late_rate_lag3"]
    ].mean(axis=1)
    )

    # Saisonnalité : mois de l'année
    prediction_data["month"] = prediction_data["date"].dt.month

    # Retirer les premières observations sans historique suffisant
    prediction_data = prediction_data.dropna(
    subset=[
        "late_rate_lag1",
        "late_rate_lag2",
        "late_rate_lag3",
    ]
    )

    print("\n===== DONNEES PRETES POUR LE MODELE =====")



    print("Dimensions :", prediction_data.shape)
    print(prediction_data.head(10))

    print("\nTaux de retard :")
    print(prediction_data["late_rate"].describe())


if __name__ == "__main__":
    main()