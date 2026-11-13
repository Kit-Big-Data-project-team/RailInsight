# def addition(a, b):
#     """Retourne la somme de deux nombres."""
#     return a + b

"""Point d'entrée principal du projet RailInsight.

Permet de lancer le chargement, le nettoyage des données et de préparer
le DataFrame pour les coéquipiers et les différentes vues.
"""

import logging

from railinsight.data.data_cleaning import FICHIER_LOCAL, URL_SNCF, TGVDataset
from railinsight.logging_config import setup_logging

# Configuration des logs pour observer le déroulement du nettoyage
setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    """Fonction principale pour exécuter le pipeline de données."""
    logger.info("Démarrage du projet RailInsight...")

    try:
        # 1. Initialisation du gestionnaire de dataset avec l'URL et le cache local
        gestionnaire = TGVDataset(url=URL_SNCF, chemin_cache=FICHIER_LOCAL)

        # 2. Exécution du nettoyage complet (gère l'API, le cache, les colonnes vides, dates et liaison)
        df_propre = gestionnaire.nettoyer_donnees()

        # 3. Vérification rapide que tout est prêt pour tes coéquipiers
        print(f"Données prêtes ! Dimensions du DataFrame : {df_propre.shape}")
        print("\nAperçu des premières lignes avec la nouvelle colonne 'liaison' :")
        print(df_propre[["date", "service", "liaison"]].head())

    except Exception as e:
        logger.error(fha=f"Une erreur est survenue lors du traitement : {e}")
        print(f"Erreur : {e}")


if __name__ == "__main__":
    main()
