"""Métriques synthétiques utilisées par la page Vue d'ensemble."""

import pandas as pd

from railinsight.analysis.history import monthly_delays_cancellations

CAUSE_COLUMNS = {
    "cause_external": "Causes externes",
    "cause_infra": "Infrastructure",
    "cause_traffic": "Gestion du trafic",
    "cause_rolling_stock": "Matériel roulant",
    "cause_station": "Gestion en gare",
    "cause_passengers": "Prise en charge des voyageurs",
}

MONTHS_FR = (
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
)


def global_kpis(df: pd.DataFrame) -> dict:
    """Indicateurs cumulés sur l'ensemble du réseau et de la période couverte."""
    scheduled = int(df["scheduled"].sum())
    cancelled = int(df["cancelled"].sum())
    late = int(df["late_arrival"].sum())
    effective = scheduled - cancelled
    dates = pd.to_datetime(df["date"])

    return {
        "n_routes": int(df["route"].nunique()),
        "date_min": dates.min(),
        "date_max": dates.max(),
        "scheduled": scheduled,
        "late_rate": (late / effective) if effective > 0 else None,
        "cancellation_rate": (cancelled / scheduled) if scheduled > 0 else None,
    }


def monthly_network_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne les taux mensuels du réseau et les volumes correspondants.

    Les taux sont calculés par les fonctions communes du module ``metrics`` via
    ``monthly_delays_cancellations`` : il s'agit de rapports de sommes, et non
    de moyennes de taux calculés liaison par liaison.
    """
    columns = ["date", "late_rate", "cancellation_rate", "scheduled", "cancelled"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    rates = monthly_delays_cancellations(working)
    volumes = working.groupby("date", as_index=False)[["scheduled", "cancelled"]].sum()
    return rates.merge(volumes, on="date", how="left").sort_values("date").reset_index(drop=True)


def _as_float_or_none(value) -> float | None:
    """Convertit une valeur numérique manquante en None."""
    return None if pd.isna(value) else float(value)


def latest_month_kpis(df: pd.DataFrame) -> dict:
    """Renvoie les taux du dernier mois et leur variation vs le mois précédent."""
    empty_result = {
        "date": None,
        "late_rate": None,
        "late_delta": None,
        "cancellation_rate": None,
        "cancellation_delta": None,
    }
    monthly = monthly_network_rates(df)
    if monthly.empty:
        return empty_result

    latest = monthly.iloc[-1]
    latest_period = latest["date"].to_period("M")
    previous_period = latest_period - 1
    previous_rows = monthly.loc[monthly["date"].dt.to_period("M") == previous_period]
    previous = previous_rows.iloc[0] if not previous_rows.empty else None

    late_rate = _as_float_or_none(latest["late_rate"])
    cancellation = _as_float_or_none(latest["cancellation_rate"])
    previous_late = _as_float_or_none(previous["late_rate"]) if previous is not None else None
    previous_cancellation = _as_float_or_none(previous["cancellation_rate"]) if previous is not None else None

    return {
        "date": latest["date"],
        "late_rate": late_rate,
        "late_delta": late_rate - previous_late if late_rate is not None and previous_late is not None else None,
        "cancellation_rate": cancellation,
        "cancellation_delta": (cancellation - previous_cancellation if cancellation is not None and previous_cancellation is not None else None),
    }


def overall_cause_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les six causes en pondérant leur part par le nombre de retards.

    Les colonnes de causes sont exprimées en pourcentage dans le dataset SNCF.
    Une ligne associée à davantage de trains en retard pèse donc davantage dans
    le résultat global.
    """
    columns = ["cause", "share"]
    required = {"late_arrival", *CAUSE_COLUMNS}
    if df.empty or not required.issubset(df.columns):
        return pd.DataFrame(columns=columns)

    weights = pd.to_numeric(df["late_arrival"], errors="coerce").fillna(0).clip(lower=0)
    total_weight = weights.sum()
    if total_weight <= 0:
        return pd.DataFrame(columns=columns)

    rows = []
    for column, label in CAUSE_COLUMNS.items():
        values = pd.to_numeric(df[column], errors="coerce").fillna(0)
        share = float((values * weights).sum() / total_weight)
        rows.append({"cause": label, "share": share})

    return pd.DataFrame(rows, columns=columns).sort_values("share", ascending=False).reset_index(drop=True)


