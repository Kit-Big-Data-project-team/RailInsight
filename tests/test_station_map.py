"""Tests du référentiel de coordonnées des gares."""

from railinsight.viz.station_map import get_station_coordinates


def test_known_station_is_resolved_case_insensitively():
    assert get_station_coordinates("paris lyon  ") == (48.8449, 2.3735)


def test_unknown_station_returns_none():
    assert get_station_coordinates("GARE FICTIVE") is None
