# VideoGrab Backend

Бэкенд-часть сервиса VideoGrab для скачивания, обработки и управления видео. Включает REST API на FastAPI, систему аутентификации (JWT), фоновые задачи на Celery и автоматический деплой через GitHub Actions.

## Быстрый старт (локально)
```bash
cd backend
# Убедись, что файл .env заполнен (POSTGRES_PASSWORD, SECRET_KEY и т.д.)
docker compose up --build

API будет доступен по http://localhost:8010.
Деплой на VPS
Деплой выполняется автоматически при пуше в ветку main через GitHub Actions.
Для ручного запуска:
ssh deploy@<VPS_IP> "cd /opt/videograb && docker compose up -d --build"

Переменные окружения
Основные переменные задаются в backend/.env:
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB — учётные данные PostgreSQL
DATABASE_URL, DATABASE_URL_SYNC — строки подключения (asyncpg / psycopg2)
SECRET_KEY — секретный ключ для JWT
REDIS_URL — подключение к Redis
SKIP_EMAIL_VERIFICATION=true — отключает проверку email в dev-режиме
Структура проекта

backend/
├── .env               # Переменные окружения
├── docker-compose.yml # Оркестрация сервисов
├── src/
│   ├── auth/          # Аутентификация, JWT, хеширование
│   ├── db/            # Модели SQLAlchemy, Alembic
│   └── api/           # Эндпоинты FastAPI (префикс /api)
├── worker.py          # Celery-воркер
└── main.py            # Точка входа
extension/             # Браузерное расширение

Тестирование

cd backend
pytest