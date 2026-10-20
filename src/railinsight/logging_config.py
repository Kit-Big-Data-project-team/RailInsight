"""
Description :
Configure le système de journalisation pour l'application RailInsight.
"""

import logging
from pathlib import Path


def setup_logging(log_dir: str = "logs") -> None:
    """Configure deux fichiers : tout (DEBUG+) et erreurs seules (ERROR+)."""
    root = logging.getLogger()
    if root.handlers:  # évite les doublons (Streamlit ré-exécute le script)
        return
    Path(log_dir).mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root.setLevel(logging.DEBUG)
    for name, level in (("debug.log", logging.DEBUG), ("errors.log", logging.ERROR)):
        h = logging.FileHandler(Path(log_dir) / name, encoding="utf-8")
        h.setLevel(level)
        h.setFormatter(fmt)
        root.addHandler(h)
