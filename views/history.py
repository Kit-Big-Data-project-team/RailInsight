"""
Description :
Page Historique & évolution (tâche 4) : évolution des retards et des annulations
dans le temps, répartition par cause et saisonnalité, pour tout le réseau ou une liaison.
"""

import streamlit as st

from railinsight.analysis.history import (
    cause_breakdown_over_time,
    monthly_delays_cancellations,
    seasonality,
)
from railinsight.data.loader import TGVDataset
from railinsight.exceptions import RailInsightError
from railinsight.viz.history import cause_area, delays_cancellations_line, seasonality_bar


@st.cache_data
def load() -> TGVDataset:
    return TGVDataset.from_db()


st.title("Historique & évolution des retards")
st.write("Évolution des retards et des annulations dans le temps, répartition par cause " "et saisonnalité. Choisissez une liaison dans le menu, ou gardez tout le réseau.")

ds = load()
options = ["Tout le réseau"] + ds.routes()
choix = st.sidebar.selectbox("Liaison", options)

try:
    data = ds.df if choix == "Tout le réseau" else ds.for_route(choix)

    st.subheader("Retards et annulations dans le temps")
    st.plotly_chart(delays_cancellations_line(monthly_delays_cancellations(data)), use_container_width=True)

    st.subheader("Répartition des causes de retard")
    st.plotly_chart(cause_area(cause_breakdown_over_time(data)), use_container_width=True)

    st.subheader("Saisonnalité")
    st.plotly_chart(seasonality_bar(seasonality(data)), use_container_width=True)
except RailInsightError as e:  # erreurs métier → message propre, pas de traceback
    st.error(f"Impossible d'afficher ces données : {e}")
