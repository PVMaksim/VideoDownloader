# VideoGrab Backend

[![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

Multi-user API для скачивания видео с ограничениями по качеству и квотам. Поддерживает YouTube, VK, GetCourse и другие платформы через `yt-dlp`. Включает JWT-аутентификацию, email-верификацию через Resend, Stripe-биллинг и очередь задач на Celery.

---

## 🚀 Быстрый старт

### Локально (без Docker)

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd backend

# 2. Создать виртуальное окружение
python -m venv .venv && source .venv/bin/activate

# 3. Установить зависимости
pip install uv && uv pip install -r requirements.txt

# 4. Настроить окружение
cp .env.example .env
# Отредактируйте .env: DATABASE_URL, RESEND_API_KEY, SECRET_KEY

# 5. Запустить сервер
uvicorn src.main:app --reload

# 6. Проверить здоровье
curl http://localhost:8000/api/health

Через Docker Compose (рекомендуется)

# 1. Настроить окружение
cp .env.example .env
# Отредактируйте необходимые переменные

# 2. Запустить все сервисы
docker-compose up --build -d

# 3. Проверить логи
docker-compose logs -f api

# 4. Проверить здоровье (порт 8201 → 8000 внутри контейнера)
curl http://localhost:8201/api/health
⚠️ Важно: При запуске через Docker Compose сервер доступен на порту 8201, а не 8000.

Документация API
После запуска откройте в браузере:

Swagger UI
http://localhost:8201/docs
🔹 ReDoc
http://localhost:8201/redoc
🔹 OpenAPI JSON
http://localhost:8201/openapi.json

Основные эндпоинты

Метод	Путь	Описание	Доступ
`POST`	`/api/auth/register`	Регистрация пользователя	Публичный
`POST`	`/api/auth/login`	Получение JWT-токена	Публичный
`POST`	`/api/auth/forgot-password`	Запрос сброса пароля	Публичный
`GET`	`/api/auth/me`	Профиль текущего пользователя	🔐 Требуется токен
`POST`	`/api/downloads/start`	Создать задачу скачивания	🔐 Требуется токен
`GET`	`/api/downloads/status/{id}`	Статус задачи	🔐 Требуется токен
`GET`	`/api/downloads/file/{id}`	Скачать готовый файл	🔐 Требуется токен
`GET`	`/api/downloads/history`	История скачиваний	🔐 Требуется токен
`GET`	`/api/health`	Проверка здоровья сервиса	Публичный

Использование защищённых эндпоинтов
После успешного логина вы получите JWT-токен:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

Используйте его в заголовке Authorization:

curl -X GET http://localhost:8201/api/downloads/history \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  В Swagger UI: нажмите кнопку "Authorize" в правом верхнем углу → вставьте токен → "Authorize".

  Переменные окружения
Все настройки — в файле .env. Скопируйте шаблон: cp .env.example .env

Переменная	Описание	Пример
`DATABASE_URL`	Подключение к PostgreSQL	`postgresql+asyncpg://user:pass@db:5432/videodownloader`
`SECRET_KEY`	Секрет для подписи JWT	`openssl rand -hex 32`
`RESEND_API_KEY`	API-ключ Resend для отправки писем	`re_xxx...`

Переменная	Описание	Пример / Значение по умолчанию		
`APP_URL`	Публичный адрес приложения (для ссылок в письмах)	`http://localhost:8201`		
`SKIP_EMAIL_VERIFICATION`	Пропускать верификацию email (только dev!)	`false`		
`SKIP_AUTH`	Отключить проверку аутентификации (только dev!)	`false`		
`EMAIL_FROM`	Адрес отправителя писем	`"VideoGrab <onboarding@resend.dev>"`		
`ACCESS_TOKEN_EXPIRE_MINUTES`	Время жизни JWT-токена	`30`		
`DAILY_LIMIT`	Лимит скачиваний в день для бесплатного тарифа	`3`		
`FREE_MAX_HEIGHT`	Максимальное качество для бесплатного тарифа	`720`		
`STRIPE_SECRET_KEY`	Секретный ключ Stripe (для биллинга)	`sk_test_...`		
`REDIS_URL`	Подключение к Redis (для очередей)	`redis://redis:6379/0`		

Настройка email-верификации
Для отправки писем через Resend:
Зарегистрируйтесь на resend.com
Получите API-ключ в дашборде
Добавьте в .env:

RESEND_API_KEY=re_xxx...
EMAIL_FROM="VideoGrab <onboarding@resend.dev>"

Важно: Без верификации домена Resend разрешает отправку только на ваш зарегистрированный email.
Для тестов на любые адреса:
Верифицируйте домен в Resend Domains, ИЛИ
Установите SKIP_EMAIL_VERIFICATION=true в .env (только для разработки!)

Миграции базы данных (Alembic)

# Создать новую миграцию после изменения моделей
alembic revision --autogenerate -m "add_user_verification_fields"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Проверить текущую ревизию
alembic current

При первом запуске приложения миграции применяются автоматически (если включено в main.py).

Сервис	Порт	Описание		
`api`	`8201:8000`	FastAPI сервер (основное приложение)		
`db`	`5432` (внутри сети)	PostgreSQL 16 — хранение данных		
`redis`	`6379` (внутри сети)	Redis 7 — кеш и брокер очередей		
`worker`	—	Celery worker — фоновые задачи (скачивание, отправка писем)		

# Полезные команды

# Просмотр логов конкретного сервиса
docker-compose logs -f api
docker-compose logs -f worker

# Перезапустить один сервис
docker-compose restart api

# Остановить и удалить контейнеры (данные БД сохранятся в volume)
docker-compose down

# Полная очистка (включая volumes — удалит данные БД!)
docker-compose down -v

 Тестирование

 # Запустить все тесты
pytest tests/ -v

# Запустить конкретный тест
pytest tests/test_integration.py::test_download_flow -v

# Запустить с покрытием кода
pytest --cov=src tests/ --cov-report=html

# Открыть отчёт о покрытии
open htmlcov/index.html
Требования к тестам:
Все новые функции должны иметь юнит-тесты
Интеграционные тесты используют тестовую БД (SQLite в памяти)
Моки для внешних сервисов: Resend, Stripe, yt-dlp

📁 Структура проекта

backend/
├── src/
│   ├── main.py              # Точка входа: FastAPI app, middleware, routers
│   ├── config.py            # Pydantic Settings, загрузка из .env
│   ├── db/
│   │   ├── database.py      # SQLAlchemy session, engine
│   │   └── models.py        # ORM-модели: User, DownloadTask, etc.
│   ├── auth/
│   │   ├── router.py        # Эндпоинты: register, login, me
│   │   ├── service.py       # Логика: hash_password, JWT, get_current_user
│   │   └── email.py         # Отправка писем через Resend
│   ├── downloads/
│   │   ├── router.py        # Эндпоинты: start, status, file, history
│   │   ├── service.py       # Логика: yt-dlp wrapper, quota checks
│   │   └── schemas.py       # Pydantic схемы запросов/ответов
│   ├── billing/
│   │   └── ...              # Stripe integration (webhooks, subscriptions)
│   └── worker.py            # Celery tasks: send_email, process_download
├── alembic/                 # Миграции БД
│   ├── versions/            # Автоматически сгенерированные миграции
│   └── env.py               # Конфигурация Alembic
├── tests/
│   ├── conftest.py          # Fixtures: test_db, mock_resend, client
│   ├── test_auth.py         # Тесты аутентификации
│   ├── test_downloads.py    # Тесты скачивания
│   └── test_integration.py  # E2E тесты
├── docker-compose.yml       # Оркестрация сервисов
├── Dockerfile               # Сборка Python-образа
├── requirements.txt         # Зависимости (pip)
├── pyproject.toml           # Конфигурация проекта (uv, ruff, mypy)
├── pytest.ini               # Настройки pytest
├── ruff.toml                # Линтинг (аналог flake8 + isort)
├── mypy.ini                 # Статическая проверка типов
├── .env.example             # Шаблон переменных окружения
├── .gitignore               # Исключения для Git
├── CLAUDE.md                # Технический контекст для AI-ассистентов
├── MEMORY.md                # Дневник разработки (сессии, решения, долги)
└── README.md                # Этот файл

❓ Частые проблемы (Troubleshooting)

Проблема	Возможная причина	Решение		
`ValueError: password cannot be longer than 72 bytes`	Ограничение bcrypt через passlib	Обновите `passlib[bcrypt]` и добавьте обрезку пароля: `password.encode()[:72]`		
`ResendError: You can only send testing emails...`	Неверифицированный домен в Resend	Отправляйте на свой зарегистрированный email ИЛИ верифицируйте домен в [Resend Domains](https://resend.com/domains)		
Порт 8000/8201 занят	Другой процесс использует порт	Проверьте: `lsof -i :8201` и освободите порт, или измените в `docker-compose.yml`		
`ModuleNotFoundError: auth.service`	Кэш `.pyc` или неверный PYTHONPATH	Очистите кэш: `find . -name "__pycache__" -exec rm -rf {} +` и пересоберите образ		
Письма не приходят	Неправильный `EMAIL_FROM` или спам-фильтр	Проверьте папку "Спам", убедитесь что `EMAIL_FROM` в формате `"Name <email@domain>"`		
JWT не принимается	Истёк срок токена или неверный секрет	Проверьте `SECRET_KEY` в `.env`, срок жизни токена в `ACCESS_TOKEN_EXPIRE_MINUTES`		
        
     🚢 Деплой на VPS (Ubuntu 22.04)

        # 1. Подключиться к серверу
ssh user@your-vps-ip

# 2. Установить Docker и Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER  # затем перелогиньтесь

# 3. Клонировать проект
git clone <repo-url> /opt/videograb
cd /opt/videograb/backend

# 4. Настроить окружение
cp .env.example .env
# Отредактируйте: DATABASE_URL (на внешний хост или оставьте db), SECRET_KEY, RESEND_API_KEY

# 5. Запустить
docker-compose pull
docker-compose up -d

# 6. (Опционально) Настроить nginx + SSL через certbot
# См. пример конфига в /docs/nginx.conf.example

Автоматический деплой через GitHub Actions
При пуше в ветку main срабатывает пайплайн .github/workflows/deploy.yml, который:
Собирает Docker-образ
Пушит в GitHub Container Registry
Подключается к серверу по SSH
Обновляет контейнеры через docker-compose pull && up -d
Требуется настроить секреты репозитория:
DEPLOY_HOST — IP или домен сервера
DEPLOY_USER — пользователь SSH
DEPLOY_KEY — приватный SSH-ключ для деплоя
🤝 Вклад в проект
Создайте ветку от main: git checkout -b feature/your-feature
Внесите изменения, добавьте тесты
Прогоните линтеры: ruff check src/ && mypy src/
Убедитесь, что тесты проходят: pytest
Создайте Pull Request с описанием изменений
Требования к коду
Все функции — с docstrings на английском
Комментарии к бизнес-логике — на русском
Никаких «магических чисел» — только именованные константы из config.py
Обработка всех исключений с логированием: log.error(...)
Модульность: один файл = одна ответственность
📄 Лицензия
MIT. См. файл LICENSE для деталей.
💡 Совет разработчику:
Перед началом работы прочитайте CLAUDE.md (технический контекст для AI) и MEMORY.md (история решений и технический долг). Это ускорит погружение в проект.