#!/bin/bash

echo "🚀 Starting Research Dashboard..."

# Kill any existing dashboard processes
pkill -f "uvicorn.*research_api" 2>/dev/null || true
sleep 2

# Start dashboard in background
python3 -m uvicorn src.research.dashboard.research_api:app --host 0.0.0.0 --port 8001 > dashboard.log 2>&1 &

# Get the process ID
DASHBOARD_PID=$!
echo "📋 Dashboard started with PID: $DASHBOARD_PID"

# Wait a moment for startup
sleep 3

# Test if it's working
if curl -s http://localhost:8001 > /dev/null 2>&1; then
    echo "✅ Dashboard is running at: http://localhost:8001"
    echo "📊 Available data:"
    echo "   • DJ30: 219,663 bars (M1 timeframe)"
    echo "   • EURUSD: 98 bars (H1 timeframe)"
    echo ""
    echo "🛑 To stop dashboard, run: kill $DASHBOARD_PID"
    echo "📋 Or check logs with: tail -f dashboard.log"
else
    echo "❌ Dashboard failed to start"
    echo "📋 Check logs: cat dashboard.log"
fi