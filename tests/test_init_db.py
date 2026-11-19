"""Tests de l'initialisation de la base."""

from unittest.mock import MagicMock, patch

import pytest

from railinsight.database import init_db as init_db_module


def test_init_db_propagates_failure():
    """Un échec de création du schéma doit être relancé, pas avalé (RI-000B).

    Une base inaccessible ou un schéma incompatible ne doit jamais passer pour un
    succès : l'ETL et l'entrypoint doivent pouvoir échouer explicitement.
    """
    engine = MagicMock()
    with (
        patch.object(init_db_module, "make_engine", return_value=engine),
        patch.object(init_db_module.db_table.metadata, "create_all", side_effect=OSError("DB down")),
    ):
        with pytest.raises(OSError):
            init_db_module.init_db()

    # Le moteur est toujours libéré, même en cas d'échec.
    engine.dispose.assert_called_once()
