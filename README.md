# VideoGrab

Chrome-расширение + облачный бэкенд для скачивания видео с GetCourse, YouTube, VK и Instagram. Работает с платформами требующими авторизации — автоматически использует cookies активной сессии браузера. Поддерживает мультипользовательский режим с тарифными планами.

## Как это работает

```
Chrome Extension
  → перехватывает видео-поток (HLS/m3u8) или берёт URL страницы
  → передаёт cookies + JWT токен на VPS

VPS Backend (FastAPI + Celery)
  → yt-dlp скачивает сегменты → ffmpeg собирает mp4
  → отдаёт готовый файл в браузер
```

## Поддерживаемые платформы

| Платформа | Статус | Авторизация |
|-----------|--------|-------------|
| GetCourse (Kinescope) | ✅ Работает | Автоматически (cookies) |
| YouTube | ✅ Работает | Автоматически (cookies) |
| VK Video | 🧪 Тестируется | Автоматически (cookies) |
| Instagram Reels/Posts | ⚠️ Нестабильно | Автоматически (cookies) |

## Тарифы

| Тариф | Скачиваний/день | Макс качество |
|-------|-----------------|---------------|
| Free | 3 | 720p |
| Pro | ∞ | 1080p |

---

## Установка расширения

1. Скачай `videograb-extension.zip`, распакуй
2. Открой `chrome://extensions/` → включи **Режим разработчика**
3. **Загрузить распакованное** → выбери папку `videograb-extension`
4. Нажми ⚙️ → укажи URL бэкенда → зарегистрируйся или войди

---

## Деплой бэкенда на VPS

### Требования
- Ubuntu 22.04+, Docker + docker-compose
- Nginx + certbot (HTTPS обязателен)
- 10+ ГБ свободного места

### Быстрый старт

```bash
# 1. Скопируй папку backend-v2/ на VPS
scp -r backend / user@your-vps:/home/deploy/videograb/

# 2. Зайди на VPS
ssh user@your-vps
cd /home/deploy/videograb

# 3. Настрой окружение
cp .env.example .env
nano .env   # заполни все переменные

# 4. Запусти
docker-compose up -d

# 5. Проверь
curl https://api.yourdomain.com/api/health
```

### Nginx конфиг

```nginx
server {
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
}
```

```bash
certbot --nginx -d api.yourdomain.com
```

---

## Переменные окружения

Все описаны в `backend /.env.example`:

```env
# Обязательные
POSTGRES_PASSWORD=    # пароль БД
SECRET_KEY=           # python3 -c "import secrets; print(secrets.token_hex(32))"
RESEND_API_KEY=       # resend.com → API Keys (бесплатно 3000 писем/мес)
EMAIL_FROM=           # VideoGrab <noreply@yourdomain.com>
APP_URL=              # https://yourdomain.com

# Опциональные (есть дефолты)
FILE_TTL_HOURS=2
FREE_DAILY_LIMIT=3
FREE_MAX_HEIGHT=720
```

---

## API

Все запросы требуют заголовок `Authorization: Bearer <jwt_token>`

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/health` | Проверка сервера |
| POST | `/auth/register` | Регистрация → письмо верификации |
| GET | `/auth/verify?token=` | Подтверждение email |
| POST | `/auth/login` | Вход → JWT токен |
| GET | `/auth/me` | Профиль + downloads_today |
| POST | `/api/download` | Создать задачу скачивания |
| GET | `/api/status/{task_id}` | Прогресс 0–100% |
| GET | `/api/file/{task_id}` | Скачать готовый mp4 |
| GET | `/api/history` | История скачиваний |

---

## Структура проекта

```
videograb/
├── extension/              Chrome Extension v1.0.0 (MV3)
│   ├── background.js       Service Worker: webRequest, keepalive
│   ├── content.js          ISOLATED: мост events → chrome.runtime
│   ├── interceptor.js      MAIN: резервный перехват fetch/XHR
│   ├── popup/              UI: видео, качество, прогресс
│   └── options/            Настройки: сервер, логин, профиль
│
├── backend-v2/             Продакшн бэкенд (мультипользовательский)
│   ├── src/auth/           JWT auth + email verification
│   ├── src/downloads/      Задачи, лимиты, файлы
│   ├── src/worker/         Celery + yt-dlp
│   ├── src/db/             PostgreSQL models
│   ├── src/billing/        Заготовка Stripe (не активна)
│   ├── docker-compose.yml  api + worker + db + redis
│   └── .env.example
│
├── backend/                Устаревший v1 (личное использование)
│
├── CLAUDE.md               Технический контекст для AI
├── MEMORY.md               Дневник разработки + следующие шаги
└── README.md               Этот файл
```

---

## Репозиторий

```
GitHub: PVMaksim/videograb
SSH ключ (git push): id_ed25519
SSH ключ (deploy CI/CD): github-actions-key
Папка на VPS: /home/deploy/videograb
```
# deploy test Wed Apr 29 13:47:45 MSK 2026
