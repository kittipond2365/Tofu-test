#!/bin/bash
set -e

echo "🔄 Running database migrations..."

# Try Alembic first, if it fails, use direct migration as fallback
if alembic upgrade head; then
    echo "✅ Alembic migration successful"
else
    echo "⚠️  Alembic migration failed, trying direct migration..."
    python scripts/run_migrations_direct.py
fi

echo "🚀 Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
