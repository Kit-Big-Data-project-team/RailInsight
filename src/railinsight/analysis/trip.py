"""Analyse descriptive de Mon trajet : issues, évolution et sens inverse.

Toutes les fonctions travaillent sur des copies ou des agrégats. Elles ne
modifient ni la base, ni le nettoyage partagé, ni les données des autres pages.
"""

import pandas as pd

from railinsight.analysis.history import CAUSE_COLUMNS
from railinsight.exceptions import DataValidationError, PeriodOutOfRangeError

UNALLOCATED_CAUSE = "cause_unallocated"
CAUSE_TOTAL_TOLERANCE = 0.1
OUTCOME_LABELS = {"on_time": "À l'heure selon les seuils SNCF", "late": "Arrivées en retard", "cancelled": "Annulations"}


def _dates(df: pd.DataFrame) -> pd.Series:
    """Valide les dates et les ramène au premier jour du mois, sans imputation.

    Args:
        df: Enregistrements mensuels contenant date.

    Returns:
        Série de dates mensuelles, avec l'index d'origine.

    Raises:
        DataValidationError: Colonne absente ou date invalide.
    """
    if "date" not in df:
        raise DataValidationError("La date des observations est indisponible.")
    dates = pd.to_datetime(df["date"], errors="coerce")
    if dates.isna().any():
        raise DataValidationError("Certaines dates sont invalides ; aucun mois n'est imputé.")
    return dates.dt.to_period("M").dt.to_timestamp()


def _counts(df: pd.DataFrame) -> pd.DataFrame:
    """Valide les effectifs nécessaires sans supprimer ni corriger de ligne.

    Args:
        df: Données avec scheduled, cancelled et late_arrival.

    Returns:
        Copie numérique des trois colonnes d'effectifs.

    Raises:
        DataValidationError: Effectifs absents, non entiers, négatifs ou incompatibles.
    """
    columns = ["scheduled", "cancelled", "late_arrival"]
    if not set(columns).issubset(df.columns):
        raise DataValidationError("Les effectifs nécessaires au calcul sont indisponibles.")
    values = df[columns].apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any() or values.isin([float("inf"), -float("inf")]).any().any():
        raise DataValidationError("Certains effectifs sont absents ou invalides ; les résultats concernés sont indisponibles.")
    if (values < 0).any().any() or (values % 1 != 0).any().any():
        raise DataValidationError("Les effectifs doivent être des nombres entiers positifs ou nuls.")
    if (values["cancelled"] + values["late_arrival"] > values["scheduled"]).any():
        raise DataValidationError("Les annulations et retards dépassent les circulations prévues dans certaines observations.")
    return values.copy()


def filter_trip_period(df: pd.DataFrame, start: str | pd.Timestamp, end: str | pd.Timestamp) -> pd.DataFrame:
    """Sélectionne une période mensuelle inclusive sans ajouter les mois absents.

    Args:
        df: Données normalisées à filtrer.
        start: Premier mois demandé.
        end: Dernier mois demandé.

    Returns:
        Copie des enregistrements compris dans la période.

    Raises:
        PeriodOutOfRangeError: Bornes inversées.
        DataValidationError: Dates source invalides.
    """
    start = pd.Timestamp(start).to_period("M").to_timestamp()
    end = pd.Timestamp(end).to_period("M").to_timestamp()
    if start > end:
        raise PeriodOutOfRangeError("Le début de période doit précéder sa fin.")
    return df.loc[_dates(df).between(start, end)].copy()


def trip_summary(df: pd.DataFrame) -> dict[str, object]:
    """Calcule les indicateurs historiques d'une liaison et d'une période.

    Args:
        df: Enregistrements normalisés de la sélection, tous services présents inclus.

    Returns:
        Effectifs, nombre de mois distincts, taux et retard moyen des trains en retard.
        Les taux sont des rapports de sommes. Le retard est rapporté aux circulations
        effectuées ; les annulations et perturbations aux circulations prévues.
        cancellation_probability reste un alias historique du taux d'annulation,
        pour préserver les appels existants ; ce n'est pas une prévision.
        Sans dénominateur, le résultat est None. Une moyenne de retard absente ou
        négative pour un enregistrement ayant des retards rend cette moyenne
        indisponible, sans modifier les autres indicateurs.

    Raises:
        DataValidationError: Dates ou effectifs incohérents.
    """
    values = _counts(df)
    dates = _dates(df)
    scheduled = int(values["scheduled"].sum())
    cancelled = int(values["cancelled"].sum())
    late = int(values["late_arrival"].sum())
    operated = scheduled - cancelled
    mean_delay = None
    if late and "avg_delay_arrival" in df:
        delays = pd.to_numeric(df["avg_delay_arrival"], errors="coerce")
        relevant = values["late_arrival"] > 0
        usable = delays.notna() & ~delays.isin([float("inf"), -float("inf")]) & (delays >= 0)
        if usable[relevant].all():
            mean_delay = float((delays[relevant] * values.loc[relevant, "late_arrival"]).sum() / late)
    cancellation = cancelled / scheduled if scheduled else None
    return {
        "n_months": int(dates.nunique()),
        "n_records": len(df),
        "date_min": dates.min() if len(df) else None,
        "date_max": dates.max() if len(df) else None,
        "scheduled": scheduled,
        "cancelled": cancelled,
        "late_arrival": late,
        "on_time": operated - late,
        "operated": operated,
        "cancellation_probability": cancellation,
        "cancellation_rate": cancellation,
        "late_rate": late / operated if operated else None,
        "disruption_rate": (cancelled + late) / scheduled if scheduled else None,
        "avg_delay_arrival": mean_delay,
    }


