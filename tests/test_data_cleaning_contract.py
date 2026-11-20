"""Garde-fou : le nettoyage ne doit pas supprimer une colonne contractuelle vide."""

from utils import make_record

from railinsight.data.data_cleaning import COLUMNS, nettoyer_donnees


def test_contractual_column_is_kept_even_when_mostly_empty():
    # Six lignes (au-delà du seuil de 5) dont une cause contractuelle entièrement vide.
    records = [make_record(date=f"2018-{month:02d}", prct_cause_externe=None) for month in range(1, 7)]

    df = nettoyer_donnees(records)

    assert "prct_cause_externe" in COLUMNS
    assert "prct_cause_externe" in df.columns  # non supprimée par la règle des 90 %
    assert df["prct_cause_externe"].isna().all()
