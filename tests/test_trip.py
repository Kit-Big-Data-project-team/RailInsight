"""Tests des indicateurs et comparaisons de Mon trajet, sans base réelle."""

import pandas as pd
import pytest

from railinsight.analysis.history import CAUSE_COLUMNS
from railinsight.analysis.trip import (
    average_causes,
    filter_trip_period,
    outcomes_per_100,
    recent_trip_evolution,
    reverse_trip_comparison,
    trip_summary,
)
from railinsight.exceptions import DataValidationError, PeriodOutOfRangeError


def _row(date="2025-01-01", origin="A", destination="B", **changes):
    """Construit une observation mensuelle cohérente avec le contrat partagé."""
    row = {
        "date": pd.Timestamp(date),
        "origin": origin,
        "destination": destination,
        "route": f"{origin} → {destination}",
        "service": "National",
        "scheduled": 100,
        "cancelled": 10,
        "late_arrival": 18,
        "avg_delay_arrival": 12.0,
        **{column: 100.0 if column == "cause_infra" else 0.0 for column in CAUSE_COLUMNS},
    }
    row.update(changes)
    return row


def _history():
    """Deux périodes complètes de douze mois avec une hausse connue des perturbations."""
    return pd.DataFrame(
        [
            _row(date, cancelled=0 if i < 12 else 10, late_arrival=10 if i < 12 else 20)
            for i, date in enumerate(pd.date_range("2024-10-01", "2026-09-01", freq="MS"))
        ]
    )


def test_summary_and_outcomes_have_explicit_denominators():
    """Cent circulations, dix annulations et dix-huit retards donnent les trois issues attendues."""
    data = pd.DataFrame([_row()])
    result = trip_summary(data)
    assert result["cancellation_rate"] == result["cancellation_probability"] == 0.1
    assert result["late_rate"] == 0.2
    assert result["disruption_rate"] == 0.28
    assert result["avg_delay_arrival"] == 12.0
    assert result["on_time"] == 72
    assert outcomes_per_100(data)["per_100"].tolist() == pytest.approx([72, 18, 10])
    assert outcomes_per_100(data)["count"].tolist() == [72, 18, 10]


def test_multiple_services_count_distinct_months_and_pool_counts():
    """Deux services d'un même mois n'ajoutent pas artificiellement un mois d'historique."""
    data = pd.DataFrame([_row(), _row(service="International", cancelled=0, late_arrival=2, avg_delay_arrival=4)])
    result = trip_summary(data)
    assert result["n_months"] == 1
    assert result["n_records"] == 2
    assert result["late_rate"] == pytest.approx(20 / 190)
    assert result["avg_delay_arrival"] == pytest.approx((18 * 12 + 2 * 4) / 20)


@pytest.mark.parametrize(
    "change", [{"scheduled": None}, {"scheduled": float("inf")}, {"cancelled": -1}, {"late_arrival": "inconnu"}, {"late_arrival": 0.5}, {"cancelled": 90}]
)
def test_invalid_core_counts_are_not_corrected(change):
    """Une donnée absente ou incohérente ne devient pas une circulation valide."""
    data = pd.DataFrame([_row(**change)])
    before = data.copy(deep=True)
    with pytest.raises(DataValidationError):
        trip_summary(data)
    pd.testing.assert_frame_equal(data, before)


def test_missing_count_or_date_column_is_explicit():
    """Une rupture du contrat de données donne une erreur métier compréhensible."""
    data = pd.DataFrame([_row()])
    for column in ["scheduled", "date"]:
        with pytest.raises(DataValidationError):
            trip_summary(data.drop(columns=column))


def test_invalid_date_is_not_imputed():
    """Une date absente ne crée pas un faux mois d'observation."""
    data = pd.DataFrame([_row()])
    data["date"] = None
    with pytest.raises(DataValidationError):
        trip_summary(data)


@pytest.mark.parametrize("delay", [None, -1, float("inf"), "inconnu"])
def test_missing_average_delay_does_not_become_zero(delay):
    """La moyenne est indisponible si une composante pondérée manque ; les taux restent calculables."""
    result = trip_summary(pd.DataFrame([_row(avg_delay_arrival=delay)]))
    assert result["avg_delay_arrival"] is None
    assert result["disruption_rate"] == 0.28


