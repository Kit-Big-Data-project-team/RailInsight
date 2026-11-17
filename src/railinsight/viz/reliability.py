"""Graphiques de la page Fiabilité des liaisons."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from railinsight.viz.theme import PRIMARY, PRIMARY_DARK


def reliability_bar(df: pd.DataFrame, title: str, color: str = PRIMARY) -> go.Figure:
    """Affiche le score de fiabilité des liaisons avec un dégradé de bleu.

    Args:
        df: Tableau avec les colonnes route et reliability_score.
        title: Titre du graphique.
        color: Couleur de référence (conservée pour compatibilité).
    """
    data = df.sort_values("reliability_score")

    # Dégradé monochrome bleu, du plus clair au plus soutenu.
    blue_gradient = [
        "#DCE6F0",
        "#C5D5E5",
        "#AEC4D9",
        "#97B3CE",
        "#80A2C3",
        "#6991B8",
        "#5280AD",
        "#3F709F",
        "#32618D",
        "#274F78",
    ]
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
    fig.update_traces(
        marker_color=blue_gradient[: len(data)],
        texttemplate="%{x:.1%}",
        textposition="inside",
        insidetextanchor="middle",
    )
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
    fig.update_traces(marker=dict(color=PRIMARY_DARK, opacity=0.65, line=dict(width=1, color="white")))
    return fig
