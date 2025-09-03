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

# Start desktop environment components
echo "Starting desktop environment..."
xfwm4 &
sleep 1
xfce4-panel &
sleep 1
xfdesktop &
sleep 2


# Start the computer control service
echo "Starting computer control service on port ${PORT:-9995}..."
cd /app/packages/computer_control

# Use system Python with installed packages
echo "Starting service with system Python..."
export PYTHONPATH="/app/packages/computer_control/src:/app/packages/shared/src:$PYTHONPATH"

# Run directly with system Python
exec python -c "
import sys
sys.path.insert(0, '/app/packages/computer_control/src')
sys.path.insert(0, '/app/packages/shared/src')
print('Python paths:', sys.path[:4])
from computer_control.main import main
main()
"

/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf -n