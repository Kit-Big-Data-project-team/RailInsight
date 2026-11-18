"""
Description :
Page Fiabilité des liaisons: classement des liaisons les plus et les
moins fiables, comparaison des services, et vue retards/annulations par liaison,
avec un seuil minimal de trafic pour éviter les petits échantillons.
"""

import streamlit as st

from railinsight.analysis.reliability import (
    reliability_by_service,
    route_reliability,
    top_reliable,
    top_unreliable,
)
from railinsight.data.loader import TGVDataset
from railinsight.viz.reliability import reliability_bar, reliability_scatter

COLS = ["route", "reliability_score", "late_rate", "cancellation_rate", "scheduled"]
COL_LABELS = {
    "route": "Liaison",
    "reliability_score": "Fiabilité",
    "late_rate": "Taux de retard",
    "cancellation_rate": "Taux d'annulation",
    "scheduled": "Trains prévus",
}


@st.cache_data
def load() -> TGVDataset:
    return TGVDataset.from_db()


st.title("Fiabilité des liaisons")
st.write(
    "Score de fiabilité = part des trains prévus qui ont circulé **et** sont arrivés à "
    "l'heure (hors annulations et retards à l'arrivée), agrégé sur toute la période. "
    "Le seuil de trafic écarte les liaisons à très faible volume, peu représentatives."
)

ds = load()
min_scheduled = st.sidebar.slider("Trafic minimum (trains prévus)", min_value=0, max_value=5000, value=500, step=100)

fiables = top_reliable(ds.df, n=10, min_scheduled=min_scheduled)
non_fiables = top_unreliable(ds.df, n=10, min_scheduled=min_scheduled)

k1, k2, k3 = st.columns(3)
k1.metric("Liaisons analysées", int((route_reliability(ds.df)["scheduled"] >= min_scheduled).sum()))

st.markdown(
    """
<style>
.st-key-metric-fiable [data-testid="stMetricValue"],
.st-key-metric-non-fiable [data-testid="stMetricValue"] {
    font-size: 24px;
}
</style>
""",
    unsafe_allow_html=True,
)

if not fiables.empty:
    with k2:
        with st.container(key="metric-fiable"):
            st.metric("Plus fiable", fiables.iloc[0]["route"], f"{fiables.iloc[0]['reliability_score']:.1%}")

if not non_fiables.empty:
    with k3:
        with st.container(key="metric-non-fiable"):
            st.metric("Moins fiable", non_fiables.iloc[0]["route"], f"{non_fiables.iloc[0]['reliability_score']:.1%}")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Top 10 des plus fiables")
    st.plotly_chart(reliability_bar(fiables, "Les plus fiables"), use_container_width=True)
with col2:
    st.subheader("Top 10 des moins fiables")
    st.plotly_chart(reliability_bar(non_fiables, "Les moins fiables"), use_container_width=True)

st.subheader("Retards et annulations : quelles liaisons sont les plus touchées ?")
st.plotly_chart(reliability_scatter(route_reliability(ds.df).query("scheduled >= @min_scheduled")), use_container_width=True)
st.caption(
    "Chaque bulle représente une liaison TGV. Plus elle est grande, plus le trafic est important. "
    "Les liaisons situées en bas à gauche cumulent moins de retards et d'annulations ; "
    "celles en haut à droite sont les plus perturbées."
)

st.subheader("La fiabilité varie-t-elle selon le type de service ?")
st.caption("Comparez les performances des TGV nationaux et internationaux à travers leur score de fiabilité, leur taux de retard et leur taux d'annulation.")
st.dataframe(
    reliability_by_service(ds.df)[["service", "reliability_score", "late_rate", "cancellation_rate"]]
    .rename(
        columns={
            "service": "Type de service",
            "reliability_score": "Score de fiabilité",
            "late_rate": "Taux de retard",
            "cancellation_rate": "Taux d'annulation",
        }
    )
    .style.format(
        {
            "Score de fiabilité": "{:.1%}",
            "Taux de retard": "{:.1%}",
            "Taux d'annulation": "{:.1%}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Quelles liaisons se démarquent ?")
st.caption("Explorez les indicateurs des dix liaisons les mieux et les moins bien classées selon leur score de fiabilité.")
tab1, tab2 = st.tabs(["Les 10 plus fiables", "Les 10 moins fiables"])
with tab1:
    st.dataframe(
        fiables[COLS].rename(columns=COL_LABELS).style.format({"Fiabilité": "{:.1%}", "Taux de retard": "{:.1%}", "Taux d'annulation": "{:.1%}"}),
        use_container_width=True,
        hide_index=True,
    )
with tab2:
    st.dataframe(
        non_fiables[COLS].rename(columns=COL_LABELS).style.format({"Fiabilité": "{:.1%}", "Taux de retard": "{:.1%}", "Taux d'annulation": "{:.1%}"}),
        use_container_width=True,
        hide_index=True,
    )
