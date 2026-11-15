"""
Description :
Calcule les indicateurs de régularité, les retards et les annulations.

Ces fonctions sont communes à toutes les pages : chaque tâche s'appuie sur ce
socle plutôt que de recoder ses propres taux, pour garder des définitions cohérentes.
"""

import pandas as pd


def monthly_late_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de retard à l'arrivée par mois, en rapport de sommes (pas de moyenne de taux).

    Le dénominateur (trains ayant réellement circulé) est protégé contre la division
    par zéro : un mois entièrement annulé (ex. grève) donne un taux manquant, pas un inf.
    """
    g = df.groupby("date")[["scheduled", "cancelled", "late_arrival"]].sum()
    effective = (g["scheduled"] - g["cancelled"]).replace(0, pd.NA)
    return (g["late_arrival"] / effective).rename("late_rate").reset_index()


def cancellation_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Taux d'annulation par mois (trains annulés / trains prévus), en rapport de sommes."""
    g = df.groupby("date")[["scheduled", "cancelled"]].sum()
    scheduled = g["scheduled"].replace(0, pd.NA)
    return (g["cancelled"] / scheduled).rename("cancellation_rate").reset_index()
