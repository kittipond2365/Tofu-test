#!/bin/bash
set -e

echo "🔄 $(date) - Starting setup..."

echo "🔧 Running comprehensive migrations..."
python scripts/run_migrations_direct.py

echo "🚀 Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
