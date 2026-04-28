FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dépendances système pour psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY pyproject.toml .
RUN pip install -e ".[prod]"

# Code source
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .
COPY data/ data/

EXPOSE 8000

# Migrations puis démarrage
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 2"]
