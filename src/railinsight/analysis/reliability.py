"""Métriques de la page Fiabilité des liaisons.

On résume chaque liaison sur toute la période : part de trains réellement arrivés
à l'heure (hors annulations et retards), afin de classer les liaisons de la plus
fiable à la moins fiable et de comparer les services.
"""

import pandas as pd


def route_reliability(df: pd.DataFrame) -> pd.DataFrame:
    """Indicateurs de fiabilité agrégés par liaison, sur toute la période.

    `reliability_score` = part des trains prévus qui ont circulé ET sont arrivés à
    l'heure = (prévus - annulés - en retard à l'arrivée) / prévus. Entre 0 et 1.
    """
    g = df.groupby("route")[["scheduled", "cancelled", "late_arrival"]].sum().reset_index()

    scheduled = g["scheduled"].replace(0, pd.NA)
    effective = (g["scheduled"] - g["cancelled"]).replace(0, pd.NA)

    g["late_rate"] = g["late_arrival"] / effective
    g["cancellation_rate"] = g["cancelled"] / scheduled
    g["reliability_score"] = (g["scheduled"] - g["cancelled"] - g["late_arrival"]) / scheduled
    return g


def reliability_by_service(df: pd.DataFrame) -> pd.DataFrame:
    """Fiabilité agrégée par service (National / International)."""
    if "service" not in df.columns:
        return pd.DataFrame(columns=["service", "scheduled", "late_rate", "cancellation_rate", "reliability_score"])

    g = df.groupby("service")[["scheduled", "cancelled", "late_arrival"]].sum().reset_index()
    scheduled = g["scheduled"].replace(0, pd.NA)
    effective = (g["scheduled"] - g["cancelled"]).replace(0, pd.NA)

    g["late_rate"] = g["late_arrival"] / effective
    g["cancellation_rate"] = g["cancelled"] / scheduled
    g["reliability_score"] = (g["scheduled"] - g["cancelled"] - g["late_arrival"]) / scheduled
    return g


def _ranked(df: pd.DataFrame, ascending: bool, n: int, min_scheduled: int) -> pd.DataFrame:
    """Classe les liaisons par score de fiabilité, après un seuil minimal de trafic."""
    rel = route_reliability(df)
    rel = rel[rel["scheduled"] >= min_scheduled]
    return rel.sort_values("reliability_score", ascending=ascending).head(n).reset_index(drop=True)


def top_reliable(df: pd.DataFrame, n: int = 10, min_scheduled: int = 0) -> pd.DataFrame:
    """Top N des liaisons les plus fiables (score le plus élevé)."""
    return _ranked(df, ascending=False, n=n, min_scheduled=min_scheduled)


def top_unreliable(df: pd.DataFrame, n: int = 10, min_scheduled: int = 0) -> pd.DataFrame:
    """Top N des liaisons les moins fiables (score le plus bas)."""
    return _ranked(df, ascending=True, n=n, min_scheduled=min_scheduled)