def test_missing_average_for_no_delayed_trains_does_not_bias_mean():
    """Un enregistrement sans retard ne participe pas au retard moyen des trains en retard."""
    data = pd.DataFrame([_row(), _row(late_arrival=0, avg_delay_arrival=None)])
    assert trip_summary(data)["avg_delay_arrival"] == 12
    assert trip_summary(data.drop(columns="avg_delay_arrival"))["avg_delay_arrival"] is None


def test_zero_traffic_and_empty_selection_remain_unavailable():
    """Sans exposition, aucun taux ni récit de probabilité n'est inventé."""
    data = pd.DataFrame([_row(scheduled=0, cancelled=0, late_arrival=0)])
    for frame in [data, data.iloc[:0]]:
        result = trip_summary(frame)
        assert result["late_rate"] is None
        assert result["cancellation_rate"] is None
        assert result["disruption_rate"] is None
        assert outcomes_per_100(frame).empty
        assert average_causes(frame).isna().all()
    assert not recent_trip_evolution(data.iloc[:0])["available"]


def test_fully_cancelled_selection_has_no_operated_delay_rate():
    """Une annulation totale n'est pas interprétée comme une ponctualité parfaite."""
    data = pd.DataFrame([_row(cancelled=100, late_arrival=0)])
    result = trip_summary(data)
    assert result["late_rate"] is None
    assert result["disruption_rate"] == 1
    assert outcomes_per_100(data)["per_100"].tolist() == [0, 0, 100]


