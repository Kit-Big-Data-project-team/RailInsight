"""
Description :
Configure le système de journalisation pour l'application RailInsight.
"""

import logging
from pathlib import Path

# Marqueur posé sur nos handlers pour les reconnaître et rester idempotent, même si
# un autre composant (Streamlit, pytest) a déjà installé ses propres handlers racine.
_MARKER = "_railinsight_handler"


def setup_logging(log_dir: str = "logs") -> None:
    """Configure deux fichiers : tout (DEBUG+) et erreurs seules (ERROR+).

    Idempotent : réappelée (Streamlit ré-exécute le script à chaque interaction), la
    fonction n'ajoute pas de doublons. La présence de handlers *étrangers* sur le
    logger racine n'empêche plus la création de nos fichiers : on ne regarde que nos
    propres handlers, repérés par un marqueur.
    """
    root = logging.getLogger()
    if any(getattr(handler, _MARKER, False) for handler in root.handlers):
        return

    Path(log_dir).mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Le niveau du logger racine filtre en amont : il doit laisser passer DEBUG pour
    # que debug.log reçoive tout, sans abaisser un seuil déjà plus bas s'il en existe un.
    if root.level == logging.NOTSET or root.level > logging.DEBUG:
        root.setLevel(logging.DEBUG)
    for name, level in (("debug.log", logging.DEBUG), ("errors.log", logging.ERROR)):
        handler = logging.FileHandler(Path(log_dir) / name, encoding="utf-8")
        handler.setLevel(level)
        handler.setFormatter(fmt)
        setattr(handler, _MARKER, True)
        root.addHandler(handler)
