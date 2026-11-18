
"""Page Streamlit : prédiction des taux de retard TGV."""

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


@st.cache_data(show_spinner="Chargement et entraînement du modèle...")
def load_predictions() -> tuple[pd.DataFrame, float, float]:
    """Prépare les données, entraîne le modèle et évalue les prédictions."""

    df = prepare_prediction_data()

    train = df[df["date"] < "2025-01-01"]
    test = df[df["date"] >= "2025-01-01"].copy()

    if train.empty or test.empty:
        raise ValueError("Données insuffisantes pour entraîner ou tester le modèle.")

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(train[FEATURES], train["late_rate"])

    test["prediction"] = model.predict(test[FEATURES]).clip(0, 1)
    test["baseline"] = test["late_rate_lag1"]

    mae_model = mean_absolute_error(
        test["late_rate"], test["prediction"]
    )
    mae_baseline = mean_absolute_error(
        test["late_rate"], test["baseline"]
    )

    return test, mae_model, mae_baseline


st.title("Prédiction des retards TGV")
st.write(
    "Comparaison des taux de retard mensuels observés et prédits "
    "par un modèle Random Forest."
)

try:
    test, mae_model, mae_baseline = load_predictions()
except Exception as exc:
    st.error(f"Impossible de charger les prédictions : {exc}")
    st.stop()

st.subheader("Performance globale du modèle")

col1, col2 = st.columns(2)

col1.metric(
    "Erreur moyenne Random Forest",
    f"{mae_model * 100:.2f} points",
)

col2.metric(
    "Erreur moyenne de référence",
    f"{mae_baseline * 100:.2f} points",
)

st.caption(
    "Évaluation sur les données de 2025 à septembre 2026. "
    "Plus l'erreur moyenne est faible, meilleure est la prédiction."
)

st.subheader("Prédictions par liaison")

liaison = st.selectbox(
    "Choisir une liaison",
    sorted(test["liaison"].unique()),
)

services = sorted(
    test.loc[test["liaison"] == liaison, "service"].unique()
)

service = st.selectbox("Service", services)

selection = (
    test[
        (test["liaison"] == liaison)
        & (test["service"] == service)
    ]
    .sort_values("date")
    .copy()
)

if selection.empty:
    st.info("Aucune donnée disponible pour cette sélection.")
    st.stop()

chart_data = selection.set_index("date")[
    ["late_rate", "prediction", "baseline"]
].rename(
    columns={
        "late_rate": "Taux observé",
        "prediction": "Random Forest",
        "baseline": "Référence",
    }
) * 100

st.line_chart(chart_data, y_label="Taux de retard (%)")

local_mae = mean_absolute_error(
    selection["late_rate"],
    selection["prediction"],
)

st.metric(
    "Erreur moyenne sur cette liaison",
    f"{local_mae * 100:.2f} points",
)

st.caption(
    "Les prédictions affichées concernent des mois déjà observés. "
    "Pour chaque mois, le modèle utilise les taux des trois mois "
    "précédents. Ce graphique sert à évaluer le modèle, "
    "pas encore à prévoir un mois futur."
)

with st.expander("Voir les données détaillées"):
    details = selection[
        ["date", "late_rate", "prediction", "baseline"]
    ].copy()

    for column in ["late_rate", "prediction", "baseline"]:
        details[column] = (details[column] * 100).round(2)

    st.dataframe(
        details.rename(
            columns={
                "date": "Mois",
                "late_rate": "Observé (%)",
                "prediction": "Prédit (%)",
                "baseline": "Référence (%)",
            }
        ),
        hide_index=True,
    )
