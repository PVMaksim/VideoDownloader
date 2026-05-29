FROM python:3.12-slim

WORKDIR /app

# Минимальные системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Копируем зависимости
COPY pyproject.toml ./
COPY requirements.txt ./
RUN pip install uv && pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY alembic.ini ./alembic.ini
COPY alembic/ alembic/
COPY src/ src/
COPY tests/ tests/
COPY pytest.ini ruff.toml mypy.ini ./

# Директория для файлов
RUN mkdir -p /app/downloads && chmod 755 /app/downloads

ENV PYTHONPATH=/app/src \
    DOWNLOAD_DIR=/app/downloads \
    DATABASE_URL=sqlite+aiosqlite:///./videograb.db \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
