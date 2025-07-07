# API Specification - Fibonacci Trading Bot

## Overview
This document defines the complete API specification for the Fibonacci-based AI trading bot, including REST endpoints, WebSocket connections, and data schemas.

## Base Information

**Base URL**: `https://api.fibonacci-trading-bot.com/v1`  
**Protocol**: HTTPS  
**Authentication**: API Key + JWT Token  
**Content-Type**: `application/json`  
**API Version**: 1.0.0  

## Authentication

### API Key Authentication
```http
GET /api/v1/health
Authorization: Bearer your-api-key-here
```

### JWT Token Authentication
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "secure_password"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## REST API Endpoints

### System Management

#### GET /health
**Description**: System health check  
**Authentication**: API Key  
**Parameters**: None  

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "mt5_connection": "healthy",
    "database": "healthy",
    "memory_usage": "75.2%",
    "cpu_usage": "45.1%",
    "disk_usage": "62.3%"
  },
  "uptime_seconds": 86400
}
```

#### GET /status
**Description**: Detailed system status  
**Authentication**: JWT Token  
**Parameters**: None  

**Response**:
```json
{
  "system": {
    "status": "running",
    "mode": "live_trading",
    "start_time": "2023-12-01T00:00:00Z",
    "last_restart": "2023-12-01T00:00:00Z"
  },
  "trading": {
    "active_positions": 3,
    "pending_orders": 1,
    "daily_pnl": 1250.50,
    "total_trades_today": 15,
    "win_rate_today": 0.733
  },
  "performance": {
    "total_return": 0.245,
    "sharpe_ratio": 1.85,
    "max_drawdown": 0.087,
    "win_rate": 0.685
  }
}
```

### Trading Operations

#### GET /positions
**Description**: Get all active positions  
**Authentication**: JWT Token  
**Parameters**: 
- `symbol` (optional): Filter by symbol
- `status` (optional): Filter by status (open, closed, pending)

**Response**:
```json
{
  "positions": [
    {
      "id": "pos_001",
      "symbol": "EURUSD",
      "side": "long",
      "size": 0.1,
      "entry_price": 1.0850,
      "current_price": 1.0875,
      "unrealized_pnl": 25.00,
      "open_time": "2023-12-01T09:15:00Z",
      "stop_loss": 1.0820,
      "take_profit": 1.0920,
      "strategy": "fibonacci_retracement"
    }
  ],
  "total_positions": 1,
  "total_unrealized_pnl": 25.00
}
```

#### POST /positions
**Description**: Open new position  
**Authentication**: JWT Token  
**Request Body**:
```json
{
  "symbol": "EURUSD",
  "side": "long",
  "size": 0.1,
  "entry_type": "market",
  "stop_loss": 1.0820,
  "take_profit": 1.0920,
  "strategy_id": "fibonacci_001"
}
```

**Response**:
```json
{
  "position_id": "pos_002",
  "status": "executed",
  "execution_price": 1.0855,
  "execution_time": "2023-12-01T10:30:00Z",
  "message": "Position opened successfully"
}
```

#### PUT /positions/{position_id}
**Description**: Modify existing position  
**Authentication**: JWT Token  
**Parameters**: 
- `position_id`: Position identifier

**Request Body**:
```json
{
  "stop_loss": 1.0825,
  "take_profit": 1.0925
}
```

#### DELETE /positions/{position_id}
**Description**: Close position  
**Authentication**: JWT Token  
**Parameters**: 
- `position_id`: Position identifier

### Strategy Management

#### GET /strategies
**Description**: Get all available strategies  
**Authentication**: JWT Token  

**Response**:
```json
{
  "strategies": [
    {
      "id": "fibonacci_retracement",
      "name": "Fibonacci Retracement Strategy",
      "description": "Entry at Fibonacci retracement levels with session analysis",
      "status": "active",
      "parameters": {
        "bars_range": 2,
        "fib_levels": [0.382, 0.618],
        "risk_per_trade": 0.01
      },
      "performance": {
        "total_trades": 245,
        "win_rate": 0.685,
        "profit_factor": 1.45,
        "sharpe_ratio": 1.85
      }
    }
  ]
}
```

#### POST /strategies
**Description**: Create new strategy  
**Authentication**: JWT Token  
**Request Body**:
```json
{
  "name": "Custom Fibonacci Strategy",
  "description": "Modified Fibonacci strategy with custom parameters",
  "parameters": {
    "bars_range": 3,
    "fib_levels": [0.236, 0.382, 0.618, 0.786],
    "risk_per_trade": 0.015,
    "session_filter": true
  }
}
```

#### PUT /strategies/{strategy_id}
**Description**: Update strategy parameters  
**Authentication**: JWT Token  

#### DELETE /strategies/{strategy_id}
**Description**: Delete strategy  
**Authentication**: JWT Token  

### Market Data

#### GET /market-data/{symbol}
**Description**: Get current market data for symbol  
**Authentication**: API Key  
**Parameters**: 
- `symbol`: Trading symbol (e.g., EURUSD)

**Response**:
```json
{
  "symbol": "EURUSD",
  "bid": 1.0850,
  "ask": 1.0852,
  "spread": 0.0002,
  "timestamp": "2023-12-01T10:30:00Z",
  "session": "london",
  "volume": 15420
}
```

#### GET /historical-data/{symbol}
**Description**: Get historical price data  
**Authentication**: API Key  
**Parameters**: 
- `symbol`: Trading symbol
- `timeframe`: Timeframe (M1, M5, M15, H1, H4, D1)
- `start_date`: Start date (ISO 8601)
- `end_date`: End date (ISO 8601)
- `limit`: Maximum number of bars (default: 1000)

**Response**:
```json
{
  "symbol": "EURUSD",
  "timeframe": "H1",
  "data": [
    {
      "timestamp": "2023-12-01T09:00:00Z",
      "open": 1.0845,
      "high": 1.0865,
      "low": 1.0840,
      "close": 1.0860,
      "volume": 2540
    }
  ],
  "count": 24
}
```

### Analysis and Signals

#### GET /fractals/{symbol}
**Description**: Get fractal analysis for symbol  
**Authentication**: JWT Token  
**Parameters**: 
- `symbol`: Trading symbol
- `timeframe`: Timeframe
- `bars_range`: Fractal detection range (default: 2)

**Response**:
```json
{
  "symbol": "EURUSD",
  "timeframe": "H1",
  "fractals": [
    {
      "timestamp": "2023-12-01T08:00:00Z",
      "price": 1.0875,
      "type": "up",
      "strength": 0.85
    },
    {
      "timestamp": "2023-12-01T06:00:00Z",
      "price": 1.0835,
      "type": "down",
      "strength": 0.92
    }
  ],
  "analysis_time": "2023-12-01T10:30:00Z"
}
```

#### GET /fibonacci/{symbol}
**Description**: Get Fibonacci analysis for symbol  
**Authentication**: JWT Token  
**Parameters**: 
- `symbol`: Trading symbol
- `timeframe`: Timeframe

**Response**:
```json
{
  "symbol": "EURUSD",
  "timeframe": "H1",
  "swing": {
    "start_price": 1.0835,
    "end_price": 1.0875,
    "start_time": "2023-12-01T06:00:00Z",
    "end_time": "2023-12-01T08:00:00Z",
    "type": "bullish"
  },
  "retracements": {
    "23.6": 1.0865,
    "38.2": 1.0860,
    "50.0": 1.0855,
    "61.8": 1.0850,
    "78.6": 1.0845
  },
  "extensions": {
    "100.0": 1.0915,
    "127.2": 1.0926,
    "161.8": 1.0940,
    "200.0": 1.0955
  },
  "current_level": "61.8_retracement",
  "confluence_score": 0.78
}
```

#### GET /signals/{symbol}
**Description**: Get trading signals for symbol  
**Authentication**: JWT Token  
**Parameters**: 
- `symbol`: Trading symbol
- `strategy_id`: Strategy identifier (optional)

**Response**:
```json
{
  "symbol": "EURUSD",
  "signals": [
    {
      "id": "signal_001",
      "timestamp": "2023-12-01T10:30:00Z",
      "action": "buy",
      "confidence": 0.85,
      "entry_price": 1.0850,
      "stop_loss": 1.0820,
      "take_profit": 1.0920,
      "risk_reward_ratio": 2.33,
      "strategy": "fibonacci_retracement",
      "reasoning": "Price at 61.8% Fibonacci retracement with NY session confluence"
    }
  ]
}
```

### Performance and Analytics

#### GET /performance
**Description**: Get trading performance metrics  
**Authentication**: JWT Token  
**Parameters**: 
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `strategy_id`: Filter by strategy (optional)

**Response**:
```json
{
  "period": {
    "start_date": "2023-11-01T00:00:00Z",
    "end_date": "2023-12-01T00:00:00Z"
  },
  "summary": {
    "total_trades": 245,
    "winning_trades": 168,
    "losing_trades": 77,
    "win_rate": 0.686,
    "total_pnl": 12450.75,
    "gross_profit": 18920.50,
    "gross_loss": -6469.75,
    "profit_factor": 2.92,
    "sharpe_ratio": 1.85,
    "max_drawdown": 0.087,
    "max_drawdown_duration_days": 12,
    "average_trade": 50.82,
    "average_winner": 112.62,
    "average_loser": -84.02
  },
  "monthly_breakdown": [
    {
      "month": "2023-11",
      "trades": 245,
      "pnl": 12450.75,
      "win_rate": 0.686
    }
  ]
}
```

#### GET /analytics/drawdown
**Description**: Get detailed drawdown analysis  
**Authentication**: JWT Token  

#### GET /analytics/risk-metrics
**Description**: Get risk management metrics  
**Authentication**: JWT Token  

### Signal Performance Analytics

#### GET /signals/analytics
**Description**: Get comprehensive signal performance analytics for ML/AI development  
**Authentication**: JWT Token  
**Parameters**: None

**Response**:
```json
{
  "overall_performance": {
    "total_signals": 45,
    "overall_win_rate": 0.667,
    "active_signals": 3
  },
  "quality_performance": {
    "weak": {
      "count": 8,
      "win_rate": 0.375,
      "avg_confluence_score": 35.2,
      "avg_pnl": -12.5
    },
    "moderate": {
      "count": 22,
      "win_rate": 0.636,
      "avg_confluence_score": 58.7,
      "avg_pnl": 45.3
    },
    "strong": {
      "count": 15,
      "win_rate": 0.867,
      "avg_confluence_score": 82.1,
      "avg_pnl": 78.9
    }
  },
  "pattern_ranking": [
    {
      "pattern": "bullish_engulfing_strong",
      "win_rate": 0.89,
      "avg_pnl": 65.4,
      "total_signals": 9,
      "avg_confluence_score": 78.3
    }
  ],
  "confluence_score_analysis": {
    "0-40": {
      "count": 8,
      "win_rate": 0.375,
      "avg_pnl": -12.5
    },
    "40-60": {
      "count": 15,
      "win_rate": 0.600,
      "avg_pnl": 23.7
    },
    "60-80": {
      "count": 12,
      "win_rate": 0.750,
      "avg_pnl": 56.2
    },
    "80-100": {
      "count": 10,
      "win_rate": 0.900,
      "avg_pnl": 89.3
    }
  },
  "ml_features": {
    "feature_count": 45,
    "feature_names": [
      "fibonacci_level",
      "confluence_score", 
      "pattern_type_encoded",
      "pattern_strength_encoded",
      "quality_encoded",
      "num_factors",
      "signal_type_encoded"
    ],
    "label_distribution": {
      "wins": 30,
      "losses": 15
    },
    "ready_for_ml": false
  }
}
```

#### GET /signals/performance/export
**Description**: Export signal performance data for external analysis  
**Authentication**: JWT Token  
**Parameters**: None

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "signal_id": "2025-07-07T10:30:00_1.0850",
      "timestamp": "2025-07-07T10:30:00Z",
      "signal_type": "buy",
      "entry_price": 1.0850,
      "stop_loss": 1.0820,
      "take_profit": 1.0920,
      "fibonacci_level": 0.618,
      "pattern_type": "bullish_engulfing",
      "pattern_strength": "strong",
      "confluence_score": 78.5,
      "quality": "strong",
      "factors": ["Key Fibonacci level (61.8%)", "bullish_engulfing pattern"],
      "max_favorable_move": 45.0,
      "max_adverse_move": -8.0,
      "bars_to_target": 23,
      "final_outcome": "target_hit",
      "actual_pnl": 70.0,
      "performance_1h": 12.5,
      "performance_4h": 45.0,
      "performance_24h": 70.0,
      "signal_efficiency": 1.95,
      "drawdown_ratio": 0.18
    }
  ],
  "total_signals": 45
}
```

