"""
Research Dashboard API
FastAPI backend for the visual backtesting and research interface.
Runs on port 8001 (separate from the main trading dashboard on 8000).
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from src.data.database import get_database_manager, initialize_database
from src.data.importers import MT4DataImporter, MT5DataImporter
from src.monitoring import get_logger
from src.strategy.backtesting_engine import BacktestingEngine

logger = get_logger("research_api")

# Pydantic models for API requests
class DataRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = None  # No default limit - load all data in range

class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    strategy_name: str = "Fibonacci"
    parameters: Dict[str, Any] = {}

class ReplayRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    current_position: int = 0
    speed: float = 1.0

# FastAPI app
app = FastAPI(
    title="Fibonacci Trading Bot Research Dashboard",
    description="Visual backtesting and strategy research interface",
    version="1.0.0"
)

# Enable CORS for frontend
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
                pass

manager = ConnectionManager()

# Global backtesting engine instance
backtesting_engine = BacktestingEngine()

# Initialize database at startup
try:
    db_manager = initialize_database()
    if db_manager:
        logger.info("Research dashboard database initialized successfully")
    else:
        logger.error("Failed to initialize research dashboard database")
except Exception as e:
    logger.error(f"Database initialization error: {e}")

@app.get("/")
async def get_research_dashboard():
    """Serve the research dashboard HTML."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fibonacci Trading Bot - Research Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                background: #131722;
                color: #d1d4dc;
                overflow: hidden;
                font-size: 12px;
            }
            .header {
                background: #1e222d;
                padding: 8px 16px;
                border-bottom: 1px solid #2a2e39;
                display: flex;
                justify-content: space-between;
                align-items: center;
                height: 44px;
            }
            .logo { 
                font-size: 13px; 
                font-weight: 500; 
                color: #d1d4dc;
                letter-spacing: -0.2px;
            }
            .controls {
                display: flex;
                gap: 12px;
                align-items: center;
            }
            .control-group {
                display: flex;
                gap: 6px;
                align-items: center;
            }
            .control-group label { 
                font-size: 11px; 
                color: #787b86; 
                font-weight: 400;
            }
            select, input { 
                background: #131722; 
                border: 1px solid #2a2e39; 
                color: #d1d4dc; 
                padding: 5px 8px; 
                border-radius: 2px;
                font-size: 11px;
                transition: all 0.2s ease;
                outline: none;
            }
            select:hover, input:hover {
                border-color: #434651;
            }
            select:focus, input:focus {
                border-color: #4a90e2;
            }
            button {
                background: transparent;
                border: 1px solid #2a2e39;
                color: #d1d4dc;
                padding: 5px 10px;
                border-radius: 2px;
                cursor: pointer;
                font-size: 11px;
                height: 26px;
                font-weight: 400;
                transition: all 0.2s ease;
            }
            button:hover { 
                background: #2a2e39; 
                color: #f0f3fa;
            }
            button:active {
                background: #363a45;
            }
            button:disabled { 
                background: transparent; 
                color: #434651; 
                cursor: not-allowed;
                border-color: #2a2e39;
            }
            .main-container {
                display: flex;
                height: calc(100vh - 44px);
            }
            .chart-tools {
                position: absolute;
                top: 12px;
                left: 12px;
                z-index: 1000;
                background: #1e222d;
                border: 1px solid #363a47;
                border-radius: 6px;
                padding: 0;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(10px);
                min-width: 48px;
            }
            .tool-section {
                border-bottom: 1px solid #363a47;
                padding: 6px;
            }
            .tool-section:last-child {
                border-bottom: none;
            }
            .tool-section.horizontal {
                display: flex;
                gap: 2px;
            }
            .tool-btn {
                width: 36px;
                height: 36px;
                border: 1px solid #363a47;
                background: #2a2e39;
                color: #b8bcc5;
                border-radius: 4px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.15s ease;
                position: relative;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 11px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }
            .tool-btn:hover {
                background: #363a47;
                color: #ffffff;
                border-color: #4a90e2;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
            }
            .tool-btn.active {
                background: #4a90e2;
                color: #ffffff;
                border-color: #4a90e2;
                box-shadow: 0 2px 12px rgba(74, 144, 226, 0.3);
            }
            .tool-btn .icon {
                width: 16px;
                height: 16px;
                fill: currentColor;
            }
            .chart-tooltip {
                position: absolute;
                background: rgba(30, 34, 45, 0.95);
                border: 1px solid #434651;
                border-radius: 4px;
                padding: 8px 12px;
                color: #d1d4dc;
                font-size: 12px;
                font-family: 'Segoe UI', monospace;
                pointer-events: none;
                z-index: 1001;
                white-space: nowrap;
                backdrop-filter: blur(5px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                display: none;
            }
            .tooltip-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 2px;
            }
            .tooltip-row:last-child {
                margin-bottom: 0;
            }
            .tooltip-label {
                color: #8b8fa3;
                margin-right: 12px;
            }
            .tooltip-value {
                color: #ffffff;
                font-weight: 500;
            }
            .chart-container {
                flex: 1;
                background: #131722;
                position: relative;
            }
            .sidebar {
                width: 280px;
                background: #1e222d;
                border-left: 1px solid #2a2e39;
                overflow-y: auto;
            }
            .sidebar-section {
                border-bottom: 1px solid #2a2e39;
            }
            .sidebar-section h3 {
                padding: 12px 16px;
                margin: 0;
                font-size: 12px;
                font-weight: 600;
                color: #d1d4dc;
                background: #2a2e39;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .sidebar-section > div:not(h3) {
                padding: 12px 16px;
            }
            #chartDiv {
                width: 100%;
                height: 100%;
                position: relative;
            }
            .chart-loading {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: #666;
                display: none;
            }
            .replay-controls {
                position: fixed !important;
                bottom: 0 !important;
                left: 0 !important;
                right: 0 !important;
                background: #1e222d !important;
                padding: 10px 20px !important;
                display: flex !important;
                gap: 8px !important;
                align-items: center !important;
                justify-content: center !important;
                z-index: 9999 !important;
                border-top: 1px solid #2a2e39 !important;
                height: 60px !important;
                visibility: visible !important;
                opacity: 1 !important;
                user-select: none !important;
            }
            .replay-btn {
                width: 36px;
                height: 36px;
                background: #2a2e39;
                border: 1px solid #434651;
                border-radius: 4px;
                color: #d1d4dc;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                transition: background 0.2s;
            }
            .replay-btn:hover { background: #363a45; }
            .replay-btn:disabled { background: #1a1e27; color: #555a67; cursor: not-allowed; }
            .replay-btn.active { background: #4CAF50; color: white; }
            .progress-bar {
                flex: 1;
                max-width: 400px;
                height: 4px;
                background: #2a2e39;
                border-radius: 2px;
                overflow: hidden;
                margin: 0 16px;
            }
            .progress-fill {
                height: 100%;
                background: #4CAF50;
                width: 0%;
                transition: width 0.1s;
            }
            .progress-text {
                font-size: 11px;
                color: #787b86;
                margin-left: 8px;
                min-width: 60px;
            }
            .status-bar {
                background: #1e222d;
                padding: 5px 15px;
                font-size: 11px;
                color: #787b86;
                text-align: center;
                border-top: 1px solid #2a2e39;
            }
            .loading {
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.8);
                padding: 20px;
                border-radius: 8px;
                z-index: 1000;
            }
            .metric {
                display: flex;
                justify-content: space-between;
                margin-bottom: 4px;
                font-size: 11px;
            }
            .metric-label { color: #787b86; }
            .metric-value { color: #d1d4dc; font-weight: 500; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">🟢 Fibonacci Research Dashboard</div>
            <div class="controls">
                <div class="control-group">
                    <label>Symbol:</label>
                    <select id="symbolSelect" onchange="onSymbolChange()">
                        <option value="DJ30">DJ30 (219,663 bars)</option>
                        <option value="EURUSD">EURUSD (98 bars)</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Timeframe:</label>
                    <select id="timeframeSelect">
                        <option value="M1" selected>M1</option>
                        <option value="M5">M5</option>
                        <option value="M15">M15</option>
                        <option value="H1">H1</option>
                        <option value="H4">H4</option>
                        <option value="D1">D1</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Start:</label>
                    <input type="date" id="startDate" value="2024-11-07">
                </div>
                <div class="control-group">
                    <label>End:</label>
                    <input type="date" id="endDate" value="2024-11-08">
                </div>
                <button onclick="loadData()">Load Data</button>
                <button onclick="runBacktest()">Run Backtest</button>
            </div>
        </div>
        
        <div class="main-container">
            <div class="chart-container" id="chartContainer">
                <div id="chartDiv" style="width: 100%; height: 100%; position: relative;">
                    <!-- Professional Chart Tools Panel -->
                    <div class="chart-tools" id="chartTools">
                        <div class="tool-section">
                            <button class="tool-btn active" id="cursorTool" onclick="selectTool('cursor')" title="Cursor Tool">
                                <svg width="16" height="16" viewBox="0 0 16 16" class="icon">
                                    <path d="M3 2L3 12L6 9L8 11L12 7L10 5L13 2L3 2Z" fill="currentColor"/>
                                </svg>
                            </button>
                        </div>
                        <div class="tool-section">
                            <button class="tool-btn" id="crosshairTool" onclick="selectTool('crosshair')" title="Crosshair Tool">
                                <svg width="16" height="16" viewBox="0 0 16 16" class="icon">
                                    <path d="M8 0V16M0 8H16" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
                                    <circle cx="8" cy="8" r="1.5" stroke="currentColor" stroke-width="1" fill="none"/>
                                </svg>
                            </button>
                        </div>
                        <div class="tool-section horizontal">
                            <button class="tool-btn" onclick="fitChart()" title="Fit Chart">
                                <svg width="16" height="16" viewBox="0 0 16 16" class="icon">
                                    <path d="M2 2H6V6M14 2H10V6M2 14H6V10M14 14H10V10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                                </svg>
                            </button>
                            <button class="tool-btn" onclick="resetZoom()" title="Reset Zoom">
                                <svg width="16" height="16" viewBox="0 0 16 16" class="icon">
                                    <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5" fill="none"/>
                                    <path d="M8 5V11M5 8H11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                </svg>
                            </button>
                        </div>
                        <div class="tool-section">
                            <button class="tool-btn" id="trendlineTool" onclick="selectTool('trendline')" title="Trend Line">
                                <svg width="16" height="16" viewBox="0 0 16 16" class="icon">
                                    <path d="M3 13L13 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                    <circle cx="3" cy="13" r="1.5" fill="currentColor"/>
                                    <circle cx="13" cy="3" r="1.5" fill="currentColor"/>
                                </svg>
                            </button>
                        </div>
                        <div class="tool-section">
                            <button class="tool-btn" onclick="clearDrawings()" title="Clear Drawings">
                                <svg width="16" height="16" viewBox="0 0 16 16" class="icon">
                                    <path d="M3 3L13 13M3 13L13 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <!-- Chart Data Tooltip -->
                    <div class="chart-tooltip" id="chartTooltip">
                        <div class="tooltip-row">
                            <span class="tooltip-label">Time:</span>
                            <span class="tooltip-value" id="tooltipTime">-</span>
                        </div>
                        <div class="tooltip-row">
                            <span class="tooltip-label">O:</span>
                            <span class="tooltip-value" id="tooltipOpen">-</span>
                        </div>
                        <div class="tooltip-row">
                            <span class="tooltip-label">H:</span>
                            <span class="tooltip-value" id="tooltipHigh">-</span>
                        </div>
                        <div class="tooltip-row">
                            <span class="tooltip-label">L:</span>
                            <span class="tooltip-value" id="tooltipLow">-</span>
                        </div>
                        <div class="tooltip-row">
                            <span class="tooltip-label">C:</span>
                            <span class="tooltip-value" id="tooltipClose">-</span>
                        </div>
                    </div>
                </div>
                <div class="chart-loading" id="chartLoading">
                    <h2>📊 Loading Chart...</h2>
                    <p>Preparing TradingView Lightweight Charts</p>
                </div>
                
                <div class="replay-controls" id="replayControls" style="display: none;">
                    <button class="replay-btn" onclick="replayAction('first')">⏮</button>
                    <button class="replay-btn" onclick="replayAction('prev')">⏪</button>
                    <button class="replay-btn" id="playBtn" onclick="togglePlay()">▶️</button>
                    <button class="replay-btn" onclick="replayAction('next')">⏩</button>
                    <button class="replay-btn" onclick="replayAction('last')">⏭</button>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <span class="progress-text" id="positionDisplay">0 / 0</span>
                    <select id="speedSelect" onchange="updateReplaySpeed()">
                        <option value="0.5">0.5x</option>
                        <option value="1" selected>1x</option>
                        <option value="2">2x</option>
                        <option value="5">5x</option>
                        <option value="10">10x</option>
                    </select>
                </div>
            </div>
            
            <div class="sidebar">
                <div class="sidebar-section">
                    <h3>📊 Data Inspector</h3>
                    <div>
                        <div class="metric">
                            <span class="metric-label">Current Bar:</span>
                            <span class="metric-value" id="currentBar">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Timestamp:</span>
                            <span class="metric-value" id="currentTime">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Open:</span>
                            <span class="metric-value" id="currentOpen">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">High:</span>
                            <span class="metric-value" id="currentHigh">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Low:</span>
                            <span class="metric-value" id="currentLow">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Close:</span>
                            <span class="metric-value" id="currentClose">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Volume:</span>
                            <span class="metric-value" id="currentVolume">-</span>
                        </div>
                    </div>
                </div>
                
                <div class="sidebar-section">
                    <h3>🐛 Debug Panel</h3>
                    <div id="debugPanel">
                        <div class="metric">
                            <span class="metric-label">Fractals:</span>
                            <span class="metric-value" id="fractalCount">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Swings:</span>
                            <span class="metric-value" id="swingCount">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Signals:</span>
                            <span class="metric-value" id="signalCount">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Current Strategy:</span>
                            <span class="metric-value" id="currentStrategy">Fibonacci</span>
                        </div>
                    </div>
                </div>
                
                <div class="sidebar-section">
                    <h3>📈 Performance</h3>
                    <div id="performancePanel">
                        <div class="metric">
                            <span class="metric-label">Total Trades:</span>
                            <span class="metric-value" id="totalTrades">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Win Rate:</span>
                            <span class="metric-value" id="winRate">0%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Profit/Loss:</span>
                            <span class="metric-value" id="profitLoss">$0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Max Drawdown:</span>
                            <span class="metric-value" id="maxDrawdown">0%</span>
                        </div>
                    </div>
                </div>
                
                <div class="sidebar-section">
                    <h3>⚙️ Settings</h3>
                    <div id="settingsPanel">
                        <div class="metric">
                            <span class="metric-label">Show Fractals:</span>
                            <input type="checkbox" id="showFractals" checked onchange="refreshChartElements()">
                        </div>
                        <div class="metric">
                            <span class="metric-label">Show Swings:</span>
                            <input type="checkbox" id="showSwings" onchange="refreshChartElements()">
                        </div>
                        <div class="metric">
                            <span class="metric-label">Show Fibonacci:</span>
                            <input type="checkbox" id="showFibonacci" onchange="refreshChartElements()">
                        </div>
                        <div class="metric">
                            <span class="metric-label">Show Signals:</span>
                            <input type="checkbox" id="showSignals" onchange="refreshChartElements()">
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="status-bar" id="statusBar">
            Ready - Select data and click Load Data to begin
        </div>
        
        <div class="loading" id="loadingIndicator">
            <div>Loading data...</div>
        </div>
        
        <!-- TradingView Lightweight Charts Library - Multiple CDNs for reliability -->
        <script>
            // Try multiple CDNs for TradingView charts
            function loadTradingViewCharts() {
                const cdnUrls = [
                    'https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js',
                    'https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js',
                    'https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js'
                ];
                
                let currentCdn = 0;
                
                function tryLoadCdn() {
                    if (currentCdn >= cdnUrls.length) {
                        console.error('❌ Failed to load TradingView charts from all CDNs');
                        updateStatus('Error: TradingView charts library failed to load');
                        return;
                    }
                    
                    const script = document.createElement('script');
                    script.src = cdnUrls[currentCdn];
                    script.onload = function() {
                        console.log('✅ TradingView charts loaded from:', cdnUrls[currentCdn]);
                        initializeApp();
                    };
                    script.onerror = function() {
                        console.warn('⚠️ Failed to load from:', cdnUrls[currentCdn]);
                        currentCdn++;
                        tryLoadCdn();
                    };
                    document.head.appendChild(script);
                }
                
                tryLoadCdn();
            }
            
            // Load charts when page loads
            loadTradingViewCharts();
        </script>
        
        <script>
            // Set default end date to today
            document.getElementById('endDate').value = new Date().toISOString().split('T')[0];
            
            let isPlaying = false;
            let currentPosition = 0;
            let totalBars = 0;
            let marketData = [];
            let playInterval = null;
            let websocket = null;
            let lastRequestSequence = 0; // Track request sequence to ignore stale responses
            let lastLoadAccumulatedCall = 0; // Throttle loadAccumulatedStrategyElements calls
            let lastBackendCall = 0; // Throttle main backend calls
            
            // TradingView Chart variables
            let chart = null;
            let candlestickSeries = null;
            let fractalSeries = null;
            let swingSeries = null;
            let fibonacciSeries = null;
            let signalSeries = null;
            let allMarkers = []; // Global array to store all markers
            
            // User interaction tracking
            let userHasManuallyPanned = false;
            let lastVisibleRange = null;
            let programmaticChange = false;
            
            // Initialize WebSocket connection
            function initWebSocket() {
                try {
                    const wsUrl = `ws://localhost:8001/ws`;
                    websocket = new WebSocket(wsUrl);
                    
                    websocket.onopen = function(event) {
                        console.log('✅ WebSocket connected successfully');
                        updateStatus('WebSocket connected');
                    };
                    
                    websocket.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    };
                    
                    websocket.onclose = function(event) {
                        console.log('⚠️ WebSocket disconnected', event);
                        updateStatus('WebSocket disconnected');
                    };
                    
                    websocket.onerror = function(error) {
                        console.error('❌ WebSocket error:', error);
                        updateStatus('WebSocket error - continuing without real-time updates');
                    };
                } catch (error) {
                    console.error('❌ Failed to initialize WebSocket:', error);
                    updateStatus('WebSocket unavailable - continuing without real-time updates');
                }
            }
            
            function handleWebSocketMessage(data) {
                if (data.type === 'data_update') {
                    marketData = data.data;
                    totalBars = marketData.length;
                    updatePositionDisplay();
                    showReplayControls();
                    updateStatus(`Loaded ${totalBars} bars`);
                } else if (data.type === 'backtest_update' || data.type === 'backtest_jump') {
                    handleBacktestUpdate(data.data);
                } else if (data.type === 'backtest_progress') {
                    updateStatus(`Backtesting: ${data.progress}%`);
                } else if (data.type === 'backtest_complete') {
                    updatePerformanceMetrics(data.results);
                    updateStatus('Backtest complete');
                }
            }
            
            // Global array to store accumulated fractals from real-time detection
            let accumulatedFractals = [];
            
            // ✅ PROPER TRADINGVIEW MARKER MANAGEMENT
            class FractalMarkerManager {
                constructor(candlestickSeries) {
                    this.series = candlestickSeries;
                    this.fractalMarkers = []; // Store all fractal markers
                    this.otherMarkers = []; // Store non-fractal markers
                }
                
                addFractal(fractal) {
                    // Convert fractal to proper TradingView marker format
                    const marker = {
                        time: Math.floor(new Date(fractal.timestamp).getTime() / 1000), // Unix timestamp
                        position: fractal.fractal_type === 'high' ? 'aboveBar' : 'belowBar',
                        color: fractal.fractal_type === 'high' ? '#ff4444' : '#00bcd4',
                        shape: fractal.fractal_type === 'high' ? 'arrowUp' : 'arrowDown', // Fixed directions
                        text: '', // No text for clean display
                        id: `fractal-${fractal.bar_index || fractal.timestamp}`
                    };
                    
                    // Check if marker already exists
                    const existingIndex = this.fractalMarkers.findIndex(m => m.id === marker.id);
                    if (existingIndex === -1) {
                        this.fractalMarkers.push(marker);
                        console.log(`✅ Added ${fractal.fractal_type} fractal marker at ${fractal.timestamp}`);
                    }
                    
                    this.updateChart();
                }
                
                loadAllFractals(fractals) {
                    // Convert all fractals to markers
                    this.fractalMarkers = fractals.map(fractal => ({
                        time: Math.floor(new Date(fractal.timestamp).getTime() / 1000),
                        position: fractal.fractal_type === 'high' ? 'aboveBar' : 'belowBar',
                        color: fractal.fractal_type === 'high' ? '#ff4444' : '#00bcd4',
                        shape: fractal.fractal_type === 'high' ? 'arrowUp' : 'arrowDown',
                        text: '',
                        id: `fractal-${fractal.bar_index || fractal.timestamp}`
                    }));
                    
                    console.log(`📍 Loaded ${this.fractalMarkers.length} fractal markers`);
                    this.updateChart();
                }
                
                clearFractals() {
                    this.fractalMarkers = [];
                    this.updateChart();
                }
                
                updateChart() {
                    // ✅ CRITICAL: Always use complete markers array
                    const allMarkers = [...this.fractalMarkers, ...this.otherMarkers];
                    this.series.setMarkers(allMarkers);
                    console.log(`🎯 Applied ${allMarkers.length} total markers (${this.fractalMarkers.length} fractals)`);
                }
            }
            
            // Global marker manager instance
            let fractalManager = null;
            
            // Simple fractal detection - removed complex logic that caused infinite loops

            // Helper function to load data into backtesting engine
            async function loadBacktestingEngine(symbol, timeframe, startDate, endDate) {
                try {
                    console.log('🔄 Loading backtesting engine with data...', {symbol, timeframe, startDate, endDate});
                    
                    const response = await fetch('/api/backtest/load', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            symbol: symbol,
                            timeframe: timeframe,
                            start_date: startDate,
                            end_date: endDate,
                            limit: null
                        })
                    });
                    
                    if (!response.ok) {
                        console.error('❌ Backtest load failed:', response.status, response.statusText);
                        return false;
                    }
                    
                    const result = await response.json();
                    if (result.success) {
                        console.log('✅ Backtesting engine loaded:', result.total_bars, 'bars');
                        return true;
                    } else {
                        console.error('❌ Backtest load error:', result.message);
                        return false;
                    }
                } catch (error) {
                    console.error('❌ Backtest load exception:', error);
                    return false;
                }
            }
            
            // Handle backtest updates from strategy engine
            function handleBacktestUpdate(data) {
                if (!data) return;
                
                // NOTE: Don't update currentPosition here as it causes position jumps
                // currentPosition is managed by replay controls, not backend responses
                totalBars = data.total_bars;
                
                // Process strategy results and accumulate fractals
                if (data.strategy_results && data.strategy_results.new_fractal) {
                    const newFractal = data.strategy_results.new_fractal;
                    
                    // Check if this fractal is already accumulated
                    const exists = accumulatedFractals.some(f => 
                        f.timestamp === newFractal.timestamp && f.fractal_type === newFractal.fractal_type
                    );
                    
                    if (!exists) {
                        accumulatedFractals.push(newFractal);
                        console.log(`🔺 New fractal detected: ${newFractal.fractal_type} at ${newFractal.timestamp}, total: ${accumulatedFractals.length}`);
                        
                        // Add to chart immediately if fractals are enabled
                        if (document.getElementById('showFractals').checked) {
                            addNewFractalToChart(newFractal);
                        }
                    }
                }
                
                // Update data inspector with current bar
                if (data.current_bar) {
                    const barData = {
                        timestamp: data.timestamp,
                        open: data.current_bar.open,
                        high: data.current_bar.high,
                        low: data.current_bar.low,
                        close: data.current_bar.close,
                        volume: data.current_bar.volume
                    };
                    updateDataInspector(barData, currentPosition);
                }
                
                // Update strategy analysis panels
                if (data.strategy_results) {
                    const results = data.strategy_results;
                    
                    // Update debug panel
                    document.getElementById('fractalCount').textContent = results.total_fractals || 0;
                    document.getElementById('swingCount').textContent = results.total_swings || 0;
                    document.getElementById('signalCount').textContent = results.total_signals || 0;
                    
                    // Show fractal detection info at the beginning
                    if (currentPosition < 10 && results.total_fractals === 0) {
                        updateStatus(`Bar ${currentPosition + 1}/${totalBars} - Need at least 10 bars for first fractal detection (5 before + 5 after)`);
                    }
                    
                    // Add new fractals to chart ONLY if checkbox is checked
                    if (results.new_fractal && document.getElementById('showFractals').checked) {
                        addNewFractalToChart(results.new_fractal);
                    }
                    
                    // Note: Removed redundant loadAccumulatedStrategyElements call here to reduce API load
                    // The main strategy calls in replay functions already handle fractal accumulation
                    
                    // Add new swings to chart ONLY if checkbox is checked
                    if (results.new_swing && document.getElementById('showSwings').checked) {
                        addNewSwingToChart(results.new_swing);
                    }
                    
                    // Add Fibonacci levels to chart ONLY if checkbox is checked
                    if (results.fibonacci_levels && results.fibonacci_levels.length > 0 && document.getElementById('showFibonacci').checked) {
                        addFibonacciLevelsToChart(results.fibonacci_levels);
                    }
                    
                    // Add new signals to chart ONLY if checkbox is checked
                    if (results.new_signals && results.new_signals.length > 0 && document.getElementById('showSignals').checked) {
                        addNewSignalsToChart(results.new_signals);
                    }
                }
                
                // Update performance metrics
                if (data.performance) {
                    updatePerformanceMetrics(data.performance);
                }
                
                // Update position display
                updatePositionDisplay();
                
                // Update status with progress
                const progressPercent = data.progress || (currentPosition / totalBars * 100);
                updateStatus(`Bar ${currentPosition + 1}/${totalBars} (${progressPercent.toFixed(1)}%) - ${data.timestamp || ''}`);
                
                // CRITICAL: Update all markers after processing to preserve fractals
                updateAllMarkers();
                
                // Additional safeguard: Ensure fractals remain visible during playback
                if (document.getElementById('showFractals').checked) {
                    setTimeout(() => {
                        loadAccumulatedStrategyElements(currentPosition);
                    }, 50);
                }
            }
            
            // Initialize TradingView Chart
            function initChart() {
                try {
                    // Check if LightweightCharts is available
                    if (typeof LightweightCharts === 'undefined') {
                        console.error('TradingView LightweightCharts library not loaded!');
                        updateStatus('Error: TradingView library not loaded');
                        return;
                    }

                    const chartContainer = document.getElementById('chartDiv');
                    if (!chartContainer) {
                        console.error('Chart container not found!');
                        updateStatus('Error: Chart container not found');
                        return;
                    }

                    if (chart) {
                        chart.remove();
                    }
                    chart = LightweightCharts.createChart(chartContainer, {
                    width: chartContainer.clientWidth,
                    height: chartContainer.clientHeight,
                    layout: {
                        background: { color: '#1e1e1e' },
                        textColor: '#d1d5db',
                    },
                    grid: {
                        vertLines: { color: '#2d3748' },
                        horzLines: { color: '#2d3748' },
                    },
                    crosshair: {
                        mode: LightweightCharts.CrosshairMode.Normal,
                    },
                    rightPriceScale: {
                        borderColor: '#4a5568',
                        scaleMargins: {
                            top: 0.1,
                            bottom: 0.1,
                        },
                    },
                    timeScale: {
                        borderColor: '#4a5568',
                        timeVisible: true,
                        secondsVisible: false,
                        rightOffset: 20, // Add some right padding
                        barSpacing: 3, // Tighter bar spacing for performance
                        minBarSpacing: 0.5, // Allow tighter zooming
                    },
                    // TradingView Performance Settings
                    handleScroll: true,
                    handleScale: true,
                    trackingMode: {
                        exitMode: LightweightCharts.TrackingModeExitMode.OnNextTap,
                    },
                });
                
                // Create candlestick series
                candlestickSeries = chart.addCandlestickSeries({
                    upColor: '#26a69a',
                    downColor: '#ef5350',
                    borderVisible: false,
                    wickUpColor: '#26a69a',
                    wickDownColor: '#ef5350',
                });
                
                // Create line series for overlays
                fractalSeries = chart.addLineSeries({
                    color: '#ff6b6b',
                    lineWidth: 1,
                    title: 'Fractals',
                });
                
                swingSeries = chart.addLineSeries({
                    color: '#4ecdc4',
                    lineWidth: 2,
                    title: 'Swings',
                });
                
                fibonacciSeries = chart.addLineSeries({
                    color: '#ffe66d',
                    lineWidth: 1,
                    title: 'Fibonacci',
                });
                
                signalSeries = chart.addLineSeries({
                    color: '#ff9ff3',
                    lineWidth: 3,
                    title: 'Signals',
                });
                
                // Track user interactions with chart
                try {
                    // Use the correct API method for tracking visible range changes
                    chart.timeScale().subscribeVisibleTimeRangeChange(() => {
                        // Only mark as user panning if it's not a programmatic change
                        if (!programmaticChange) {
                            setTimeout(() => {
                                userHasManuallyPanned = true;
                            }, 100);
                        }
                    });
                } catch (e) {
                    console.warn('Chart range tracking not available in this version');
                }
                
                // Function to set range programmatically without triggering user panning flag
                window.setProgrammaticRange = function(from, to) {
                    programmaticChange = true;
                    chart.timeScale().setVisibleRange({ from, to });
                    setTimeout(() => {
                        programmaticChange = false;
                    }, 200);
                };
                
                // Reset panning flag when user loads new data
                window.resetChartPanning = function() {
                    userHasManuallyPanned = false;
                };
                
                // Handle resize
                const resizeObserver = new ResizeObserver(entries => {
                    if (chart) {
                        chart.applyOptions({
                            width: chartContainer.clientWidth,
                            height: chartContainer.clientHeight,
                        });
                    }
                });
                resizeObserver.observe(chartContainer);
                
                // Chart click handler for tools and data inspection
                chart.subscribeClick((param) => {
                    if (drawingMode && currentTool === 'trendline') {
                        handleTrendLineClick(param);
                    } else if (param.time) {
                        // Regular data inspection
                        const barIndex = marketData.findIndex(bar => 
                            new Date(bar.timestamp).getTime() / 1000 === param.time
                        );
                        if (barIndex !== -1) {
                            currentPosition = barIndex;
                            updatePositionDisplay();
                            updateDataInspector(marketData[barIndex], barIndex);
                        }
                    }
                });
                
                console.log('Chart initialized successfully!');
                
                // ✅ Initialize proper marker management
                fractalManager = new FractalMarkerManager(candlestickSeries);
                
                // Initialize professional tools system
                selectTool('cursor');
                
                // Show welcome message on empty chart
                if (!marketData || marketData.length === 0) {
                    showWelcomeMessage();
                }
                
            } catch (error) {
                console.error('Error initializing chart:', error);
                updateStatus('Error initializing chart: ' + error.message);
            }
            }
            
            // Update chart with market data (full range - for initial load)
            function updateChart(data) {
                if (!chart || !candlestickSeries) {
                    initChart();
                }

                // Store full market data for progressive replay
                marketData = data;
                totalBars = data.length;

                // Reset panning flag and chart overlays for new data
                userHasManuallyPanned = false;
                allMarkers = []; // Clear all fractal/signal markers
                accumulatedFractals = []; // Clear accumulated fractals for new data

                // FIXED: Clear full chart data cache to force regeneration
                window.fullChartData = null;
                window.currentBacktestPosition = 0;

                // Clear any existing position indicator
                if (window.currentPositionLine) {
                    candlestickSeries.removePriceLine(window.currentPositionLine);
                    window.currentPositionLine = null;
                }

                // Clear any existing markers on the chart
                if (candlestickSeries) {
                    candlestickSeries.setMarkers([]);
                }

                // For backtesting: start at currentPosition (which is set by loadData to user's start date)
                updateChartProgressive(currentPosition);
            }
            
            
            // Progressive chart update for backtesting (shows data up to current position)
            function updateChartProgressive(position) {
                if (!chart || !candlestickSeries || !marketData) return;

                // Convert user position to data array position
                const dataPosition = (window.userStartOffset || 0) + position;
                
                // Ensure we don't go out of bounds
                if (dataPosition >= marketData.length) {
                    console.warn(`Position ${dataPosition} exceeds data length ${marketData.length}`);
                    return;
                }

                // Progressive loading: convert and show only data up to current position
                if (!window.fullChartData) {
                    console.log(`📊 Converting full dataset ${marketData.length} bars for progressive loading...`);
                    window.fullChartData = marketData.map(bar => ({
                        time: Math.floor(new Date(bar.timestamp).getTime() / 1000),
                        open: bar.open,
                        high: bar.high,
                        low: bar.low,
                        close: bar.close
                    }));
                    console.log(`✅ Data ready: ${window.fullChartData.length} bars available`);
                }

                // Progressive approach: Update chart incrementally to avoid jumps
                if (!window.lastChartPosition || window.lastChartPosition > dataPosition) {
                    // Reset needed (first time or going backwards)
                    const progressiveData = window.fullChartData.slice(0, dataPosition + 1);
                    candlestickSeries.setData(progressiveData);
                    console.log(`📊 Chart reset: showing ${progressiveData.length}/${window.fullChartData.length} bars (up to position ${dataPosition})`);
                } else if (window.lastChartPosition < dataPosition) {
                    // Add new bars incrementally to avoid jumping
                    for (let i = window.lastChartPosition + 1; i <= dataPosition; i++) {
                        if (window.fullChartData[i]) {
                            candlestickSeries.update(window.fullChartData[i]);
                        }
                    }
                    console.log(`📊 Incremental update: added ${dataPosition - window.lastChartPosition} bars (now at position ${dataPosition})`);
                }
                
                // Track last position to enable incremental updates
                window.lastChartPosition = dataPosition;
                

                // Store current data position for marker filtering
                window.currentBacktestPosition = dataPosition;

                // Store the time mapping for progressive data only (up to current position)
                window.chartTimeMapping = window.fullChartData.slice(0, dataPosition + 1).map((d, i) => ({
                    index: i,
                    time: d.time,
                    timestamp: marketData[i].timestamp // This correctly maps to the actual market data
                }));

                // Get current visible range before any updates
                const currentRange = chart.timeScale().getVisibleRange();

                // Add current position indicator (vertical line)
                updateCurrentPositionIndicator(dataPosition);

                // Handle auto-scrolling to current position
                if (window.fullChartData && dataPosition < window.fullChartData.length) {
                    const currentTime = window.fullChartData[dataPosition].time;

                    if (position === 0) {
                        // Progressive approach: Show all available data initially (which is limited)
                        const startTime = window.fullChartData[0].time;
                        const endTime = window.fullChartData[dataPosition].time;
                        
                        // Use built-in range setting for progressive data
                        chart.timeScale().setVisibleRange({ from: startTime, to: endTime });
                        userHasManuallyPanned = false;
                        
                        console.log('📏 TradingView optimized view:', {
                            startDate: new Date(startTime * 1000).toISOString().split('T')[0],
                            endDate: new Date(endTime * 1000).toISOString().split('T')[0],
                            showingBars: barsToShow
                        });
                    } else if (!userHasManuallyPanned && currentRange && position > 0) {
                        // Auto-scroll only if user hasn't manually panned and we're not at start
                        // Only scroll if current position is completely outside visible range
                        if (currentTime > currentRange.to) {
                            // Gently scroll to keep current position visible on the right side
                            const rangeWidth = currentRange.to - currentRange.from;
                            if (window.setProgrammaticRange) {
                                window.setProgrammaticRange(
                                    currentTime - rangeWidth * 0.8, // Position current bar at 80% of range
                                    currentTime + rangeWidth * 0.2  // 20% padding on right
                                );
                            }
                        }
                        // Don't auto-scroll backwards to avoid confusion
                    } else if (userHasManuallyPanned && currentRange) {
                        // User has manually positioned chart - preserve their view
                        // Only scroll if current position is way outside their view
                        if (currentTime > currentRange.to + (30 * 60) || currentTime < currentRange.from - (30 * 60)) {
                            // Current position is way outside - gently adjust to show it
                            if (window.setProgrammaticRange) {
                                const adjustment = currentTime > currentRange.to ? (15 * 60) : -(15 * 60);
                                window.setProgrammaticRange(
                                    currentRange.from + adjustment,
                                    currentRange.to + adjustment
                                );
                            }
                        }
                    }
                }

                // Update markers with position filtering
                updateAllMarkers();
            }
            
            // Add fractals to chart
            function addFractalsToChart(fractals) {
                if (!candlestickSeries) return;
                
                // Clear existing fractal markers from allMarkers
                allMarkers = allMarkers.filter(m => !m.shape || (m.shape !== 'arrowDown' && m.shape !== 'arrowUp'));
                
                const fractalMarkers = fractals.map(fractal => ({
                    time: Math.floor(new Date(fractal.timestamp).getTime() / 1000),
                    position: fractal.type === 'high' ? 'aboveBar' : 'belowBar',
                    color: fractal.type === 'high' ? '#ff6b6b' : '#4ecdc4',
                    shape: fractal.type === 'high' ? 'arrowDown' : 'arrowUp',
                    text: '', // No text for clean display
                    size: 1
                }));
                
                // Add new fractal markers to allMarkers
                allMarkers.push(...fractalMarkers);
                
                // Sort markers by time to ensure proper display
                allMarkers.sort((a, b) => a.time - b.time);
                
                // Debug logging
                console.log('Initial fractals loaded:', {
                    count: fractals.length,
                    timestamps: fractals.slice(0, 5).map(f => ({
                        original: f.timestamp,
                        unix: Math.floor(new Date(f.timestamp).getTime() / 1000)
                    })),
                    totalMarkers: allMarkers.length,
                    markerRange: allMarkers.length > 0 ? {
                        first: new Date(allMarkers[0].time * 1000).toISOString(),
                        last: new Date(allMarkers[allMarkers.length - 1].time * 1000).toISOString()
                    } : null
                });
                
                candlestickSeries.setMarkers(allMarkers);
                
                // Debug: Check marker positions after setting
                setTimeout(() => {
                    console.log('Verifying fractal positions after 100ms:', {
                        totalMarkers: allMarkers.length,
                        sampleMarkers: allMarkers.slice(0, 5).map(m => ({
                            time: m.time,
                            date: new Date(m.time * 1000).toISOString(),
                            position: m.position,
                            shape: m.shape
                        }))
                    });
                }, 100);
            }
            
            // Add swings to chart
            function addSwingsToChart(swings) {
                if (!swingSeries) return;
                
                swings.forEach(swing => {
                    const startTime = Math.floor(new Date(swing.start_timestamp).getTime() / 1000);
                    const endTime = Math.floor(new Date(swing.end_timestamp).getTime() / 1000);
                    
                    // Create swing line data
                    const swingData = [
                        { time: startTime, value: swing.start_price },
                        { time: endTime, value: swing.end_price }
                    ];
                    
                    // Add swing line WITHOUT TITLE to avoid text labels
                    const swingLine = chart.addLineSeries({
                        color: swing.direction === 'up' ? '#26a69a' : '#ef5350',
                        lineWidth: 2,
                        // NO TITLE - this prevents text labels on chart
                    });
                    
                    swingLine.setData(swingData);
                });
            }
            
            // Add signals to chart
            function addSignalsToChart(signals) {
                if (!candlestickSeries) return;
                
                // Clear existing signal markers (size 2) from allMarkers
                allMarkers = allMarkers.filter(m => m.size !== 2);
                
                const signalMarkers = signals.map(signal => ({
                    time: Math.floor(new Date(signal.timestamp).getTime() / 1000),
                    position: signal.direction === 'buy' ? 'belowBar' : 'aboveBar',
                    color: signal.direction === 'buy' ? '#26a69a' : '#ef5350',
                    shape: signal.direction === 'buy' ? 'arrowUp' : 'arrowDown',
                    text: '', // No text for clean display
                    size: 2
                }));
                
                // Add new signal markers to allMarkers
                allMarkers.push(...signalMarkers);
                
                // Sort markers by time to ensure proper display
                allMarkers.sort((a, b) => a.time - b.time);
                
                candlestickSeries.setMarkers(allMarkers);
            }
            
            // Dynamic chart update functions for real-time strategy visualization
            
            // ✅ NEW PROPER MARKER SYSTEM
            function updateAllMarkers() {
                if (!fractalManager || !document.getElementById('showFractals').checked) {
                    // Clear fractals if checkbox is unchecked
                    if (fractalManager) {
                        fractalManager.clearFractals();
                    }
                    console.log('Fractals hidden by checkbox');
                    return;
                }

                // Load all accumulated fractals using proper marker management
                if (accumulatedFractals.length > 0) {
                    fractalManager.loadAllFractals(accumulatedFractals);
                }
            }

            // Add current position indicator to show backtesting progress
            function updateCurrentPositionIndicator(position) {
                if (!chart || !window.fullChartData || position >= window.fullChartData.length) return;

                // Remove existing position line if it exists
                if (window.currentPositionLine) {
                    candlestickSeries.removePriceLine(window.currentPositionLine);
                    window.currentPositionLine = null;
                }

                // Add vertical line at current position
                const currentTime = window.fullChartData[position].time;
                const currentPrice = window.fullChartData[position].close;

                // Create a subtle vertical line indicator
                window.currentPositionLine = candlestickSeries.createPriceLine({
                    price: currentPrice,
                    color: '#FFD700', // Gold color
                    lineWidth: 2,
                    lineStyle: 2, // Dashed line
                    axisLabelVisible: true,
                    title: `Current: ${position - (window.userStartOffset || 0) + 1}/${window.fullChartData.length - (window.userStartOffset || 0)}`,
                });
            }

            // Load all accumulated strategy elements for current position
            async function loadAccumulatedStrategyElements(barIndex) {
                try {
                    // Throttle calls to prevent resource exhaustion
                    const now = Date.now();
                    if (now - lastLoadAccumulatedCall < 200) { // Minimum 200ms between calls
                        console.log(`⏳ Throttling loadAccumulatedStrategyElements call for bar ${barIndex}`);
                        return;
                    }
                    lastLoadAccumulatedCall = now;
                    
                    // Use the working jump endpoint which has proper JSON serialization
                    const response = await fetch(`/api/backtest/jump/${barIndex}`, { method: 'POST' });
                    if (response.ok) {
                        const jumpData = await response.json();
                        if (jumpData.success && jumpData.data && jumpData.data.strategy_results) {
                            const results = jumpData.data.strategy_results;
                            
                            // Log the total fractals count
                            console.log(`📊 Strategy results: ${results.total_fractals || 0} total fractals, ${results.total_swings || 0} total swings`);
                            
                            // For now, use loadAllStrategyElements which calls the analyze-all endpoint
                            // This will trigger a full analysis and fractal loading
                            await loadAllStrategyElements();
                            
                            console.log(`Loaded strategy elements for bar ${barIndex}`);
                        }
                    }
                } catch (error) {
                    console.error('Error loading strategy elements:', error);
                }
            }

            function loadAllFractalsToChart(fractals) {
                if (!fractals || !candlestickSeries) return;
                
                // Clear existing fractal markers
                allMarkers = allMarkers.filter(m => !m.shape || (m.shape !== 'arrowDown' && m.shape !== 'arrowUp'));
                
                // Add all accumulated fractals
                fractals.forEach(fractal => {
                    const fractalTime = Math.floor(new Date(fractal.timestamp).getTime() / 1000);
                    
                    const marker = {
                        time: fractalTime,
                        position: fractal.type === 'high' ? 'aboveBar' : 'belowBar',
                        color: fractal.type === 'high' ? '#FF0000' : '#0000FF',
                        shape: fractal.type === 'high' ? 'arrowDown' : 'arrowUp',
                        text: '', // Clean display
                        size: 2
                    };
                    
                    allMarkers.push(marker);
                });
                
                // Sort markers by time
                allMarkers.sort((a, b) => a.time - b.time);
                
                console.log(`Loaded ${fractals.length} accumulated fractals to chart`);
            }

            // ✅ SIMPLIFIED - Use proper marker manager
            function addNewFractalToChart(fractal) {
                if (!fractal || !fractalManager) return;
                
                // Add to accumulated fractals array
                const exists = accumulatedFractals.some(f => 
                    f.timestamp === fractal.timestamp && f.fractal_type === fractal.fractal_type
                );
                
                if (!exists) {
                    accumulatedFractals.push(fractal);
                    fractalManager.addFractal(fractal);
                    console.log(`🔺 DISPLAY: New ${fractal.fractal_type} fractal added to chart at ${fractal.timestamp} (bar ${fractal.bar_index})`);
                    console.log(`🔺 ACCUMULATED: Total fractals now: ${accumulatedFractals.length}`);
                } else {
                    console.log(`⚠️ DUPLICATE: Fractal at ${fractal.timestamp} already exists, skipping`);
                }
            }
            
            function addNewSwingToChart(swing) {
                if (!swing || !chart) return;
                
                const startTime = Math.floor(new Date(swing.start_fractal.timestamp).getTime() / 1000);
                const endTime = Math.floor(new Date(swing.end_fractal.timestamp).getTime() / 1000);
                
                // Create swing line data
                const swingData = [
                    { time: startTime, value: swing.start_fractal.price },
                    { time: endTime, value: swing.end_fractal.price }
                ];
                
                // Add swing line (no title to avoid text clutter)
                const swingLine = chart.addLineSeries({
                    color: swing.direction === 'up' ? '#26a69a' : '#ef5350',
                    lineWidth: 2,
                    // No title to avoid text labels on chart
                });
                
                swingLine.setData(swingData);
                
                console.log(`Added ${swing.direction} swing: ${swing.points.toFixed(1)} points`);
            }
            
            function addFibonacciLevelsToChart(fibLevels) {
                if (!fibLevels || !chart || !document.getElementById('showFibonacci').checked) return;
                
                // Only show key levels (38.2%, 50%, 61.8%) to avoid clutter
                const keyLevels = fibLevels.filter(level => 
                    level.level === 0.382 || level.level === 0.500 || level.level === 0.618
                );
                
                keyLevels.forEach(level => {
                    // Create horizontal line for each key Fibonacci level WITHOUT TITLE
                    const fibLine = chart.addLineSeries({
                        color: getFibonacciColor(level.level),
                        lineWidth: 1,
                        lineStyle: 2, // Dashed line
                        // NO TITLE - this prevents text labels on chart
                    });
                    
                    // Create line data for limited visible range
                    const currentTime = Math.floor(Date.now() / 1000);
                    const fibData = [
                        { time: currentTime - 7200, value: level.price }, // 2 hours ago
                        { time: currentTime + 7200, value: level.price }  // 2 hours ahead
                    ];
                    
                    fibLine.setData(fibData);
                });
                
                console.log(`Added ${keyLevels.length} key Fibonacci levels (filtered from ${fibLevels.length})`);
            }
            
            function getFibonacciColor(level) {
                const colorMap = {
                    0.236: '#e74c3c',  // Red
                    0.382: '#f39c12',  // Orange  
                    0.500: '#f1c40f',  // Yellow
                    0.618: '#27ae60',  // Green
                    0.786: '#3498db'   // Blue
                };
                return colorMap[level] || '#95a5a6'; // Default gray
            }
            
            function addNewSignalsToChart(signals) {
                if (!signals || !candlestickSeries) return;
                
                signals.forEach(signal => {
                    const marker = {
                        time: Math.floor(new Date(signal.timestamp).getTime() / 1000),
                        position: signal.signal_type === 'buy' ? 'belowBar' : 'aboveBar',
                        color: signal.signal_type === 'buy' ? '#26a69a' : '#ef5350',
                        shape: signal.signal_type === 'buy' ? 'arrowUp' : 'arrowDown',
                        text: '', // No text for clean display
                        size: 2
                    };
                    
                    // Check if marker already exists at this timestamp
                    const existingIndex = allMarkers.findIndex(m => m.time === marker.time);
                    if (existingIndex === -1) {
                        allMarkers.push(marker);
                    }
                });
                
                // Sort markers by time to ensure proper display
                allMarkers.sort((a, b) => a.time - b.time);
                
                candlestickSeries.setMarkers(allMarkers);
                
                console.log(`Added ${signals.length} trading signals`);
            }
            
            async function loadData() {
                const symbol = document.getElementById('symbolSelect').value;
                const timeframe = document.getElementById('timeframeSelect').value;
                const startDate = document.getElementById('startDate').value;
                const endDate = document.getElementById('endDate').value;
                
                if (!startDate || !endDate) {
                    alert('Please select start and end dates');
                    return;
                }
                
                // Calculate date range and warn if too large
                const start = new Date(startDate);
                const end = new Date(endDate);
                const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
                
                // Estimate bars (M1 = ~1440 bars/day, H1 = ~24 bars/day)
                const barsPerDay = timeframe === 'M1' ? 1440 : timeframe === 'H1' ? 24 : 288; // Assume M5 default
                const estimatedBars = daysDiff * barsPerDay;
                
                // Simple data size check (TradingView can handle large datasets)
                if (estimatedBars > 100000) {
                    const confirm = window.confirm(
                        `📊 Large Dataset\n\n` +
                        `Loading ${estimatedBars.toLocaleString()} bars (${daysDiff} days)\n\n` +
                        `This may take a moment to load.\n` +
                        `Continue?`
                    );
                    if (!confirm) return;
                }
                
                updateStatus('Loading data...');
                showLoading(true);
                
                try {
                    // Calculate pre-load start date (load extra data before start date for context)
                    const userStartDate = new Date(startDate);
                    const preloadDays = timeframe === 'M1' ? 7 : timeframe === 'H1' ? 30 : 14; // Days to preload
                    const preloadStartDate = new Date(userStartDate.getTime() - (preloadDays * 24 * 60 * 60 * 1000));
                    const preloadStartDateStr = preloadStartDate.toISOString().split('T')[0];

                    const response = await fetch('/api/data', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            symbol: symbol,
                            timeframe: timeframe,
                            start_date: preloadStartDateStr, // Start earlier for context
                            end_date: endDate,
                            limit: null  // Load all data in extended range
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        marketData = result.data;
                        totalBars = marketData.length;

                        // Debug: Log loaded data range
                        if (marketData.length > 0) {
                            console.log(`📊 Loaded data range:`);
                            console.log(`📅 First bar: ${marketData[0].timestamp}`);
                            console.log(`📅 Last bar: ${marketData[marketData.length - 1].timestamp}`);
                            console.log(`📊 Total bars: ${totalBars}`);
                            console.log(`📅 User selected start: ${startDate}`);
                        }

                        // Find the index where user's selected start date begins
                        const userStartIndex = marketData.findIndex(bar =>
                            new Date(bar.timestamp).getTime() >= userStartDate.getTime()
                        );
                        
                        // Store the offset for position mapping
                        window.userStartOffset = Math.max(0, userStartIndex);
                        
                        // Find the index where user's selected end date ends
                        const userEndDate = new Date(endDate + 'T23:59:59'); // End of selected day
                        const userEndIndex = marketData.findIndex(bar =>
                            new Date(bar.timestamp).getTime() > userEndDate.getTime()
                        );
                        
                        // If no bar is found after end date, user can go to the last bar
                        window.userEndOffset = userEndIndex === -1 ? marketData.length - 1 : userEndIndex - 1;
                        
                        // Calculate max user position (in user's perspective)
                        window.maxUserPosition = window.userEndOffset - window.userStartOffset;
                        
                        // User position starts at 0 (their perspective)
                        currentPosition = 0;

                        console.log(`📅 User range: start index ${userStartIndex} to end index ${window.userEndOffset}, max user position: ${window.maxUserPosition}`);
                        console.log(`🔍 Debug start date: ${startDate}, end date: ${endDate}`);
                        console.log(`🔍 Debug userStartDate: ${userStartDate.toISOString()}, userEndDate: ${userEndDate.toISOString()}`);
                        if (marketData[userStartIndex]) {
                            console.log(`🔍 First bar in range: ${marketData[userStartIndex].timestamp}`);
                        }
                        if (marketData[window.userEndOffset]) {
                            console.log(`🔍 Last bar in range: ${marketData[window.userEndOffset].timestamp}`);
                        }

                        // ✅ LOAD BACKTESTING ENGINE - Added at known working point
                        console.log('🔄 Loading backtesting engine NOW...');
                        try {
                            const backtestSuccess = await loadBacktestingEngine(symbol, timeframe, startDate, endDate);
                            if (backtestSuccess) {
                                console.log('✅ Backtesting engine loaded successfully!');
                            } else {
                                console.log('❌ Backtesting engine failed to load');
                            }
                        } catch (error) {
                            console.error('❌ Backtesting engine load error:', error);
                        }

                        console.log('🔄 CHECKPOINT 1: About to hide welcome and update chart...');

                        // Hide welcome message and show chart
                        hideWelcomeMessage();
                        
                        console.log('🔄 CHECKPOINT 2: Welcome hidden, about to update chart...');
                        
                        // Force clear any existing overlays
                        const chartDiv = document.getElementById('chartDiv');
                        const existingOverlays = chartDiv.querySelectorAll('#welcomeOverlay');
                        existingOverlays.forEach(overlay => overlay.remove());
                        
                        // Update chart with new data (will show only up to current position)
                        updateChart(marketData);
                        
                        // Clear all markers when loading new data
                        allMarkers = [];
                        
                        console.log('🚨 DEBUG: About to load backtesting engine...');
                        
                        // FORCE backtesting engine to load data for fractal detection
                        await loadBacktestingEngine(symbol, timeframe, startDate, endDate);
                        
                        // Load data into backtesting engine for interactive analysis
                        console.log('🔄 Loading data into backtesting engine...', {symbol, timeframe, startDate, endDate});
                        const backtestResponse = await fetch('/api/backtest/load', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                symbol: symbol,
                                timeframe: timeframe,
                                start_date: startDate,
                                end_date: endDate,
                                limit: null
                            })
                        });
                        
                        if (!backtestResponse.ok) {
                            console.error('❌ Backtest load request failed:', backtestResponse.status, backtestResponse.statusText);
                            return;
                        }
                        
                        const backtestResult = await backtestResponse.json();
                        console.log('📊 Backtest load response:', backtestResult);
                        if (backtestResult.success) {
                            console.log('✅ Backtesting engine loaded successfully:', backtestResult.total_bars, 'bars');
                        } else {
                            console.warn('⚠️ Failed to load backtesting engine:', backtestResult.message);
                        }
                        
                        // Synchronize backend to the correct start position
                        try {
                            // Use relative position for backend sync (backend has filtered dataset)
                            const relativePosition = currentPosition; // Backend uses 0-based index within the filtered date range
                            console.log(`🔄 Synchronizing backend to relative position ${relativePosition} (user position ${currentPosition})...`);
                            await fetch(`/api/backtest/jump/${relativePosition}`, { method: 'POST' });

                            // Run background analysis to detect fractals
                            console.log('🔄 Running initial fractal analysis...');
                            const analysisResponse = await fetch('/api/backtest/analyze-all', { method: 'POST' });
                            const analysisResult = await analysisResponse.json();
                            if (analysisResult.success) {
                                console.log(`✅ Background analysis complete: ${analysisResult.fractals_detected || 0} fractals detected`);
                                // Load all detected elements for display
                                loadAllStrategyElements();
                            } else {
                                console.warn('⚠️ Fractal analysis failed:', analysisResult.message);
                            }
                        } catch (error) {
                            console.warn('Backend synchronization error:', error);
                            // Fallback: try to load any existing fractals
                            loadAllStrategyElements();
                        }
                        
                        // Update chart to show starting position (position 0)
                        updateChartProgressive(currentPosition);
                        updatePositionDisplay();
                        // Show replay controls (make visible)
                        const replayControls = document.getElementById('replayControls');
                        if (replayControls) {
                            replayControls.style.display = 'flex';
                        }
                        updateStatus(`📊 Loaded ${totalBars.toLocaleString()} bars (${startDate} to ${endDate}) - Ready for analysis!`);

                        // Update data inspector with first bar at user's start position
                        if (marketData.length > 0 && window.userStartOffset < marketData.length) {
                            const dataPosition = window.userStartOffset + currentPosition;
                            updateDataInspector(marketData[dataPosition], currentPosition);
                        }
                        
                        // CRITICAL: Ensure loading indicator is hidden after all setup
                        setTimeout(() => {
                            showLoading(false);
                            // Force hide any remaining loading indicators
                            document.querySelectorAll('#loadingIndicator, #chartLoading, .loading, .chart-loading').forEach(el => {
                                el.style.display = 'none';
                                el.style.visibility = 'hidden';
                                el.style.opacity = '0';
                            });
                            
                            // Ensure tools are properly initialized
                            if (currentTool === 'cursor') {
                                selectTool('cursor');
                            }
                            console.log('🎉 Data loading completed, all systems ready');
                        }, 1000); // Increased timeout to ensure everything is loaded
                    } else {
                        updateStatus(`Error: ${result.message}`);
                    }
                } catch (error) {
                    updateStatus(`Error loading data: ${error.message}`);
                } finally {
                    showLoading(false);
                }
            }
            
            // Refresh chart elements based on settings checkboxes
            function refreshChartElements() {
                console.log('🔄 Refreshing chart elements based on settings...');
                
                if (!chart || !candlestickSeries) {
                    console.warn('Chart not initialized yet');
                    return;
                }
                
                // Simply update markers based on checkbox states - no need to recreate chart
                updateAllMarkers();
                
                console.log('✅ Chart elements refreshed');
            }
            
            // Load all strategy elements from the database (bypassing broken JSON endpoints)
            async function loadAllStrategyElements() {
                try {
                    console.log('🔄 Loading all strategy elements from database...');
                    
                    // Get current symbol and timeframe from form
                    const symbol = document.getElementById('symbolSelect').value;
                    const timeframe = document.getElementById('timeframeSelect').value;
                    const startDate = document.getElementById('startDate').value;
                    const endDate = document.getElementById('endDate').value;
                    
                    // Load fractals directly from database endpoint
                    const fractalsResponse = await fetch(`/api/fractals?symbol=${symbol}&timeframe=${timeframe}&start_date=${startDate}&end_date=${endDate}`);
                    const fractalsResult = await fractalsResponse.json();
                    
                    if (fractalsResult.success && fractalsResult.fractals) {
                        console.log(`📍 Loaded ${fractalsResult.fractals.length} fractals from database`);

                        // Clear existing markers first to avoid duplication
                        allMarkers = [];
                        
                        // Add fractals to chart if checkbox is checked
                        if (fractalsResult.fractals.length > 0 && document.getElementById('showFractals').checked) {
                            console.log('📍 Processing fractals for chart display...');

                            fractalsResult.fractals.forEach(fractal => {
                                const marker = {
                                    time: Math.floor(new Date(fractal.timestamp).getTime() / 1000),
                                    position: fractal.type === 'high' ? 'aboveBar' : 'belowBar',
                                    color: fractal.type === 'high' ? '#ff4444' : '#00bcd4', // Brighter colors
                                    shape: fractal.type === 'high' ? 'arrowDown' : 'arrowUp',
                                    text: '', // No text for clean look
                                    size: 2 // Increase size for visibility
                                };
                                allMarkers.push(marker);
                            });

                            console.log(`📍 Created ${allMarkers.length} fractal markers, setting on chart...`);
                            candlestickSeries.setMarkers(allMarkers);
                        } else {
                            console.log('📍 No fractals to display:', {
                                fractalCount: fractalsResult.fractals?.length || 0,
                                checkboxChecked: document.getElementById('showFractals').checked
                            });
                        }
                    } else {
                        console.log('📍 Failed to load fractals:', fractalsResult.message);
                    }
                    
                    // TODO: Load swings and signals from database endpoints too
                    console.log('✅ Strategy elements loaded from database');
                    
                } catch (error) {
                    console.error('❌ Error loading strategy elements:', error);
                }
            }
            
            // Load chart overlays (fractals, swings, signals) - LEGACY VERSION
            async function loadChartOverlays(symbol, timeframe, startDate, endDate) {
                try {
                    // Load fractals
                    const fractalsResponse = await fetch(`/api/fractals?symbol=${symbol}&timeframe=${timeframe}&start_date=${startDate}&end_date=${endDate}`);
                    const fractalsResult = await fractalsResponse.json();
                    if (fractalsResult.success && document.getElementById('showFractals').checked) {
                        addFractalsToChart(fractalsResult.fractals);
                        document.getElementById('fractalCount').textContent = fractalsResult.count;
                    }
                    
                    // Load swings
                    const swingsResponse = await fetch(`/api/swings?symbol=${symbol}&timeframe=${timeframe}&start_date=${startDate}&end_date=${endDate}`);
                    const swingsResult = await swingsResponse.json();
                    if (swingsResult.success && document.getElementById('showSwings').checked) {
                        addSwingsToChart(swingsResult.swings);
                        document.getElementById('swingCount').textContent = swingsResult.count;
                    }
                    
                    // Load signals
                    const signalsResponse = await fetch(`/api/signals?symbol=${symbol}&start_date=${startDate}&end_date=${endDate}`);
                    const signalsResult = await signalsResponse.json();
                    if (signalsResult.success && document.getElementById('showSignals').checked) {
                        addSignalsToChart(signalsResult.signals);
                        document.getElementById('signalCount').textContent = signalsResult.count;
                    }
                    
                } catch (error) {
                    console.error('Error loading chart overlays:', error);
                }
            }
            
            async function runBacktest() {
                const symbol = document.getElementById('symbolSelect').value;
                const timeframe = document.getElementById('timeframeSelect').value;
                const startDate = document.getElementById('startDate').value;
                const endDate = document.getElementById('endDate').value;
                
                if (!startDate || !endDate) {
                    alert('Please select start and end dates');
                    return;
                }
                
                updateStatus('Running backtest...');
                showLoading(true);
                
                try {
                    const response = await fetch('/api/backtest', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            symbol: symbol,
                            timeframe: timeframe,
                            start_date: startDate,
                            end_date: endDate,
                            strategy_name: 'Fibonacci'
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        updatePerformanceMetrics(result.results);
                        updateStatus(`Backtest complete: ${result.results.total_trades} trades`);
                    } else {
                        updateStatus(`Backtest error: ${result.message}`);
                    }
                } catch (error) {
                    updateStatus(`Backtest error: ${error.message}`);
                } finally {
                    showLoading(false);
                }
            }
            

            async function replayAction(action) {
                if (totalBars === 0) return;

                try {
                    // Use the pre-calculated maximum user position from selected date range
                    const maxUserPosition = window.maxUserPosition || 0;
                    
                    switch(action) {
                        case 'first':
                            currentPosition = 0;
                            break;
                        case 'prev':
                            currentPosition = Math.max(0, currentPosition - 1);
                            break;
                        case 'next':
                            currentPosition = Math.min(maxUserPosition, currentPosition + 1);
                            break;
                        case 'last':
                            currentPosition = maxUserPosition;
                            break;
                    }
                    
                    // Debug: Log current position and data
                    const dataPosition = window.userStartOffset + currentPosition;
                    console.log(`🎮 Replay ${action}: user position ${currentPosition}, data position ${dataPosition}/${totalBars}`);
                    console.log(`🔍 Debug: userStartOffset=${window.userStartOffset}, maxUserPosition=${window.maxUserPosition}, userEndOffset=${window.userEndOffset}`);
                    if (marketData[dataPosition]) {
                        console.log(`📅 Current bar timestamp: ${marketData[dataPosition].timestamp}`);
                    }
                    if (marketData[dataPosition - 1] && action === 'next') {
                        console.log(`📅 Previous bar timestamp: ${marketData[dataPosition - 1].timestamp}`);
                    }

                    // Update chart progressively to show only bars up to current position
                    updateChartProgressive(currentPosition);

                    // Update UI displays
                    updatePositionDisplay();
                    if (marketData[dataPosition]) {
                        updateDataInspector(marketData[dataPosition], currentPosition);
                    }
                    
                    // Call backend for strategy analysis to get real-time fractals/swings (only if needed)
                    try {
                        // SAFETY: Only call backend if any analysis features are enabled
                        if (document.getElementById('showFractals').checked || 
                            document.getElementById('showSwings').checked || 
                            document.getElementById('showFibonacci').checked || 
                            document.getElementById('showSignals').checked) {
                            
                            // Throttle backend calls to prevent resource exhaustion
                            const now = Date.now();
                            if (now - lastBackendCall < 100) { // Minimum 100ms between calls
                                console.log(`⏳ Throttling backend call for position ${currentPosition}`);
                                return;
                            }
                            lastBackendCall = now;
                            
                            // Generate sequence number for this request
                            const requestSequence = ++lastRequestSequence;
                            const expectedDataPosition = dataPosition;
                            
                            // Convert absolute data position to relative position for backend
                            const relativePosition = currentPosition; // Backend should use user's relative position, not absolute data position
                            console.log(`🔄 Calling backend: /api/backtest/jump/${relativePosition} (relative pos ${relativePosition}, was abs pos ${dataPosition}) (seq: ${requestSequence})`);
                            const result = await fetch(`/api/backtest/jump/${relativePosition}`, { method: 'POST' });
                            console.log(`📡 Backend response status: ${result.status} (seq: ${requestSequence})`);
                            const data = await result.json();
                            
                            // Check if this response is still relevant (user might have moved on)
                            const currentDataPosition = window.userStartOffset + currentPosition;
                            if (currentDataPosition !== expectedDataPosition) {
                                console.log(`⚠️ Ignoring stale response: expected position ${expectedDataPosition}, current position ${currentDataPosition} (seq: ${requestSequence})`);
                                return; // Ignore stale response
                            }
                            
                            console.log(`📊 Processing current response:`, data, `(seq: ${requestSequence})`);
                        
                        if (data.success && data.data) {
                            // Update strategy panels with live strategy data
                            if (data.data.strategy_results) {
                                const results = data.data.strategy_results;
                                console.log(`🔍 Strategy results at position ${currentPosition}:`, results);
                                console.log(`🔍 Backend bar_index: ${results.bar_index}, Frontend position: ${currentPosition}`);
                                console.log(`🔍 New fractal:`, results.new_fractal);
                                console.log(`🔍 All result keys:`, Object.keys(results));
                                document.getElementById('fractalCount').textContent = results.total_fractals || 0;
                                document.getElementById('swingCount').textContent = results.total_swings || 0;
                                document.getElementById('signalCount').textContent = results.total_signals || 0;
                                
                                // Real fractal processing will be handled by the backend strategy results
                                // No test fractals needed

                                // Add real-time fractals and swings to chart ONLY if checkboxes are checked
                                if (results.new_fractal && document.getElementById('showFractals').checked) {
                                    console.log(`🎯 TIMING: Adding fractal to chart at frontend position ${currentPosition}, fractal detected at backend bar ${results.bar_index}`);
                                    console.log(`🎯 FRACTAL DETAILS:`, results.new_fractal);
                                    addNewFractalToChart(results.new_fractal);
                                }
                                
                                if (results.new_swing && document.getElementById('showSwings').checked) {
                                    addNewSwingToChart(results.new_swing);
                                }
                                
                                if (results.fibonacci_levels && results.fibonacci_levels.length > 0 && document.getElementById('showFibonacci').checked) {
                                    addFibonacciLevelsToChart(results.fibonacci_levels);
                                }
                                
                                if (results.new_signals && results.new_signals.length > 0 && document.getElementById('showSignals').checked) {
                                    addNewSignalsToChart(results.new_signals);
                                }
                            }
                        }
                        } // End of analysis features check
                    } catch (strategyError) {
                        console.warn('Strategy analysis error:', strategyError);
                    }
                    
                    // Show user position and actual timestamp
                    const userTotalBars = totalBars - window.userStartOffset;
                    updateStatus(`📊 Bar ${currentPosition + 1}/${userTotalBars} - ${marketData[dataPosition]?.timestamp || 'N/A'}`);
                    
                    // Update all markers after replay action
                    updateAllMarkers();
                    
                } catch (error) {
                    console.error('Replay action error:', error);
                    updateStatus(`Error: ${error.message}`);
                }
            }
            
            function togglePlay() {
                if (totalBars === 0) return;
                
                isPlaying = !isPlaying;
                const playBtn = document.getElementById('playBtn');
                
                if (isPlaying) {
                    playBtn.textContent = '⏸️';
                    playBtn.classList.add('active');
                    startReplay();
                } else {
                    playBtn.textContent = '▶️';
                    playBtn.classList.remove('active');
                    stopReplay();
                }
            }
            
            function startReplay() {
                // SAFETY: Clear any existing interval first
                if (playInterval) {
                    clearInterval(playInterval);
                    playInterval = null;
                }
                
                const speed = parseFloat(document.getElementById('speedSelect').value);
                const interval = 1000 / speed; // Base interval of 1 second
                
                playInterval = setInterval(async () => {
                    const maxUserPosition = window.maxUserPosition || 0;
                    if (currentPosition >= maxUserPosition) {
                        togglePlay(); // Auto-stop at end
                        return;
                    }
                    
                    currentPosition++;
                    updateChartProgressive(currentPosition); // Progressive chart update
                    updatePositionDisplay();
                    
                    const dataPosition = window.userStartOffset + currentPosition;
                    updateDataInspector(marketData[dataPosition], currentPosition);
                    
                    // Get real-time strategy analysis during auto-replay (only if backend is loaded)
                    try {
                        // SAFETY: Only call backend if fractals checkbox is checked (user wants live analysis)
                        if (document.getElementById('showFractals').checked) {
                            // Generate sequence number for this auto-replay request
                            const requestSequence = ++lastRequestSequence;
                            const expectedDataPosition = dataPosition;
                            
                            // Use relative position for backend (same fix as manual navigation)
                            const relativePosition = currentPosition;
                            const result = await fetch(`/api/backtest/jump/${relativePosition}`, { method: 'POST' });
                            const data = await result.json();
                            
                            // Check if this response is still relevant for auto-replay
                            const currentDataPosition = window.userStartOffset + currentPosition;
                            if (currentDataPosition !== expectedDataPosition) {
                                console.log(`⚠️ Ignoring stale auto-replay response: expected ${expectedDataPosition}, current ${currentDataPosition} (seq: ${requestSequence})`);
                                return; // Ignore stale response
                            }
                            if (data.success && data.data && data.data.strategy_results) {
                                const results = data.data.strategy_results;
                                document.getElementById('fractalCount').textContent = results.total_fractals || 0;
                                document.getElementById('swingCount').textContent = results.total_swings || 0;
                                document.getElementById('signalCount').textContent = results.total_signals || 0;
                                
                                // Add visual elements during auto-replay ONLY if checkboxes are checked
                                if (results.new_fractal) {
                                    addNewFractalToChart(results.new_fractal);
                                }
                                if (results.new_swing && document.getElementById('showSwings').checked) {
                                    addNewSwingToChart(results.new_swing);
                                }
                                if (results.fibonacci_levels && results.fibonacci_levels.length > 0 && document.getElementById('showFibonacci').checked) {
                                    addFibonacciLevelsToChart(results.fibonacci_levels);
                                }
                                if (results.new_signals && results.new_signals.length > 0 && document.getElementById('showSignals').checked) {
                                    addNewSignalsToChart(results.new_signals);
                                }
                            } else if (!data.success) {
                                // If backend is not loaded, stop auto-replay to prevent infinite loop
                                console.warn('Backend not ready, stopping auto-replay:', data.message);
                                togglePlay(); // Stop auto-replay
                                return;
                            }
                        }
                    } catch (error) {
                        console.warn('Auto-replay strategy analysis error:', error);
                        // Stop auto-replay on errors to prevent infinite loops
                        togglePlay();
                        return;
                    }
                    
                    const userTotalBars = totalBars - window.userStartOffset;
                    updateStatus(`📊 Bar ${currentPosition + 1}/${userTotalBars} - ${marketData[dataPosition]?.timestamp || 'N/A'}`);
                }, interval);
            }
            
            // Function to update replay speed while playing
            function updateReplaySpeed() {
                if (isPlaying && playInterval) {
                    // Restart the interval with new speed
                    stopReplay();
                    startReplay();
                }
            }
            
            
            function stopReplay() {
                if (playInterval) {
                    clearInterval(playInterval);
                    playInterval = null;
                }
                // Reset request sequence to prevent stale responses when replay stops
                lastRequestSequence = 0;
            }
            
            function updatePositionDisplay() {
                const userTotalBars = totalBars - (window.userStartOffset || 0);
                document.getElementById('positionDisplay').textContent = `${currentPosition + 1} / ${userTotalBars}`;
                const progressPercent = userTotalBars > 0 ? (currentPosition / (userTotalBars - 1)) * 100 : 0;
                document.getElementById('progressFill').style.width = `${progressPercent}%`;
            }
            
            function updateDataInspector(barData, position) {
                document.getElementById('currentBar').textContent = position + 1;
                document.getElementById('currentTime').textContent = barData.timestamp || '-';
                document.getElementById('currentOpen').textContent = barData.open ? barData.open.toFixed(5) : '-';
                document.getElementById('currentHigh').textContent = barData.high ? barData.high.toFixed(5) : '-';
                document.getElementById('currentLow').textContent = barData.low ? barData.low.toFixed(5) : '-';
                document.getElementById('currentClose').textContent = barData.close ? barData.close.toFixed(5) : '-';
                document.getElementById('currentVolume').textContent = barData.volume || '0';
            }
            
            function updatePerformanceMetrics(results) {
                document.getElementById('totalTrades').textContent = results.total_trades || 0;
                document.getElementById('winRate').textContent = `${(results.win_rate || 0).toFixed(1)}%`;
                document.getElementById('profitLoss').textContent = `$${(results.total_profit || 0).toFixed(2)}`;
                document.getElementById('maxDrawdown').textContent = `${(results.max_drawdown || 0).toFixed(1)}%`;
            }
            
            
            // Professional Chart Tools System
            let currentTool = 'cursor';
            let drawingMode = false;
            let isTooltipEnabled = false;
            let chartTooltip = null;
            
            // Trend line drawing variables
            let isDrawingTrendLine = false;
            let trendLineStart = null;
            let currentTrendLine = null;
            let trendLines = [];
            
            function selectTool(tool) {
                // Remove active class from all tools
                document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
                
                // Add active class to selected tool
                const toolBtn = document.getElementById(tool + 'Tool');
                if (toolBtn) {
                    toolBtn.classList.add('active');
                }
                
                const previousTool = currentTool;
                currentTool = tool;
                console.log(`🔧 Tool switched: ${previousTool} → ${tool}`);
                
                // Update chart interaction mode
                if (chart) {
                    switch(tool) {
                        case 'cursor':
                            disableTooltip();
                            chart.applyOptions({
                                handleScroll: true,
                                handleScale: true,
                            });
                            updateStatus('Cursor tool active - Click and drag to pan, scroll to zoom');
                            break;
                        case 'crosshair':
                            enableTooltip();
                            chart.applyOptions({
                                handleScroll: true,
                                handleScale: true,
                            });
                            updateStatus('Crosshair tool active - Hover over candles to see data tooltip');
                            break;
                        case 'trendline':
                            disableTooltip();
                            drawingMode = true;
                            updateStatus('Trend line tool active - Click and drag to draw trend lines');
                            console.log('📈 Trend line mode activated');
                            break;
                    }
                }
            }
            
            function enableTooltip() {
                if (chart && !isTooltipEnabled) {
                    chartTooltip = document.getElementById('chartTooltip');
                    isTooltipEnabled = true;
                    
                    // Subscribe to crosshair move events
                    chart.subscribeCrosshairMove(handleCrosshairMove);
                    
                    // Update crosshair visibility
                    chart.applyOptions({
                        crosshair: {
                            mode: LightweightCharts.CrosshairMode.Normal,
                            vertLine: {
                                width: 1,
                                color: '#4a90e2',
                                style: LightweightCharts.LineStyle.Solid,
                            },
                            horzLine: {
                                width: 1,
                                color: '#4a90e2', 
                                style: LightweightCharts.LineStyle.Solid,
                            },
                        },
                    });
                    
                    console.log('✅ Crosshair tooltip enabled with enhanced visibility');
                }
            }
            
            function disableTooltip() {
                if (chartTooltip) {
                    chartTooltip.style.display = 'none';
                }
                isTooltipEnabled = false;
                
                // Reset crosshair to normal
                if (chart) {
                    chart.applyOptions({
                        crosshair: {
                            mode: LightweightCharts.CrosshairMode.Normal,
                            vertLine: {
                                width: 1,
                                color: '#758696',
                                style: LightweightCharts.LineStyle.Dotted,
                            },
                            horzLine: {
                                width: 1,
                                color: '#758696',
                                style: LightweightCharts.LineStyle.Dotted,
                            },
                        },
                    });
                }
                console.log('❌ Crosshair tooltip disabled, normal crosshair restored');
            }
            
            function handleCrosshairMove(param) {
                if (!isTooltipEnabled || !chartTooltip) {
                    if (chartTooltip) chartTooltip.style.display = 'none';
                    return;
                }
                
                if (!param.time || !param.point) {
                    chartTooltip.style.display = 'none';
                    return;
                }
                
                // Find the data point for this time
                const dataPoint = param.seriesData.get(candlestickSeries);
                if (!dataPoint) {
                    chartTooltip.style.display = 'none';
                    return;
                }
                
                // Update tooltip content
                const time = new Date(param.time * 1000);
                document.getElementById('tooltipTime').textContent = time.toLocaleString();
                document.getElementById('tooltipOpen').textContent = dataPoint.open.toFixed(5);
                document.getElementById('tooltipHigh').textContent = dataPoint.high.toFixed(5);
                document.getElementById('tooltipLow').textContent = dataPoint.low.toFixed(5);
                document.getElementById('tooltipClose').textContent = dataPoint.close.toFixed(5);
                
                // Position tooltip near cursor
                const chartRect = document.getElementById('chartDiv').getBoundingClientRect();
                const x = param.point.x + 15; // Offset from cursor
                const y = param.point.y - 10;
                
                // Keep tooltip within chart bounds
                const tooltipRect = chartTooltip.getBoundingClientRect();
                const maxX = chartRect.width - tooltipRect.width - 20;
                const maxY = chartRect.height - tooltipRect.height - 20;
                
                chartTooltip.style.left = Math.min(x, maxX) + 'px';
                chartTooltip.style.top = Math.max(10, Math.min(y, maxY)) + 'px';
                chartTooltip.style.display = 'block';
                
                // Debug logging (remove in production)
                console.log('🎯 Crosshair tooltip updated:', {
                    time: time.toLocaleString(),
                    data: dataPoint,
                    position: { x, y }
                });
            }
            
            function fitChart() {
                if (chart && window.fullChartData && window.fullChartData.length > 0) {
                    const firstTime = window.fullChartData[0].time;
                    const lastTime = window.fullChartData[window.fullChartData.length - 1].time;
                    
                    if (window.setProgrammaticRange) {
                        window.setProgrammaticRange(firstTime, lastTime);
                    }
                    console.log('📏 Chart fitted to all data');
                    updateStatus('Chart fitted to show all data');
                }
            }
            
            function resetZoom() {
                if (chart && window.fullChartData && window.fullChartData.length > 0) {
                    // Reset to initial zoom level (33% of data)
                    const totalBars = window.fullChartData.length;
                    const barsToShow = Math.min(500, Math.max(100, Math.floor(totalBars / 3)));
                    const currentPosition = window.currentBacktestPosition || 0;
                    const currentTime = window.fullChartData[currentPosition].time;
                    
                    const avgTimeStep = (window.fullChartData[totalBars - 1].time - window.fullChartData[0].time) / totalBars;
                    const rangeSeconds = barsToShow * avgTimeStep;
                    
                    if (window.setProgrammaticRange) {
                        window.setProgrammaticRange(
                            Math.max(window.fullChartData[0].time, currentTime - rangeSeconds * 0.1),
                            currentTime + rangeSeconds * 0.9
                        );
                    }
                    console.log('🎯 Zoom reset to default level');
                    updateStatus('Zoom reset to default level');
                }
            }
            
            function clearDrawings() {
                // Clear all trend lines
                if (chart && trendLines.length > 0) {
                    const count = trendLines.length;
                    trendLines.forEach(line => {
                        try {
                            chart.removeSeries(line);
                        } catch (e) {
                            console.warn('Error removing trend line:', e);
                        }
                    });
                    trendLines = [];
                    console.log('🗑️ Cleared all trend lines');
                    updateStatus(`Cleared ${count} trend lines`);
                } else {
                    console.log('🗑️ No trend lines to clear');
                    updateStatus('No drawings to clear');
                }
            }
            
            // Trend line drawing functionality
            function handleTrendLineClick(param) {
                if (!param.time || !param.point) {
                    return;
                }
                
                if (!isDrawingTrendLine) {
                    // Start drawing trend line
                    isDrawingTrendLine = true;
                    trendLineStart = {
                        time: param.time,
                        price: param.point.y ? candlestickSeries.coordinateToPrice(param.point.y) : 0
                    };
                    updateStatus('Click second point to complete trend line');
                    console.log('📈 Trend line started at:', trendLineStart);
                } else {
                    // Complete trend line
                    const trendLineEnd = {
                        time: param.time,
                        price: param.point.y ? candlestickSeries.coordinateToPrice(param.point.y) : 0
                    };
                    
                    // Create trend line
                    createTrendLine(trendLineStart, trendLineEnd);
                    
                    // Reset drawing state
                    isDrawingTrendLine = false;
                    trendLineStart = null;
                    updateStatus('Trend line created - Click to start another or switch tools');
                    console.log('📈 Trend line completed');
                }
            }
            
            function createTrendLine(start, end) {
                if (!chart) return;
                
                try {
                    // Create line series for trend line
                    const trendLine = chart.addLineSeries({
                        color: '#FFD700', // Gold color
                        lineWidth: 2,
                        lineStyle: LightweightCharts.LineStyle.Solid,
                        crosshairMarkerVisible: false,
                        lastValueVisible: false,
                        priceLineVisible: false,
                    });
                    
                    // Set line data
                    const lineData = [
                        { time: start.time, value: start.price },
                        { time: end.time, value: end.price }
                    ];
                    
                    trendLine.setData(lineData);
                    trendLines.push(trendLine);
                    
                    console.log('📈 Trend line created:', {
                        start: { time: new Date(start.time * 1000), price: start.price },
                        end: { time: new Date(end.time * 1000), price: end.price }
                    });
                } catch (error) {
                    console.error('Error creating trend line:', error);
                    updateStatus('Error creating trend line');
                }
            }
            
            // Drag functionality temporarily removed - focusing on core backtesting features
            
            function updateStatus(message) {
                document.getElementById('statusBar').textContent = message;
            }
            
            function showLoading(show) {
                // More aggressive loading indicator hiding
                const loadingSelectors = [
                    '#loadingIndicator',
                    '#chartLoading',
                    '.loading',
                    '.chart-loading'
                ];
                
                loadingSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(element => {
                        if (show) {
                            element.style.display = 'block';
                            element.style.visibility = 'visible';
                            element.style.opacity = '1';
                        } else {
                            element.style.display = 'none';
                            element.style.visibility = 'hidden';
                            element.style.opacity = '0';
                        }
                    });
                });
                
                console.log(show ? '🔄 Loading indicators shown' : '✅ All loading indicators hidden');
            }
            
            function showWelcomeMessage() {
                const chartDiv = document.getElementById('chartDiv');
                
                // Create welcome overlay
                const welcomeOverlay = document.createElement('div');
                welcomeOverlay.id = 'welcomeOverlay';
                welcomeOverlay.style.cssText = `
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    text-align: center;
                    color: #888;
                    font-size: 16px;
                    z-index: 100;
                    padding: 40px;
                    background: rgba(30, 30, 30, 0.8);
                    border-radius: 12px;
                    border: 2px dashed #555;
                    max-width: 500px;
                `;
                
                welcomeOverlay.innerHTML = `
                    <div style="font-size: 48px; margin-bottom: 20px;">📊</div>
                    <h2 style="color: #4CAF50; margin-bottom: 15px;">Interactive Fibonacci Backtesting</h2>
                    <p style="margin-bottom: 20px; line-height: 1.5;">
                        Select a date range and click <strong>"Load Data"</strong> to begin step-by-step strategy analysis.
                    </p>
                    <div style="font-size: 14px; color: #666; line-height: 1.4;">
                        <p>💡 <strong>Tip:</strong> Start with 7-30 days for best performance</p>
                        <p>🎮 Use replay controls to step through bars one by one</p>
                        <p>👀 Watch fractals, swings, and signals appear in real-time</p>
                    </div>
                `;
                
                // Remove existing welcome message
                const existing = document.getElementById('welcomeOverlay');
                if (existing) existing.remove();
                
                chartDiv.appendChild(welcomeOverlay);
            }
            
            function hideWelcomeMessage() {
                console.log('🙈 Hiding welcome message...');
                const welcomeOverlay = document.getElementById('welcomeOverlay');
                if (welcomeOverlay) {
                    welcomeOverlay.remove();
                    console.log('✅ Welcome message hidden');
                } else {
                    console.log('ℹ️ No welcome message to hide');
                }
            }
            
            
            // Load available symbols from database
            async function loadAvailableSymbols() {
                try {
                    const response = await fetch('/api/symbols');
                    const data = await response.json();
                    
                    if (data.success && data.symbols.length > 0) {
                        const symbolSelect = document.getElementById('symbolSelect');
                        const timeframeSelect = document.getElementById('timeframeSelect');
                        
                        // Clear existing options
                        symbolSelect.innerHTML = '';
                        
                        // Add symbols to dropdown
                        data.symbols.forEach(symbolData => {
                            const option = document.createElement('option');
                            option.value = symbolData.symbol;
                            option.textContent = `${symbolData.symbol} (${symbolData.total_bars} bars)`;
                            symbolSelect.appendChild(option);
                        });
                        
                        // Store symbols data for timeframe updates
                        window.symbolsData = data.symbols;
                        
                        // Update timeframes for first symbol
                        if (data.symbols.length > 0) {
                            updateTimeframes(data.symbols[0].symbol);
                        }
                        
                        updateStatus(`Loaded ${data.symbols.length} symbols from database`);
                    } else {
                        updateStatus('No symbols found in database');
                    }
                } catch (error) {
                    console.error('Error loading symbols:', error);
                    updateStatus('Error loading symbols from database');
                }
            }
            
            // Update timeframes based on selected symbol
            function updateTimeframes(selectedSymbol) {
                const timeframeSelect = document.getElementById('timeframeSelect');
                if (!window.symbolsData) {
                    console.warn('symbolsData not loaded yet');
                    return;
                }
                const symbolData = window.symbolsData.find(s => s.symbol === selectedSymbol);
                
                if (symbolData) {
                    // Clear existing options
                    timeframeSelect.innerHTML = '';
                    
                    // Add available timeframes
                    symbolData.timeframes.forEach(tf => {
                        const option = document.createElement('option');
                        option.value = tf.timeframe;
                        option.textContent = `${tf.timeframe} (${tf.bars} bars)`;
                        timeframeSelect.appendChild(option);
                    });
                }
            }
            
            // Handle symbol change
            function onSymbolChange() {
                const symbolSelect = document.getElementById('symbolSelect');
                updateTimeframes(symbolSelect.value);
                updateDateRangeForSymbol();
            }
            
            // Update date range based on selected symbol
            function updateDateRangeForSymbol() {
                const symbolSelect = document.getElementById('symbolSelect');
                const timeframeSelect = document.getElementById('timeframeSelect');
                const selectedSymbol = symbolSelect.value;
                const selectedTimeframe = timeframeSelect.value;
                
                // Find date range for selected symbol/timeframe
                if (window.symbolsData && window.symbolsData.length > 0) {
                    const symbolData = window.symbolsData.find(s => s.symbol === selectedSymbol);
                    if (symbolData && symbolData.timeframes) {
                        const timeframeData = symbolData.timeframes.find(tf => tf.timeframe === selectedTimeframe);
                        if (timeframeData) {
                            // Extract just the date part (yyyy-MM-dd) from potential datetime strings
                            const startDateOnly = timeframeData.start_date.split(' ')[0].split('T')[0];
                            const endDateOnly = timeframeData.end_date.split(' ')[0].split('T')[0];
                            
                            document.getElementById('startDate').value = startDateOnly;
                            document.getElementById('endDate').value = endDateOnly;
                            
                            updateStatus(`📊 ${selectedSymbol} ${selectedTimeframe}: ${startDateOnly} to ${endDateOnly} (${timeframeData.bars?.toLocaleString()} bars available)`);
                            return;
                        }
                    }
                }
                
                // Fallback: use DJ30 default range (proper format)
                document.getElementById('startDate').value = '2024-11-07';
                document.getElementById('endDate').value = '2025-06-16';
                updateStatus(`📊 Ready for analysis! Select dates and click "Load Data" to begin.`);
            }

            // Initialize app after TradingView library loads
            function initializeApp() {
                console.log('✅ Initializing application...');
                try {
                    initChart();
                    console.log('✅ Chart initialized successfully');
                    
                    initWebSocket();
                    console.log('✅ WebSocket initialized');
                    
                    loadAvailableSymbols();
                    console.log('✅ Loading symbols...');
                    
                    loadAvailableDateRanges();
                    console.log('✅ Loading date ranges...');
                    
                    // Show welcome message on initial load
                    showWelcomeMessage();
                    console.log('✅ Welcome message shown');
                    
                    // Status will be updated by loadAvailableDateRanges()
                } catch (error) {
                    console.error('❌ Error during app initialization:', error);
                    updateStatus('Error: Failed to initialize dashboard');
                }
            }
            
            // Load available date ranges for user selection (no auto-loading)
            async function loadAvailableDateRanges() {
                try {
                    const response = await fetch('/api/date-ranges');
                    const data = await response.json();
                    
                    if (data.success && data.ranges.length > 0) {
                        // Set date range based on currently selected symbol
                        updateDateRangeForSymbol();
                        updateStatus(`📊 Ready for analysis! Select dates and click "Load Data" to begin interactive backtesting.`);
                    }
                } catch (error) {
                    console.error('Error loading date ranges:', error);
                    updateStatus('📅 Please select date range and click "Load Data" to start');
                }
            }
            
            // Initialize on page load (fallback if TradingView doesn't load)
            window.onload = function() {
                // Check if TradingView loaded
                if (typeof LightweightCharts !== 'undefined') {
                    initializeApp();
                } else {
                    updateStatus('Waiting for TradingView charts to load...');
                    loadAvailableSymbols();
                    loadAvailableDateRanges();
                    showWelcomeMessage(); // Only show if charts don't load
                }
            };
            
            // Cleanup on page unload
            // Clean up any existing intervals on page load/reload
            window.addEventListener('load', function() {
                // Force stop any running intervals from previous session
                if (playInterval) {
                    clearInterval(playInterval);
                    playInterval = null;
                }
                isPlaying = false;
                const playBtn = document.getElementById('playBtn');
                if (playBtn) {
                    playBtn.textContent = '▶️';
                    playBtn.classList.remove('active');
                }
                console.log('🧹 Page loaded: cleaned up any leftover intervals');
            });

            window.onbeforeunload = function() {
                if (websocket) {
                    websocket.close();
                }
                stopReplay();
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(
        content=html_content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.post("/api/data")
async def get_market_data(request: DataRequest):
    """Get historical market data for visualization."""
    try:
        db_manager = get_database_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Parse dates
        start_date = None
        end_date = None
        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date)
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date)
        
        # Get historical data
        df = db_manager.get_historical_data(
            request.symbol, 
            request.timeframe, 
            start_date, 
            end_date, 
            request.limit
        )
        
        if df.empty:
            return JSONResponse({
                "success": False,
                "message": f"No data found for {request.symbol} {request.timeframe}"
            })
        
        # Convert to list of dictionaries for JSON response
        data = []
        for timestamp, row in df.iterrows():
            data.append({
                "timestamp": timestamp.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            })
        
        logger.info(f"Served {len(data)} bars for {request.symbol} {request.timeframe}")
        
        return JSONResponse({
            "success": True,
            "data": data,
            "count": len(data),
            "symbol": request.symbol,
            "timeframe": request.timeframe
        })
        
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint."""
    return {"message": "Test endpoint working!"}

@app.get("/api/symbols")
async def get_available_symbols():
    """Get available symbols from database."""
    try:
        # Query database for distinct symbols
        with db_manager.get_session() as session:
            from sqlalchemy import text
            
            # Get distinct symbols and their available timeframes
            result = session.execute(text("""
                SELECT DISTINCT symbol, timeframe, COUNT(*) as bar_count,
                       MIN(timestamp) as start_date, MAX(timestamp) as end_date
                FROM historical_data 
                GROUP BY symbol, timeframe 
                ORDER BY symbol, timeframe
            """))
            
            symbols_data = {}
            for row in result:
                symbol = row.symbol
                if symbol not in symbols_data:
                    symbols_data[symbol] = {
                        "symbol": symbol,
                        "timeframes": [],
                        "total_bars": 0
                    }
                
                symbols_data[symbol]["timeframes"].append({
                    "timeframe": row.timeframe,
                    "bars": row.bar_count,
                    "start_date": row.start_date.isoformat() if hasattr(row.start_date, 'isoformat') else str(row.start_date) if row.start_date else None,
                    "end_date": row.end_date.isoformat() if hasattr(row.end_date, 'isoformat') else str(row.end_date) if row.end_date else None
                })
                symbols_data[symbol]["total_bars"] += row.bar_count
            
            symbols_list = list(symbols_data.values())
            
            logger.info(f"Found {len(symbols_list)} symbols with data")
            
            return JSONResponse({
                "success": True,
                "symbols": symbols_list,
                "count": len(symbols_list)
            })
    
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e),
            "symbols": []
        })

@app.get("/api/date-ranges")
async def get_available_date_ranges():
    """Get available date ranges from database for auto-selection."""
    try:
        db_manager = get_database_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
            
        with db_manager.get_session() as session:
            from sqlalchemy import text
            
            # Get date ranges for each symbol/timeframe combination
            result = session.execute(text("""
                SELECT symbol, timeframe, 
                       MIN(timestamp) as start_date, 
                       MAX(timestamp) as end_date,
                       COUNT(*) as total_bars
                FROM historical_data 
                GROUP BY symbol, timeframe 
                ORDER BY MAX(timestamp) DESC, symbol, timeframe
            """))
            
            ranges = []
            for row in result:
                # Handle both datetime and string date formats
                start_date = None
                end_date = None
                
                if row.start_date:
                    if hasattr(row.start_date, 'strftime'):
                        start_date = row.start_date.strftime('%Y-%m-%d')
                    else:
                        start_date = str(row.start_date)[:10]  # Take first 10 chars (YYYY-MM-DD)
                        
                if row.end_date:
                    if hasattr(row.end_date, 'strftime'):
                        end_date = row.end_date.strftime('%Y-%m-%d')
                    else:
                        end_date = str(row.end_date)[:10]  # Take first 10 chars (YYYY-MM-DD)
                
                ranges.append({
                    "symbol": row.symbol,
                    "timeframe": row.timeframe,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_bars": row.total_bars
                })
            
            logger.info(f"Found {len(ranges)} date ranges")
            
            return JSONResponse({
                "success": True,
                "ranges": ranges,
                "count": len(ranges)
            })
            
    except Exception as e:
        logger.error(f"Error getting date ranges: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e),
            "ranges": []
        })

@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """Run a backtest and return results."""
    try:
        db_manager = get_database_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        # For now, return mock results
        # TODO: Integrate with actual backtesting engine
        mock_results = {
            "total_trades": 45,
            "winning_trades": 28,
            "losing_trades": 17,
            "win_rate": 62.2,
            "total_profit": 347.50,
            "max_drawdown": 8.3,
            "profit_factor": 1.68,
            "sharpe_ratio": 1.24
        }
        
        # Store backtest run in database
        run_data = {
            "strategy_name": request.strategy_name,
            "strategy_version": "1.0.0",
            "date_range_start": start_date,
            "date_range_end": end_date,
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "parameters": json.dumps(request.parameters),
            **mock_results
        }
        
        run_id = db_manager.store_backtest_run(run_data)
        
        logger.info(f"Backtest completed for {request.symbol} {request.timeframe}: {run_id}")
        
        return JSONResponse({
            "success": True,
            "results": mock_results,
            "run_id": run_id
        })
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/fractals")
async def get_fractals(
    symbol: str = Query(...),
    timeframe: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get fractals for the chart overlay."""
    try:
        db_manager = get_database_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Parse dates
        start = None
        end = None
        if start_date:
            start = datetime.fromisoformat(start_date)
        if end_date:
            end = datetime.fromisoformat(end_date)
        
        # Get fractals from database
        fractals = db_manager.get_fractals(symbol, timeframe, start, end)
        
        # Convert to JSON-serializable format
        fractal_data = []
        for fractal in fractals:
            fractal_data.append({
                "id": fractal.id,
                "timestamp": fractal.timestamp.isoformat(),
                "type": fractal.fractal_type,
                "price": float(fractal.price),
                "strength": fractal.strength,
                "is_valid": fractal.is_valid
            })
        
        return JSONResponse({
            "success": True,
            "fractals": fractal_data,
            "count": len(fractal_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting fractals: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/swings")
async def get_swings(
    symbol: str = Query(...),
    timeframe: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    dominant_only: bool = Query(False)
):
    """Get swings for the chart overlay."""
    try:
        db_manager = get_database_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Parse dates
        start = None
        end = None
        if start_date:
            start = datetime.fromisoformat(start_date)
        if end_date:
            end = datetime.fromisoformat(end_date)
        
        # Get swings from database
        swings = db_manager.get_swings(symbol, timeframe, start, end, dominant_only)
        
        # Convert to JSON-serializable format
        swing_data = []
        for swing in swings:
            fibonacci_levels = []
            if swing.fibonacci_levels:
                try:
                    fibonacci_levels = json.loads(swing.fibonacci_levels)
                except:
                    pass
            
            swing_data.append({
                "id": swing.id,
                "start_timestamp": swing.start_timestamp.isoformat(),
                "end_timestamp": swing.end_timestamp.isoformat(),
                "start_price": float(swing.start_price),
                "end_price": float(swing.end_price),
                "direction": swing.direction,
                "magnitude_pips": float(swing.magnitude_pips),
                "magnitude_percent": float(swing.magnitude_percent),
                "fibonacci_levels": fibonacci_levels,
                "is_dominant": swing.is_dominant
            })
        
        return JSONResponse({
            "success": True,
            "swings": swing_data,
            "count": len(swing_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting swings: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/signals")
async def get_signals(
    symbol: str = Query(...),
    timeframe: str = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    backtest_run_id: Optional[str] = Query(None)
):
    """Get trading signals for the chart overlay."""
    try:
        db_manager = get_database_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Parse dates
        start = None
        end = None
        if start_date:
            start = datetime.fromisoformat(start_date)
        if end_date:
            end = datetime.fromisoformat(end_date)
        
        # Get signals from database
        signals = db_manager.get_signals(backtest_run_id, symbol, start, end)
        
        # Convert to JSON-serializable format
        signal_data = []
        for signal in signals:
            signal_data.append({
                "id": signal.id,
                "timestamp": signal.timestamp.isoformat(),
                "signal_type": signal.signal_type,
                "direction": signal.direction,
                "price": float(signal.price),
                "fibonacci_level": float(signal.fibonacci_level) if signal.fibonacci_level else None,
                "confidence": float(signal.confidence) if signal.confidence else None,
                "outcome": signal.outcome,
                "profit_loss_pips": float(signal.profit_loss_pips) if signal.profit_loss_pips else None
            })
        
        return JSONResponse({
            "success": True,
            "signals": signal_data,
            "count": len(signal_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/backtest-runs")
async def get_backtest_runs(
    symbol: Optional[str] = Query(None),
    strategy_name: Optional[str] = Query(None),
    limit: int = Query(50)
):
    """Get list of backtest runs."""
    try:
        db_manager = get_database_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")
        
        runs = db_manager.get_backtest_runs(symbol, strategy_name, limit)
        
        # Convert to JSON-serializable format
        run_data = []
        for run in runs:
            run_data.append({
                "id": run.id,
                "run_date": run.run_date.isoformat(),
                "strategy_name": run.strategy_name,
                "strategy_version": run.strategy_version,
                "symbol": run.symbol,
                "timeframe": run.timeframe,
                "date_range_start": run.date_range_start.isoformat(),
                "date_range_end": run.date_range_end.isoformat(),
                "total_trades": run.total_trades,
                "win_rate": float(run.win_rate),
                "total_profit": float(run.total_profit),
                "max_drawdown": float(run.max_drawdown)
            })
        
        return JSONResponse({
            "success": True,
            "runs": run_data,
            "count": len(run_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting backtest runs: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

# =====================================
# INTERACTIVE BACKTESTING ENDPOINTS
# =====================================

@app.post("/api/backtest/load")
async def load_backtest_data(request: DataRequest):
    """Load data into backtesting engine for interactive analysis."""
    try:
        logger.info(f"🔄 Loading backtest data: {request.symbol} {request.timeframe} from {request.start_date} to {request.end_date}")
        
        db_manager = get_database_manager()
        if not db_manager:
            logger.error("Database manager not available")
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Parse dates
        start_date = None
        end_date = None
        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date)
            logger.info(f"📅 Parsed start date: {start_date}")
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date)
            logger.info(f"📅 Parsed end date: {end_date}")
        
        # Get historical data
        logger.info(f"📊 Fetching data from database...")
        df = db_manager.get_historical_data(
            request.symbol, 
            request.timeframe, 
            start_date, 
            end_date, 
            request.limit
        )
        
        logger.info(f"📊 Database returned {len(df)} rows")
        
        if df.empty:
            logger.warning(f"No data found for {request.symbol} {request.timeframe}")
            return JSONResponse({
                "success": False,
                "message": f"No data found for {request.symbol} {request.timeframe}"
            })
        
        # Load data into backtesting engine
        logger.info(f"🔄 Loading {len(df)} bars into backtesting engine...")
        try:
            backtesting_engine.load_data(df)
            logger.info(f"✅ Successfully loaded {len(df)} bars into backtesting engine")
        except Exception as e:
            logger.error(f"❌ Failed to load data into backtesting engine: {e}")
            raise
        
        return JSONResponse({
            "success": True,
            "message": f"Loaded {len(df)} bars for interactive backtesting",
            "total_bars": len(df),
            "date_range": {
                "start": df.index[0].isoformat(),
                "end": df.index[-1].isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error loading backtest data: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.post("/api/backtest/next")
async def process_next_bar():
    """Process next bar in backtesting sequence."""
    try:
        # Check if backtesting engine has data loaded
        if backtesting_engine.data is None:
            return JSONResponse({
                "success": False,
                "message": "Backtesting engine not loaded with data. Please load data first."
            })
        
        result = backtesting_engine.process_next_bar()
        
        if 'error' in result:
            return JSONResponse({
                "success": False,
                "message": result['error']
            })
        
        # Broadcast update to connected WebSocket clients
        await manager.broadcast(json.dumps({
            "type": "backtest_update",
            "data": result
        }))
        
        return JSONResponse({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Error processing next bar: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.post("/api/backtest/analyze-all")
async def analyze_all_data():
    """Run fractal analysis on all loaded data without changing current position."""
    try:
        # Save current position
        current_pos = backtesting_engine.current_bar_index

        # Temporarily process all data to detect fractals
        total_bars = backtesting_engine.total_bars
        if total_bars > 0:
            # Jump to end to process all data
            result = backtesting_engine.jump_to_bar(total_bars - 1)

            # Get the detected fractals count
            strategy_state = backtesting_engine.strategy.get_current_state()
            fractals_detected = len(strategy_state.get('fractals', []))

            # Restore original position
            backtesting_engine.jump_to_bar(current_pos)

            return JSONResponse({
                "success": True,
                "fractals_detected": fractals_detected,
                "message": f"Analyzed {total_bars} bars, detected {fractals_detected} fractals"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "No data loaded"
            })

    except Exception as e:
        logger.error(f"Error analyzing all data: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.post("/api/backtest/jump/{bar_index}")
async def jump_to_bar(bar_index: int):
    """Jump to specific bar index."""
    try:
        # Check if backtesting engine has data loaded
        if backtesting_engine.data is None:
            return JSONResponse({
                "success": False,
                "message": "Backtesting engine not loaded with data. Please load data first."
            })
        
        result = backtesting_engine.jump_to_bar(bar_index)
        
        if 'error' in result:
            return JSONResponse({
                "success": False,
                "message": result['error']
            })
        
        # Broadcast update to connected WebSocket clients
        await manager.broadcast(json.dumps({
            "type": "backtest_jump",
            "data": result
        }))
        
        return JSONResponse({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Error jumping to bar: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/backtest/strategy-state")
async def get_strategy_state(bar_index: Optional[int] = None):
    """Get current strategy state with all accumulated elements."""
    try:
        # Get strategy state from the backtesting engine
        if hasattr(backtesting_engine, 'strategy') and backtesting_engine.strategy:
            strategy_state = backtesting_engine.strategy.get_current_state()
            
            return JSONResponse({
                "success": True,
                "state": strategy_state,
                "bar_index": bar_index or backtesting_engine.current_bar_index
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Strategy not initialized"
            })
        
    except Exception as e:
        logger.error(f"Error getting strategy state: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/backtest/state")
async def get_backtest_state():
    """Get current backtesting state."""
    try:
        state = backtesting_engine.get_current_state()
        
        return JSONResponse({
            "success": True,
            "state": state
        })
        
    except Exception as e:
        logger.error(f"Error getting backtest state: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.post("/api/backtest/reset")
async def reset_backtest():
    """Reset backtesting engine to beginning."""
    try:
        backtesting_engine.reset()
        
        return JSONResponse({
            "success": True,
            "message": "Backtesting engine reset"
        })
        
    except Exception as e:
        logger.error(f"Error resetting backtest: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)