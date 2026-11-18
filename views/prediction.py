
"""Page Streamlit : prévision et évaluation des retards TGV."""

import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from railinsight.analysis.prepare_prediction import prepare_prediction_data


FEATURES = [
    "late_rate_lag1",
    "late_rate_lag2",
    "late_rate_lag3",
    "late_rate_mean3",
    "month",
]


def create_model():
    return RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )


@st.cache_data(show_spinner="Calcul des prédictions...")
def load_predictions():
    df = prepare_prediction_data()

    # Évaluation historique : entraînement avant 2025.
    train = df[df["date"] < "2025-01-01"]
    test = df[df["date"] >= "2025-01-01"].copy()

    evaluation_model = create_model()
    evaluation_model.fit(train[FEATURES], train["late_rate"])

    test["prediction"] = (
        evaluation_model.predict(test[FEATURES]).clip(0, 1)
    )
    test["baseline"] = test["late_rate_lag1"]

    mae_model = mean_absolute_error(
        test["late_rate"], test["prediction"]
    )
    mae_baseline = mean_absolute_error(
        test["late_rate"], test["baseline"]
    )

    # Prévision future : réentraînement avec toutes les données.
    future_model = create_model()
    future_model.fit(df[FEATURES], df["late_rate"])

    latest_month = df["date"].max().to_period("M")
    next_month = latest_month + 1

    forecasts = []

    for (liaison, service), group in df.groupby(
        ["liaison", "service"]
    ):
        group = group.sort_values("date")
        recent = group.tail(3)

        # On exige trois mois récents consécutifs.
        expected_months = [
            latest_month - 2,
            latest_month - 1,
            latest_month,
        ]
        actual_months = list(
            recent["date"].dt.to_period("M")
        )

        if actual_months != expected_months:
            continue

        rates = recent["late_rate"].tolist()

        future_features = pd.DataFrame([{
            "late_rate_lag1": rates[-1],
            "late_rate_lag2": rates[-2],
            "late_rate_lag3": rates[-3],
            "late_rate_mean3": sum(rates) / 3,
            "month": next_month.month,
        }])

        predicted_rate = float(
            future_model.predict(future_features)[0]
        )
        predicted_rate = max(0.0, min(1.0, predicted_rate))

        forecasts.append({
            "liaison": liaison,
            "service": service,
            "forecast_date": next_month.to_timestamp(),
            "forecast_rate": predicted_rate,
            "last_observed_rate": rates[-1],
        })

    return (
        test,
        pd.DataFrame(forecasts),
        mae_model,
        mae_baseline,
    )


st.title("Prédiction des retards TGV")

st.write(
    "Cette page utilise un modèle de machine learning "
    "(Random Forest) pour estimer la proportion de trains "
    "qui arriveront en retard sur une liaison donnée."
)

try:
    test, forecasts, mae_model, mae_baseline = load_predictions()
except Exception as exc:
    st.error(f"Erreur lors du calcul : {exc}")
    st.stop()


# SECTION 1 : PRÉVISION FUTURE

st.header("1. Prévision du prochain mois")

if forecasts.empty:
    st.warning(
        "Aucune liaison ne dispose de trois mois récents "
        "consécutifs pour établir une prévision."
    )
else:
    liaison = st.selectbox(
        "Choisir une liaison",
        sorted(forecasts["liaison"].unique()),
    )

    services = sorted(
        forecasts.loc[
            forecasts["liaison"] == liaison, "service"
        ].unique()
    )
    service = st.selectbox("Service", services)

    forecast_row = forecasts[
        (forecasts["liaison"] == liaison)
        & (forecasts["service"] == service)
    ].iloc[0]

    forecast_date = forecast_row["forecast_date"]
    forecast_rate = forecast_row["forecast_rate"]
    previous_rate = forecast_row["last_observed_rate"]

    st.subheader(
        f"Prévision pour {forecast_date.strftime('%m/%Y')}"
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Taux de retard prédit",
        f"{forecast_rate * 100:.1f} %",
    )

    col2.metric(
        "Dernier taux observé",
        f"{previous_rate * 100:.1f} %",
    )

    st.info(
        "Le taux prédit représente la proportion estimée "
        "de trains arrivant en retard sur cette liaison "
        "pendant le mois indiqué. Ce n'est pas la probabilité "
        "de retard d'un train individuel."
    )

    st.caption(
        "Prévision calculée à partir des trois derniers "
        "mois observés. Le modèle a été réentraîné sur "
        "toutes les données disponibles."
    )

    # Historique récent et point de prévision future.
    historical = test[
        (test["liaison"] == liaison)
        & (test["service"] == service)
    ].sort_values("date").tail(12)

    history_chart = historical[
        ["date", "late_rate"]
    ].copy()
    history_chart["observed"] = (
        history_chart["late_rate"] * 100
    )
    history_chart["forecast"] = float("nan")

    # Relier visuellement la prévision au dernier mois observé.
    if not history_chart.empty:
        history_chart.loc[
            history_chart.index[-1], "forecast"
        ] = history_chart.iloc[-1]["observed"]

    future_point = pd.DataFrame([{
        "date": forecast_date,
        "observed": float("nan"),
        "forecast": forecast_rate * 100,
    }])

    chart = pd.concat(
        [
            history_chart[["date", "observed", "forecast"]],
            future_point,
        ],
        ignore_index=True,
    ).set_index("date")

    st.line_chart(
        chart.rename(columns={
            "observed": "Taux observé",
            "forecast": "Prévision future",
        }),
        y_label="Taux de retard (%)",
    )

    st.caption(
        "La courbe de prévision se prolonge après "
        "le dernier mois observé. La valeur future "
        "n'est pas encore vérifiée par les données SNCF."
    )


