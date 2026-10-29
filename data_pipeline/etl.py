import logging
import os
import sys
from datetime import date

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import Engine, insert, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db_table
from database.conf_db import make_engine

load_dotenv()
logger = logging.getLogger(__name__)

TABLE = "regularite_tgv"
KEY = ["date", "service", "gare_depart", "gare_arrivee"]

COLUMNS = [
    "date",
    "service",
    "gare_depart",
    "gare_arrivee",
    "duree_moyenne",
    "nb_train_prevu",
    "nb_annulation",
    "nb_train_depart_retard",
    "retard_moyen_depart",
    "retard_moyen_tous_trains_depart",
    "nb_train_retard_arrivee",
    "retard_moyen_arrivee",
    "retard_moyen_tous_trains_arrivee",
    "nb_train_retard_sup_15",
    "retard_moyen_trains_retard_sup15",
    "nb_train_retard_sup_30",
    "nb_train_retard_sup_60",
    "prct_cause_externe",
    "prct_cause_infra",
    "prct_cause_gestion_trafic",
    "prct_cause_materiel_roulant",
    "prct_cause_gestion_gare",
    "prct_cause_prise_en_charge_voyageurs",
]


def fetch_data(api_url: str, since: date | None) -> list[dict] | None:
    logger.info(f"Fetching data from API : {api_url}")

    params = {}
    if since is not None:
        params["where"] = f'date > "{since:%Y-%m}"'
    try:
        response = requests.get(api_url, params=params, timeout=120)
        response.raise_for_status()
        data = response.json()
        logger.info("Data successfully retrieved. \n HTTP Status : %d. \n Number of data : %d", response.status_code, len(data))
        return data
    except requests.exceptions.Timeout:
        logger.error("API request timed out.")
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error occurred: %s", e)
    except requests.exceptions.RequestException as e:
        logger.error("API request failed: %s", e)
    except ValueError:
        logger.error("Failed to decode API response as JSON.")

    return None


def transform(data: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(data)
    # Convertir les NaN/NaT en None pour PostgreSQL.
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df[COLUMNS]


def last_loaded_month(engine: Engine) -> date | None:
    query_last_month = f"SELECT MAX(date) FROM {TABLE}"
    with engine.connect() as conn:
        return conn.execute(text(query_last_month)).scalar_one()


def insert_data(data: pd.DataFrame, engine: Engine) -> None:
    """Insert data into database."""

    if data.empty:
        logger.info("No data to insert.")
        return
    records = data.to_dict(orient="records")
    try:
        with engine.begin() as conn:
            stmt = insert(db_table.regularite_tgv_table).values(records)
            conn.execute(stmt)
        logger.info("Successfully processed %d records.", len(records))
    except Exception:
        logger.exception("Failed to insert records.")
        raise
    finally:
        engine.dispose()


def main():
    engine = make_engine()
    last_record_date = last_loaded_month(engine)
    api_url = os.getenv("URl_SNCF_DATASET")
    try:
        data = fetch_data(api_url, last_record_date)

    except Exception as e:
        logger.error("Data retrieval failed. Stopping ETL : %s", e)

        sys.exit(1)
    df = transform(data)
    if df.empty:
        logger.info("No new data.")
        return
    insert_data(df, engine)


if __name__ == "__main__":
    main()
