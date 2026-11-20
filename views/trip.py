"""Page Mon trajet : fréquences historiques, évolution et comparaison des directions."""

import logging

import pandas as pd
import streamlit as st

from railinsight.analysis.trip import (
    average_causes,
    filter_trip_period,
    outcomes_per_100,
    recent_trip_evolution,
    reverse_trip_comparison,
    trip_summary,
)
from railinsight.data.loader import TGVDataset
from railinsight.exceptions import RailInsightError
from railinsight.viz.history import MONTH_LABELS
from railinsight.viz.trip import causes_bar, comparison_bars, outcomes_bar

logger = logging.getLogger(__name__)

# Durée de vie du cache : la base est rafraîchie une fois par mois.
CACHE_TTL = 3600


@st.cache_data(ttl=CACHE_TTL)
def load() -> TGVDataset:
    """Charge le contrat de données partagé depuis PostgreSQL, sans le modifier."""
    return TGVDataset.from_db()


def month_label(date: pd.Timestamp) -> str:
    """Formate un mois en français sans dépendre de la locale du système."""
    date = pd.Timestamp(date)
    return f"{MONTH_LABELS[date.month]} {date.year}"


def percent(value: float | None) -> str:
    """Affiche une fraction en pourcentage français ou un tiret si indisponible."""
    return "—" if value is None or pd.isna(value) else f"{value:.1%}".replace(".", ",")


st.title("Mon trajet")
st.write("Explorez une liaison : ses résultats historiques, leur évolution et les différences entre les deux directions.")
try:
    ds = load()
except Exception:
    logger.exception("Impossible de charger les données de Mon trajet.")
    st.error("Les données sont momentanément indisponibles. Réessayez ultérieurement.")
    st.stop()
if ds.df.empty:
    st.info("Aucune donnée disponible pour le moment.")
    st.stop()
route = st.sidebar.selectbox("Liaison", ds.routes())

