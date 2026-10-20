"""
Description :
Contient les différentes pages de l'application : vue d'ensemble, analyse de la régularité, évolution temporelle, etc.

"""

import streamlit as st

from railinsight.analysis.metrics import monthly_late_rate
from railinsight.data.loader import TGVDataset
from railinsight.exceptions import RailInsightError
from railinsight.viz.charts import late_rate_line


@st.cache_data
def load() -> TGVDataset:
    return TGVDataset.from_csv("data/regularite-mensuelle-tgv-aqst.csv")


st.title("Vue d'ensemble du réseau TGV")
ds = load()

route = st.sidebar.selectbox("Liaison", ds.routes())
try:
    st.plotly_chart(late_rate_line(monthly_late_rate(ds.for_route(route)), route), use_container_width=True)
except RailInsightError as e:  # erreurs métier → message propre, pas de traceback
    st.error(f"Impossible d'afficher cette liaison : {e}")
