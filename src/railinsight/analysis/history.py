"""Métriques de la page Historique & évolution (tâche 4).

Évolution des retards et des annulations dans le temps, répartition des causes,
sévérité des retards, comparaison des services et saisonnalité. Toutes les fonctions
sont pures : elles prennent le DataFrame normalisé (contrat de données) et renvoient
un DataFrame prêt à visualiser.
"""

import pandas as pd

from railinsight.analysis.metrics import cancellation_rate, monthly_late_rate

# Colonnes de causes (part en %) issues du contrat de données.
CAUSE_COLUMNS = [
    "cause_external",
    "cause_infra",
    "cause_traffic",
    "cause_rolling_stock",
    "cause_station",
    "cause_passengers",
]


def monthly_delays_cancellations(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de retard et taux d'annulation par mois, réunis dans un seul tableau."""
    late = monthly_late_rate(df)
    cancelled = cancellation_rate(df)
    return late.merge(cancelled, on="date")


def punctuality_by_service(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de retard par mois et par service (National / International)."""
    if "service" not in df.columns:
        return pd.DataFrame(columns=["date", "service", "late_rate"])

    g = df.groupby(["date", "service"])[["scheduled", "cancelled", "late_arrival"]].sum().reset_index()
    effective = (g["scheduled"] - g["cancelled"]).replace(0, pd.NA)
    g["late_rate"] = g["late_arrival"] / effective
    return g[["date", "service", "late_rate"]]


def delay_severity_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """Part des trains prévus en retard de plus de 15 / 30 / 60 minutes, par mois."""
    g = df.groupby("date")[["scheduled", "late_15", "late_30", "late_60"]].sum().reset_index()
    scheduled = g["scheduled"].replace(0, pd.NA)
    for col in ("late_15", "late_30", "late_60"):
        g[col] = g[col] / scheduled
    return g[["date", "late_15", "late_30", "late_60"]]


def cause_breakdown_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """Répartition moyenne des causes de retard par mois.

    La moyenne est pondérée par le nombre de trains en retard à l'arrivée : une
    liaison qui a beaucoup de retards pèse davantage dans le mix des causes du mois.
    """
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["date"])

    lignes = []
    for date, groupe in tmp.groupby("date"):
        poids = groupe["late_arrival"].fillna(0)
        total = poids.sum()
        ligne = {"date": date}
        for cause in CAUSE_COLUMNS:
            valeurs = groupe[cause].fillna(0)
            ligne[cause] = (valeurs * poids).sum() / total if total > 0 else valeurs.mean()
        lignes.append(ligne)

    return pd.DataFrame(lignes)


def seasonality(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de retard moyen par mois de l'année (1-12), pour révéler la saisonnalité."""
    mensuel = monthly_late_rate(df.assign(date=pd.to_datetime(df["date"])))
    mensuel["month"] = pd.to_datetime(mensuel["date"]).dt.month
    return mensuel.groupby("month")["late_rate"].mean().reset_index()
