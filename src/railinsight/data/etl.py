import logging
import os
import sys
from datetime import date, datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import Engine, insert, text

from railinsight.data.data_cleaning import COLUMNS, nettoyer_donnees  # Import de la fonction de nettoyage
from railinsight.database import db_table
from railinsight.database.conf_db import make_engine

load_dotenv()
logger = logging.getLogger(__name__)

TABLE = "regularite_tgv"
KEY = ["date", "service", "gare_depart", "gare_arrivee"]


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
        json_data = response.json()

        # Extraction garantie de la liste sous 'results' si le format est un dictionnaire OpenDataSoft
        if isinstance(json_data, dict):
            data = [json_data]
        else:
            data = json_data

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
    """Run the ETL workflow: fetch new data, clean it directly, and write it to the DB.

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

    df = nettoyer_donnees(data)

    # Vérification stricte du schéma requis avant l'insertion en base
    for col in COLUMNS:
        if col not in df.columns:
            raise KeyError(f"Missing expected column: {col}")

    insert_data(df, engine)


def main():
    """Execute the ETL pipeline with the default database configuration."""
    pipeline(None)


if __name__ == "__main__":
    main()
