FROM python:3.12-slim

WORKDIR /app

# Gestionnaire de paquets uv
RUN pip install --no-cache-dir uv

# Dépendances d'abord (meilleure mise en cache des couches)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Code applicatif
COPY src ./src
COPY views ./views
COPY streamlit_app.py ./
COPY .streamlit ./.streamlit
COPY docker/entrypoint.sh ./docker/entrypoint.sh
RUN chmod +x ./docker/entrypoint.sh

EXPOSE 8501

ENTRYPOINT ["./docker/entrypoint.sh"]
