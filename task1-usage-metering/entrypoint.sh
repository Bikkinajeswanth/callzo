#!/bin/sh
set -e

echo "=== Starting Callzo Usage Metering Service ==="

# Wait for PostgreSQL to be ready if DATABASE_URL is postgresql
if echo "$DATABASE_URL" | grep -q "postgres"; then
    echo "Waiting for PostgreSQL database to accept connections..."
    until python -c "
import sys, os, psycopg2
try:
    raw_url = os.getenv('DATABASE_URL_SYNC') or os.getenv('DATABASE_URL')
    if '://' in raw_url:
        _, rest = raw_url.split('://', 1)
        dsn = 'postgresql://' + rest
    else:
        dsn = raw_url
    conn = psycopg2.connect(dsn, connect_timeout=3)
    conn.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
"; do
        echo "PostgreSQL is unavailable - sleeping 1 second"
        sleep 1
    done
    echo "PostgreSQL is up and accepting connections!"

    echo "Running database schema migrations via Alembic..."
    alembic upgrade head
    echo "Migrations applied successfully."
fi

if [ $# -gt 0 ]; then
    exec "$@"
fi

echo "Launching Uvicorn server on ${HOST:-0.0.0.0}:${PORT:-8000}..."
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
