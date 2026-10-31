import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from railinsight.database.db_table import regularite_tgv_table

SAMPLE = Path(__file__).parent / "data" / "sncf_sample.json"


@pytest.fixture
def sample_records() -> list[dict]:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


@pytest.fixture
def db_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    regularite_tgv_table.metadata.create_all(engine)
    yield engine
    engine.dispose()
