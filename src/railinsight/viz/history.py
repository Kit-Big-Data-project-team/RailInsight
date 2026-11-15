"""Graphiques de la page Historique & évolution (tâche 4)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Libellés lisibles des causes pour les légendes.
CAUSE_LABELS = {
    "cause_external": "Externe",
    "cause_infra": "Infrastructure",
    "cause_traffic": "Gestion du trafic",
    "cause_rolling_stock": "Matériel roulant",
    "cause_station": "Gestion en gare",
    "cause_passengers": "Prise en charge voyageurs",
}


def delays_cancellations_line(df: pd.DataFrame, title: str = "Évolution des retards et des annulations") -> go.Figure:
    """Courbes du taux de retard et du taux d'annulation dans le temps."""
    long = df.melt(id_vars="date", value_vars=["late_rate", "cancellation_rate"], var_name="Indicateur", value_name="Taux")
    long["Indicateur"] = long["Indicateur"].map({"late_rate": "Taux de retard", "cancellation_rate": "Taux d'annulation"})
    return px.line(long, x="date", y="Taux", color="Indicateur", title=title, labels={"date": ""})


def cause_area(df: pd.DataFrame, title: str = "Répartition des causes de retard dans le temps") -> go.Figure:
    """Aire empilée de la part de chaque cause de retard au fil des mois."""
    long = df.melt(id_vars="date", var_name="Cause", value_name="Part (%)")
    long["Cause"] = long["Cause"].map(CAUSE_LABELS)
    return px.area(long, x="date", y="Part (%)", color="Cause", title=title, labels={"date": ""})


def seasonality_bar(df: pd.DataFrame, title: str = "Saisonnalité du taux de retard") -> go.Figure:
    """Taux de retard moyen par mois de l'année."""
    return px.bar(df, x="month", y="late_rate", title=title, labels={"month": "Mois", "late_rate": "Taux de retard moyen"})
