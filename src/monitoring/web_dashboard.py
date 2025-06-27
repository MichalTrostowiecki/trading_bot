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
from src.data.mt5_interface import get_mt5_interface
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
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
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

        <!-- Charts and Positions -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Live Chart -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-semibold mb-4">Live Chart</h2>
                <div id="live-chart" style="height: 400px;"></div>
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
async def get_chart_data(symbol: str, bars: int = 100):
    """Get chart data for visualization."""
    mt5 = get_mt5_interface()
    if not mt5:
        raise HTTPException(status_code=503, detail="MT5 interface not available")
    
    try:
        # Get market data
        data = await mt5.get_historical_data(symbol, "M1", bars)
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Create candlestick chart
        fig = go.Figure(data=go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name=symbol
        ))
        
        # Add Fibonacci levels if available
        engine = get_trading_engine()
        if engine:
            fibonacci_levels = engine.get_fibonacci_levels(symbol)
            if fibonacci_levels and 'retracements' in fibonacci_levels:
                for level_name, level_price in fibonacci_levels['retracements'].items():
                    fig.add_hline(
                        y=level_price,
                        line_dash="dash",
                        annotation_text=f"Fib {level_name}",
                        annotation_position="bottom right"
                    )
        
        fig.update_layout(
            title=f"{symbol} Live Chart",
            xaxis_title="Time",
            yaxis_title="Price",
            height=400
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
    mt5 = get_mt5_interface()
    
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