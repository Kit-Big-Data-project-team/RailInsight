# Déploiement de RailInsight

Deux options : **Docker** (tout en local / auto-hébergé, le plus simple pour démontrer) ou **cloud** (Supabase + Streamlit Community Cloud).

## 0. Option Docker (recommandée pour une démo locale)

Le dépôt fournit un stack complet : Postgres + l'application Streamlit, avec initialisation de la base et chargement des données **automatiques** au démarrage.

1. Copier `.env.example` en `.env` et renseigner les variables (`DB_USERNAME`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`, `URl_SNCF_DATASET`). `DB_HOST` est géré par Compose.
2. Lancer :
   ```
   docker compose up --build
   ```
3. Ouvrir l'application sur **http://localhost:8501**.

Au démarrage, le conteneur `app` attend que la base soit prête (healthcheck), crée les tables, charge les données SNCF, puis sert l'application.

---

## Déploiement cloud

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
