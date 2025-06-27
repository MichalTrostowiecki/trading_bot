"""
Web Trading Dashboard
FastAPI-based web interface for trading bot control and monitoring.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.utils

from src.execution.trading_engine import get_trading_engine, TradingState, TradingParameters
from src.data.mt5_interface import get_connection
from src.monitoring import get_logger

logger = get_logger("web_dashboard")

# Pydantic models for API requests
class TradingParametersUpdate(BaseModel):
    enabled_symbols: Optional[List[str]] = None
    risk_per_trade: Optional[float] = None
    max_positions: Optional[int] = None
    max_daily_loss: Optional[float] = None
    london_session: Optional[bool] = None
    new_york_session: Optional[bool] = None
    asian_session: Optional[bool] = None
    news_filter: Optional[bool] = None


class EmergencyAction(BaseModel):
    action: str  # "stop", "pause", "resume", "emergency_stop"
    close_positions: bool = False


# FastAPI app
app = FastAPI(title="Fibonacci Trading Bot Dashboard", version="1.0.0")

# Enable CORS for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection might be closed
                pass

manager = ConnectionManager()


# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fibonacci Trading Bot Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.28.0.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .status-running { color: #10b981; }
        .status-stopped { color: #ef4444; }
        .status-paused { color: #f59e0b; }
        .status-error { color: #dc2626; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div class="flex justify-between items-center">
                <h1 class="text-3xl font-bold text-gray-800">Fibonacci Trading Bot</h1>
                <div class="flex items-center space-x-4">
                    <div class="text-sm">
                        <span class="text-gray-600">Status:</span>
                        <span id="bot-status" class="font-semibold">Loading...</span>
                    </div>
                    <div class="text-sm">
                        <span class="text-gray-600">Daily P&L:</span>
                        <span id="daily-pnl" class="font-semibold">$0.00</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Control Panel -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <!-- Bot Controls -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Bot Controls</h2>
                <div class="space-y-3">
                    <button id="start-btn" class="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded">
                        Start Trading
                    </button>
                    <button id="pause-btn" class="w-full bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-2 px-4 rounded">
                        Pause Trading
                    </button>
                    <button id="stop-btn" class="w-full bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-4 rounded">
                        Stop Trading
                    </button>
                    <button id="emergency-btn" class="w-full bg-red-800 hover:bg-red-900 text-white font-semibold py-2 px-4 rounded">
                        Emergency Stop
                    </button>
                </div>
            </div>

            <!-- Risk Settings -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Risk Settings</h2>
                <div class="space-y-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Risk per Trade (%)</label>
                        <input id="risk-per-trade" type="number" step="0.01" min="0.01" max="5" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Max Positions</label>
                        <input id="max-positions" type="number" min="1" max="10" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Max Daily Loss (%)</label>
                        <input id="max-daily-loss" type="number" step="0.01" min="1" max="20" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                    </div>
                    <button id="update-risk-btn" class="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded">
                        Update Risk Settings
                    </button>
                </div>
            </div>

            <!-- Symbol Selection -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Trading Symbols</h2>
                <div class="space-y-2">
                    <div class="flex items-center">
                        <input id="eurusd-cb" type="checkbox" class="mr-2">
                        <label for="eurusd-cb">EUR/USD</label>
                    </div>
                    <div class="flex items-center">
                        <input id="gbpusd-cb" type="checkbox" class="mr-2">
                        <label for="gbpusd-cb">GBP/USD</label>
                    </div>
                    <div class="flex items-center">
                        <input id="usdjpy-cb" type="checkbox" class="mr-2">
                        <label for="usdjpy-cb">USD/JPY</label>
                    </div>
                    <div class="flex items-center">
                        <input id="audusd-cb" type="checkbox" class="mr-2">
                        <label for="audusd-cb">AUD/USD</label>
                    </div>
                    <button id="update-symbols-btn" class="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded mt-3">
                        Update Symbols
                    </button>
                </div>
            </div>
        </div>

        <!-- Performance Metrics -->
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
            <div class="bg-white rounded-lg shadow-lg p-6 text-center">
                <h3 class="text-lg font-semibold text-gray-700">Active Positions</h3>
                <p id="active-positions" class="text-3xl font-bold text-blue-600">0</p>
            </div>
            <div class="bg-white rounded-lg shadow-lg p-6 text-center">
                <h3 class="text-lg font-semibold text-gray-700">Daily Trades</h3>
                <p id="daily-trades" class="text-3xl font-bold text-green-600">0</p>
            </div>
            <div class="bg-white rounded-lg shadow-lg p-6 text-center">
                <h3 class="text-lg font-semibold text-gray-700">Win Rate</h3>
                <p id="win-rate" class="text-3xl font-bold text-purple-600">0%</p>
            </div>
            <div class="bg-white rounded-lg shadow-lg p-6 text-center">
                <h3 class="text-lg font-semibold text-gray-700">Total Trades</h3>
                <p id="total-trades" class="text-3xl font-bold text-indigo-600">0</p>
            </div>
        </div>

        <!-- Full Width Chart -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">Live Chart - EUR/USD with Fibonacci Analysis & Fractals</h2>
            <div id="live-chart" style="height: 800px; width: 100%;"></div>
        </div>

        <!-- Active Positions -->
        <div class="bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Active Positions</h2>
            <div id="positions-table" class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">P&L</th>
                        </tr>
                    </thead>
                    <tbody id="positions-tbody" class="bg-white divide-y divide-gray-200">
                        <!-- Positions will be populated here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };

        // Update dashboard with real-time data
        function updateDashboard(data) {
            // Update status
            const statusElement = document.getElementById('bot-status');
            statusElement.textContent = data.state || 'Unknown';
            statusElement.className = `font-semibold status-${data.state || 'unknown'}`;

            // Update metrics
            document.getElementById('daily-pnl').textContent = `$${(data.daily_pnl || 0).toFixed(2)}`;
            document.getElementById('active-positions').textContent = data.active_positions || 0;
            document.getElementById('daily-trades').textContent = data.daily_trades || 0;
            document.getElementById('win-rate').textContent = `${(data.win_rate || 0).toFixed(1)}%`;
            document.getElementById('total-trades').textContent = data.total_trades || 0;

            // Update positions table
            updatePositionsTable(data.positions || []);
        }

        // Update positions table
        function updatePositionsTable(positions) {
            const tbody = document.getElementById('positions-tbody');
            tbody.innerHTML = '';

            positions.forEach(position => {
                const row = document.createElement('tr');
                const profitClass = position.profit >= 0 ? 'text-green-600' : 'text-red-600';
                
                row.innerHTML = `
                    <td class="px-3 py-2 text-sm">${position.symbol}</td>
                    <td class="px-3 py-2 text-sm">${position.type.toUpperCase()}</td>
                    <td class="px-3 py-2 text-sm">${position.volume}</td>
                    <td class="px-3 py-2 text-sm ${profitClass}">$${position.profit.toFixed(2)}</td>
                `;
                tbody.appendChild(row);
            });
        }

        // Bot control functions
        async function controlBot(action, closePositions = false) {
            try {
                const response = await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action, close_positions: closePositions })
                });
                
                if (!response.ok) {
                    throw new Error('Control action failed');
                }
                
                const result = await response.json();
                console.log('Control result:', result);
            } catch (error) {
                console.error('Control error:', error);
                alert('Control action failed: ' + error.message);
            }
        }

        // Update risk settings
        async function updateRiskSettings() {
            const riskPerTrade = parseFloat(document.getElementById('risk-per-trade').value) / 100;
            const maxPositions = parseInt(document.getElementById('max-positions').value);
            const maxDailyLoss = parseFloat(document.getElementById('max-daily-loss').value) / 100;

            try {
                const response = await fetch('/api/parameters', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        risk_per_trade: riskPerTrade,
                        max_positions: maxPositions,
                        max_daily_loss: maxDailyLoss
                    })
                });

                if (!response.ok) {
                    throw new Error('Update failed');
                }

                alert('Risk settings updated successfully');
            } catch (error) {
                console.error('Update error:', error);
                alert('Update failed: ' + error.message);
            }
        }

        // Update trading symbols
        async function updateSymbols() {
            const symbols = [];
            if (document.getElementById('eurusd-cb').checked) symbols.push('EURUSD');
            if (document.getElementById('gbpusd-cb').checked) symbols.push('GBPUSD');
            if (document.getElementById('usdjpy-cb').checked) symbols.push('USDJPY');
            if (document.getElementById('audusd-cb').checked) symbols.push('AUDUSD');

            try {
                const response = await fetch('/api/parameters', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled_symbols: symbols })
                });

                if (!response.ok) {
                    throw new Error('Update failed');
                }

                alert('Trading symbols updated successfully');
            } catch (error) {
                console.error('Update error:', error);
                alert('Update failed: ' + error.message);
            }
        }

        // Event listeners
        document.getElementById('start-btn').addEventListener('click', () => controlBot('start'));
        document.getElementById('pause-btn').addEventListener('click', () => controlBot('pause'));
        document.getElementById('stop-btn').addEventListener('click', () => controlBot('stop'));
        document.getElementById('emergency-btn').addEventListener('click', () => {
            if (confirm('Are you sure you want to execute emergency stop? This will close all positions immediately.')) {
                controlBot('emergency_stop', true);
            }
        });
        document.getElementById('update-risk-btn').addEventListener('click', updateRiskSettings);
        document.getElementById('update-symbols-btn').addEventListener('click', updateSymbols);

        // Load and display chart
        async function loadChart(symbol = 'EURUSD') {
            try {
                const response = await fetch(`/api/chart/${symbol}`);
                const data = await response.json();
                
                if (data.chart) {
                    const chartDiv = document.getElementById('live-chart');
                    Plotly.newPlot(chartDiv, data.chart.data, data.chart.layout, {responsive: true});
                } else {
                    console.error('No chart data received');
                }
            } catch (error) {
                console.error('Failed to load chart:', error);
                // Show placeholder text
                document.getElementById('live-chart').innerHTML = '<p class="text-center text-gray-500 mt-20">Chart data not available</p>';
            }
        }

        // Initialize dashboard
        async function initializeDashboard() {
            try {
                // Load current status
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);

                // Load current parameters
                const paramsResponse = await fetch('/api/parameters');
                const params = await paramsResponse.json();
                
                // Set form values
                document.getElementById('risk-per-trade').value = (params.risk_per_trade * 100).toFixed(2);
                document.getElementById('max-positions').value = params.max_positions;
                document.getElementById('max-daily-loss').value = (params.max_daily_loss * 100).toFixed(2);
                
                // Set symbol checkboxes
                const symbols = params.enabled_symbols || [];
                document.getElementById('eurusd-cb').checked = symbols.includes('EURUSD');
                document.getElementById('gbpusd-cb').checked = symbols.includes('GBPUSD');
                document.getElementById('usdjpy-cb').checked = symbols.includes('USDJPY');
                document.getElementById('audusd-cb').checked = symbols.includes('AUDUSD');

                // Load initial chart
                loadChart('EURUSD');

            } catch (error) {
                console.error('Failed to initialize dashboard:', error);
            }
        }

        // Initialize when page loads
        window.addEventListener('load', initializeDashboard);

        // Refresh data every 5 seconds
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to refresh data:', error);
            }
        }, 5000);

        // Refresh chart every 3 seconds for live updates (more responsive)
        setInterval(async () => {
            try {
                loadChart('EURUSD');
            } catch (error) {
                console.error('Failed to refresh chart:', error);
            }
        }, 3000);
    </script>
</body>
</html>
"""