#### GET /signals/performance/real-time
**Description**: Get real-time signal performance statistics  
**Authentication**: JWT Token  
**Parameters**: None

**Response**:
```json
{
  "success": true,
  "stats": {
    "active_signals": 3,
    "completed_signals": 42,
    "win_rate": 66.7,
    "avg_bars_to_resolution": 28.5
  }
}
```

### Configuration

#### GET /config
**Description**: Get current configuration  
**Authentication**: JWT Token  

**Response**:
```json
{
  "trading": {
    "risk_per_trade": 0.01,
    "max_positions": 5,
    "max_daily_loss": 0.06
  },
  "fibonacci": {
    "retracement_levels": [0.236, 0.382, 0.5, 0.618, 0.786],
    "extension_levels": [1.0, 1.272, 1.618, 2.0]
  },
  "fractal": {
    "bars_range": 2
  },
  "session_analysis": {
    "enabled": true,
    "ny_open_time": "13:30",
    "london_open_time": "07:00"
  }
}
```

#### PUT /config
**Description**: Update configuration  
**Authentication**: JWT Token  
**Request Body**: Configuration object

## WebSocket API

### Connection
**URL**: `wss://api.fibonacci-trading-bot.com/v1/ws`  
**Authentication**: API Key in query parameter or JWT token in header

