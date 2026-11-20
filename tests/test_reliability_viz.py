"""Tests des graphiques de la page Fiabilité des liaisons (sans accès base)."""

import pandas as pd

from railinsight.viz.reliability import reliability_bar, reliability_scatter


def _ranked() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "route": ["A", "B"],
            "reliability_score": [0.9, 0.5],
            "late_rate": [0.1, 0.3],
            "cancellation_rate": [0.01, 0.05],
            "scheduled": [1000, 800],
        }
    )


def test_reliability_bar_builds_a_horizontal_bar():
    fig = reliability_bar(_ranked(), title="Top fiables")

    assert len(fig.data) == 1
    assert fig.data[0].type == "bar"


def test_reliability_scatter_plots_late_vs_cancellation():
    fig = reliability_scatter(_ranked())

    assert len(fig.data) == 1
    assert fig.data[0].type == "scatter"
