"""Graphiques de la page Mon trajet (tâche 6)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from railinsight.viz.history import CAUSE_LABELS


def causes_pie(causes: pd.Series, title: str = "Répartition des causes de retard") -> go.Figure:
    """Camembert de la part de chaque cause de retard pour la liaison."""
    data = causes.rename(index=CAUSE_LABELS).reset_index()
    data.columns = ["Cause", "Part"]
    return px.pie(data, names="Cause", values="Part", title=title)
