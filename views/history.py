"""
Description :
Page Historique & évolution (tâche 4) : évolution des retards et des annulations
dans le temps, sévérité, répartition par cause, comparaison des services et
saisonnalité, pour tout le réseau ou une liaison choisie.
"""

import streamlit as st

from railinsight.analysis.history import (
    cause_breakdown_over_time,
    delay_severity_over_time,
    monthly_delays_cancellations,
    punctuality_by_service,
    seasonality,
)
from railinsight.data.loader import TGVDataset
from railinsight.exceptions import RailInsightError
from railinsight.viz.history import (
    cause_area,
    delays_cancellations_line,
    seasonality_bar,
    service_line,
    severity_area,
)


@st.cache_data
def load() -> TGVDataset:
    return TGVDataset.from_db()


st.title("Historique & évolution des retards")
st.write("Comment la ponctualité des TGV évolue dans le temps : retards, annulations, sévérité, causes et saisonnalité. Choisissez une liaison dans le menu, ou gardez tout le réseau.")

ds = load()
options = ["Tout le réseau"] + ds.routes()
choix = st.sidebar.selectbox("Liaison", options)

try:
    data = ds.df if choix == "Tout le réseau" else ds.for_route(choix)

    # Indicateurs de synthèse sur la période.
    scheduled = int(data["scheduled"].sum())
    cancelled = int(data["cancelled"].sum())
    late = int(data["late_arrival"].sum())
    effective = scheduled - cancelled
    c1, c2, c3 = st.columns(3)
    c1.metric("Taux de retard moyen", f"{late / effective:.1%}" if effective else "—")
    c2.metric("Taux d'annulation moyen", f"{cancelled / scheduled:.1%}" if scheduled else "—")
    c3.metric("Trains prévus", f"{scheduled:,}".replace(",", " "))

    st.subheader("Retards et annulations dans le temps")
    st.plotly_chart(delays_cancellations_line(monthly_delays_cancellations(data)), use_container_width=True)
    st.caption("Le taux de retard est rapporté aux trains ayant réellement circulé ; le taux d'annulation aux trains prévus.")

    st.subheader("National vs International")
    st.plotly_chart(service_line(punctuality_by_service(data)), use_container_width=True)
    st.caption("Comparaison du taux de retard selon le type de desserte.")

    st.subheader("Sévérité des retards")
    st.plotly_chart(severity_area(delay_severity_over_time(data)), use_container_width=True)
    st.caption("Part des trains prévus en retard de plus de 15, 30 et 60 minutes.")

    st.subheader("Répartition des causes de retard")
    st.plotly_chart(cause_area(cause_breakdown_over_time(data)), use_container_width=True)
    st.caption("Moyenne pondérée par le nombre de trains en retard chaque mois.")

    st.subheader("Saisonnalité")
    st.plotly_chart(seasonality_bar(seasonality(data)), use_container_width=True)
    st.caption("Taux de retard moyen par mois de l'année, toutes années confondues.")
except RailInsightError as e:  # erreurs métier → message propre, pas de traceback
    st.error(f"Impossible d'afficher ces données : {e}")
