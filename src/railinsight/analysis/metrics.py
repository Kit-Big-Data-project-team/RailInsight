"""
Description :
Calcule les indicateurs de régularité, les retards et les annulations.

"""

import pandas as pd


def monthly_late_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Taux de retard à l'arrivée par mois, en rapport de sommes (pas de moyenne de taux)."""
    g = df.groupby("date")[["scheduled", "cancelled", "late_arrival"]].sum()
    effective = g["scheduled"] - g["cancelled"]
    return (g["late_arrival"] / effective).rename("late_rate").reset_index()
