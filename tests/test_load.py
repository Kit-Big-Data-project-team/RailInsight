import pandas as pd
from sqlalchemy import select
from utils import make_record

from railinsight.data.data_cleaning import nettoyer_donnees
from railinsight.data.etl import insert_data, last_loaded_month
from railinsight.database.db_table import regularite_tgv_table as table


def read_rows(engine):
    with engine.connect() as conn:
        return conn.execute(select(table)).mappings().all()


def test_last_loaded_month_is_none_on_empty_table(db_engine):
    assert last_loaded_month(db_engine) is None


def test_last_loaded_month_returns_the_max_date(db_engine):
    df = nettoyer_donnees([make_record(date="2018-01"), make_record(date="2018-03"), make_record(date="2018-02")])
    insert_data(df, db_engine)
    print(last_loaded_month(db_engine))
    assert last_loaded_month(db_engine) == "2018-03-01"


def test_insert_returns_count_and_stores_rows(db_engine):
    assert len(read_rows(db_engine)) == 0
    df = nettoyer_donnees([make_record(), make_record(gare_depart="VANNES")])
    insert_data(df, db_engine)
    assert len(read_rows(db_engine)) == 2


def test_insert_empty_dataframe_does_nothing(db_engine):
    insert_data(pd.DataFrame(), db_engine)
    assert read_rows(db_engine) == []


def test_null_values_are_stored_as_null(db_engine):
    insert_data(nettoyer_donnees([make_record(retard_moyen_depart=None)]), db_engine)
    assert read_rows(db_engine)[0]["retard_moyen_depart"] is None


def test_existing_key_is_updated_not_rejected(db_engine):
    """Une clé déjà présente est mise à jour (UPSERT), sans rejeter le reste du lot."""
    insert_data(nettoyer_donnees([make_record(nb_train_prevu=100)]), db_engine)
    batch = nettoyer_donnees([make_record(gare_depart="VANNES"), make_record(nb_train_prevu=999)])
    insert_data(batch, db_engine)

    rows = {r["gare_depart"]: r for r in read_rows(db_engine)}
    assert set(rows) == {"LE MANS", "VANNES"}  # VANNES inséré, LE MANS mis à jour
    assert rows["LE MANS"]["nb_train_prevu"] == 999


def test_duplicate_within_batch_keeps_last_version(db_engine):
    """Deux lignes de même clé dans un lot : la dernière version est conservée (RI-010)."""
    batch = nettoyer_donnees([make_record(nb_train_prevu=1), make_record(nb_train_prevu=2)])
    insert_data(batch, db_engine)

    rows = read_rows(db_engine)
    assert len(rows) == 1
    assert rows[0]["nb_train_prevu"] == 2
