#!/bin/bash
# Run script for Badminton API

VENV_PATH="/Users/pondai/.openclaw/workspace/.venv_badminton"
PROJECT_PATH="/Volumes/pondai/projects/badminton_v2/backend"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Change to project directory
cd "$PROJECT_PATH"

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Add PostgreSQL to PATH
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"

# Run the server
echo "Starting Badminton API..."
echo "API Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
