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

SEVERITY_LABELS = {
    "late_15": "> 15 min",
    "late_30": "> 30 min",
    "late_60": "> 60 min",
}

MONTH_LABELS = {
    1: "Jan",
    2: "Fév",
    3: "Mar",
    4: "Avr",
    5: "Mai",
    6: "Juin",
    7: "Juil",
    8: "Août",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Déc",
}


def delays_cancellations_line(df: pd.DataFrame, title: str = "Évolution des retards et des annulations") -> go.Figure:
    """Courbes du taux de retard et du taux d'annulation dans le temps."""
    long = df.melt(id_vars="date", value_vars=["late_rate", "cancellation_rate"], var_name="Indicateur", value_name="Taux")
    long["Indicateur"] = long["Indicateur"].map({"late_rate": "Taux de retard", "cancellation_rate": "Taux d'annulation"})
    fig = px.line(long, x="date", y="Taux", color="Indicateur", title=title, labels={"date": ""})
    fig.update_layout(yaxis_tickformat=".0%")
    return fig


def service_line(df: pd.DataFrame, title: str = "Taux de retard : National vs International") -> go.Figure:
    """Courbes du taux de retard dans le temps, une par service."""
    fig = px.line(df, x="date", y="late_rate", color="service", title=title, labels={"date": "", "late_rate": "Taux de retard", "service": "Service"})
    fig.update_layout(yaxis_tickformat=".0%")
    return fig


def severity_area(df: pd.DataFrame, title: str = "Sévérité des retards dans le temps") -> go.Figure:
    """Part des trains en retard de plus de 15 / 30 / 60 minutes au fil des mois."""
    long = df.melt(id_vars="date", value_vars=["late_15", "late_30", "late_60"], var_name="Seuil", value_name="Part")
    long["Seuil"] = long["Seuil"].map(SEVERITY_LABELS)
    fig = px.line(long, x="date", y="Part", color="Seuil", title=title, labels={"date": ""})
    fig.update_layout(yaxis_tickformat=".0%")
    return fig


def cause_area(df: pd.DataFrame, title: str = "Répartition des causes de retard dans le temps") -> go.Figure:
    """Aire empilée de la part de chaque cause de retard au fil des mois."""
    long = df.melt(id_vars="date", var_name="Cause", value_name="Part (%)")
    long["Cause"] = long["Cause"].map(CAUSE_LABELS)
    return px.area(long, x="date", y="Part (%)", color="Cause", title=title, labels={"date": ""})


def seasonality_bar(df: pd.DataFrame, title: str = "Saisonnalité du taux de retard") -> go.Figure:
    """Taux de retard moyen par mois de l'année, avec les noms de mois."""
    data = df.copy()
    data["Mois"] = data["month"].map(MONTH_LABELS)
    order = [MONTH_LABELS[m] for m in sorted(data["month"].unique())]
    fig = px.bar(data, x="Mois", y="late_rate", title=title, labels={"late_rate": "Taux de retard moyen"}, category_orders={"Mois": order})
    fig.update_layout(yaxis_tickformat=".0%")
    return fig
