"""Page Streamlit : prévision et évaluation des retards TGV."""

import pandas as pd
import pydeck as pdk
import streamlit as st
from sklearn.metrics import mean_absolute_error

from railinsight.analysis.forecast import get_recent_rates
from railinsight.analysis.prediction_model import FEATURES, create_model
from railinsight.analysis.prepare_prediction import get_monthly_prediction_data, prepare_prediction_data
from railinsight.viz.station_map import get_station_coordinates


@st.cache_data(show_spinner="Calcul des prédictions...")
def load_predictions():
    """Évalue le modèle et calcule les prévisions du mois suivant.

    Entraîne une Random Forest sur les données antérieures à 2025
    pour mesurer ses performances sur la période de test.

    Réentraîne ensuite un modèle sur toutes les données disponibles
    afin de prévoir le mois suivant, pour chaque liaison disposant
    de trois mois récents consécutifs.

    Returns:
        tuple:
            - test : données de test avec les prédictions historiques.
            - forecasts : prévisions du prochain mois par liaison.
            - mae_model : erreur absolue moyenne de la Random Forest.
            - mae_baseline : erreur absolue moyenne de la référence.
    """
    df = prepare_prediction_data()
    monthly_df = get_monthly_prediction_data()

    # Évaluation historique : entraînement avant 2025.
    train = df[df["date"] < "2025-01-01"]
    test = df[df["date"] >= "2025-01-01"].copy()

    evaluation_model = create_model()
    evaluation_model.fit(train[FEATURES], train["late_rate"])

    test["prediction"] = evaluation_model.predict(test[FEATURES]).clip(0, 1)
    test["baseline"] = test["late_rate_lag1"]

    mae_model = mean_absolute_error(test["late_rate"], test["prediction"])
    mae_baseline = mean_absolute_error(test["late_rate"], test["baseline"])

    # Prévision future : réentraînement avec toutes les données.
    future_model = create_model()
    future_model.fit(df[FEATURES], df["late_rate"])

    latest_month = monthly_df["date"].max().to_period("M")
    next_month = latest_month + 1

    forecasts = []

    for (liaison, service), group in monthly_df.groupby(["liaison", "service"]):
        group = group.sort_values("date")

        rates = get_recent_rates(group, latest_month)

        if rates is None:
            continue

        future_features = pd.DataFrame(
            [
                {
                    "late_rate_lag1": rates[-1],
                    "late_rate_lag2": rates[-2],
                    "late_rate_lag3": rates[-3],
                    "late_rate_mean3": sum(rates) / 3,
                    "month": next_month.month,
                }
            ]
        )

        predicted_rate = float(future_model.predict(future_features)[0])
        predicted_rate = max(0.0, min(1.0, predicted_rate))

        forecasts.append(
            {
                "liaison": liaison,
                "service": service,
                "forecast_date": next_month.to_timestamp(),
                "forecast_rate": predicted_rate,
                "last_observed_rate": rates[-1],
            }
        )

    return (
        test,
        pd.DataFrame(forecasts),
        mae_model,
        mae_baseline,
    )


st.title("Prédiction des retards TGV par liaison")

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
    st.warning("Aucune liaison ne dispose de trois mois récents " "consécutifs pour établir une prévision.")
