"""Graphiques de la page Fiabilité des liaisons (tâche 5)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def reliability_bar(df: pd.DataFrame, title: str) -> go.Figure:
    """Barres horizontales du score de fiabilité par liaison, triées pour la lisibilité."""
    data = df.sort_values("reliability_score")
    fig = px.bar(
        data,
        x="reliability_score",
        y="route",
        orientation="h",
        title=title,
        labels={"reliability_score": "Score de fiabilité", "route": ""},
        range_x=[0, 1],
    )
    return fig
