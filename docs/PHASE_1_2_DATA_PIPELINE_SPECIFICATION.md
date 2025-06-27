# Phase 1.2: Data Pipeline Implementation - Detailed Specification

## Overview
Phase 1.2 implements the core data pipeline for the trading bot, including MT5 integration, historical data collection, real-time streaming, and data validation systems.

## Objectives
- Establish reliable MT5 connection and data retrieval
- Implement historical data collection with caching
- Create real-time data streaming system
- Build data validation and quality assurance
- Set up data storage and management systems

## Prerequisites
- Phase 1.1 (Environment Setup) completed
- MT5 terminal installed and configured
- Python environment with all dependencies
- Configuration system operational

## Detailed Tasks

### Task 1.2.1: MT5 Interface Implementation
**Duration**: 6 hours  
**Priority**: Critical  
**Dependencies**: Phase 1.1 complete  

#### Implementation Steps

1. **Create MT5 Connection Manager**

   **File**: `src/data/mt5_interface.py`
   ```python
   import MetaTrader5 as mt5
   import pandas as pd
   from datetime import datetime, timedelta
   from typing import Optional, List, Dict, Any
   from loguru import logger
   from src.utils.config import config
   from src.monitoring.logging_config import trading_logger
   
   class MT5Interface:
       """MetaTrader 5 interface for data retrieval and trading operations."""
       
       def __init__(self):
           self.connected = False
           self.account_info = None
           self.symbols_info = {}
           
       def connect(self) -> bool:
           """Establish connection to MT5 terminal."""
           try:
               # Initialize MT5 connection
               if not mt5.initialize():
                   logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                   return False
               
               # Login to account if credentials provided
               if config.mt5.login and config.mt5.password:
                   login_result = mt5.login(
                       login=config.mt5.login,
                       password=config.mt5.password,
                       server=config.mt5.server,
                       timeout=config.mt5.timeout
                   )
                   
                   if not login_result:
                       logger.error(f"MT5 login failed: {mt5.last_error()}")
                       return False
               
               # Get account information
               self.account_info = mt5.account_info()
               if self.account_info is None:
                   logger.error("Failed to get account information")
                   return False
               
               self.connected = True
               logger.info(f"Connected to MT5 - Account: {self.account_info.login}")
               return True
               
           except Exception as e:
               logger.error(f"MT5 connection error: {e}")
               return False
       
       def disconnect(self):
           """Disconnect from MT5 terminal."""
           if self.connected:
               mt5.shutdown()
               self.connected = False
               logger.info("Disconnected from MT5")
       
       def get_symbol_info(self, symbol: str) -> Optional[Dict]:
           """Get symbol information and cache it."""
           if symbol in self.symbols_info:
               return self.symbols_info[symbol]
           
           symbol_info = mt5.symbol_info(symbol)
           if symbol_info is None:
               logger.warning(f"Symbol {symbol} not found")
               return None
           
           # Convert to dictionary and cache
           info_dict = symbol_info._asdict()
           self.symbols_info[symbol] = info_dict
           return info_dict
       
       def get_historical_data(
           self, 
           symbol: str, 
           timeframe: int, 
           start_date: datetime, 
           end_date: Optional[datetime] = None,
           count: Optional[int] = None
       ) -> Optional[pd.DataFrame]:
           """Retrieve historical OHLCV data."""
           
           if not self.connected:
               logger.error("MT5 not connected")
               return None
           
           try:
               # Convert timeframe string to MT5 constant
               tf_map = {
                   "M1": mt5.TIMEFRAME_M1,
                   "M5": mt5.TIMEFRAME_M5,
                   "M15": mt5.TIMEFRAME_M15,
                   "M30": mt5.TIMEFRAME_M30,
                   "H1": mt5.TIMEFRAME_H1,
                   "H4": mt5.TIMEFRAME_H4,
                   "D1": mt5.TIMEFRAME_D1,
                   "W1": mt5.TIMEFRAME_W1,
                   "MN1": mt5.TIMEFRAME_MN1
               }
               
               mt5_timeframe = tf_map.get(timeframe)
               if mt5_timeframe is None:
                   logger.error(f"Invalid timeframe: {timeframe}")
                   return None
               
               # Get data using appropriate method
               if count:
                   rates = mt5.copy_rates_from(symbol, mt5_timeframe, start_date, count)
               elif end_date:
                   rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)
               else:
                   # Default to 1000 bars from start_date
                   rates = mt5.copy_rates_from(symbol, mt5_timeframe, start_date, 1000)
               
               if rates is None or len(rates) == 0:
                   logger.warning(f"No data retrieved for {symbol} {timeframe}")
                   return None
               
               # Convert to DataFrame
               df = pd.DataFrame(rates)
               df['time'] = pd.to_datetime(df['time'], unit='s')
               df.set_index('time', inplace=True)
               
               # Rename columns to standard format
               df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Spread', 'Real_Volume']
               
               logger.info(f"Retrieved {len(df)} bars for {symbol} {timeframe}")
               return df
               
           except Exception as e:
               logger.error(f"Error retrieving historical data: {e}")
               return None
       
       def get_current_tick(self, symbol: str) -> Optional[Dict]:
           """Get current tick data for symbol."""
           if not self.connected:
               return None
           
           tick = mt5.symbol_info_tick(symbol)
           if tick is None:
               return None
           
           return {
               'symbol': symbol,
               'time': datetime.fromtimestamp(tick.time),
               'bid': tick.bid,
               'ask': tick.ask,
               'last': tick.last,
               'volume': tick.volume,
               'spread': tick.ask - tick.bid
           }
       
       def get_market_hours(self, symbol: str) -> Dict[str, Any]:
           """Get trading session information for symbol."""
           symbol_info = self.get_symbol_info(symbol)
           if not symbol_info:
               return {}
           
           return {
               'trade_mode': symbol_info.get('trade_mode'),
               'trade_execution': symbol_info.get('trade_execution'),
               'trade_stops_level': symbol_info.get('trade_stops_level'),
               'trade_freeze_level': symbol_info.get('trade_freeze_level')
           }
   
   # Global MT5 interface instance
   mt5_interface = MT5Interface()
   ```

