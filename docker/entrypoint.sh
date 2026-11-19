#!/bin/sh
set -e

# 1. Initialisation de la base : BLOQUANTE. Une base inaccessible ou un schéma
#    incompatible doit arrêter le conteneur (set -e), pas démarrer une app vide.
echo "Initialisation de la base de données..."
uv run --no-sync python -c "from railinsight.database.init_db import init_db; init_db()"

# 2. Chargement des données (ETL) : TOLÉRÉ. Si l'API SNCF est momentanément
#    indisponible, l'app démarre avec les données déjà présentes en base.
echo "Chargement des données SNCF..."
uv run --no-sync python src/railinsight/data/etl.py || echo "ETL non effectué (API indisponible ?) — démarrage avec les données déjà en base."

echo "Démarrage de l'application Streamlit sur le port 8501..."
exec uv run --no-sync streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
