FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY regularite-mensuelle-tgv-aqst.csv analyse_sncf.ipynb ./

EXPOSE 8888

CMD ["uv", "run", "--no-sync", "jupyter", "lab", "analyse_sncf.ipynb", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