2. **Create Connection Health Monitor**

   **File**: `src/data/connection_monitor.py`
   ```python
   import asyncio
   import time
   from datetime import datetime
   from typing import Callable, Optional
   from loguru import logger
   from src.data.mt5_interface import mt5_interface
   
   class ConnectionMonitor:
       """Monitor MT5 connection health and handle reconnections."""
       
       def __init__(self, check_interval: int = 30):
           self.check_interval = check_interval
           self.is_monitoring = False
           self.last_check = None
           self.connection_callbacks = []
           self.disconnection_callbacks = []
       
       def add_connection_callback(self, callback: Callable):
           """Add callback to execute when connection is established."""
           self.connection_callbacks.append(callback)
       
       def add_disconnection_callback(self, callback: Callable):
           """Add callback to execute when connection is lost."""
           self.disconnection_callbacks.append(callback)
       
       async def start_monitoring(self):
           """Start connection monitoring loop."""
           self.is_monitoring = True
           logger.info("Starting connection monitoring")
           
           while self.is_monitoring:
               try:
                   await self._check_connection()
                   await asyncio.sleep(self.check_interval)
               except Exception as e:
                   logger.error(f"Connection monitoring error: {e}")
                   await asyncio.sleep(5)  # Short delay before retry
       
       def stop_monitoring(self):
           """Stop connection monitoring."""
           self.is_monitoring = False
           logger.info("Stopping connection monitoring")
       
       async def _check_connection(self):
           """Check MT5 connection status."""
           self.last_check = datetime.now()
           
           if not mt5_interface.connected:
               logger.warning("MT5 not connected, attempting reconnection")
               if await self._reconnect():
                   await self._execute_callbacks(self.connection_callbacks)
               return
           
           # Test connection with a simple operation
           try:
               test_symbol = "EURUSD"  # Use a common symbol for testing
               tick = mt5_interface.get_current_tick(test_symbol)
               
               if tick is None:
                   logger.warning("Connection test failed, attempting reconnection")
                   if await self._reconnect():
                       await self._execute_callbacks(self.connection_callbacks)
               else:
                   logger.debug("Connection test successful")
                   
           except Exception as e:
               logger.error(f"Connection test error: {e}")
               if await self._reconnect():
                   await self._execute_callbacks(self.connection_callbacks)
       
       async def _reconnect(self) -> bool:
           """Attempt to reconnect to MT5."""
           try:
               # Disconnect first
               mt5_interface.disconnect()
               await asyncio.sleep(2)
               
               # Attempt reconnection
               if mt5_interface.connect():
                   logger.info("MT5 reconnection successful")
                   return True
               else:
                   logger.error("MT5 reconnection failed")
                   await self._execute_callbacks(self.disconnection_callbacks)
                   return False
                   
           except Exception as e:
               logger.error(f"Reconnection error: {e}")
               return False
       
       async def _execute_callbacks(self, callbacks: list):
           """Execute list of callbacks."""
           for callback in callbacks:
               try:
                   if asyncio.iscoroutinefunction(callback):
                       await callback()
                   else:
                       callback()
               except Exception as e:
                   logger.error(f"Callback execution error: {e}")
   
   # Global connection monitor instance
   connection_monitor = ConnectionMonitor()
   ```

