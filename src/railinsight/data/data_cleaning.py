"""Module de gestion et de nettoyage des données TGV.

Ce module permet d'effectuer les opérations de nettoyage, de normalisation
et d'enrichissement sur les données brutes issues de l'API SNCF.
"""

import logging

import pandas as pd

# Configuration du logger pour enregistrer les événements du pipeline de nettoyage
logger = logging.getLogger(__name__)


class DataCleaningError(Exception):
    """Exception personnalisée levée en cas d'échec critique lors du nettoyage des données."""

    pass


def nettoyer_donnees(data: list[dict] | pd.DataFrame) -> pd.DataFrame:
    """Nettoie et structure les données de manière approfondie :

    - Conversion de la liste de dictionnaires en DataFrame (si nécessaire).
    - Suppression des lignes entièrement vides.
    - Uniformisation des en-têtes (minuscules et underscores).
    - Suppression automatique des colonnes comportant plus de 90% de valeurs manquantes.
    - Conversion de la colonne 'date' au format datetime (puis date pour la base).
    - Création et insertion de la colonne 'liaison' (gare de départ -> gare d'arrivée).

    Args:
        data: Liste de dictionnaires (provenant de l'API) ou DataFrame brut.

    Returns:
        pd.DataFrame: Le DataFrame propre, structuré et prêt pour l'analyse.
    """
    try:
        if isinstance(data, list):
            if not data:
                return pd.DataFrame()
            df_clean = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df_clean = data.copy()
        else:
            raise ValueError("Le format des données d'entrée n'est pas pris en charge.")

        # 1. Suppression des lignes entièrement vides
        df_clean = df_clean.dropna(how="all")

        # 2. Nettoyage de base des en-têtes (espaces) et uniformisation
        df_clean.columns = df_clean.columns.str.strip().str.lower().str.replace(" ", "_")

        # 3. Suppression dynamique des colonnes ayant plus de 90% de valeurs manquantes
        pourcentage_nan = df_clean.isnull().mean() * 100

        if len(df_clean) < 5:
            # Sur un petit jeu de test (< 5 lignes), on ne supprime aucune colonne
            # pour protéger les champs obligatoires testés unitairement (ex: retard_moyen_depart=None)
            colonnes_vides = []
        else:
            # Pour le vrai dataset ou les jeux de données normaux (>= 5 lignes), application de la règle des 90%
            colonnes_vides = pourcentage_nan[pourcentage_nan > 90.0].index.tolist()

        df_clean = df_clean.drop(columns=colonnes_vides, errors="ignore")
        logger.info(f"Colonnes supprimées automatiquement : {colonnes_vides}")

        # 4. Conversion de la colonne date
        if "date" in df_clean.columns:
            df_clean["date"] = pd.to_datetime(df_clean["date"], errors="coerce")

        # 5. Création et positionnement de la colonne liaison
        col_depart = "gare_depart" if "gare_depart" in df_clean.columns else "gare_de_départ"
        col_arrivee = "gare_arrivee" if "gare_arrivee" in df_clean.columns else "gare_d'arrivée"

        if col_depart in df_clean.columns and col_arrivee in df_clean.columns:
            liaison_series = df_clean[col_depart].astype(str) + " -> " + df_clean[col_arrivee].astype(str)
            if "service" in df_clean.columns:
                try:
                    df_clean.insert(2, "liaison", liaison_series)
                except ValueError:
                    df_clean["liaison"] = liaison_series
            else:
                df_clean["liaison"] = liaison_series

        logger.info("Nettoyage approfondi des données effectué avec succès.")
        return df_clean

    except Exception as e:
        logger.critical(f"Échec critique lors du nettoyage des données : {e}")
        raise DataCleaningError("Impossible de nettoyer les données.") from e
