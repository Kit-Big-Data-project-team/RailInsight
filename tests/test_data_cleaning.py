import pandas as pd
import pytest

from railinsight.data_cleaning import DataCleaningError, TGVDataset


def test_nettoyer_donnees(tmp_path):
    """Teste le processus complet de nettoyage sur un DataFrame simulé."""
    # Création de données brutes factices pour le test
    data = {
        "Date": ["2018-01", "2018-02"],
        "Service": ["National", "National"],
        "Gare de départ": ["PARIS", "LYON"],
        "Gare d'arrivée": ["LYON", "MARSEILLE"],
        "Commentaire annulations": [None, None],  # Sera supprimé (>90% vide)
    }
    df_brut = pd.DataFrame(data)

    # Fichier cache temporaire
    cache_file = tmp_path / "cache_test.csv"
    df_brut.to_csv(cache_file, sep=";", index=False)

    # Initialisation et injection des données brutes
    dataset = TGVDataset(url="http://fake-url", chemin_cache=cache_file)
    dataset.df = df_brut.copy()

    # Exécution du nettoyage
    df_clean = dataset.nettoyer_donnees()

    # Validations
    assert "liaison" in df_clean.columns, "La colonne 'liaison' doit être créée"
    assert df_clean.loc[0, "liaison"] == "PARIS -> LYON"
    assert "commentaire_annulations" not in df_clean.columns, "La colonne vide (>90%) doit être supprimée"
    assert pd.api.types.is_datetime64_any_dtype(df_clean["date"]), "La date doit être au format datetime"


def test_charger_donnees_fallback(tmp_path):
    """Teste le basculement (fallback) sur le cache local si l'API est injoignable."""
    cache_file = tmp_path / "cache_test.csv"
    df_cache = pd.DataFrame({"date": ["2018-01"], "service": ["National"]})
    df_cache.to_csv(cache_file, sep=";", index=False)

    # URL intentionnellement fausse pour forcer l'échec de l'API
    dataset = TGVDataset(url="http://url-invalide-qui-nexiste-pas.com", chemin_cache=cache_file)
    df_charge = dataset.charger_donnees()

    assert not df_charge.empty
    assert "date" in df_charge.columns


def test_charger_donnees_erreur_critique(tmp_path):
    """Teste la levée d'une exception si l'API échoue et qu'aucun cache n'existe."""
    cache_file = tmp_path / "inexistant.csv"
    dataset = TGVDataset(url="http://url-invalide-qui-nexiste-pas.com", chemin_cache=cache_file)

    with pytest.raises(DataCleaningError):
        dataset.charger_donnees()


def test_charger_donnees_api_succes_sans_cache(tmp_path, monkeypatch):
    """Teste le cas où l'API réussit à télécharger les données et crée le cache."""
    cache_file = tmp_path / "nouveau_cache.csv"

    # On simule un retour d'API réussi en remplaçant pd.read_csv par un DataFrame factice
    df_mock = pd.DataFrame({"date": ["2020-01"], "service": ["National"], "gare de départ": ["A"], "gare d'arrivée": ["B"]})

    monkeypatch.setattr("pandas.read_csv", lambda *args, **kwargs: df_mock)

    dataset = TGVDataset(url="http://fake-url", chemin_cache=cache_file)
    df_result = dataset.charger_donnees()

    assert not df_result.empty
    assert cache_file.exists(), "Le fichier cache local doit être créé après un succès API"