def outcomes_per_100(df: pd.DataFrame) -> pd.DataFrame:
    """Exprime les trois issues historiques sur une base de 100 circulations prévues.

    Args:
        df: Sélection d'une liaison et d'une période.

    Returns:
        Tableau outcome, per_100 et count. Les valeurs ne sont pas arrondies
        dans le calcul et leur somme vaut 100. Ce sont des fréquences descriptives,
        pas la prédiction de cent prochains trains. Sans train prévu, tableau vide.

    Raises:
        DataValidationError: Effectifs ou dates invalides, selon trip_summary.
    """
    summary = trip_summary(df)
    if not summary["scheduled"]:
        return pd.DataFrame(columns=["outcome", "per_100", "count"])
    counts = {"on_time": summary["on_time"], "late": summary["late_arrival"], "cancelled": summary["cancelled"]}
    return pd.DataFrame([{"outcome": OUTCOME_LABELS[key], "per_100": value / summary["scheduled"] * 100, "count": value} for key, value in counts.items()])


def recent_trip_evolution(df: pd.DataFrame) -> dict[str, object]:
    """Compare les douze derniers mois disponibles aux douze précédents de la sélection.

    Args:
        df: Données d'une liaison déjà limitées à la période choisie.

    Returns:
        available, reason, periods et deltas_pp. Il faut les 24 mois consécutifs
        se terminant au dernier mois observé de la sélection ; aucun mois absent
        n'est remplacé par zéro et aucune observation hors sélection n'est utilisée.
        periods contient les deux périodes, effectifs et trois taux. Les écarts
        sont récents moins précédents, en points de pourcentage ; ils ne prédisent
        pas l'avenir. Une base sans circulations rend la comparaison indisponible.

    Raises:
        DataValidationError: Données incohérentes.
    """
    dates = _dates(df)
    unavailable = {"available": False, "periods": pd.DataFrame(), "deltas_pp": {}}
    if df.empty:
        return {**unavailable, "reason": "Aucune observation dans la sélection."}
    end = dates.max()
    start = end - pd.DateOffset(months=23)
    expected = pd.date_range(start, end, freq="MS")
    if not set(expected).issubset(set(dates)):
        return {**unavailable, "reason": "Il faut 24 mois consécutifs dans la sélection pour comparer deux périodes de douze mois."}
    current_start = end - pd.DateOffset(months=11)
    previous_end = current_start - pd.DateOffset(months=1)
    rows = []
    for label, first, last in [("Période précédente", start, previous_end), ("Période récente", current_start, end)]:
        summary = trip_summary(df.loc[dates.between(first, last)])
        if not summary["scheduled"]:
            return {**unavailable, "reason": "Une des périodes ne contient aucune circulation prévue."}
        rows.append({"period": label, "start": first, "end": last, **{key: summary[key] for key in ("scheduled", "late_rate", "cancellation_rate", "disruption_rate")}})
    table = pd.DataFrame(rows)
    deltas = {}
    for key in ("late_rate", "cancellation_rate", "disruption_rate"):
        before, after = table[key].iloc[0], table[key].iloc[1]
        deltas[key] = None if pd.isna(before) or pd.isna(after) else float((after - before) * 100)
    return {"available": True, "reason": None, "periods": table, "deltas_pp": deltas}


