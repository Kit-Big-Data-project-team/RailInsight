"""Fonctions communes pour préparer les prévisions futures."""

import pandas as pd


def get_recent_rates(
    df: pd.DataFrame,
    latest_month: pd.Period,
) -> list[float] | None:
    """Retourne les trois derniers taux si les mois sont consécutifs."""

    recent = df.sort_values("date").tail(3)

    expected = [
        latest_month - 2,
        latest_month - 1,
        latest_month,
    ]

    actual = list(recent["date"].dt.to_period("M"))

    if actual != expected:
        return None

    return recent["late_rate"].astype(float).tolist()