# SECTION 2 : ÉVALUATION HISTORIQUE

st.divider()
st.header("2. Comment évaluer notre modèle ?")

st.write(
    "Avant de prévoir un mois futur, nous avons entraîné "
    "la Random Forest sur les données de 2018 à 2024, "
    "puis testé ses prédictions sur les mois de 2025 "
    "à septembre 2026."
)

st.write(
    "**La référence** est une méthode simple : elle prédit "
    "que le taux de retard sera identique à celui du mois "
    "précédent. Elle sert à vérifier si le machine learning "
    "apporte une réelle amélioration."
)

col1, col2 = st.columns(2)

col1.metric(
    "Erreur moyenne Random Forest",
    f"{mae_model * 100:.2f} points de %",
)

col2.metric(
    "Erreur moyenne de référence",
    f"{mae_baseline * 100:.2f} points de %",
)

improvement = (
    (mae_baseline - mae_model) / mae_baseline * 100
    if mae_baseline > 0
    else 0
)

if improvement > 0:
    st.success(
        f"La Random Forest réduit l'erreur moyenne "
        f"de {improvement:.1f} % par rapport à la référence."
    )
else:
    st.warning(
        "La Random Forest ne fait pas mieux que "
        "la méthode de référence sur cette période."
    )

st.caption(
    "Une erreur de 4,51 points de pourcentage signifie "
    "par exemple que le modèle peut prédire 15 % "
    "alors que le taux réel est de 19,51 %. "
    "Il s'agit d'une erreur moyenne, pas d'une "
    "marge de confiance garantie."
)

st.subheader("Historique : taux observés et prédits")

if forecasts.empty:
    evaluation = test.copy()
else:
    evaluation = test[
        (test["liaison"] == liaison)
        & (test["service"] == service)
    ].copy()

evaluation = evaluation.sort_values("date")

if evaluation.empty:
    st.info("Pas de données de test pour cette liaison.")
else:
    chart_data = evaluation.set_index("date")[
        ["late_rate", "prediction", "baseline"]
    ].rename(columns={
        "late_rate": "Taux observé",
        "prediction": "Random Forest",
        "baseline": "Référence",
    }) * 100

    st.line_chart(
        chart_data,
        y_label="Taux de retard (%)",
    )

    st.markdown(
        """
        **Comment lire ce graphique ?**

        - **Taux observé** : ce qui s'est réellement passé.
        - **Random Forest** : ce que notre modèle avait prédit.
        - **Référence** : le taux du mois précédent, utilisé
          comme prédiction simple.

        Plus la courbe Random Forest est proche de la courbe
        observée, plus la prédiction est précise.

        Les prédictions de ce graphique portent sur des mois
        déjà connus : elles servent à mesurer les performances
        du modèle, contrairement à la prévision future affichée
        dans la première section.
        """
    )

    with st.expander("Voir les données détaillées"):
        details = evaluation[
            ["date", "late_rate", "prediction", "baseline"]
        ].copy()

        for column in [
            "late_rate", "prediction", "baseline"
        ]:
            details[column] = (
                details[column] * 100
            ).round(2)

        st.dataframe(
            details.rename(columns={
                "date": "Mois",
                "late_rate": "Observé (%)",
                "prediction": "Prédit (%)",
                "baseline": "Référence (%)",
            }),
            hide_index=True,
        )
