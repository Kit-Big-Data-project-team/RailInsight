"""Graphiques de synthèse utilisés par la page Vue d'ensemble."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from railinsight.viz.theme import CAUSE_COLORS, SEQUENTIAL

MONTHS_SHORT = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]


def network_trend_line(df: pd.DataFrame, title: str = "Évolution des retards et des annulations") -> go.Figure:
    """Compare les taux mensuels de retard et d'annulation sur le réseau."""
    if df.empty:
        return go.Figure()

    long = df.melt(
        id_vars="date",
        value_vars=["late_rate", "cancellation_rate"],
        var_name="Indicateur",
        value_name="Taux",
    )
    long["Indicateur"] = long["Indicateur"].map({"late_rate": "Taux de retard", "cancellation_rate": "Taux d'annulation"})
    fig = px.line(
        long,
        x="date",
        y="Taux",
        color="Indicateur",
        markers=True,
        labels={"date": "", "Taux": "Taux", "Indicateur": ""},
        title=title,
    )
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_layout(
        height=370,
        margin=dict(l=12, r=12, t=108, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )
    return fig


def causes_bar(df: pd.DataFrame, title: str = "Répartition des causes de retard") -> go.Figure:
    """Classe les six causes selon leur part pondérée dans les retards."""
    if df.empty:
        return go.Figure()

    ordered = df.sort_values("share", ascending=True)
    fig = px.bar(
        ordered,
        x="share",
        y="cause",
        color="cause",
        color_discrete_map=CAUSE_COLORS,
        orientation="h",
        text="share",
        labels={"share": "Part pondérée (%)", "cause": ""},
        title=title,
    )
    fig.update_traces(texttemplate="%{x:.1f} %", textposition="outside", cliponaxis=False)
    fig.update_xaxes(ticksuffix=" %", rangemode="tozero")
    fig.update_layout(
        height=360,
        margin=dict(l=12, r=38, t=58, b=12),
        showlegend=False,
    )
    return fig


def seasonality_heatmap(df: pd.DataFrame, title: str = "Taux de retard par année et par mois") -> go.Figure:
    """Affiche une heatmap année × mois à partir des taux mensuels du réseau."""
    if df.empty:
        return go.Figure()

    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    working["year"] = working["date"].dt.year
    working["month"] = working["date"].dt.month
    matrix = working.pivot(index="year", columns="month", values="late_rate")
    matrix = matrix.reindex(columns=range(1, 13)).sort_index()

    fig = go.Figure(
        data=go.Heatmap(
            x=MONTHS_SHORT,
            y=[str(year) for year in matrix.index],
            z=matrix.to_numpy(dtype=float) * 100,
            colorscale=SEQUENTIAL,
            xgap=3,
            ygap=3,
            colorbar=dict(title="Retard", ticksuffix=" %"),
            hovertemplate="Année : %{y}<br>Mois : %{x}<br>Taux de retard : %{z:.1f} %<extra></extra>",
            connectgaps=False,
        )
    )
    fig.update_layout(
        title=title,
        height=360,
        margin=dict(l=12, r=12, t=58, b=12),
        xaxis_title="",
        yaxis_title="Année",
    )
    return fig
