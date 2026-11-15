"""Indicateurs globaux de la page Overview (tâche 3)."""

import pandas as pd


def global_kpis(df: pd.DataFrame) -> dict:
    """Indicateurs clés sur l'ensemble du réseau et de la période couverte."""
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
        "late_rate": (late / effective) if effective else None,
        "cancellation_rate": (cancelled / scheduled) if scheduled else None,
    }
