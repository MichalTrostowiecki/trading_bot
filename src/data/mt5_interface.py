"""
MetaTrader 5 Interface
Handles connection, data retrieval, and order management with MT5.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

# Try to import MetaTrader5, fallback to mock if not available (for testing)
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    # Simple mock for environments where MT5 isn't available
    class MockMT5:
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_M30 = 30
        TIMEFRAME_H1 = 60
        TIMEFRAME_H4 = 240
        TIMEFRAME_D1 = 1440
        TIMEFRAME_W1 = 10080
        TIMEFRAME_MN1 = 43200
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        
        def initialize(self): return False  # Will fail gracefully
        def shutdown(self): return True
        def login(self, *args, **kwargs): return False
        def account_info(self): return None
        def last_error(self): return "MT5 not available on this platform"
    
    mt5 = MockMT5()
    MT5_AVAILABLE = False

from src.utils.config import get_config, MT5Config
from src.monitoring import get_logger

logger = get_logger("mt5_interface")


class ConnectionStatus(Enum):
    """Connection status enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class TimeFrame(Enum):
    """MT5 timeframe enumeration."""
    M1 = mt5.TIMEFRAME_M1
    M5 = mt5.TIMEFRAME_M5
    M15 = mt5.TIMEFRAME_M15
    M30 = mt5.TIMEFRAME_M30
    H1 = mt5.TIMEFRAME_H1
    H4 = mt5.TIMEFRAME_H4
    D1 = mt5.TIMEFRAME_D1
    W1 = mt5.TIMEFRAME_W1
    MN1 = mt5.TIMEFRAME_MN1


@dataclass
class ConnectionInfo:
    """MT5 connection information."""
    status: ConnectionStatus
    server: str
    login: int
    company: str
    currency: str
    leverage: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    connected_at: Optional[datetime] = None
    last_error: Optional[str] = None


@dataclass
class SymbolInfo:
    """Symbol information from MT5."""
    name: str
    description: str
    currency_base: str
    currency_profit: str
    currency_margin: str
    digits: int
    point: float
    spread: int
    trade_contract_size: float
    minimum_volume: float
    maximum_volume: float
    volume_step: float
    margin_initial: float
    margin_maintenance: float
    session_deals: int
    session_buy_orders: int
    session_sell_orders: int
    visible: bool
    select: bool


