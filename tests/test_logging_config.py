"""Tests de la configuration de journalisation."""

import logging

import pytest

from railinsight.logging_config import setup_logging


@pytest.fixture
def clean_root():
    """Isole le logger racine : repart propre, puis restaure l'état initial."""
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    root.handlers.clear()
    yield root
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)
    for handler in saved_handlers:
        root.addHandler(handler)
    root.setLevel(saved_level)


def test_setup_logging_creates_both_files(clean_root, tmp_path):
    setup_logging(str(tmp_path))
    logging.getLogger("railinsight.test").info("info msg")
    logging.getLogger("railinsight.test").error("boom")
    for handler in clean_root.handlers:
        handler.flush()

    debug = (tmp_path / "debug.log").read_text(encoding="utf-8")
    errors = (tmp_path / "errors.log").read_text(encoding="utf-8")
    assert "info msg" in debug and "boom" in debug
    assert "boom" in errors and "info msg" not in errors


def test_setup_logging_is_idempotent(clean_root, tmp_path):
    setup_logging(str(tmp_path))
    count = len(clean_root.handlers)
    setup_logging(str(tmp_path))
    assert len(clean_root.handlers) == count


def test_setup_logging_runs_despite_a_preexisting_handler(clean_root, tmp_path):
    """Un handler étranger ne doit pas empêcher la création des fichiers (bug corrigé)."""
    clean_root.addHandler(logging.StreamHandler())
    setup_logging(str(tmp_path))
    logging.getLogger("railinsight.test").error("late error")
    for handler in clean_root.handlers:
        handler.flush()

    assert (tmp_path / "debug.log").exists()
    assert "late error" in (tmp_path / "errors.log").read_text(encoding="utf-8")
