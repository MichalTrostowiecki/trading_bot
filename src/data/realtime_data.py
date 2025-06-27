"""
Real-time Data Streaming System
Manages real-time market data feeds and tick processing.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from collections import deque
from queue import Queue, Empty
from enum import Enum
import pandas as pd
import numpy as np
from src.data.mt5_interface import MT5Interface, get_connection
from src.utils.config import get_config, DataConfig
from src.monitoring import get_logger

logger = get_logger("realtime_data")


class StreamStatus(Enum):
    """Stream status enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class Tick:
    """Single tick data point."""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume: int
    flags: int = 0
    
    @property
    def spread(self) -> float:
        """Calculate spread in points."""
        return abs(self.ask - self.bid)
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price."""
        return (self.bid + self.ask) / 2


@dataclass
class Quote:
    """Current market quote."""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    spread: float
    volume: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'bid': self.bid,
            'ask': self.ask,
            'spread': self.spread,
            'volume': self.volume
        }


@dataclass
class StreamStats:
    """Stream statistics."""
    symbol: str
    start_time: datetime
    ticks_received: int = 0
    bytes_received: int = 0
    last_tick_time: Optional[datetime] = None
    errors: int = 0
    reconnections: int = 0
    avg_latency_ms: float = 0.0
    
    def update_tick(self, tick: Tick, latency_ms: float = 0.0):
        """Update statistics with new tick."""
        self.ticks_received += 1
        self.last_tick_time = tick.timestamp
        self.bytes_received += 64  # Estimated tick size
        
        # Update average latency (exponential moving average)
        alpha = 0.1
        self.avg_latency_ms = (alpha * latency_ms + 
                              (1 - alpha) * self.avg_latency_ms)


class TickBuffer:
    """Thread-safe circular buffer for tick data."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.RLock()
        self._current_quote: Optional[Quote] = None
    
    def add_tick(self, tick: Tick):
        """Add tick to buffer."""
        with self.lock:
            self.buffer.append(tick)
            
            # Update current quote
            self._current_quote = Quote(
                symbol=tick.symbol,
                timestamp=tick.timestamp,
                bid=tick.bid,
                ask=tick.ask,
                spread=tick.spread,
                volume=tick.volume
            )
    
    def get_current_quote(self) -> Optional[Quote]:
        """Get current market quote."""
        with self.lock:
            return self._current_quote
    
    def get_recent_ticks(self, count: int = 100) -> List[Tick]:
        """Get recent ticks."""
        with self.lock:
            return list(self.buffer)[-count:]
    
    def get_ticks_since(self, since: datetime) -> List[Tick]:
        """Get ticks since a specific time."""
        with self.lock:
            return [tick for tick in self.buffer if tick.timestamp >= since]
    
    def to_dataframe(self, count: Optional[int] = None) -> pd.DataFrame:
        """Convert buffer to DataFrame."""
        with self.lock:
            ticks = list(self.buffer)[-count:] if count else list(self.buffer)
            
            if not ticks:
                return pd.DataFrame()
            
            data = {
                'symbol': [t.symbol for t in ticks],
                'timestamp': [t.timestamp for t in ticks],
                'bid': [t.bid for t in ticks],
                'ask': [t.ask for t in ticks],
                'last': [t.last for t in ticks],
                'volume': [t.volume for t in ticks],
                'spread': [t.spread for t in ticks]
            }
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
    
    def clear(self):
        """Clear buffer."""
        with self.lock:
            self.buffer.clear()
            self._current_quote = None