**Acceptance Criteria**:
- [ ] MT5 connection established successfully
- [ ] Historical data retrieval working for all configured symbols
- [ ] Current tick data accessible
- [ ] Connection monitoring and auto-reconnection functional
- [ ] Error handling for all connection scenarios
- [ ] Logging captures all connection events

### Task 1.2.2: Historical Data Collection System
**Duration**: 8 hours  
**Priority**: Critical  
**Dependencies**: Task 1.2.1 complete  

#### Implementation Steps

1. **Create Data Collection Manager**

   **File**: `src/data/data_collector.py`
   ```python
   import pandas as pd
   from datetime import datetime, timedelta
   from pathlib import Path
   from typing import List, Dict, Optional
   from concurrent.futures import ThreadPoolExecutor, as_completed
   from loguru import logger
   from src.data.mt5_interface import mt5_interface
   from src.utils.config import config
   
   class HistoricalDataCollector:
       """Collect and manage historical market data."""
       
       def __init__(self):
           self.data_path = Path("data/historical")
           self.data_path.mkdir(parents=True, exist_ok=True)
           self.cache = {}
       
       def collect_symbol_data(
           self, 
           symbol: str, 
           timeframes: List[str], 
           days_back: int = None
       ) -> Dict[str, pd.DataFrame]:
           """Collect historical data for a symbol across multiple timeframes."""
           
           if days_back is None:
               days_back = config.data.history_days
           
           start_date = datetime.now() - timedelta(days=days_back)
           results = {}
           
           for timeframe in timeframes:
               logger.info(f"Collecting {symbol} {timeframe} data")
               
               try:
                   df = mt5_interface.get_historical_data(
                       symbol=symbol,
                       timeframe=timeframe,
                       start_date=start_date
                   )
                   
                   if df is not None and not df.empty:
                       # Save to cache
                       cache_key = f"{symbol}_{timeframe}"
                       self.cache[cache_key] = df
                       
                       # Save to file
                       self._save_data(df, symbol, timeframe)
                       results[timeframe] = df
                       
                       logger.info(f"Collected {len(df)} bars for {symbol} {timeframe}")
                   else:
                       logger.warning(f"No data collected for {symbol} {timeframe}")
                       
               except Exception as e:
                   logger.error(f"Error collecting {symbol} {timeframe}: {e}")
           
           return results
       
       def collect_all_configured_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
           """Collect data for all configured symbols and timeframes."""
           
           all_data = {}
           
           # Use ThreadPoolExecutor for parallel data collection
           with ThreadPoolExecutor(max_workers=4) as executor:
               future_to_symbol = {
                   executor.submit(
                       self.collect_symbol_data, 
                       symbol, 
                       config.data.timeframes
                   ): symbol 
                   for symbol in config.data.symbols
               }
               
               for future in as_completed(future_to_symbol):
                   symbol = future_to_symbol[future]
                   try:
                       symbol_data = future.result()
                       all_data[symbol] = symbol_data
                       logger.info(f"Completed data collection for {symbol}")
                   except Exception as e:
                       logger.error(f"Failed to collect data for {symbol}: {e}")
           
           return all_data
       
       def _save_data(self, df: pd.DataFrame, symbol: str, timeframe: str):
           """Save DataFrame to CSV file."""
           filename = f"{symbol}_{timeframe}.csv"
           filepath = self.data_path / filename
           
           try:
               df.to_csv(filepath)
               logger.debug(f"Saved {symbol} {timeframe} data to {filepath}")
           except Exception as e:
               logger.error(f"Error saving data to {filepath}: {e}")
       
       def load_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
           """Load historical data from cache or file."""
           
           # Check cache first
           cache_key = f"{symbol}_{timeframe}"
           if cache_key in self.cache:
               return self.cache[cache_key]
           
           # Load from file
           filename = f"{symbol}_{timeframe}.csv"
           filepath = self.data_path / filename
           
           if filepath.exists():
               try:
                   df = pd.read_csv(filepath, index_col=0, parse_dates=True)
                   self.cache[cache_key] = df
                   return df
               except Exception as e:
                   logger.error(f"Error loading data from {filepath}: {e}")
           
           return None
       
       def update_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
           """Update existing data with latest bars."""
           
           existing_data = self.load_data(symbol, timeframe)
           
           if existing_data is None or existing_data.empty:
               # No existing data, collect from scratch
               return self.collect_symbol_data(symbol, [timeframe]).get(timeframe)
           
           # Get the last timestamp
           last_timestamp = existing_data.index[-1]
           
           # Collect new data from last timestamp
           new_data = mt5_interface.get_historical_data(
               symbol=symbol,
               timeframe=timeframe,
               start_date=last_timestamp,
               count=1000  # Get recent bars
           )
           
           if new_data is None or new_data.empty:
               logger.info(f"No new data for {symbol} {timeframe}")
               return existing_data
           
           # Remove duplicate timestamps and combine
           new_data = new_data[new_data.index > last_timestamp]
           
           if not new_data.empty:
               combined_data = pd.concat([existing_data, new_data])
               combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
               combined_data.sort_index(inplace=True)
               
               # Update cache and save
               cache_key = f"{symbol}_{timeframe}"
               self.cache[cache_key] = combined_data
               self._save_data(combined_data, symbol, timeframe)
               
               logger.info(f"Updated {symbol} {timeframe} with {len(new_data)} new bars")
               return combined_data
           
           return existing_data
       
       def get_data_summary(self) -> Dict[str, Dict]:
           """Get summary of available data."""
           summary = {}
           
           for symbol in config.data.symbols:
               symbol_summary = {}
               for timeframe in config.data.timeframes:
                   data = self.load_data(symbol, timeframe)
                   if data is not None:
                       symbol_summary[timeframe] = {
                           'bars': len(data),
                           'start_date': data.index[0].strftime('%Y-%m-%d'),
                           'end_date': data.index[-1].strftime('%Y-%m-%d'),
                           'file_size_mb': self._get_file_size(symbol, timeframe)
                       }
                   else:
                       symbol_summary[timeframe] = None
               
               summary[symbol] = symbol_summary
           
           return summary
       
       def _get_file_size(self, symbol: str, timeframe: str) -> float:
           """Get file size in MB."""
           filename = f"{symbol}_{timeframe}.csv"
           filepath = self.data_path / filename
           
           if filepath.exists():
               return filepath.stat().st_size / (1024 * 1024)
           return 0.0
   
   # Global data collector instance
   data_collector = HistoricalDataCollector()
   ```

