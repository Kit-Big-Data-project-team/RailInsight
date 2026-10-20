"""
Description :
Contient les exceptions personnalisées pour le projet RailInsight.

"""


class RailInsightError(Exception):
    """Base de toutes les erreurs du projet."""


class RouteNotFoundError(RailInsightError):
    """La liaison demandée n'existe pas dans le jeu de données."""


class PeriodOutOfRangeError(RailInsightError):
    """La période demandée est hors de la plage disponible."""


class DataValidationError(RailInsightError):
    """Le fichier de données est invalide (colonnes manquantes...)."""
