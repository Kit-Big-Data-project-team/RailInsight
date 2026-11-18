"""Configuration commune du modèle de prédiction."""

from sklearn.ensemble import RandomForestRegressor

FEATURES = [
    "late_rate_lag1",
    "late_rate_lag2",
    "late_rate_lag3",
    "late_rate_mean3",
    "month",
]


def create_model() -> RandomForestRegressor:
    """Crée le modèle Random Forest utilisé pour les prédictions.

    Returns:
        RandomForestRegressor configuré avec 100 arbres,
        une profondeur maximale de 8 et une graine fixe
        pour assurer la reproductibilité.
    """
    return RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )