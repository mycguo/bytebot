#!/bin/bash
set -e

echo "🚀 Starting Web UI Service..."

# Optional: Try to wait for services but don't block startup
echo "Checking for backend services..."
for i in {1..5}; do
  if curl -f http://${AI_AGENT_HOST:-ai-agent}:${AI_AGENT_PORT:-9996}/health >/dev/null 2>&1; then
    echo "AI Agent service is ready!"
    break
  fi
  if [ $i -eq 5 ]; then
    echo "Warning: AI Agent service not ready, starting Web UI anyway"
  fi
  sleep 1
done

for i in {1..5}; do
  if curl -f http://${COMPUTER_CONTROL_HOST:-computer-control}:${COMPUTER_CONTROL_PORT:-9995}/health >/dev/null 2>&1; then
    echo "Computer Control service is ready!"
    break
  fi
  if [ $i -eq 5 ]; then
    echo "Warning: Computer Control service not ready, starting Web UI anyway"
  fi
  sleep 1
done

# Start the web UI service
echo "Starting Web UI service on port 9999..."
cd /app/packages/web_ui
export STREAMLIT_PORT=9999

# Use system Python with installed packages  
echo "Starting Streamlit with system Python..."
exec python run.py