"""Graphiques de la prévision avec intervalles et du backtesting."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

RATE_LABELS = {"mae_model": "Modèle", "mae_baseline": "Référence (mois précédent)"}


def backtest_error_line(backtest: pd.DataFrame, title: str = "Erreur de prévision mois par mois (backtesting)") -> go.Figure:
    """Courbes de l'erreur absolue moyenne du modèle et de la référence au fil des mois.

    Args:
        backtest: Sortie de walk_forward_backtest (date, mae_model, mae_baseline).
        title: Titre de la figure.

    Returns:
        Figure Plotly ; une erreur plus basse et sous la référence indique un meilleur modèle.
    """
    long = backtest.melt(id_vars="date", value_vars=["mae_model", "mae_baseline"], var_name="Série", value_name="MAE")
    long["Série"] = long["Série"].map(RATE_LABELS)
    fig = px.line(long, x="date", y="MAE", color="Série", title=title, labels={"date": "", "MAE": "Erreur absolue moyenne"})
    fig.update_layout(yaxis_tickformat=".1%")
    return fig


def forecast_interval_chart(history: pd.DataFrame, forecast: dict, title: str = "Prévision du mois prochain avec intervalle") -> go.Figure:
    """Trace l'historique récent d'une liaison et la prévision encadrée par son intervalle.

    Args:
        history: Données observées récentes avec les colonnes date et late_rate.
        forecast: Dictionnaire date, low, median, high de la prévision.
        title: Titre de la figure.

    Returns:
        Figure Plotly : ligne historique + point de prévision avec barres d'incertitude.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=history["date"], y=history["late_rate"], mode="lines+markers", name="Observé"))
    fig.add_trace(
        go.Scatter(
            x=[forecast["date"]],
            y=[forecast["median"]],
            mode="markers",
            name="Prévision",
            marker={"size": 11, "color": "#BE4850"},
            error_y={
                "type": "data",
                "symmetric": False,
                "array": [forecast["high"] - forecast["median"]],
                "arrayminus": [forecast["median"] - forecast["low"]],
            },
        )
    )
    fig.update_layout(title=title, yaxis_tickformat=".0%", xaxis_title="", yaxis_title="Taux de retard")
    return fig
