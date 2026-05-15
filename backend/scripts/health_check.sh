#!/bin/bash
# health_check.sh — Проверка состояния всех сервисов VideoGrab
# Запускать: ./scripts/api/health_check.sh
# Возвращает 0 если всё ОК, 1 если есть проблемы

set -e

APP_URL="${APP_URL:-http://localhost:8000}"
ERRORS=0

echo "=== VideoGrab Health Check ==="
echo "$(date)"
echo ""

# ── API ──────────────────────────────────────────────────────────
echo -n "API /api/api/health ... "
HTTP_CODE=$(curl -s -o /tmp/vg_health.json -w "%{http_code}" "$APP_URL/api/api/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  STATUS=$(cat /tmp/vg_health.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "?")
  echo "✅ OK (status=$STATUS)"
else
  echo "❌ FAIL (HTTP $HTTP_CODE)"
  ERRORS=$((ERRORS + 1))
fi

# ── PostgreSQL ───────────────────────────────────────────────────
echo -n "PostgreSQL ... "
if docker exec videograb-db-1 pg_isready -U "${POSTGRES_USER:-videograb}" -q 2>/dev/null; then
  echo "✅ OK"
else
  echo "❌ FAIL"
  ERRORS=$((ERRORS + 1))
fi

# ── Redis ────────────────────────────────────────────────────────
echo -n "Redis ... "
if docker exec videograb-redis-1 redis-cli ping 2>/dev/null | grep -q "PONG"; then
  echo "✅ OK"
else
  echo "❌ FAIL"
  ERRORS=$((ERRORS + 1))
fi

# ── Celery Worker ────────────────────────────────────────────────
echo -n "Celery Worker ... "
if docker ps --filter "name=videograb-worker" --filter "status=running" | grep -q worker; then
  echo "✅ Running"
else
  echo "❌ NOT RUNNING"
  ERRORS=$((ERRORS + 1))
fi

# ── Disk space ───────────────────────────────────────────────────
echo -n "Disk space ... "
DISK_USE=$(df /tmp | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USE" -lt 85 ]; then
  echo "✅ OK (${DISK_USE}% used)"
else
  echo "⚠️  WARNING (${DISK_USE}% used)"
fi

echo ""
echo "─────────────────────────────"

if [ "$ERRORS" -eq 0 ]; then
  echo "✅ Все сервисы работают нормально"
  exit 0
else
  echo "❌ Проблемы: $ERRORS сервис(а/ов) не работают"
  exit 1
fi
