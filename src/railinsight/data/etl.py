"""Pipeline ETL : récupération des données SNCF, nettoyage et chargement idempotent.

Interroge l'API open data SNCF (régularité mensuelle des TGV), nettoie les
enregistrements puis les insère en base par UPSERT (idempotent), avec une petite
fenêtre de reprise pour rattraper les rectifications publiées sur les mois récents.
"""

import logging
import os
import sys
from datetime import date, datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import Engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from railinsight.data.data_cleaning import COLUMNS, nettoyer_donnees  # Import de la fonction de nettoyage
from railinsight.database import db_table
from railinsight.database.conf_db import make_engine

load_dotenv()
logger = logging.getLogger(__name__)

TABLE = "regularite_tgv"
KEY = ["date", "service", "gare_depart", "gare_arrivee"]

# Fenêtre de reprise : on réinterroge l'API sur les derniers mois déjà chargés, afin
# de rattraper d'éventuelles rectifications publiées par la SNCF sur un mois récent.
# Combiné à l'UPSERT, cela reste idempotent (réimporter les mêmes données ne change rien).
RESYNC_MONTHS = 2


def dataset_url() -> str | None:
    """Adresse de l'API du jeu de données SNCF.

    Lit en priorité ``URL_SNCF_DATASET`` (nom correct) et, à défaut, l'ancien nom mal
    orthographié ``URl_SNCF_DATASET`` conservé par compatibilité avec les secrets déjà
    configurés. Aucune rupture : les deux noms fonctionnent.
    """
    return os.getenv("URL_SNCF_DATASET") or os.getenv("URl_SNCF_DATASET")


def _months_before(reference: date, months: int) -> date:
    """Retourne le premier jour du mois situé ``months`` mois avant ``reference``."""
    index = reference.year * 12 + (reference.month - 1) - months
    year, month = divmod(index, 12)
    return date(year, month + 1, 1)


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
        since_str = since.strftime("%Y-%m-%d") if isinstance(since, (date, datetime)) else str(since)
        # Borne inclusive : la fenêtre de reprise doit réimporter le mois `since` lui-même.
        params["where"] = f'date >= "{since_str}"'

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


def _upsert_statement(engine: Engine, records: list[dict]):
    """Construit un INSERT ... ON CONFLICT DO UPDATE adapté au dialecte de la base.

    PostgreSQL (production) et SQLite (tests) supportent tous deux ``ON CONFLICT`` ;
    seul le constructeur d'instruction diffère. En cas de conflit sur la clé
    (date, service, gare_depart, gare_arrivee), les colonnes non clés sont mises à
    jour avec les nouvelles valeurs : une rectification de la source est propagée.
    """
    table = db_table.regularite_tgv_table
    dialect = engine.dialect.name
    if dialect == "postgresql":
        stmt = pg_insert(table).values(records)
    elif dialect == "sqlite":
        stmt = sqlite_insert(table).values(records)
    else:
        raise RuntimeError(f"UPSERT non pris en charge pour le dialecte « {dialect} ».")

    updatable = {column.name: stmt.excluded[column.name] for column in table.columns if column.name not in KEY}
    return stmt.on_conflict_do_update(index_elements=KEY, set_=updatable)


def insert_data(data: pd.DataFrame, engine: Engine) -> None:
    """Insère ou met à jour les données nettoyées dans la base (UPSERT idempotent).

    Les doublons à l'intérieur d'un même lot sont d'abord écartés en conservant la
    dernière version (une rectification arrive après la valeur initiale). L'insertion
    utilise ensuite ``ON CONFLICT DO UPDATE`` : réimporter les mêmes données ne crée
    pas de doublon, et une valeur corrigée remplace l'ancienne.

    Args:
        data: DataFrame contenant les enregistrements à sauvegarder.
        engine: Moteur SQLAlchemy permettant d'accéder à la base de données.
    """
    if data.empty:
        logger.info("No data to insert.")
        return

    before = len(data)
    deduped = data.drop_duplicates(subset=KEY, keep="last")
    dropped = before - len(deduped)
    if dropped:
        logger.warning("Doublons intra-lot écartés (dernière version conservée) : %d", dropped)

    records = deduped.to_dict(orient="records")
    try:
        with engine.begin() as conn:
            conn.execute(_upsert_statement(engine, records))
        logger.info("Successfully upserted %d records.", len(records))
    except Exception:
        logger.exception("Failed to upsert records.")
        raise


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
    # Première charge : tout l'historique. Sinon : fenêtre de reprise sur les derniers
    # mois déjà chargés, pour rattraper d'éventuelles rectifications sans tout recharger.
    # MAX(date) renvoie un `date` sous PostgreSQL mais une chaîne sous SQLite : on normalise.
    since = None
    if last_record_date is not None:
        reference = last_record_date if isinstance(last_record_date, date) else date.fromisoformat(str(last_record_date)[:10])
        since = _months_before(reference, RESYNC_MONTHS)

    api_url = dataset_url()
    data = fetch_data(api_url, since)

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
