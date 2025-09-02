#!/usr/bin/env python3
"""Launch script for Bytebot Web UI."""

import sys
import os
import subprocess

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Launch the Streamlit app."""
    port = int(os.getenv("STREAMLIT_PORT", "9992"))
    
    # Launch streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "src/web_ui/main.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--theme.base", "light",
        "--theme.primaryColor", "#3b82f6",
        "--server.headless", "true"
    ]
    
    print(f"🚀 Starting Bytebot Web UI on port {port}...")
    print(f"📱 Access at: http://localhost:{port}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Bytebot Web UI stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()