class DataSubscription:
    """Data subscription configuration."""
    
    def __init__(self, symbol: str, callback: Optional[Callable[[Tick], None]] = None):
        self.symbol = symbol
        self.callback = callback
        self.is_active = False
        self.stats = StreamStats(symbol=symbol, start_time=datetime.now())
        self.buffer = TickBuffer()
        
    def process_tick(self, tick: Tick):
        """Process incoming tick."""
        try:
            # Calculate latency
            latency_ms = (datetime.now() - tick.timestamp).total_seconds() * 1000
            
            # Update statistics
            self.stats.update_tick(tick, latency_ms)
            
            # Add to buffer
            self.buffer.add_tick(tick)
            
            # Call user callback
            if self.callback:
                self.callback(tick)
                
        except Exception as e:
            logger.error(f"Error processing tick for {self.symbol}: {e}")
            self.stats.errors += 1


class RealTimeDataStream:
    """Real-time data streaming manager."""
    
    def __init__(self, config: Optional[DataConfig] = None):
        self.config = config or get_config().data
        self.mt5_interface: Optional[MT5Interface] = None
        self.subscriptions: Dict[str, DataSubscription] = {}
        self.status = StreamStatus.STOPPED
        self.stream_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.tick_queue = Queue(maxsize=10000)
        self.processing_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Stream configuration
        self.tick_interval = 0.1  # seconds between MT5 polls
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5.0  # seconds
        
    def subscribe(self, symbol: str, callback: Optional[Callable[[Tick], None]] = None) -> bool:
        """Subscribe to real-time data for a symbol."""
        with self._lock:
            try:
                if symbol in self.subscriptions:
                    logger.warning(f"Already subscribed to {symbol}")
                    return True
                
                # Create subscription
                subscription = DataSubscription(symbol, callback)
                self.subscriptions[symbol] = subscription
                
                # Start streaming if not already running
                if self.status == StreamStatus.STOPPED:
                    self._start_stream()
                
                subscription.is_active = True
                logger.info(f"Subscribed to real-time data for {symbol}")
                return True
                
            except Exception as e:
                logger.error(f"Error subscribing to {symbol}: {e}")
                return False
    
    def unsubscribe(self, symbol: str) -> bool:
        """Unsubscribe from real-time data for a symbol."""
        with self._lock:
            try:
                if symbol not in self.subscriptions:
                    logger.warning(f"Not subscribed to {symbol}")
                    return True
                
                # Deactivate subscription
                self.subscriptions[symbol].is_active = False
                del self.subscriptions[symbol]
                
                logger.info(f"Unsubscribed from real-time data for {symbol}")
                
                # Stop streaming if no active subscriptions
                if not self.subscriptions and self.status == StreamStatus.RUNNING:
                    self._stop_stream()
                
                return True
                
            except Exception as e:
                logger.error(f"Error unsubscribing from {symbol}: {e}")
                return False
    
    def get_current_quote(self, symbol: str) -> Optional[Quote]:
        """Get current quote for a symbol."""
        subscription = self.subscriptions.get(symbol)
        if subscription:
            return subscription.buffer.get_current_quote()
        return None
    
    def get_recent_ticks(self, symbol: str, count: int = 100) -> List[Tick]:
        """Get recent ticks for a symbol."""
        subscription = self.subscriptions.get(symbol)
        if subscription:
            return subscription.buffer.get_recent_ticks(count)
        return []
    
    def get_tick_dataframe(self, symbol: str, count: Optional[int] = None) -> pd.DataFrame:
        """Get tick data as DataFrame."""
        subscription = self.subscriptions.get(symbol)
        if subscription:
            return subscription.buffer.to_dataframe(count)
        return pd.DataFrame()
    
    def get_stream_stats(self, symbol: str) -> Optional[StreamStats]:
        """Get stream statistics for a symbol."""
        subscription = self.subscriptions.get(symbol)
        if subscription:
            return subscription.stats
        return None
    
    def _start_stream(self):
        """Start the streaming threads."""
        try:
            self.status = StreamStatus.STARTING
            self.stop_event.clear()
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._process_ticks,
                name="TickProcessor"
            )
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            # Start streaming thread
            self.stream_thread = threading.Thread(
                target=self._stream_worker,
                name="DataStreamer"
            )
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
            self.status = StreamStatus.RUNNING
            logger.info("Real-time data stream started")
            
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            self.status = StreamStatus.ERROR
    
    def _stop_stream(self):
        """Stop the streaming threads."""
        try:
            self.status = StreamStatus.STOPPED
            self.stop_event.set()
            
            # Wait for threads to finish
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=5.0)
            
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5.0)
            
            logger.info("Real-time data stream stopped")
            
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
    
    def _stream_worker(self):
        """Main streaming worker thread."""
        reconnect_attempts = 0
        
        while not self.stop_event.is_set() and reconnect_attempts < self.max_reconnect_attempts:
            try:
                # Get MT5 connection
                if self.mt5_interface is None:
                    self.mt5_interface = get_connection()
                    if self.mt5_interface is None:
                        logger.error("No MT5 connection available")
                        time.sleep(self.reconnect_delay)
                        reconnect_attempts += 1
                        continue
                
                # Reset reconnect attempts on successful connection
                reconnect_attempts = 0
                
                # Main streaming loop
                while not self.stop_event.is_set():
                    try:
                        # Check MT5 connection
                        if not self.mt5_interface.is_alive():
                            logger.warning("MT5 connection lost, attempting reconnection")
                            if not self.mt5_interface.reconnect():
                                raise ConnectionError("Failed to reconnect to MT5")
                        
                        # Get ticks for all subscribed symbols
                        self._collect_ticks()
                        
                        # Sleep before next poll
                        time.sleep(self.tick_interval)
                        
                    except ConnectionError as e:
                        logger.error(f"Connection error: {e}")
                        self.status = StreamStatus.RECONNECTING
                        break
                    except Exception as e:
                        logger.error(f"Error in streaming loop: {e}")
                        time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Critical error in stream worker: {e}")
                reconnect_attempts += 1
                
                if reconnect_attempts < self.max_reconnect_attempts:
                    logger.info(f"Attempting reconnection {reconnect_attempts}/{self.max_reconnect_attempts}")
                    self.status = StreamStatus.RECONNECTING
                    time.sleep(self.reconnect_delay)
                else:
                    logger.error("Max reconnection attempts reached")
                    self.status = StreamStatus.ERROR
                    break
        
        self.status = StreamStatus.STOPPED
    
    def _collect_ticks(self):
        """Collect ticks from MT5 for all subscribed symbols."""
        for symbol, subscription in self.subscriptions.items():
            if not subscription.is_active:
                continue
            
            try:
                # Get recent ticks (last 100 ticks or last minute)
                since_time = datetime.now() - timedelta(minutes=1)
                tick_data = self.mt5_interface.get_ticks(symbol, count=100, from_date=since_time)
                
                if tick_data is not None and not tick_data.empty:
                    # Convert to Tick objects and queue for processing
                    for timestamp, row in tick_data.iterrows():
                        tick = Tick(
                            symbol=symbol,
                            timestamp=timestamp,
                            bid=row.get('bid', 0.0),
                            ask=row.get('ask', 0.0),
                            last=row.get('last', 0.0),
                            volume=row.get('volume', 0),
                            flags=row.get('flags', 0)
                        )
                        
                        try:
                            self.tick_queue.put_nowait((symbol, tick))
                        except:
                            # Queue full, skip this tick
                            pass
                            
            except Exception as e:
                logger.error(f"Error collecting ticks for {symbol}: {e}")
                subscription.stats.errors += 1
    
    def _process_ticks(self):
        """Process ticks from the queue."""
        while not self.stop_event.is_set():
            try:
                # Get tick from queue with timeout
                symbol, tick = self.tick_queue.get(timeout=1.0)
                
                # Process tick
                subscription = self.subscriptions.get(symbol)
                if subscription and subscription.is_active:
                    subscription.process_tick(tick)
                
                self.tick_queue.task_done()
                
            except Empty:
                # Timeout is normal, continue
                continue
            except Exception as e:
                logger.error(f"Error processing tick: {e}")
    
    def start(self) -> bool:
        """Start the real-time data stream."""
        if self.status == StreamStatus.RUNNING:
            logger.warning("Stream is already running")
            return True
        
        self._start_stream()
        return self.status == StreamStatus.RUNNING
    
    def stop(self) -> bool:
        """Stop the real-time data stream."""
        if self.status == StreamStatus.STOPPED:
            logger.warning("Stream is already stopped")
            return True
        
        self._stop_stream()
        return True
    
    def is_running(self) -> bool:
        """Check if stream is running."""
        return self.status == StreamStatus.RUNNING
    
    def get_status(self) -> StreamStatus:
        """Get current stream status."""
        return self.status
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols."""
        return list(self.subscriptions.keys())
    
    def clear_buffers(self):
        """Clear all tick buffers."""
        for subscription in self.subscriptions.values():
            subscription.buffer.clear()


class MarketDataManager:
    """High-level market data manager combining historical and real-time data."""
    
    def __init__(self, config: Optional[DataConfig] = None):
        self.config = config or get_config().data
        self.realtime_stream = RealTimeDataStream(config)
        self.symbol_callbacks: Dict[str, List[Callable]] = {}
        
    def subscribe_symbol(self, symbol: str, callback: Optional[Callable[[Tick], None]] = None) -> bool:
        """Subscribe to real-time data for a symbol."""
        # Store callback for this symbol
        if symbol not in self.symbol_callbacks:
            self.symbol_callbacks[symbol] = []
        
        if callback:
            self.symbol_callbacks[symbol].append(callback)
        
        # Create combined callback
        def combined_callback(tick: Tick):
            for cb in self.symbol_callbacks[symbol]:
                try:
                    cb(tick)
                except Exception as e:
                    logger.error(f"Error in callback for {symbol}: {e}")
        
        return self.realtime_stream.subscribe(symbol, combined_callback)
    
    def unsubscribe_symbol(self, symbol: str) -> bool:
        """Unsubscribe from real-time data for a symbol."""
        if symbol in self.symbol_callbacks:
            del self.symbol_callbacks[symbol]
        
        return self.realtime_stream.unsubscribe(symbol)
    
    def get_live_quote(self, symbol: str) -> Optional[Quote]:
        """Get current live quote for a symbol."""
        return self.realtime_stream.get_current_quote(symbol)
    
    def get_live_data(self, symbol: str, count: int = 1000) -> pd.DataFrame:
        """Get recent live tick data as DataFrame."""
        return self.realtime_stream.get_tick_dataframe(symbol, count)
    
    def start_streaming(self) -> bool:
        """Start real-time data streaming."""
        return self.realtime_stream.start()
    
    def stop_streaming(self) -> bool:
        """Stop real-time data streaming."""
        return self.realtime_stream.stop()
    
    def is_streaming(self) -> bool:
        """Check if streaming is active."""
        return self.realtime_stream.is_running()
    
    def get_stream_status(self) -> StreamStatus:
        """Get streaming status."""
        return self.realtime_stream.get_status()


# Global market data manager instance
market_data_manager = MarketDataManager()

# Convenience functions
def subscribe_to_symbol(symbol: str, callback: Optional[Callable[[Tick], None]] = None) -> bool:
    """Subscribe to real-time data for a symbol."""
    return market_data_manager.subscribe_symbol(symbol, callback)

def unsubscribe_from_symbol(symbol: str) -> bool:
    """Unsubscribe from real-time data for a symbol."""
    return market_data_manager.unsubscribe_symbol(symbol)

def get_current_quote(symbol: str) -> Optional[Quote]:
    """Get current quote for a symbol."""
    return market_data_manager.get_live_quote(symbol)

def start_market_data_stream() -> bool:
    """Start the global market data stream."""
    return market_data_manager.start_streaming()

def stop_market_data_stream() -> bool:
    """Stop the global market data stream."""
    return market_data_manager.stop_streaming()