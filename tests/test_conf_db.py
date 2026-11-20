"""Tests de la configuration du moteur de base de données."""

import os
from unittest.mock import patch

from railinsight.database.conf_db import make_engine


def test_make_engine_builds_a_postgres_engine_from_env():
    env = {"DB_USERNAME": "user", "DB_PASSWORD": "pwd", "DB_HOST": "db.example", "DB_PORT": "5432", "DB_NAME": "rail"}
    with patch.dict(os.environ, env, clear=False):
        engine = make_engine()

    try:
        assert engine.dialect.name == "postgresql"
        assert engine.url.username == "user"
        assert engine.url.host == "db.example"
        assert engine.url.database == "rail"
    finally:
        engine.dispose()
