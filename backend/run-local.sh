#!/bin/bash
# Local development server with SQLite

cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Export local env
export $(cat .env.local | xargs)

# Create/initialize database
echo "🗄️  Initializing local SQLite database..."
python3 -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
print('✅ Database initialized')
"

# Run migrations (if any)
echo "🔄 Running migrations..."
python3 scripts/run_migrations_direct.py 2>/dev/null || echo "⚠️  Migration script skipped (SQLite may not need it)"

# Start server
echo "🚀 Starting local server at http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
