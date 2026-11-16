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
    fig.update_layout(xaxis_tickformat=".0%")
    return fig


def reliability_scatter(df: pd.DataFrame, title: str = "Retards vs annulations par liaison") -> go.Figure:
    """Nuage de points : taux d'annulation contre taux de retard, taille = trafic.

    Les liaisons en bas à gauche sont les plus fiables (peu de retards, peu d'annulations).
    """
    fig = px.scatter(
        df,
        x="late_rate",
        y="cancellation_rate",
        size="scheduled",
        hover_name="route",
        title=title,
        labels={"late_rate": "Taux de retard", "cancellation_rate": "Taux d'annulation", "scheduled": "Trains prévus"},
    )
    fig.update_layout(xaxis_tickformat=".0%", yaxis_tickformat=".0%")
    return fig
