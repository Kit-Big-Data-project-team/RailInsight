import os
from unittest.mock import patch

import pytest
import requests
from sqlalchemy import select
from utils import API_URL, make_response

from railinsight.data.etl import pipeline
from railinsight.database.db_table import regularite_tgv_table as table


@pytest.fixture
def fake_api(sample_records):
    """requests.get renvoie le contenu du fichier JSON."""
    with patch(
        "railinsight.data.etl.requests.get",
        return_value=make_response(sample_records),
    ) as mock_get:
        yield mock_get


@pytest.fixture
def etl_env(db_engine):
    """Environnement de main() : variable d'URL et make_engine() pointant vers la base de test."""
    with patch.dict(os.environ, {"SNCF_EXPORT_URL": API_URL}), patch("railinsight.data.etl.make_engine", return_value=db_engine):
        yield


def read_rows(engine):
    with engine.connect() as conn:
        return conn.execute(select(table)).mappings().all()


def test_first_load_inserts_every_row_of_the_json(db_engine, fake_api, sample_records):
    pipeline(db_engine)
    assert len(read_rows(db_engine)) == len(sample_records)
    assert fake_api.call_args.kwargs["params"] == {}


def test_rows_are_stored_with_expected_values(db_engine, fake_api):
    pipeline(db_engine)

    row = next(r for r in read_rows(db_engine) if r["gare_depart"] == "LE MANS")
    assert row["date"].isoformat() == "2026-01-01"
    assert row["gare_arrivee"] == "PARIS MONTPARNASSE"
    assert row["nb_train_prevu"] == 417
    assert "commentaire_annulation" not in row


def test_second_run_asks_only_for_newer_months(db_engine, fake_api, sample_records):
    fake_api.side_effect = [make_response(sample_records), make_response([])]

    pipeline(db_engine)
    pipeline(db_engine)
    assert fake_api.call_args_list[1].kwargs["params"] == {"where": 'date > "2026-09-01"'}
    assert len(read_rows(db_engine)) == len(sample_records)


def test_api_failure_raises_and_leaves_database_untouched(db_engine, fake_api):
    fake_api.side_effect = requests.exceptions.Timeout()

    with pytest.raises(SystemExit):
        pipeline(db_engine)

    assert read_rows(db_engine) == []


def test_api_schema_change_fails_before_touching_database(db_engine, fake_api, sample_records):
    broken = [{k: v for k, v in r.items() if k != "duree_moyenne"} for r in sample_records]
    fake_api.return_value = make_response(broken)

    with pytest.raises(KeyError, match="duree_moyenne"):
        pipeline(db_engine)

    assert read_rows(db_engine) == []
