#!/bin/bash
# backup.sh — Бэкап PostgreSQL → локальная папка + опционально S3
# Запускать: ./scripts/backup.sh
# По расписанию: добавить в cron или GitHub Actions scheduled workflow

set -e

# Настройки из .env или переменных окружения
DB_NAME="${POSTGRES_DB:-videograb}"
DB_USER="${POSTGRES_USER:-videograb}"
DB_HOST="${POSTGRES_HOST:-localhost}"
BACKUP_DIR="/home/deploy/backups/videograb"
KEEP_DAYS=7  # хранить бэкапы за последние 7 дней

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="videograb_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[backup] Начинаю бэкап БД $DB_NAME..."

# Дамп через docker exec (БД в контейнере)
docker exec videograb-db-1 pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$FILENAME"

echo "[backup] Готово: $BACKUP_DIR/$FILENAME ($(du -sh "$BACKUP_DIR/$FILENAME" | cut -f1))"

# Удаляем бэкапы старше KEEP_DAYS дней
find "$BACKUP_DIR" -name "videograb_*.sql.gz" -mtime +$KEEP_DAYS -delete
echo "[backup] Старые бэкапы (>$KEEP_DAYS дней) удалены"

# Опционально: загрузить в S3 (раскомментировать если нужно)
# aws s3 cp "$BACKUP_DIR/$FILENAME" "s3://your-bucket/videograb/$FILENAME"
# echo "[backup] Загружен в S3"

echo "[backup] Всё готово ✅"
