"""
Description :
Centralise les fonctions de création des graphiques.

"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def late_rate_line(df: pd.DataFrame, title: str) -> go.Figure:
    return px.line(df, x="date", y="late_rate", title=title, labels={"late_rate": "Taux de retard", "date": ""})
