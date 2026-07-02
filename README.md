# VideoGrab Backend (VideoDownloader)

Многопользовательский API для скачивания видео с поддержкой подписок и ограничений качества. Поддерживает регистрацию, верификацию по email, очередь задач на скачивание и интеграцию со Stripe.

## Быстрый старт (локально)

```bash
# 1. Копируем окружение
cp .env.example .env

# 2. Запускаем через Docker
docker-compose up --build

# Или локально (нужен Python 3.12)
pip install uv && uv pip install -r requirements.txt
uvicorn src.main:app --reload

Деплой на VPS
Автоматически
Через GitHub Actions при пуше в main.
Вручную

ssh deploy@193.242.109.48 "cd /home/deploy/VideoDownloader/backend && git pull origin main && docker-compose up --build -d"

Доступ к API
URL: http://193.242.109.48:8301
Health check: http://193.242.109.48:8301/api/health
Swagger UI (только при DEBUG=true): http://193.242.109.48:8301/docs
Переменные окружения
Обязательные:
DATABASE_URL — строка подключения к PostgreSQL (postgresql+asyncpg://user:pass@db:5432/videodownloader)
SECRET_KEY — секретный ключ для JWT токенов
ALGORITHM — алгоритм шифрования (по умолчанию HS256)
Опциональные:
DEBUG — режим отладки (true/false, по умолчанию false)
SKIP_EMAIL_VERIFICATION — пропустить верификацию email (true для локальной разработки)
SKIP_AUTH — пропустить аутентификацию (true только для тестов!)
APP_URL — публичный URL приложения (по умолчанию http://193.242.109.48:8301)
Email (Resend):
RESEND_API_KEY — API ключ от Resend
EMAIL_FROM — адрес отправителя (например, VideoGrab <noreply@neoxis.store>)
SMTP (альтернатива Resend):
SMTP_HOST — SMTP сервер (например, smtp.mail.ru)
SMTP_PORT — порт SMTP (обычно 587)
SMTP_USER — логин SMTP
SMTP_PASS — пароль SMTP
Ограничения (Free tier):
FREE_DAILY_LIMIT — лимит скачиваний в день (по умолчанию 3)
FREE_MAX_HEIGHT — максимальное качество видео (по умолчанию 720)
Файлы:
DOWNLOAD_DIR — папка для скачанных файлов (по умолчанию /tmp/videodownloader)
FILE_TTL_HOURS — время хранения файлов в часах (по умолчанию 2)
Структура проекта

backend/
├── src/
│   ├── main.py              # FastAPI приложение
│   ├── config.py            # Настройки из .env
│   ├── auth/
│   │   ├── router.py        # Эндпоинты регистрации/логина
│   │   ├── service.py       # Логика аутентификации
│   │   └── email.py         # Отправка писем
│   ├── downloads/
│   │   ├── router.py        # Эндпоинты скачивания
│   │   └── service.py       # Логика скачивания
│   ├── billing/
│   │   └── router.py        # Эндпоинты Stripe
│   ├── db/
│   │   ├── database.py      # Подключение к БД
│   │   └── models.py        # SQLAlchemy модели
│   └── worker/
│       └── tasks.py         # Celery задачи
├── tests/                   # Интеграционные тесты
├── alembic/                 # Миграции БД
├── .github/workflows/       # CI/CD пайплайны
├── Dockerfile               # Образ для API
├── Dockerfile.worker        # Образ для Celery worker (с ffmpeg)
├── docker-compose.yml       # Docker Compose конфигурация
└── requirements.txt         # Python зависимости

API Endpoints
Аутентификация (/api/auth)
POST /api/auth/register — регистрация нового пользователя
POST /api/auth/login — получение JWT токена
POST /api/auth/forgot-password — запрос сброса пароля
POST /api/auth/reset-password — сброс пароля по токену
GET /api/auth/me — получение данных текущего пользователя
Скачивание (/api/downloads)
POST /api/downloads — создать задачу на скачивание
GET /api/downloads/status/{task_id} — статус задачи
GET /api/downloads/file/{task_id} — скачать файл
GET /api/downloads/history — история скачиваний
GET /api/downloads/stats — статистика использования
Подписки (/api/billing)
POST /api/billing/subscribe — оформить подписку
GET /api/billing/subscription — информация о подписке
POST /api/billing/cancel — отменить подписку
POST /api/billing/webhook — webhook от Stripe
Системные
GET /api/health — проверка работоспособности
Тестирование

# Запустить все тесты
pytest tests/ -v

# Запустить конкретный тест
pytest tests/test_auth.py -v

# С покрытием
pytest tests/ --cov=src --cov-report=html

Проверка работоспособности
1. Health check
curl http://localhost:8301/api/health

2. Регистрация

curl -X POST http://localhost:8301/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}'

  3. Логин

  curl -X POST http://localhost:8301/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}'

  4. Проверка токена

  TOKEN="<токен_из_предыдущего_шага>"
curl -X GET http://localhost:8301/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

  Логи

  # Логи API
docker-compose logs --tail=50 api

# Логи Worker
docker-compose logs --tail=50 worker

# Все логи
docker-compose logs --tail=100

База данных

# Подключиться к PostgreSQL
docker-compose exec db psql -U user -d videodownloader

# Список пользователей
docker-compose exec db psql -U user -d videodownloader -c "SELECT id, email, is_verified, plan FROM users;"

# Структура таблицы users
docker-compose exec db psql -U user -d videodownloader -c "\d users"

Известные проблемы и решения
1. Ошибка insufficient permission for adding an object to repository database .git/objects
Причина: Файлы в .git/ принадлежат разным пользователям.
Решение:

sudo chown -R deploy:deploy /home/deploy/VideoDownloader/.git
chmod -R g+rwX /home/deploy/VideoDownloader/.git
git config core.sharedRepository true

2. Ошибка The neoxis.store domain is not verified
Причина: Домен не верифицирован в Resend.
Решение:
Вариант 1: Верифицировать домен на https://resend.com/domains
Вариант 2: Использовать onboarding@resend.dev в EMAIL_FROM
Вариант 3: Установить SKIP_EMAIL_VERIFICATION=true для тестов
3. Пароли хранятся как dummy_hash_
Причина: В src/auth/service.py используется заглушка вместо bcrypt.
Решение: Заменить на нормальный bcrypt:

import bcrypt

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]  # bcrypt ограничение 72 байта
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

Мониторинг

# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Очистка старых файлов
docker system prune -f

Обновление

cd /home/deploy/VideoDownloader/backend
git pull origin main
docker-compose up --build -d

Контакты
Email для тестов: m008ba@mail.ru
VPS: 193.242.109.48
Порт API: 8301