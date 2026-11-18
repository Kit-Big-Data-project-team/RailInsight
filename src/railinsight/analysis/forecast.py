"""Fonctions communes pour préparer les prévisions futures."""

import pandas as pd


def get_recent_rates(
    df: pd.DataFrame,
    latest_month: pd.Period,
) -> list[float] | None:
    """Récupère les taux des trois mois précédant la prévision.

    Args:
        df: Historique mensuel d'une liaison et d'un service.
        latest_month: Dernier mois observé dans le jeu de données.

    Returns:
        Liste des trois taux, du plus ancien au plus récent,
        ou None si les mois attendus sont absents.
    """

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
