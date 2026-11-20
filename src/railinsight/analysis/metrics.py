"""
Description :
Calcule les indicateurs de régularité, les retards et les annulations.

Ces fonctions sont communes à toutes les pages : chaque tâche s'appuie sur ce
socle plutôt que de recoder ses propres taux, pour garder des définitions cohérentes.

Biais à connaître : un mois dont le dénominateur est nul (ex. mois entièrement
annulé) produit un taux manquant et non un zéro. Ces mois sont donc écartés des
moyennes et des recherches de maximum. L'exclusion se fait indicateur par
indicateur : un mois peut compter pour le taux d'annulation tout en étant absent du
taux de retard. Les agrégats restent donc des moyennes sur les mois *disponibles*,
ce qui peut introduire un léger biais si les mois manquants ne sont pas aléatoires.
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


def monthly_disruption_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule la part des trains prévus annulés ou arrivés en retard par mois.

    Les annulations et les retards à l'arrivée sont des issues distinctes.
    On additionne leurs effectifs avant de diviser par les trains prévus ;
    additionner les taux de retard et d'annulation serait incorrect, car leurs
    dénominateurs diffèrent. Chaque train prévu a ainsi le même poids.

    Args:
        df: Données normalisées avec date, scheduled, cancelled et late_arrival.
            Les effectifs doivent être renseignés et cohérents.

    Returns:
        Tableau avec date et disruption_rate (fraction entre 0 et 1).
        Un dénominateur nul produit une valeur manquante, et non un taux nul.
    """
    grouped = df.groupby("date")[["scheduled", "cancelled", "late_arrival"]].sum()
    scheduled = grouped["scheduled"].replace(0, float("nan"))
    return ((grouped["cancelled"] + grouped["late_arrival"]) / scheduled).rename("disruption_rate").reset_index()
