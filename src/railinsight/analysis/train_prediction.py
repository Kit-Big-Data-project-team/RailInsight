
"""Entraîne et évalue un modèle de prédiction des retards TGV."""

from railinsight.analysis.prediction_model import FEATURES, create_model
from sklearn.metrics import mean_absolute_error

from railinsight.analysis.prepare_prediction import prepare_prediction_data





def main() -> None:
    """Compare une Random Forest à une prédiction de référence."""

    df = prepare_prediction_data()

    # Séparation chronologique : aucune observation future
    # n'est utilisée pour entraîner le modèle.
    train = df[df["date"] < "2025-01-01"]
    test = df[df["date"] >= "2025-01-01"]

    model = create_model()

    model.fit(train[FEATURES], train["late_rate"])

    predictions = model.predict(test[FEATURES]).clip(0, 1)

    # Référence : reprendre le taux observé le mois précédent.
    baseline = test["late_rate_lag1"]

    mae_baseline = mean_absolute_error(
        test["late_rate"], baseline
    )
    mae_model = mean_absolute_error(
        test["late_rate"], predictions
    )

    print("\n===== EVALUATION DU MODELE =====")
    print(f"Observations entraînement : {len(train)}")
    print(f"Observations test : {len(test)}")

    print(
        f"MAE référence : {mae_baseline * 100:.2f} "
        "points de pourcentage"
    )
    print(
        f"MAE Random Forest : {mae_model * 100:.2f} "
        "points de pourcentage"
    )

    if mae_model < mae_baseline:
        print("La Random Forest améliore la référence.")
    else:
        print("La Random Forest ne dépasse pas la référence.")


if __name__ == "__main__":
    main()
