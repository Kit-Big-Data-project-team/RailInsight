"""
Description :
Page Fiabilité des liaisons (tâche 5) : classement des liaisons les plus et les
moins fiables, avec un seuil minimal de trafic pour éviter les petits échantillons.
"""

import streamlit as st

from railinsight.analysis.reliability import top_reliable, top_unreliable
from railinsight.data.loader import TGVDataset
from railinsight.viz.reliability import reliability_bar


@st.cache_data
def load() -> TGVDataset:
    return TGVDataset.from_db()


st.title("Fiabilité des liaisons")
st.write("Score de fiabilité = part des trains prévus qui ont circulé **et** sont arrivés à " "l'heure (hors annulations et retards à l'arrivée), agrégé sur toute la période.")

ds = load()
min_scheduled = st.sidebar.slider("Trafic minimum (trains prévus)", min_value=0, max_value=5000, value=500, step=100)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top 10 des plus fiables")
    st.plotly_chart(reliability_bar(top_reliable(ds.df, n=10, min_scheduled=min_scheduled), "Les plus fiables"), use_container_width=True)
with col2:
    st.subheader("Top 10 des moins fiables")
    st.plotly_chart(reliability_bar(top_unreliable(ds.df, n=10, min_scheduled=min_scheduled), "Les moins fiables"), use_container_width=True)

st.caption("💡 Carte géographique des liaisons : optionnelle, à ajouter si on récupère les coordonnées des gares.")
