
"""Tests de préparation des données pour la prédiction."""

import pandas as pd
import pytest

from railinsight.analysis.prepare_prediction import prepare_prediction_data


def make_data(months, liaison="PARIS -> LYON", service="National"):
    """Crée des observations mensuelles fictives."""
    return pd.DataFrame({
        "date": pd.to_datetime(months),
        "liaison": liaison,
        "service": service,
        "scheduled": [100] * len(months),
        "cancelled": [0] * len(months),
        "late_arrival": [10 * (i + 1) for i in range(len(months))],
    })


def mock_loader(monkeypatch, df):
    """Remplace le chargement PostgreSQL par des données fictives."""

    class FakeDataset:
        def __init__(self):
            self.df = df

        @classmethod
        def from_db(cls):
            return cls()

    monkeypatch.setattr(
        "railinsight.analysis.prepare_prediction.TGVDataset",
        FakeDataset,
    )


def test_lags_use_previous_months(monkeypatch):
    """La cible d'avril utilise janvier, février et mars."""
    df = make_data([
        "2026-01-01",
        "2026-02-01",
        "2026-03-01",
        "2026-04-01",
        "2026-05-01",
    ])

    mock_loader(monkeypatch, df)
    result = prepare_prediction_data()

    april = result.loc[
        result["date"] == pd.Timestamp("2026-04-01")
    ].iloc[0]

    assert april["late_rate"] == pytest.approx(0.4)
    assert april["late_rate_lag1"] == pytest.approx(0.3)
    assert april["late_rate_lag2"] == pytest.approx(0.2)
    assert april["late_rate_lag3"] == pytest.approx(0.1)
    assert april["late_rate_mean3"] == pytest.approx(0.2)
    assert april["month"] == 4


def test_missing_month_is_not_treated_as_previous_month(monkeypatch):
    """Une interruption dans l'historique invalide les décalages."""
    df = make_data([
        "2026-01-01",
        "2026-02-01",
        "2026-04-01",
        "2026-05-01",
    ])

    mock_loader(monkeypatch, df)
    result = prepare_prediction_data()

    assert result.empty


def test_liaisons_are_independent(monkeypatch):
    """Les historiques de deux liaisons ne doivent pas être mélangés."""
    months = [
        "2026-01-01",
        "2026-02-01",
        "2026-03-01",
        "2026-04-01",
    ]

    first = make_data(months, liaison="PARIS -> LYON")
    second = make_data(months, liaison="LYON -> PARIS")
    second["late_arrival"] = [5, 10, 15, 20]

    mock_loader(
        monkeypatch,
        pd.concat([first, second], ignore_index=True),
    )

    result = prepare_prediction_data()

    assert len(result) == 2

    paris_lyon = result[
        result["liaison"] == "PARIS -> LYON"
    ].iloc[0]

    lyon_paris = result[
        result["liaison"] == "LYON -> PARIS"
    ].iloc[0]

    assert paris_lyon["late_rate_lag1"] == pytest.approx(0.3)
    assert lyon_paris["late_rate_lag1"] == pytest.approx(0.15)

def test_main_displays_prediction_summary(monkeypatch, capsys):
    """Vérifie que le script affiche un résumé des données préparées."""
    from railinsight.analysis.prepare_prediction import main

    df = make_data([
        "2026-01-01",
        "2026-02-01",
        "2026-03-01",
        "2026-04-01",
    ])

    mock_loader(monkeypatch, df)

    main()

    output = capsys.readouterr().out

    assert "DONNEES PRETES POUR LE MODELE" in output
    assert "Dimensions" in output
    assert "Taux de retard" in output