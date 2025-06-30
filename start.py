#!/usr/bin/env python3
"""
🚀 ONE-CLICK FIBONACCI TRADING DASHBOARD
Simple command: python3 start.py
"""

import subprocess
import sys
import time

# Clean up any existing processes
subprocess.run(['pkill', '-f', 'uvicorn'], capture_output=True)
time.sleep(2)

print("🚀 Starting Fibonacci Trading Dashboard...")
print("🌐 URL: http://127.0.0.1:9000")
print("📊 Data: 219,663 DJ30 bars ready")
print("-" * 40)

# Start dashboard
cmd = [
    sys.executable, '-m', 'uvicorn',
    'src.research.dashboard.research_api:app',
    '--host', '127.0.0.1',
    '--port', '9000'
]

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n🛑 Dashboard stopped")