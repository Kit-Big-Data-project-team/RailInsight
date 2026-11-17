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
    """Récupère les enregistrements bruts de la SNCF depuis l'API.

    Args:
        api_url: Adresse du point d'accès permettant de récupérer les données de régularité.
        since: Date minimale facultative. Seuls les enregistrements postérieurs à cette date sont récupérés.

    Returns:
        Liste des enregistrements bruts renvoyés par l'API, ou None en cas d'échec de la requête.
    """
    logger.info(f"Fetching data from API : {api_url}")

    params = {}
    if since is not None:
        params["where"] = f'date > "{since:%Y-%m-%d}"' if isinstance(since, datetime) else f'date > "{since}"'

    try:
        response = requests.get(api_url, params=params, timeout=120)
        response.raise_for_status()
        json_data = response.json()

        # L'endpoint /exports/json renvoie directement une liste. Si une réponse
        # paginée OpenDataSoft (/records) est utilisée, les lignes sont sous 'results'.
        if isinstance(json_data, dict):
            data = json_data.get("results", [])
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
    """Récupère la date la plus récente des données enregistrées dans la base.

    Args:
        engine: Moteur SQLAlchemy connecté à la base de données cible.

    Returns:
        Date du dernier enregistrement présent dans la table, ou None si celle-ci est vide.
    """
    query_last_month = f"SELECT MAX(date) FROM {TABLE}"
    with engine.connect() as conn:
        return conn.execute(text(query_last_month)).scalar_one()


def insert_data(data: pd.DataFrame, engine: Engine) -> None:
    """Insère les données nettoyées dans la base de données.

    Args:
        data: DataFrame contenant les enregistrements à sauvegarder.
        engine: Moteur SQLAlchemy permettant d'accéder à la base de données.
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
    """Exécute le processus ETL de récupération, de nettoyage et de stockage des données.

    Récupère les nouvelles données depuis l'API SNCF à partir de la dernière date
    enregistrée, les nettoie et vérifie leur conformité au schéma attendu avant
    de les insérer dans la base de données.

    Args:
        engine: Moteur SQLAlchemy facultatif. Un nouveau moteur est créé si aucun
            moteur n'est fourni.
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
    """Lance le processus ETL avec la configuration par défaut de la base de données."""
    logger.info("Démarrage pipeline ETL...")
    try:
        pipeline(None)
        logger.info("Pipeline ETL terminé avec succès.")
    except Exception as e:
        logger.error("Une erreur est survenue lors du traitement : %s", e)
        raise


if __name__ == "__main__":
    main()
