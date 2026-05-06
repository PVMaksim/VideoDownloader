# VideoDownloader Backend

Multi-user API для скачивания видео с ограничениями по качеству и квотам. Поддерживает YouTube, VK, GetCourse и другие платформы. Включает аутентификацию, email-верификацию, Stripe-биллинг и очередь задач.

## Быстрый старт (локально)

```bash
# 1. Клонировать и подготовить окружение
git clone <repo>
cd backend
python -m venv .venv && source .venv/bin/activate

# 2. Установить зависимости
pip install uv && uv pip install -r pyproject.toml

# 3. Настроить переменные окружения
cp .env.example .env  # заполнить DATABASE_URL, JWT_SECRET, etc.

# 4. Запустить сервер
uvicorn src.main:app --reload

# 5. Проверить здоровье
curl http://localhost:8000/api/health

API Документация
После запуска откройте в браузере:
🔹 Swagger UI: http://localhost:8000/docs
🔹 ReDoc: http://localhost:8000/redoc
Основные эндпоинты
Метод	Путь	Описание
POST	`/api/auth/register`	Регистрация пользователя
POST	`/api/auth/login`	Получение JWT-токена
POST	`/api/download`	Создать задачу скачивания
GET	`/api/status/{id}`	Статус задачи
GET	`/api/file/{id}`	Скачать готовый файл
GET	`/api/history`	История скачиваний
GET	`/api/me`	Профиль пользователя

Переменные окружения
Все настройки — в файле .env:

# Приложение
APP_NAME=VideoGrab
DEBUG=true

# База данных
DATABASE_URL=sqlite+aiosqlite:///./videograb.db

# JWT
JWT_SECRET=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Лимиты
DAILY_LIMIT=3
FREE_MAX_HEIGHT=720

# Email (опционально)
RESEND_API_KEY=
SKIP_EMAIL_VERIFICATION=true  # для локальной разработки

# Stripe (опционально)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

backend/
├── src/
│   ├── main.py              # FastAPI app, middleware
│   ├── config.py           # Pydantic settings
│   ├── db/                 # SQLAlchemy models, database
│   ├── auth/               # Authentication endpoints
│   ├── downloads/          # Download queue & logic
│   ├── billing/            # Stripe integration
│   └── worker/             # Celery tasks (ready)
├── tests/
│   ├── conftest.py         # Fixtures, mocks
│   └── test_integration.py # E2E тесты
├── pyproject.toml          # Зависимости
├── pytest.ini              # Настройки тестов
├── ruff.toml               # Линтинг
├── mypy.ini                # Типизация
└── .env.example            # Шаблон переменных

# Запустить все тесты
pytest tests/ -v

# Запустить конкретный тест
pytest tests/test_integration.py::test_download_flow -v

# С покрытием
pytest --cov=src tests/

# 1. Собрать образ
docker build -t videograb-backend .

# 2. Запустить (пример)
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  -v ./downloads:/app/downloads \
  videograb-backend

  Лицензия
MIT
EOF