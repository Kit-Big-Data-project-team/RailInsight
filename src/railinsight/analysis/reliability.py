"""Métriques de la page Fiabilité des liaisons.

On résume chaque liaison sur toute la période : part de trains réellement arrivés
à l'heure (hors annulations et retards), afin de classer les liaisons de la plus
fiable à la moins fiable et de comparer les services.
"""

import pandas as pd


def _add_reliability_metrics(g: pd.DataFrame) -> pd.DataFrame:
    """Ajoute late_rate, cancellation_rate et reliability_score à des effectifs agrégés.

    `reliability_score` = (prévus - annulés - en retard à l'arrivée) / prévus, entre 0 et 1.
    Le calcul repose sur l'indicateur de retard à l'arrivée fourni par les données SNCF,
    pas sur les seuils fixes 15/30/60 min (utilisés séparément pour la sévérité).

    Les effectifs agrégés incohérents (annulés > prévus, retards > circulés, valeurs
    négatives) ne peuvent pas produire un score valide : les métriques concernées sont
    alors marquées NULL, afin que l'anomalie reste visible plutôt que masquée par un
    bornage artificiel (clip 0–1).
    """
    scheduled = g["scheduled"].replace(0, pd.NA)
    effective_raw = g["scheduled"] - g["cancelled"]
    effective = effective_raw.replace(0, pd.NA)

    g["late_rate"] = g["late_arrival"] / effective
    g["cancellation_rate"] = g["cancelled"] / scheduled
    g["reliability_score"] = (g["scheduled"] - g["cancelled"] - g["late_arrival"]) / scheduled

    impossible = (g[["scheduled", "cancelled", "late_arrival"]] < 0).any(axis=1) | (g["cancelled"] > g["scheduled"]) | (g["late_arrival"] > effective_raw)
    g.loc[impossible, ["late_rate", "cancellation_rate", "reliability_score"]] = pd.NA
    return g


def route_reliability(df: pd.DataFrame) -> pd.DataFrame:
    """Indicateurs de fiabilité agrégés par liaison, sur toute la période.

    Plus le score est élevé, plus la liaison présente une bonne régularité sur la
    période étudiée. Voir ``_add_reliability_metrics`` pour la définition exacte et
    le traitement des effectifs incohérents.
    """
    g = df.groupby("route")[["scheduled", "cancelled", "late_arrival"]].sum().reset_index()
    return _add_reliability_metrics(g)


def reliability_by_service(df: pd.DataFrame) -> pd.DataFrame:
    """Fiabilité agrégée par service (National / International)."""
    if "service" not in df.columns:
        return pd.DataFrame(columns=["service", "scheduled", "late_rate", "cancellation_rate", "reliability_score"])

    g = df.groupby("service")[["scheduled", "cancelled", "late_arrival"]].sum().reset_index()
    return _add_reliability_metrics(g)


def _ranked(df: pd.DataFrame, ascending: bool, n: int, min_scheduled: int) -> pd.DataFrame:
    """Classe les liaisons par score de fiabilité, après un seuil minimal de trafic.

    Les liaisons dont le score est invalide (effectifs incohérents) sont exclues du
    classement plutôt que d'y figurer avec une valeur aberrante.
    """
    rel = route_reliability(df)
    rel = rel[rel["scheduled"] >= min_scheduled]
    rel = rel.dropna(subset=["reliability_score"])
    return rel.sort_values("reliability_score", ascending=ascending).head(n).reset_index(drop=True)


def top_reliable(df: pd.DataFrame, n: int = 10, min_scheduled: int = 0) -> pd.DataFrame:
    """Top N des liaisons les plus fiables (score le plus élevé)."""
    return _ranked(df, ascending=False, n=n, min_scheduled=min_scheduled)


def top_unreliable(df: pd.DataFrame, n: int = 10, min_scheduled: int = 0) -> pd.DataFrame:
    """Top N des liaisons les moins fiables (score le plus bas)."""
    return _ranked(df, ascending=True, n=n, min_scheduled=min_scheduled)
