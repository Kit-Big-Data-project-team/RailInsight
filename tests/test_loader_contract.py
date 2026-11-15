"""Tests du contrat de données exposé par TGVDataset.from_db().

On vérifie que toutes les colonnes convenues (utilisées par les pages 3/4/5/6)
sont bien exposées avec les noms standard, sans toucher à une vraie base.
"""

from unittest.mock import MagicMock, patch

import pandas as pd

from railinsight.data import loader

RAW = pd.DataFrame(
    {
        "date": ["2026-01-01", "2026-02-01"],
        "service": ["National", "International"],
        "gare_depart": ["PARIS", "LYON"],
        "gare_arrivee": ["LYON", "PARIS"],
        "duree_moyenne": [120.0, 118.0],
        "nb_train_prevu": [100, 80],
        "nb_annulation": [2, 1],
        "nb_train_depart_retard": [10, 8],
        "nb_train_retard_arrivee": [12, 9],
        "nb_train_retard_sup_15": [5, 4],
        "nb_train_retard_sup_30": [2, 1],
        "nb_train_retard_sup_60": [1, 0],
        "retard_moyen_depart": [8.5, 7.0],
        "retard_moyen_arrivee": [10.2, 9.1],
        "prct_cause_externe": [20.0, 15.0],
        "prct_cause_infra": [30.0, 25.0],
        "prct_cause_gestion_trafic": [10.0, 20.0],
        "prct_cause_materiel_roulant": [15.0, 10.0],
        "prct_cause_gestion_gare": [15.0, 20.0],
        "prct_cause_prise_en_charge_voyageurs": [10.0, 10.0],
    }
)

EXPECTED_COLUMNS = {
    "date",
    "origin",
    "destination",
    "route",
    "service",
    "scheduled",
    "cancelled",
    "late_departure",
    "late_arrival",
    "late_15",
    "late_30",
    "late_60",
    "avg_delay_departure",
    "avg_delay_arrival",
    "avg_trip_duration",
    "cause_external",
    "cause_infra",
    "cause_traffic",
    "cause_rolling_stock",
    "cause_station",
    "cause_passengers",
}


def test_from_db_exposes_the_full_data_contract():
    with (
        patch("railinsight.data.loader.make_engine", return_value=MagicMock()),
        patch("railinsight.data.loader.pd.read_sql", return_value=RAW.copy()),
    ):
        ds = loader.TGVDataset.from_db()

    assert EXPECTED_COLUMNS.issubset(set(ds.df.columns))
    assert ds.df["route"].iloc[0] == "PARIS → LYON"
    assert sorted(ds.routes()) == ["LYON → PARIS", "PARIS → LYON"]
