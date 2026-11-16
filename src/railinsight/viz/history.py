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
    "cause_unallocated": "Part non ventilée dans les données",
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


def delays_cancellations_line(df: pd.DataFrame, title: str = "Retards, annulations et perturbations") -> go.Figure:
    """Affiche les trois taux sans les empiler ni additionner leurs pourcentages.

    Args:
        df: Tableau mensuel avec date, late_rate, cancellation_rate et disruption_rate.
        title: Titre du graphique.

    Returns:
        Figure avec trois courbes, axe et infobulles exprimés en pourcentages.
        Les légendes précisent la population de chaque indicateur.
    """
    labels = {
        "late_rate": "Retards / trains ayant circulé",
        "cancellation_rate": "Annulations / trains prévus",
        "disruption_rate": "Perturbations / trains prévus",
    }
    long = df.melt(id_vars="date", value_vars=list(labels), var_name="Indicateur", value_name="Taux")
    long["Indicateur"] = long["Indicateur"].map(labels)
    fig = px.line(long, x="date", y="Taux", color="Indicateur", line_dash="Indicateur", title=title, labels={"date": ""})
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_traces(hovertemplate="%{x|%m/%Y}<br>Taux : %{y:.1%}<extra>%{fullData.name}</extra>", connectgaps=False)
    return fig


def cause_area(df: pd.DataFrame, title: str = "Répartition des causes de retard dans le temps") -> go.Figure:
    """Présente les causes déclarées et le complément non ventilé en gris.

    Args:
        df: Répartition mensuelle, en pourcentages de 0 à 100. Les mois sans
            retard ont des parts manquantes et sont signalés par une annotation.
        title: Titre du graphique.

    Returns:
        Aire empilée sans normalisation des parts publiées ; les infobulles
        précisent les pourcentages. Une annotation signale chaque mois sans retard.
    """
    long = df.melt(id_vars="date", value_vars=list(CAUSE_LABELS), var_name="Cause", value_name="Part (%)")
    long["Cause"] = long["Cause"].map(CAUSE_LABELS)
    fig = px.area(
        long,
        x="date",
        y="Part (%)",
        color="Cause",
        title=title,
        labels={"date": ""},
        color_discrete_map={"Part non ventilée dans les données": "#9CA3AF"},
    )
    fig.update_yaxes(ticksuffix=" %", rangemode="tozero")
    fig.update_traces(hovertemplate="%{x|%m/%Y}<br>Part : %{y:.1f} %<extra>%{fullData.name}</extra>", connectgaps=False)
    for date in df.loc[df[list(CAUSE_LABELS)].isna().all(axis=1), "date"]:
        fig.add_annotation(x=date, y=0, text="Aucun retard enregistré", showarrow=True)
    return fig


def seasonality_bar(df: pd.DataFrame, title: str = "Comparaison par mois de l'année") -> go.Figure:
    """Réutilise les mois français d'Abdelmounaim pour comparer les trois taux.

    Args:
        df: Tableau de seasonality avec les trois taux et n_years.
        title: Titre du graphique, sans interprétation causale.

    Returns:
        Barres groupées non additives, pourcentages et nombre d'années en infobulle.
    """
    labels = {
        "late_rate": "Retards / trains ayant circulé",
        "cancellation_rate": "Annulations / trains prévus",
        "disruption_rate": "Perturbations / trains prévus",
    }
    data = df.copy()
    data["Mois"] = data["month"].map(MONTH_LABELS)
    long = data.melt(id_vars=["Mois", "n_years"], value_vars=list(labels), var_name="Indicateur", value_name="Taux")
    long["Indicateur"] = long["Indicateur"].map(labels)
    fig = px.bar(long, x="Mois", y="Taux", color="Indicateur", barmode="group", title=title, custom_data=["n_years"], category_orders={"Mois": list(MONTH_LABELS.values())})
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_traces(hovertemplate="%{x}<br>Taux : %{y:.1%}<br>Années contributrices : %{customdata[0]}<extra>%{fullData.name}</extra>")
    return fig


def service_line(df: pd.DataFrame, title: str = "Taux de retard : National vs International") -> go.Figure:
    """Affiche la comparaison des services proposée par Abdelmounaim.

    Args:
        df: Taux de retard par date et service.
        title: Titre du graphique.

    Returns:
        Courbes en pourcentages, sans interpolation des valeurs manquantes.
    """
    fig = px.line(df, x="date", y="late_rate", color="service", title=title, labels={"date": "", "late_rate": "Taux de retard", "service": "Service"})
    fig.update_layout(yaxis_tickformat=".0%")
    fig.update_traces(connectgaps=False, hovertemplate="%{x|%m/%Y}<br>Taux : %{y:.1%}<extra>%{fullData.name}</extra>")
    return fig


def severity_area(df: pd.DataFrame, title: str = "Sévérité des retards dans le temps") -> go.Figure:
    """Conserve les courbes de sévérité d'Abdelmounaim sans empiler les seuils.

    Args:
        df: Parts mensuelles des seuils, rapportées aux trains prévus.
        title: Titre du graphique.

    Returns:
        Trois courbes en pourcentages ; une valeur indisponible laisse une coupure.
        Le nom historique de la fonction est conservé pour faciliter l'intégration.
    """
    long = df.melt(id_vars="date", value_vars=["late_15", "late_30", "late_60"], var_name="Seuil", value_name="Part")
    long["Seuil"] = long["Seuil"].map(SEVERITY_LABELS)
    fig = px.line(long, x="date", y="Part", color="Seuil", title=title, labels={"date": ""})
    fig.update_layout(yaxis_tickformat=".0%")
    fig.update_traces(connectgaps=False, hovertemplate="%{x|%m/%Y}<br>Taux : %{y:.1%}<extra>%{fullData.name}</extra>")
    return fig
