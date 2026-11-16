"""Tests des métriques de la page Fiabilité (tâche 5)."""

import pandas as pd

from railinsight.analysis.reliability import (
    reliability_by_service,
    route_reliability,
    top_reliable,
    top_unreliable,
)


def _sample() -> pd.DataFrame:
    """Trois liaisons : A très fiable, B peu fiable, C fiable mais trafic minuscule."""
    return pd.DataFrame(
        {
            "route": ["A", "A", "B", "B", "C"],
            "service": ["National", "National", "International", "International", "National"],
            "scheduled": [60, 40, 50, 50, 5],
            "cancelled": [0, 0, 5, 5, 0],
            "late_arrival": [5, 0, 20, 20, 0],
        }
    )


def test_route_reliability_score():
    out = route_reliability(_sample()).set_index("route")

    assert out.loc["A", "reliability_score"] == 0.95
    assert out.loc["B", "reliability_score"] == 0.50


def test_top_reliable_respects_min_scheduled():
    out = top_reliable(_sample(), n=10, min_scheduled=10)

    assert "C" not in out["route"].values
    assert out.iloc[0]["route"] == "A"


def test_top_unreliable_puts_worst_first():
    out = top_unreliable(_sample(), n=10, min_scheduled=10)

    assert out.iloc[0]["route"] == "B"


def test_reliability_by_service_aggregates_per_service():
    out = reliability_by_service(_sample()).set_index("service")

    # National = A (100, 0 annulés, 5 retards) + C (5, 0, 0) -> (105 - 0 - 5) / 105
    assert out.loc["National", "reliability_score"] == 100 / 105
    # International = B (100, 10 annulés, 40 retards) -> (100 - 10 - 40) / 100
    assert out.loc["International", "reliability_score"] == 0.50
