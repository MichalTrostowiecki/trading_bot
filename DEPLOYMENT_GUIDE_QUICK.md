# Quick Deployment Guide - Fibonacci Trading Bot

## 🚀 PRODUCTION READY SYSTEM

### Prerequisites
- **Windows Machine** (MT5 Python API requirement)
- **MetaTrader 5** installed and configured
- **Python 3.10+** installed
- **Active MT5 Account** (Demo or Live)

### Quick Start (5 Minutes)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure MT5 Account**
   Edit `config/development.yaml`:
   ```yaml
   mt5:
     login: YOUR_LOGIN
     password: YOUR_PASSWORD
     server: YOUR_SERVER
     timeout: 10000
   ```

3. **Start the Bot**
   ```bash
   python main.py
   ```

4. **Access Dashboard**
   Open browser: http://localhost:8000

### Current Configuration
- **Demo Account**: BlueberryMarkets-Demo (Login: 12605399)
- **Trading Symbols**: EURUSD (currently enabled)
- **Risk Settings**: 1% per trade, max 3 positions
- **Chart Updates**: Every 3 seconds
- **Fractal Detection**: 3-period responsive algorithm

### Dashboard Controls
- **Start Trading**: Begin automated trading
- **Pause**: Stop new trades, keep positions
- **Stop**: Stop trading and optionally close positions
- **Emergency Stop**: Immediately close all positions

### Key Features Working
✅ Real MT5 order placement
✅ Fibonacci retracement analysis
✅ Fractal-based swing detection
✅ Live chart visualization
✅ Position management
✅ Risk controls
✅ Web-based monitoring

### Production Deployment
- Deploy on Windows VPS
- Configure as Windows service
- Set up monitoring alerts
- Enable 24/7 operation

### Support
- All logs available in console output
- Detailed fractal and trade execution logging
- Real-time position tracking
- Comprehensive error handling

**System is fully operational and ready for live trading!** 📊✨