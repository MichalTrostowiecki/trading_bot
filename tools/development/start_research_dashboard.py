#!/usr/bin/env python3
"""
Simple dashboard startup script
Run this script to start the research dashboard
"""

import subprocess
import sys
import signal
import time

def signal_handler(sig, frame):
    print('\n🛑 Dashboard stopped by user')
    sys.exit(0)

def main():
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting Fibonacci Trading Bot Research Dashboard")
    print("=" * 60)
    print("🌐 Dashboard will be available at: http://localhost:8001")
    print("📊 Available data:")
    print("   • DJ30: 219,663 bars (M1 timeframe)")
    print("   • EURUSD: 98 bars (H1 timeframe)")
    print()
    print("⏹️  Press Ctrl+C to stop the dashboard")
    print("=" * 60)
    
    try:
        # Start uvicorn directly
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'src.research.dashboard.research_api:app',
            '--host', '0.0.0.0',
            '--port', '8001',
            '--log-level', 'info'
        ])
    except KeyboardInterrupt:
        print('\n🛑 Dashboard stopped')
    except Exception as e:
        print(f'\n❌ Error starting dashboard: {e}')
        sys.exit(1)

if __name__ == "__main__":
    main()