"""Point d'entrée principal du projet RailInsight.

Initialise la base de données si nécessaire, puis exécute le pipeline ETL
qui récupère les données SNCF, les nettoie et les insère en base.
"""

import logging

from railinsight.data.etl import pipeline
from railinsight.database.init_db import init_db
from railinsight.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Exécute le pipeline de données RailInsight de bout en bout."""
    setup_logging()
    logger.info("Démarrage du projet RailInsight...")

    try:
        init_db()
        pipeline(None)
        logger.info("Pipeline RailInsight terminé avec succès.")
    except Exception as e:
        logger.error("Une erreur est survenue lors du traitement : %s", e)
        raise


if __name__ == "__main__":
    main()
