FROM python:3.12-slim

WORKDIR /app

# Gestionnaire de paquets uv
RUN pip install --no-cache-dir uv

# 1) Dépendances seules d'abord (couche mise en cache tant que le lock ne change pas)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) Code applicatif
COPY src ./src
COPY views ./views
COPY streamlit_app.py ./
COPY .streamlit ./.streamlit
COPY docker/entrypoint.sh ./docker/entrypoint.sh

# 3) Installer le projet lui-même (le package railinsight) maintenant que le code est là
RUN uv sync --frozen --no-dev && chmod +x ./docker/entrypoint.sh

# Filet de sécurité : rendre le package importable même sans installation
ENV PYTHONPATH=/app/src

EXPOSE 8501

ENTRYPOINT ["./docker/entrypoint.sh"]
