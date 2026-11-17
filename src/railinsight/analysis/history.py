"""Métriques de la page Historique & évolution.

Évolution des retards et des annulations dans le temps, répartition des causes,
sévérité, comparaison des services et saisonnalité. Toutes les fonctions sont pures : elles prennent le DataFrame
normalisé (contrat de données) et renvoient un DataFrame prêt à visualiser.
"""

import pandas as pd

from railinsight.analysis.metrics import cancellation_rate, monthly_disruption_rate, monthly_late_rate
from railinsight.exceptions import DataValidationError

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
    """Réunit les trois taux mensuels, exprimés en fractions.

    Args:
        df: Données normalisées avec date et effectifs des trains prévus,
            annulés et arrivés en retard.

    Returns:
        Tableau avec date, late_rate, cancellation_rate et disruption_rate.
        Le retard porte sur les trains ayant circulé ; les deux autres taux
        portent sur les trains prévus. Les courbes ne sont pas additives.
        Plusieurs liaisons peuvent compter le même TGV : leur regroupement
        décrit les enregistrements disponibles, pas les taux officiels du réseau.
    """
    late = monthly_late_rate(df)
    cancelled = cancellation_rate(df)
    disrupted = monthly_disruption_rate(df)
    return late.merge(cancelled, on="date").merge(disrupted, on="date")


# Tolérance en points de pourcentage : arrondis de publication, sans renormalisation.
CAUSE_TOTAL_TOLERANCE = 0.1
UNALLOCATED_CAUSE = "cause_unallocated"


