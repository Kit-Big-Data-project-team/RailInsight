#!/bin/sh
set -e

# main.py initialise la base (init_db) puis lance l'ETL (fetch + nettoyage + insertion).
# On ne bloque pas le démarrage de l'app si l'API SNCF est momentanément indisponible.
echo "Initialisation de la base et chargement des données SNCF..."
uv run --no-sync python src/railinsight/main.py || echo "ETL non effectué (API indisponible ?) — l'application démarre quand même."

echo "Démarrage de l'application Streamlit sur le port 8501..."
exec uv run --no-sync streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
