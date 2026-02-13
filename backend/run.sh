#!/bin/bash
set -e

echo "🔄 Starting database migrations..."
echo "📅 $(date)"

# Try Alembic first, if it fails, use direct migration as fallback
if alembic upgrade head 2>&1; then
    echo "✅ Alembic migration successful"
else
    echo "⚠️  Alembic migration failed, trying direct migration..."
    python scripts/run_migrations_direct.py
fi

echo "🚀 Starting application..."
echo "📅 $(date)"

uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