def cause_breakdown_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les causes déclarées et leur part non ventilée, par mois.

    Hypothèse approuvée : les pourcentages décrivent une répartition des retards
    à l'arrivée ; leur pondération utilise donc late_arrival. Les métadonnées
    SNCF ne confirment pas explicitement ce dénominateur. Le résultat est une
    estimation sur les enregistrements des liaisons, pas un indicateur officiel.

    Le complément à 100 est calculé pour chaque enregistrement avant pondération.
    Une cause manquante n'ajoute aucune part connue ; elle reste dans le complément.
    Les six parts publiées ne sont jamais renormalisées. Un écart de 0,1 point
    au maximum est toléré comme arrondi, sans créer de part non ventilée.

    Args:
        df: Données normalisées avec date, late_arrival et les six CAUSE_COLUMNS.

    Returns:
        Tableau avec date, les six causes et cause_unallocated, en pourcentages
        de 0 à 100. Sans retard, toutes les parts restent manquantes.
        Une sélection vide conserve ces mêmes colonnes.

    Raises:
        DataValidationError: Effectif manquant ou négatif, pourcentage hors de
            [0, 100], ou somme dépassant 100 au-delà de la tolérance d'arrondi.
    """
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["date"])
    weights = tmp["late_arrival"]
    values = tmp[CAUSE_COLUMNS]
    if weights.isna().any() or (weights < 0).any():
        raise DataValidationError("Les effectifs de retard doivent être renseignés et positifs ou nuls.")
    if ((values < 0) | (values > 100)).any().any():
        raise DataValidationError("Les pourcentages des causes doivent être compris entre 0 et 100.")
    totals = values.sum(axis=1)
    if (totals > 100 + CAUSE_TOTAL_TOLERANCE).any():
        raise DataValidationError("La somme des causes dépasse 100 % au-delà de la tolérance de 0,1 point.")
    residual = (100 - totals).clip(lower=0)
    tmp[UNALLOCATED_CAUSE] = residual.where(residual > CAUSE_TOTAL_TOLERANCE, 0.0)
    columns = [*CAUSE_COLUMNS, UNALLOCATED_CAUSE]
    rows = []
    for date, group in tmp.groupby("date"):
        weights = group["late_arrival"]
        total = weights.sum()
        shares = group[columns].fillna(0).multiply(weights, axis=0).sum() / total if total > 0 else pd.Series(float("nan"), index=columns)
        rows.append({"date": date, **shares.to_dict()})
    return pd.DataFrame(rows, columns=["date", *columns])


def seasonality(df: pd.DataFrame, complete_years_only: bool = True) -> pd.DataFrame:
    """Compare les mois de l'année par rapports de sommes des effectifs.

    Les années complètes sont déterminées sur la sélection courante : chaque
    année doit contenir les douze mois. Aucun mois ni aucune année manquante
    n'est imputé. Les années exceptionnelles, dont 2020, ne sont pas exclues.
    Ce descriptif ne démontre pas un effet saisonnier récurrent ou causal.

    Args:
        df: Données normalisées avec date, scheduled, cancelled et late_arrival.
        complete_years_only: Conserver uniquement les années couvrant douze mois.

    Returns:
        Tableau avec month, les trois taux et n_years (années contributrices).
        Un dénominateur nul donne une valeur manquante. Sans année complète,
        le résultat par défaut est vide ; aucun changement de méthode n'est effectué.
    """
    columns = ["month", "late_rate", "cancellation_rate", "disruption_rate", "n_years"]
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["date"])
    tmp["year"] = tmp["date"].dt.year
    tmp["month"] = tmp["date"].dt.month
    if complete_years_only:
        coverage = tmp.groupby("year")["month"].nunique()
        tmp = tmp[tmp["year"].isin(coverage[coverage == 12].index)]
    if tmp.empty:
        return pd.DataFrame(columns=columns)
    grouped = tmp.groupby("month")[["scheduled", "cancelled", "late_arrival"]].sum()
    operated = (grouped["scheduled"] - grouped["cancelled"]).replace(0, float("nan"))
    scheduled = grouped["scheduled"].replace(0, float("nan"))
    grouped["late_rate"] = grouped["late_arrival"] / operated
    grouped["cancellation_rate"] = grouped["cancelled"] / scheduled
    grouped["disruption_rate"] = (grouped["cancelled"] + grouped["late_arrival"]) / scheduled
    grouped["n_years"] = tmp.groupby("month")["year"].nunique()
    return grouped.reset_index()[columns]


def punctuality_by_service(df: pd.DataFrame) -> pd.DataFrame:
    """Compare les taux mensuels par service, selon la contribution d'Abdelmounaim.

    Args:
        df: Données normalisées avec date, service et effectifs de circulation.

    Returns:
        Tableau date, service et late_rate, calculé sur les trains ayant circulé.
        Sans colonne service, le tableau est vide. Les écarts descriptifs peuvent
        refléter des différences de liaisons et de durées, sans établir de causalité.
    """
    if "service" not in df.columns:
        return pd.DataFrame(columns=["date", "service", "late_rate"])

    g = df.groupby(["date", "service"])[["scheduled", "cancelled", "late_arrival"]].sum().reset_index()
    effective = (g["scheduled"] - g["cancelled"]).replace(0, pd.NA)
    g["late_rate"] = g["late_arrival"] / effective
    return g[["date", "service", "late_rate"]]


def delay_severity_over_time(df: pd.DataFrame) -> pd.DataFrame:
    """Adapte les seuils de sévérité d'Abdelmounaim sans corriger les données brutes.

    Args:
        df: Données normalisées avec date, scheduled, late_15, late_30 et late_60.

    Returns:
        Tableau mensuel des trois parts rapportées aux trains prévus. Si un
        effectif d'un seuil est manquant ou négatif dans un mois, le résultat de
        ce mois pour ce seul seuil est manquant. Les autres seuils sont conservés.
        Un dénominateur nul donne aussi une valeur manquante. Les seuils sont
        cumulatifs et leurs parts ne doivent pas être additionnées.
    """
    thresholds = ["late_15", "late_30", "late_60"]
    grouped = df.groupby("date")[["scheduled", *thresholds]].sum(min_count=1)
    scheduled = grouped["scheduled"].replace(0, float("nan"))
    for column in thresholds:
        invalid = df.assign(invalid=df[column].isna() | (df[column] < 0)).groupby("date")["invalid"].any()
        grouped[column] = (grouped[column] / scheduled).mask(invalid)
    return grouped.reset_index()[["date", *thresholds]]


def severity_source_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Expose les valeurs négatives ou absentes des seuils, sans modifier la source.

    Args:
        df: Données normalisées avec les seuils de sévérité.

    Returns:
        Tableau des anomalies avec date, liaison et service si disponibles,
        seuil et valeur brute. Les valeurs servent au diagnostic et non à un calcul.
    """
    identifiers = [column for column in ("date", "route", "service") if column in df]
    long = df.melt(id_vars=identifiers, value_vars=["late_15", "late_30", "late_60"], var_name="seuil", value_name="valeur_source")
    return long.loc[long["valeur_source"].isna() | (long["valeur_source"] < 0)].reset_index(drop=True)


