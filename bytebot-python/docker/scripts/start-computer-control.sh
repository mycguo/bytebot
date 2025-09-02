#!/bin/bash
set -e

echo "🚀 Starting Computer Control Service..."

# Start virtual display
echo "Starting virtual display..."
# Clean up any existing X server lock
rm -f /tmp/.X99-lock
# Start Xvfb
Xvfb :99 -screen 0 1280x960x24 &
export DISPLAY=:99

# Wait for display to be ready
sleep 3

# Start the computer control service
echo "Starting computer control service on port ${PORT:-9995}..."
cd /app
export PYTHONPATH=/app/packages/computer_control/src:$PYTHONPATH
cd /app/packages/computer_control
exec poetry run python -m computer_control.main