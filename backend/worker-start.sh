#!/bin/bash
set -e

# Устанавливаем deno для yt-dlp
if ! command -v deno &> /dev/null; then
    echo "Installing deno..."
    curl -fsSL https://deno.land/install.sh | sh
    export DENO_INSTALL="/root/.deno"
    export PATH="$DENO_INSTALL/bin:$PATH"
fi

# Устанавливаем yt-dlp
pip install --upgrade yt-dlp

# Устанавливаем ffmpeg
apt-get update && apt-get install -y ffmpeg

# Устанавливаем psycopg2
pip install psycopg2-binary

# Запускаем celery
exec celery -A src.worker.tasks worker --loglevel=info