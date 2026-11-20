Installation et démarrage
=========================

Prérequis
---------

- Python 3.11 ou plus récent.
- `uv <https://docs.astral.sh/uv/>`_ pour la gestion des dépendances.
- Une base PostgreSQL accessible, renseignée via les variables ``DB_USERNAME``,
  ``DB_PASSWORD``, ``DB_HOST``, ``DB_PORT`` et ``DB_NAME`` (voir ``.env.example``).

Installation avec uv
--------------------

.. code-block:: bash

   uv sync
   uv run streamlit run streamlit_app.py

Le tableau de bord est alors accessible sur http://localhost:8501.

Pipeline de données (ETL)
-------------------------

.. code-block:: bash

   uv run python -m railinsight.main

Cette commande initialise le schéma si nécessaire, puis charge les données SNCF
par UPSERT idempotent (réexécuter la commande ne crée pas de doublon).

Avec Docker
-----------

.. code-block:: bash

   docker compose up --build

Déploiement
-----------

Le déploiement sur Streamlit Community Cloud est décrit dans ``docs/DEPLOYMENT.md``.
Les dépendances d'exécution sont figées dans ``requirements.txt`` et ``uv.lock``.
