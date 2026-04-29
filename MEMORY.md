# MEMORY.md — VideoGrab

## Последняя сессия: 2026-04-28

### Сделано
- ✅ Доказана концепция: yt-dlp + cookies скачивает видео с GetCourse
- ✅ Chrome Extension MV3 v1.0.0 — перехват HLS, popup с прогресс-баром
- ✅ Решена проблема lockdown-библиотеки GetCourse (два world: MAIN + ISOLATED)
- ✅ webRequest как основной метод перехвата (надёжнее fetch/XHR)
- ✅ Дедупликация по хэшу видео, выбор качества 360–1080p
- ✅ Поддержка YouTube, VK, Instagram (по URL страницы → yt-dlp)
- ✅ Backend v1 (личный): FastAPI + yt-dlp + ffmpeg, X-API-Key auth
- ✅ Backend v2 (мультипользовательский):
  - PostgreSQL + SQLAlchemy async (User, Download models)
  - Celery + Redis (фоновые задачи, прогресс в БД)
  - JWT auth (register/login/me)
  - Email верификация через Resend API
  - Лимиты Free: 3 скачивания/день, макс 720p
  - Заготовка Stripe (billing/router.py, не подключена)
- ✅ Options page: форма логин/регистрация, профиль с usage bar
- ✅ Popup: JWT вместо API ключа, обработка 402/401/403

### Проблемы / Баги
- [ ] `chrome.downloads.download` с кастомным `Authorization` заголовком — нужно тестировать, MV3 может не поддерживать
- [ ] Instagram нестабилен — Meta меняет защиту
- [ ] VK не тестировался на боевых данных
- [ ] `interceptor.js` остался в проекте но не используется (lockdown блокирует)
- [ ] `backend/` (v1) и `backend-v2/` оба в репозитории — нужно удалить v1 перед продакшном
- [ ] Нет GitHub Actions для автодеплоя
- [ ] Нет Alembic миграций — таблицы создаются через `create_all` при старте

### Принятые решения
- **Celery вместо asyncio задач** — фоновые загрузки в отдельном процессе, API не блокируется, можно масштабировать
- **Resend вместо SMTP** — проще настройка, 3000 писем/мес бесплатно, не нужен свой почтовый сервер
- **JWT в chrome.storage.local** — изолировано от страниц, безопаснее localStorage
- **Без Stripe пока** — заготовка есть, подключим когда будет аудитория

## Следующая сессия

### Приоритет 1 — Деплой на VPS
- [ ] Создать репозиторий `PVMaksim/videograb` на GitHub
- [ ] Настроить VPS: Docker, docker-compose, Nginx, certbot
- [ ] Задеплоить backend-v2 на VPS
- [ ] Получить SSL сертификат для API домена
- [ ] Протестировать полный флоу: расширение → бэкенд → mp4

### Приоритет 2 — Доработки после деплоя
- [ ] Заменить `create_all` на Alembic миграции
- [ ] Добавить GitHub Actions для автодеплоя при пуше в main
- [ ] Протестировать `chrome.downloads` с Authorization заголовком — если не работает, переделать на временный download token
- [ ] Удалить backend-v1, interceptor.js из продакшн ветки
- [ ] Добавить Sentry для отслеживания ошибок

### Приоритет 3 — Рост
- [ ] Лендинг / сайт для регистрации
- [ ] Подключить Stripe (billing/router.py уже есть)
- [ ] Личный кабинет (история скачиваний)
- [ ] Публикация расширения в Chrome Web Store

## Известный технический долг
- `create_all` при старте вместо Alembic — не безопасно для продакшн изменений схемы
- `TASKS` dict в backend-v1 — in-memory, не переживает рестарт (устарело, v2 использует БД)
- `interceptor.js` — мёртвый код, lockdown GetCourse блокирует его работу
- `billing/router.py` — не подключён к `main.py`, заготовка
- Нет rate limiting на API эндпоинтах (только бизнес-лимиты на скачивания)
- Нет тестов (unit / integration)
