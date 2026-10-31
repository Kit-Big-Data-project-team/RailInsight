import logging
import os
import sys
from datetime import date, datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import Engine, insert, text

from railinsight.database import db_table
from railinsight.database.conf_db import make_engine

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
    """Fetch raw SNCF records from the API since the provided date.

    Args:
        api_url: The endpoint used to retrieve the regularity dataset.
        since: Optional lower bound date. Only records newer than this date are returned.

    Returns:
        A list of raw API records, or None if the request fails.
    """
    logger.info(f"Fetching data from API : {api_url}")

    params = {}
    if since is not None:
        params["where"] = f'date > "{since:%Y-%m-%d}"' if isinstance(since, datetime) else f'date > "{since}"'
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
    """Convert the raw API payload into a DataFrame using the expected schema.

    Args:
        data: Raw records returned by the API.

    Returns:
        A DataFrame containing the normalized columns expected by the database.
    """
    df = pd.DataFrame(data)
    # Convertir les NaN/NaT en None pour PostgreSQL.
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df[COLUMNS]


def last_loaded_month(engine: Engine) -> date | None:
    """Retrieves the date of the most recently recorded data from the database.

    Args:
        engine: SQLAlchemy engine connected to the target database.

    Returns:
        The latest date present in the table, or None if the table is empty.
    """
    query_last_month = f"SELECT MAX(date) FROM {TABLE}"
    with engine.connect() as conn:
        return conn.execute(text(query_last_month)).scalar_one()


def insert_data(data: pd.DataFrame, engine: Engine) -> None:
    """Insert data into database.

    Args:
        data: DataFrame containing rows to persist.
        engine: SQLAlchemy engine connected to the database.
    """

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


def pipeline(engine: Engine | None):
    """Run the ETL workflow: fetch new data, transform it, and write it to the DB.

    Args:
        engine: Optional SQLAlchemy engine. A new engine is created if omitted.
    """
    if not engine:
        engine = make_engine()
    last_record_date = last_loaded_month(engine)
    api_url = os.getenv("URl_SNCF_DATASET")
    data = fetch_data(api_url, last_record_date)
    if data is None:
        logger.error("Data retrieval failed. Stopping ETL.")
        sys.exit(1)
    if not data:
        logger.info("No new data.")
        return

    df = transform(data)
    insert_data(df, engine)


def main():
    """Execute the ETL pipeline with the default database configuration."""
    pipeline(None)


if __name__ == "__main__":
    main()
