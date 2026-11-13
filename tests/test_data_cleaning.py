"""Module de tests unitaires pour la fonction de nettoyage des données TGV.

Ce module valide le bon fonctionnement de la fonction nettoyer_donnees
en vérifiant l'ensemble des règles de nettoyage, de normalisation et d'enrichissement.
"""

import pandas as pd
import pytest

from railinsight.data.data_cleaning import DataCleaningError, nettoyer_donnees


def test_nettoyer_donnees_avec_service():
    """Teste le nettoyage complet avec la colonne 'service' présente et la suppression des colonnes vides."""
    # 5 lignes pour simuler un dataset suffisant pour déclencher la suppression de la colonne vide
    donnees_brutes = [
        {
            "date": "2018-01",
            "service": "National",
            "gare_depart": "PARIS",
            "gare_arrivee": "LYON",
            "col_vide": None,  # 100% vide sur 5 lignes -> sera supprimée
        }
        for _ in range(5)
    ]

    df_clean = nettoyer_donnees(donnees_brutes)

    assert "liaison" in df_clean.columns
    assert df_clean.loc[0, "liaison"] == "PARIS -> LYON"
    assert "service" in df_clean.columns
    assert "col_vide" not in df_clean.columns  # Vérifie que la colonne vide a bien été supprimée


def test_nettoyer_donnees_sans_service():
    """Teste le nettoyage lorsque la colonne 'service' est absente du jeu de données."""
    donnees_brutes = pd.DataFrame(
        {
            "date": ["2018-01"],
            "gare_depart": ["LILLE"],
            "gare_arrivee": ["NANTES"],
        }
    )

    df_clean = nettoyer_donnees(donnees_brutes)

    assert "liaison" in df_clean.columns
    assert df_clean.loc[0, "liaison"] == "LILLE -> NANTES"


def test_nettoyer_donnees_liste_vide():
    """Teste le comportement de la fonction si la liste de données d'entrée est vide."""
    df_clean = nettoyer_donnees([])
    assert df_clean.empty


def test_nettoyer_donnees_format_invalide():
    """Teste la levée d'erreur si le format d'entrée n'est ni une liste ni un DataFrame."""
    with pytest.raises(DataCleaningError):
        nettoyer_donnees("format_texte_invalide")
