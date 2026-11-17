"""Tests des métriques communes de régularité (socle partagé par toutes les pages)."""

import pandas as pd
import pytest

from railinsight.analysis.metrics import cancellation_rate, monthly_disruption_rate, monthly_late_rate


def test_monthly_late_rate_aggregates_by_month():
    """Le taux est un rapport de sommes : on agrège d'abord, puis on divise."""
    df = pd.DataFrame(
        {
            "date": ["2026-01", "2026-01", "2026-02"],
            "scheduled": [100, 100, 50],
            "cancelled": [0, 0, 0],
            "late_arrival": [10, 10, 5],
        }
    )
    out = monthly_late_rate(df)

    assert out.loc[out["date"] == "2026-01", "late_rate"].iloc[0] == 20 / 200
    assert out.loc[out["date"] == "2026-02", "late_rate"].iloc[0] == 5 / 50


def test_monthly_late_rate_handles_fully_cancelled_month():
    """Un mois entièrement annulé (ex. grève) ne doit pas produire d'infini."""
    df = pd.DataFrame(
        {
            "date": ["2026-03"],
            "scheduled": [40],
            "cancelled": [40],  # tout annulé -> dénominateur = 0
            "late_arrival": [0],
        }
    )
    out = monthly_late_rate(df)

    assert pd.isna(out["late_rate"].iloc[0])


def test_cancellation_rate_aggregates_by_month():
    """Taux d'annulation = annulés / prévus, en rapport de sommes."""
    df = pd.DataFrame(
        {
            "date": ["2026-01", "2026-01"],
            "scheduled": [100, 100],
            "cancelled": [1, 3],
        }
    )
    out = cancellation_rate(df)

    assert out["cancellation_rate"].iloc[0] == 4 / 200


@pytest.mark.parametrize(
    ("scheduled", "cancelled", "late", "expected"),
    [(100, 10, 18, 0.28), (100, 0, 0, 0.0), (100, 100, 0, 1.0), (100, 0, 100, 1.0)],
)
def test_disruption_rate_for_distinct_outcomes(scheduled, cancelled, late, expected):
    """Vérifie les issues normales, sans perturbation et totalement perturbées."""
    df = pd.DataFrame({"date": ["2026-01"], "scheduled": [scheduled], "cancelled": [cancelled], "late_arrival": [late]})
    assert monthly_disruption_rate(df)["disruption_rate"].iloc[0] == pytest.approx(expected)


def test_disruption_aggregates_counts_instead_of_averaging_rates():
    """Une petite liaison ne doit pas peser autant qu'une liaison très fréquentée."""
    df = pd.DataFrame({"date": ["2026-01", "2026-01", "2026-02"], "scheduled": [10, 90, 50], "cancelled": [2, 0, 0], "late_arrival": [3, 5, 5]})
    out = monthly_disruption_rate(df).set_index("date")
    assert out.loc["2026-01", "disruption_rate"] == pytest.approx(10 / 100)
    assert out.loc["2026-02", "disruption_rate"] == pytest.approx(5 / 50)


def test_disruption_rate_zero_denominator_is_missing():
    """Un mois sans trains prévus n'est pas présenté comme parfaitement fiable."""
    df = pd.DataFrame({"date": ["2026-01"], "scheduled": [0], "cancelled": [0], "late_arrival": [0]})
    assert pd.isna(monthly_disruption_rate(df)["disruption_rate"].iloc[0])


def test_disruption_rate_empty_input_preserves_schema():
    """Une sélection vide conserve le contrat du tableau de sortie."""
    df = pd.DataFrame(columns=["date", "scheduled", "cancelled", "late_arrival"])
    out = monthly_disruption_rate(df)
    assert out.empty
    assert list(out.columns) == ["date", "disruption_rate"]


def test_disruption_rate_does_not_mutate_input():
    """Le calcul partagé ne modifie pas les données des autres graphiques."""
    df = pd.DataFrame({"date": ["2026-01"], "scheduled": [100], "cancelled": [10], "late_arrival": [18]})
    original = df.copy(deep=True)
    monthly_disruption_rate(df)
    pd.testing.assert_frame_equal(df, original)
