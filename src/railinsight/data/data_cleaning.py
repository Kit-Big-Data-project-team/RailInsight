"""Module de gestion et de nettoyage des données TGV.

Ce module permet de charger le jeu de données de régularité mensuelle TGV
depuis l'API Open Data de la SNCF avec un système de secours (fallback)
sur un fichier local en cache, et d'effectuer les opérations de nettoyage nécessaires.
"""

import logging
from pathlib import Path

import pandas as pd

# Configuration du logger pour enregistrer les événements dans les fichiers de logs du projet
logger = logging.getLogger(__name__)

# Définition des constantes globales pour l'URL de l'API SNCF et les chemins locaux
URL_SNCF = (
    "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/" "regularite-mensuelle-tgv-aqst/exports/csv?lang=fr&timezone=Europe%2FParis" "&use_labels=true&csv_separator=%3B"
)
DOSSIER_DATA = Path("data")
FICHIER_LOCAL = DOSSIER_DATA / "regularite-mensuelle-tgv-aqst.csv"


class DataCleaningError(Exception):
    """Exception personnalisée levée en cas d'échec critique du chargement

    ou du nettoyage des données (ex: API injoignable et absence de cache local).
    """

    pass


class TGVDataset:
    """Classe responsable du chargement hybride (API + Cache local)

    et du nettoyage rigoureux des données de ponctualité TGV.
    """

    def __init__(self, url: str, chemin_cache: Path) -> None:
        """Initialise le gestionnaire de dataset TGV.

        Args:
            url (str): L'URL de l'API Open Data SNCF pour l'export CSV.
            chemin_cache (Path): Le chemin vers le fichier CSV local de secours.
        """
        self.url = url
        self.chemin_cache = Path(chemin_cache)
        # Attribut qui stockera le DataFrame pandas une fois chargé en mémoire
        self.df: pd.DataFrame | None = None

    def charger_donnees(self) -> pd.DataFrame:
        """Charge le jeu de données depuis l'API SNCF.

        En cas d'échec (absence de réseau ou indisponibilité du service distant),
        le système bascule automatiquement sur la copie locale en cache.

        Returns:
            pd.DataFrame: Le DataFrame contenant les données brutes chargées.

        Raises:
            DataCleaningError: Si l'API est inaccessible et qu'aucun fichier
                local de secours n'est présent sur le disque.
        """
        # Étape 1 : S'assurer que le dossier parent du cache (ex: 'data/') existe physiquement
        self.chemin_cache.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Étape 2 : Tentative de récupération des données fraîches depuis l'API en ligne
            logger.info("Tentative de telechargement des donnees depuis l'API SNCF.")
            df_temp = pd.read_csv(self.url, sep=";")

            # Étape 3 : Sauvegarde de ces données en local pour constituer un cache à jour
            df_temp.to_csv(self.chemin_cache, sep=";", index=False)
            logger.info("Copie locale mise a jour avec succes dans le dossier data.")
            self.df = df_temp

        except Exception as api_error:
            # Étape 4 : En cas d'erreur réseau, on bascule sur le fichier de secours local
            logger.warning(f"Impossible de contacter l'API ({api_error}). Tentative de chargement du cache local.")

            if self.chemin_cache.exists():
                logger.info("Chargement de la version locale en cache.")
                self.df = pd.read_csv(self.chemin_cache, sep=";")
            else:
                # Étape 5 : Si le cache n'existe pas non plus, on lève une erreur critique personnalisée
                logger.critical("Echec critique : API injoignable et aucun fichier local de secours trouve.")
                raise DataCleaningError("Impossible d'acceder a l'API et aucun fichier local trouve dans data/.") from api_error

        # Étape 6 : Nettoyage de base des en-têtes (suppression des espaces superflus)
        self.df.columns = self.df.columns.str.strip()
        return self.df

    def nettoyer_donnees(self) -> pd.DataFrame:
        """Nettoie le DataFrame de manière approfondie :

        - Suppression des lignes entièrement vides
        - Uniformisation des en-têtes (minuscules et underscores)
        - Suppression automatique des colonnes trop vides (>90% de NaN)
        - Conversion de la date en type datetime
        - Insertion de la colonne 'liaison' à l'index 2

        Returns:
            pd.DataFrame: Le DataFrame propre, structuré et prêt pour l'analyse.
        """
        if self.df is None:
            self.charger_donnees()

        # Création d'une copie pour éviter de modifier directement le DataFrame brut initial
        df_clean = self.df.copy()

        # 1. Suppression des lignes qui sont complètement vides
        df_clean = df_clean.dropna(how="all")

        # 2. Uniformisation des noms de colonnes (minuscules et underscores)
        df_clean.columns = df_clean.columns.str.strip().str.lower().str.replace(" ", "_")

        # 3. Suppression dynamique des colonnes ayant plus de 90% de valeurs manquantes
        seuil_manquant = 90.0
        pourcentage_nan = df_clean.isnull().mean() * 100
        colonnes_vides = pourcentage_nan[pourcentage_nan > seuil_manquant].index.tolist()
        df_clean = df_clean.drop(columns=colonnes_vides, errors="ignore")
        logger.info(f"Colonnes supprimees automatiquement (>90% vides) : {colonnes_vides}")

        # 4. Conversion de la colonne date en type datetime
        if "date" in df_clean.columns:
            df_clean["date"] = pd.to_datetime(df_clean["date"], errors="coerce")

        # 5. Création et positionnement de la colonne liaison à l'index 2 (après service)
        if "gare_de_départ" in df_clean.columns and "gare_d'arrivée" in df_clean.columns:
            liaison_series = df_clean["gare_de_départ"] + " -> " + df_clean["gare_d'arrivée"]
            df_clean.insert(2, "liaison", liaison_series)

        logger.info("Nettoyage approfondi des donnees effectue avec succes.")
        return df_clean
