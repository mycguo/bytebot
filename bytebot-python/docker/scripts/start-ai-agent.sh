#!/bin/bash
set -e

echo "🚀 Starting AI Agent Service..."

# Wait for database to be ready with retries
echo "Waiting for database to be ready..."
for i in {1..30}; do
  if pg_isready -h ${DATABASE_HOST:-postgres} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-postgres} >/dev/null 2>&1; then
    echo "Database is ready!"
    break
  else
    echo "Waiting for PostgreSQL... (attempt $i/30)"
    sleep 2
  fi
  if [ $i -eq 30 ]; then
    echo "Database connection timeout after 60 seconds"
    exit 1
  fi
done

# Run database migrations
echo "Running database migrations..."
cd /app
if command -v alembic >/dev/null 2>&1 && [ -f "alembic.ini" ]; then
  alembic upgrade head
else
  echo "Warning: alembic not available or alembic.ini not found, skipping migrations"
fi

# Start the AI agent service
echo "Starting AI agent service on port ${PORT:-9996}..."
cd /app/packages/ai_agent

# Use the specific virtual environment Python
VENV_PYTHON=$(poetry env info --path)/bin/python
export PYTHONPATH="/app/packages/ai_agent/src:/app/packages/shared/src:$PYTHONPATH"

# Debug: Show Python path and uvicorn location
echo "Using Python: $VENV_PYTHON"
$VENV_PYTHON -c "import sys; print('Python path:', sys.path[:3])"
$VENV_PYTHON -c "import uvicorn; print('uvicorn found:', uvicorn.__version__)"

# Start the service
exec $VENV_PYTHON -m ai_agent.main