try:
    route_data = ds.for_route(route)
    months = sorted(pd.to_datetime(route_data["date"]).unique())
    start, end = st.sidebar.select_slider("Période", options=months, value=(months[0], months[-1]), format_func=month_label)
    sub = filter_trip_period(route_data, start, end)
    if sub.empty:
        st.info("Aucune observation pour cette liaison et cette période.")
        st.stop()
    summary = trip_summary(sub)
    logger.info("Consultation de Mon trajet : liaison=%s, début=%s, fin=%s", route, start, end)
    st.subheader(route)
    st.caption(
        f"Données de {month_label(summary['date_min'])} à {month_label(summary['date_max'])} : {summary['n_months']} "
        f"mois distincts et {summary['scheduled']:,} circulations prévues enregistrées.".replace(",", " ")
    )
    st.caption(
        "Ces fréquences historiques décrivent les circulations enregistrées, pas les voyageurs ni la probabilité de votre prochain train. "
        "Les mois absents ne sont pas remplacés par zéro."
    )
    columns = st.columns(4)
    columns[0].metric("Taux historique d'annulation", percent(summary["cancellation_rate"]))
    columns[1].metric("Retards parmi les circulations effectuées", percent(summary["late_rate"]))
    columns[2].metric("Taux historique de perturbation", percent(summary["disruption_rate"]))
    delay = summary["avg_delay_arrival"]
    columns[3].metric("Retard moyen des trains en retard", "—" if delay is None else f"{delay:.1f} min".replace(".", ","))
    st.caption(
        "Perturbation = annulation ou arrivée en retard. Le taux de retard est rapporté aux circulations effectuées "
        "; annulations et perturbations aux circulations prévues. Le retard moyen concerne uniquement les trains en "
        "retard."
    )

    st.subheader("Sur 100 circulations prévues")
    outcomes = outcomes_per_100(sub)
    if outcomes.empty:
        st.info("Aucune circulation prévue : les proportions sont indisponibles.")
    else:
        st.plotly_chart(outcomes_bar(outcomes), width="stretch")
        values = outcomes.set_index("outcome")["per_100"]
        on_time = f"{values.iloc[0]:.1f}".replace(".", ",")
        late = f"{values.iloc[1]:.1f}".replace(".", ",")
        cancelled = f"{values.iloc[2]:.1f}".replace(".", ",")
        st.write(
            f"Sur une base historique de 100 circulations prévues : "
            f"environ {on_time} à l'heure selon les seuils SNCF, {late} arrivées en retard et {cancelled} annulations."
        )
        st.caption(
            "Aucun tirage aléatoire : les effectifs de toute la liaison et de la période sélectionnées sont ramenés "
            "à une base de 100, puis arrondis pour la lecture. Ce ne sont pas 100 trains sélectionnés ni une prévision. "
            "Le retard suit les seuils SNCF liés à la durée du trajet."
        )

    st.subheader("Évolution sur les dernières données disponibles")
    st.caption(
        "Cette comparaison exige 24 mois consécutifs dans la sélection : les 12 derniers constituent la période récente, "
        "et les 12 précédents la période précédente. Avec moins de 24 mois, ou un mois manquant dans ces deux périodes, "
        "la comparaison et son écart ne sont pas affichés. Aucune donnée extérieure à la sélection n’est utilisée ; "
        "les autres indicateurs restent calculés sur la période choisie."
    )
    evolution = recent_trip_evolution(sub)
    if not evolution["available"]:
        st.info(evolution["reason"])
    else:
        periods = evolution["periods"]
        previous, current = periods.iloc[0], periods.iloc[1]
        st.caption(
            f"{month_label(current['start'])}–{month_label(current['end'])} comparé à "
            f"{month_label(previous['start'])}–{month_label(previous['end'])} : deux périodes de douze mois consécutifs "
            f"dans la sélection."
        )
        dated_periods = periods.copy()
        dated_periods["period"] = [f"{row.period} : {month_label(row.start)}–{month_label(row.end)}" for row in periods.itertuples()]
        st.plotly_chart(comparison_bars(dated_periods, "period"), width="stretch")
        delta = evolution["deltas_pp"]["disruption_rate"]
        text = f"{delta:+.2f}".replace(".", ",")
        st.write(
            f"Écart du taux de perturbation : {text} points de pourcentage (période récente moins période précédente). "
            f"Une baisse décrit moins de perturbations observées, sans garantir les prochains trajets."
        )

    st.subheader("Et dans l'autre sens ?")
    reverse = reverse_trip_comparison(ds.df, route, start, end)
    if not reverse["available"]:
        st.info(reverse["reason"])
    else:
        common = reverse["common_months"]
        st.caption(
            f"Comparaison sur {len(common)} mois communs aux deux directions, parmi {reverse['n_requested_months']} mois "
            f"calendaires demandés, entre {month_label(common[0])} et {month_label(common[-1])}."
        )
        st.plotly_chart(comparison_bars(reverse["directions"], "direction"), width="stretch")
        st.caption(
            "Axe vertical : pourcentage des circulations de chaque direction sur les mois communs. "
            "Retards = trains arrivés en retard / trains ayant circulé ; "
            "annulations = trains annulés / trains prévus ; "
            "perturbations = (trains annulés + trains arrivés en retard) / trains prévus."
        )
        st.caption(
            "Les deux directions sont recalculées sur les mêmes mois. Si cette couverture est plus courte, leurs "
            "résultats peuvent différer de la synthèse ci-dessus. Les volumes de circulation peuvent aussi différer."
        )

    st.subheader("Causes déclarées des retards")
    causes = average_causes(sub)
    if causes.isna().all():
        st.info("Aucun retard enregistré : aucune répartition des causes à afficher.")
    else:
        st.plotly_chart(causes_bar(causes), width="stretch")
        st.caption(
            "Parts pondérées par le nombre de trains en retard à l'arrivée. La part grise représente une ventilation "
            "inconnue, pas une cause identifiée ; les parts déclarées ne sont pas renormalisées. Tolérance d'arrondi : "
            "0,1 point de pourcentage. Les causes concernent les retards, pas les annulations."
        )
except RailInsightError as error:
    logger.warning("Résultats de Mon trajet indisponibles : %s", error)
    st.error(f"Résultats indisponibles pour cette sélection : {error}")
