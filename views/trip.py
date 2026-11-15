"""
Description :
Page Mon trajet (tâche 6) : on choisit une liaison et on obtient ses indicateurs
de ponctualité (retard moyen, taux de retard, probabilité d'annulation) et ses causes.
"""

import streamlit as st

from railinsight.analysis.trip import average_causes, trip_summary
from railinsight.data.loader import TGVDataset
from railinsight.exceptions import RailInsightError
from railinsight.viz.trip import causes_pie


@st.cache_data
def load() -> TGVDataset:
    return TGVDataset.from_db()


st.title("Mon trajet")
st.write("Choisissez une liaison pour voir ses retards, ses annulations et les causes dominantes.")

ds = load()
route = st.sidebar.selectbox("Liaison", ds.routes())

try:
    sub = ds.for_route(route)
    resume = trip_summary(sub)

    c1, c2, c3 = st.columns(3)
    c1.metric("Probabilité d'annulation", f"{resume['cancellation_probability']:.1%}" if resume["cancellation_probability"] is not None else "—")
    c2.metric("Taux de retard", f"{resume['late_rate']:.1%}" if resume["late_rate"] is not None else "—")
    c3.metric("Retard moyen à l'arrivée", f"{resume['avg_delay_arrival']:.1f} min" if resume["avg_delay_arrival"] is not None else "—")

    st.caption(f"Basé sur {resume['n_months']} mois de données pour la liaison {route}.")

    st.subheader("Causes de retard")
    st.plotly_chart(causes_pie(average_causes(sub)), use_container_width=True)
except RailInsightError as e:
    st.error(f"Impossible d'afficher cette liaison : {e}")
