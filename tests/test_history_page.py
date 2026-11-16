"""Tests de la page historique sans dépendance à une base réelle."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from railinsight.analysis.history import CAUSE_COLUMNS
from railinsight.data.loader import TGVDataset

PAGE = Path(__file__).resolve().parents[1] / "views" / "history.py"


@pytest.fixture
def history_frame():
    """Deux années complètes, deux services et une anomalie source connue."""
    rows = []
    for date in pd.date_range("2024-01-01", "2025-12-01", freq="MS"):
        for route, service, scheduled in [("A → B", "National", 100), ("C → D", "International", 50)]:
            rows.append(
                {
                    "date": date,
                    "route": route,
                    "service": service,
                    "scheduled": scheduled,
                    "cancelled": 0,
                    "late_arrival": 10,
                    "late_15": 5,
                    "late_30": -1 if date == pd.Timestamp("2025-01-01") and service == "National" else 2,
                    "late_60": 1,
                    **{column: 100.0 if column == "cause_infra" else 0.0 for column in CAUSE_COLUMNS},
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture(autouse=True)
def clear_page_cache():
    """Isole le chargement mis en cache entre les scénarios."""
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def test_page_filters_update_all_sections(history_frame):
    """Les filtres actualisent les indicateurs, anomalies, services et années retenues."""
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(history_frame)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
        assert not app.exception
        assert len(app.metric) == 4
        assert app.metric[3].value == "3 600"
        assert len(app.get("plotly_chart")) == 5
        assert not app.warning
        assert any("Certaines données de retard sont incohérentes" in item.value for item in app.caption)
        assert not any("vérifier avec l'équipe" in item.label for item in app.expander)
        assert not app.dataframe
        assert any("taux officiels" in message.value for message in app.info)
        app.sidebar.select_slider[0].set_value((pd.Timestamp("2024-01-01"), pd.Timestamp("2024-03-01"))).run(timeout=30)
        assert not app.exception
        assert app.metric[3].value == "450"
        assert not app.warning
        assert not any("Certaines données de retard sont incohérentes" in item.value for item in app.caption)
        assert len(app.get("plotly_chart")) == 4
        assert any("Aucune année complète" in message.value for message in app.info)
        app.sidebar.selectbox[0].select("C → D").run(timeout=30)
        assert not app.exception
        assert any("Un seul service" in message.value for message in app.caption)
        assert not any("taux officiels" in message.value for message in app.info)


def test_page_without_delays_does_not_invent_causes(history_frame):
    """Une période sans retard reçoit un message plutôt qu'une répartition artificielle."""
    frame = history_frame.iloc[:1].copy()
    frame[["late_arrival", "late_15", "late_30", "late_60"]] = 0
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(frame)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("Aucun retard enregistré" in message.value for message in app.info)
    assert len(app.get("plotly_chart")) == 3
    assert app.metric[0].value == "0.0%"


def test_missing_service_preserves_other_charts(history_frame):
    """Sans service, seule la comparaison correspondante devient indisponible."""
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(history_frame.drop(columns="service"))):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("comparaison des services n'est pas disponible" in message.value for message in app.info)
    assert len(app.get("plotly_chart")) == 4


def test_invalid_cause_distribution_is_reported(history_frame):
    """Une incohérence des causes est signalée plutôt que corrigée silencieusement."""
    frame = history_frame.copy()
    frame.loc[0, "cause_infra"] = 101
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(frame)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("Impossible d'afficher ces données" in message.value for message in app.error)


def test_empty_selection_has_a_message():
    """Une sélection vide normalisée arrête les graphiques avant les calculs."""
    frame = pd.DataFrame(columns=["route", "date"])
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(frame)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("Aucune donnée disponible" in message.value for message in app.info)
    assert not app.get("plotly_chart")


def test_observations_follow_the_selected_period(history_frame):
    """Les constats ne conservent pas le maximum d'une période précédemment sélectionnée."""
    frame = history_frame.copy()
    january = frame["date"] == pd.Timestamp("2025-01-01")
    frame.loc[january, "cancelled"] = 10
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(frame)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
        assert not app.exception
        assert any("Jan 2025" in item.value and "plus élevé" in item.value for item in app.markdown)
        app.sidebar.select_slider[0].set_value((pd.Timestamp("2024-01-01"), pd.Timestamp("2024-03-01"))).run(timeout=30)
        assert not app.exception
        assert any("identique dans les 3 mois" in item.value for item in app.markdown)
        assert not any("Jan 2025" in item.value and "plus élevé" in item.value for item in app.markdown)
        assert any("Infrastructure" in item.value and "part déclarée" in item.value for item in app.markdown)


def test_observations_keep_multiple_peak_months(history_frame):
    """Un ensemble d'ex aequo n'est pas présenté comme un maximum unique."""
    frame = history_frame.copy()
    frame.loc[frame["date"].between("2024-01-01", "2024-06-01"), "cancelled"] = 10
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(frame)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("partagé par 6 mois" in item.value and "3 autre(s) mois" in item.value for item in app.markdown)


def test_unallocated_causes_are_not_presented_as_an_identified_cause(history_frame):
    """Une ventilation entièrement absente est expliquée sans nommer une cause dominante."""
    frame = history_frame.copy()
    frame.loc[:, CAUSE_COLUMNS] = 0.0
    with patch("railinsight.data.loader.TGVDataset.from_db", return_value=TGVDataset(frame)):
        app = AppTest.from_file(str(PAGE)).run(timeout=30)
    assert not app.exception
    assert any("Aucune cause n'est ventilée" in item.value for item in app.markdown)
    assert any("Part non ventilée sur la période : 100,0 %" in item.value for item in app.caption)
