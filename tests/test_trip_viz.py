"""Tests des représentations de Mon trajet et de leurs dénominateurs."""

import pandas as pd
import pytest

from railinsight.analysis.trip import OUTCOME_LABELS
from railinsight.viz.trip import causes_bar, causes_pie, comparison_bars, outcomes_bar


def test_outcomes_use_three_exclusive_parts_summing_to_one_hundred():
    """Les effectifs et proportions restent visibles, sans cumul entre taux différents."""
    data = pd.DataFrame({"outcome": list(OUTCOME_LABELS.values()), "per_100": [72, 18, 10], "count": [720, 180, 100]})
    fig = outcomes_bar(data)
    assert len(fig.data) == 3
    assert fig.layout.barmode == "stack"
    assert sum(trace.x[0] for trace in fig.data) == 100
    assert fig.data[0].customdata[0][0] == 720
    assert list(fig.layout.xaxis.range) == [0, 100]


@pytest.mark.parametrize("category", ["period", "direction"])
def test_comparisons_group_rates_and_show_exposure(category):
    """La comparaison affiche les populations de référence sans additionner les trois taux."""
    data = pd.DataFrame({category: ["A", "B"], "scheduled": [100, 200], "late_rate": [0.2, 0.1], "cancellation_rate": [0.1, 0.05], "disruption_rate": [0.28, 0.145]})
    fig = comparison_bars(data, category)
    assert fig.layout.barmode == "group"
    assert fig.layout.yaxis.tickformat == ".0%"
    assert len(fig.data) == 2
    assert fig.data[0].y.tolist() == pytest.approx([0.2, 0.1, 0.28])
    assert (fig.data[1].customdata[:, 0] == 200).all()


def test_unknown_cause_is_grey_and_published_values_are_preserved():
    """La largeur et les étiquettes représentent les parts fournies, pas une redistribution."""
    data = pd.Series({"cause_infra": 40.0, "cause_unallocated": 60.0})
    fig = causes_bar(data)
    grey = next(trace for trace in fig.data if trace.name == "Part non ventilée dans les données")
    assert grey.marker.color == "#9CA3AF"
    assert grey.x[0] == 60.0
    assert list(fig.layout.xaxis.range) == [0, 100]
    legacy = causes_pie(data)
    assert legacy.data[0].values.tolist() == [40.0, 60.0]
    assert "value" in legacy.data[0].texttemplate
