"""Tests des métriques de la page Historique & évolution."""

import pandas as pd
import pytest

from railinsight.analysis.history import (
    CAUSE_COLUMNS,
    UNALLOCATED_CAUSE,
    cause_breakdown_over_time,
    delay_severity_over_time,
    history_period_summary,
    monthly_delays_cancellations,
    punctuality_by_service,
    seasonality,
    severity_source_issues,
)
from railinsight.exceptions import DataValidationError


def _row(**kw) -> dict:
    """Construit un enregistrement de test avec les six causes renseignées."""
    row = {c: 0.0 for c in CAUSE_COLUMNS}
    row.update(kw)
    return row


def _sample() -> pd.DataFrame:
    """Deux mois, deux services, avec les colonnes du contrat de données."""
    rows = [
        _row(date="2026-01-01", service="National", scheduled=100, cancelled=2, late_arrival=10, late_15=8, late_30=4, late_60=1, cause_infra=100.0),
        _row(date="2026-01-01", service="International", scheduled=100, cancelled=4, late_arrival=30, late_15=20, late_30=10, late_60=5, cause_external=100.0),
        _row(date="2026-02-01", service="National", scheduled=50, cancelled=0, late_arrival=5, late_15=3, late_30=1, late_60=0, cause_infra=100.0),
    ]
    return pd.DataFrame(rows)


def test_monthly_delays_cancellations_has_three_rates():
    """Vérifie les trois taux mensuels et leurs dénominateurs distincts."""
    out = monthly_delays_cancellations(_sample())

    assert set(out.columns) == {"date", "late_rate", "cancellation_rate", "disruption_rate"}
    janvier = out.loc[out["date"] == "2026-01-01"].iloc[0]
    # retard : (10 + 30) / ((200) - (6)) ; annulation : 6 / 200
    assert janvier["late_rate"] == 40 / 194
    assert janvier["cancellation_rate"] == 6 / 200
    assert janvier["disruption_rate"] == 46 / 200


def test_cause_breakdown_is_weighted_by_late_trains():
    """Vérifie la pondération des causes par les effectifs de retards."""
    out = cause_breakdown_over_time(_sample())

    janvier = out.loc[out["date"] == pd.Timestamp("2026-01-01")].iloc[0]
    # 10 trains "infra" vs 30 trains "externe" -> externe pèse 3x plus
    assert round(janvier["cause_external"], 2) == round(100 * 30 / 40, 2)
    assert round(janvier["cause_infra"], 2) == round(100 * 10 / 40, 2)


def test_seasonality_returns_one_row_per_month():
    """Vérifie le contrat de sortie lorsque les années incomplètes sont autorisées."""
    out = seasonality(_sample(), complete_years_only=False)

    assert set(out["month"]) == {1, 2}
    assert list(out.columns) == ["month", "late_rate", "cancellation_rate", "disruption_rate", "n_years"]


def test_incomplete_causes_keep_reported_shares_and_weight_the_remainder():
    """Les parts publiées restent intactes ; seul leur complément est ajouté."""
    df = _sample().iloc[:2].copy()
    df.loc[:, CAUSE_COLUMNS] = 0.0
    df.loc[df.index[0], "cause_infra"] = 90.0
    out = cause_breakdown_over_time(df).iloc[0]
    assert out["cause_infra"] == pytest.approx(90 * 10 / 40)
    assert out[UNALLOCATED_CAUSE] == pytest.approx((10 * 10 + 100 * 30) / 40)
    assert out[[*CAUSE_COLUMNS, UNALLOCATED_CAUSE]].sum() == pytest.approx(100)


def test_missing_cause_stays_in_unallocated_share():
    """Une valeur absente ne devient pas une cause connue de retard."""
    df = _sample().iloc[:1].copy()
    df.loc[:, CAUSE_COLUMNS] = 0.0
    df.loc[df.index[0], "cause_infra"] = 40.0
    df.loc[df.index[0], "cause_external"] = float("nan")
    out = cause_breakdown_over_time(df).iloc[0]
    assert out["cause_infra"] == 40.0
    assert out[UNALLOCATED_CAUSE] == 60.0


def test_zero_delays_have_no_cause_distribution():
    """Sans retard, même des pourcentages présents ne justifient pas une répartition."""
    df = _sample().iloc[:1].copy()
    df["late_arrival"] = 0
    out = cause_breakdown_over_time(df)
    assert out[[*CAUSE_COLUMNS, UNALLOCATED_CAUSE]].isna().all().all()


def test_rounding_does_not_change_reported_percentages():
    """Les petits écarts sont tolérés sans renormalisation des valeurs publiées."""
    df = _sample().iloc[:1].copy()
    df.loc[:, CAUSE_COLUMNS] = 0.0
    df.loc[df.index[0], "cause_infra"] = 50.0
    df.loc[df.index[0], "cause_external"] = 49.99999999
    out = cause_breakdown_over_time(df).iloc[0]
    assert out["cause_external"] == pytest.approx(49.99999999)
    assert out[UNALLOCATED_CAUSE] == 0.0


@pytest.mark.parametrize("change", [{"late_arrival": -1}, {"late_arrival": None}, {"cause_external": 101}, {"cause_external": -1}, {"cause_external": 1}])
def test_invalid_causes_or_weights_are_rejected(change):
    """Une incohérence n'est ni masquée ni corrigée par normalisation."""
    df = _sample().iloc[:1].copy()
    for key, value in change.items():
        df[key] = value
    with pytest.raises(DataValidationError):
        cause_breakdown_over_time(df)