def test_period_filter_is_inclusive_and_does_not_modify_input():
    """Le filtre s'applique au mois entier sans ajouter de ligne manquante."""
    data = _history()
    before = data.copy(deep=True)
    result = filter_trip_period(data, "2025-01-15", "2025-02-20")
    assert result["date"].tolist() == [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")]
    assert filter_trip_period(data, "2030-01", "2030-02").empty
    with pytest.raises(PeriodOutOfRangeError):
        filter_trip_period(data, "2025-03", "2025-01")
    pd.testing.assert_frame_equal(data, before)


def test_recent_evolution_compares_the_agreed_windows():
    """La comparaison utilise les 24 derniers mois consécutifs de la sélection."""
    result = recent_trip_evolution(_history())
    assert result["available"]
    table = result["periods"]
    assert table["start"].tolist() == [pd.Timestamp("2024-10-01"), pd.Timestamp("2025-10-01")]
    assert table["end"].tolist() == [pd.Timestamp("2025-09-01"), pd.Timestamp("2026-09-01")]
    assert result["deltas_pp"]["disruption_rate"] == pytest.approx(20)
    assert result["deltas_pp"]["cancellation_rate"] == pytest.approx(10)
    assert result["deltas_pp"]["late_rate"] == pytest.approx((20 / 90 - 10 / 100) * 100)


def test_recent_evolution_aggregates_counts_instead_of_averaging_months():
    """Un mois de fort trafic reçoit son poids réel dans la période."""
    data = pd.concat([_history(), pd.DataFrame([_row("2026-09-01", scheduled=900, cancelled=0, late_arrival=0)])], ignore_index=True)
    result = recent_trip_evolution(data)
    assert result["periods"]["disruption_rate"].iloc[1] == pytest.approx(360 / 2100)


def test_recent_comparison_does_not_skip_missing_months_or_use_outside_selection():
    """Un trou n'est ni remplacé par zéro ni compensé par un mois plus ancien."""
    data = _history()
    missing = data.drop(index=4)
    missing = pd.concat([pd.DataFrame([_row("2024-09-01")]), missing], ignore_index=True)
    assert not recent_trip_evolution(missing)["available"]
    assert not recent_trip_evolution(filter_trip_period(data, "2026-01", "2026-09"))["available"]


def test_recent_comparison_without_traffic_and_operated_denominator():
    """Une période sans exposition est indisponible ; un taux de retard peut manquer seul."""
    data = _history()
    data.loc[:11, ["scheduled", "cancelled", "late_arrival"]] = 0
    assert not recent_trip_evolution(data)["available"]
    data = _history()
    data.loc[:11, "cancelled"] = 100
    data.loc[:11, "late_arrival"] = 0
    result = recent_trip_evolution(data)
    assert result["available"]
    assert result["deltas_pp"]["late_rate"] is None


def _directions():
    """Deux sens dont seuls février et mars sont communs dans la période demandée."""
    rows = [_row("2025-01-01", cancelled=100, late_arrival=0), _row("2025-02-01"), _row("2025-03-01")]
    rows += [_row(date, origin="B", destination="A", scheduled=50, cancelled=0, late_arrival=5) for date in ["2025-02-01", "2025-03-01", "2025-04-01"]]
    return pd.DataFrame(rows)


def test_reverse_comparison_uses_only_common_months_for_both_directions():
    """La synthèse de l'aller n'est pas comparée à un retour d'une autre période."""
    result = reverse_trip_comparison(_directions(), "A → B", "2025-01", "2025-03")
    assert result["available"]
    assert result["common_months"] == [pd.Timestamp("2025-02-01"), pd.Timestamp("2025-03-01")]
    assert result["n_requested_months"] == 3
    table = result["directions"]
    assert table["scheduled"].tolist() == [200, 100]
    assert table["n_months"].tolist() == [2, 2]
    assert table["disruption_rate"].tolist() == pytest.approx([0.28, 0.1])


def test_reverse_comparison_handles_missing_direction_information():
    """Une liaison absente ou un sens inverse absent n'entraîne aucune extrapolation."""
    data = _directions()
    assert not reverse_trip_comparison(data, "X → Y", "2025-01", "2025-03")["available"]
    assert not reverse_trip_comparison(data.drop(columns="origin"), "A → B", "2025-01", "2025-03")["available"]
    assert not reverse_trip_comparison(data[data.origin == "A"], "A → B", "2025-01", "2025-03")["available"]
    assert not reverse_trip_comparison(data, "A → B", "2025-01", "2025-01")["available"]


def test_reverse_comparison_detects_ambiguous_station_pair():
    """Un libellé reliant plusieurs paires de gares n'est pas interprété arbitrairement."""
    data = _directions()
    data.loc[0, "origin"] = "C"
    with pytest.raises(DataValidationError):
        reverse_trip_comparison(data, "A → B", "2025-01", "2025-03")


def test_reverse_comparison_without_exposure_stays_unavailable():
    """Un sens sans circulation ne reçoit pas de taux artificiel."""
    data = _directions()
    data.loc[data.origin == "B", ["scheduled", "cancelled", "late_arrival"]] = 0
    assert not reverse_trip_comparison(data, "A → B", "2025-01", "2025-03")["available"]


def test_cause_shares_keep_the_unallocated_part():
    """La ventilation manquante n'est pas redistribuée entre les catégories connues."""
    data = pd.DataFrame([_row(late_arrival=10), _row(late_arrival=30)])
    data.loc[1, CAUSE_COLUMNS] = 0.0
    data.loc[1, "cause_external"] = 50.0
    result = average_causes(data)
    assert result["cause_infra"] == 25
    assert result["cause_external"] == result["cause_unallocated"] == 37.5
    assert result.sum() == 100
    data.loc[:, CAUSE_COLUMNS] = 0.0
    assert average_causes(data)["cause_unallocated"] == 100
    data.loc[0, "cause_infra"] = 40
    data.loc[0, "cause_external"] = float("nan")
    assert average_causes(data)["cause_unallocated"] == 90


@pytest.mark.parametrize(
    "column,value",
    [("late_arrival", -1), ("late_arrival", None), ("late_arrival", float("inf")), ("cause_external", -1), ("cause_external", 101), ("cause_external", 1)],
)
def test_invalid_causes_and_weights_are_explicit(column, value):
    """Les valeurs incohérentes sont signalées plutôt que normalisées."""
    data = pd.DataFrame([_row()])
    data[column] = value
    with pytest.raises(DataValidationError):
        average_causes(data)


def test_cause_schema_and_rounding_are_handled_without_rescaling():
    """Le contrat est contrôlé et les faibles arrondis ne modifient pas les parts connues."""
    data = pd.DataFrame([_row()])
    with pytest.raises(DataValidationError):
        average_causes(data.drop(columns="cause_infra"))
    data["cause_infra"] = 50
    data["cause_external"] = 50.00000001
    result = average_causes(data)
    assert result["cause_external"] == pytest.approx(50.00000001)
    assert result["cause_unallocated"] == 0


def test_analysis_does_not_mutate_shared_input():
    """Toutes les analyses de la page conservent les données partagées intactes."""
    data = _history()
    before = data.copy(deep=True)
    trip_summary(data)
    average_causes(data)
    recent_trip_evolution(data)
    outcomes_per_100(data)
    reverse_trip_comparison(data, "A → B", "2024-10", "2026-09")
    pd.testing.assert_frame_equal(data, before)
