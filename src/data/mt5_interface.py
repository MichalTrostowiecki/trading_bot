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
import MetaTrader5 as mt5
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
        self.config = config or get_config().mt5
        self.pool_size = pool_size
        self.connections: List[MT5Interface] = []
        self.active_connections = 0
        self._lock = threading.RLock()
        self.auto_reconnect = True
        self.reconnect_interval = 30  # seconds
        self._monitor_thread = None
        self._stop_monitoring = False
    
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


# Global connection manager instance
connection_manager = MT5ConnectionManager()

# Convenience functions
def get_connection() -> Optional[MT5Interface]:
    """Get an MT5 connection from the global pool."""
    return connection_manager.get_connection()

def initialize_mt5() -> bool:
    """Initialize the global MT5 connection manager."""
    return connection_manager.initialize()

def shutdown_mt5():
    """Shutdown the global MT5 connection manager."""
    connection_manager.shutdown()