"""Description :
Le point d'entrée de l'application Streamlit : navigation et configuration générale.
"""

import streamlit as st

from railinsight.logging_config import setup_logging

st.set_page_config(page_title="RailInsight", layout="wide")


@st.cache_resource
def _init() -> bool:
    setup_logging()  # exécuté une seule fois par processus
    return True


_init()

pages = [st.Page("views/overview.py", title="Vue d'ensemble", default=True)]
st.navigation(pages).run()
