"""
Description :
Page Overview (tâche 3) : objectif du projet, indicateurs clés du réseau et
présentation des différentes pages de l'application.
"""

import streamlit as st

from railinsight.analysis.metrics import monthly_late_rate
from railinsight.analysis.overview import global_kpis
from railinsight.data.loader import TGVDataset
from railinsight.viz.charts import late_rate_line


@st.cache_data
def load() -> TGVDataset:
    return TGVDataset.from_db()


st.title("Vue d'ensemble du réseau TGV")
st.write(
    "**RailInsight** explore la ponctualité des TGV à partir des données ouvertes de la SNCF : "
    "retards, annulations et causes, par liaison et dans le temps. Cette page résume l'état du "
    "réseau ; les autres pages détaillent chaque angle d'analyse."
)

ds = load()
kpis = global_kpis(ds.df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Liaisons suivies", kpis["n_routes"])
c2.metric("Trains prévus (total)", f"{kpis['scheduled']:,}".replace(",", " "))
c3.metric("Taux de retard", f"{kpis['late_rate']:.1%}" if kpis["late_rate"] is not None else "—")
c4.metric("Taux d'annulation", f"{kpis['cancellation_rate']:.1%}" if kpis["cancellation_rate"] is not None else "—")

if kpis["date_min"] is not None:
    st.caption(f"Période couverte : {kpis['date_min']:%b %Y} → {kpis['date_max']:%b %Y}")

st.subheader("Taux de retard du réseau dans le temps")
st.plotly_chart(late_rate_line(monthly_late_rate(ds.df), "Taux de retard global"), use_container_width=True)

st.subheader("Les pages de l'application")
st.markdown(
    "- **Historique & évolution** — retards et annulations dans le temps, répartition par cause, saisonnalité.\n"
    "- **Fiabilité des liaisons** — classement des liaisons les plus et les moins fiables.\n"
    "- **Mon trajet** — choisissez une liaison et obtenez ses retards, annulations et causes."
)
