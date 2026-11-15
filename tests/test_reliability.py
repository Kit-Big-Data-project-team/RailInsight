"""Tests des métriques de la page Fiabilité (tâche 5)."""

import pandas as pd

from railinsight.analysis.reliability import route_reliability, top_reliable, top_unreliable


def _sample() -> pd.DataFrame:
    """Trois liaisons : A très fiable, B peu fiable, C fiable mais trafic minuscule."""
    return pd.DataFrame(
        {
            "route": ["A", "A", "B", "B", "C"],
            "scheduled": [60, 40, 50, 50, 5],
            "cancelled": [0, 0, 5, 5, 0],
            "late_arrival": [5, 0, 20, 20, 0],
        }
    )


def test_route_reliability_score():
    out = route_reliability(_sample()).set_index("route")

    # A : (100 - 0 - 5) / 100 = 0.95
    assert out.loc["A", "reliability_score"] == 0.95
    # B : (100 - 10 - 40) / 100 = 0.50
    assert out.loc["B", "reliability_score"] == 0.50


def test_top_reliable_respects_min_scheduled():
    # C est "parfaite" (score 1.0) mais n'a que 5 trains -> exclue par le seuil
    out = top_reliable(_sample(), n=10, min_scheduled=10)

    assert "C" not in out["route"].values
    assert out.iloc[0]["route"] == "A"  # meilleure liaison retenue


def test_top_unreliable_puts_worst_first():
    out = top_unreliable(_sample(), n=10, min_scheduled=10)

    assert out.iloc[0]["route"] == "B"
