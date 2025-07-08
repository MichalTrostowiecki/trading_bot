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
from sqlalchemy import text

logger = get_logger("research_api")

# Pydantic models for API requests
class DataRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = None  # No default limit - load all data in range
    fractal_periods: Optional[int] = 5  # Configurable fractal detection periods
    lookback_candles: Optional[int] = 140  # Configurable lookback period for swing analysis

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
                cursor: pointer;
                user-select: none;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .sidebar-section h3:hover {
                background: #363b47;
            }
            .sidebar-section .collapse-icon {
                font-size: 10px;
                transition: transform 0.2s;
            }
            .sidebar-section.collapsed .collapse-icon {
                transform: rotate(-90deg);
            }
            .sidebar-section.collapsed .section-content {
                display: none;
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
                <button onclick="emergencyStopAllUpdates()" style="background-color: #ff4444; border-color: #ff4444; color: white;" title="Stop all automatic updates and chart flashing">🛑 Stop</button>
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
                    <h3 onclick="toggleSection(this)">📊 Data Inspector <span class="collapse-icon">▼</span></h3>
                    <div class="section-content">
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
                    <h3 onclick="toggleSection(this)">🎯 Market Bias <span class="collapse-icon">▼</span></h3>
                    <div class="section-content" id="marketBiasPanel">
                        <div class="metric">
                            <span class="metric-label">Sentiment:</span>
                            <span class="metric-value" id="marketSentiment">NEUTRAL</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Direction:</span>
                            <span class="metric-value" id="marketDirection">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Points:</span>
                            <span class="metric-value" id="dominantPoints">0</span>
                        </div>
                        <div class="metric" style="margin-top: 8px;">
                            <span class="metric-label" style="font-weight: bold;">Trading Direction:</span>
                        </div>
                        <div class="metric" style="margin-top: 4px;">
                            <span class="metric-value" id="tradingDirection" style="color: #FFD700; font-weight: bold; font-size: 10px;">Wait for setup</span>
                        </div>
                    </div>
                </div>
                
                <div class="sidebar-section">
                    <h3 onclick="toggleSection(this)">🐛 Debug Panel <span class="collapse-icon">▼</span></h3>
                    <div class="section-content" id="debugPanel">
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
                            <span class="metric-label">Enhanced Signals:</span>
                            <span class="metric-value" id="enhancedSignalCount">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">ABC Patterns:</span>
                            <span class="metric-value" id="abcPatternCount">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Current Strategy:</span>
                            <span class="metric-value" id="currentStrategy">Fibonacci</span>
                        </div>
                    </div>
                </div>
                
                <div class="sidebar-section collapsed">
                    <h3 onclick="toggleSection(this)">📈 Performance <span class="collapse-icon">▼</span></h3>
                    <div class="section-content" id="performancePanel">
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
                    <h3 onclick="toggleSection(this)">⚙️ Settings <span class="collapse-icon">▼</span></h3>
                    <div class="section-content" id="settingsPanel">
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
                            <input type="checkbox" id="showFibonacci" checked onchange="refreshChartElements()">
                        </div>
                        <div class="metric">
                            <span class="metric-label">Show ABC Patterns:</span>
                            <input type="checkbox" id="showABC" onchange="refreshChartElements()">
                        </div>
                        <div class="metric">
                            <span class="metric-label">Show Signals:</span>
                            <input type="checkbox" id="showSignals" onchange="refreshChartElements()">
                        </div>
                        <div class="metric">
                            <span class="metric-label">Show Enhanced Signals:</span>
                            <input type="checkbox" id="showEnhancedSignals" checked onchange="refreshChartElements()">
                        </div>
                        <div class="metric">
                            <span class="metric-label">Fractal Periods:</span>
                            <input type="number" id="fractalPeriods" min="1" max="50" value="5" onchange="refreshChartElements()" style="width: 60px;" title="Number of bars before AND after the high/low point for fractal validation. Period N = N bars delay after actual turning point.">
                        </div>
                        <div class="metric" style="font-size: 0.8em; color: #666; margin-top: 5px;">
                            <span>ℹ️ Fractal detection requires N bars after the high/low point for confirmation</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Lookback Candles:</span>
                            <input type="number" id="lookbackCandles" min="50" max="500" value="140" onchange="refreshChartElements()" style="width: 70px;" title="Number of candles to look back for swing analysis. Strategy only considers swings within this period.">
                        </div>
                        <div class="metric" style="font-size: 0.8em; color: #666; margin-top: 5px;">
                            <span>📊 Only swings within lookback period are considered for dominance</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Show Lookback Line:</span>
                            <input type="checkbox" id="showLookbackLine" onchange="refreshChartElements()">
                        </div>
                        <div class="metric" style="margin-top: 15px; border-top: 1px solid #444; padding-top: 10px;">
                            <span class="metric-label" style="font-weight: bold;">📦 Supply & Demand Zones</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Show S&D Zones:</span>
                            <input type="checkbox" id="showSupplyDemandZones" onchange="toggleSupplyDemandZones()">
                        </div>
                        <div class="metric" style="font-size: 0.8em; color: #888;">
                            <span>📦 Toggle to load and display S&D zones</span>
                        </div>
                        
                        <!-- Zone Debug Panel -->
                        <div id="zoneDebugPanel" style="margin-top: 10px; padding: 8px; background: rgba(0,50,100,0.3); border-radius: 4px; border: 1px solid #444; display: none;">
                            <div style="font-weight: bold; color: #4fc3f7; margin-bottom: 5px;">🔍 Zone Debug Info</div>
                            <div class="metric" style="font-size: 0.75em;">
                                <span class="metric-label">Current Bar:</span>
                                <span class="metric-value" id="debugCurrentBar">-</span>
                            </div>
                            <div class="metric" style="font-size: 0.75em;">
                                <span class="metric-label">Current Time:</span>
                                <span class="metric-value" id="debugCurrentTime">-</span>
                            </div>
                            <div class="metric" style="font-size: 0.75em;">
                                <span class="metric-label">Chart Date Range:</span>
                                <span class="metric-value" id="debugChartDateRange">-</span>
                            </div>
                            <div class="metric" style="font-size: 0.75em;">
                                <span class="metric-label">Chart Price Range:</span>
                                <span class="metric-value" id="debugChartPriceRange">-</span>
                            </div>
                            <div class="metric" style="font-size: 0.75em;">
                                <span class="metric-label">Zones Loaded:</span>
                                <span class="metric-value" id="debugZonesLoaded">0</span>
                            </div>
                            <div class="metric" style="font-size: 0.75em;">
                                <span class="metric-label">Zones Visible:</span>
                                <span class="metric-value" id="debugZonesVisible">0</span>
                            </div>
                            <div class="metric" style="font-size: 0.75em;">
                                <span class="metric-label">Zone Date Range:</span>
                                <span class="metric-value" id="debugZoneDateRange">-</span>
                            </div>
                            <div class="metric" style="font-size: 0.75em;">
                                <span class="metric-label">Zone Price Range:</span>
                                <span class="metric-value" id="debugZonePriceRange">-</span>
                            </div>
                            <div class="metric" style="font-size: 0.75em;">
                                <span class="metric-label">Next Zone At:</span>
                                <span class="metric-value" id="debugNextZone">-</span>
                            </div>
                            <div class="metric" style="font-size: 0.75em; color: #ff6b6b;">
                                <span class="metric-label">⚠️ Date/Price Mismatch:</span>
                                <span class="metric-value" id="debugMismatchWarning">-</span>
                            </div>
                            <div id="debugZoneEvents" style="margin-top: 5px; max-height: 60px; overflow-y: auto; font-size: 0.7em; color: #aaa;"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Enhanced Signals Panel -->
                <div class="sidebar-section" id="enhancedSignalsSection">
                    <h3 onclick="toggleSection('enhancedSignalsSection')">
                        🎯 Enhanced Signals 
                        <span class="collapse-icon">▼</span>
                    </h3>
                    <div class="section-content" id="enhancedSignalsPanel">
                        <div class="metric" style="margin-bottom: 10px;">
                            <span class="metric-label">Live Signals:</span>
                            <span class="metric-value" id="liveEnhancedSignalCount">0</span>
                        </div>
                        <div id="enhancedSignalsList" style="max-height: 300px; overflow-y: auto; border: 1px solid #444; border-radius: 4px; background: rgba(0,0,0,0.3);">
                            <div style="color: #888; font-size: 0.9em; text-align: center; padding: 20px;">
                                No enhanced signals detected yet.<br>
                                Load data and navigate to see signals with pattern confirmation.
                            </div>
                        </div>
                        <div class="metric" style="margin-top: 10px; border-top: 1px solid #444; padding-top: 10px;">
                            <button onclick="clearAllEnhancedSignals()" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 0.8em;">
                                Clear All
                            </button>
                            <button onclick="exportEnhancedSignals()" style="background: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-left: 5px; font-size: 0.8em;">
                                Export CSV
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Signal Performance Analytics Panel -->
                <div class="sidebar-section" id="signalPerformanceSection">
                    <h3 onclick="toggleSection('signalPerformanceSection')">
                        📊 Signal Analytics 
                        <span class="collapse-icon">▼</span>
                    </h3>
                    <div class="section-content" id="signalPerformancePanel">
                        <div class="metrics-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px;">
                            <div class="metric">
                                <span class="metric-label">Active:</span>
                                <span class="metric-value" id="activeSignalsCount">0</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Completed:</span>
                                <span class="metric-value" id="completedSignalsCount">0</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Win Rate:</span>
                                <span class="metric-value" id="signalWinRate">0%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Avg Bars:</span>
                                <span class="metric-value" id="avgBarsToResolution">0</span>
                            </div>
                        </div>
                        
                        <div class="performance-controls" style="margin-bottom: 10px;">
                            <button onclick="refreshSignalAnalytics()" style="background: #4a90e2; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 0.8em; width: 100%;">
                                Refresh Analytics
                            </button>
                        </div>
                        
                        <div id="signalAnalyticsDetails" style="max-height: 200px; overflow-y: auto; border: 1px solid #444; border-radius: 4px; background: rgba(0,0,0,0.3); padding: 8px; font-size: 0.8em;">
                            <div style="color: #888; text-align: center; padding: 20px;">
                                Generate signals to see performance analytics
                            </div>
                        </div>
                        
                        <div class="export-controls" style="margin-top: 10px; border-top: 1px solid #444; padding-top: 10px;">
                            <button onclick="exportSignalPerformance()" style="background: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 0.8em; width: 100%;">
                                Export Performance Data
                            </button>
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
            // 🔧 Global debug logging control - centralized logging management
            const DEBUG_LOGGING = {
                markers: false,
                swings: false,
                fractals: false,
                navigation: false,
                websocket: true,
                errors: true,
                performance: false,
                swing_details: false,  // Disable detailed swing logging
                chart_updates: false   // Disable chart update logging
            };
            
            // Centralized debug logging function
            function debugLog(category, message, data = null) {
                if (DEBUG_LOGGING[category] || category === 'errors') {
                    if (data) {
                        console.log(message, data);
                    } else {
                        console.log(message);
                    }
                }
            }
            
            // ✅ ESSENTIAL FUNCTIONS - Define these first to avoid reference errors
            function updateStatus(message) {
                const statusBar = document.getElementById('statusBar');
                if (statusBar) {
                    statusBar.textContent = message;
                }
            }
            
            function initializeApp() {
                console.log('✅ Initializing application...');
                try {
                    // Delay initChart to ensure it's defined (function hoisting issue)
                    setTimeout(() => {
                        try {
                            initChart();
                            console.log('✅ Chart initialized successfully');
                        } catch (chartError) {
                            console.error('❌ Error initializing chart:', chartError);
                            updateStatus('Error: Chart initialization failed');
                        }
                    }, 10);
                    
                    // Initialize lookback indicator manager
                    lookbackManager = new LookbackIndicatorManager();
                    console.log('✅ Lookback indicator manager initialized');
                    
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
                        console.log('🎯 LightweightCharts available:', typeof LightweightCharts !== 'undefined');
                        try {
                            initializeApp();
                        } catch (error) {
                            console.error('❌ Error during initializeApp:', error);
                            updateStatus('Error: Failed to initialize application');
                        }
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
            // Legacy allMarkers array removed - now using UnifiedMarkerManager
            let enhancedSignalsData = []; // Global array to store enhanced signals for panel
            let enhancedSignalLines = []; // Global array to store price line references
            
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
            
            // Global arrays to store accumulated data from real-time detection
            let accumulatedFractals = [];
            let accumulatedSwings = [];
            let accumulatedFibonacci = [];
            let accumulatedABCPatterns = [];
            let accumulatedDominantSwing = null;
            
            // Make accumulated data globally accessible for batcher
            window.accumulatedFractals = accumulatedFractals;
            
            // ✅ UNIFIED MARKER MANAGEMENT SYSTEM - Eliminates flashing and race conditions
            class UnifiedMarkerManager {
                constructor(candlestickSeries) {
                    this.series = candlestickSeries;
                    this.markers = new Map(); // Use Map for efficient marker management by unique ID
                    this.updatePending = false;
                    this.updateTimeout = null;
                }

                // Add or update a marker by unique ID
                setMarker(id, markerData) {
                    if (!markerData || !id) return;

                    this.markers.set(id, {
                        ...markerData,
                        id: id
                    });

                    this.scheduleUpdate();
                }

                // Add multiple markers at once
                setMarkers(markersArray, idPrefix = '') {
                    if (!Array.isArray(markersArray)) return;

                    markersArray.forEach((marker, index) => {
                        const id = marker.id || `${idPrefix}_${marker.time}_${index}`;
                        this.setMarker(id, marker);
                    });
                }

                // Remove marker by ID
                removeMarker(id) {
                    if (this.markers.has(id)) {
                        this.markers.delete(id);
                        this.scheduleUpdate();
                    }
                }

                // Remove markers by pattern (e.g., all fractals, all signals)
                removeMarkersByPattern(pattern) {
                    let removed = 0;
                    for (const [id, marker] of this.markers) {
                        if (id.includes(pattern)) {
                            this.markers.delete(id);
                            removed++;
                        }
                    }
                    if (removed > 0) {
                        this.scheduleUpdate();
                        debugLog('markers', `🗑️ Removed ${removed} markers matching pattern: ${pattern}`);
                    }
                }

                // Clear all markers
                clearAll() {
                    this.markers.clear();
                    this.scheduleUpdate();
                }

                // Get current marker count
                getMarkerCount() {
                    return this.markers.size;
                }

                // Schedule a batched update to prevent flashing
                scheduleUpdate() {
                    if (this.updateTimeout) {
                        clearTimeout(this.updateTimeout);
                    }

                    // Batch updates with delay to prevent flashing and coordinate with ChartUpdateBatcher
                    this.updateTimeout = setTimeout(() => {
                        this.performUpdate();
                    }, 20); // 20ms delay - longer than ChartUpdateBatcher to avoid conflicts
                }

                // Force immediate update
                forceUpdate() {
                    if (this.updateTimeout) {
                        clearTimeout(this.updateTimeout);
                        this.updateTimeout = null;
                    }
                    this.performUpdate();
                }

                // Perform the actual chart update
                performUpdate() {
                    // 🚨 CRITICAL FIX: Always use the current candlestickSeries, not stored reference
                    const currentSeries = window.candlestickSeries || this.series;
                    if (!currentSeries) {
                        console.error('❌ No valid series reference for markers!');
                        return;
                    }

                    // Convert Map to array and sort by time
                    const markersArray = Array.from(this.markers.values());
                    markersArray.sort((a, b) => a.time - b.time);

                    // Single setMarkers call - no flashing
                    console.log(`🔍 CRITICAL: About to call setMarkers with ${markersArray.length} markers`);
                    console.log(`🔍 Using series:`, currentSeries === this.series ? 'stored reference' : 'GLOBAL candlestickSeries');
                    if (markersArray.length > 0) {
                        console.log(`🔍 First marker:`, markersArray[0]);
                    }
                    
                    currentSeries.setMarkers(markersArray);
                    
                    console.log(`🔍 CRITICAL: setMarkers completed - markers should be visible now`);
                    
                    // Immediate verification - no delayed timeouts that might interfere
                    console.log(`🔍 IMMEDIATE VERIFY: Series valid=${!!currentSeries}, Manager has ${this.getMarkerCount()} markers`);
                    
                    // Store reference to successful marker application
                    this.lastSuccessfulMarkerCount = markersArray.length;
                    
                    this.updateTimeout = null;
                }

                // Helper methods for specific marker types
                addFractal(fractal) {
                    if (!fractal) return;

                    const id = `fractal_${fractal.timestamp}_${fractal.fractal_type}`;
                    const marker = {
                        time: Math.floor(new Date(fractal.timestamp).getTime() / 1000),
                        position: fractal.fractal_type === 'high' ? 'aboveBar' : 'belowBar',
                        color: fractal.fractal_type === 'high' ? '#ff4444' : '#00bcd4',
                        shape: fractal.fractal_type === 'high' ? 'arrowUp' : 'arrowDown',
                        text: '',
                        size: 2
                    };

                    this.setMarker(id, marker);
                }

                addSignal(signal, signalType = 'signal') {
                    if (!signal) return;

                    const id = `${signalType}_${signal.timestamp}_${signal.signal_type || 'unknown'}`;
                    const marker = {
                        time: Math.floor(new Date(signal.timestamp).getTime() / 1000),
                        position: signal.signal_type === 'buy' ? 'belowBar' : 'aboveBar',
                        color: signal.signal_type === 'buy' ? '#00ff88' : '#ff4444',
                        shape: signal.signal_type === 'buy' ? 'arrowUp' : 'arrowDown',
                        text: signal.text || '',
                        size: signal.size || 2
                    };

                    this.setMarker(id, marker);
                }

                loadFractals(fractals) {
                    if (!Array.isArray(fractals)) {
                        console.log(`🚨 loadFractals called with non-array: ${typeof fractals}`);
                        return;
                    }

                    console.log(`🔍 loadFractals: Removing existing fractals, then loading ${fractals.length} new fractals`);
                    
                    // Remove existing fractals first
                    this.removeMarkersByPattern('fractal_');

                    // Add all fractals
                    fractals.forEach(fractal => this.addFractal(fractal));

                    console.log(`🔍 loadFractals: After processing, unified manager has ${this.getMarkerCount()} total markers`);
                }

                loadSignals(signals, signalType = 'signal') {
                    if (!Array.isArray(signals)) return;

                    // Remove existing signals of this type first
                    this.removeMarkersByPattern(signalType + '_');

                    // Add all signals
                    signals.forEach(signal => this.addSignal(signal, signalType));

                    // Silenced: console.log(`📍 Loaded ${signals.length} ${signalType} signals into unified manager`);
                }
            }

            // Global unified marker manager instance
            let unifiedMarkerManager = null;
            
            // 🚨 CRITICAL: Ensure markers persist across all chart operations
            function restoreAllMarkersAfterChartUpdate() {
                if (!unifiedMarkerManager) return;
                
                // Restore fractals if checkbox is checked (check both global and local arrays)
                const fractalSource = (accumulatedFractals.length > 0) ? accumulatedFractals : window.accumulatedFractals;
                if (document.getElementById('showFractals').checked && fractalSource && fractalSource.length > 0) {
                    unifiedMarkerManager.loadFractals(fractalSource);
                    debugLog('markers', `🔄 Restored ${fractalSource.length} fractals after chart update`);
                } else {
                    debugLog('markers', '🔄 No fractals to restore - either checkbox unchecked or no accumulated data');
                }
                
                // Force immediate update to ensure markers show
                unifiedMarkerManager.forceUpdate();
            }

            // Legacy compatibility - keep for backward compatibility during transition
            let fractalManager = null;
            
            let swingLineManager = null;
            let fibonacciManager = null;
            let abcPatternManager = null;
            let lookbackManager = null;
            let supplyDemandManager = null;
            
            // ✅ PROFESSIONAL TRADINGVIEW SWING LINE IMPLEMENTATION
            // Following TradingView Lightweight Charts best practices for custom line drawing
            
            // Swing Line Primitive - Core line drawing component
            class SwingLinePrimitive {
                constructor(point1, point2, options = {}) {
                    this._point1 = point1; // { time: Time, value: number }
                    this._point2 = point2; // { time: Time, value: number }
                    this._options = {
                        color: options.color || '#26A69A',
                        lineWidth: options.lineWidth || 2,
                        lineStyle: options.lineStyle || 0, // solid
                        opacity: options.opacity || 0.8,
                        ...options
                    };
                    this._paneViews = [new SwingLinePaneView(this)];
                }
                
                // Required TradingView interface methods
                attached(params) {
                    this._attachedParams = params;
                }
                
                detached() {
                    // Cleanup when primitive is detached
                }
                
                paneViews() {
                    return this._paneViews;
                }
                
                updateAllViews() {
                    this._paneViews.forEach(view => view.update());
                }
                
                // Update line points
                updatePoints(point1, point2) {
                    this._point1 = point1;
                    this._point2 = point2;
                    this.updateAllViews();
                }
                
                // Getters for rendering
                point1() { return this._point1; }
                point2() { return this._point2; }
                options() { return this._options; }
            }
            
            // Swing Line Pane View - View management
            class SwingLinePaneView {
                constructor(source) {
                    this._source = source;
                    this._renderer = new SwingLineRenderer();
                }
                
                update() {
                    this._renderer.update(this._source);
                }
                
                renderer() {
                    return this._renderer;
                }
            }
            
            // Swing Line Renderer - Actual drawing implementation
            class SwingLineRenderer {
                constructor() {
                    this._point1 = null;
                    this._point2 = null;
                    this._options = null;
                }
                
                update(source) {
                    this._point1 = source.point1();
                    this._point2 = source.point2();
                    this._options = source.options();
                }
                
                draw(target) {
                    if (!this._point1 || !this._point2 || !target.canvasRenderingContext2D) return;
                    
                    const ctx = target.canvasRenderingContext2D;
                    const pixelRatio = target.pixelRatio;
                    
                    // Convert time/price coordinates to pixel coordinates
                    const timeToCoordinate = target.context.timeScale.timeToCoordinate.bind(target.context.timeScale);
                    const priceToCoordinate = target.context.priceScale.priceToCoordinate.bind(target.context.priceScale);
                    
                    const x1 = timeToCoordinate(this._point1.time);
                    const y1 = priceToCoordinate(this._point1.value);
                    const x2 = timeToCoordinate(this._point2.time);
                    const y2 = priceToCoordinate(this._point2.value);
                    
                    // Skip if coordinates are invalid
                    if (x1 === null || y1 === null || x2 === null || y2 === null) return;
                    
                    // Viewport culling for performance
                    const margin = 50; // pixels
                    const viewport = {
                        left: -margin,
                        right: target.mediaSize.width + margin,
                        top: -margin,
                        bottom: target.mediaSize.height + margin
                    };
                    
                    if (!this._lineIntersectsViewport(x1, y1, x2, y2, viewport)) {
                        return; // Skip off-screen lines
                    }
                    
                    // Draw the swing line
                    ctx.save();
                    ctx.globalAlpha = this._options.opacity;
                    ctx.strokeStyle = this._options.color;
                    ctx.lineWidth = this._options.lineWidth * pixelRatio;
                    ctx.setLineDash(this._getLineDash());
                    
                    ctx.beginPath();
                    ctx.moveTo(x1 * pixelRatio, y1 * pixelRatio);
                    ctx.lineTo(x2 * pixelRatio, y2 * pixelRatio);
                    ctx.stroke();
                    ctx.restore();
                }
                
                _lineIntersectsViewport(x1, y1, x2, y2, viewport) {
                    // Simple bounding box check for line visibility
                    const minX = Math.min(x1, x2);
                    const maxX = Math.max(x1, x2);
                    const minY = Math.min(y1, y2);
                    const maxY = Math.max(y1, y2);
                    
                    return maxX >= viewport.left && minX <= viewport.right &&
                           maxY >= viewport.top && minY <= viewport.bottom;
                }
                
                _getLineDash() {
                    // Convert line style to dash pattern
                    switch (this._options.lineStyle) {
                        case 1: return [5, 5]; // dashed
                        case 2: return [2, 2]; // dotted
                        default: return []; // solid
                    }
                }
            }
            
            // Swing Line Manager - High-level management with performance optimization
            class SwingLineManager {
                constructor(series) {
                    this._series = series;
                    this._lines = new Map();
                    this._simpleLines = new Map(); // Simple line series for debugging
                    this._nextId = 0;
                    this._lastSwingSignature = null; // Track swing data changes to prevent unnecessary redraws
                    
                    // Color scheme following best practices
                    this.COLORS = {
                        uptrend: '#26A69A',        // Teal for bullish swings
                        downtrend: '#EF5350',     // Red for bearish swings
                        major: '#FF6B35',         // Orange for major swings
                        minor: '#95A5A6',         // Gray for minor swings
                        dominant_up: '#00E676',   // Bright green for dominant bullish
                        dominant_down: '#FF1744', // Bright red for dominant bearish
                        normal_up: '#4CAF50',     // Normal green for regular bullish
                        normal_down: '#F44336'    // Normal red for regular bearish
                    };
                }
                
                addSwingLine(point1, point2, direction = 'neutral', strength = 'normal') {
                    const id = this._nextId++;
                    
                    // 🚨 CRITICAL: Final coordinate validation before drawing
                    // SILENCED: console.log(`🎯 ADDING SWING LINE ${id}:`, { point1, point2, direction, strength });
                    
                    // Validate coordinates one more time
                    if (!point1 || !point2) {
                        console.error(`❌ ADDSWINGLINE: Missing points`, { point1, point2 });
                        return null;
                    }
                    
                    if (typeof point1.time !== 'number' || typeof point1.value !== 'number' ||
                        typeof point2.time !== 'number' || typeof point2.value !== 'number') {
                        console.error(`❌ ADDSWINGLINE: Invalid coordinate types`, { point1, point2 });
                        return null;
                    }
                    
                    if (isNaN(point1.time) || isNaN(point1.value) || isNaN(point2.time) || isNaN(point2.value)) {
                        console.error(`❌ ADDSWINGLINE: NaN coordinates`, { point1, point2 });
                        return null;
                    }
                    
                    // Check for identical points (would create invisible line)
                    if (point1.time === point2.time && point1.value === point2.value) {
                        console.warn(`⚠️ ADDSWINGLINE: Identical points (invisible line)`, { point1, point2 });
                        return null;
                    }
                    
                    // Color coding based on direction and strength
                    const color = this._getSwingColor(direction, strength);
                    let lineWidth = 2; // Default line width
                    let lineStyle = 0; // Default solid line
                    
                    // Set line styling based on strength
                    if (strength === 'dominant') {
                        lineWidth = 4; // Thick for dominant swing
                        lineStyle = 0; // Solid line for dominant
                    } else if (strength === 'major') {
                        lineWidth = 3; // Thick for major swings
                        lineStyle = 0; // Solid line for major
                    } else {
                        lineWidth = 2; // Normal width for non-dominant
                        lineStyle = 1; // Dashed line for non-dominant
                    }
                    
                    try {
                        // Enhanced swing line with proper styling
                        const swingData = [
                            { time: point1.time, value: point1.value },
                            { time: point2.time, value: point2.value }
                        ];
                        
                        // SILENCED: TradingView data logging
                        // console.log(`🎯 TRADINGVIEW DATA for swing ${id}:`, {
                        //     swingData,
                        //     config: {
                        //         color,
                        //         lineWidth,
                        //         lineStyle,
                        //         direction,
                        //         strength
                        //     }
                        // });
                        
                        // Validate TradingView data format
                        swingData.forEach((point, idx) => {
                            if (typeof point.time !== 'number' || typeof point.value !== 'number') {
                                throw new Error(`Invalid data point ${idx}: time=${point.time} (${typeof point.time}), value=${point.value} (${typeof point.value})`);
                            }
                            if (isNaN(point.time) || isNaN(point.value)) {
                                throw new Error(`NaN in data point ${idx}: time=${point.time}, value=${point.value}`);
                            }
                        });
                        
                        const lineSeries = chart.addLineSeries({
                            color: color,
                            lineWidth: lineWidth,
                            lineStyle: lineStyle, // 0 = solid, 1 = dashed, 2 = dotted
                            priceLineVisible: false,
                            lastValueVisible: false,
                            title: strength === 'dominant' ? `Dominant ${direction.toUpperCase()} swing` : `${direction.toUpperCase()} swing`
                        });
                        
                        lineSeries.setData(swingData);
                        this._simpleLines.set(id, lineSeries);
                        
                        // SILENCED: console.log(`✅ SUCCESS: Added ${direction} swing line ${id} from time ${point1.time} (${point1.value}) to time ${point2.time} (${point2.value})`);
                        return id;
                    } catch (error) {
                        // Keep critical errors: console.error(`❌ CRITICAL ERROR adding swing line ${id}:`, error, { point1, point2, direction, strength });
                        return null;
                    }
                }
                
                updateSwingLine(id, point1, point2) {
                    const line = this._lines.get(id);
                    if (line) {
                        line.updatePoints(point1, point2);
                    }
                }
                
                removeSwingLine(id) {
                    const line = this._lines.get(id);
                    if (line) {
                        this._series.detachPrimitive(line);
                        this._lines.delete(id);
                    }
                }
                
                removeAllSwingLines() {
                    debugLog('swing_details', `🧹 Removing ${this._simpleLines.size} swing lines`);
                    this._simpleLines.forEach(lineSeries => {
                        chart.removeSeries(lineSeries);
                    });
                    this._simpleLines.clear();
                    this._lines.clear();
                }
                
                loadAllSwings(swings) {
                    debugLog('swing_details', `🔍 DEBUG: Loading ${swings.length} swings for filtering`, swings);
                    
                    // 🎯 CRITICAL: Only show the LATEST 2 swings (1 up + 1 down) within lookback period
                    if (!swings || swings.length === 0) {
                        debugLog('swing_details', 'No swings to display');
                        this.removeAllSwingLines(); // Only clear if no swings
                        return;
                    }
                    
                    // 🚨 PERFORMANCE FIX: Check if swing data has actually changed before clearing/redrawing
                    const currentSwingSignature = swings.map(s => `${s.direction}-${s.start_fractal.timestamp}-${s.end_fractal.timestamp}-${s.is_dominant}`).join('|');
                    if (this._lastSwingSignature === currentSwingSignature) {
                        debugLog('chart_updates', '📊 Swing data unchanged, skipping redraw to prevent flashing');
                        return;
                    }
                    this._lastSwingSignature = currentSwingSignature;
                    
                    // Only clear and redraw if data has actually changed
                    this.removeAllSwingLines();
                    
                    // Filter swings within lookback period if current position is available
                    let filteredSwings = swings;
                    if (typeof currentPosition !== 'undefined' && currentPosition !== null) {
                        const lookbackCandles = parseInt(document.getElementById('lookbackCandles').value) || 140;
                        const lookbackStart = Math.max(0, currentPosition - lookbackCandles);
                        
                        filteredSwings = swings.filter(swing => {
                            const swingPosition = swing.end_fractal.bar_index || swing.position || 0;
                            return swingPosition >= lookbackStart;
                        });
                        
                        debugLog('swing_details', `📊 Step 1: Filtered from ${swings.length} to ${filteredSwings.length} swings within lookback period (position ${currentPosition}, lookback ${lookbackCandles})`);
                    } else {
                        debugLog('swing_details', '📊 Step 1: No current position, using all swings for filtering');
                    }
                    
                    // 🚨 CRITICAL FIX: Respect backend's dominance calculation completely
                    // The backend uses Elliott Wave principles to determine dominance correctly
                    // Frontend should ALWAYS show the dominant swing + one opposing swing for context

                    // Find the swing marked as dominant by the backend
                    const dominantSwing = filteredSwings.find(swing => swing.is_dominant);

                    if (!dominantSwing) {
                        console.warn('⚠️ No dominant swing found in filtered swings - showing all');
                        // Fallback: show all filtered swings if no dominance is set
                        const displaySwings = filteredSwings;
                        displaySwings.forEach((swing, index) => {
                            // Use the same validation and drawing logic as the main path
                            this._drawValidatedSwingInternal(swing, index);
                        });
                        return;
                    }

                    // Always include the dominant swing
                    const displaySwings = [dominantSwing];

                    // Find the most recent swing in the opposite direction for context
                    const oppositeDirection = dominantSwing.direction === 'up' ? 'down' : 'up';
                    const oppositeSwings = filteredSwings.filter(swing =>
                        swing.direction === oppositeDirection && !swing.is_dominant
                    );

                    if (oppositeSwings.length > 0) {
                        // Sort by end time and take the most recent
                        oppositeSwings.sort((a, b) => {
                            const timeA = new Date(a.end_fractal.timestamp).getTime();
                            const timeB = new Date(b.end_fractal.timestamp).getTime();
                            return timeB - timeA; // Most recent first
                        });
                        displaySwings.push(oppositeSwings[0]);
                    }
                    
                    debugLog('swing_details', `🎯 DISPLAY STRATEGY: Showing ${displaySwings.length} swings (dominant + context)`);
                    displaySwings.forEach((swing, i) => {
                        const isDominant = swing.is_dominant || false;
                        const magnitude = Math.abs(swing.points || Math.abs(swing.end_fractal.price - swing.start_fractal.price));
                        debugLog('swing_details', `   ${i + 1}. ${swing.direction.toUpperCase()} swing: ${magnitude.toFixed(5)} pts (${(magnitude*10000).toFixed(1)} pips) - ${isDominant ? 'DOMINANT' : 'context'}`);
                    });

                    // Update market bias based on backend's dominant swing
                    if (dominantSwing) {
                        const magnitude = Math.abs(dominantSwing.points || Math.abs(dominantSwing.end_fractal.price - dominantSwing.start_fractal.price));
                        updateMarketBiasFromDominantSwing(dominantSwing, magnitude);
                        debugLog('swing_details', `🔒 BACKEND DOMINANCE: ${dominantSwing.direction.toUpperCase()} swing (${magnitude.toFixed(5)} pts / ${(magnitude*10000).toFixed(1)} pips) marked as dominant`);
                    }
                    
                    // Add only the latest swing lines with proper styling
                    displaySwings.forEach((swing, index) => {
                        this._drawValidatedSwingInternal(swing, index);
                    });
                    
                    debugLog('swing_details', `📊 Clean display: ${displaySwings.length} swing lines loaded (using backend invalidation-based dominance)`);
                }

                _drawValidatedSwingInternal(swing, index) {
                    // 🚨 CRITICAL: Validate swing data before drawing
                    debugLog('swing_details', `🔍 VALIDATING SWING ${index + 1}:`, swing);

                    // Validate fractal data exists
                    if (!swing.start_fractal || !swing.end_fractal) {
                        console.error(`❌ INVALID SWING: Missing fractal data`, swing);
                        return;
                    }

                    // Validate timestamps
                    if (!swing.start_fractal.timestamp || !swing.end_fractal.timestamp) {
                        console.error(`❌ INVALID SWING: Missing timestamps`, swing);
                        return;
                    }

                    // Validate prices
                    if (typeof swing.start_fractal.price !== 'number' || typeof swing.end_fractal.price !== 'number') {
                        console.error(`❌ INVALID SWING: Invalid prices`, swing);
                        return;
                    }

                    if (isNaN(swing.start_fractal.price) || isNaN(swing.end_fractal.price)) {
                        console.error(`❌ INVALID SWING: NaN prices`, swing);
                        return;
                    }

                    // Calculate coordinates
                    const startTime = new Date(swing.start_fractal.timestamp).getTime();
                    const endTime = new Date(swing.end_fractal.timestamp).getTime();

                    // Validate timestamp conversion
                    if (isNaN(startTime) || isNaN(endTime)) {
                        console.error(`❌ INVALID SWING: Invalid timestamp conversion`, {
                            start: swing.start_fractal.timestamp,
                            end: swing.end_fractal.timestamp,
                            startTime,
                            endTime
                        });
                        return;
                    }

                    const point1 = {
                        time: Math.floor(startTime / 1000),
                        value: swing.start_fractal.price
                    };
                    const point2 = {
                        time: Math.floor(endTime / 1000),
                        value: swing.end_fractal.price
                    };

                    // Validate final coordinates
                    if (isNaN(point1.time) || isNaN(point1.value) || isNaN(point2.time) || isNaN(point2.value)) {
                        console.error(`❌ INVALID COORDINATES:`, { point1, point2 });
                        return;
                    }

                    // Calculate time and price differences for validation
                    const timeDiff = Math.abs(point2.time - point1.time);
                    const priceDiff = Math.abs(point2.value - point1.value);

                    console.log(`✅ VALID SWING ${index + 1}: ${swing.direction}`, {
                        start: { time: point1.time, price: point1.value, timestamp: swing.start_fractal.timestamp },
                        end: { time: point2.time, price: point2.value, timestamp: swing.end_fractal.timestamp },
                        timeDiff: `${timeDiff} seconds`,
                        priceDiff: `${priceDiff.toFixed(2)} points`,
                        dominant: swing.is_dominant || false
                    });

                    // Warn about suspicious swing characteristics
                    if (timeDiff < 60) { // Less than 1 minute
                        console.warn(`⚠️ SUSPICIOUS: Very short time span (${timeDiff}s) for swing`, { point1, point2 });
                    }

                    if (priceDiff > 1000) { // More than 1000 points
                        console.warn(`⚠️ SUSPICIOUS: Very large price movement (${priceDiff.toFixed(2)} pts) for swing`, { point1, point2 });
                    }

                    // Draw the swing if validation passes
                    const strength = swing.is_dominant ? 'dominant' : 'normal';
                    this.addSwingLine(point1, point2, swing.direction, strength);
                }

                _getSwingColor(direction, strength) {
                    // Handle dominant swings with special colors
                    if (strength === 'dominant') {
                        return direction === 'up' ? this.COLORS.dominant_up : this.COLORS.dominant_down;
                    }
                    
                    // Handle major swings
                    if (strength === 'major') {
                        return this.COLORS.major;
                    }
                    
                    // Handle normal swings with improved colors
                    if (direction === 'up') {
                        return this.COLORS.normal_up;
                    } else if (direction === 'down') {
                        return this.COLORS.normal_down;
                    }
                    
                    // Fallback to original colors
                    return direction === 'up' ? this.COLORS.uptrend : this.COLORS.downtrend;
                }
                
                _determineStrength(swing) {
                    // Determine swing strength based on price movement and duration
                    const priceMove = Math.abs(swing.points || 0);
                    const duration = swing.bars || 0;
                    
                    // Major swings: large price movement or long duration
                    if (priceMove > 100 || duration > 50) {
                        return 'major';
                    }
                    return 'normal';
                }
            }

            // ✅ Fibonacci Level Manager - Professional Fibonacci retracement display
            class FibonacciLevelManager {
                constructor(candlestickSeries) {
                    this.candlestickSeries = candlestickSeries;
                    this.fibonacciLines = [];
                    this.fibonacciColors = {
                        0.236: '#ff9800',  // Orange
                        0.382: '#2196f3',  // Blue
                        0.500: '#9c27b0',  // Purple
                        0.618: '#4caf50',  // Green
                        0.786: '#f44336'   // Red
                    };
                }

                updateFibonacciLevels(fibonacciLevels, dominantSwing) {
                    // Clear existing Fibonacci lines
                    this.clearFibonacci();

                    if (!fibonacciLevels || fibonacciLevels.length === 0 || !dominantSwing) return;

                    // Get chart time range for horizontal lines
                    const swingStartTime = new Date(dominantSwing.start_timestamp).getTime() / 1000;
                    const swingEndTime = new Date(dominantSwing.end_timestamp).getTime() / 1000;

                    // Extend lines beyond the swing for better visibility
                    const timeRange = swingEndTime - swingStartTime;
                    const extendedStartTime = swingStartTime - (timeRange * 0.1);
                    const extendedEndTime = swingEndTime + (timeRange * 0.5);

                    // Add Fibonacci level lines
                    fibonacciLevels.forEach(fibLevel => {
                        this.addFibonacciLine(fibLevel, extendedStartTime, extendedEndTime);
                    });
                }

                addFibonacciLine(fibLevel, startTime, endTime) {
                    try {
                        const levelPercentage = (fibLevel.level * 100).toFixed(1);
                        const color = this.fibonacciColors[fibLevel.level] || '#ffffff';

                        const lineStyle = {
                            color: color,
                            width: 0.5, // Thinner lines to reduce clutter
                            style: 2, // Dotted line
                            priceLineVisible: false,
                            lastValueVisible: false
                        };

                        // Create horizontal line data
                        const lineData = [
                            { time: startTime, value: fibLevel.price },
                            { time: endTime, value: fibLevel.price }
                        ];

                        // Create line series for this Fibonacci level
                        const lineSeries = chart.addLineSeries(lineStyle);
                        lineSeries.setData(lineData);

                        // Add price line with label
                        lineSeries.createPriceLine({
                            price: fibLevel.price,
                            color: color,
                            lineWidth: 0.5, // Thinner price line
                            lineStyle: 2, // Dotted
                            axisLabelVisible: true,
                            title: `${levelPercentage}%`
                        });

                        this.fibonacciLines.push(lineSeries);

                    } catch (error) {
                        console.error('Error adding Fibonacci line:', error);
                    }
                }

                clearFibonacci() {
                    this.fibonacciLines.forEach(line => {
                        try {
                            chart.removeSeries(line);
                        } catch (error) {
                            console.error('Error removing Fibonacci line:', error);
                        }
                    });
                    this.fibonacciLines = [];
                }
            }

            // ✅ ABC PATTERN VISUALIZATION MANAGER
            class ABCPatternManager {
                constructor(candlestickSeries) {
                    this.candlestickSeries = candlestickSeries;
                    this.abcLines = [];
                    this.abcLabels = [];
                    this.addedPatterns = new Set(); // 🔧 Track added patterns to prevent duplicates
                    this.lastDominantSwingId = null; // 🔧 Track dominant swing changes
                    
                    // ABC wave styling - dotted lines to show wave connections
                    this.waveStyles = {
                        A: { color: '#FF6B6B', width: 2, style: 2 }, // Dotted red (A to B)
                        B: { color: '#4ECDC4', width: 2, style: 2 }, // Dotted teal (B to C) 
                        C: { color: '#45B7D1', width: 2, style: 2 }  // Dotted blue (C continuation)
                    };
                    
                    console.log('📊 ABCPatternManager initialized');
                }

                // Add new ABC pattern to chart
                addABCPattern(pattern, currentDominantSwing = null) {
                    try {
                        if (!pattern) return;

                        // Create unique pattern ID to prevent duplicates
                        const patternId = `${pattern.wave_a.start_timestamp}_${pattern.wave_c.end_timestamp || pattern.wave_c.start_timestamp}`;
                        
                        // Check if pattern already added
                        if (this.addedPatterns.has(patternId)) {
                            console.log(`🔄 ABC Pattern already added, skipping: ${patternId}`);
                            return;
                        }
                        
                        // Log pattern structure for debugging
                        console.log(`🔍 ABC Pattern structure:`, {
                            wave_a: pattern.wave_a,
                            wave_b: pattern.wave_b,
                            wave_c: pattern.wave_c,
                            is_complete: pattern.is_complete
                        });
                        
                        console.log(`🔍 ABC Pattern ID: ${patternId}, Pattern complete: ${pattern.is_complete}`);

                        // 🚨 CRITICAL FIX: Check if dominant swing has changed before adding pattern
                        const currentSwingId = currentDominantSwing ? 
                            `${currentDominantSwing.start_fractal.timestamp}-${currentDominantSwing.end_fractal.timestamp}` : null;
                        
                        if (this.lastDominantSwingId && this.lastDominantSwingId !== currentSwingId) {
                            console.log('🔄 DOMINANT SWING CHANGED - Clearing old ABC patterns before adding new one');
                            this.clearABCPatterns();
                        }
                        
                        this.lastDominantSwingId = currentSwingId;

                        console.log(`🌊 Adding ABC pattern ${patternId} for dominant swing:`, currentSwingId);

                        // Wave A line
                        console.log(`🌊 ABC: Processing Wave A:`, pattern.wave_a);
                        this.addWaveLine('A', pattern.wave_a);
                        
                        // Wave B line
                        console.log(`🌊 ABC: Processing Wave B:`, pattern.wave_b);
                        this.addWaveLine('B', pattern.wave_b);
                        
                        // Wave C line (if complete)
                        if (pattern.is_complete) {
                            console.log(`🌊 ABC: Processing Wave C (complete):`, pattern.wave_c);
                            this.addWaveLine('C', pattern.wave_c);
                        } else {
                            console.log(`🌊 ABC: Processing Wave C projections (incomplete)`);
                            // Add projection levels for incomplete Wave C
                            this.addProjectionLevels(pattern);
                        }

                        // Track that this pattern has been added
                        this.addedPatterns.add(patternId);
                        console.log(`✅ ABC Pattern ${patternId} added successfully. Total patterns: ${this.addedPatterns.size}`);

                    } catch (error) {
                        console.error('❌ Error adding ABC pattern:', error);
                    }
                }

                // Add line for individual wave
                addWaveLine(waveType, waveData) {
                    try {
                        const style = this.waveStyles[waveType];
                        
                        // Convert timestamps to chart time format
                        const startTime = new Date(waveData.start_timestamp).getTime() / 1000;
                        const endTime = new Date(waveData.end_timestamp).getTime() / 1000;
                        
                        // Validate timestamps
                        if (isNaN(startTime) || isNaN(endTime)) {
                            console.warn('⚠️ Invalid timestamps for wave', waveType);
                            return;
                        }

                        // Create line data
                        const lineData = [
                            { time: startTime, value: waveData.start_price },
                            { time: endTime, value: waveData.end_price }
                        ];

                        // Create line series
                        const lineSeries = chart.addLineSeries({
                            color: style.color,
                            lineWidth: style.width,
                            lineStyle: style.style,
                            priceLineVisible: false,
                            lastValueVisible: false,
                            title: `ABC-Wave-${waveType}`
                        });

                        lineSeries.setData(lineData);
                        this.abcLines.push(lineSeries);

                        console.log(`✅ ABC: Added Wave ${waveType} line from ${waveData.start_price} to ${waveData.end_price} (time: ${startTime} to ${endTime})`);
                        console.log(`📊 ABC: Line series created with style:`, style);
                        console.log(`📈 ABC: Total ABC lines now: ${this.abcLines.length}`);

                    } catch (error) {
                        console.error(`❌ Error adding wave ${waveType} line:`, error);
                    }
                }

                // Load all ABC patterns at once
                loadAllABCPatterns(abcPatterns, currentDominantSwing = null) {
                    try {
                        if (!abcPatterns || abcPatterns.length === 0) {
                            return;
                        }

                        // SILENCED: console.log('🔄 Loading', abcPatterns.length, 'ABC patterns');
                        
                        // 🔧 CRUCIAL: Check if dominant swing has changed
                        const currentSwingId = currentDominantSwing ? 
                            `${currentDominantSwing.start_fractal.timestamp}-${currentDominantSwing.end_fractal.timestamp}` : null;
                        
                        if (this.lastDominantSwingId && this.lastDominantSwingId !== currentSwingId) {
                            // SILENCED: console.log('🔄 DOMINANT SWING CHANGED - Clearing old ABC patterns');
                            this.clearABCPatterns();
                        }
                        
                        this.lastDominantSwingId = currentSwingId;

                        // 🔧 FIXED: Only add new patterns, don't clear and re-add everything
                        let newPatternsAdded = 0;
                        
                        abcPatterns.forEach((pattern) => {
                            const patternId = this.getPatternId(pattern);
                            if (!this.addedPatterns.has(patternId)) {
                                this.addABCPattern(pattern);
                                this.addedPatterns.add(patternId);
                                newPatternsAdded++;
                            }
                        });
                        
                        if (newPatternsAdded > 0) {
                            console.log(`✅ Added ${newPatternsAdded} new ABC patterns (${this.addedPatterns.size} total)`);
                        }

                    } catch (error) {
                        console.error('❌ Error loading ABC patterns:', error);
                    }
                }

                // Add C wave projection levels (Fe62, Fe100, Fe127)
                addProjectionLevels(pattern) {
                    try {
                        if (!pattern.fe62_target || !pattern.fe100_target || !pattern.fe127_target) {
                            console.warn('⚠️ No projection levels found in pattern');
                            return;
                        }

                        const waveC = pattern.wave_c;
                        const startTime = new Date(waveC.start_timestamp).getTime() / 1000;
                        
                        // 🔧 FIXED: Create shorter projection lines (not full-width)
                        const projectionLength = 3600 * 24 * 2; // 2 days forward only
                        const endTime = startTime + projectionLength;
                        
                        // Fe62 level (61.8%) - Orange
                        this.addProjectionLine(startTime, endTime, pattern.fe62_target, 'Fe62', '#FF9500');
                        
                        // Fe100 level (100%) - Red
                        this.addProjectionLine(startTime, endTime, pattern.fe100_target, 'Fe100', '#FF0000');
                        
                        // Fe127 level (127%) - Dark Red
                        this.addProjectionLine(startTime, endTime, pattern.fe127_target, 'Fe127', '#8B0000');
                        
                        console.log('✅ Added C wave projection levels:', {
                            fe62: pattern.fe62_target,
                            fe100: pattern.fe100_target,
                            fe127: pattern.fe127_target
                        });
                        
                    } catch (error) {
                        console.error('❌ Error adding projection levels:', error);
                    }
                }
                
                // Add individual projection line with text label
                addProjectionLine(startTime, endTime, price, label, color) {
                    try {
                        const lineData = [
                            { time: startTime, value: price },
                            { time: endTime, value: price }
                        ];

                        const lineSeries = chart.addLineSeries({
                            color: color,
                            lineWidth: 1,
                            lineStyle: 1, // Dashed line
                            priceLineVisible: false,  // 🔧 FIXED: Prevent price scale clutter
                            lastValueVisible: false,  // 🔧 FIXED: Prevent price scale clutter
                            title: `ABC-${label}`,
                            priceFormat: {
                                type: 'price',
                                precision: 2,
                                minMove: 0.01,
                            }
                        });

                        lineSeries.setData(lineData);
                        this.abcLines.push(lineSeries);
                        
                        // 🏷️ Add text label above the line
                        const markerTime = startTime + ((endTime - startTime) * 0.3); // Position at 30% of line length
                        const textMarker = {
                            time: markerTime,
                            position: 'aboveBar',
                            color: color,
                            shape: 'square',
                            text: label,
                            size: 0 // Hide the marker shape, just show text
                        };
                        
                        // 🚨 CRITICAL: Route through unified marker manager instead of direct setMarkers
                        if (unifiedMarkerManager) {
                            unifiedMarkerManager.setMarker(`abc_projection_${label}_${startTime}`, textMarker);
                        } else {
                            lineSeries.setMarkers([textMarker]);
                        }
                        
                        debugLog('swing_details', `✅ Added ${label} projection line at ${price} with text label`);
                        
                    } catch (error) {
                        console.error(`❌ Error adding ${label} projection line:`, error);
                    }
                }

                // Generate unique ID for pattern to prevent duplicates
                getPatternId(pattern) {
                    // 🚨 DEFENSIVE: Check if pattern and waves exist
                    if (!pattern || !pattern.wave_a || !pattern.wave_b || !pattern.wave_c) {
                        console.warn('Invalid ABC pattern structure:', pattern);
                        return `invalid_pattern_${Date.now()}_${Math.random()}`;
                    }
                    
                    // Create unique ID based on wave timestamps and prices
                    const waveA = pattern.wave_a;
                    const waveB = pattern.wave_b;
                    const waveC = pattern.wave_c;
                    
                    // 🚨 DEFENSIVE: Check if timestamps exist
                    if (!waveA.start_timestamp || !waveA.end_timestamp || !waveB.end_timestamp || !waveC.start_timestamp) {
                        console.warn('Missing timestamps in ABC pattern waves:', {waveA, waveB, waveC});
                        return `pattern_${waveA.start_price || 0}_${waveB.end_price || 0}_${waveC.end_price || 0}_${Date.now()}`;
                    }
                    
                    return `${waveA.start_timestamp}_${waveA.end_timestamp}_${waveB.end_timestamp}_${waveC.start_timestamp}`;
                }

                // Clear all ABC patterns from chart
                clearABCPatterns() {
                    try {
                        this.abcLines.forEach(line => {
                            chart.removeSeries(line);
                        });
                        this.abcLines = [];
                        this.addedPatterns.clear(); // 🔧 Clear tracking set too
                        
                        // 🚨 CRITICAL FIX: Clear accumulated ABC patterns to prevent re-adding
                        if (typeof accumulatedABCPatterns !== 'undefined') {
                            accumulatedABCPatterns = [];
                        }
                        
                        console.log('🧹 Cleared all ABC patterns and accumulated patterns');
                    } catch (error) {
                        console.error('❌ Error clearing ABC patterns:', error);
                    }
                }
            }

            // Simple fractal detection - removed complex logic that caused infinite loops

            // Helper function to load data into backtesting engine
            async function loadBacktestingEngine(symbol, timeframe, startDate, endDate) {
                try {
                    const fractalPeriods = parseInt(document.getElementById('fractalPeriods').value) || 5;
                    const lookbackCandles = parseInt(document.getElementById('lookbackCandles').value) || 140;
                    console.log('🔄 Loading backtesting engine with data...', {symbol, timeframe, startDate, endDate, fractalPeriods, lookbackCandles});
                    
                    const response = await fetch('/api/backtest/load', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            symbol: symbol,
                            timeframe: timeframe,
                            start_date: startDate,
                            end_date: endDate,
                            limit: null,
                            fractal_periods: fractalPeriods,
                            lookback_candles: lookbackCandles
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
            
            // ✅ CHART UPDATE BATCHER - Eliminates flashing by batching all updates
            class ChartUpdateBatcher {
                constructor() {
                    this.pendingUpdates = {
                        fractals: [],
                        swings: [],
                        fibonacci: null,
                        abc_patterns: [],
                        signals: [],
                        enhanced_signals: [],
                        markers: false,
                        debug_panel: {}
                    };
                    this.batchTimeout = null;
                    this.isProcessing = false;
                }
                
                // Add fractal update to batch
                addFractal(fractal) {
                    if (!fractal || this.pendingUpdates.fractals.some(f => 
                        f.timestamp === fractal.timestamp && f.fractal_type === fractal.fractal_type)) {
                        return; // Skip duplicates
                    }
                    this.pendingUpdates.fractals.push(fractal);
                    this.scheduleBatch();
                }
                
                // Add swing update to batch
                addSwing(swing) {
                    if (!swing) return;
                    this.pendingUpdates.swings.push(swing);
                    this.scheduleBatch();
                }
                
                // Add fibonacci levels to batch
                addFibonacci(fibLevels, dominantSwing) {
                    this.pendingUpdates.fibonacci = { fibLevels, dominantSwing };
                    this.scheduleBatch();
                }
                
                // Add ABC patterns to batch
                addABCPatterns(patterns, dominantSwing) {
                    this.pendingUpdates.abc_patterns = { patterns, dominantSwing };
                    this.scheduleBatch();
                }
                
                // Add signals to batch
                addSignals(signals) {
                    if (!signals || !Array.isArray(signals)) return;
                    this.pendingUpdates.signals.push(...signals);
                    this.scheduleBatch();
                }
                
                // Add enhanced signals to batch
                addEnhancedSignals(signals) {
                    if (!signals || !Array.isArray(signals)) return;
                    this.pendingUpdates.enhanced_signals.push(...signals);
                    this.scheduleBatch();
                }
                
                // Mark that markers need updating
                markersNeedUpdate() {
                    this.pendingUpdates.markers = true;
                    this.scheduleBatch();
                }
                
                // Add debug panel update
                updateDebugPanel(updates) {
                    Object.assign(this.pendingUpdates.debug_panel, updates);
                    this.scheduleBatch();
                }
                
                // Schedule batched update (debounced)
                scheduleBatch() {
                    if (this.isProcessing) return;
                    
                    if (this.batchTimeout) {
                        clearTimeout(this.batchTimeout);
                    }
                    
                    this.batchTimeout = setTimeout(() => {
                        this.processBatch();
                    }, 16); // ~60fps batching
                }
                
                // Process all pending updates in a single batch
                processBatch() {
                    if (this.isProcessing) return;
                    this.isProcessing = true;
                    
                    try {
                        // SILENCED: Excessive batch update logging disabled
                        // console.log('🎯 BATCH UPDATE: Processing batched chart updates...', {
                        //     fractals: this.pendingUpdates.fractals.length,
                        //     swings: this.pendingUpdates.swings.length,
                        //     fibonacci: !!this.pendingUpdates.fibonacci,
                        //     abc_patterns: !!this.pendingUpdates.abc_patterns.patterns,
                        //     signals: this.pendingUpdates.signals.length,
                        //     enhanced_signals: this.pendingUpdates.enhanced_signals.length,
                        //     markers: this.pendingUpdates.markers
                        // });
                        
                        // 1. Process fractals (accumulate and sync)
                        if (this.pendingUpdates.fractals.length > 0) {
                            this.pendingUpdates.fractals.forEach(fractal => {
                                const exists = window.accumulatedFractals.some(f => 
                                    f.timestamp === fractal.timestamp && f.fractal_type === fractal.fractal_type
                                );
                                if (!exists) {
                                    window.accumulatedFractals.push(fractal);
                                    // Also sync with the local array reference
                                    accumulatedFractals.push(fractal);
                                }
                            });
                            // Silenced: console.log(`🔺 Batched: ${this.pendingUpdates.fractals.length} fractals (total: ${window.accumulatedFractals.length})`);
                            
                            // Update fractal manager directly
                            if (fractalManager && document.getElementById('showFractals').checked) {
                                fractalManager.loadAllFractals(window.accumulatedFractals);
                            }
                        }
                        
                        // 2. Process swings (accumulate and update)
                        if (this.pendingUpdates.swings.length > 0) {
                            this.pendingUpdates.swings.forEach(swing => {
                                const exists = accumulatedSwings.some(s => 
                                    s.start_fractal.timestamp === swing.start_fractal.timestamp && 
                                    s.end_fractal.timestamp === swing.end_fractal.timestamp &&
                                    s.direction === swing.direction
                                );
                                if (!exists) {
                                    accumulatedSwings.push(swing);
                                }
                            });
                            
                            // Update swing display once
                            if (document.getElementById('showSwings').checked && swingLineManager) {
                                swingLineManager.loadAllSwings(accumulatedSwings);
                            }
                            // Silenced: console.log(`📈 Batched: ${this.pendingUpdates.swings.length} swings`);
                        }
                        
                        // 3. Process Fibonacci levels (update once)
                        if (this.pendingUpdates.fibonacci) {
                            const { fibLevels, dominantSwing } = this.pendingUpdates.fibonacci;
                            accumulatedFibonacci = fibLevels;
                            accumulatedDominantSwing = dominantSwing;
                            
                            if (document.getElementById('showFibonacci').checked && fibonacciManager) {
                                fibonacciManager.updateFibonacciLevels(fibLevels, dominantSwing);
                            }
                            // Silenced: console.log(`📐 Batched: Fibonacci levels updated`);
                        }
                        
                        // 4. Process ABC patterns (update once)
                        if (this.pendingUpdates.abc_patterns.patterns) {
                            const { patterns, dominantSwing } = this.pendingUpdates.abc_patterns;
                            accumulatedABCPatterns = patterns;
                            
                            if (document.getElementById('showABC') && document.getElementById('showABC').checked && abcPatternManager) {
                                abcPatternManager.loadAllABCPatterns(patterns, dominantSwing);
                            }
                            // Silenced: console.log(`🌊 Batched: ABC patterns updated`);
                        }
                        
                        // 5. Build complete marker collection
                        let finalMarkers = [];
                        let shouldUpdateMarkers = false;
                        
                        // Add signal markers
                        if (this.pendingUpdates.signals.length > 0) {
                            this.pendingUpdates.signals.forEach(signal => {
                                const marker = {
                                    time: Math.floor(new Date(signal.timestamp).getTime() / 1000),
                                    position: signal.signal_type === 'buy' ? 'belowBar' : 'aboveBar',
                                    color: signal.signal_type === 'buy' ? '#26a69a' : '#ef5350',
                                    shape: signal.signal_type === 'buy' ? 'arrowUp' : 'arrowDown',
                                    text: '',
                                    size: 2
                                };
                                
                                const existingIndex = finalMarkers.findIndex(m => m.time === marker.time);
                                if (existingIndex === -1) {
                                    finalMarkers.push(marker);
                                    shouldUpdateMarkers = true;
                                }
                            });
                            // Silenced: console.log(`📊 Batched: ${this.pendingUpdates.signals.length} signals`);
                        }
                        
                        // Add enhanced signal markers
                        if (this.pendingUpdates.enhanced_signals.length > 0) {
                            this.pendingUpdates.enhanced_signals.forEach(signal => {
                                const marker = {
                                    time: Math.floor(new Date(signal.timestamp).getTime() / 1000),
                                    position: signal.signal_type === 'buy' ? 'belowBar' : 'aboveBar',
                                    color: signal.signal_type === 'buy' ? '#00ff88' : '#ff4444',
                                    shape: signal.signal_type === 'buy' ? 'arrowUp' : 'arrowDown',
                                    text: `${signal.quality || 'N/A'}\\n${signal.pattern_type || 'N/A'}\\n${signal.confluence_score ? signal.confluence_score.toFixed(0) : '0'}%`,
                                    size: 4
                                };
                                
                                const existingIndex = finalMarkers.findIndex(m => 
                                    m.time === marker.time && m.color === marker.color
                                );
                                if (existingIndex === -1) {
                                    finalMarkers.push(marker);
                                    shouldUpdateMarkers = true;
                                }
                            });
                            // Silenced: console.log(`⭐ Batched: ${this.pendingUpdates.enhanced_signals.length} enhanced signals`);
                        }
                        
                        // 6. Handle fractal markers through unified manager
                        if (this.pendingUpdates.fractals.length > 0 && window.unifiedMarkerManager) {
                            // Add new fractals through unified manager
                            this.pendingUpdates.fractals.forEach(fractal => {
                                window.unifiedMarkerManager.addFractal(fractal);
                            });
                            // Silenced: console.log(`🔺 Batched: Added ${this.pendingUpdates.fractals.length} fractals through unified manager`);
                        }
                        
                        // 7. Update signal markers through unified manager (no race conditions)
                        if (shouldUpdateMarkers && window.unifiedMarkerManager) {
                            // Remove old signal markers and add new ones through unified manager
                            window.unifiedMarkerManager.removeMarkersByPattern('signal_');
                            window.unifiedMarkerManager.removeMarkersByPattern('enhanced_signal_');

                            // Add new signal markers
                            finalMarkers.forEach((marker, index) => {
                                const signalType = marker.size === 4 ? 'enhanced_signal' : 'signal';
                                const id = `${signalType}_${marker.time}_${index}`;
                                window.unifiedMarkerManager.setMarker(id, marker);
                            });

                            // Silenced: console.log(`🎯 Batched: Updated ${finalMarkers.length} signal markers through unified manager`);
                        }
                        
                        // 7. Update debug panel once
                        if (Object.keys(this.pendingUpdates.debug_panel).length > 0) {
                            Object.entries(this.pendingUpdates.debug_panel).forEach(([key, value]) => {
                                const element = document.getElementById(key);
                                if (element) {
                                    element.textContent = value;
                                }
                            });
                            // Silenced: console.log(`📊 Batched: Debug panel updated`);
                        }
                        
                        // Silenced: console.log('✅ BATCH UPDATE: Completed - Chart updated with single redraw');
                        
                    } catch (error) {
                        console.error('❌ Error in batch update:', error);
                    } finally {
                        // Reset all pending updates
                        this.pendingUpdates = {
                            fractals: [],
                            swings: [],
                            fibonacci: null,
                            abc_patterns: [],
                            signals: [],
                            enhanced_signals: [],
                            markers: false,
                            debug_panel: {}
                        };
                        this.isProcessing = false;
                        this.batchTimeout = null;
                    }
                }
                
                // Force immediate batch processing
                flushBatch() {
                    if (this.batchTimeout) {
                        clearTimeout(this.batchTimeout);
                        this.batchTimeout = null;
                    }
                    this.processBatch();
                }
            }
            
            // Global chart update batcher instance
            let chartUpdateBatcher = null;
            
            // ✅ SIMPLIFIED UPDATE SYSTEM - Handle backtest updates directly
            function handleBacktestUpdate(data) {
                if (!data || !unifiedMarkerManager) return;

                // Only process if there are actual updates to avoid continuous logging
                const hasUpdates = data.strategy_results && (
                    data.strategy_results.new_fractal ||
                    data.strategy_results.new_swing ||
                    data.strategy_results.new_signals ||
                    data.strategy_results.enhanced_signals
                );

                if (!hasUpdates) return; // Skip if no meaningful updates
                
                // NOTE: Don't update currentPosition here as it causes position jumps
                // currentPosition is managed by replay controls, not backend responses
                totalBars = data.total_bars;
                
                // Prepare debug panel updates
                let debugUpdates = {};
                
                // Process strategy results with minimal updates
                if (data.strategy_results) {
                    const results = data.strategy_results;

                    // 1. Process new fractals directly through unified manager
                    if (results.new_fractal && document.getElementById('showFractals').checked) {
                        unifiedMarkerManager.addFractal(results.new_fractal);
                        // Add to accumulated array for other systems
                        const exists = accumulatedFractals.some(f =>
                            f.timestamp === results.new_fractal.timestamp && f.fractal_type === results.new_fractal.fractal_type
                        );
                        if (!exists) {
                            accumulatedFractals.push(results.new_fractal);
                        }
                    }

                    // 2. Process signals directly through unified manager
                    if (results.new_signals && results.new_signals.length > 0 && document.getElementById('showSignals').checked) {
                        unifiedMarkerManager.loadSignals(results.new_signals, 'signal');
                    }

                    // 3. Process enhanced signals directly through unified manager
                    if (results.enhanced_signals && results.enhanced_signals.length > 0 && document.getElementById('showEnhancedSignals') && document.getElementById('showEnhancedSignals').checked) {
                        results.enhanced_signals.forEach(signal => {
                            const enhancedSignalData = {
                                timestamp: signal.timestamp,
                                signal_type: signal.signal_type,
                                text: `${signal.quality || 'N/A'}\\n${signal.pattern_type || 'N/A'}\\n${signal.confluence_score ? signal.confluence_score.toFixed(0) : '0'}%`,
                                size: 4
                            };
                            unifiedMarkerManager.addSignal(enhancedSignalData, 'enhanced_signal');
                        });
                    }

                    // Skip complex swing/fibonacci/ABC processing to eliminate continuous updates
                    return; // Exit early to prevent further processing
                }
            }

            // ❌ MALFORMED FUNCTION REMOVED - The correct initChart function is defined below
            
            // Initialize TradingView Chart
            function initChart() {
                try {
                    console.log('🎯 DEBUG: initChart starting...');
                    
                    // Check if LightweightCharts is available
                    if (typeof LightweightCharts === 'undefined') {
                        console.error('❌ TradingView LightweightCharts library not loaded!');
                        updateStatus('Error: TradingView library not loaded');
                        return;
                    }
                    console.log('✅ LightweightCharts library available');

                    const chartContainer = document.getElementById('chartDiv');
                    if (!chartContainer) {
                        console.error('❌ Chart container not found!');
                        updateStatus('Error: Chart container not found');
                        return;
                    }
                    console.log('✅ Chart container found:', chartContainer);

                    if (chart) {
                        console.log('🔄 Removing existing chart...');
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
                console.log('✅ Chart created successfully');
                
                // Create candlestick series
                candlestickSeries = chart.addCandlestickSeries({
                    upColor: '#26a69a',
                    downColor: '#ef5350',
                    borderVisible: false,
                    wickUpColor: '#26a69a',
                    wickDownColor: '#ef5350',
                });
                
                // 🚨 CRITICAL: Make candlestickSeries globally accessible
                window.candlestickSeries = candlestickSeries;
                
                console.log('✅ Candlestick series created and made globally accessible');
                
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
                            // 🚨 CRITICAL FIX: Don't corrupt currentPosition with chart clicks
                            // currentPosition should only be changed by navigation buttons
                            // Just update the data inspector without changing position
                            updateDataInspector(marketData[barIndex], barIndex);
                            console.log(`🖱️ Chart clicked: showing data for bar ${barIndex} (timestamp: ${marketData[barIndex].timestamp})`);
                            console.log(`🔍 Current navigation position remains: ${currentPosition}`);
                        }
                    }
                });
                
                console.log('Chart initialized successfully!');
                
                // ✅ Initialize unified marker management system
                unifiedMarkerManager = new UnifiedMarkerManager(candlestickSeries);
                window.unifiedMarkerManager = unifiedMarkerManager; // Make globally accessible
                console.log('✅ Unified marker manager initialized');

                // Legacy compatibility during transition
                fractalManager = unifiedMarkerManager; // Point to unified manager for compatibility

                swingLineManager = new SwingLineManager(candlestickSeries);
                fibonacciManager = new FibonacciLevelManager(candlestickSeries);
                abcPatternManager = new ABCPatternManager(candlestickSeries);
                lookbackManager = new LookbackIndicatorManager();
                supplyDemandManager = new SupplyDemandZoneManager(candlestickSeries);

                // ✅ Chart update batcher disabled - using UnifiedMarkerManager only
                chartUpdateBatcher = null; // Disable to prevent conflicts
                window.chartUpdateBatcher = null;
                console.log('✅ Chart update batcher disabled - using unified manager only');
                
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
                // SILENCED: console.log(`🎯 DEBUG: updateChart called with ${data ? data.length : 0} bars`);
                
                if (!chart || !candlestickSeries) {
                    // SILENCED: console.log('🎯 Chart not initialized, calling initChart...');
                    initChart();
                }

                if (!data || data.length === 0) {
                    console.error('❌ No data provided to updateChart');
                    updateStatus('Error: No data to display');
                    return;
                }

                // Store full market data for progressive replay
                marketData = data;
                totalBars = data.length;

                // Reset panning flag and chart overlays for new data
                userHasManuallyPanned = false;

                // Clear all markers through unified manager (for new data load only)
                if (unifiedMarkerManager) {
                    unifiedMarkerManager.clearAll();
                }

                accumulatedFractals = []; // Clear accumulated fractals for new data
                accumulatedSwings = []; // Clear accumulated swings for new data

                // ✅ FIXED: Generate fullChartData immediately instead of clearing it
                window.fullChartData = data.map(bar => ({
                    time: Math.floor(new Date(bar.timestamp).getTime() / 1000),
                    open: bar.open,
                    high: bar.high,
                    low: bar.low,
                    close: bar.close,
                    volume: bar.volume || 0
                }));

                console.log(`🎯 DEBUG: Generated fullChartData with ${window.fullChartData.length} bars`);
                console.log(`🎯 DEBUG: First bar:`, window.fullChartData[0]);
                console.log(`🎯 DEBUG: Last bar:`, window.fullChartData[window.fullChartData.length - 1]);

                window.currentBacktestPosition = 0;

                // Clear any existing position indicator
                if (window.currentPositionLine) {
                    candlestickSeries.removePriceLine(window.currentPositionLine);
                    window.currentPositionLine = null;
                }

                // 🚨 REMOVED: Don't clear markers during navigation - preserve accumulated markers
                // Markers should persist during navigation, only clear when loading new data
                
                // For backtesting: start at currentPosition (which is set by loadData to user's start date)
                updateChartProgressive(currentPosition);
            }
            
            
            // Progressive chart update for backtesting (shows data up to current position)
            function updateChartProgressive(position) {
                // SILENCED: console.log(`🎯 DEBUG: updateChartProgressive called with position=${position}, dataLength=${marketData ? marketData.length : 0}`);
                
                if (!chart || !candlestickSeries || !marketData) {
                    console.error('❌ Missing required objects:', { chart: !!chart, candlestickSeries: !!candlestickSeries, marketData: !!marketData });
                    return;
                }

                // Convert user position to data array position
                const dataPosition = (window.userStartOffset || 0) + position;
                // SILENCED: console.log(`🎯 DEBUG: dataPosition=${dataPosition}, userStartOffset=${window.userStartOffset || 0}`);
                
                // Ensure we don't go out of bounds
                if (dataPosition >= marketData.length) {
                    console.warn(`Position ${dataPosition} exceeds data length ${marketData.length}`);
                    return;
                }

                // Progressive loading: convert and show only data up to current position
                if (!window.fullChartData) {
                    debugLog('performance', `📊 Converting full dataset ${marketData.length} bars for progressive loading...`);
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
                    debugLog('performance', `🎯 DEBUG: Setting chart data with ${progressiveData.length} bars (position 0 to ${dataPosition})`);
                    
                    // 🚨 CRITICAL FIX: Proper marker persistence during setData()
                    let markersToRestore = [];
                    let hasMarkersToRestore = false;
                    
                    if (unifiedMarkerManager && unifiedMarkerManager.getMarkerCount() > 0) {
                        // Get all current markers for restoration
                        markersToRestore = Array.from(unifiedMarkerManager.markers.values());
                        hasMarkersToRestore = markersToRestore.length > 0;
                        console.log(`🔍 SAVING ${markersToRestore.length} markers before setData operation`);
                    }
                    
                    // Call setData which will clear all markers
                    candlestickSeries.setData(progressiveData);
                    console.log(`🔍 setData() completed - all markers cleared by TradingView`);
                    
                    // 🚨 IMMEDIATE RESTORATION: Don't wait, restore markers immediately
                    if (hasMarkersToRestore) {
                        console.log(`🔍 IMMEDIATELY restoring ${markersToRestore.length} markers`);
                        
                        // Method 1: Direct series setMarkers call
                        try {
                            candlestickSeries.setMarkers(markersToRestore);
                            console.log(`✅ Direct setMarkers successful`);
                        } catch (e) {
                            console.error(`❌ Direct setMarkers failed:`, e);
                        }
                        
                        // Method 2: Force unified manager to restore its state 
                        setTimeout(() => {
                            console.log(`🔍 BACKUP: Forcing unified manager update`);
                            if (unifiedMarkerManager) {
                                unifiedMarkerManager.forceUpdate();
                            }
                        }, 10);
                    }
                    
                    debugLog('performance', `📊 Chart reset: showing ${progressiveData.length}/${window.fullChartData.length} bars (up to position ${dataPosition})`);
                } else if (window.lastChartPosition < dataPosition) {
                    // Add new bars incrementally to avoid jumping - markers should persist
                    for (let i = window.lastChartPosition + 1; i <= dataPosition; i++) {
                        if (window.fullChartData[i]) {
                            candlestickSeries.update(window.fullChartData[i]);
                        }
                    }
                    debugLog('performance', `📊 Incremental update: added ${dataPosition - window.lastChartPosition} bars (now at position ${dataPosition})`);
                    // Note: Incremental updates via .update() should preserve markers
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
                        
                        // 🚨 CRITICAL FIX: setVisibleRange might interfere with markers
                        // Store markers before range change
                        let rangeChangeMarkers = [];
                        if (unifiedMarkerManager && unifiedMarkerManager.getMarkerCount() > 0) {
                            rangeChangeMarkers = Array.from(unifiedMarkerManager.markers.values());
                            console.log(`🔍 Saving ${rangeChangeMarkers.length} markers before setVisibleRange`);
                        }
                        
                        // Use built-in range setting for progressive data
                        console.log('🔍 Calling setVisibleRange...');
                        chart.timeScale().setVisibleRange({ from: startTime, to: endTime });
                        userHasManuallyPanned = false;
                        
                        // 🚨 IMMEDIATE RESTORATION after range change
                        if (rangeChangeMarkers.length > 0) {
                            console.log(`🔍 IMMEDIATELY restoring ${rangeChangeMarkers.length} markers after setVisibleRange`);
                            try {
                                candlestickSeries.setMarkers(rangeChangeMarkers);
                                console.log(`✅ Markers restored after setVisibleRange`);
                            } catch (e) {
                                console.error(`❌ Failed to restore markers after setVisibleRange:`, e);
                            }
                        }
                        
                        // Additional backup restoration
                        setTimeout(() => {
                            console.log('🔍 BACKUP: Force manager update after setVisibleRange');
                            if (unifiedMarkerManager) {
                                unifiedMarkerManager.forceUpdate();
                            }
                        }, 20);
                        
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

                // ✅ RESTORED: Direct marker updates for continuous visibility  
                // 🔍 DEBUG: Log fractal state before updateAllMarkers
                console.log(`🔍 BEFORE updateAllMarkers: local=${accumulatedFractals.length}, global=${window.accumulatedFractals ? window.accumulatedFractals.length : 0}, checkbox=${document.getElementById('showFractals').checked}`);
                console.log(`🔍 candlestickSeries object:`, candlestickSeries);
                console.log(`🔍 unifiedMarkerManager.series same as candlestickSeries?`, unifiedMarkerManager && unifiedMarkerManager.series === candlestickSeries);
                
                // Update markers immediately
                updateAllMarkers();
                
                console.log(`🔍 AFTER updateAllMarkers: unified manager has ${unifiedMarkerManager ? unifiedMarkerManager.getMarkerCount() : 'no manager'} markers`);
                
                // 🚨 CRITICAL: Final marker persistence verification
                setTimeout(() => {
                    const managerCount = unifiedMarkerManager ? unifiedMarkerManager.getMarkerCount() : 0;
                    console.log(`🔍 100ms VERIFICATION: Manager has ${managerCount} markers`);
                    
                    // If manager has markers but they're not visible, force restoration
                    if (unifiedMarkerManager && managerCount > 0) {
                        console.log('🔍 FINAL FORCE: Ensuring markers are visible');
                        const allMarkers = Array.from(unifiedMarkerManager.markers.values());
                        try {
                            candlestickSeries.setMarkers(allMarkers);
                            console.log(`✅ FINAL: ${allMarkers.length} markers forcibly restored`);
                        } catch (e) {
                            console.error(`❌ FINAL restoration failed:`, e);
                        }
                    } else if (managerCount === 0) {
                        // Check if we should have markers from accumulated data
                        const fractalSource = (accumulatedFractals.length > 0) ? accumulatedFractals : window.accumulatedFractals;
                        const shouldHaveMarkers = document.getElementById('showFractals').checked && fractalSource && fractalSource.length > 0;
                        
                        if (shouldHaveMarkers) {
                            console.log(`🚨 EMERGENCY: Manager empty but should have ${fractalSource.length} fractals - rebuilding`);
                            unifiedMarkerManager.loadFractals(fractalSource);
                            unifiedMarkerManager.forceUpdate();
                        }
                    }
                }, 100);
            }
            
            // ✅ RESTORED - Direct fractal loading for continuous visibility
            function addFractalsToChart(fractals) {
                if (!fractals || !fractalManager) return;
                
                console.log(`🔺 DIRECT: Loading ${fractals.length} fractals to chart`);
                
                // Add each fractal to the manager for immediate display
                fractals.forEach(fractal => {
                    const fractalData = {
                        timestamp: fractal.timestamp,
                        fractal_type: fractal.type || fractal.fractal_type, // Handle both formats
                        bar_index: fractal.bar_index
                    };
                    
                    // Add to accumulated array and display immediately
                    const exists = accumulatedFractals.some(f => 
                        f.timestamp === fractalData.timestamp && f.fractal_type === fractalData.fractal_type
                    );
                    
                    if (!exists) {
                        accumulatedFractals.push(fractalData);
                        window.accumulatedFractals.push(fractalData); // Sync with global reference
                    }
                });
                
                // Update fractal manager with all accumulated fractals
                fractalManager.loadAllFractals(accumulatedFractals);
            }
            
            // Add swings to chart
            function addSwingsToChart(swings) {
                if (!swingLineManager || !swings || swings.length === 0) return;
                
                // Convert swings to proper format and add to accumulated swings
                const convertedSwings = swings.map(swing => ({
                    start_fractal: {
                        timestamp: swing.start_timestamp,
                        price: swing.start_price
                    },
                    end_fractal: {
                        timestamp: swing.end_timestamp,
                        price: swing.end_price
                    },
                    direction: swing.direction,
                    points: swing.points || Math.abs(swing.end_price - swing.start_price),
                    bars: swing.bars || 0,
                    is_dominant: swing.is_dominant || false
                }));
                
                // Add to accumulated swings and load via manager
                accumulatedSwings.push(...convertedSwings);
                swingLineManager.loadAllSwings(convertedSwings);
                
                console.log(`📊 Loaded ${swings.length} swing lines from database`);
            }
            
            // ✅ SIGNALS: Use unified manager directly (no batching conflicts)
            function addSignalsToChart(signals) {
                if (!signals || !unifiedMarkerManager) return;

                // Use unified manager directly to prevent conflicts
                unifiedMarkerManager.loadSignals(signals, 'signal');
            }
            
            // Dynamic chart update functions for real-time strategy visualization
            
            // Track last update time to prevent rapid calls
            let lastUpdateAllMarkersCall = 0;
            
            // ✅ UNIFIED MARKER SYSTEM - No more flashing or race conditions
            function updateAllMarkers() {
                try {
                    // Prevent rapid successive calls
                    const now = Date.now();
                    const timeSinceLastCall = now - lastUpdateAllMarkersCall;
                    
                    console.log(`🔄 updateAllMarkers CALLED - ${timeSinceLastCall}ms since last call`);
                    
                    if (timeSinceLastCall < 50) {
                        console.log('🚨 THROTTLED: updateAllMarkers called too rapidly, skipping');
                        return;
                    }
                    
                    lastUpdateAllMarkersCall = now;
                    
                    console.trace();
                    debugLog('markers', '🔄 Updating all chart markers and lines...');

                    // Safety check for unified manager
                    if (!unifiedMarkerManager) {
                        console.warn('Unified marker manager not initialized yet');
                        return;
                    }

                    // Handle fractals
                    const showFractals = document.getElementById('showFractals').checked;
                    
                    // 🚨 CRITICAL FIX: Use consistent fractal source (check both local and global)
                    const fractalSource = (accumulatedFractals.length > 0) ? accumulatedFractals : window.accumulatedFractals;
                    const totalFractals = fractalSource ? fractalSource.length : 0;
                    
                    debugLog('markers', `🔄 Processing fractals: checkbox=${showFractals}, accumulated=${totalFractals} (local: ${accumulatedFractals.length}, global: ${window.accumulatedFractals ? window.accumulatedFractals.length : 0})`);
                    
                    if (!showFractals) {
                        unifiedMarkerManager.removeMarkersByPattern('fractal_');
                        debugLog('markers', 'Fractals hidden by checkbox');
                    } else {
                        // Load all accumulated fractals using unified manager
                        if (fractalSource && totalFractals > 0) {
                            unifiedMarkerManager.loadFractals(fractalSource);
                            debugLog('markers', `📍 Showing ${totalFractals} fractals from ${fractalSource === accumulatedFractals ? 'local' : 'global'} source`);
                        } else {
                            debugLog('markers', 'No fractals accumulated in either local or global arrays');
                        }
                    }
                    
                    // Handle swing lines
                    const showSwings = document.getElementById('showSwings').checked;
                    debugLog('markers', `🔄 Processing swings: checkbox=${showSwings}, accumulated=${accumulatedSwings.length}`);
                    if (!showSwings) {
                        swingLineManager.removeAllSwingLines();
                        debugLog('markers', 'Swing lines hidden by checkbox');
                    } else {
                        // Load all accumulated swings using proper line management
                        if (accumulatedSwings.length > 0) {
                            swingLineManager.loadAllSwings(accumulatedSwings);
                            debugLog('markers', `📈 Showing ${accumulatedSwings.length} swing lines`);
                        } else {
                            debugLog('markers', 'No swings accumulated yet');
                        }
                    }

                    // Handle Fibonacci levels
                    if (!document.getElementById('showFibonacci').checked) {
                        fibonacciManager.clearFibonacci();
                        debugLog('markers', 'Fibonacci levels hidden by checkbox');
                    } else {
                        // Show Fibonacci levels for the dominant swing
                        if (accumulatedFibonacci && accumulatedFibonacci.length > 0 && accumulatedDominantSwing) {
                            fibonacciManager.updateFibonacciLevels(accumulatedFibonacci, accumulatedDominantSwing);
                            console.log(`📐 Showing ${accumulatedFibonacci.length} Fibonacci levels`);
                        } else {
                            console.log('No Fibonacci levels or dominant swing available yet');
                        }
                    }

                    // Handle ABC patterns - CAREFULLY avoid clearing recently added patterns
                    const showABC = document.getElementById('showABC') ? document.getElementById('showABC').checked : false;
                    console.log(`🔄 Processing ABC: checkbox=${showABC}, accumulated=${accumulatedABCPatterns ? accumulatedABCPatterns.length : 0}`);
                    
                    // 🚨 CRITICAL FIX: Only clear ABC patterns if checkbox is explicitly unchecked
                    // Do NOT interfere with recently added patterns
                    if (!showABC) {
                        if (abcPatternManager) {
                            abcPatternManager.clearABCPatterns();
                            console.log('ABC patterns hidden by checkbox');
                        }
                    } else {
                        // Only reload all patterns if we have accumulated patterns and no current patterns on display
                        if (accumulatedABCPatterns && accumulatedABCPatterns.length > 0) {
                            // Check if we already have patterns displayed
                            const currentPatternCount = abcPatternManager ? abcPatternManager.addedPatterns.size : 0;
                            
                            if (currentPatternCount === 0) {
                                // No patterns currently displayed, load all accumulated
                                if (abcPatternManager) {
                                    abcPatternManager.loadAllABCPatterns(accumulatedABCPatterns, accumulatedDominantSwing);
                                    console.log(`🌊 Loading ${accumulatedABCPatterns.length} accumulated ABC patterns`);
                                }
                            } else {
                                // Patterns already displayed, don't interfere
                                console.log(`🌊 ABC patterns already displayed (${currentPatternCount} patterns), skipping reload`);
                            }
                        } else {
                            console.log('No ABC patterns accumulated yet');
                        }
                    }

                    console.log('✅ Marker update completed successfully');
                } catch (error) {
                    console.error('❌ Error updating markers:', error);
                    // Don't throw - prevent browser freeze
                }
            }

            // ✅ LOOKBACK PERIOD INDICATOR MANAGER
            class LookbackIndicatorManager {
                constructor() {
                    this.lookbackLine = null;
                }
                
                updateLookbackIndicator(currentPosition) {
                    if (!chart || !window.fullChartData || currentPosition >= window.fullChartData.length) return;
                    
                    // Remove existing lookback line if it exists
                    this.removeLookbackLine();
                    
                    const lookbackCandles = parseInt(document.getElementById('lookbackCandles').value) || 140;
                    const lookbackPosition = Math.max(0, currentPosition - lookbackCandles);
                    
                    if (lookbackPosition < window.fullChartData.length) {
                        const lookbackTime = window.fullChartData[lookbackPosition].time;
                        
                        // Create a vertical line using line series (proper vertical line)
                        // Get price range for vertical line
                        const lookbackData = window.fullChartData[lookbackPosition];
                        const minPrice = lookbackData.low * 0.999; // Slightly below low
                        const maxPrice = lookbackData.high * 1.001; // Slightly above high
                        
                        // Create vertical line data points
                        const verticalLineData = [
                            { time: lookbackTime, value: minPrice },
                            { time: lookbackTime, value: maxPrice }
                        ];
                        
                        // Create line series for vertical lookback indicator
                        this.lookbackLine = chart.addLineSeries({
                            color: '#9E9E9E', // Gray color
                            lineWidth: 2,
                            lineStyle: 1, // Dashed line
                            priceLineVisible: false,
                            lastValueVisible: false,
                            title: `Lookback Start (${lookbackCandles} bars)`,
                            crosshairMarkerVisible: false
                        });
                        
                        this.lookbackLine.setData(verticalLineData);
                        
                        console.log(`📏 Vertical lookback line created at position ${lookbackPosition} (${lookbackCandles} bars from current ${currentPosition})`);
                    }
                }
                
                removeLookbackLine() {
                    if (this.lookbackLine) {
                        chart.removeSeries(this.lookbackLine);
                        this.lookbackLine = null;
                    }
                }
                
                isVisible() {
                    return document.getElementById('showLookbackLine')?.checked || false;
                }
            }
            
            // ✅ SUPPLY & DEMAND RECTANGLE DRAWING PLUGIN
            // Custom rectangle renderer for professional S&D zones

            // ✅ PROFESSIONAL SUPPLY & DEMAND ZONE MANAGER WITH PRICE LINES
            // Uses TradingView's native price line system for reliable zone display

            // ✅ ENHANCED SUPPLY & DEMAND ZONE MANAGER WITH RECTANGLE PLUGIN
            class SupplyDemandZoneManager {
                constructor(candlestickSeries) {
                    try {
                        
                        this.candlestickSeries = candlestickSeries;
                        this.chart = chart; // Use global chart variable
                        
                        // Verify chart is available
                        if (!this.chart) {
                            throw new Error('Chart not available for SupplyDemandZoneManager');
                        }
                        
                        this.zoneLineSeries = new Map(); // Store zone line series
                        this.addedZones = new Set();
                        this.zonesVisible = true;
                        this.currentBarIndex = 0; // Track current position for dynamic zones
                        this.allZones = []; // Store all zones for dynamic display
                        this.currentlyVisibleZones = new Set(); // Track which zones are currently visible

                        // Zone styling based on type (MT4 style colors)
                        this.zoneStyles = {
                            supply: {
                                topColor: '#ff4757',
                                bottomColor: '#ff6b7a',
                                lineWidth: 2
                            },
                            demand: {
                                topColor: '#2ed573',
                                bottomColor: '#48e68a',
                                lineWidth: 2
                            },
                            continuation: {
                                topColor: '#ffa502',
                                bottomColor: '#ffc107',
                                lineWidth: 2
                            }
                        };

                        // Manager initialized successfully
                    } catch (error) {
                        console.error('❌ Error initializing SupplyDemandZoneManager:', error);
                        throw error;
                    }
                }
                
                // Add individual zone using time-bounded line series (MT4 style)
                addZone(zone, currentBarIndex = null) {
                    try {
                        const zoneId = this.getZoneId(zone);

                        // Check if zone already added
                        if (this.addedZones.has(zoneId)) {
                            return;
                        }

                        // Get zone styling
                        const style = this.zoneStyles[zone.zone_type] || this.zoneStyles.supply;
                        
                        // Parse zone start time
                        const zoneStartTime = this.parseTime(zone.left_time);
                        if (!zoneStartTime) {
                            console.warn('Invalid zone start time:', zone.left_time);
                            return;
                        }

                        // Calculate zone end time (2-3 bars into future from current position)
                        const barsExtension = 3; // Extend 3 bars into future
                        const barDurationSeconds = 60; // 1 minute for M1 timeframe
                        const currentTime = currentBarIndex ? this.getCurrentBarTime(currentBarIndex) : zoneStartTime;
                        const zoneEndTime = currentTime + (barsExtension * barDurationSeconds);

                        // Create top line series
                        const topLineSeries = this.chart.addLineSeries({
                            color: style.topColor,
                            lineWidth: style.lineWidth,
                            lineStyle: 0, // Solid line
                            crosshairMarkerVisible: false,
                            lastValueVisible: false,
                            priceLineVisible: false
                        });

                        // Create bottom line series  
                        const bottomLineSeries = this.chart.addLineSeries({
                            color: style.bottomColor,
                            lineWidth: style.lineWidth,
                            lineStyle: 1, // Dashed line
                            crosshairMarkerVisible: false,
                            lastValueVisible: false,
                            priceLineVisible: false
                        });

                        // Set line data (horizontal lines from start to end time)
                        const topLineData = [
                            { time: zoneStartTime, value: zone.top_price },
                            { time: zoneEndTime, value: zone.top_price }
                        ];
                        
                        const bottomLineData = [
                            { time: zoneStartTime, value: zone.bottom_price },
                            { time: zoneEndTime, value: zone.bottom_price }
                        ];

                        topLineSeries.setData(topLineData);
                        bottomLineSeries.setData(bottomLineData);

                        // Store zone line series
                        this.zoneLineSeries.set(zoneId, {
                            zone: zone,
                            topSeries: topLineSeries,
                            bottomSeries: bottomLineSeries,
                            id: zoneId,
                            visible: this.zonesVisible,
                            startTime: zoneStartTime,
                            endTime: zoneEndTime
                        });

                        this.addedZones.add(zoneId);

                        // Zone added successfully - debug via UI panel

                    } catch (error) {
                        console.error('❌ Error adding S&D zone:', error);
                    }
                }

                // Parse time string to TradingView time format
                parseTime(timeStr) {
                    try {
                        if (!timeStr) return null;

                        // Handle ISO string format
                        if (typeof timeStr === 'string') {
                            const date = new Date(timeStr);
                            if (isNaN(date.getTime())) return null;
                            return Math.floor(date.getTime() / 1000); // Convert to Unix timestamp
                        }

                        // Handle Unix timestamp
                        if (typeof timeStr === 'number') {
                            return timeStr > 1000000000000 ? Math.floor(timeStr / 1000) : timeStr;
                        }

                        return null;
                    } catch (error) {
                        console.error('Error parsing time:', timeStr, error);
                        return null;
                    }
                }
                
                // Load multiple zones at once (MT4 style)
                loadAllZones(zones, currentBarIndex = null) {
                    console.log(`📦 Loading ${zones.length} S&D zones (MT4 style)...`);

                    // Clear existing zones first
                    this.clearZones();

                    // Add each zone with current bar context
                    zones.forEach(zone => {
                        this.addZone(zone, currentBarIndex);
                    });

                    console.log(`✅ Loaded ${this.zoneLineSeries.size} S&D line series zones`);
                }

                // Toggle zone visibility
                toggleZoneVisibility() {
                    this.zonesVisible = !this.zonesVisible;
                    
                    // Toggle visibility of all line series
                    this.zoneLineSeries.forEach(zoneData => {
                        try {
                            if (this.zonesVisible) {
                                // Show the series
                                zoneData.topSeries.applyOptions({ visible: true });
                                zoneData.bottomSeries.applyOptions({ visible: true });
                            } else {
                                // Hide the series
                                zoneData.topSeries.applyOptions({ visible: false });
                                zoneData.bottomSeries.applyOptions({ visible: false });
                            }
                            zoneData.visible = this.zonesVisible;
                        } catch (error) {
                            console.warn('Error toggling zone visibility:', error);
                        }
                    });

                    console.log(`📦 S&D zones ${this.zonesVisible ? 'shown' : 'hidden'}`);
                }

                // Filter zones by type
                filterZonesByType(zoneTypes) {
                    console.log(`📦 Filtering zones by type: ${zoneTypes.join(', ')}`);

                    // Toggle visibility instead of removing/re-adding
                    this.zoneLineSeries.forEach(zoneData => {
                        const shouldShow = zoneTypes.includes(zoneData.zone.zone_type) && this.zonesVisible;
                        try {
                            zoneData.topSeries.applyOptions({ visible: shouldShow });
                            zoneData.bottomSeries.applyOptions({ visible: shouldShow });
                            zoneData.visible = shouldShow;
                        } catch (error) {
                            console.warn('Error filtering zone visibility:', error);
                        }
                    });
                }

                // Filter zones by minimum strength
                filterZonesByStrength(minStrength) {
                    console.log(`📦 Filtering zones by minimum strength: ${minStrength}`);

                    // Toggle visibility based on strength
                    this.zoneLineSeries.forEach(zoneData => {
                        const strength = zoneData.zone.strength_score || 0;
                        const shouldShow = strength >= minStrength && this.zonesVisible;
                        try {
                            zoneData.topSeries.applyOptions({ visible: shouldShow });
                            zoneData.bottomSeries.applyOptions({ visible: shouldShow });
                            zoneData.visible = shouldShow;
                        } catch (error) {
                            console.warn('Error filtering zone by strength:', error);
                        }
                    });
                }

                // Clear all zones
                clearZones() {
                    // Remove all line series
                    this.zoneLineSeries.forEach(zoneData => {
                        try {
                            this.chart.removeSeries(zoneData.topSeries);
                            this.chart.removeSeries(zoneData.bottomSeries);
                        } catch (error) {
                            console.warn('Warning removing line series:', error);
                        }
                    });

                    this.zoneLineSeries.clear();
                    this.addedZones.clear();

                    // Zones cleared
                }
                
                // Generate unique zone ID
                getZoneId(zone) {
                    return zone.id || `${zone.symbol}_${zone.timeframe}_${zone.zone_type}_${zone.left_time}_${zone.top_price}_${zone.bottom_price}`;
                }

                // Get zone statistics
                getZoneStats() {
                    const stats = {
                        total: this.zoneLineSeries.size,
                        supply: 0,
                        demand: 0,
                        continuation: 0,
                        visible: Array.from(this.zoneLineSeries.values()).filter(zoneData => zoneData.visible !== false).length
                    };

                    this.zoneLineSeries.forEach(zoneData => {
                        if (zoneData.zone && zoneData.zone.zone_type) {
                            stats[zoneData.zone.zone_type] = (stats[zoneData.zone.zone_type] || 0) + 1;
                        }
                    });

                    return stats;
                }

                // Update all zone line series (useful for chart updates)
                updateAllZones(currentBarIndex = null) {
                    if (currentBarIndex !== null) {
                        this.updateZoneExtensions(currentBarIndex);
                    }
                    console.log(`📦 Updated ${this.zoneLineSeries.size} S&D zones`);
                }

                // Get zones by type
                getZonesByType(zoneType) {
                    return Array.from(this.zoneLineSeries.values()).filter(zoneData => zoneData.zone.zone_type === zoneType);
                }

                // Remove specific zone
                removeZone(zoneId) {
                    const zoneData = this.zoneLineSeries.get(zoneId);
                    if (zoneData) {
                        // Remove line series
                        try {
                            this.chart.removeSeries(zoneData.topSeries);
                            this.chart.removeSeries(zoneData.bottomSeries);
                        } catch (error) {
                            console.warn('Warning removing specific line series:', error);
                        }
                        
                        // Remove from collections
                        this.zoneLineSeries.delete(zoneId);
                        this.addedZones.delete(zoneId);
                        
                        console.log(`🗑️ Removed zone: ${zoneId}`);
                    }
                }
                
                // Get current bar time for dynamic zone extension
                getCurrentBarTime(barIndex) {
                    if (window.fullChartData && barIndex < window.fullChartData.length) {
                        return window.fullChartData[barIndex].time;
                    }
                    return Math.floor(Date.now() / 1000); // Fallback to current time
                }
                
                // Update zone extensions based on current bar position
                updateZoneExtensions(currentBarIndex) {
                    this.currentBarIndex = currentBarIndex;
                    
                    // Update each zone's end time to extend from current position
                    this.zoneLineSeries.forEach(zoneData => {
                        try {
                            const barsExtension = 3;
                            const barDurationSeconds = 60; // 1 minute for M1
                            const currentTime = this.getCurrentBarTime(currentBarIndex);
                            const newEndTime = currentTime + (barsExtension * barDurationSeconds);
                            
                            // Update line data with new end time
                            const topLineData = [
                                { time: zoneData.startTime, value: zoneData.zone.top_price },
                                { time: newEndTime, value: zoneData.zone.top_price }
                            ];
                            
                            const bottomLineData = [
                                { time: zoneData.startTime, value: zoneData.zone.bottom_price },
                                { time: newEndTime, value: zoneData.zone.bottom_price }
                            ];
                            
                            zoneData.topSeries.setData(topLineData);
                            zoneData.bottomSeries.setData(bottomLineData);
                            zoneData.endTime = newEndTime;
                            
                        } catch (error) {
                            console.warn('Error updating zone extension:', error);
                        }
                    });
                }
                
                // Store zones for dynamic display (MT4 style - zones appear when replay reaches them)
                storeZonesForDynamicDisplay(zones) {
                    this.allZones = zones;
                    
                    // Clear any existing zones
                    this.clearZones();
                    this.currentlyVisibleZones.clear();
                    
                    // Debug event
                    if (typeof addZoneDebugEvent === 'function') {
                        addZoneDebugEvent(`Loaded ${zones.length} zones for dynamic display`);
                    }
                }
                
                // Update dynamic zone display based on current bar position
                updateDynamicZoneDisplay(currentBarIndex) {
                    if (!this.allZones || this.allZones.length === 0) return;
                    
                    this.currentBarIndex = currentBarIndex;
                    const currentTime = this.getCurrentBarTime(currentBarIndex);
                    
                    this.allZones.forEach(zone => {
                        const zoneId = this.getZoneId(zone);
                        const zoneStartTime = this.parseTime(zone.left_time);
                        
                        // Check if zone should be visible (replay has reached the zone detection point)
                        if (zoneStartTime && currentTime >= zoneStartTime) {
                            // Zone should be visible
                            if (!this.currentlyVisibleZones.has(zoneId)) {
                                // Add the zone
                                this.addZone(zone, currentBarIndex);
                                this.currentlyVisibleZones.add(zoneId);
                                
                                // Debug event
                                if (typeof addZoneDebugEvent === 'function') {
                                    const timeStr = new Date(zoneStartTime * 1000).toISOString().substring(11, 19);
                                    addZoneDebugEvent(`${zone.zone_type.toUpperCase()} zone appeared at ${timeStr} (${zone.top_price.toFixed(2)}-${zone.bottom_price.toFixed(2)})`);
                                }
                                
                                // Update debug info
                                if (typeof updateZoneDebugInfo === 'function') {
                                    updateZoneDebugInfo();
                                }
                            } else {
                                // Zone already visible, just update its extension
                                this.updateZoneExtensions(currentBarIndex);
                            }
                        } else {
                            // Zone should not be visible yet
                            if (this.currentlyVisibleZones.has(zoneId)) {
                                // Remove the zone (shouldn't happen in forward replay, but useful for backward nav)
                                this.removeZone(zoneId);
                                this.currentlyVisibleZones.delete(zoneId);
                                
                                // Debug event
                                if (typeof addZoneDebugEvent === 'function') {
                                    addZoneDebugEvent(`${zone.zone_type.toUpperCase()} zone hidden (before detection)`);
                                }
                            }
                        }
                    });
                }
            }
            
            // Global lookback indicator manager
            let lookbackManager = null;
            
            // Global supply demand zone manager
            let supplyDemandManager = null;

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
                
                // Update lookback indicator
                if (lookbackManager && lookbackManager.isVisible()) {
                    lookbackManager.updateLookbackIndicator(position);
                }
            }

            // Load all accumulated strategy elements for current position
            async function loadAccumulatedStrategyElements(barIndex) {
                try {
                    // 🚨 TEMPORARY FIX: Completely disable this function to test marker persistence
                    console.log(`🚨 DISABLED: loadAccumulatedStrategyElements called for bar ${barIndex} - FUNCTION DISABLED FOR TESTING`);
                    return; // Exit immediately without doing anything
                    
                    // 🔍 DEBUG: Add stack trace to find who's calling this function
                    console.log(`🔍 STACK TRACE: loadAccumulatedStrategyElements called for bar ${barIndex}`);
                    console.trace();
                    
                    // Throttle calls to prevent resource exhaustion
                    const now = Date.now();
                    if (now - lastLoadAccumulatedCall < 200) { // Minimum 200ms between calls
                        debugLog('performance', `⏳ Throttling loadAccumulatedStrategyElements call for bar ${barIndex}`);
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
                            debugLog('performance', `📊 Strategy results: ${results.total_fractals || 0} total fractals, ${results.total_swings || 0} total swings`);
                            
                            // 🚨 CRITICAL FIX: Don't call loadAllStrategyElements to prevent infinite recursion
                            // Process the jump data directly without triggering a full reload
                            if (results.fractals && results.fractals.length > 0) {
                                const fractalData = results.fractals.map(fractal => ({
                                    timestamp: fractal.timestamp,
                                    fractal_type: fractal.type
                                }));
                                if (unifiedMarkerManager && document.getElementById('showFractals').checked) {
                                    unifiedMarkerManager.loadFractals(fractalData);
                                }
                            }
                            
                            debugLog('performance', `Loaded strategy elements for bar ${barIndex}`);
                        }
                    }
                } catch (error) {
                    console.error('Error loading strategy elements:', error);
                }
            }

            function loadAllFractalsToChart(fractals) {
                if (!fractals || !unifiedMarkerManager) return;

                // Use unified manager to load fractals (no race conditions)
                const fractalData = fractals.map(fractal => ({
                    timestamp: fractal.timestamp,
                    fractal_type: fractal.type
                }));

                unifiedMarkerManager.loadFractals(fractalData);
                debugLog('markers', `Loaded ${fractals.length} accumulated fractals through unified manager`);
            }

            // ✅ UNIFIED - Direct fractal processing for continuous visibility
            function addNewFractalToChart(fractal) {
                if (!fractal || !unifiedMarkerManager) return;

                // Add to accumulated fractals array
                const exists = accumulatedFractals.some(f =>
                    f.timestamp === fractal.timestamp && f.fractal_type === fractal.fractal_type
                );

                if (!exists) {
                    accumulatedFractals.push(fractal);
                    window.accumulatedFractals.push(fractal); // Sync with global reference
                    unifiedMarkerManager.addFractal(fractal); // No race conditions
                    // SILENCED: console.log(`🔺 UNIFIED: New ${fractal.fractal_type} fractal added to chart at ${fractal.timestamp} (bar ${fractal.bar_index})`);
                    // SILENCED: console.log(`🔺 ACCUMULATED: Total fractals now: ${accumulatedFractals.length}`);
                } else {
                    // SILENCED: console.log(`⚠️ DUPLICATE: Fractal at ${fractal.timestamp} already exists, skipping`);
                }
            }
            
            function addNewSwingToChart(swing) {
                if (!swing || !swingLineManager) return;
                
                // 🚨 CRITICAL FIX: Handle swing extensions properly
                // Check for exact duplicate (same start AND end)
                const exactDuplicate = accumulatedSwings.some(s => 
                    s.start_fractal.timestamp === swing.start_fractal.timestamp && 
                    s.end_fractal.timestamp === swing.end_fractal.timestamp &&
                    s.direction === swing.direction
                );
                
                if (exactDuplicate) {
                    // SILENCED: console.log(`⚠️ EXACT DUPLICATE: Swing already exists, skipping`);
                    return;
                }
                
                // Check for swing extension (same start, different end, same direction)
                const existingSwingIndex = accumulatedSwings.findIndex(s => 
                    s.start_fractal.timestamp === swing.start_fractal.timestamp && 
                    s.direction === swing.direction
                );
                
                if (existingSwingIndex !== -1) {
                    // This is a swing extension - replace the old swing
                    console.log(`🔄 SWING EXTENSION: Updating ${swing.direction} swing from ${swing.start_fractal.timestamp}`);
                    console.log(`   Old end: ${accumulatedSwings[existingSwingIndex].end_fractal.timestamp}`);
                    console.log(`   New end: ${swing.end_fractal.timestamp}`);
                    accumulatedSwings[existingSwingIndex] = swing;
                } else {
                    // This is a completely new swing
                    accumulatedSwings.push(swing);
                    console.log(`📈 NEW SWING: ${swing.direction} swing from ${swing.start_fractal.timestamp} to ${swing.end_fractal.timestamp}`);
                }
                
                // 🚨 CRITICAL: Recalculate dominance for all accumulated swings
                updateSwingDominance();
                
                // Reload all swings with updated data
                if (document.getElementById('showSwings').checked) {
                    swingLineManager.loadAllSwings(accumulatedSwings);
                }
            }
            
            function updateSwingDominance() {
                // 🚨 CRITICAL FIX: Don't override backend dominance logic!
                // The backend strategy already calculates dominance correctly using Elliott Wave principles
                // Frontend should RESPECT the backend's dominance determination, not recalculate it

                console.log('📊 Preserving backend-calculated swing dominance (no frontend override)');

                // Find the swing that's already marked as dominant by the backend
                let backendDominantSwing = null;
                accumulatedSwings.forEach(swing => {
                    if (swing.is_dominant) {
                        backendDominantSwing = swing;
                        const magnitude = Math.abs(swing.points || Math.abs(swing.end_fractal.price - swing.start_fractal.price));
                        console.log(`🎯 BACKEND DOMINANT: ${swing.direction.toUpperCase()} swing (${magnitude.toFixed(5)} pts / ${(magnitude*10000).toFixed(1)} pips) - PRESERVING`);
                    }
                });

                // Update market bias display based on backend's dominant swing
                if (backendDominantSwing) {
                    const magnitude = Math.abs(backendDominantSwing.points || Math.abs(backendDominantSwing.end_fractal.price - backendDominantSwing.start_fractal.price));
                    updateMarketBiasFromDominantSwing(backendDominantSwing, magnitude);

                    // 🚨 CRITICAL FIX: Update accumulatedDominantSwing for Fibonacci manager
                    accumulatedDominantSwing = {
                        start_timestamp: backendDominantSwing.start_fractal.timestamp,
                        end_timestamp: backendDominantSwing.end_fractal.timestamp,
                        start_price: backendDominantSwing.start_fractal.price,
                        end_price: backendDominantSwing.end_fractal.price,
                        direction: backendDominantSwing.direction
                    };
                    debugLog('swing_details', `🔄 Updated accumulatedDominantSwing for Fibonacci manager:`, accumulatedDominantSwing);
                } else {
                    console.warn('⚠️ No backend-dominant swing found in accumulated swings');
                    accumulatedDominantSwing = null; // Clear if no dominant swing
                }
            }
            
            function updateMarketBiasFromDominantSwing(dominantSwing, magnitude) {
                // Create market bias object based on the corrected dominant swing
                const marketBias = {
                    bias: dominantSwing.direction === 'up' ? 'BULLISH' : 'BEARISH',
                    direction: dominantSwing.direction === 'up' ? 'UP' : 'DOWN',
                    points: dominantSwing.points || magnitude,
                    trading_direction: dominantSwing.direction === 'up' ? 'LOOK FOR BUY OPPORTUNITIES' : 'LOOK FOR SELL OPPORTUNITIES'
                };
                
                console.log(`📊 CORRECTED Market Bias: ${marketBias.bias} (${marketBias.direction}) - ${marketBias.points.toFixed(5)} points (${(marketBias.points*10000).toFixed(1)} pips)`);
                updateMarketBiasDisplay(marketBias);
            }
            
            function addFibonacciLevelsToChart(fibLevels) {
                if (!fibLevels || !chart || !document.getElementById('showFibonacci').checked) return;

                // Update accumulated Fibonacci levels
                accumulatedFibonacci = fibLevels;

                // Extract dominant swing information if available
                if (fibLevels.length > 0 && fibLevels[0].swing_start_time && fibLevels[0].swing_end_time) {
                    accumulatedDominantSwing = {
                        start_timestamp: fibLevels[0].swing_start_time,
                        end_timestamp: fibLevels[0].swing_end_time,
                        start_price: fibLevels[0].swing_start_price,
                        end_price: fibLevels[0].swing_end_price,
                        direction: fibLevels[0].swing_direction
                    };
                }

                // Use the professional Fibonacci manager if available
                if (fibonacciManager && accumulatedDominantSwing) {
                    fibonacciManager.updateFibonacciLevels(fibLevels, accumulatedDominantSwing);
                    console.log(`📐 Updated ${fibLevels.length} Fibonacci levels using professional manager`);
                } else {
                    // Fallback to old method if manager not available
                    console.warn('FibonacciManager not available, using fallback method');

                    // Only show key levels (38.2%, 50%, 61.8%) to avoid clutter
                    const keyLevels = fibLevels.filter(level =>
                        level.level === 0.382 || level.level === 0.500 || level.level === 0.618
                    );

                    keyLevels.forEach(level => {
                        // Create horizontal line for each key Fibonacci level WITHOUT TITLE
                        const fibLine = chart.addLineSeries({
                            color: getFibonacciColor(level.level),
                            lineWidth: 0.5, // Thinner lines to reduce clutter
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
                if (!signals || !unifiedMarkerManager) return;

                // Use unified manager to add signals (no race conditions)
                unifiedMarkerManager.loadSignals(signals, 'signal');
                console.log(`Added ${signals.length} trading signals through unified manager`);
            }
            
            // Enhanced signals visualization with pattern confirmation details
            function addEnhancedSignalsToChart(enhancedSignals) {
                if (!enhancedSignals || !Array.isArray(enhancedSignals) || !unifiedMarkerManager) {
                    console.warn('Invalid enhanced signals data or unified manager not ready:', {
                        hasSignals: !!enhancedSignals,
                        isArray: Array.isArray(enhancedSignals),
                        hasManager: !!unifiedMarkerManager
                    });
                    return;
                }

                // Filter for truly new signals
                const newSignals = enhancedSignals.filter(signal => {
                    if (!signal || !signal.timestamp || !signal.price) return false;

                    return !enhancedSignalsData.find(existing =>
                        existing.timestamp === signal.timestamp &&
                        existing.price === signal.price &&
                        existing.signal_type === signal.signal_type
                    );
                });

                if (newSignals.length === 0) {
                    console.log('No new enhanced signals - keeping existing display');
                    return;
                }

                console.log(`Processing ${newSignals.length} NEW enhanced signals`);

                // Process new signals through unified manager
                newSignals.forEach(signal => {
                    try {
                        if (!signal || !signal.timestamp || !signal.price) return;

                        // Add enhanced signal through unified manager
                        const enhancedSignalData = {
                            timestamp: signal.timestamp,
                            signal_type: signal.signal_type,
                            text: `${signal.quality || 'N/A'}\\n${signal.pattern_type || 'N/A'}\\n${signal.confluence_score ? signal.confluence_score.toFixed(0) : '0'}%`,
                            size: 4
                        };

                        unifiedMarkerManager.addSignal(enhancedSignalData, 'enhanced_signal');

                        // Add horizontal lines for entry, stop loss, and take profit
                        const signalTime = Math.floor(new Date(signal.timestamp).getTime() / 1000);
                        addSignalLevelsToChart(signal, signalTime);

                        // Add to panel for new signals only
                        addSignalToPanel(signal);

                    } catch (error) {
                        console.error('Error processing individual signal:', error, signal);
                    }
                });

                console.log(`Added ${newSignals.length} enhanced trading signals through unified manager`);
            }
            
            // Add horizontal lines for signal levels (entry, stop, take profit)
            function addSignalLevelsToChart(signal, signalTime) {
                if (!chart) return;
                
                try {
                    // 🚨 ANTI-FLASHING: Check if lines already exist for this signal
                    const existingLines = enhancedSignalLines.find(line => 
                        line.timestamp === signal.timestamp && 
                        Math.abs(line.entryPrice - signal.price) < 0.0001
                    );
                    
                    if (existingLines) {
                        debugLog('markers', `Price lines already exist for signal at ${signal.timestamp} - skipping`);
                        return;
                    }
                    
                    // Entry level (signal price) - white line
                    const entryLine = chart.addPriceLine({
                        price: signal.price,
                        color: '#ffffff',
                        lineWidth: 2,
                        lineStyle: LightweightCharts.LineStyle.Solid,
                        axisLabelVisible: true,
                        title: `Entry: ${signal.price.toFixed(2)}`
                    });
                    
                    // Stop Loss level - red line
                    const stopLine = chart.addPriceLine({
                        price: signal.stop_loss,
                        color: '#ff4444',
                        lineWidth: 2,
                        lineStyle: LightweightCharts.LineStyle.Dashed,
                        axisLabelVisible: true,
                        title: `SL: ${signal.stop_loss.toFixed(2)}`
                    });
                    
                    // Take Profit level - green line
                    const takeProfitLine = chart.addPriceLine({
                        price: signal.take_profit,
                        color: '#44ff44',
                        lineWidth: 2,
                        lineStyle: LightweightCharts.LineStyle.Dashed,
                        axisLabelVisible: true,
                        title: `TP: ${signal.take_profit.toFixed(2)} (R:R ${signal.risk_reward_ratio ? signal.risk_reward_ratio.toFixed(1) : '2.0'}:1)`
                    });
                    
                    // Store references for cleanup with entry price for duplicate checking
                    enhancedSignalLines.push({
                        timestamp: signal.timestamp,
                        entryPrice: signal.price,
                        entryLine: entryLine,
                        stopLine: stopLine,
                        takeProfitLine: takeProfitLine
                    });
                    
                    debugLog('markers', `Added signal levels for ${signal.signal_type} at ${signal.price}`);
                } catch (error) {
                    console.error('Error adding signal levels:', error);
                }
            }
            
            // Clear enhanced signal lines
            function clearEnhancedSignalLines() {
                enhancedSignalLines.forEach(signalLevel => {
                    try {
                        if (signalLevel.entryLine) chart.removePriceLine(signalLevel.entryLine);
                        if (signalLevel.stopLine) chart.removePriceLine(signalLevel.stopLine);
                        if (signalLevel.takeProfitLine) chart.removePriceLine(signalLevel.takeProfitLine);
                    } catch (error) {
                        console.warn('Error removing signal line:', error);
                    }
                });
                enhancedSignalLines = [];
            }
            
            // Add signal to enhanced signals panel
            function addSignalToPanel(signal) {
                // Add to global data array
                enhancedSignalsData.push(signal);
                
                // Update the panel display
                updateEnhancedSignalsPanel();
            }
            
            // Update enhanced signals panel display
            function updateEnhancedSignalsPanel() {
                const signalsList = document.getElementById('enhancedSignalsList');
                const liveCount = document.getElementById('liveEnhancedSignalCount');
                
                if (!signalsList || !liveCount) return;
                
                // Update live count
                liveCount.textContent = enhancedSignalsData.length;
                
                if (enhancedSignalsData.length === 0) {
                    signalsList.innerHTML = `
                        <div style="color: #888; font-size: 0.9em; text-align: center; padding: 20px;">
                            No enhanced signals detected yet.<br>
                            Load data and navigate to see signals with pattern confirmation.
                        </div>
                    `;
                    return;
                }
                
                // Build signals list HTML
                let signalsHTML = '';
                enhancedSignalsData.slice(-10).reverse().forEach((signal, index) => { // Show last 10 signals, newest first
                    const timestamp = new Date(signal.timestamp).toLocaleString();
                    const qualityColor = signal.quality === 'strong' ? '#44ff44' : 
                                       signal.quality === 'moderate' ? '#ffaa44' : '#ff6666';
                    
                    signalsHTML += `
                        <div style="padding: 8px; margin: 4px 0; border: 1px solid #444; border-radius: 4px; background: rgba(0,0,0,0.5);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <span style="color: ${signal.signal_type === 'buy' ? '#44ff44' : '#ff4444'}; font-weight: bold;">
                                    ${signal.signal_type.toUpperCase()}
                                </span>
                                <span style="color: ${qualityColor}; font-size: 0.8em; font-weight: bold;">
                                    ${signal.quality.toUpperCase()}
                                </span>
                            </div>
                            <div style="font-size: 0.75em; color: #ccc; margin-bottom: 4px;">
                                ${timestamp}
                            </div>
                            <div style="font-size: 0.8em; color: #ddd;">
                                <div>📍 Entry: ${signal.price.toFixed(2)}</div>
                                <div>🛑 Stop: ${signal.stop_loss.toFixed(2)}</div>
                                <div>🎯 Target: ${signal.take_profit.toFixed(2)}</div>
                                <div>📊 Fib: ${(signal.fibonacci_level * 100).toFixed(1)}%</div>
                                <div>🔀 Pattern: ${signal.pattern_type}</div>
                                <div>⚡ Score: ${signal.confluence_score.toFixed(0)}% (${signal.factors.join(', ')})</div>
                                <div>💰 R:R: ${signal.risk_reward_ratio.toFixed(1)}:1</div>
                            </div>
                        </div>
                    `;
                });
                
                signalsList.innerHTML = signalsHTML;
            }
            
            // Clear all enhanced signals
            function clearAllEnhancedSignals() {
                enhancedSignalsData = [];
                clearEnhancedSignalLines();
                updateEnhancedSignalsPanel();

                // Remove enhanced signal markers through unified manager
                if (unifiedMarkerManager) {
                    unifiedMarkerManager.removeMarkersByPattern('enhanced_signal_');
                }

                console.log('Cleared all enhanced signals through unified manager');
            }
            
            // Export enhanced signals to CSV
            function exportEnhancedSignals() {
                if (enhancedSignalsData.length === 0) {
                    alert('No enhanced signals to export');
                    return;
                }
                
                // Create CSV content
                const headers = [
                    'Timestamp', 'Signal Type', 'Entry Price', 'Stop Loss', 'Take Profit', 
                    'Fibonacci Level', 'Pattern Type', 'Pattern Strength', 'Quality', 
                    'Confluence Score', 'Risk Reward Ratio', 'Factors'
                ];
                
                let csvContent = headers.join(',') + '\\n';
                
                enhancedSignalsData.forEach(signal => {
                    const row = [
                        signal.timestamp,
                        signal.signal_type,
                        signal.price.toFixed(2),
                        signal.stop_loss.toFixed(2),
                        signal.take_profit.toFixed(2),
                        (signal.fibonacci_level * 100).toFixed(1) + '%',
                        signal.pattern_type,
                        signal.pattern_strength,
                        signal.quality,
                        signal.confluence_score.toFixed(0),
                        signal.risk_reward_ratio.toFixed(1),
                        '"' + signal.factors.join('; ') + '"'
                    ];
                    csvContent += row.join(',') + '\\n';
                });
                
                // Download CSV file
                const blob = new Blob([csvContent], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `enhanced_signals_${new Date().toISOString().slice(0,19)}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                console.log(`Exported ${enhancedSignalsData.length} enhanced signals to CSV`);
            }
            
            // =====================================
            // SIGNAL PERFORMANCE ANALYTICS FUNCTIONS
            // =====================================
            
            async function refreshSignalAnalytics() {
                try {
                    const response = await fetch('/api/signals/analytics');
                    const result = await response.json();
                    
                    if (result.success) {
                        updateSignalPerformancePanel(result.analytics);
                    } else {
                        console.error('Failed to fetch signal analytics:', result.message);
                    }
                } catch (error) {
                    console.error('Error fetching signal analytics:', error);
                }
            }
            
            function updateSignalPerformancePanel(analytics) {
                // Update real-time stats first
                updateSignalPerformanceStats();
                
                if (!analytics || analytics.message) {
                    document.getElementById('signalAnalyticsDetails').innerHTML = `
                        <div style="color: #888; text-align: center; padding: 20px;">
                            ${analytics?.message || 'No signal performance data available'}
                        </div>
                    `;
                    return;
                }
                
                // Build detailed analytics HTML
                let analyticsHtml = '';
                
                // Overall performance
                if (analytics.overall_performance) {
                    const overall = analytics.overall_performance;
                    analyticsHtml += `
                        <div style="margin-bottom: 10px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;">
                            <strong>Overall Performance:</strong><br>
                            Total Signals: ${overall.total_signals}<br>
                            Win Rate: ${(overall.overall_win_rate * 100).toFixed(1)}%<br>
                            Active: ${overall.active_signals}
                        </div>
                    `;
                }
                
                // Quality performance
                if (analytics.quality_performance) {
                    analyticsHtml += '<div style="margin-bottom: 10px;"><strong>Quality Breakdown:</strong><br>';
                    Object.entries(analytics.quality_performance).forEach(([quality, data]) => {
                        analyticsHtml += `
                            <div style="margin-left: 10px; font-size: 0.9em;">
                                ${quality.toUpperCase()}: ${data.count} signals, ${(data.win_rate * 100).toFixed(1)}% win rate
                            </div>
                        `;
                    });
                    analyticsHtml += '</div>';
                }
                
                // Top patterns
                if (analytics.pattern_ranking && analytics.pattern_ranking.length > 0) {
                    analyticsHtml += '<div style="margin-bottom: 10px;"><strong>Top Patterns:</strong><br>';
                    analytics.pattern_ranking.slice(0, 3).forEach(pattern => {
                        analyticsHtml += `
                            <div style="margin-left: 10px; font-size: 0.9em;">
                                ${pattern.pattern}: ${(pattern.win_rate * 100).toFixed(1)}% (${pattern.total_signals})
                            </div>
                        `;
                    });
                    analyticsHtml += '</div>';
                }
                
                // Confluence score analysis
                if (analytics.confluence_score_analysis) {
                    analyticsHtml += '<div><strong>Confluence Score Ranges:</strong><br>';
                    Object.entries(analytics.confluence_score_analysis).forEach(([range, data]) => {
                        analyticsHtml += `
                            <div style="margin-left: 10px; font-size: 0.9em;">
                                ${range}: ${(data.win_rate * 100).toFixed(1)}% (${data.count} signals)
                            </div>
                        `;
                    });
                    analyticsHtml += '</div>';
                }
                
                // ML readiness
                if (analytics.ml_features) {
                    const ml = analytics.ml_features;
                    analyticsHtml += `
                        <div style="margin-top: 10px; padding: 8px; background: rgba(0,255,0,0.1); border-radius: 4px;">
                            <strong>ML Readiness:</strong><br>
                            Features: ${ml.feature_count}<br>
                            Ready: ${ml.ready_for_ml ? 'Yes' : 'No (need 50+ signals)'}
                        </div>
                    `;
                }
                
                document.getElementById('signalAnalyticsDetails').innerHTML = analyticsHtml;
            }
            
            async function updateSignalPerformanceStats() {
                try {
                    const response = await fetch('/api/signals/performance/real-time');
                    const result = await response.json();
                    
                    if (result.success) {
                        const stats = result.stats;
                        document.getElementById('activeSignalsCount').textContent = stats.active_signals;
                        document.getElementById('completedSignalsCount').textContent = stats.completed_signals;
                        document.getElementById('signalWinRate').textContent = stats.win_rate + '%';
                        document.getElementById('avgBarsToResolution').textContent = stats.avg_bars_to_resolution;
                    }
                } catch (error) {
                    console.error('Error updating signal performance stats:', error);
                }
            }
            
            async function exportSignalPerformance() {
                try {
                    const response = await fetch('/api/signals/performance/export');
                    const result = await response.json();
                    
                    if (!result.success) {
                        alert('Failed to export signal performance: ' + result.message);
                        return;
                    }
                    
                    if (result.data.length === 0) {
                        alert('No signal performance data to export');
                        return;
                    }
                    
                    // Convert to CSV
                    const headers = Object.keys(result.data[0]);
                    let csvContent = headers.join(',') + '\\n';
                    
                    result.data.forEach(signal => {
                        const row = headers.map(header => {
                            const value = signal[header];
                            if (typeof value === 'string' && value.includes(',')) {
                                return '"' + value + '"';
                            }
                            return value;
                        });
                        csvContent += row.join(',') + '\\n';
                    });
                    
                    // Download CSV file
                    const blob = new Blob([csvContent], { type: 'text/csv' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `signal_performance_${new Date().toISOString().slice(0,19)}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    
                    debugLog('performance', `Exported ${result.data.length} signal performance records to CSV`);
                } catch (error) {
                    console.error('Error exporting signal performance:', error);
                    alert('Error exporting signal performance data');
                }
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
                    // First check available data range to avoid requesting non-existent dates
                    console.log('🔍 Checking available data range before loading...');
                    const symbolsResponse = await fetch('/api/symbols');
                    const symbolsResult = await symbolsResponse.json();
                    
                    let actualStartDate = startDate;
                    if (symbolsResult.success && symbolsResult.symbols) {
                        const currentSymbol = symbolsResult.symbols.find(s => s.symbol === symbol);
                        if (currentSymbol) {
                            const currentTimeframe = currentSymbol.timeframes.find(tf => tf.timeframe === timeframe);
                            if (currentTimeframe) {
                                const availableStart = currentTimeframe.start_date.split(' ')[0]; // Extract date part
                                
                                // Calculate desired preload start date
                                const userStartDate = new Date(startDate);
                                const preloadDays = timeframe === 'M1' ? 7 : timeframe === 'H1' ? 30 : 14;
                                const preloadStartDate = new Date(userStartDate.getTime() - (preloadDays * 24 * 60 * 60 * 1000));
                                const preloadStartDateStr = preloadStartDate.toISOString().split('T')[0];
                                
                                // Use the later of: available start date or desired preload date
                                actualStartDate = availableStart > preloadStartDateStr ? availableStart : preloadStartDateStr;
                                console.log(`📅 Adjusted start date: requested ${preloadStartDateStr}, available from ${availableStart}, using ${actualStartDate}`);
                            }
                        }
                    }

                    const response = await fetch('/api/data', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            symbol: symbol,
                            timeframe: timeframe,
                            start_date: actualStartDate, // Use adjusted start date
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
                        const userStartDate = new Date(startDate);
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
                                // Initialize last known parameter values to prevent refresh loops
                                lastFractalPeriods = parseInt(document.getElementById('fractalPeriods').value) || 5;
                                lastLookbackCandles = parseInt(document.getElementById('lookbackCandles').value) || 140;
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

                        // Clear all markers when loading completely new data through unified manager
                        if (unifiedMarkerManager) {
                            unifiedMarkerManager.clearAll();
                            // Note: markers will be restored by loadAllStrategyElements() call below
                        }

                        console.log('✅ Chart updated with market data, backtesting engine loaded successfully');
                        
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
                                // 🚨 CRITICAL FIX: Only load strategy elements if we don't already have accumulated data
                                if ((!accumulatedFractals || accumulatedFractals.length === 0) && 
                                    (!window.accumulatedFractals || window.accumulatedFractals.length === 0)) {
                                    console.log('📍 No accumulated fractals found, loading from database...');
                                    loadAllStrategyElements();
                                } else {
                                    console.log(`📍 Using existing accumulated fractals (${accumulatedFractals.length} local, ${window.accumulatedFractals ? window.accumulatedFractals.length : 0} global)`);
                                }
                            } else {
                                console.warn('⚠️ Fractal analysis failed:', analysisResult.message);
                            }
                        } catch (error) {
                            console.warn('Backend synchronization error:', error);
                            // 🚨 CRITICAL FIX: Only fallback to loadAllStrategyElements if no accumulated data exists
                            if ((!accumulatedFractals || accumulatedFractals.length === 0) && 
                                (!window.accumulatedFractals || window.accumulatedFractals.length === 0)) {
                                console.log('📍 No accumulated fractals found, trying database fallback...');
                                loadAllStrategyElements();
                            } else {
                                console.log(`📍 Preserving existing accumulated fractals instead of database fallback`);
                            }
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
            
            // Track last fractal periods to prevent unnecessary reloads
            let lastFractalPeriods = null;
            let lastLookbackCandles = null;
            
            // Refresh chart elements based on settings checkboxes
            function refreshChartElements() {
                console.log('🔄 Refreshing chart elements based on settings...');
                
                // Debug: Log checkbox states
                console.log('📊 Checkbox states:', {
                    fractals: document.getElementById('showFractals') ? document.getElementById('showFractals').checked : 'not found',
                    swings: document.getElementById('showSwings') ? document.getElementById('showSwings').checked : 'not found',
                    fibonacci: document.getElementById('showFibonacci') ? document.getElementById('showFibonacci').checked : 'not found',
                    abc: document.getElementById('showABC') ? document.getElementById('showABC').checked : 'not found',
                    signals: document.getElementById('showSignals') ? document.getElementById('showSignals').checked : 'not found',
                    enhancedSignals: document.getElementById('showEnhancedSignals') ? document.getElementById('showEnhancedSignals').checked : 'not found'
                });
                
                if (!chart || !candlestickSeries) {
                    console.warn('Chart not initialized yet - skipping refresh');
                    return;
                }
                
                // Check if fractal periods or lookback changed - if so, need to reload backend data
                const currentFractalPeriods = parseInt(document.getElementById('fractalPeriods').value) || 5;
                const currentLookbackCandles = parseInt(document.getElementById('lookbackCandles').value) || 140;
                const symbolSelect = document.getElementById('symbolSelect');
                const timeframeSelect = document.getElementById('timeframeSelect');
                const startDate = document.getElementById('startDate').value;
                const endDate = document.getElementById('endDate').value;
                
                // Only reload if parameters actually changed and data is loaded
                const fractalPeriodsChanged = lastFractalPeriods !== null && lastFractalPeriods !== currentFractalPeriods;
                const lookbackCandlesChanged = lastLookbackCandles !== null && lastLookbackCandles !== currentLookbackCandles;
                
                if ((fractalPeriodsChanged || lookbackCandlesChanged) && symbolSelect && symbolSelect.value && startDate && endDate) {
                    console.log(`🔄 Parameters changed - Fractal: ${lastFractalPeriods} → ${currentFractalPeriods}, Lookback: ${lastLookbackCandles} → ${currentLookbackCandles}`);
                    
                    // Update stored values
                    lastFractalPeriods = currentFractalPeriods;
                    lastLookbackCandles = currentLookbackCandles;
                    
                    // Reload backend with new parameters (non-blocking)
                    loadBacktestingEngine(symbolSelect.value, timeframeSelect.value, startDate, endDate)
                        .then(() => {
                            console.log('✅ Backend reloaded with new parameters');
                            // Update display after backend reload directly
                            updateAllMarkers();
                        })
                        .catch(error => {
                            console.warn('Backend reload failed, updating display only:', error);
                            // Still update display even if backend fails
                            updateAllMarkers();
                        });
                } else {
                    // Just update display without backend reload
                    if (lastFractalPeriods === null) {
                        lastFractalPeriods = currentFractalPeriods;
                    }
                    if (lastLookbackCandles === null) {
                        lastLookbackCandles = currentLookbackCandles;
                    }
                    updateAllMarkers();
                }
                
                // Handle lookback line visibility
                if (lookbackManager) {
                    const showLookbackLine = document.getElementById('showLookbackLine').checked;
                    if (showLookbackLine && currentPosition >= 0) {
                        // Show lookback line at current position
                        lookbackManager.updateLookbackIndicator(currentPosition);
                    } else {
                        // Hide lookback line
                        lookbackManager.removeLookbackLine();
                    }
                }

                // Handle supply & demand zones refresh
                if (supplyDemandManager) {
                    supplyDemandManager.updateAllZones();
                    console.log('🔄 Updated S&D zone rectangles');
                }
                
                // Handle enhanced signals visibility through unified manager
                const showEnhancedSignals = document.getElementById('showEnhancedSignals') ? document.getElementById('showEnhancedSignals').checked : false;
                if (!showEnhancedSignals) {
                    // Hide enhanced signals but keep data
                    clearEnhancedSignalLines();
                    if (unifiedMarkerManager) {
                        unifiedMarkerManager.removeMarkersByPattern('enhanced_signal_');
                    }
                    console.log('🔄 Hidden enhanced signals through unified manager');
                } else if (enhancedSignalsData.length > 0 && unifiedMarkerManager) {
                    // Re-show enhanced signals from cache through unified manager
                    console.log('🔄 Re-showing enhanced signals from cache through unified manager');
                    enhancedSignalsData.forEach(signal => {
                        const enhancedSignalData = {
                            timestamp: signal.timestamp,
                            signal_type: signal.signal_type,
                            text: `${signal.quality}\\n${signal.pattern_type}\\n${signal.confluence_score.toFixed(0)}%`,
                            size: 4
                        };
                        unifiedMarkerManager.addSignal(enhancedSignalData, 'enhanced_signal');
                    });
                }

                console.log('✅ Chart elements refresh initiated');
            }
            
            // Supply & Demand Zone Control Functions
            function toggleSupplyDemandZones() {
                const showZones = document.getElementById('showSupplyDemandZones').checked;
                const debugPanel = document.getElementById('zoneDebugPanel');
                
                // Show/hide debug panel
                if (showZones) {
                    debugPanel.style.display = 'block';
                    updateZoneDebugInfo();
                } else {
                    debugPanel.style.display = 'none';
                }
                
                // Initialize manager if needed
                if (!supplyDemandManager) {
                    if (candlestickSeries) {
                        try {
                            supplyDemandManager = new SupplyDemandZoneManager(candlestickSeries);
                            console.log('✅ S&D zone manager initialized');
                        } catch (error) {
                            console.error('❌ Failed to initialize S&D manager:', error);
                            updateStatus('❌ Failed to initialize S&D manager');
                            return;
                        }
                    } else {
                        updateStatus('❌ Load chart data first');
                        return;
                    }
                }
                
                if (showZones) {
                    // Load zones if not already loaded
                    if (!supplyDemandManager.allZones || supplyDemandManager.allZones.length === 0) {
                        loadSupplyDemandZones();
                    } else {
                        supplyDemandManager.toggleZoneVisibility();
                        updateZoneDebugInfo();
                    }
                } else {
                    // Hide zones
                    supplyDemandManager.toggleZoneVisibility();
                }
                
                updateStatus(`📦 S&D zones ${showZones ? 'enabled' : 'disabled'}`);
            }
            
            // Update Zone Debug Info Panel
            function updateZoneDebugInfo() {
                if (!supplyDemandManager) return;
                
                const currentBar = currentPosition || 0;
                const currentTime = window.fullChartData && window.fullChartData[currentBar] 
                    ? window.fullChartData[currentBar].time 
                    : 0;
                const currentTimeStr = currentTime ? new Date(currentTime * 1000).toISOString().substring(0, 19) : '-';
                
                // Chart data analysis
                let chartDateRange = '-';
                let chartPriceRange = '-';
                if (window.fullChartData && window.fullChartData.length > 0) {
                    const firstBar = window.fullChartData[0];
                    const lastBar = window.fullChartData[window.fullChartData.length - 1];
                    chartDateRange = `${new Date(firstBar.time * 1000).toISOString().substring(0, 10)} to ${new Date(lastBar.time * 1000).toISOString().substring(0, 10)}`;
                    
                    // Find price range
                    let minPrice = firstBar.low;
                    let maxPrice = firstBar.high;
                    for (const bar of window.fullChartData) {
                        if (bar.low < minPrice) minPrice = bar.low;
                        if (bar.high > maxPrice) maxPrice = bar.high;
                    }
                    chartPriceRange = `${minPrice.toFixed(1)} - ${maxPrice.toFixed(1)}`;
                }
                
                // Zone data analysis
                let zoneDateRange = '-';
                let zonePriceRange = '-';
                let mismatchWarning = 'Checking...';
                
                if (supplyDemandManager.allZones && supplyDemandManager.allZones.length > 0) {
                    const zones = supplyDemandManager.allZones;
                    let earliestZone = zones[0];
                    let latestZone = zones[0];
                    let minZonePrice = zones[0].bottom_price;
                    let maxZonePrice = zones[0].top_price;
                    
                    for (const zone of zones) {
                        const zoneTime = supplyDemandManager.parseTime(zone.left_time);
                        const earliestTime = supplyDemandManager.parseTime(earliestZone.left_time);
                        const latestTime = supplyDemandManager.parseTime(latestZone.left_time);
                        
                        if (zoneTime < earliestTime) earliestZone = zone;
                        if (zoneTime > latestTime) latestZone = zone;
                        if (zone.bottom_price < minZonePrice) minZonePrice = zone.bottom_price;
                        if (zone.top_price > maxZonePrice) maxZonePrice = zone.top_price;
                    }
                    
                    zoneDateRange = `${new Date(supplyDemandManager.parseTime(earliestZone.left_time) * 1000).toISOString().substring(0, 10)} to ${new Date(supplyDemandManager.parseTime(latestZone.left_time) * 1000).toISOString().substring(0, 10)}`;
                    zonePriceRange = `${minZonePrice.toFixed(1)} - ${maxZonePrice.toFixed(1)}`;
                    
                    // Check for mismatch
                    if (window.fullChartData && window.fullChartData.length > 0) {
                        const chartStartTime = window.fullChartData[0].time;
                        const chartEndTime = window.fullChartData[window.fullChartData.length - 1].time;
                        const zoneStartTime = supplyDemandManager.parseTime(earliestZone.left_time);
                        const zoneEndTime = supplyDemandManager.parseTime(latestZone.left_time);
                        
                        if (zoneStartTime > chartEndTime || zoneEndTime < chartStartTime) {
                            mismatchWarning = 'DATE MISMATCH! Zones are from different time period than chart data';
                        } else {
                            mismatchWarning = 'Dates align ✓';
                        }
                    }
                }
                
                // Update debug panel
                document.getElementById('debugCurrentBar').textContent = currentBar;
                document.getElementById('debugCurrentTime').textContent = currentTimeStr;
                document.getElementById('debugChartDateRange').textContent = chartDateRange;
                document.getElementById('debugChartPriceRange').textContent = chartPriceRange;
                document.getElementById('debugZonesLoaded').textContent = supplyDemandManager.allZones ? supplyDemandManager.allZones.length : 0;
                document.getElementById('debugZonesVisible').textContent = supplyDemandManager.zoneLineSeries.size;
                document.getElementById('debugZoneDateRange').textContent = zoneDateRange;
                document.getElementById('debugZonePriceRange').textContent = zonePriceRange;
                document.getElementById('debugMismatchWarning').textContent = mismatchWarning;
                
                // Find next zone
                let nextZone = null;
                if (supplyDemandManager.allZones) {
                    for (const zone of supplyDemandManager.allZones) {
                        const zoneTime = supplyDemandManager.parseTime(zone.left_time);
                        if (zoneTime && zoneTime > currentTime) {
                            if (!nextZone || zoneTime < supplyDemandManager.parseTime(nextZone.left_time)) {
                                nextZone = zone;
                            }
                        }
                    }
                }
                
                if (nextZone) {
                    const nextZoneTime = new Date(supplyDemandManager.parseTime(nextZone.left_time) * 1000).toISOString().substring(0, 19);
                    document.getElementById('debugNextZone').textContent = `${nextZone.zone_type} at ${nextZoneTime}`;
                } else {
                    document.getElementById('debugNextZone').textContent = 'None in current timeframe';
                }
            }
            
            // Add zone event to debug log
            function addZoneDebugEvent(message) {
                const debugEvents = document.getElementById('debugZoneEvents');
                const time = new Date().toISOString().substring(11, 19);
                debugEvents.innerHTML = `<div>${time}: ${message}</div>` + debugEvents.innerHTML;
                
                // Keep only last 5 events
                const events = debugEvents.children;
                while (events.length > 5) {
                    debugEvents.removeChild(events[events.length - 1]);
                }
            }
            
            // Toggle sidebar section collapse
            function toggleSection(headerElement) {
                const section = headerElement.parentElement;
                section.classList.toggle('collapsed');
            }
            
            async function loadSupplyDemandZones() {
                try {
                    // Get current form values
                    const symbol = document.getElementById('symbolSelect').value;
                    const timeframe = document.getElementById('timeframeSelect').value;

                    if (!symbol || !timeframe) {
                        console.warn('Symbol or timeframe not selected');
                        updateStatus('⚠️ Please select symbol and timeframe first');
                        return;
                    }

                    // Show loading status
                    updateStatus('📦 Loading supply & demand zones...');

                    // Call the zones API
                    const url = `/api/supply-demand/zones?symbol=${symbol}&timeframe=${timeframe}&limit=50`;
                    const response = await fetch(url);

                    if (response.ok) {
                        const result = await response.json();

                        if (result.success && result.zones && result.zones.length > 0) {
                            // Store zones for dynamic display during replay
                            if (supplyDemandManager) {
                                // Store all zones but DON'T display them yet - they appear only during replay navigation
                                supplyDemandManager.storeZonesForDynamicDisplay(result.zones);
                                
                                // DO NOT call updateDynamicZoneDisplay here - zones should only appear during replay
                                updateStatus(`✅ Loaded ${result.zones.length} S&D zones for dynamic display. Use replay controls to see zones appear.`);
                                
                                // Update debug info (will show 0 visible zones until replay starts)
                                updateZoneDebugInfo();
                                
                                // Add debug event
                                addZoneDebugEvent(`Zones loaded. Start replay to see them appear at detection points.`);
                            } else {
                                console.error('❌ Supply & Demand manager not initialized!');
                                updateStatus('❌ S&D manager not initialized');
                            }
                        } else {
                            console.warn('No zones returned from API');
                            updateStatus('⚠️ No S&D zones found for current symbol/timeframe');
                        }
                    } else {
                        const errorText = await response.text();
                        console.error('API error:', response.status, errorText);
                        updateStatus(`❌ API error: ${response.status}`);
                    }
                } catch (error) {
                    console.error('Error loading S&D zones:', error);
                    updateStatus(`❌ Error loading zones: ${error.message}`);
                }
            }
            
            function createDemoSupplyDemandZones() {
                console.log('📦 Creating demo S&D zones...');
                
                // Create some demo zones for testing
                if (!marketData || marketData.length === 0) {
                    console.warn('No market data available for demo zones');
                    updateStatus('⚠️ Load chart data first to see demo zones');
                    return;
                }
                
                const demoZones = [];
                const dataLength = marketData.length;
                
                // Create a few demo supply zones
                for (let i = 0; i < 3; i++) {
                    const startIndex = Math.floor(dataLength * 0.2) + (i * 100);
                    if (startIndex >= dataLength) break;
                    
                    const startBar = marketData[startIndex];
                    const endBar = marketData[Math.min(startIndex + 20, dataLength - 1)];
                    
                    demoZones.push({
                        id: `demo_supply_${i}`,
                        symbol: 'DEMO',
                        timeframe: 'M1',
                        zone_type: 'supply',
                        top_price: startBar.high + (startBar.high * 0.001),
                        bottom_price: startBar.high - (startBar.high * 0.001),
                        left_time: startBar.timestamp,
                        right_time: endBar.timestamp,
                        strength_score: 0.7 + (i * 0.1)
                    });
                }
                
                // Create a few demo demand zones
                for (let i = 0; i < 3; i++) {
                    const startIndex = Math.floor(dataLength * 0.4) + (i * 120);
                    if (startIndex >= dataLength) break;
                    
                    const startBar = marketData[startIndex];
                    const endBar = marketData[Math.min(startIndex + 25, dataLength - 1)];
                    
                    demoZones.push({
                        id: `demo_demand_${i}`,
                        symbol: 'DEMO',
                        timeframe: 'M1',
                        zone_type: 'demand',
                        top_price: startBar.low + (startBar.low * 0.001),
                        bottom_price: startBar.low - (startBar.low * 0.001),
                        left_time: startBar.timestamp,
                        right_time: endBar.timestamp,
                        strength_score: 0.6 + (i * 0.15)
                    });
                }
                
                if (supplyDemandManager && demoZones.length > 0) {
                    supplyDemandManager.loadAllZones(demoZones);
                    updateStatus(`✅ Created ${demoZones.length} demo S&D zones`);
                    console.log(`📦 Created ${demoZones.length} demo zones`);
                } else {
                    updateStatus('❌ Failed to create demo zones');
                }
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
                    const fractalPeriods = parseInt(document.getElementById('fractalPeriods').value) || 5;
                    const fractalsResponse = await fetch(`/api/fractals?symbol=${symbol}&timeframe=${timeframe}&start_date=${startDate}&end_date=${endDate}&periods=${fractalPeriods}`);
                    const fractalsResult = await fractalsResponse.json();
                    
                    if (fractalsResult.success && fractalsResult.fractals) {
                        console.log(`📍 Loaded ${fractalsResult.fractals.length} fractals from database`);

                        // Clear existing markers through unified manager
                        if (unifiedMarkerManager) {
                            unifiedMarkerManager.clearAll();
                        }

                        // Only clear enhanced signals if loading completely new data
                        const isNewDataLoad = true; // This happens only on fresh data load
                        if (isNewDataLoad) {
                            console.log('🔄 Loading new data - clearing enhanced signals');
                            clearAllEnhancedSignals();
                        }

                        // Add fractals to chart if checkbox is checked
                        if (fractalsResult.fractals.length > 0 && document.getElementById('showFractals').checked && unifiedMarkerManager) {
                            debugLog('markers', '📍 Processing fractals for chart display...');

                            // 🚨 CRITICAL FIX: Only clear accumulated fractals if this is a fresh data load
                            // During navigation, preserve existing accumulated fractals
                            const isNavigation = (accumulatedFractals.length > 0 || (window.accumulatedFractals && window.accumulatedFractals.length > 0));
                            
                            if (!isNavigation) {
                                // Fresh data load - clear and rebuild
                                accumulatedFractals = [];
                                window.accumulatedFractals = [];
                                debugLog('markers', '📍 Fresh data load - clearing accumulated fractals');
                            } else {
                                debugLog('markers', '📍 Navigation mode - preserving existing accumulated fractals');
                            }

                            // Convert database fractals to proper format and accumulate them
                            fractalsResult.fractals.forEach(fractal => {
                                const fractalData = {
                                    timestamp: fractal.timestamp,
                                    fractal_type: fractal.type
                                };
                                
                                // Only add if not already exists (prevent duplicates)
                                const exists = accumulatedFractals.some(f => f.timestamp === fractalData.timestamp && f.fractal_type === fractalData.fractal_type);
                                if (!exists) {
                                    accumulatedFractals.push(fractalData);
                                    window.accumulatedFractals.push(fractalData);
                                }
                            });

                            // Load all accumulated fractals into unified manager
                            unifiedMarkerManager.loadFractals(accumulatedFractals);
                            debugLog('markers', `📍 Loaded and accumulated ${accumulatedFractals.length} fractal markers through unified manager`);
                        } else if (fractalsResult.fractals.length === 0) {
                            // 🚨 CRITICAL FIX: Don't clear markers if database is empty but we have accumulated data
                            const hasAccumulatedFractals = (accumulatedFractals.length > 0 || (window.accumulatedFractals && window.accumulatedFractals.length > 0));
                            if (hasAccumulatedFractals) {
                                debugLog('markers', `📍 Database empty but preserving ${accumulatedFractals.length || window.accumulatedFractals.length} accumulated fractals`);
                            } else {
                                debugLog('markers', '📍 No fractals to display (database empty, no accumulated data):', {
                                    fractalCount: fractalsResult.fractals?.length || 0,
                                    checkboxChecked: document.getElementById('showFractals').checked,
                                    hasManager: !!unifiedMarkerManager
                                });
                            }
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
                    const fractalPeriods = parseInt(document.getElementById('fractalPeriods').value) || 5;
                    const fractalsResponse = await fetch(`/api/fractals?symbol=${symbol}&timeframe=${timeframe}&start_date=${startDate}&end_date=${endDate}&periods=${fractalPeriods}`);
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
                        document.getElementById('enhancedSignalCount').textContent = 0; // Reset enhanced signals for new data load
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
                    // SILENCED: console.log(`🎮 Replay ${action}: user position ${currentPosition}, data position ${dataPosition}/${totalBars}`);
                    // SILENCED: console.log(`🔍 Debug: userStartOffset=${window.userStartOffset}, maxUserPosition=${window.maxUserPosition}, userEndOffset=${window.userEndOffset}`);
                    if (marketData[dataPosition]) {
                        // SILENCED: console.log(`📅 Current bar timestamp: ${marketData[dataPosition].timestamp}`);
                    }
                    if (marketData[dataPosition - 1] && action === 'next') {
                        // SILENCED: console.log(`📅 Previous bar timestamp: ${marketData[dataPosition - 1].timestamp}`);
                    }

                    // Update chart progressively to show only bars up to current position
                    updateChartProgressive(currentPosition);
                    
                    // Update Supply & Demand zones dynamically (MT4 style - zones appear as replay reaches them)
                    if (supplyDemandManager && supplyDemandManager.allZones && supplyDemandManager.allZones.length > 0) {
                        supplyDemandManager.updateDynamicZoneDisplay(currentPosition);
                        updateZoneDebugInfo();
                    }

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
                            // SILENCED: console.log(`🔄 Calling backend: /api/backtest/jump/${relativePosition} (relative pos ${relativePosition}, was abs pos ${dataPosition}) (seq: ${requestSequence})`);
                            const result = await fetch(`/api/backtest/jump/${relativePosition}`, { method: 'POST' });
                            // SILENCED: console.log(`📡 Backend response status: ${result.status} (seq: ${requestSequence})`);
                            const data = await result.json();
                            
                            // Check if this response is still relevant (user might have moved on)
                            const currentDataPosition = window.userStartOffset + currentPosition;
                            if (currentDataPosition !== expectedDataPosition) {
                                // SILENCED: console.log(`⚠️ Ignoring stale response: expected position ${expectedDataPosition}, current position ${currentDataPosition} (seq: ${requestSequence})`);
                                return; // Ignore stale response
                            }
                            
                            // SILENCED: console.log(`📊 Processing current response:`, data, `(seq: ${requestSequence})`);
                        
                        if (data.success && data.data) {
                            // Update strategy panels with live strategy data
                            if (data.data.strategy_results) {
                                const results = data.data.strategy_results;
                                // SILENCED: console.log(`🔍 Strategy results at position ${currentPosition}:`, results);
                                // SILENCED: console.log(`🔍 Backend bar_index: ${results.bar_index}, Frontend position: ${currentPosition}`);
                                // SILENCED: console.log(`🔍 New fractal:`, results.new_fractal);
                                // SILENCED: console.log(`🔍 All result keys:`, Object.keys(results));
                                document.getElementById('fractalCount').textContent = results.total_fractals || 0;
                                document.getElementById('swingCount').textContent = results.total_swings || 0;
                                document.getElementById('signalCount').textContent = results.total_signals || 0;
                                document.getElementById('enhancedSignalCount').textContent = results.total_enhanced_signals || 0;
                                document.getElementById('abcPatternCount').textContent = results.total_abc_patterns || 0;
                                
                                // Real fractal processing will be handled by the backend strategy results
                                // No test fractals needed

                                // Add real-time fractals and swings to chart ONLY if checkboxes are checked
                                if (results.new_fractal && document.getElementById('showFractals').checked) {
                                    // SILENCED: console.log(`🎯 TIMING: Adding fractal to chart at frontend position ${currentPosition}, fractal detected at backend bar ${results.bar_index}`);
                                    // SILENCED: console.log(`🎯 FRACTAL DETAILS:`, results.new_fractal);
                                    addNewFractalToChart(results.new_fractal);
                                }
                                
                                if (results.new_swing && document.getElementById('showSwings').checked) {
                                    addNewSwingToChart(results.new_swing);
                                }
                                
                                if (results.fibonacci_levels && results.fibonacci_levels.length > 0 && document.getElementById('showFibonacci').checked) {
                                    addFibonacciLevelsToChart(results.fibonacci_levels);
                                }
                                
                                // 🚨 CRITICAL FIX: Process ABC patterns from backend results
                                if (results.new_abc_pattern && document.getElementById('showABC').checked) {
                                    console.log(`🌊 Processing new ABC pattern from backend:`, results.new_abc_pattern);
                                    // Add new pattern to accumulated array
                                    if (!accumulatedABCPatterns) accumulatedABCPatterns = [];
                                    
                                    // Check if pattern already exists (avoid duplicates)
                                    const patternId = `${results.new_abc_pattern.wave_a.start_timestamp}_${results.new_abc_pattern.wave_c.end_timestamp || results.new_abc_pattern.wave_c.start_timestamp}`;
                                    if (!accumulatedABCPatterns.some(p => `${p.wave_a.start_timestamp}_${p.wave_c.end_timestamp || p.wave_c.start_timestamp}` === patternId)) {
                                        // 🚨 CRITICAL FIX: Limit ABC patterns to prevent overcrowding (keep only latest 5)
                                        if (accumulatedABCPatterns.length >= 5) {
                                            console.log('📊 ABC Pattern limit reached, removing oldest pattern');
                                            accumulatedABCPatterns.shift(); // Remove oldest
                                        }
                                        
                                        accumulatedABCPatterns.push(results.new_abc_pattern);
                                        console.log(`📈 NEW ABC PATTERN: Added pattern, total: ${accumulatedABCPatterns.length}`);
                                        
                                        if (abcPatternManager) {
                                            abcPatternManager.addABCPattern(results.new_abc_pattern, accumulatedDominantSwing);
                                        }
                                    } else {
                                        console.log(`🔄 ABC Pattern already exists, skipping duplicate: ${patternId}`);
                                    }
                                } else if (results.new_abc_pattern && !document.getElementById('showABC').checked) {
                                    console.log(`🚫 ABC Pattern available but checkbox disabled, skipping`);
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
                    
                    // 🚨 REMOVED DUPLICATE: updateAllMarkers is already called by updateChartProgressive
                    // updateAllMarkers();
                    
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
                                document.getElementById('enhancedSignalCount').textContent = results.total_enhanced_signals || 0;
                                document.getElementById('abcPatternCount').textContent = results.total_abc_patterns || 0;
                                
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
                                
                                // 🚨 CRITICAL FIX: Process ABC patterns from backend results (auto-replay)
                                if (results.new_abc_pattern && document.getElementById('showABC').checked) {
                                    console.log(`🌊 Auto-replay: Processing new ABC pattern from backend:`, results.new_abc_pattern);
                                    // Add new pattern to accumulated array
                                    if (!accumulatedABCPatterns) accumulatedABCPatterns = [];
                                    
                                    // Check if pattern already exists (avoid duplicates)
                                    const patternId = `${results.new_abc_pattern.wave_a.start_timestamp}_${results.new_abc_pattern.wave_c.end_timestamp || results.new_abc_pattern.wave_c.start_timestamp}`;
                                    if (!accumulatedABCPatterns.some(p => `${p.wave_a.start_timestamp}_${p.wave_c.end_timestamp || p.wave_c.start_timestamp}` === patternId)) {
                                        // 🚨 CRITICAL FIX: Limit ABC patterns to prevent overcrowding (keep only latest 5)
                                        if (accumulatedABCPatterns.length >= 5) {
                                            console.log('📊 Auto-replay: ABC Pattern limit reached, removing oldest pattern');
                                            accumulatedABCPatterns.shift(); // Remove oldest
                                        }
                                        
                                        accumulatedABCPatterns.push(results.new_abc_pattern);
                                        console.log(`📈 Auto-replay: NEW ABC PATTERN: Added pattern, total: ${accumulatedABCPatterns.length}`);
                                        
                                        if (abcPatternManager) {
                                            abcPatternManager.addABCPattern(results.new_abc_pattern, accumulatedDominantSwing);
                                        }
                                    }
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
            
            function updateMarketBiasDisplay(marketBias) {
                if (!marketBias) return;
                
                console.log('📊 Updating market bias:', marketBias);
                
                // Update sentiment with color coding
                const sentimentElement = document.getElementById('marketSentiment');
                sentimentElement.textContent = marketBias.bias;
                
                // Color code the sentiment
                if (marketBias.bias === 'BULLISH') {
                    sentimentElement.style.color = '#00E676'; // Bright green
                } else if (marketBias.bias === 'BEARISH') {
                    sentimentElement.style.color = '#FF1744'; // Bright red
                } else {
                    sentimentElement.style.color = '#FFD700'; // Gold for neutral
                }
                
                // Update direction
                document.getElementById('marketDirection').textContent = marketBias.direction;
                
                // Update points with both price and pips
                document.getElementById('dominantPoints').textContent = `${marketBias.points.toFixed(5)} (${(marketBias.points*10000).toFixed(1)} pips)`;
                
                // Update trading direction with color coding
                const tradingDirectionElement = document.getElementById('tradingDirection');
                tradingDirectionElement.textContent = marketBias.trading_direction;
                
                if (marketBias.bias === 'BULLISH') {
                    tradingDirectionElement.style.color = '#00E676'; // Bright green for buy
                } else if (marketBias.bias === 'BEARISH') {
                    tradingDirectionElement.style.color = '#FF1744'; // Bright red for sell
                } else {
                    tradingDirectionElement.style.color = '#FFD700'; // Gold for neutral
                }
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
            // ✅ Function moved to top of script section to avoid reference errors
            
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
            // ✅ EMERGENCY STOP FUNCTION - Call this to immediately halt all auto-updates
            function emergencyStopAllUpdates() {
                // Clear all possible intervals and timeouts
                if (playInterval) {
                    clearInterval(playInterval);
                    playInterval = null;
                    console.log('🛑 Emergency stop: playInterval cleared');
                }
                
                if (swingStateReloadTimeout) {
                    clearTimeout(swingStateReloadTimeout);
                    swingStateReloadTimeout = null;
                    console.log('🛑 Emergency stop: swingStateReloadTimeout cleared');
                }
                
                // Stop any unified marker manager updates
                if (unifiedMarkerManager && unifiedMarkerManager.updateTimeout) {
                    clearTimeout(unifiedMarkerManager.updateTimeout);
                    unifiedMarkerManager.updateTimeout = null;
                    console.log('🛑 Emergency stop: unifiedMarkerManager timeout cleared');
                }
                
                // Reset play state
                isPlaying = false;
                const playBtn = document.getElementById('playBtn');
                if (playBtn) {
                    playBtn.textContent = '▶️';
                    playBtn.classList.remove('active');
                }
                
                console.log('🛑 EMERGENCY STOP: All auto-updates halted');
                updateStatus('⏸️ All automatic updates stopped - Chart is now idle');
            }

            window.addEventListener('load', function() {
                // Force stop any running intervals from previous session
                emergencyStopAllUpdates();
                console.log('🧹 Page loaded: cleaned up any leftover intervals');
            });

            // Add keyboard shortcut for emergency stop (ESC key)
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Escape') {
                    emergencyStopAllUpdates();
                    console.log('⌨️ Emergency stop triggered via ESC key');
                }
            });

            // 🚨 CRITICAL FIX: Function to reload current swing state when recalculation happens
            let swingStateReloadTimeout = null;
            async function reloadCurrentSwingState() {
                // Debounce rapid calls to prevent flashing
                if (swingStateReloadTimeout) {
                    clearTimeout(swingStateReloadTimeout);
                }
                
                swingStateReloadTimeout = setTimeout(async () => {
                    try {
                        const symbol = document.getElementById('symbolSelect').value;
                        const timeframe = document.getElementById('timeframeSelect').value;
                        
                        if (!symbol || !timeframe) {
                            console.log('⚠️ No symbol/timeframe selected for swing state reload');
                            return;
                        }
                        
                        console.log('🔄 Reloading current swing state from backend...');
                        const response = await fetch(`/api/strategy/current-state?symbol=${symbol}&timeframe=${timeframe}`);
                        
                        if (response.ok) {
                            const data = await response.json();
                            
                            if (data.swings && data.swings.length > 0) {
                                // Clear and reload swings
                                accumulatedSwings = data.swings;
                                console.log(`🔥 Reloaded ${data.swings.length} swings from backend`);
                                
                                // Find dominant swing
                                accumulatedDominantSwing = data.swings.find(s => s.is_dominant) || null;
                                
                                // Update display if swings are enabled
                                if (document.getElementById('showSwings').checked && swingLineManager) {
                                    swingLineManager.loadAllSwings(accumulatedSwings);
                                    console.log(`✅ Swing lines updated on chart`);
                                }
                            }
                            
                            if (data.fibonacci_levels && data.fibonacci_levels.length > 0) {
                                accumulatedFibonacci = data.fibonacci_levels;
                                console.log(`📐 Reloaded ${data.fibonacci_levels.length} Fibonacci levels`);
                            }
                        } else {
                            console.error('❌ Failed to reload swing state:', response.status);
                        }
                    } catch (error) {
                        console.error('❌ Error reloading swing state:', error);
                    }
                }, 100); // 100ms debounce delay
            }

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
    end_date: Optional[str] = Query(None),
    periods: Optional[int] = Query(5, description="Number of periods for fractal detection")
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
        
        # Create backtesting engine with fractal and lookback configuration
        logger.info(f"🔄 Creating backtesting engine with fractal_periods={request.fractal_periods}, lookback_candles={request.lookback_candles}...")
        strategy_config = {
            'fractal_periods': request.fractal_periods or 5,
            'min_swing_points': 10.0,  # Lower threshold for DJ30 M1 data - was 50.0
            'lookback_candles': request.lookback_candles or 140
        }
        
        # Create new engine instance with configuration or reconfigure existing one
        global backtesting_engine
        backtesting_engine = BacktestingEngine()
        
        # Configure strategy with the provided parameters
        if hasattr(backtesting_engine.strategy, 'configure'):
            backtesting_engine.strategy.configure(strategy_config)
        else:
            # Update strategy parameters directly
            if 'fractal_period' in strategy_config:
                backtesting_engine.strategy.fractal_period = strategy_config['fractal_period']
            if 'min_swing_points' in strategy_config:
                backtesting_engine.strategy.min_swing_points = strategy_config['min_swing_points']
            if 'lookback_candles' in strategy_config:
                backtesting_engine.strategy.lookback_candles = strategy_config['lookback_candles']
        
        # Load data into backtesting engine
        logger.info(f"🔄 Loading {len(df)} bars into backtesting engine...")
        try:
            backtesting_engine.load_data(df)
            logger.info(f"✅ Successfully loaded {len(df)} bars into backtesting engine with {request.fractal_periods} fractal periods")
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

@app.get("/api/strategy/current-state")
async def get_current_strategy_state(
    symbol: str = Query(...),
    timeframe: str = Query(...)
):
    """Get current strategy state with all swings and fibonacci levels."""
    try:
        # Get strategy state from the backtesting engine
        if hasattr(backtesting_engine, 'strategy') and backtesting_engine.strategy:
            strategy_state = backtesting_engine.strategy.get_current_state()
            
            logger.debug(f"🔍 Current strategy state: {len(strategy_state.get('swings', []))} swings, {len(strategy_state.get('fibonacci_levels', []))} fib levels")
            
            return JSONResponse({
                "success": True,
                "swings": strategy_state.get('swings', []),
                "fibonacci_levels": strategy_state.get('fibonacci_levels', []),
                "dominant_swing": strategy_state.get('dominant_swing'),
                "fractals": strategy_state.get('fractals', []),
                "signals": strategy_state.get('signals', [])
            })
        else:
            logger.warning("No strategy available for current state")
            return JSONResponse({
                "success": True,
                "swings": [],
                "fibonacci_levels": [],
                "dominant_swing": None,
                "fractals": [],
                "signals": []
            })
            
    except Exception as e:
        logger.error(f"Error getting current strategy state: {e}")
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

# =====================================
# SIGNAL PERFORMANCE ANALYTICS ENDPOINTS
# =====================================

@app.get("/api/signals/analytics")
async def get_signal_analytics():
    """Get comprehensive signal performance analytics for ML/AI development."""
    try:
        analytics = backtesting_engine.strategy.get_signal_analytics()
        
        return JSONResponse({
            "success": True,
            "analytics": analytics
        })
    
    except Exception as e:
        logger.error(f"Error getting signal analytics: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/signals/performance/export")
async def export_signal_performance():
    """Export signal performance data for external analysis."""
    try:
        performance_df = backtesting_engine.strategy.export_signal_performance_data()
        
        if performance_df.empty:
            return JSONResponse({
                "success": True,
                "data": [],
                "message": "No signal performance data available"
            })
        
        # Convert DataFrame to JSON
        performance_data = performance_df.to_dict('records')
        
        return JSONResponse({
            "success": True,
            "data": performance_data,
            "total_signals": len(performance_data)
        })
    
    except Exception as e:
        logger.error(f"Error exporting signal performance: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.get("/api/signals/performance/real-time")
async def get_real_time_signal_performance():
    """Get real-time signal performance statistics."""
    try:
        stats = backtesting_engine.strategy.signal_performance_tracker.get_real_time_stats()
        
        return JSONResponse({
            "success": True,
            "stats": stats
        })
    
    except Exception as e:
        logger.error(f"Error getting real-time signal performance: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

# =====================================
# SUPPLY & DEMAND ZONES ENDPOINTS
# =====================================

@app.get("/api/supply-demand/zones")
async def get_supply_demand_zones(
    symbol: str = Query(...),
    timeframe: str = Query(...),
    limit: int = Query(50, description="Maximum number of zones to return")
):
    """Get supply and demand zones for symbol and timeframe."""
    try:
        logger.info(f"🔄 Getting S&D zones: {symbol} {timeframe} (limit: {limit})")

        # For now, create demo zones based on current market data
        # In the future, this will use the actual SupplyDemandZoneDetector

        db_manager = get_database_manager()
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not available")

        # Get recent market data for zone detection
        with db_manager.get_session() as session:
            # Query recent data (last 1000 bars for zone detection)
            query = text("""
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE symbol = :symbol
                AND timeframe = :timeframe
                ORDER BY timestamp DESC
                LIMIT 1000
            """)

            result = session.execute(query, {
                'symbol': symbol,
                'timeframe': timeframe
            })

            rows = result.fetchall()

            if not rows:
                return JSONResponse({
                    "success": True,
                    "zones": [],
                    "message": f"No market data found for {symbol} {timeframe}"
                })

            # Convert to DataFrame for zone detection
            import pandas as pd
            df = pd.DataFrame([{
                'timestamp': row[0],
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': float(row[5]) if row[5] else 0.0
            } for row in rows])

            # Reverse to chronological order
            df = df.iloc[::-1].reset_index(drop=True)

            # Create demo zones based on price action
            zones = create_demo_zones_from_data(df, symbol, timeframe, limit)

            logger.info(f"✅ Generated {len(zones)} S&D zones for {symbol} {timeframe}")

            return JSONResponse({
                "success": True,
                "zones": zones,
                "count": len(zones)
            })

    except Exception as e:
        logger.error(f"Error getting S&D zones: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e),
            "zones": []
        })

def create_demo_zones_from_data(df, symbol, timeframe, limit):
    """Create demo supply and demand zones from market data."""
    zones = []

    if len(df) < 50:
        return zones

    try:
        # Find significant highs and lows for zone creation
        window = 20

        # Find local highs (potential supply zones)
        for i in range(window, len(df) - window):
            current_high = df.iloc[i]['high']

            # Check if this is a local high
            is_local_high = True
            for j in range(i - window, i + window + 1):
                if j != i and df.iloc[j]['high'] >= current_high:
                    is_local_high = False
                    break

            if is_local_high and len([z for z in zones if z['zone_type'] == 'supply']) < limit // 2:
                # Create supply zone
                zone_height = current_high * 0.002  # 0.2% zone height
                zones.append({
                    'id': f"supply_{symbol}_{i}",
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'zone_type': 'supply',
                    'top_price': current_high + zone_height,
                    'bottom_price': current_high - zone_height,
                    'left_time': df.iloc[max(0, i-10)]['timestamp'],
                    'right_time': df.iloc[min(len(df)-1, i+10)]['timestamp'],
                    'strength_score': 0.6 + (abs(current_high - df.iloc[i]['close']) / current_high) * 2,
                    'status': 'active',
                    'test_count': 0,
                    'created_at': df.iloc[i]['timestamp']
                })

        # Find local lows (potential demand zones)
        for i in range(window, len(df) - window):
            current_low = df.iloc[i]['low']

            # Check if this is a local low
            is_local_low = True
            for j in range(i - window, i + window + 1):
                if j != i and df.iloc[j]['low'] <= current_low:
                    is_local_low = False
                    break

            if is_local_low and len([z for z in zones if z['zone_type'] == 'demand']) < limit // 2:
                # Create demand zone
                zone_height = current_low * 0.002  # 0.2% zone height
                zones.append({
                    'id': f"demand_{symbol}_{i}",
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'zone_type': 'demand',
                    'top_price': current_low + zone_height,
                    'bottom_price': current_low - zone_height,
                    'left_time': df.iloc[max(0, i-10)]['timestamp'],
                    'right_time': df.iloc[min(len(df)-1, i+10)]['timestamp'],
                    'strength_score': 0.6 + (abs(df.iloc[i]['close'] - current_low) / current_low) * 2,
                    'status': 'active',
                    'test_count': 0,
                    'created_at': df.iloc[i]['timestamp']
                })

        # Sort zones by strength score (strongest first)
        zones.sort(key=lambda x: x['strength_score'], reverse=True)

        # Limit to requested number
        zones = zones[:limit]

        # Convert timestamps to ISO format for frontend
        for zone in zones:
            if hasattr(zone['left_time'], 'isoformat'):
                zone['left_time'] = zone['left_time'].isoformat()
            if hasattr(zone['right_time'], 'isoformat'):
                zone['right_time'] = zone['right_time'].isoformat()
            if hasattr(zone['created_at'], 'isoformat'):
                zone['created_at'] = zone['created_at'].isoformat()

        return zones

    except Exception as e:
        logger.error(f"Error creating demo zones: {e}")
        return []

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