def reverse_trip_comparison(df: pd.DataFrame, route: str, start: str | pd.Timestamp, end: str | pd.Timestamp) -> dict[str, object]:
    """Compare les deux directions sur les seuls mois disponibles en commun.

    Args:
        df: Jeu normalisé complet avec route, origin et destination.
        route: Liaison orientée choisie.
        start: Début de la période demandée.
        end: Fin de la période demandée.

    Returns:
        Disponibilité, motif, tableau par direction, mois communs et nombre de
        mois calendaires demandés. Les mois absents ne sont pas imputés et les
        effectifs sont regroupés avant division. Les indicateurs de comparaison
        peuvent différer de la synthèse si leur période commune est plus courte.

    Raises:
        DataValidationError: Origine/destination ambiguë ou données incohérentes.
        PeriodOutOfRangeError: Bornes inversées.
    """
    unavailable = {"available": False, "directions": pd.DataFrame(), "common_months": [], "n_requested_months": 0}
    if not {"origin", "destination", "route"}.issubset(df.columns):
        return {**unavailable, "reason": "Les informations de direction ne sont pas disponibles."}
    forward = df.loc[df["route"] == route]
    if forward.empty:
        return {**unavailable, "reason": "La liaison choisie n'est pas disponible."}
    pair = forward[["origin", "destination"]].drop_duplicates()
    if len(pair) != 1 or pair.isna().any().any():
        raise DataValidationError("L'origine ou la destination de cette liaison est ambiguë.")
    origin, destination = pair.iloc[0]
    backward = df.loc[(df["origin"] == destination) & (df["destination"] == origin)]
    if backward.empty:
        return {**unavailable, "reason": "Le sens inverse n'est pas disponible dans les données."}
    forward = filter_trip_period(forward, start, end)
    backward = filter_trip_period(backward, start, end)
    common = sorted(set(_dates(forward)) & set(_dates(backward)))
    if not common:
        return {**unavailable, "reason": "Aucun mois commun aux deux directions dans la période choisie."}
    rows = []
    for label, part in [(route, forward), (f"{destination} → {origin}", backward)]:
        part = part.loc[_dates(part).isin(common)]
        summary = trip_summary(part)
        if not summary["scheduled"]:
            return {**unavailable, "reason": "Une des directions ne contient aucune circulation prévue sur les mois communs."}
        rows.append({"direction": label, **{key: summary[key] for key in ("scheduled", "n_months", "late_rate", "cancellation_rate", "disruption_rate")}})
    requested = len(pd.date_range(pd.Timestamp(start).to_period("M").to_timestamp(), pd.Timestamp(end).to_period("M").to_timestamp(), freq="MS"))
    return {"available": True, "reason": None, "directions": pd.DataFrame(rows), "common_months": common, "n_requested_months": requested}


def average_causes(df: pd.DataFrame) -> pd.Series:
    """Conserve les parts déclarées et complète la ventilation inconnue en gris.

    Args:
        df: Données avec late_arrival et les six CAUSE_COLUMNS.

    Returns:
        Six parts pondérées par les retards et cause_unallocated, en pourcentages.
        Le complément à 100 est calculé par ligne avant pondération. Une valeur
        absente reste dans le complément ; aucune part déclarée n'est renormalisée.
        Une tolérance de 0,1 point absorbe les arrondis. Sans retard, toutes les
        parts sont manquantes plutôt que remplacées par une moyenne artificielle.
        Cette pondération reprend l'hypothèse approuvée pour l'historique.

    Raises:
        DataValidationError: Poids absents/négatifs, pourcentages hors de [0,100]
            ou ventilation supérieure à 100 au-delà de la tolérance.
    """
    if not {"late_arrival", *CAUSE_COLUMNS}.issubset(df.columns):
        raise DataValidationError("Les colonnes nécessaires à la répartition des causes sont indisponibles.")
    weights = pd.to_numeric(df["late_arrival"], errors="coerce")
    values = df[CAUSE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if weights.isna().any() or (weights < 0).any() or weights.isin([float("inf"), -float("inf")]).any():
        raise DataValidationError("Les effectifs de retard nécessaires aux causes sont invalides.")
    if ((values < 0) | (values > 100)).any().any():
        raise DataValidationError("Les pourcentages des causes doivent être compris entre 0 et 100.")
    totals = values.sum(axis=1)
    if (totals > 100 + CAUSE_TOTAL_TOLERANCE).any():
        raise DataValidationError("La somme des causes dépasse 100 % au-delà des arrondis tolérés.")
    values = values.copy()
    residual = (100 - totals).clip(lower=0)
    values[UNALLOCATED_CAUSE] = residual.where(residual > CAUSE_TOTAL_TOLERANCE, 0.0)
    total = weights.sum()
    if total == 0:
        return pd.Series(float("nan"), index=[*CAUSE_COLUMNS, UNALLOCATED_CAUSE])
    return values.fillna(0).multiply(weights, axis=0).sum() / total
