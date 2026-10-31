from datetime import date
from unittest.mock import patch

import pytest
import requests
from utils import API_URL, make_response

from railinsight.data.etl import fetch_data


def test_fetch_data_returns_list():
    data = fetch_data(API_URL, None)

    assert data is not None
    assert isinstance(data, list)

    if data:
        assert isinstance(data[0], dict)


def test_fetch_data_with_date_filter():
    data = fetch_data(API_URL, date(2026, 9, 1))

    assert data is not None
    assert isinstance(data, list)


def test_fetch_data_empty_result_is_valid():
    data = fetch_data(API_URL, date(5000, 1, 1))

    assert data is not None
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.parametrize(
    "error",
    [requests.exceptions.Timeout(), requests.exceptions.ConnectionError()],
)
def test_returns_none_on_network_errors(error):
    with patch("railinsight.data.etl.requests.get", side_effect=error):
        assert fetch_data(API_URL, since=None) is None


def test_returns_none_on_http_error():
    resp = make_response(http_error=requests.exceptions.HTTPError("500 Server Error"))
    with patch("railinsight.data.etl.requests.get", return_value=resp):
        assert fetch_data(API_URL, since=None) is None


def test_returns_none_on_invalid_json():
    resp = make_response(json_error=ValueError("not json"))
    with patch("railinsight.data.etl.requests.get", return_value=resp):
        assert fetch_data(API_URL, since=None) is None
