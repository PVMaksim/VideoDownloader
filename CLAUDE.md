# CLAUDE.md — VideoGrab

## Стек

### Extension (Chrome MV3)
- Язык: JavaScript (Vanilla, без фреймворков)
- Платформа: Chrome Extension Manifest V3
- Хранилище: `chrome.storage.local`
- Файлы: `background.js`, `content.js`, `interceptor.js`, `popup/`, `options/`

### Backend (VPS)
- Язык: Python 3.12
- Фреймворк: FastAPI 0.115
- Загрузчик: yt-dlp (последняя версия)
- Медиа: ffmpeg (системный, в Docker)
- Инфраструктура: Docker, docker-compose, Nginx + Let's Encrypt

## Архитектура

```
Chrome Browser
├── interceptor.js  (MAIN world)      — перехват fetch/XHR страницы
├── content.js      (ISOLATED world)  — мост: window events → chrome.runtime
├── background.js   (Service Worker)  — webRequest + хранилище найденных видео
├── popup/          — UI: список видео, выбор качества, прогресс-бар
└── options/        — настройки: URL бэкенда, API ключ

VPS Backend
├── main.py         — FastAPI роуты: /api/download, /api/status, /api/file
├── downloader.py   — обёртка над yt-dlp, отслеживание прогресса
└── config.py       — настройки из .env
```

**Поток данных:**
1. Страница делает запрос к видео → `webRequest` в `background.js` перехватывает URL
2. Для YouTube/VK/Instagram — URL страницы берётся напрямую из `tab.url`
3. Popup показывает список → пользователь нажимает "Скачать"
4. Расширение собирает cookies → POST `/api/download` на VPS
5. VPS запускает yt-dlp → скачивает HLS сегменты → ffmpeg собирает mp4
6. Popup опрашивает `/api/status` каждые 1.5 сек → показывает прогресс
7. При статусе `ready` → GET `/api/file` → браузер скачивает mp4

## Поддерживаемые платформы

| Платформа | Метод обнаружения | Выбор качества |
|-----------|-------------------|----------------|
| GetCourse (Kinescope) | webRequest `gceuproxy.com/api/playlist/master/*` | Вручную 360p–1080p |
| Kinescope (прямой) | webRequest `*.kinescopecdn.net/*.m3u8` | Вручную |
| YouTube | URL страницы (`youtube.com/watch`, `youtu.be`) | Автоматически (best) |
| VK Video | URL страницы (`vk.com/video`, `vkvideo.ru`) | Автоматически |
| Instagram | URL страницы (`/reel/`, `/p/`, `/stories/`) | Автоматически |

## Ключевые технические решения

- **Два content script'а** — `interceptor.js` в MAIN world переопределяет `fetch`/`XHR`, `content.js` в ISOLATED world имеет доступ к `chrome.runtime`. Общаются через `window.dispatchEvent`.
- **webRequest как основной метод** для GetCourse — надёжнее перехвата fetch, не зависит от lockdown-библиотек платформы.
- **Дедупликация по хэшу видео** — из URL `/playlist/master/HASH/...` извлекаем HASH, предпочитаем master над media.
- **Keepalive через `chrome.alarms`** — не даём Service Worker засыпать.
- **Cookies передаются автоматически** через `chrome.cookies.getAll()` — пользователь не копирует ничего вручную.

## Правила написания кода

- Все функции в `backend/src/` должны иметь docstrings (на английском)
- Комментарии к бизнес-логике: на русском
- В расширении — чистый vanilla JS, без зависимостей
- Обрабатывать все ошибки: в popup показывать понятный текст, в backend логировать через `logging`
- Один файл = одна ответственность

## Инструкции для ИИ

- `background.js` — Service Worker, нет доступа к DOM, только chrome.* API
- `interceptor.js` — MAIN world, нет `chrome.*`, только `window.dispatchEvent`
- `content.js` — ISOLATED world, есть `chrome.runtime`, слушает `window` события
- При изменении паттернов webRequest — обновлять и в `manifest.json` (host_permissions), и в `background.js`
- Backend TASKS — in-memory dict, не переживает рестарт контейнера (это нормально для временных файлов)
