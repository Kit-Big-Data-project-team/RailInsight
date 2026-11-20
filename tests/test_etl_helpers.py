"""Tests ciblés des utilitaires et chemins d'erreur de l'ETL."""

from unittest.mock import MagicMock, patch

import pytest
from utils import make_record

from railinsight.data.data_cleaning import nettoyer_donnees
from railinsight.data.etl import _upsert_statement, dataset_url, insert_data, pipeline
from railinsight.data.etl import main as etl_main
from railinsight.database import init_db as init_db_module


def test_dataset_url_prefers_the_correct_name():
    # os.getenv est simulé : les noms d'env sont insensibles à la casse sous Windows.
    values = {"URL_SNCF_DATASET": "correct", "URl_SNCF_DATASET": "legacy"}
    with patch("railinsight.data.etl.os.getenv", side_effect=values.get):
        assert dataset_url() == "correct"


def test_dataset_url_falls_back_to_legacy_name():
    values = {"URl_SNCF_DATASET": "legacy"}
    with patch("railinsight.data.etl.os.getenv", side_effect=values.get):
        assert dataset_url() == "legacy"


def test_upsert_statement_rejects_unsupported_dialect():
    engine = MagicMock()
    engine.dialect.name = "mysql"
    with pytest.raises(RuntimeError, match="mysql"):
        _upsert_statement(engine, [])


def test_insert_data_reraises_on_upsert_failure(db_engine):
    data = nettoyer_donnees([make_record()])
    with patch("railinsight.data.etl._upsert_statement", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            insert_data(data, db_engine)


def test_pipeline_stops_cleanly_when_no_new_data(db_engine):
    with patch("railinsight.data.etl.fetch_data", return_value=[]):
        pipeline(db_engine)  # ne lève rien, ne tente aucune insertion


def test_etl_main_runs_pipeline():
    with patch("railinsight.data.etl.pipeline") as pipe:
        etl_main()
    pipe.assert_called_once_with(None)


def test_etl_main_propagates_errors():
    with patch("railinsight.data.etl.pipeline", side_effect=RuntimeError("down")):
        with pytest.raises(RuntimeError):
            etl_main()


def test_init_db_success_path(db_engine):
    with patch.object(init_db_module, "make_engine", return_value=db_engine):
        init_db_module.init_db()  # create_all idempotent sur la base de test
