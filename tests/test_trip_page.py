"""Tests de Mon trajet avec données contrôlées, sans accès à Supabase."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from railinsight.analysis.history import CAUSE_COLUMNS
from railinsight.data.loader import TGVDataset

PAGE = Path(__file__).resolve().parents[1] / "views" / "trip.py"


@pytest.fixture
def trip_frame():
    """Deux directions sur 24 mois et deux services pour un même mois de l'aller."""
    rows = []
    for date in pd.date_range("2024-10-01", "2026-09-01", freq="MS"):
        for origin, destination in [("A", "B"), ("B", "A")]:
            rows.append(
                {
                    "date": date,
                    "origin": origin,
                    "destination": destination,
                    "route": f"{origin} → {destination}",
                    "service": "National",
                    "scheduled": 100,
                    "cancelled": 10 if origin == "A" else 0,
                    "late_arrival": 18 if origin == "A" else 10,
                    "avg_delay_arrival": 12.0,
                    **{column: 100.0 if column == "cause_infra" else 0.0 for column in CAUSE_COLUMNS},
                }
            )
    rows.append({**rows[0], "service": "International", "cancelled": 0, "late_arrival": 0, "avg_delay_arrival": None})
    return pd.DataFrame(rows)


@pytest.fixture(autouse=True)
def clear_cache():
    """Évite de partager le chargement simulé entre les scénarios."""
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def test_page_filters_update_outcomes_and_comparisons(trip_frame):
    """Un filtre court retire la comparaison récente sans conserver les anciens résultats."""
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(trip_frame)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
        assert not app.exception
        assert len(app.metric) == 4
        assert len(app.get("plotly_chart")) == 4
        assert any("24 mois distincts" in item.value for item in app.caption)
        assert any("2 500 circulations" in item.value for item in app.caption)
        assert any("Sur une base historique de 100" in item.value for item in app.markdown)
        app.sidebar.select_slider[0].set_value((pd.Timestamp("2026-01-01"), pd.Timestamp("2026-03-01"))).run(timeout=30)
        assert not app.exception
        assert len(app.get("plotly_chart")) == 3
        assert any("24 mois consécutifs" in item.value for item in app.info)
        assert any("3 mois distincts" in item.value and "300 circulations" in item.value for item in app.caption)
        assert any("3 mois communs" in item.value for item in app.caption)
        app.sidebar.selectbox[0].select("B → A").run(timeout=30)
        assert not app.exception
        assert app.metric[0].value == "0,0%"


def test_missing_reverse_direction_keeps_other_features(trip_frame):
    """L'absence de sens inverse ne bloque pas la synthèse ni l'évolution."""
    data = trip_frame.loc[trip_frame.origin == "A"]
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(data)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 3
    assert any("sens inverse n'est pas disponible" in item.value for item in app.info)


def test_only_common_months_are_disclosed(trip_frame):
    """Une couverture partielle est annoncée sans imputer les mois absents."""
    data = trip_frame.loc[~((trip_frame.origin == "B") & (trip_frame.date == pd.Timestamp("2025-01-01")))]
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(data)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("23 mois communs" in item.value and "24 mois calendaires" in item.value for item in app.caption)


def test_missing_delay_average_keeps_rates(trip_frame):
    """La moyenne indisponible reste un tiret, les fréquences historiques restent visibles."""
    data = trip_frame.copy()
    data["avg_delay_arrival"] = None
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(data)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert app.metric[3].value == "—"
    assert app.metric[0].value != "—"


@pytest.mark.parametrize("scheduled,cancelled", [(100, 100), (0, 0)])
def test_no_delays_or_no_traffic_do_not_invent_causes(trip_frame, scheduled, cancelled):
    """Une période sans retard ne reçoit pas de ventilation artificielle."""
    data = trip_frame.iloc[:1].copy()
    data[["scheduled", "cancelled", "late_arrival"]] = [scheduled, cancelled, 0]
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(data)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("Aucun retard enregistré" in item.value for item in app.info)
    assert app.metric[1].value == "—"
    assert len(app.get("plotly_chart")) == (1 if scheduled else 0)


def test_empty_database_has_a_public_message():
    """Une base vide, même non normalisée, s'arrête avant les filtres."""
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(pd.DataFrame())):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("Aucune donnée disponible" in item.value for item in app.info)
    assert not app.metric


def test_database_failure_has_no_public_traceback():
    """Une erreur de chargement reçoit un message français sans exposer de détails techniques."""
    with patch("railinsight.data.loader.TGVDataset.from_db", side_effect=RuntimeError("Erreur de connexion simulée")):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("momentanément indisponibles" in item.value for item in app.error)


def test_invalid_source_counts_are_reported(trip_frame):
    """Une valeur négative n'est ni supprimée ni transformée en zéro."""
    data = trip_frame.copy()
    data.loc[0, "cancelled"] = -1
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(data)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("Résultats indisponibles" in item.value for item in app.error)
    assert not app.get("plotly_chart")


def test_unknown_causes_remain_visible(trip_frame):
    """Une ventilation absente reste grise et ne se transforme pas en cause connue."""
    data = trip_frame.copy()
    data.loc[:, CAUSE_COLUMNS] = 0.0
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(data)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 4
    assert any("part grise" in item.value for item in app.caption)


def test_direction_metadata_unavailable_preserves_the_page(trip_frame):
    """Sans origine/destination structurées, seule la comparaison des directions est indisponible."""
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(trip_frame.drop(columns="origin"))):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("informations de direction" in item.value for item in app.info)
