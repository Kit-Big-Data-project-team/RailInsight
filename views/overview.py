"""Page d'accueil : synthèse de la ponctualité des liaisons TGV du jeu de données."""

import logging

import streamlit as st

from railinsight.analysis.overview import (
    format_month_fr,
    global_kpis,
    latest_month_kpis,
    monthly_network_rates,
    overall_cause_distribution,
    overview_highlights,
)
from railinsight.data.loader import TGVDataset
from railinsight.viz.overview import causes_bar, network_trend_line, seasonality_heatmap

logger = logging.getLogger(__name__)

# Durée de vie du cache : la base est rafraîchie une fois par mois.
CACHE_TTL = 3600


@st.cache_data(ttl=CACHE_TTL)
def load() -> TGVDataset:
    """Charge le dataset préparé depuis PostgreSQL."""
    return TGVDataset.from_db()


st.title("La ponctualité des TGV en un coup d'œil")
st.markdown("""
Derrière chaque retard, chaque annulation et chaque trajet perturbé se cache une histoire.
RailInsight explore les données ouvertes de SNCF Voyageurs pour décrypter la ponctualité
des liaisons TGV et répondre à une question essentielle : les retards sont-ils de simples
incidents ou révèlent-ils des problèmes plus profonds ?

Commencez par découvrir le réseau dans son ensemble, puis remontez le fil des perturbations :
leur évolution dans le temps, leurs principales causes et les liaisons les plus ou les moins fiables.
Les chiffres racontent une histoire ; à vous de l'explorer.
""")

try:
    ds = load()
except Exception:
    logger.exception("Impossible de charger les données de la Vue d'ensemble.")
    st.error("Les données sont momentanément indisponibles. Réessayez ultérieurement.")
    st.stop()
df = ds.df

if df.empty:
    st.warning("Aucune donnée n'est disponible dans la base pour le moment.")
    st.stop()

kpis = global_kpis(df)
latest = latest_month_kpis(df)
latest_label = format_month_fr(latest["date"])

st.subheader("Les liaisons du jeu de données en chiffres")
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Liaisons suivies",
    f"{kpis['n_routes']:,}".replace(",", " "),
    help="Nombre de liaisons distinctes présentes dans le jeu de données.",
)
c2.metric(
    "Trains prévus · cumul",
    f"{kpis['scheduled']:,}".replace(",", " "),
    help="Nombre total de circulations prévues sur toute la période disponible.",
)
c3.metric(
    f"Taux de retard · {latest_label}",
    f"{latest['late_rate']:.1%}" if latest["late_rate"] is not None else "—",
    delta=f"{latest['late_delta'] * 100:+.1f} pt" if latest["late_delta"] is not None else None,
    delta_color="inverse",
    help=("Trains en retard à l'arrivée / trains ayant effectivement circulé. Le delta compare le dernier mois disponible au mois calendaire précédent."),
)
c4.metric(
    f"Taux d'annulation · {latest_label}",
    f"{latest['cancellation_rate']:.1%}" if latest["cancellation_rate"] is not None else "—",
    delta=(f"{latest['cancellation_delta'] * 100:+.1f} pt" if latest["cancellation_delta"] is not None else None),
    delta_color="inverse",
    help="Trains annulés / trains prévus. Le delta compare le dernier mois au mois précédent.",
)

if kpis["date_min"] is not None:
    st.caption(
        f"Période couverte : {kpis['date_min']:%m/%Y} – {kpis['date_max']:%m/%Y}. Les deux taux de retard affichés correspondent au dernier mois disponible."
    )

st.info(
    "**Périmètre des indicateurs.** Ces chiffres agrègent les observations mensuelles "
    "**par liaison** du jeu SNCF (AQST). Un même train peut être compté dans plusieurs "
    "liaisons : ils ne représentent donc **pas** la régularité nationale officielle des TGV, "
    "et ne doivent pas être additionnés pour en déduire un taux « réseau » global.",
    icon="ℹ️",
)

st.divider()
st.subheader("Comment évoluent les retards et les annulations ?")
st.caption("Suivez mois après mois l'évolution des perturbations et repérez les périodes où la régularité des liaisons s'améliore ou se dégrade.")
monthly = monthly_network_rates(df)
st.plotly_chart(
    network_trend_line(monthly),
    use_container_width=True,
    config={"displayModeBar": False},
)

st.subheader("Ce qu'il faut retenir")
highlights = overview_highlights(df)
insight_columns = st.columns(3)
for column, key in zip(insight_columns, ("trend", "worst_month", "dominant_cause")):
    insight = highlights[key]
    with column:
        with st.container(border=True):
            st.markdown(f"**{insight['title']}**")
            st.write(insight["text"])

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Quelles sont les principales causes ?")
    st.caption("Découvrez les facteurs qui contribuent le plus aux retards à l'arrivée. ")
    causes = overall_cause_distribution(df)
    if causes.empty:
        st.info("La répartition des causes n'est pas disponible pour cette période.")
    else:
        st.plotly_chart(
            causes_bar(causes),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    st.caption("Les parts sont pondérées par le nombre de trains en retard à l'arrivée.")


with right:
    st.subheader("Les périodes les plus perturbées")
    st.caption("Repérez les mois qui concentrent le plus de retards et observez si certaines périodes de l'année sont régulièrement plus difficiles.")
    if monthly.empty:
        st.info("Aucune donnée mensuelle exploitable pour construire la heatmap.")
    else:
        st.plotly_chart(
            seasonality_heatmap(monthly),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    st.caption("Chaque cellule représente le taux de retard observé pour un mois donné.")

st.divider()
st.subheader("Explorer les autres analyses")
nav1, nav2, nav3 = st.columns(3)
with nav1:
    with st.container(border=True):
        st.markdown("**Historique & évolution**")
        st.caption(
            "Explorer l'évolution des retards et des annulations, "
            "analyser les causes de retard et identifier les tendances saisonnières, "
            "à l'échelle du réseau ou d'une liaison."
        )
with nav2:
    with st.container(border=True):
        st.markdown("**Fiabilité des liaisons**")
        st.caption(
            "Classer les liaisons selon leur fiabilité, comparer les retards "
            "et les annulations, et analyser les différences entre services nationaux et internationaux."
        )
with nav3:
    with st.container(border=True):
        st.markdown("**Mon trajet**")
        st.caption(
            "Consulter les indicateurs de ponctualité d'une liaison : risque d'annulation, taux de retard, retard moyen à l'arrivée et répartition des causes."
        )
