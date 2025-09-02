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
if [ -f "alembic.ini" ]; then
  alembic upgrade head
else
  echo "Warning: alembic.ini not found, skipping migrations"
fi

# Start the AI agent service
echo "Starting AI agent service on port ${PORT:-9996}..."
cd /app/packages/ai_agent
exec poetry run python -m ai_agent.main