**Acceptance Criteria**:
- [ ] Historical data collection for all configured symbols/timeframes
- [ ] Data saved to CSV files with proper formatting
- [ ] Caching system reduces redundant data requests
- [ ] Parallel data collection improves performance
- [ ] Data update mechanism adds only new bars
- [ ] Data summary provides overview of available data

### Task 1.2.3: Real-time Data Streaming
**Duration**: 6 hours  
**Priority**: High  
**Dependencies**: Task 1.2.2 complete  

#### Implementation Steps

1. **Create Real-time Data Stream Manager**

   **File**: `src/data/realtime_stream.py`
   ```python
   import asyncio
   import pandas as pd
   from datetime import datetime
   from typing import Dict, List, Callable, Optional
   from collections import deque
   from loguru import logger
   from src.data.mt5_interface import mt5_interface
   from src.utils.config import config
   
   class RealTimeDataStream:
       """Manage real-time data streaming and tick processing."""
       
       def __init__(self, buffer_size: int = 1000):
           self.buffer_size = buffer_size
           self.tick_buffers = {}  # symbol -> deque of ticks
           self.bar_buffers = {}   # symbol_timeframe -> deque of bars
           self.subscribers = {}   # event_type -> list of callbacks
           self.is_streaming = False
           self.stream_task = None
           
           # Initialize buffers for configured symbols
           for symbol in config.data.symbols:
               self.tick_buffers[symbol] = deque(maxlen=buffer_size)
               for timeframe in config.data.timeframes:
                   key = f"{symbol}_{timeframe}"
                   self.bar_buffers[key] = deque(maxlen=buffer_size)
       
       def subscribe(self, event_type: str, callback: Callable):
           """Subscribe to data events."""
           if event_type not in self.subscribers:
               self.subscribers[event_type] = []
           self.subscribers[event_type].append(callback)
           logger.info(f"Subscribed to {event_type} events")
       
       def unsubscribe(self, event_type: str, callback: Callable):
           """Unsubscribe from data events."""
           if event_type in self.subscribers:
               try:
                   self.subscribers[event_type].remove(callback)
               except ValueError:
                   pass
       
       async def start_streaming(self):
           """Start real-time data streaming."""
           if self.is_streaming:
               logger.warning("Data streaming already active")
               return
           
           self.is_streaming = True
           self.stream_task = asyncio.create_task(self._stream_loop())
           logger.info("Started real-time data streaming")
       
       async def stop_streaming(self):
           """Stop real-time data streaming."""
           if not self.is_streaming:
               return
           
           self.is_streaming = False
           if self.stream_task:
               self.stream_task.cancel()
               try:
                   await self.stream_task
               except asyncio.CancelledError:
                   pass
           
           logger.info("Stopped real-time data streaming")
       
       async def _stream_loop(self):
           """Main streaming loop."""
           while self.is_streaming:
               try:
                   # Process ticks for all symbols
                   for symbol in config.data.symbols:
                       await self._process_symbol_tick(symbol)
                   
                   # Small delay to prevent excessive CPU usage
                   await asyncio.sleep(0.1)
                   
               except Exception as e:
                   logger.error(f"Streaming loop error: {e}")
                   await asyncio.sleep(1)
       
       async def _process_symbol_tick(self, symbol: str):
           """Process tick data for a symbol."""
           try:
               tick_data = mt5_interface.get_current_tick(symbol)
               
               if tick_data:
                   # Add to tick buffer
                   self.tick_buffers[symbol].append(tick_data)
                   
                   # Notify tick subscribers
                   await self._notify_subscribers('tick', {
                       'symbol': symbol,
                       'data': tick_data
                   })
                   
                   # Check for new bar formation
                   await self._check_new_bars(symbol, tick_data)
                   
           except Exception as e:
               logger.error(f"Error processing tick for {symbol}: {e}")
       
       async def _check_new_bars(self, symbol: str, tick_data: Dict):
           """Check if new bars have formed and update bar buffers."""
           
           for timeframe in config.data.timeframes:
               try:
                   # Get latest bar from MT5
                   latest_bar = mt5_interface.get_historical_data(
                       symbol=symbol,
                       timeframe=timeframe,
                       start_date=datetime.now(),
                       count=1
                   )
                   
                   if latest_bar is not None and not latest_bar.empty:
                       key = f"{symbol}_{timeframe}"
                       
                       # Check if this is a new bar
                       if (not self.bar_buffers[key] or 
                           latest_bar.index[-1] > self.bar_buffers[key][-1]['timestamp']):
                           
                           bar_dict = {
                               'symbol': symbol,
                               'timeframe': timeframe,
                               'timestamp': latest_bar.index[-1],
                               'open': latest_bar.iloc[-1]['Open'],
                               'high': latest_bar.iloc[-1]['High'],
                               'low': latest_bar.iloc[-1]['Low'],
                               'close': latest_bar.iloc[-1]['Close'],
                               'volume': latest_bar.iloc[-1]['Volume']
                           }
                           
                           self.bar_buffers[key].append(bar_dict)
                           
                           # Notify bar subscribers
                           await self._notify_subscribers('new_bar', bar_dict)
                           
               except Exception as e:
                   logger.error(f"Error checking new bars for {symbol} {timeframe}: {e}")
       
       async def _notify_subscribers(self, event_type: str, data: Dict):
           """Notify all subscribers of an event."""
           if event_type in self.subscribers:
               for callback in self.subscribers[event_type]:
                   try:
                       if asyncio.iscoroutinefunction(callback):
                           await callback(data)
                       else:
                           callback(data)
                   except Exception as e:
                       logger.error(f"Error in subscriber callback: {e}")
       
       def get_recent_ticks(self, symbol: str, count: int = 100) -> List[Dict]:
           """Get recent tick data for a symbol."""
           if symbol in self.tick_buffers:
               return list(self.tick_buffers[symbol])[-count:]
           return []
       
       def get_recent_bars(self, symbol: str, timeframe: str, count: int = 100) -> List[Dict]:
           """Get recent bar data for a symbol and timeframe."""
           key = f"{symbol}_{timeframe}"
           if key in self.bar_buffers:
               return list(self.bar_buffers[key])[-count:]
           return []
       
       def get_current_prices(self) -> Dict[str, Dict]:
           """Get current prices for all symbols."""
           current_prices = {}
           
           for symbol in config.data.symbols:
               if symbol in self.tick_buffers and self.tick_buffers[symbol]:
                   latest_tick = self.tick_buffers[symbol][-1]
                   current_prices[symbol] = {
                       'bid': latest_tick['bid'],
                       'ask': latest_tick['ask'],
                       'spread': latest_tick['spread'],
                       'time': latest_tick['time']
                   }
           
           return current_prices
   
   # Global real-time data stream instance
   realtime_stream = RealTimeDataStream()
   ```

