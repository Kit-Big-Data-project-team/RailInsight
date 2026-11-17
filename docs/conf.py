"""Configuration Sphinx pour la documentation de RailInsight."""

import os
import sys


# Rendre le package importable pour l'autodoc.
sys.path.insert(0, os.path.abspath("../src"))

project = "RailInsight"
author = "Équipe Kit Big Data"
language = "fr"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # docstrings style Google (Args/Returns)
    "sphinx.ext.viewcode",
]

autodoc_mock_imports = [
    "requests",
    "sqlalchemy",
    "streamlit",
    "dotenv",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "sphinx_rtd_theme"