def test_empty_causes_preserve_schema_and_inputs_are_unchanged():
    """Le contrat est stable sur une sélection vide et les données ne sont pas modifiées."""
    df = _sample()
    before = df.copy(deep=True)
    cause_breakdown_over_time(df)
    pd.testing.assert_frame_equal(df, before)
    out = cause_breakdown_over_time(df.iloc[:0])
    assert out.empty
    assert list(out) == ["date", *CAUSE_COLUMNS, UNALLOCATED_CAUSE]


def test_punctuality_by_service_splits_by_service():
    """Conserve le test de comparaison des services proposé par Abdelmounaim."""
    out = punctuality_by_service(_sample())

    national = out[(out["date"] == "2026-01-01") & (out["service"] == "National")].iloc[0]
    inter = out[(out["date"] == "2026-01-01") & (out["service"] == "International")].iloc[0]
    assert national["late_rate"] == 10 / 98
    assert inter["late_rate"] == 30 / 96


def test_delay_severity_over_time_is_share_of_scheduled():
    """Conserve le test des seuils rapportés aux trains prévus proposé par Abdelmounaim."""
    out = delay_severity_over_time(_sample())

    janvier = out[out["date"] == "2026-01-01"].iloc[0]
    assert janvier["late_15"] == 28 / 200
    assert janvier["late_30"] == 14 / 200
    assert janvier["late_60"] == 6 / 200


def test_negative_severity_invalidates_only_affected_month_and_threshold():
    """Une somme positive ne doit pas masquer une valeur source négative."""
    df = _sample()
    df.loc[0, "late_30"] = -1
    before = df.copy(deep=True)
    out = delay_severity_over_time(df).set_index("date")
    assert pd.isna(out.loc["2026-01-01", "late_30"])
    assert out.loc["2026-01-01", "late_60"] == pytest.approx(6 / 200)
    assert out.loc["2026-02-01", "late_30"] == pytest.approx(1 / 50)
    assert severity_source_issues(df)["valeur_source"].tolist() == [-1]
    pd.testing.assert_frame_equal(df, before)


def test_severity_missing_value_and_zero_denominator_remain_unavailable():
    """Une absence n'est pas interprétée comme zéro et aucun taux infini n'est créé."""
    df = _sample()
    df.loc[0, "late_30"] = float("nan")
    df.loc[2, "scheduled"] = 0
    out = delay_severity_over_time(df).set_index("date")
    assert pd.isna(out.loc["2026-01-01", "late_30"])
    assert out.loc["2026-02-01", ["late_15", "late_30", "late_60"]].isna().all()
    assert len(severity_source_issues(df)) == 1


def test_service_missing_or_no_operated_trains():
    """L'absence de service et un mois annulé ne produisent pas de faux taux."""
    df = _sample()
    assert punctuality_by_service(df.drop(columns="service")).empty
    df["cancelled"] = df["scheduled"]
    assert punctuality_by_service(df)["late_rate"].isna().all()


def test_period_kpis_aggregate_counts_and_handle_empty_selection():
    """Les indicateurs de période sont des rapports d'effectifs, pas des moyennes de mois."""
    out = history_period_summary(_sample())
    assert out["scheduled"] == 250
    assert out["late_rate"] == pytest.approx(45 / 244)
    assert out["cancellation_rate"] == pytest.approx(6 / 250)
    assert out["disruption_rate"] == pytest.approx(51 / 250)
    empty = history_period_summary(_sample().iloc[:0])
    assert empty["scheduled"] == 0
    assert all(empty[key] is None for key in ("late_rate", "cancellation_rate", "disruption_rate"))


def _seasonal_sample():
    """Deux années complètes de volumes différents et une troisième année incomplète."""
    rows = []
    for year in (2024, 2025):
        for month in range(1, 13):
            scheduled, cancelled, late = (100, 0, 10)
            if month == 1:
                scheduled, cancelled, late = (100, 10, 18) if year == 2024 else (900, 0, 9)
            rows.append({"date": pd.Timestamp(year, month, 1), "scheduled": scheduled, "cancelled": cancelled, "late_arrival": late})
    rows.append({"date": pd.Timestamp(2026, 1, 1), "scheduled": 10, "cancelled": 10, "late_arrival": 0})
    return pd.DataFrame(rows)


def test_seasonality_pools_counts_over_complete_years():
    """Les années ont un poids lié au trafic et une année partielle n'ajoute pas de mois."""
    df = _seasonal_sample()
    before = df.copy(deep=True)
    out = seasonality(df).set_index("month")
    assert len(out) == 12
    assert (out["n_years"] == 2).all()
    assert out.loc[1, "late_rate"] == pytest.approx(27 / 990)
    assert out.loc[1, "cancellation_rate"] == pytest.approx(10 / 1000)
    assert out.loc[1, "disruption_rate"] == pytest.approx(37 / 1000)
    pd.testing.assert_frame_equal(df, before)


def test_seasonality_does_not_silently_fall_back_to_incomplete_years():
    """Sans douze mois, aucun faux profil annuel n'est affiché par défaut."""
    assert seasonality(_sample()).empty
    assert seasonality(_sample().iloc[:0]).empty
    out = seasonality(_seasonal_sample(), complete_years_only=False).set_index("month")
    assert out.loc[1, "n_years"] == 3
    assert out.loc[2, "n_years"] == 2


def test_seasonality_zero_denominators_remain_missing():
    """Les mois sans circulation ne deviennent pas des mois parfaitement ponctuels."""
    df = _seasonal_sample()
    df[["scheduled", "cancelled", "late_arrival"]] = 0
    out = seasonality(df)
    assert out[["late_rate", "cancellation_rate", "disruption_rate"]].isna().all().all()
