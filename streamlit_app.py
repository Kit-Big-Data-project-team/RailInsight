"""Description :
Le point d'entrée de l'application Streamlit : navigation et configuration générale.
"""

import os
import sys

# Rendre le package importable même sans installation (ex. Streamlit Cloud, qui exécute
# le dépôt tel quel sans `uv sync`).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import streamlit as st  # noqa: E402

from railinsight.logging_config import setup_logging  # noqa: E402

st.set_page_config(page_title="RailInsight", layout="wide")

# Variables de connexion attendues par la couche base de données.
_DB_KEYS = ("DB_USERNAME", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")


def _bridge_secrets_to_env() -> None:
    """Sur Streamlit Cloud, recopie les secrets de connexion en variables d'environnement.

    La configuration de la base lit `os.getenv(...)` ; en local ces valeurs viennent du
    `.env`, en ligne du fichier secrets de Streamlit. Ce pont évite de dupliquer la logique.
    """
    try:
        for key in _DB_KEYS:
            if key in st.secrets and not os.getenv(key):
                os.environ[key] = str(st.secrets[key])
    except Exception:
        # Pas de secrets configurés (ex. exécution locale) : on garde le .env.
        pass


@st.cache_resource
def _init() -> bool:
    setup_logging()  # exécuté une seule fois par processus
    _bridge_secrets_to_env()
    return True


_init()

pages = [
    st.Page("views/overview.py", title="Vue d'ensemble", default=True),
    st.Page("views/history.py", title="Historique & évolution"),
    st.Page("views/reliability.py", title="Fiabilité des liaisons"),
    st.Page("views/trip.py", title="Mon trajet"),
    st.Page("views/prediction.py", title="Prédiction des retards"),
]
st.navigation(pages).run()
