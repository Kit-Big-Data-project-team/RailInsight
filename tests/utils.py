import os
from unittest.mock import MagicMock

import requests
from dotenv import load_dotenv

from railinsight.data.etl import COLUMNS

load_dotenv()

API_URL = os.getenv("URl_SNCF_DATASET")


def make_record(**overrides) -> dict:
    record = {col: 1 for col in COLUMNS}
    record.update(
        date="2018-01",
        service="National",
        gare_depart="LE MANS",
        gare_arrivee="PARIS MONTPARNASSE",
        commentaire_annulation=None,
    )
    record.update(overrides)
    return record


def make_response(json_data=None, *, http_error=None, json_error=None, status=200):
    # spec : le mock refuse les attributs qui n'existent pas sur une vraie Response
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    if http_error:
        resp.raise_for_status.side_effect = http_error
    if json_error:
        resp.json.side_effect = json_error
    else:
        resp.json.return_value = json_data
    return resp
