"""Module de chargement et de préparation des datasets TGV.

Ce module permet de charger les données de ponctualité TGV soit depuis un
fichier CSV brut, soit directement depuis la base de données PostgreSQL,
puis d'appliquer les validations et les transformations nécessaires pour l'analyse.
"""

import logging

import pandas as pd

from railinsight.database.conf_db import make_engine
from railinsight.exceptions import RouteNotFoundError

# Configuration du logger pour le suivi des opérations de chargement
logger = logging.getLogger(__name__)

# Dictionnaire de correspondance pour renommer les colonnes brutes vers le schéma standard
RENAME = {
    "Date": "date",
    "Gare de départ": "origin",
    "Gare d'arrivée": "destination",
    "Nombre de circulations prévues": "scheduled",
    "Nombre de trains annulés": "cancelled",
    "Nombre de trains en retard à l'arrivée": "late_arrival",
    "Nombre trains en retard > 15min": "late_15",
}


class TGVDataset:
    """Représente le jeu de données de régularité TGV, nettoyé et prêt à être interrogé."""

    def __init__(self, df: pd.DataFrame) -> None:
        """Initialise le dataset TGV avec un DataFrame Pandas préparé.

        Args:
            df (pd.DataFrame): Le DataFrame contenant les données normalisées.
        """
        self.df = df

    # @classmethod
    # def from_csv(cls, path: str | Path) -> "TGVDataset":
    #     """Charge et valide les données TGV à partir d'un fichier CSV local.

    #     Args:
    #         path (str | Path): Chemin vers le fichier CSV source.

    #     Returns:
    #         TGVDataset: Une instance de la classe contenant les données nettoyées.

    #     Raises:
    #         DataValidationError: Si des colonnes obligatoires manquent dans le CSV.
    #     """
    #     raw = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    #     missing = set(RENAME) - set(raw.columns)
    #     if missing:
    #         raise DataValidationError(f"Colonnes manquantes : {sorted(missing)}")

    #     df = raw.rename(columns=RENAME)[list(RENAME.values())].copy()
    #     df["date"] = pd.to_datetime(df["date"], format="%Y-%m")
    #     df["route"] = df["origin"] + " → " + df["destination"]

    #     n0 = len(df)
    #     df = df[df["scheduled"] > 0]  # Suppression des lignes vides ou sans circulations prévues
    #     logger.info("Lignes vides retirées du CSV : %d", n0 - len(df))

    #     return cls(df)

    @classmethod
    def from_db(cls) -> "TGVDataset":
        """Charge les données de ponctualité TGV directement depuis la base PostgreSQL.

        Returns:
            TGVDataset: Une instance de la classe contenant les données de la base.
        """
        logger.info("Chargement des données depuis la base PostgreSQL...")
        engine = make_engine()
        query = "SELECT * FROM regularite_tgv"

        try:
            df = pd.read_sql(query, con=engine)
        finally:
            engine.dispose()  # Fermeture propre de la connexion à la base

        if df.empty:
            logger.warning("La table de la base de données est vide.")
            return cls(df)

        # Mapping des colonnes de la base vers le format interne standard
        db_rename = {
            "gare_depart": "origin",
            "gare_arrivee": "destination",
            "nb_train_prevu": "scheduled",
            "nb_annulation": "cancelled",
            "nb_train_retard_arrivee": "late_arrival",
            "nb_train_retard_sup_15": "late_15",
        }

        df = df.rename(columns=db_rename)

        # Traitements de normalisation standard
        df["date"] = pd.to_datetime(df["date"])
        df["route"] = df["origin"] + " → " + df["destination"]

        n0 = len(df)
        if "scheduled" in df.columns:
            df = df[df["scheduled"] > 0]
        logger.info("Lignes vides retirées (depuis la BD) : %d", n0 - len(df))

        return cls(df)

    def routes(self) -> list[str]:
        """Retourne la liste triée de toutes les liaisons (routes) disponibles dans le dataset.

        Returns:
            list[str]: Liste des routes uniques.
        """
        return sorted(self.df["route"].unique())

    def for_route(self, route: str) -> pd.DataFrame:
        """Extrait les données filtrées pour une liaison (route) spécifique.

        Args:
            route (str): Le nom de la liaison (ex: 'PARIS -> LYON').

        Returns:
            pd.DataFrame: Le sous-ensemble de données correspondant à la route.

        Raises:
            RouteNotFoundError: Si la route demandée n'existe pas dans le dataset.
        """
        sub = self.df[self.df["route"] == route]
        if sub.empty:
            raise RouteNotFoundError(route)
        return sub
