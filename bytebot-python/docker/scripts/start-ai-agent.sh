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

# Skip database migrations as they're handled by the application
echo "Skipping database migrations - handled by application initialization"

# Start the AI agent service
echo "Starting AI agent service on port ${PORT:-9996}..."
cd /app/packages/ai_agent

# Use system Python with installed packages
echo "Starting service with system Python..."
export PYTHONPATH="/app/packages/ai_agent/src:/app/packages/shared/src:$PYTHONPATH"

# Run directly with system Python
exec python -c "
import sys
sys.path.insert(0, '/app/packages/ai_agent/src')
sys.path.insert(0, '/app/packages/shared/src')
print('Python paths:', sys.path[:4])
from ai_agent.main import main
main()
"