import pandas as pd
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from utils import make_record

from railinsight.data.etl import insert_data, last_loaded_month, transform
from railinsight.database.db_table import regularite_tgv_table as table


def read_rows(engine):
    with engine.connect() as conn:
        return conn.execute(select(table)).mappings().all()


def test_last_loaded_month_is_none_on_empty_table(db_engine):
    assert last_loaded_month(db_engine) is None


def test_last_loaded_month_returns_the_max_date(db_engine):
    df = transform([make_record(date="2018-01"), make_record(date="2018-03"), make_record(date="2018-02")])
    insert_data(df, db_engine)
    print(last_loaded_month(db_engine))
    assert last_loaded_month(db_engine) == "2018-03-01"


def test_insert_returns_count_and_stores_rows(db_engine):
    assert len(read_rows(db_engine)) == 0
    df = transform([make_record(), make_record(gare_depart="VANNES")])
    insert_data(df, db_engine)
    assert len(read_rows(db_engine)) == 2


def test_insert_empty_dataframe_does_nothing(db_engine):
    insert_data(pd.DataFrame(), db_engine)
    assert read_rows(db_engine) == []


def test_null_values_are_stored_as_null(db_engine):
    insert_data(transform([make_record(retard_moyen_depart=None)]), db_engine)
    assert read_rows(db_engine)[0]["retard_moyen_depart"] is None


def test_duplicate_key_is_rejected_and_transaction_rolled_back(db_engine):
    insert_data(transform([make_record()]), db_engine)
    batch = transform([make_record(gare_depart="VANNES"), make_record()])  # 2e = doublon

    with pytest.raises(IntegrityError):
        insert_data(batch, db_engine)

    assert len(read_rows(db_engine)) == 1  # VANNES n'a pas été inséré non plus
