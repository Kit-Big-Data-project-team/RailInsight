"""Initialisation du schéma de la base de données.

Crée les tables définies dans ``db_table`` si elles n'existent pas déjà. Toute erreur
d'initialisation est journalisée puis relancée : une base inaccessible ne doit jamais
passer pour un succès.
"""

import logging

from railinsight.database import db_table
from railinsight.database.conf_db import make_engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialise la base de données et crée les tables nécessaires.

    Utilise le moteur SQLAlchemy pour créer les tables définies dans les
    métadonnées du module db_table. Les tables existantes sont conservées
    et ne sont pas recréées.

    Enregistre les opérations et les éventuelles erreurs dans les journaux,
    puis libère les ressources de connexion à la base de données.

    Raises:
        Exception: Toute erreur d'initialisation est journalisée puis relancée.
            Une base inaccessible ou un schéma incompatible ne doit pas passer
            pour un succès : l'appelant (ETL, entrypoint) doit pouvoir échouer.
    """

    engine = make_engine()
    try:
        db_table.metadata.create_all(engine)
        logger.info(f"Database {db_table.TABLE_NAME} and tables created successfully")
    except Exception:
        logger.exception("Database initialization failed")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    init_db()
