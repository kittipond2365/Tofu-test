#!/bin/bash
set -e

echo "🔄 $(date) - Starting setup..."

echo "🗄️  Creating database tables..."
python3 << 'PYEOF'
import asyncio
import os

# Ensure SECRET_KEY is set for config
os.environ.setdefault('SECRET_KEY', 'temporary-secret-key-for-db-init')

from app.core.database import init_db

async def setup():
    try:
        await init_db()
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"⚠️  Table creation note: {e}")
        # Continue even if some tables exist

asyncio.run(setup())
PYEOF

echo "🔧 Running migrations (if any)..."
python scripts/run_migrations_direct.py || echo "⚠️  Migration script completed with warnings"

echo "🚀 Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
