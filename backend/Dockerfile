FROM python:3.12-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY pyproject.toml ./
RUN pip install uv && uv pip install --system -r pyproject.toml

# Копируем код
COPY src/ src/
COPY tests/ tests/
COPY pytest.ini ruff.toml mypy.ini ./

# Создаём директорию для файлов
RUN mkdir -p /app/downloads && chmod 755 /app/downloads

# Переменные окружения
ENV PYTHONPATH=/app/src \
    DOWNLOAD_DIR=/app/downloads \
    DATABASE_URL=sqlite+aiosqlite:///./videograb.db \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