def _rate_for_month_range(df: pd.DataFrame, start: pd.Period, end: pd.Period) -> float | None:
    """Calcule un taux de retard agrégé entre deux mois inclus."""
    periods = pd.to_datetime(df["date"]).dt.to_period("M")
    subset = df.loc[periods.between(start, end)]
    if subset.empty:
        return None

    scheduled = subset["scheduled"].sum()
    cancelled = subset["cancelled"].sum()
    effective = scheduled - cancelled
    if effective <= 0:
        return None
    return float(subset["late_arrival"].sum() / effective)


def format_month_fr(value) -> str:
    """Formate une date en mois/année avec un libellé français stable."""
    if value is None or pd.isna(value):
        return "—"
    date = pd.to_datetime(value)
    return f"{MONTHS_FR[date.month - 1]} {date.year}"


def overview_highlights(df: pd.DataFrame) -> dict:
    """Construit trois observations courtes pour contextualiser les KPI."""
    monthly = monthly_network_rates(df)
    default = {
        "trend": {
            "title": "Tendance récente",
            "text": "Les données disponibles ne permettent pas encore de comparer deux périodes de trois mois.",
            "status": "neutral",
        },
        "worst_month": {
            "title": "Mois le plus perturbé",
            "text": "Aucun taux mensuel exploitable n'est disponible.",
            "status": "neutral",
        },
        "dominant_cause": {
            "title": "Cause la plus représentée",
            "text": "La répartition des causes n'est pas disponible.",
            "status": "neutral",
        },
    }
    if monthly.empty:
        return default

    # Comparaison de deux fenêtres calendaires consécutives de trois mois.
    latest_period = monthly["date"].max().to_period("M")
    six_periods = pd.period_range(end=latest_period, periods=6, freq="M")
    observed_periods = set(monthly["date"].dt.to_period("M"))
    if set(six_periods).issubset(observed_periods):
        previous_start, previous_end = six_periods[0], six_periods[2]
        recent_start, recent_end = six_periods[3], six_periods[5]
        previous_rate = _rate_for_month_range(df, previous_start, previous_end)
        recent_rate = _rate_for_month_range(df, recent_start, recent_end)

        if previous_rate is not None and recent_rate is not None:
            delta_points = (recent_rate - previous_rate) * 100
            if delta_points < -0.1:
                status = "good"
                title = "Amélioration récente"
                verb = "diminué"
            elif delta_points > 0.1:
                status = "bad"
                title = "Dégradation récente"
                verb = "augmenté"
            else:
                status = "neutral"
                title = "Situation plutôt stable"
                verb = "est resté relativement stable"

            if status == "neutral":
                text = (
                    f"Le taux de retard {verb} : {previous_rate:.1%} sur les trois mois précédents "
                    f"et {recent_rate:.1%} sur les trois derniers mois disponibles."
                )
            else:
                text = (
                    f"Le taux de retard a {verb}, passant de {previous_rate:.1%} à {recent_rate:.1%} "
                    f"({delta_points:+.1f} point(s) sur les deux périodes de trois mois)."
                )
            default["trend"] = {"title": title, "text": text, "status": status}

    # Le mois est accompagné du volume de circulations effectives pour donner du contexte.
    valid_months = monthly.dropna(subset=["late_rate"])
    if not valid_months.empty:
        worst = valid_months.loc[valid_months["late_rate"].idxmax()]
        effective = worst["scheduled"] - worst["cancelled"]
        effective_label = f"{effective:,.0f}".replace(",", " ")
        default["worst_month"] = {
            "title": "Mois le plus perturbé",
            "text": (
                f"{format_month_fr(worst['date'])} présente le taux de retard mensuel le plus élevé "
                f"({worst['late_rate']:.1%}), pour {effective_label} circulations effectives."
            ),
            "status": "neutral",
        }

    causes = overall_cause_distribution(df)

    if not causes.empty and causes["share"].fillna(0).sum() > 0:
        dominant = causes.iloc[0]
        default["dominant_cause"] = {
            "title": "Cause la plus représentée",
            "text": (f"{dominant['cause']} arrive en tête avec une part pondérée " f"de {dominant['share']:.1f} % des causes de retard."),
            "status": "neutral",
        }
    else:
        default["dominant_cause"] = {
            "title": "Causes des retards",
            "text": "Répartition indisponible pour cette période.",
            "status": "neutral",
        }
    return default
