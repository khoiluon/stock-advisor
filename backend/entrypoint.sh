#!/bin/bash
# ============================================================
# Entrypoint script cho Backend container (Production)
# ============================================================
# Script này đảm bảo:
# 1. Đợi MySQL sẵn sàng
# 2. Chạy migrations (chỉ khi là backend service)
# 3. Collect static files cho Django Admin (chỉ khi là backend service)
# 4. Khởi động lệnh chính (daphne, celery worker, celery beat, ...)

set -e

# --- Đợi MySQL sẵn sàng ---
echo "⏳ Đang đợi MySQL ($DB_HOST:$DB_PORT) sẵn sàng..."
while ! python -c "
import MySQLdb
try:
    MySQLdb.connect(
        host='${DB_HOST:-db}',
        port=int('${DB_PORT:-3306}'),
        user='${DB_USER:-root}',
        passwd='${DB_PASSWORD:-123123}',
        db='${DB_NAME:-stock_advisor_db}'
    )
    print('✅ MySQL đã sẵn sàng!')
except Exception as e:
    print(f'⏳ MySQL chưa sẵn sàng: {e}')
    exit(1)
" 2>/dev/null; do
    sleep 2
done

# --- Chạy migrations + collectstatic (chỉ cho backend service chính) ---
# Biến RUN_MIGRATIONS=true chỉ được set cho service backend trong docker-compose
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🔄 Đang chạy database migrations..."
    python manage.py migrate --noinput
    echo "✅ Migrations hoàn tất!"

    echo "🔄 Đang collect static files..."
    python manage.py collectstatic --noinput
    echo "✅ Collectstatic hoàn tất!"
fi

# --- Khởi động lệnh chính ---
echo "🚀 Khởi động: $@"
exec "$@"