#!/bin/bash
set -e

echo "🚀 Starting Web UI Service..."

# Wait for AI Agent service to be ready
echo "Waiting for AI Agent service to be ready..."
until curl -f http://${AI_AGENT_HOST:-ai-agent}:${AI_AGENT_PORT:-9996}/health; do
  echo "Waiting for AI Agent service..."
  sleep 2
done

echo "AI Agent service is ready!"

# Wait for Computer Control service to be ready
echo "Waiting for Computer Control service to be ready..."
until curl -f http://${COMPUTER_CONTROL_HOST:-computer-control}:${COMPUTER_CONTROL_PORT:-9995}/health; do
  echo "Waiting for Computer Control service..."
  sleep 2
done

echo "Computer Control service is ready!"

# Start the web UI service
echo "Starting Web UI service on port 9992..."
cd /app/packages/web_ui
export STREAMLIT_PORT=9992
python run.py