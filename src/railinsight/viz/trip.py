"""Visualisations descriptives de Mon trajet, sans calcul des indicateurs."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from railinsight.viz.history import CAUSE_LABELS

TRIP_CAUSE_LABELS = {**CAUSE_LABELS, "cause_unallocated": "Part non ventilée dans les données"}
RATE_LABELS = {"late_rate": "Retards / circulations effectuées", "cancellation_rate": "Annulations / circulations prévues", "disruption_rate": "Perturbations / circulations prévues"}


def outcomes_bar(outcomes: pd.DataFrame) -> go.Figure:
    """Représente les trois issues historiques sur une base commune de 100.

    Args:
        outcomes: Tableau outcome, per_100 et count fourni par l'analyse.

    Returns:
        Barre empilée dont les valeurs non arrondies totalisent 100.
    """
    data = outcomes.assign(selection="Historique de la sélection")
    fig = px.bar(
        data,
        x="per_100",
        y="selection",
        color="outcome",
        orientation="h",
        barmode="stack",
        custom_data=["count"],
        color_discrete_map={"À l'heure selon les seuils SNCF": "#23856D", "Arrivées en retard": "#D58B20", "Annulations": "#BE4850"},
        labels={"per_100": "Circulations pour 100 prévues", "selection": "", "outcome": "Issue observée"},
    )
    fig.update_layout(height=150, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    fig.update_yaxes(visible=False)
    fig.update_xaxes(range=[0, 100])
    fig.update_traces(hovertemplate="%{fullData.name}<br>Pour 100 : %{x:.1f}<br>Effectif observé : %{customdata[0]}<extra></extra>")
    return fig


def comparison_bars(table: pd.DataFrame, category: str) -> go.Figure:
    """Compare les trois taux entre deux périodes ou directions sans les additionner.

    Args:
        table: Tableau de l'analyse avec les trois taux, scheduled et category.
        category: Nom de la colonne period ou direction.

    Returns:
        Barres groupées, pourcentages et effectifs en infobulle.
    """
    long = table.melt(id_vars=[category, "scheduled"], value_vars=list(RATE_LABELS), var_name="rate", value_name="value")
    long["rate"] = long["rate"].map(RATE_LABELS)
    fig = px.bar(
        long,
        x="rate",
        y="value",
        color=category,
        barmode="group",
        custom_data=["scheduled"],
        labels={"rate": "Indicateur", "value": "Taux historique", category: "Période" if category == "period" else "Direction"},
    )
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_traces(hovertemplate="%{x}<br>Taux : %{y:.1%}<br>Circulations prévues : %{customdata[0]}<extra>%{fullData.name}</extra>")
    return fig


def causes_bar(causes: pd.Series) -> go.Figure:
    """Présente les parts déclarées et non ventilées sans normaliser leur longueur.

    Args:
        causes: Série de pourcentages issue de average_causes.

    Returns:
        Barres horizontales sur un axe de 0 à 100 %, complément inconnu en gris.
    """
    data = causes.rename(index=TRIP_CAUSE_LABELS).rename("Part").rename_axis("Cause").reset_index()
    fig = px.bar(data, x="Part", y="Cause", color="Cause", orientation="h", color_discrete_map={"Part non ventilée dans les données": "#9CA3AF"}, labels={"Part": "Part des retards (%)"})
    fig.update_xaxes(range=[0, 100], ticksuffix=" %")
    fig.update_layout(showlegend=False)
    fig.update_traces(hovertemplate="%{y}<br>Part : %{x:.1f} %<extra></extra>")
    return fig


def causes_pie(causes: pd.Series, title: str = "Répartition des causes de retard") -> go.Figure:
    """Préserve l'ancien point d'entrée pour les appels existants.

    Args:
        causes: Parts déclarées et éventuel complément non ventilé.
        title: Titre de la figure.

    Returns:
        Camembert dont les étiquettes affichent les valeurs fournies. La page
        Mon trajet utilise désormais causes_bar pour éviter toute normalisation visuelle.
    """
    data = causes.rename(index=TRIP_CAUSE_LABELS).rename("Part").rename_axis("Cause").reset_index()
    fig = px.pie(data, names="Cause", values="Part", title=title)
    fig.update_traces(texttemplate="%{label}<br>%{value:.1f} %")
    return fig
