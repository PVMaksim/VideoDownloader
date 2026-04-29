# CLAUDE.md — VideoGrab

## Стек

### Extension (Chrome MV3) — v1.0.0
- Язык: JavaScript (Vanilla, без фреймворков)
- Платформа: Chrome Extension Manifest V3
- Auth: JWT токен в `chrome.storage.local`
- Файлы: `background.js`, `content.js`, `interceptor.js`, `popup/`, `options/`

### Backend v2 (Production-ready, VPS)
- Язык: Python 3.12
- Фреймворк: FastAPI 0.115 + Uvicorn
- БД: PostgreSQL 16 (async через asyncpg + SQLAlchemy 2.0)
- Очередь: Celery 5.4 + Redis 7
- Email: Resend API (3000 писем/мес бесплатно)
- Инфраструктура: Docker, docker-compose, Nginx + Let's Encrypt

### Backend v1 (устарел, только для личного использования)
- FastAPI + yt-dlp + ffmpeg, без auth, без БД
- Оставлен в `backend/` как reference

## Архитектура

```
Chrome Extension (v1.0.0)
├── background.js      Service Worker: webRequest перехват HLS/m3u8, keepalive
├── content.js         ISOLATED world: мост window events → chrome.runtime
├── interceptor.js     MAIN world: перехват fetch/XHR (резервный метод)
├── popup/             UI: список видео, выбор качества, прогресс-бар, JWT auth
└── options/           Настройки: URL сервера, логин/регистрация, профиль

Backend v2 (мультипользовательский)
├── src/auth/          register, login, JWT, email verification (Resend)
├── src/downloads/     create task, status polling, file download, лимиты
├── src/worker/        Celery task: yt-dlp subprocess + прогресс в БД
├── src/db/            SQLAlchemy models: User, Download
├── src/billing/       Заготовка под Stripe (не активна)
└── src/main.py        FastAPI app, CORS, startup, cleanup loop
```

**Поток данных (полный цикл):**
```
1. Страница → webRequest перехватывает HLS URL (gceuproxy.com)
   ИЛИ tab.url берётся для YouTube/VK/Instagram
2. Popup: пользователь выбирает качество → "Скачать"
3. Extension: cookies из браузера + JWT → POST /api/download
4. Backend: создаёт Download в БД → Celery.delay(task_id)
5. Celery Worker: yt-dlp скачивает HLS → ffmpeg собирает mp4
6. Popup: polling /api/status каждые 1.5с → прогресс-бар
7. При ready: GET /api/file → chrome.downloads.download
```

## Поддерживаемые платформы

| Платформа | Обнаружение | Качество |
|-----------|-------------|----------|
| GetCourse (Kinescope) | webRequest `gceuproxy.com/api/playlist/master/*` | Вручную 360–1080p |
| Kinescope (прямой) | webRequest `*.kinescopecdn.net/*.m3u8` | Вручную |
| YouTube | URL страницы `youtube.com/watch`, `youtu.be` | Auto (best) |
| VK Video | URL страницы `vk.com/video`, `vkvideo.ru` | Auto (best) |
| Instagram | URL страницы `/reel/`, `/p/`, `/stories/` | Auto (best) |

## Тарифная логика

| Тариф | Скачиваний/день | Макс качество |
|-------|-----------------|---------------|
| Free  | 3               | 720p          |
| Pro   | ∞               | 1080p         |

Ошибка `402 LIMIT_REACHED` или `402 QUALITY_LOCKED` если превышен лимит.

## Ключевые технические решения

- **webRequest как основной метод** — GetCourse использует `lockdown-install.js` (SES), который блокирует переопределение `window.fetch`. webRequest работает на уровне браузера, неуязвим.
- **Два content script world** — MV3 не позволяет одному скрипту быть в MAIN и ISOLATED одновременно. Общаются через `window.dispatchEvent("__vg_found__")`.
- **Дедупликация по хэшу** — из URL `/playlist/master/HASH/...` извлекаем HASH, предпочитаем master над media.
- **Celery вместо asyncio** — фоновые задачи в отдельном процессе, не блокируют API, можно масштабировать воркеры.
- **JWT в chrome.storage.local** — токен хранится в изолированном хранилище расширения, не в localStorage страницы.

## Правила написания кода

- Все функции в `backend-v2/src/` — docstrings на английском
- Комментарии к бизнес-логике — на русском
- В расширении — чистый vanilla JS, без npm зависимостей
- Обрабатывать все ошибки: popup показывает человеческий текст, backend логирует через `logging`
- Один файл = одна ответственность

## Инструкции для ИИ

- `background.js` — Service Worker, нет DOM, только chrome.* API
- `interceptor.js` — MAIN world, нет chrome.*, только window events
- `content.js` — ISOLATED world, есть chrome.runtime, слушает window
- При изменении webRequest паттернов — обновлять в `background.js` И в `manifest.json`
- `TASKS` dict устарел — теперь состояние в PostgreSQL через Celery
- `billing/router.py` есть в коде но не подключён к `main.py` — заготовка под Stripe