class MT5Interface:
    """MetaTrader 5 interface for data and trading operations."""
    
    def __init__(self, config: Optional[MT5Config] = None):
        self.config = config or get_config().mt5
        self.connection_info: Optional[ConnectionInfo] = None
        self.is_connected = False
        self._lock = threading.RLock()
        self._last_heartbeat = None
        self._heartbeat_interval = 30  # seconds
        
    def connect(self) -> bool:
        """Establish connection to MT5 terminal."""
        with self._lock:
            try:
                logger.info(f"Connecting to MT5 server: {self.config.server}")
                
                # Initialize MT5
                if not mt5.initialize():
                    error_msg = f"MT5 initialize failed: {mt5.last_error()}"
                    logger.error(error_msg)
                    return False
                
                # Authorize with credentials
                authorized = mt5.login(
                    login=self.config.login,
                    password=self.config.password,
                    server=self.config.server,
                    timeout=self.config.timeout
                )
                
                if not authorized:
                    error_msg = f"MT5 login failed: {mt5.last_error()}"
                    logger.error(error_msg)
                    mt5.shutdown()
                    return False
                
                # Get account info
                account_info = mt5.account_info()
                if account_info is None:
                    error_msg = "Failed to retrieve account information"
                    logger.error(error_msg)
                    mt5.shutdown()
                    return False
                
                # Store connection information
                self.connection_info = ConnectionInfo(
                    status=ConnectionStatus.CONNECTED,
                    server=account_info.server,
                    login=account_info.login,
                    company=account_info.company,
                    currency=account_info.currency,
                    leverage=account_info.leverage,
                    balance=account_info.balance,
                    equity=account_info.equity,
                    margin=account_info.margin,
                    free_margin=account_info.margin_free,
                    connected_at=datetime.now()
                )
                
                self.is_connected = True
                self._last_heartbeat = time.time()
                
                logger.info(
                    f"Connected to MT5: {account_info.company} "
                    f"(Login: {account_info.login}, Server: {account_info.server})"
                )
                return True
                
            except Exception as e:
                error_msg = f"Connection error: {e}"
                logger.error(error_msg)
                self.connection_info = ConnectionInfo(
                    status=ConnectionStatus.ERROR,
                    server="",
                    login=0,
                    company="",
                    currency="",
                    leverage=0,
                    balance=0.0,
                    equity=0.0,
                    margin=0.0,
                    free_margin=0.0,
                    last_error=error_msg
                )
                return False
    
    def disconnect(self) -> bool:
        """Disconnect from MT5 terminal."""
        with self._lock:
            try:
                if self.is_connected:
                    mt5.shutdown()
                    self.is_connected = False
                    if self.connection_info:
                        self.connection_info.status = ConnectionStatus.DISCONNECTED
                    logger.info("Disconnected from MT5")
                return True
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
                return False
    
    def is_alive(self) -> bool:
        """Check if connection is alive."""
        if not self.is_connected:
            return False
        
        try:
            # Simple heartbeat check
            current_time = time.time()
            if (self._last_heartbeat and 
                current_time - self._last_heartbeat > self._heartbeat_interval):
                
                # Test connection with a simple query
                account_info = mt5.account_info()
                if account_info is None:
                    logger.warning("Heartbeat failed - connection lost")
                    self.is_connected = False
                    return False
                
                self._last_heartbeat = current_time
            
            return True
            
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            self.is_connected = False
            return False
    
    def reconnect(self) -> bool:
        """Reconnect to MT5 terminal."""
        logger.info("Attempting to reconnect to MT5")
        self.disconnect()
        return self.connect()
    
    def get_symbols(self) -> List[SymbolInfo]:
        """Get list of available symbols."""
        if not self.is_alive():
            raise ConnectionError("Not connected to MT5")
        
        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                logger.error(f"Failed to get symbols: {mt5.last_error()}")
                return []
            
            symbol_list = []
            for symbol in symbols:
                symbol_info = SymbolInfo(
                    name=symbol.name,
                    description=symbol.description,
                    currency_base=symbol.currency_base,
                    currency_profit=symbol.currency_profit,
                    currency_margin=symbol.currency_margin,
                    digits=symbol.digits,
                    point=symbol.point,
                    spread=symbol.spread,
                    trade_contract_size=symbol.trade_contract_size,
                    minimum_volume=symbol.volume_min,
                    maximum_volume=symbol.volume_max,
                    volume_step=symbol.volume_step,
                    margin_initial=symbol.margin_initial,
                    margin_maintenance=symbol.margin_maintenance,
                    session_deals=symbol.session_deals,
                    session_buy_orders=symbol.session_buy_orders,
                    session_sell_orders=symbol.session_sell_orders,
                    visible=symbol.visible,
                    select=symbol.select
                )
                symbol_list.append(symbol_info)
            
            logger.debug(f"Retrieved {len(symbol_list)} symbols")
            return symbol_list
            
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return []
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get information for a specific symbol."""
        if not self.is_alive():
            raise ConnectionError("Not connected to MT5")
        
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.warning(f"Symbol not found: {symbol}")
                return None
            
            return SymbolInfo(
                name=symbol_info.name,
                description=symbol_info.description,
                currency_base=symbol_info.currency_base,
                currency_profit=symbol_info.currency_profit,
                currency_margin=symbol_info.currency_margin,
                digits=symbol_info.digits,
                point=symbol_info.point,
                spread=symbol_info.spread,
                trade_contract_size=symbol_info.trade_contract_size,
                minimum_volume=symbol_info.volume_min,
                maximum_volume=symbol_info.volume_max,
                volume_step=symbol_info.volume_step,
                margin_initial=symbol_info.margin_initial,
                margin_maintenance=symbol_info.margin_maintenance,
                session_deals=symbol_info.session_deals,
                session_buy_orders=symbol_info.session_buy_orders,
                session_sell_orders=symbol_info.session_sell_orders,
                visible=symbol_info.visible,
                select=symbol_info.select
            )
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_rates(self, symbol: str, timeframe: TimeFrame, 
                  count: int = 1000, from_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """Get historical rates for a symbol."""
        if not self.is_alive():
            raise ConnectionError("Not connected to MT5")
        
        try:
            # Enable symbol if not selected
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol: {symbol}")
                return None
            
            # Get rates
            if from_date:
                rates = mt5.copy_rates_from(symbol, timeframe.value, from_date, count)
            else:
                rates = mt5.copy_rates_from_pos(symbol, timeframe.value, 0, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No rates data for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Rename columns to standard format
            df.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'tick_volume': 'Volume'
            }, inplace=True)
            
            logger.debug(f"Retrieved {len(df)} rates for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting rates for {symbol}: {e}")
            return None
    
    def get_ticks(self, symbol: str, count: int = 1000, 
                  from_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """Get tick data for a symbol."""
        if not self.is_alive():
            raise ConnectionError("Not connected to MT5")
        
        try:
            # Enable symbol if not selected
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol: {symbol}")
                return None
            
            # Get ticks
            if from_date:
                ticks = mt5.copy_ticks_from(symbol, from_date, count, mt5.COPY_TICKS_ALL)
            else:
                ticks = mt5.copy_ticks_from_pos(symbol, 0, count, mt5.COPY_TICKS_ALL)
            
            if ticks is None or len(ticks) == 0:
                logger.warning(f"No tick data for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            logger.debug(f"Retrieved {len(df)} ticks for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting ticks for {symbol}: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get current account information."""
        if not self.is_alive():
            raise ConnectionError("Not connected to MT5")
        
        try:
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                return None
            
            return {
                'login': account_info.login,
                'trade_mode': account_info.trade_mode,
                'leverage': account_info.leverage,
                'limit_orders': account_info.limit_orders,
                'margin_so_mode': account_info.margin_so_mode,
                'trade_allowed': account_info.trade_allowed,
                'trade_expert': account_info.trade_expert,
                'margin_mode': account_info.margin_mode,
                'currency_digits': account_info.currency_digits,
                'balance': account_info.balance,
                'credit': account_info.credit,
                'profit': account_info.profit,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'margin_level': account_info.margin_level,
                'margin_so_call': account_info.margin_so_call,
                'margin_so_so': account_info.margin_so_so,
                'margin_initial': account_info.margin_initial,
                'margin_maintenance': account_info.margin_maintenance,
                'assets': account_info.assets,
                'liabilities': account_info.liabilities,
                'commission_blocked': account_info.commission_blocked,
                'name': account_info.name,
                'server': account_info.server,
                'currency': account_info.currency,
                'company': account_info.company
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols."""
        if not self.is_alive():
            return []
        
        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                return []
            
            # Return just the symbol names
            symbol_names = [s.name for s in symbols]
            logger.info(f"Found {len(symbol_names)} available symbols")
            
            # Log forex symbols for debugging
            forex_symbols = [s for s in symbol_names if any(pair in s.upper() for pair in ['EUR', 'GBP', 'USD', 'AUD', 'JPY'])]
            logger.info(f"Forex symbols found: {forex_symbols[:20]}")  # Log first 20
            
            return symbol_names
            
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return []
    
    def get_positions(self, symbol: str = None) -> List:
        """Get current open positions."""
        if not self.is_alive():
            logger.warning("Cannot get positions - not connected to MT5")
            return []
        
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            return list(positions)
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def place_order(self, symbol: str, order_type: str, volume: float, 
                   price: float = None, stop_loss: float = None, 
                   take_profit: float = None) -> Optional[int]:
        """Place a trading order."""
        if not self.is_alive():
            logger.warning("Cannot place order - not connected to MT5")
            return None
        
        try:
            # Ensure symbol is selected and available
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol {symbol}")
                return None
            
            # Wait a moment for symbol to load
            import time
            time.sleep(0.2)  # Longer wait for symbol initialization
            
            # Get symbol info first
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Symbol {symbol} not found")
                return None
            
            if not symbol_info.visible:
                logger.error(f"Symbol {symbol} not visible in Market Watch")
                return None
            
            # Validate minimum volume
            if volume < symbol_info.volume_min:
                logger.error(f"Volume {volume} below minimum {symbol_info.volume_min}")
                return None
            
            if volume > symbol_info.volume_max:
                logger.error(f"Volume {volume} above maximum {symbol_info.volume_max}")
                return None
            
            # Round volume to volume step
            volume_step = symbol_info.volume_step
            volume = round(volume / volume_step) * volume_step
            
            # Get current prices with retry
            tick = None
            for i in range(5):  # Try 5 times
                tick = mt5.symbol_info_tick(symbol)
                if tick is not None and tick.bid > 0 and tick.ask > 0:
                    break
                time.sleep(0.1)
            
            if tick is None or tick.bid <= 0 or tick.ask <= 0:
                logger.error(f"No valid tick data for {symbol} after retries")
                return None
            
            logger.debug(f"Symbol {symbol}: bid={tick.bid}, ask={tick.ask}, spread={tick.ask-tick.bid:.5f}")
            
            # Check if market is open
            if abs(tick.ask - tick.bid) > 0.01:  # Abnormally wide spread
                logger.warning(f"Wide spread detected for {symbol}: {tick.ask-tick.bid:.5f}")
            
            # Store the current price for logging and order
            current_price = tick.ask if order_type.lower() == "buy" else tick.bid
            
            # Prepare market order request with current price
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY if order_type.lower() == "buy" else mt5.ORDER_TYPE_SELL,
                "price": current_price,  # Add current price for market orders
                "deviation": 50,  # Increased deviation for better execution
                "magic": 234000,
                "comment": "Fibonacci Bot",
                "type_filling": mt5.ORDER_FILLING_FOK,  # Fill or Kill for market orders
                "type_time": mt5.ORDER_TIME_GTC,
            }
            
            # Add stop loss and take profit if provided
            if stop_loss and stop_loss > 0:
                request["sl"] = round(stop_loss, 5)
            if take_profit and take_profit > 0:
                request["tp"] = round(take_profit, 5)
            
            # Log the request for debugging
            logger.info(f"Attempting order: {order_type.upper()} {volume} {symbol} at {current_price}")
            logger.debug(f"Full request: {request}")
            logger.debug(f"Symbol info: min_vol={symbol_info.volume_min}, max_vol={symbol_info.volume_max}, step={symbol_info.volume_step}")
            logger.debug(f"Current tick: bid={tick.bid}, ask={tick.ask}, spread={tick.ask-tick.bid:.5f}")
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                error_msg = f"Order send failed: {mt5.last_error()}"
                logger.error(error_msg)
                return None
            
            logger.debug(f"Order result: retcode={result.retcode}, comment='{result.comment}', request_id={result.request_id}")
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                # Try with different filling policy if FOK failed
                if result.retcode == mt5.TRADE_RETCODE_INVALID_FILL:
                    logger.warning("FOK filling failed, trying IOC filling")
                    request["type_filling"] = mt5.ORDER_FILLING_IOC
                    result = mt5.order_send(request)
                    
                    if result is None:
                        logger.error(f"Order send failed (IOC): {mt5.last_error()}")
                        return None
                    
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        logger.error(f"Order failed (IOC): {result.retcode} - {result.comment}")
                        return None
                # Try without specifying price for market orders (let MT5 handle it)
                elif result.retcode == 10015:  # Invalid price
                    logger.warning("Invalid price error, trying market order without price")
                    request_no_price = request.copy()
                    del request_no_price["price"]  # Remove price for pure market order
                    result = mt5.order_send(request_no_price)
                    
                    if result is None:
                        logger.error(f"Order send failed (no price): {mt5.last_error()}")
                        return None
                    
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        logger.error(f"Order failed (no price): {result.retcode} - {result.comment}")
                        logger.error(f"Failed request details: {request_no_price}")
                        return None
                else:
                    logger.error(f"Order failed: {result.retcode} - {result.comment}")
                    logger.debug(f"Failed request: {request}")
                    # Try to get more info about the error
                    error_desc = {
                        10004: "Requote",
                        10006: "Request rejected", 
                        10007: "Request canceled",
                        10008: "Order placed",
                        10009: "Request completed",
                        10010: "Only part of the request was completed",
                        10011: "Request processing error",
                        10012: "Request canceled by timeout",
                        10013: "Invalid request",
                        10014: "Invalid volume in the request",
                        10015: "Invalid price in the request",
                        10016: "Invalid stops in the request",
                        10017: "Trade is disabled",
                        10018: "Market is closed",
                        10019: "There is not enough money to complete the request",
                        10020: "Prices changed",
                        10021: "There are no quotes to process the request",
                        10022: "Invalid order expiration date in the request",
                        10023: "Order state changed",
                        10024: "Too frequent requests",
                        10025: "No changes in request",
                        10026: "Autotrading disabled by server",
                        10027: "Autotrading disabled by client terminal",
                        10028: "Request locked for processing",
                        10029: "Order or position frozen",
                        10030: "Invalid order filling type",
                    }
                    error_msg = error_desc.get(result.retcode, "Unknown error")
                    logger.error(f"Error {result.retcode}: {error_msg}")
                    return None
            
            logger.info(f"✅ Order placed successfully: {order_type.upper()} {volume} {symbol} at {current_price}")
            return result.order
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def close_position(self, ticket: int) -> bool:
        """Close a position by ticket number."""
        if not self.is_alive():
            logger.warning("Cannot close position - not connected to MT5")
            return False
        
        try:
            # Get position info
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                logger.warning(f"Position {ticket} not found")
                return False
            
            position = positions[0]
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "deviation": 20,
                "magic": 234000,
                "comment": "Close by Fibonacci Bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            
            if result is None:
                logger.error(f"Close order failed: {mt5.last_error()}")
                return False
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Close failed: {result.retcode} - {result.comment}")
                return False
            
            logger.info(f"Position {ticket} closed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position {ticket}: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class MT5ConnectionManager:
    """Connection manager with automatic reconnection and pooling."""
    
    def __init__(self, config: Optional[MT5Config] = None, pool_size: int = 1):
        self._custom_config = config
        self._config = None
        self.pool_size = pool_size
        self.connections: List[MT5Interface] = []
        self.active_connections = 0
        self._lock = threading.RLock()
        self.auto_reconnect = True
        self.reconnect_interval = 30  # seconds
        self._monitor_thread = None
        self._stop_monitoring = False
    
    @property
    def config(self):
        """Lazy-load configuration."""
        if self._config is None:
            if self._custom_config:
                self._config = self._custom_config
            else:
                try:
                    self._config = get_config().mt5
                except RuntimeError:
                    # Fallback to default config if not loaded yet
                    logger.warning("Configuration not loaded, using default MT5 config")
                    self._config = {
                        'server': 'Demo-Server',
                        'login': 12345678,
                        'password': 'demo_password',
                        'timeout': 10000
                    }
        return self._config
    
    def initialize(self) -> bool:
        """Initialize connection pool."""
        with self._lock:
            try:
                logger.info(f"Initializing MT5 connection pool (size: {self.pool_size})")
                
                for i in range(self.pool_size):
                    interface = MT5Interface(self.config)
                    if interface.connect():
                        self.connections.append(interface)
                        self.active_connections += 1
                        logger.debug(f"Connection {i+1} established")
                    else:
                        logger.error(f"Failed to establish connection {i+1}")
                
                if self.active_connections > 0:
                    logger.info(f"Connection pool initialized with {self.active_connections} connections")
                    
                    # Start monitoring thread
                    if self.auto_reconnect:
                        self._start_monitoring()
                    
                    return True
                else:
                    logger.error("Failed to establish any connections")
                    return False
                    
            except Exception as e:
                logger.error(f"Error initializing connection pool: {e}")
                return False
    
    def get_connection(self) -> Optional[MT5Interface]:
        """Get an active connection from the pool."""
        with self._lock:
            for connection in self.connections:
                if connection.is_alive():
                    return connection
            
            logger.warning("No active connections available")
            return None
    
    def _start_monitoring(self):
        """Start connection monitoring thread."""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_monitoring = False
            self._monitor_thread = threading.Thread(target=self._monitor_connections)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
            logger.debug("Connection monitoring started")
    
    def _monitor_connections(self):
        """Monitor and reconnect failed connections."""
        while not self._stop_monitoring:
            try:
                with self._lock:
                    for i, connection in enumerate(self.connections):
                        if not connection.is_alive():
                            logger.warning(f"Connection {i+1} lost, attempting reconnection")
                            if connection.reconnect():
                                logger.info(f"Connection {i+1} restored")
                            else:
                                logger.error(f"Failed to restore connection {i+1}")
                
                time.sleep(self.reconnect_interval)
                
            except Exception as e:
                logger.error(f"Error in connection monitoring: {e}")
                time.sleep(self.reconnect_interval)
    
    def shutdown(self):
        """Shutdown connection pool."""
        with self._lock:
            logger.info("Shutting down MT5 connection pool")
            
            # Stop monitoring
            self._stop_monitoring = True
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5)
            
            # Disconnect all connections
            for i, connection in enumerate(self.connections):
                try:
                    connection.disconnect()
                    logger.debug(f"Connection {i+1} disconnected")
                except Exception as e:
                    logger.error(f"Error disconnecting connection {i+1}: {e}")
            
            self.connections.clear()
            self.active_connections = 0
            logger.info("Connection pool shutdown complete")


# Global connection manager instance (lazy initialization)
connection_manager = None

# Convenience functions
def get_connection() -> Optional[MT5Interface]:
    """Get an MT5 connection from the global pool."""
    global connection_manager
    if connection_manager is None:
        connection_manager = MT5ConnectionManager()
    return connection_manager.get_connection()

def initialize_mt5() -> bool:
    """Initialize the global MT5 connection manager."""
    global connection_manager
    if connection_manager is None:
        connection_manager = MT5ConnectionManager()
    return connection_manager.initialize()

def shutdown_mt5():
    """Shutdown the global MT5 connection manager."""
    global connection_manager
    if connection_manager is not None:
        connection_manager.shutdown()