# API Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard HTML."""
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/api/status")
async def get_status():
    """Get current trading bot status."""
    engine = get_trading_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    status = engine.get_status()
    positions = engine.get_positions()
    
    return {
        **status,
        "positions": positions,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/parameters")
async def get_parameters():
    """Get current trading parameters."""
    engine = get_trading_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    params = engine.parameters
    return {
        "enabled_symbols": params.enabled_symbols,
        "timeframe": params.timeframe,
        "risk_per_trade": params.risk_per_trade,
        "max_positions": params.max_positions,
        "max_daily_loss": params.max_daily_loss,
        "fibonacci_levels": params.fibonacci_levels,
        "fractal_periods": params.fractal_periods,
        "swing_lookback": params.swing_lookback,
        "stop_buffer_pips": params.stop_buffer_pips,
        "london_session": params.london_session,
        "new_york_session": params.new_york_session,
        "asian_session": params.asian_session,
        "news_filter": params.news_filter,
        "ai_pattern_recognition": params.ai_pattern_recognition,
        "ai_parameter_optimization": params.ai_parameter_optimization,
        "ai_entry_timing": params.ai_entry_timing
    }


@app.put("/api/parameters")
async def update_parameters(params: TradingParametersUpdate):
    """Update trading parameters."""
    engine = get_trading_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    # Convert to dict and filter None values
    update_dict = {k: v for k, v in params.dict().items() if v is not None}
    
    success = engine.update_parameters(update_dict)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update parameters")
    
    return {"message": "Parameters updated successfully", "updated": update_dict}


@app.post("/api/control")
async def control_bot(action: EmergencyAction):
    """Control trading bot (start, stop, pause, emergency stop)."""
    engine = get_trading_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    try:
        if action.action == "start":
            success = await engine.start()
        elif action.action == "stop":
            engine._close_all_on_stop = action.close_positions
            success = await engine.stop()
        elif action.action == "pause":
            success = await engine.pause()
        elif action.action == "resume":
            success = await engine.resume()
        elif action.action == "emergency_stop":
            success = await engine.emergency_stop_all()
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        if not success:
            raise HTTPException(status_code=500, detail="Control action failed")
        
        return {"message": f"Action '{action.action}' completed successfully"}
        
    except Exception as e:
        logger.error(f"Control action failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions")
async def get_positions():
    """Get current positions."""
    engine = get_trading_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    return {"positions": engine.get_positions()}


@app.get("/api/fibonacci/{symbol}")
async def get_fibonacci_levels(symbol: str):
    """Get Fibonacci levels for a specific symbol."""
    engine = get_trading_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")
    
    levels = engine.get_fibonacci_levels(symbol)
    return {"symbol": symbol, "fibonacci_levels": levels}


@app.get("/api/chart/{symbol}")
async def get_chart_data(symbol: str, bars: int = 200):
    """Get chart data for visualization."""
    mt5 = get_connection()
    if not mt5:
        # Return mock chart data when MT5 is not available
        return {
            "chart": {
                "data": [],
                "layout": {
                    "title": f"{symbol} - Chart Not Available (MT5 Required)",
                    "xaxis": {"title": "Time"},
                    "yaxis": {"title": "Price"},
                    "annotations": [{
                        "text": "MT5 connection required for live chart data<br>Run on Windows with MT5 installed",
                        "x": 0.5,
                        "y": 0.5,
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16}
                    }]
                }
            }
        }
    
    try:
        # Get market data using get_rates method
        from src.data.mt5_interface import TimeFrame
        timeframe = TimeFrame.M1  # 1-minute timeframe
        data = mt5.get_rates(symbol, timeframe, bars)
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Create candlestick chart with improved styling
        fig = go.Figure(data=go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=symbol,
            increasing=dict(line=dict(color='#16A34A', width=1), fillcolor='#16A34A'),  # Green
            decreasing=dict(line=dict(color='#DC2626', width=1), fillcolor='#DC2626'),  # Red
            line=dict(width=1),
            hoverinfo='x+y+text',
            text=[f'O:{o:.5f} H:{h:.5f} L:{l:.5f} C:{c:.5f}' 
                  for o, h, l, c in zip(data['Open'], data['High'], data['Low'], data['Close'])]
        ))
        
        # Get trading engine data
        engine = get_trading_engine()
        if engine:
            # Add fractal points
            fractals = engine.fractals_cache.get(symbol, [])
            if fractals:
                # Separate up and down fractals
                up_fractals = [f for f in fractals if f.type.value == 'up']
                down_fractals = [f for f in fractals if f.type.value == 'down']
                
                # Add up fractals (highs) - positioned above candles
                if up_fractals:
                    fractal_times = []
                    fractal_prices = []
                    for f in up_fractals:
                        # Position markers above the actual fractal price for visibility
                        offset = (data['High'].max() - data['Low'].min()) * 0.002  # 0.2% offset
                        fractal_times.append(f.timestamp)
                        fractal_prices.append(f.price + offset)
                    
                    if fractal_times:
                        fig.add_trace(go.Scatter(
                            x=fractal_times,
                            y=fractal_prices,
                            mode='markers',
                            marker=dict(color='#DC2626', size=16, symbol='triangle-down', 
                                      line=dict(color='white', width=2)),
                            name='Up Fractals (Swing Highs)',
                            hovertemplate='Swing High<br>Actual Price: %{customdata:.5f}<br>Time: %{x}<extra></extra>',
                            customdata=[f.price for f in up_fractals]
                        ))
                
                # Add down fractals (lows) - positioned below candles
                if down_fractals:
                    fractal_times = []
                    fractal_prices = []
                    for f in down_fractals:
                        # Position markers below the actual fractal price for visibility
                        offset = (data['High'].max() - data['Low'].min()) * 0.002  # 0.2% offset
                        fractal_times.append(f.timestamp)
                        fractal_prices.append(f.price - offset)
                    
                    if fractal_times:
                        fig.add_trace(go.Scatter(
                            x=fractal_times,
                            y=fractal_prices,
                            mode='markers',
                            marker=dict(color='#2563EB', size=16, symbol='triangle-up',
                                      line=dict(color='white', width=2)),
                            name='Down Fractals (Swing Lows)',
                            hovertemplate='Swing Low<br>Actual Price: %{customdata:.5f}<br>Time: %{x}<extra></extra>',
                            customdata=[f.price for f in down_fractals]
                        ))
            
            # Add Fibonacci levels with improved visualization
            fibonacci_levels = engine.get_fibonacci_levels(symbol)
            if fibonacci_levels and 'retracements' in fibonacci_levels:
                # Get all fractals for showing swing structure
                fractals = engine.fractals_cache.get(symbol, [])
                
                # Create proper swing connections between alternating highs and lows
                if len(fractals) >= 2:
                    # Only draw swing lines that make sense (connecting different fractal types)
                    swing_lines = []
                    
                    for i in range(len(fractals) - 1):
                        current_fractal = fractals[i]
                        next_fractal = fractals[i + 1]
                        
                        # Only connect if fractals are different types (high to low or low to high)
                        if current_fractal.type != next_fractal.type:
                            swing_lines.append((current_fractal, next_fractal, i))
                    
                    # Draw the swing lines with proper styling
                    for idx, (start_fractal, end_fractal, position) in enumerate(swing_lines):
                        # Determine line style based on recency
                        if position >= len(fractals) - 3:  # Most recent swings
                            line_color = '#8B5CF6'
                            line_width = 3
                            line_dash = 'solid'
                            opacity = 1.0
                            show_markers = True
                            marker_size = 6
                            line_name = f'Recent Swing ({end_fractal.price - start_fractal.price:+.5f})'
                        elif position >= len(fractals) - 5:  # Previous swings
                            line_color = '#A78BFA'
                            line_width = 2
                            line_dash = 'dash'
                            opacity = 0.7
                            show_markers = False
                            marker_size = 4
                            line_name = f'Previous Swing ({end_fractal.price - start_fractal.price:+.5f})'
                        else:  # Older swings
                            line_color = '#C4B5FD'
                            line_width = 1
                            line_dash = 'dot'
                            opacity = 0.4
                            show_markers = False
                            marker_size = 3
                            line_name = None
                        
                        # Add swing line only if it makes sense
                        fig.add_trace(go.Scatter(
                            x=[start_fractal.timestamp, end_fractal.timestamp],
                            y=[start_fractal.price, end_fractal.price],
                            mode='lines+markers' if show_markers else 'lines',
                            line=dict(color=line_color, width=line_width, dash=line_dash),
                            marker=dict(color=line_color, size=marker_size) if show_markers else None,
                            name=line_name,
                            hovertemplate=f'{start_fractal.type.value.title()} to {end_fractal.type.value.title()}<br>Price: %{{y:.5f}}<br>Time: %{{x}}<extra></extra>',
                            opacity=opacity,
                            showlegend=line_name is not None and idx < 2  # Only show first 2 in legend
                        ))
                
                # Calculate time range for limited Fibonacci lines
                time_range = data.index[-1] - data.index[0]
                # Use the dominant swing from Fibonacci levels for timing
                if 'swing_start' in fibonacci_levels:
                    fib_start_time = max(fibonacci_levels['swing_start'].timestamp, data.index[-1] - time_range * 0.7)
                else:
                    fib_start_time = data.index[-1] - time_range * 0.7
                fib_end_time = data.index[-1] + time_range * 0.15  # Extend 15% into future
                
                # Add Fibonacci retracement levels with limited width and better colors
                fib_colors = ['#FFD700', '#FF8C00', '#FF4500', '#32CD32', '#4169E1']  # Gold, DarkOrange, OrangeRed, LimeGreen, RoyalBlue
                fib_styles = ['solid', 'dash', 'dot', 'dashdot', 'longdash']
                
                for i, (level_name, level_price) in enumerate(fibonacci_levels['retracements'].items()):
                    color = fib_colors[i % len(fib_colors)]
                    dash_style = fib_styles[i % len(fib_styles)]
                    
                    # Add horizontal line with limited width
                    fig.add_trace(go.Scatter(
                        x=[fib_start_time, fib_end_time],
                        y=[level_price, level_price],
                        mode='lines',
                        line=dict(color=color, width=2, dash=dash_style),
                        name=f'Fib {level_name} ({level_price:.5f})',
                        hovertemplate=f'Fibonacci {level_name}<br>Price: %{{y:.5f}}<extra></extra>',
                        showlegend=True
                    ))
                    
                    # Add text annotation on the right
                    fig.add_annotation(
                        x=fib_end_time,
                        y=level_price,
                        text=f"  {level_name}",
                        showarrow=False,
                        xanchor="left",
                        yanchor="middle",
                        font=dict(size=10, color=color),
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor=color,
                        borderwidth=1
                    )
        
        fig.update_layout(
            title={
                'text': f"{symbol} - Fibonacci Trading Analysis",
                'x': 0.5,
                'font': {'size': 20}
            },
            xaxis_title="Time",
            yaxis_title="Price",
            height=800,  # Increased height
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(
                l=60,   # Left margin
                r=120,  # Right margin - increased for space
                t=80,   # Top margin
                b=60    # Bottom margin
            ),
            xaxis=dict(
                gridcolor='lightgray',
                gridwidth=1,
                domain=[0, 0.85]  # Chart takes 85% of width, leaving space on right
            ),
            yaxis=dict(
                gridcolor='lightgray',
                gridwidth=1,
                side='left'
            ),
            hovermode='x unified'
        )
        
        return {"chart": json.loads(fig.to_json())}
        
    except Exception as e:
        logger.error(f"Failed to get chart data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send real-time updates every 2 seconds
            engine = get_trading_engine()
            if engine:
                status = engine.get_status()
                positions = engine.get_positions()
                
                data = {
                    **status,
                    "positions": positions,
                    "timestamp": datetime.now().isoformat()
                }
                
                await manager.send_personal_message(json.dumps(data), websocket)
            
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    engine = get_trading_engine()
    mt5 = get_connection()
    
    return {
        "status": "healthy",
        "trading_engine": "available" if engine else "unavailable",
        "mt5_interface": "available" if mt5 else "unavailable",
        "timestamp": datetime.now().isoformat()
    }


# Initialize dashboard
async def start_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Start the web dashboard server."""
    import uvicorn
    
    logger.info(f"Starting web dashboard on http://{host}:{port}")
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        reload=False
    )
    
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(start_dashboard())