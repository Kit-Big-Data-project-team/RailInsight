"""Métriques de la page Mon trajet (tâche 6).

Résumé d'une liaison choisie : probabilité d'annulation, taux de retard, retard
moyen et répartition des causes.
"""

import pandas as pd

from railinsight.analysis.history import CAUSE_COLUMNS


def average_causes(df: pd.DataFrame) -> pd.Series:
    """Part moyenne de chaque cause de retard, pondérée par le nombre de trains en retard."""
    poids = df["late_arrival"].fillna(0)
    total = poids.sum()
    if total == 0:
        return df[CAUSE_COLUMNS].mean()
    return df[CAUSE_COLUMNS].fillna(0).multiply(poids, axis=0).sum() / total


def trip_summary(df: pd.DataFrame) -> dict:
    """Indicateurs d'une liaison (DataFrame déjà filtré sur cette liaison)."""
    scheduled = int(df["scheduled"].sum())
    cancelled = int(df["cancelled"].sum())
    late = int(df["late_arrival"].sum())
    effective = scheduled - cancelled

    poids = df["late_arrival"].fillna(0)
    total_poids = poids.sum()
    retard_moyen = (df["avg_delay_arrival"].fillna(0) * poids).sum() / total_poids if total_poids else None

    return {
        "n_months": int(len(df)),
        "cancellation_probability": (cancelled / scheduled) if scheduled else None,
        "late_rate": (late / effective) if effective else None,
        "avg_delay_arrival": retard_moyen,
    }
