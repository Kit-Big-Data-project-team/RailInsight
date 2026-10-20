"""
Description :
Charge le CSV, vérifie les colonnes, traite les valeurs manquantes et prépare les données.

"""

import logging
from pathlib import Path

import pandas as pd

from railinsight.exceptions import DataValidationError, RouteNotFoundError

logger = logging.getLogger(__name__)

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
    """Jeu de données de régularité TGV, nettoyé et prêt à interroger."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    @classmethod
    def from_csv(cls, path: str | Path) -> "TGVDataset":
        raw = pd.read_csv(path, sep=";", encoding="utf-8-sig")
        missing = set(RENAME) - set(raw.columns)
        if missing:
            raise DataValidationError(f"Colonnes manquantes : {sorted(missing)}")
        df = raw.rename(columns=RENAME)[list(RENAME.values())].copy()
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m")
        df["route"] = df["origin"] + " → " + df["destination"]
        n0 = len(df)
        df = df[df["scheduled"] > 0]  # lignes vides
        logger.info("Lignes vides retirées : %d", n0 - len(df))
        return cls(df)

    def routes(self) -> list[str]:
        return sorted(self.df["route"].unique())

    def for_route(self, route: str) -> pd.DataFrame:
        sub = self.df[self.df["route"] == route]
        if sub.empty:
            raise RouteNotFoundError(route)
        return sub
