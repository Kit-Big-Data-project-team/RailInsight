"""Tests des constats descriptifs de la sélection historique."""

import pandas as pd
import pytest

from railinsight.analysis.history import CAUSE_COLUMNS, history_cause_observations, history_trend_observations


def _data():
    """Trois mois aux volumes et perturbations différents, dont deux lignes en janvier."""
    return pd.DataFrame(
        [
            {
                "date": date,
                "scheduled": scheduled,
                "cancelled": cancelled,
                "late_arrival": late,
                **{cause: 100.0 if cause == "cause_infra" else 0.0 for cause in CAUSE_COLUMNS},
            }
            for date, scheduled, cancelled, late in [
                ("2025-01-01", 10, 2, 3),
                ("2025-01-01", 90, 0, 5),
                ("2025-02-01", 100, 10, 20),
                ("2025-03-01", 100, 0, 0),
            ]
        ]
    )


def test_peak_uses_pooled_monthly_rate_and_reports_counts():
    """Le maximum est déterminé après regroupement, avec son volume d'exposition."""
    result = history_trend_observations(_data())
    assert result["peak_disruption_rate"] == pytest.approx(0.3)
    assert result["peak_months"].date.tolist() == [pd.Timestamp("2025-02-01")]
    assert result["peak_months"].scheduled.tolist() == [100]
    assert result["cancelled_share"] == pytest.approx(12 / 40)
    assert result["late_share"] == pytest.approx(28 / 40)
    assert result["n_months"] == 3


def test_peak_preserves_all_tied_months():
    """Un ex aequo n'est pas départagé arbitrairement."""
    df = _data()
    df.loc[3, "cancelled"] = 30
    result = history_trend_observations(df)
    assert len(result["peak_months"]) == 2
    assert not result["constant_rate"]


def test_constant_rates_are_not_described_as_a_unique_peak():
    """Une série constante est distinguée d'un mois exceptionnel."""
    df = _data().iloc[[2, 3]].copy()
    df.loc[:, "late_arrival"] = 0
    df.loc[:, "cancelled"] = 10
    result = history_trend_observations(df)
    assert result["constant_rate"]
    assert result["cancelled_share"] == 1
    assert result["late_share"] == 0


@pytest.mark.parametrize("empty", [False, True])
def test_no_disruption_or_no_observation_does_not_invent_a_breakdown(empty):
    """Sans événement, aucune part parmi les perturbations n'est inventée."""
    df = _data()
    df[["cancelled", "late_arrival"]] = 0
    if empty:
        df = df.iloc[:0]
    result = history_trend_observations(df)
    assert result["cancelled_share"] is None
    assert result["late_share"] is None
    assert result["disrupted_count"] == 0


def test_zero_denominator_is_excluded_from_peak():
    """Un taux indisponible n'est pas interprété comme zéro ni comme un maximum."""
    df = _data().iloc[:1].copy()
    df[["scheduled", "cancelled", "late_arrival"]] = 0
    result = history_trend_observations(df)
    assert result["peak_disruption_rate"] is None
    assert result["peak_months"].empty
    assert result["n_valid_months"] == 0


def test_causes_are_weighted_across_months_without_redistributing_unknown_share():
    """Les mois ont un poids lié aux retards ; une part non ventilée reste inconnue."""
    df = _data().iloc[[0, 2]].copy()
    df.loc[:, CAUSE_COLUMNS] = 0.0
    df.loc[df.index[0], "cause_infra"] = 100
    df.loc[df.index[1], "cause_external"] = 50
    result = history_cause_observations(df)
    assert result["leaders"] == ["cause_external"]
    assert result["largest_reported_share"] == pytest.approx(50 * 20 / 23)
    assert result["unallocated_share"] == pytest.approx(50 * 20 / 23)


def test_cause_ties_preserve_all_leaders():
    """Deux catégories de même part sont toutes les deux signalées."""
    df = _data().iloc[:1].copy()
    df.loc[:, CAUSE_COLUMNS] = 0.0
    df["cause_infra"] = 50
    df["cause_external"] = 50
    result = history_cause_observations(df)
    assert set(result["leaders"]) == {"cause_infra", "cause_external"}


def test_all_unallocated_data_does_not_name_a_known_cause():
    """Une ventilation entièrement absente ne désigne aucune cause dominante."""
    df = _data()
    df.loc[:, CAUSE_COLUMNS] = 0.0
    result = history_cause_observations(df)
    assert result["leaders"] == []
    assert result["unallocated_share"] == 100


@pytest.mark.parametrize("empty", [False, True])
def test_cause_observations_without_delays_remain_unavailable(empty):
    """Sans retard, la présence de pourcentages ne justifie pas un constat de causes."""
    df = _data()
    df["late_arrival"] = 0
    if empty:
        df = df.iloc[:0]
    assert history_cause_observations(df) == {"leaders": [], "largest_reported_share": None, "unallocated_share": None}


def test_observations_do_not_mutate_input():
    """Les constats de la page ne modifient pas les données partagées."""
    df = _data()
    before = df.copy(deep=True)
    history_trend_observations(df)
    history_cause_observations(df)
    pd.testing.assert_frame_equal(df, before)