**Acceptance Criteria**:
- [ ] Real-time tick data streaming for all configured symbols
- [ ] New bar detection and notification system
- [ ] Event subscription system for data consumers
- [ ] Buffering system maintains recent data in memory
- [ ] Error handling prevents stream interruption
- [ ] Performance optimized for continuous operation

### Deliverables Summary

#### Phase 1.2 Deliverables
- [ ] MT5Interface class with connection management
- [ ] ConnectionMonitor for health monitoring and auto-reconnection
- [ ] HistoricalDataCollector for bulk data collection and caching
- [ ] RealTimeDataStream for live data processing
- [ ] Data validation and quality assurance systems
- [ ] Comprehensive error handling and logging
- [ ] Performance optimization for large datasets

#### Quality Gates
- [ ] MT5 connection stable for >1 hour continuous operation
- [ ] Historical data collection completes for all symbols/timeframes
- [ ] Real-time streaming processes >1000 ticks without errors
- [ ] Data validation catches and handles corrupt data
- [ ] Memory usage remains stable during extended operation
- [ ] All data operations logged appropriately

#### Integration Points
- [ ] Configuration system integration
- [ ] Logging system integration
- [ ] Error handling integration
- [ ] Performance monitoring integration

### Next Phase Dependencies
Phase 1.3 (Research Tools Development) requires:
- [ ] Working data pipeline with historical and real-time data
- [ ] Stable MT5 connection
- [ ] Data caching and storage systems operational
- [ ] Event subscription system functional
