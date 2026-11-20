"""Tests du point d'entrée principal RailInsight."""

from unittest.mock import patch

import pytest

import railinsight.main as main_module


def test_main_runs_init_then_pipeline():
    with (
        patch.object(main_module, "setup_logging"),
        patch.object(main_module, "init_db") as init,
        patch.object(main_module, "pipeline") as pipe,
    ):
        main_module.main()

    init.assert_called_once()
    pipe.assert_called_once_with(None)


def test_main_propagates_errors():
    with (
        patch.object(main_module, "setup_logging"),
        patch.object(main_module, "init_db", side_effect=RuntimeError("db down")),
    ):
        with pytest.raises(RuntimeError):
            main_module.main()
