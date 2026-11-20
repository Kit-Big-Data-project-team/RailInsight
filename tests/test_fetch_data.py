"""Tests de récupération des données de l'API SNCF.

Les appels réseau sont simulés : la suite ne dépend plus du service SNCF réel
ni de la variable d'environnement de l'URL du jeu de données.
"""

from datetime import date
from unittest.mock import patch

import pytest
import requests
from utils import API_URL, make_record, make_response

from railinsight.data.etl import fetch_data

URL = API_URL or "https://example.test/dataset"


def test_fetch_data_returns_list():
    resp = make_response(json_data=[make_record()])
    with patch("railinsight.data.etl.requests.get", return_value=resp):
        data = fetch_data(URL, None)

    assert isinstance(data, list)
    assert isinstance(data[0], dict)


def test_fetch_data_passes_inclusive_date_filter():
    resp = make_response(json_data=[make_record()])
    with patch("railinsight.data.etl.requests.get", return_value=resp) as mock_get:
        data = fetch_data(URL, date(2026, 9, 1))

    assert isinstance(data, list)
    params = mock_get.call_args.kwargs["params"]
    assert params["where"] == 'date >= "2026-09-01"'


def test_fetch_data_unwraps_opendatasoft_results():
    """Une réponse paginée OpenDataSoft expose les lignes sous la clé ``results``."""
    resp = make_response(json_data={"results": [make_record(), make_record()]})
    with patch("railinsight.data.etl.requests.get", return_value=resp):
        data = fetch_data(URL, None)

    assert isinstance(data, list)
    assert len(data) == 2


def test_fetch_data_empty_result_is_valid():
    resp = make_response(json_data=[])
    with patch("railinsight.data.etl.requests.get", return_value=resp):
        data = fetch_data(URL, date(5000, 1, 1))

    assert data == []


@pytest.mark.parametrize(
    "error",
    [requests.exceptions.Timeout(), requests.exceptions.ConnectionError()],
)
def test_returns_none_on_network_errors(error):
    with patch("railinsight.data.etl.requests.get", side_effect=error):
        assert fetch_data(URL, since=None) is None


def test_returns_none_on_http_error():
    resp = make_response(http_error=requests.exceptions.HTTPError("500 Server Error"))
    with patch("railinsight.data.etl.requests.get", return_value=resp):
        assert fetch_data(URL, since=None) is None


def test_returns_none_on_invalid_json():
    resp = make_response(json_error=ValueError("not json"))
    with patch("railinsight.data.etl.requests.get", return_value=resp):
        assert fetch_data(URL, since=None) is None