else:
    liaison = st.selectbox(
        "Choisir une liaison",
        sorted(forecasts["liaison"].unique()),
    )

    services = sorted(forecasts.loc[forecasts["liaison"] == liaison, "service"].unique())
    service = st.selectbox("Service", services)
    st.subheader("Carte de la liaison")

    # Le champ liaison contient le départ et l'arrivée.
    parts = liaison.split("->")

    if len(parts) == 2:
        departure, arrival = [part.strip() for part in parts]

        start_coords = get_station_coordinates(departure)
        end_coords = get_station_coordinates(arrival)

        if start_coords is not None and end_coords is not None:
            stations = pd.DataFrame(
                [
                    {
                        "lat": start_coords[0],
                        "lon": start_coords[1],
                        "size": 150,
                    },
                    {
                        "lat": end_coords[0],
                        "lon": end_coords[1],
                        "size": 150,
                    },
                ]
            )

            route = pd.DataFrame(
                [
                    {
                        "start_lon": start_coords[1],
                        "start_lat": start_coords[0],
                        "end_lon": end_coords[1],
                        "end_lat": end_coords[0],
                    }
                ]
            )

            points_layer = pdk.Layer(
                "ScatterplotLayer",
                data=stations,
                get_position="[lon, lat]",
                get_radius=800,
                get_fill_color=[20, 110, 210, 220],
                pickable=True,
            )

            route_layer = pdk.Layer(
                "LineLayer",
                data=route,
                get_source_position="[start_lon, start_lat]",
                get_target_position="[end_lon, end_lat]",
                get_color=[230, 80, 60],
                get_width=5,
                get_width_units="pixels",
            )

            # Adapter le zoom à la distance entre les deux gares.
            lat_diff = abs(start_coords[0] - end_coords[0])
            lon_diff = abs(start_coords[1] - end_coords[1])
            max_diff = max(lat_diff, lon_diff)

            if max_diff > 5:
                zoom = 5
            elif max_diff > 2:
                zoom = 6
            elif max_diff > 1:
                zoom = 7
            else:
                zoom = 8

            view_state = pdk.ViewState(
                latitude=(start_coords[0] + end_coords[0]) / 2,
                longitude=(start_coords[1] + end_coords[1]) / 2,
                zoom=zoom,
            )

            st.pydeck_chart(
                pdk.Deck(
                    layers=[route_layer, points_layer],
                    initial_view_state=view_state,
                    map_style="light",
                )
            )

            st.caption("Ligne droite indicative entre les deux gares, " "et non tracé réel des voies SNCF.")
            st.caption(f"Départ : {departure} | Arrivée : {arrival}")
        else:
            st.pydeck_chart(
                pdk.Deck(
                    layers=[],
                    initial_view_state=pdk.ViewState(
                        latitude=46.6,
                        longitude=2.5,
                        zoom=5,
                    ),
                    map_style="light",
                )
            )
            st.warning("La carte reste disponible, mais les coordonnées " "de cette liaison ne sont pas encore renseignées.")

    forecast_row = forecasts[(forecasts["liaison"] == liaison) & (forecasts["service"] == service)].iloc[0]

    forecast_date = forecast_row["forecast_date"]
    forecast_rate = forecast_row["forecast_rate"]
    previous_rate = forecast_row["last_observed_rate"]

    st.subheader(f"Prévision pour {forecast_date.strftime('%m/%Y')}")

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

    st.caption("Prévision calculée à partir des trois derniers " "mois observés. Le modèle a été réentraîné sur " "toutes les données disponibles.")

    # Historique récent et point de prévision future.
    historical = test[(test["liaison"] == liaison) & (test["service"] == service)].sort_values("date").tail(12)

    history_chart = historical[["date", "late_rate"]].copy()
    history_chart["observed"] = history_chart["late_rate"] * 100
    history_chart["forecast"] = float("nan")

    # Relier visuellement la prévision au dernier mois observé.
    if not history_chart.empty:
        history_chart.loc[history_chart.index[-1], "forecast"] = history_chart.iloc[-1]["observed"]

    future_point = pd.DataFrame(
        [
            {
                "date": forecast_date,
                "observed": float("nan"),
                "forecast": forecast_rate * 100,
            }
        ]
    )

    chart = pd.concat(
        [
            history_chart[["date", "observed", "forecast"]],
            future_point,
        ],
        ignore_index=True,
    ).set_index("date")

    st.line_chart(
        chart.rename(
            columns={
                "observed": "Taux observé",
                "forecast": "Prévision future",
            }
        ),
        y_label="Taux de retard (%)",
    )

    st.caption("La courbe de prévision se prolonge après " "le dernier mois observé. La valeur future " "n'est pas encore vérifiée par les données SNCF.")


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

improvement = (mae_baseline - mae_model) / mae_baseline * 100 if mae_baseline > 0 else 0

if improvement > 0:
    st.success(f"La Random Forest réduit l'erreur moyenne " f"de {improvement:.1f} % par rapport à la référence.")
else:
    st.warning("La Random Forest ne fait pas mieux que " "la méthode de référence sur cette période.")

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
    evaluation = test[(test["liaison"] == liaison) & (test["service"] == service)].copy()

evaluation = evaluation.sort_values("date")

if evaluation.empty:
    st.info("Pas de données de test pour cette liaison.")
else:
    chart_data = (
        evaluation.set_index("date")[["late_rate", "prediction", "baseline"]].rename(
            columns={
                "late_rate": "Taux observé",
                "prediction": "Random Forest",
                "baseline": "Référence",
            }
        )
        * 100
    )

    st.line_chart(
        chart_data,
        y_label="Taux de retard (%)",
    )

    st.markdown("""
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
        """)

    with st.expander("Voir les données détaillées"):
        details = evaluation[["date", "late_rate", "prediction", "baseline"]].copy()

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