### Subscription Messages

#### Subscribe to Real-time Prices
```json
{
  "action": "subscribe",
  "channel": "prices",
  "symbols": ["EURUSD", "GBPUSD"]
}
```

#### Subscribe to Trading Signals
```json
{
  "action": "subscribe",
  "channel": "signals",
  "strategies": ["fibonacci_retracement"]
}
```

#### Subscribe to Position Updates
```json
{
  "action": "subscribe",
  "channel": "positions"
}
```

### Real-time Data Messages

#### Price Update
```json
{
  "channel": "prices",
  "data": {
    "symbol": "EURUSD",
    "bid": 1.0850,
    "ask": 1.0852,
    "timestamp": "2023-12-01T10:30:00Z"
  }
}
```

#### Trading Signal
```json
{
  "channel": "signals",
  "data": {
    "signal_id": "signal_001",
    "symbol": "EURUSD",
    "action": "buy",
    "confidence": 0.85,
    "timestamp": "2023-12-01T10:30:00Z"
  }
}
```

#### Position Update
```json
{
  "channel": "positions",
  "data": {
    "position_id": "pos_001",
    "event": "opened",
    "symbol": "EURUSD",
    "side": "long",
    "size": 0.1,
    "price": 1.0850,
    "timestamp": "2023-12-01T10:30:00Z"
  }
}
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "The specified symbol is not supported",
    "details": {
      "symbol": "INVALID",
      "supported_symbols": ["EURUSD", "GBPUSD", "USDJPY"]
    },
    "timestamp": "2023-12-01T10:30:00Z",
    "request_id": "req_12345"
  }
}
```

### HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Common Error Codes
- `INVALID_SYMBOL`: Unsupported trading symbol
- `INSUFFICIENT_FUNDS`: Not enough account balance
- `MARKET_CLOSED`: Market is currently closed
- `INVALID_PARAMETERS`: Request parameters are invalid
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `MT5_CONNECTION_ERROR`: MT5 connection issue
- `STRATEGY_NOT_FOUND`: Strategy does not exist

## Rate Limiting

### Rate Limits
- **Authentication endpoints**: 10 requests per minute
- **Market data endpoints**: 100 requests per minute
- **Trading endpoints**: 50 requests per minute
- **WebSocket connections**: 5 connections per API key

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701432600
```

## Data Schemas

### Position Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string"},
    "symbol": {"type": "string"},
    "side": {"type": "string", "enum": ["long", "short"]},
    "size": {"type": "number", "minimum": 0.01},
    "entry_price": {"type": "number"},
    "current_price": {"type": "number"},
    "unrealized_pnl": {"type": "number"},
    "open_time": {"type": "string", "format": "date-time"},
    "stop_loss": {"type": "number"},
    "take_profit": {"type": "number"},
    "strategy": {"type": "string"}
  },
  "required": ["id", "symbol", "side", "size", "entry_price"]
}
```

### Signal Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string"},
    "timestamp": {"type": "string", "format": "date-time"},
    "symbol": {"type": "string"},
    "action": {"type": "string", "enum": ["buy", "sell", "hold"]},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "entry_price": {"type": "number"},
    "stop_loss": {"type": "number"},
    "take_profit": {"type": "number"},
    "risk_reward_ratio": {"type": "number"},
    "strategy": {"type": "string"},
    "reasoning": {"type": "string"}
  },
  "required": ["id", "timestamp", "symbol", "action", "confidence"]
}
```

This API specification provides a comprehensive interface for interacting with the Fibonacci trading bot, enabling both programmatic access and real-time monitoring of trading operations.