def history_period_summary(df: pd.DataFrame) -> dict[str, int | float | None]:
    """Calcule les indicateurs de synthèse ajoutés par Abdelmounaim, hors interface.

    Args:
        df: Enregistrements normalisés de la période et de la liaison sélectionnées.

    Returns:
        Effectif prévu et trois taux sur la période, calculés après addition des
        effectifs. Les taux ne sont pas des moyennes arithmétiques des mois.
        Un dénominateur nul produit None.
    """
    scheduled = int(df["scheduled"].sum())
    cancelled = int(df["cancelled"].sum())
    late = int(df["late_arrival"].sum())
    operated = scheduled - cancelled
    return {
        "scheduled": scheduled,
        "late_rate": late / operated if operated else None,
        "cancellation_rate": cancelled / scheduled if scheduled else None,
        "disruption_rate": (cancelled + late) / scheduled if scheduled else None,
    }


def history_trend_observations(df: pd.DataFrame) -> dict[str, object]:
    """Extrait des constats descriptifs sur la sélection, sans expliquer leurs causes.

    Args:
        df: Données normalisées de la liaison et de la période sélectionnées.

    Returns:
        Nombre de mois observés et calculables, taux maximal de perturbation,
        tous les mois ex aequo et leurs effectifs, indicateur de taux constant,
        et parts des annulations et retards dans les perturbations de la période.
        Ces deux dernières parts ont le même dénominateur : annulés + retards.
        Sans perturbation, elles restent manquantes. Les mois à dénominateur nul
        sont exclus du maximum et aucun mois absent n'est reconstitué.
    """
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["date"])
    monthly = monthly_delays_cancellations(tmp)
    counts = tmp.groupby("date")[["scheduled", "cancelled", "late_arrival"]].sum().reset_index()
    monthly = monthly.merge(counts, on="date")
    valid = monthly.dropna(subset=["disruption_rate"])
    maximum = float(valid["disruption_rate"].max()) if not valid.empty else None
    peaks = valid.loc[valid["disruption_rate"] == maximum].copy()
    cancelled = int(tmp["cancelled"].sum())
    late = int(tmp["late_arrival"].sum())
    disrupted = cancelled + late
    return {
        "n_months": len(monthly),
        "n_valid_months": len(valid),
        "peak_disruption_rate": maximum,
        "peak_months": peaks[["date", "scheduled", "cancelled", "late_arrival"]],
        "constant_rate": len(valid) > 1 and valid["disruption_rate"].nunique() == 1,
        "disrupted_count": disrupted,
        "cancelled_share": cancelled / disrupted if disrupted else None,
        "late_share": late / disrupted if disrupted else None,
    }


def history_cause_observations(df: pd.DataFrame) -> dict[str, object]:
    """Résume les parts déclarées sur la période selon la pondération approuvée.

    Args:
        df: Données normalisées avec date, late_arrival et les six causes.

    Returns:
        Toutes les catégories déclarées ex aequo pour la plus grande part,
        cette part en pourcentage, et la part non ventilée de la période.
        Les parts mensuelles sont pondérées par leurs effectifs de retards,
        sans moyenne simple entre mois ni redistribution de la part inconnue.
        Sans retard, les parts sont manquantes et aucune catégorie n'est désignée.

    Raises:
        DataValidationError: Données incompatibles avec le contrat des causes,
            selon les mêmes règles que cause_breakdown_over_time.
    """
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["date"])
    monthly = cause_breakdown_over_time(tmp)
    if monthly.empty:
        return {"leaders": [], "largest_reported_share": None, "unallocated_share": None}
    counts = tmp.groupby("date")["late_arrival"].sum().reset_index()
    weighted = monthly.merge(counts, on="date")
    total = weighted["late_arrival"].sum()
    if total == 0:
        return {"leaders": [], "largest_reported_share": None, "unallocated_share": None}
    columns = [*CAUSE_COLUMNS, UNALLOCATED_CAUSE]
    shares = weighted[columns].multiply(weighted["late_arrival"], axis=0).sum() / total
    known = shares[CAUSE_COLUMNS]
    largest = float(known.max())
    leaders = known.index[known == largest].tolist() if largest > 0 else []
    return {"leaders": leaders, "largest_reported_share": largest, "unallocated_share": float(shares[UNALLOCATED_CAUSE])}
