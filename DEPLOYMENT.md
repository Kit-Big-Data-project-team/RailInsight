# Déploiement de RailInsight

Architecture cible : base **PostgreSQL hébergée sur Supabase** + application **Streamlit Community Cloud**.

## 1. Base de données (Supabase)

1. Créer un projet sur [supabase.com](https://supabase.com) → récupérer les identifiants PostgreSQL (host, port, user, password, db) dans *Project Settings → Database*.
2. Créer les tables : lancer en local, avec le `.env` pointant vers Supabase :
   ```
   uv run python -m railinsight.database.init_db
   ```
3. Charger les données (ETL) :
   ```
   uv run python src/railinsight/main.py
   ```

## 2. Application (Streamlit Community Cloud)

1. Sur [share.streamlit.io](https://share.streamlit.io), connecter le repo GitHub.
2. **Main file path** : `streamlit_app.py`.
3. Dans **Settings → Secrets**, coller le contenu de `.streamlit/secrets.toml.example` en remplaçant par les vraies valeurs Supabase.
4. Déployer. L'app lit les secrets, les expose comme variables d'environnement (voir `streamlit_app.py`), et la couche base de données s'y connecte.

## Notes

- Le vrai fichier `.streamlit/secrets.toml` ne doit **jamais** être commité (déjà dans `.gitignore`).
- Les dépendances sont résolues automatiquement depuis `pyproject.toml` / `uv.lock`.
- En local, les mêmes variables viennent du fichier `.env` (voir `.env.example`).
