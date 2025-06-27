"""
Historical Data Collection System
Manages collection, storage, and retrieval of historical market data.
"""

import os
import pickle
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
from src.data.mt5_interface import MT5Interface, TimeFrame, get_connection
from src.utils.config import get_config, DataConfig
from src.monitoring import get_logger

logger = get_logger("historical_data")


@dataclass
class DataRequest:
    """Data request specification."""
    symbol: str
    timeframe: TimeFrame
    start_date: datetime
    end_date: datetime
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class DataInfo:
    """Metadata about stored data."""
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    records_count: int
    file_size: int
    last_updated: datetime
    data_quality: float  # 0.0 to 1.0


class DataStorage:
    """Abstract base class for data storage backends."""
    
    def store_data(self, symbol: str, timeframe: str, data: pd.DataFrame) -> bool:
        """Store data."""
        raise NotImplementedError
    
    def load_data(self, symbol: str, timeframe: str, 
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """Load data."""
        raise NotImplementedError
    
    def get_data_info(self, symbol: str, timeframe: str) -> Optional[DataInfo]:
        """Get data information."""
        raise NotImplementedError
    
    def delete_data(self, symbol: str, timeframe: str) -> bool:
        """Delete data."""
        raise NotImplementedError


class FileStorage(DataStorage):
    """File-based data storage using Parquet format."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.base_path / "metadata.sqlite"
        self._init_metadata_db()
    
    def _init_metadata_db(self):
        """Initialize metadata database."""
        with sqlite3.connect(self.metadata_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_metadata (
                    symbol TEXT,
                    timeframe TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    records_count INTEGER,
                    file_size INTEGER,
                    last_updated TEXT,
                    data_quality REAL,
                    PRIMARY KEY (symbol, timeframe)
                )
            """)
    
    def _get_file_path(self, symbol: str, timeframe: str) -> Path:
        """Get file path for symbol and timeframe."""
        return self.base_path / f"{symbol}_{timeframe}.parquet"
    
    def store_data(self, symbol: str, timeframe: str, data: pd.DataFrame) -> bool:
        """Store data in Parquet format."""
        try:
            file_path = self._get_file_path(symbol, timeframe)
            
            # Save data
            data.to_parquet(file_path, compression='snappy')
            
            # Update metadata
            file_size = file_path.stat().st_size
            data_quality = self._calculate_data_quality(data)
            
            with sqlite3.connect(self.metadata_file) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO data_metadata 
                    (symbol, timeframe, start_date, end_date, records_count, 
                     file_size, last_updated, data_quality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, timeframe,
                    data.index.min().isoformat(),
                    data.index.max().isoformat(),
                    len(data),
                    file_size,
                    datetime.now().isoformat(),
                    data_quality
                ))
            
            logger.debug(f"Stored {len(data)} records for {symbol}_{timeframe}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing data for {symbol}_{timeframe}: {e}")
            return False
    
    def load_data(self, symbol: str, timeframe: str,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """Load data from Parquet file."""
        try:
            file_path = self._get_file_path(symbol, timeframe)
            
            if not file_path.exists():
                return None
            
            # Load data
            data = pd.read_parquet(file_path)
            
            # Filter by date range if specified
            if start_date or end_date:
                if start_date:
                    data = data[data.index >= start_date]
                if end_date:
                    data = data[data.index <= end_date]
            
            logger.debug(f"Loaded {len(data)} records for {symbol}_{timeframe}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading data for {symbol}_{timeframe}: {e}")
            return None
    
    def get_data_info(self, symbol: str, timeframe: str) -> Optional[DataInfo]:
        """Get data information from metadata."""
        try:
            with sqlite3.connect(self.metadata_file) as conn:
                cursor = conn.execute("""
                    SELECT * FROM data_metadata 
                    WHERE symbol = ? AND timeframe = ?
                """, (symbol, timeframe))
                
                row = cursor.fetchone()
                if row is None:
                    return None
                
                return DataInfo(
                    symbol=row[0],
                    timeframe=row[1],
                    start_date=datetime.fromisoformat(row[2]),
                    end_date=datetime.fromisoformat(row[3]),
                    records_count=row[4],
                    file_size=row[5],
                    last_updated=datetime.fromisoformat(row[6]),
                    data_quality=row[7]
                )
                
        except Exception as e:
            logger.error(f"Error getting data info for {symbol}_{timeframe}: {e}")
            return None
    
    def delete_data(self, symbol: str, timeframe: str) -> bool:
        """Delete data file and metadata."""
        try:
            file_path = self._get_file_path(symbol, timeframe)
            
            # Delete file if exists
            if file_path.exists():
                file_path.unlink()
            
            # Delete metadata
            with sqlite3.connect(self.metadata_file) as conn:
                conn.execute("""
                    DELETE FROM data_metadata 
                    WHERE symbol = ? AND timeframe = ?
                """, (symbol, timeframe))
            
            logger.debug(f"Deleted data for {symbol}_{timeframe}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting data for {symbol}_{timeframe}: {e}")
            return False
    
    def _calculate_data_quality(self, data: pd.DataFrame) -> float:
        """Calculate data quality score (0.0 to 1.0)."""
        if data.empty:
            return 0.0
        
        quality_score = 1.0
        
        # Check for missing values
        missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
        quality_score -= missing_ratio * 0.3
        
        # Check for duplicate timestamps
        if data.index.duplicated().any():
            duplicate_ratio = data.index.duplicated().sum() / len(data)
            quality_score -= duplicate_ratio * 0.2
        
        # Check for unrealistic price movements (gaps > 5%)
        if 'Close' in data.columns:
            returns = data['Close'].pct_change().fillna(0)
            extreme_moves = (returns.abs() > 0.05).sum()
            extreme_ratio = extreme_moves / len(data)
            quality_score -= extreme_ratio * 0.1
        
        # Check for zero volumes (if available)
        if 'Volume' in data.columns:
            zero_volume_ratio = (data['Volume'] == 0).sum() / len(data)
            quality_score -= zero_volume_ratio * 0.1
        
        return max(0.0, min(1.0, quality_score))
    
    def list_stored_data(self) -> List[DataInfo]:
        """List all stored data."""
        try:
            with sqlite3.connect(self.metadata_file) as conn:
                cursor = conn.execute("SELECT * FROM data_metadata")
                
                data_list = []
                for row in cursor.fetchall():
                    data_info = DataInfo(
                        symbol=row[0],
                        timeframe=row[1],
                        start_date=datetime.fromisoformat(row[2]),
                        end_date=datetime.fromisoformat(row[3]),
                        records_count=row[4],
                        file_size=row[5],
                        last_updated=datetime.fromisoformat(row[6]),
                        data_quality=row[7]
                    )
                    data_list.append(data_info)
                
                return data_list
                
        except Exception as e:
            logger.error(f"Error listing stored data: {e}")
            return []


class HistoricalDataCollector:
    """Historical data collection and management system."""
    
    def __init__(self, config: Optional[DataConfig] = None, storage: Optional[DataStorage] = None):
        self.config = config or get_config().data
        self.storage = storage or FileStorage(str(Path("data/historical")))
        self.mt5_interface: Optional[MT5Interface] = None
        self.max_workers = 4
        self._collection_stats = {
            'symbols_processed': 0,
            'records_collected': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def collect_all_symbols(self, timeframes: Optional[List[TimeFrame]] = None,
                           days_back: Optional[int] = None) -> Dict[str, Dict[str, bool]]:
        """Collect historical data for all configured symbols."""
        logger.info("Starting bulk historical data collection")
        
        timeframes = timeframes or [TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
        days_back = days_back or self.config.history_days
        symbols = self.config.symbols
        
        self._collection_stats['start_time'] = datetime.now()
        self._collection_stats['symbols_processed'] = 0
        self._collection_stats['records_collected'] = 0
        self._collection_stats['errors'] = 0
        
        results = {}
        
        # Create data requests
        requests = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        for symbol in symbols:
            for timeframe in timeframes:
                request = DataRequest(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                requests.append(request)
        
        # Process requests in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_request = {
                executor.submit(self._collect_symbol_data, req): req 
                for req in requests
            }
            
            for future in as_completed(future_to_request):
                request = future_to_request[future]
                try:
                    success = future.result()
                    
                    if request.symbol not in results:
                        results[request.symbol] = {}
                    
                    results[request.symbol][request.timeframe.name] = success
                    
                    if success:
                        logger.info(f"✅ {request.symbol} {request.timeframe.name}")
                    else:
                        logger.warning(f"❌ {request.symbol} {request.timeframe.name}")
                        self._collection_stats['errors'] += 1
                    
                except Exception as e:
                    logger.error(f"Error collecting {request.symbol} {request.timeframe.name}: {e}")
                    if request.symbol not in results:
                        results[request.symbol] = {}
                    results[request.symbol][request.timeframe.name] = False
                    self._collection_stats['errors'] += 1
        
        self._collection_stats['end_time'] = datetime.now()
        duration = self._collection_stats['end_time'] - self._collection_stats['start_time']
        
        logger.info(f"Data collection completed in {duration}")
        logger.info(f"Stats: {self._collection_stats}")
        
        return results
    
    def collect_symbol_data(self, symbol: str, timeframe: TimeFrame,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           force_refresh: bool = False) -> bool:
        """Collect historical data for a specific symbol and timeframe."""
        request = DataRequest(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date or datetime.now() - timedelta(days=self.config.history_days),
            end_date=end_date or datetime.now()
        )
        
        return self._collect_symbol_data(request, force_refresh)
    
    def _collect_symbol_data(self, request: DataRequest, force_refresh: bool = False) -> bool:
        """Internal method to collect data for a single request."""
        try:
            # Check if data already exists and is recent
            if not force_refresh:
                existing_info = self.storage.get_data_info(request.symbol, request.timeframe.name)
                if existing_info and self._is_data_current(existing_info, request):
                    logger.debug(f"Current data exists for {request.symbol} {request.timeframe.name}")
                    return True
            
            # Get MT5 connection
            if self.mt5_interface is None:
                self.mt5_interface = get_connection()
                if self.mt5_interface is None:
                    logger.error("No MT5 connection available")
                    return False
            
            # Calculate data chunks to avoid MT5 limits
            chunks = self._calculate_chunks(request)
            all_data = []
            
            for chunk_start, chunk_end, chunk_count in chunks:
                logger.debug(f"Collecting {request.symbol} {request.timeframe.name} "
                           f"from {chunk_start} to {chunk_end} ({chunk_count} bars)")
                
                # Get data from MT5
                data = self.mt5_interface.get_rates(
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    count=chunk_count,
                    from_date=chunk_start
                )
                
                if data is not None and not data.empty:
                    # Filter to exact date range
                    data = data[(data.index >= chunk_start) & (data.index <= chunk_end)]
                    all_data.append(data)
                else:
                    logger.warning(f"No data received for {request.symbol} {request.timeframe.name} "
                                 f"chunk {chunk_start} to {chunk_end}")
            
            if not all_data:
                logger.warning(f"No data collected for {request.symbol} {request.timeframe.name}")
                return False
            
            # Combine all chunks
            combined_data = pd.concat(all_data)
            combined_data = combined_data.sort_index().drop_duplicates()
            
            # Store data
            success = self.storage.store_data(
                request.symbol, 
                request.timeframe.name, 
                combined_data
            )
            
            if success:
                self._collection_stats['symbols_processed'] += 1
                self._collection_stats['records_collected'] += len(combined_data)
                logger.info(f"Collected {len(combined_data)} records for "
                          f"{request.symbol} {request.timeframe.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error collecting data for {request.symbol} {request.timeframe.name}: {e}")
            return False
    
    def _calculate_chunks(self, request: DataRequest) -> List[Tuple[datetime, datetime, int]]:
        """Calculate data collection chunks to avoid MT5 limits."""
        # MT5 typically limits to 100,000 bars per request
        max_bars_per_chunk = 50000  # Conservative limit
        
        # Calculate bars per day for timeframe
        bars_per_day = {
            TimeFrame.M1: 1440,
            TimeFrame.M5: 288,
            TimeFrame.M15: 96,
            TimeFrame.M30: 48,
            TimeFrame.H1: 24,
            TimeFrame.H4: 6,
            TimeFrame.D1: 1,
            TimeFrame.W1: 1/7,
            TimeFrame.MN1: 1/30
        }
        
        timeframe_bars_per_day = bars_per_day.get(request.timeframe, 24)
        total_days = (request.end_date - request.start_date).days
        estimated_bars = int(total_days * timeframe_bars_per_day)
        
        chunks = []
        
        if estimated_bars <= max_bars_per_chunk:
            # Single chunk
            chunks.append((request.start_date, request.end_date, estimated_bars))
        else:
            # Multiple chunks
            days_per_chunk = int(max_bars_per_chunk / timeframe_bars_per_day)
            current_date = request.start_date
            
            while current_date < request.end_date:
                chunk_end = min(
                    current_date + timedelta(days=days_per_chunk),
                    request.end_date
                )
                chunk_days = (chunk_end - current_date).days
                chunk_bars = int(chunk_days * timeframe_bars_per_day)
                
                chunks.append((current_date, chunk_end, chunk_bars))
                current_date = chunk_end
        
        return chunks
    
    def _is_data_current(self, data_info: DataInfo, request: DataRequest) -> bool:
        """Check if existing data is current enough."""
        # Check if data covers the requested range
        if (data_info.start_date > request.start_date or 
            data_info.end_date < request.end_date):
            return False
        
        # Check if data was updated recently (within last day)
        age = datetime.now() - data_info.last_updated
        if age > timedelta(days=1):
            return False
        
        # Check data quality
        if data_info.data_quality < 0.8:
            return False
        
        return True
    
    def update_symbol_data(self, symbol: str, timeframe: TimeFrame,
                          max_age_hours: int = 24) -> bool:
        """Update data for a symbol if it's older than max_age_hours."""
        try:
            data_info = self.storage.get_data_info(symbol, timeframe.name)
            
            if data_info is None:
                # No data exists, collect from scratch
                return self.collect_symbol_data(symbol, timeframe)
            
            # Check if update is needed
            age = datetime.now() - data_info.last_updated
            if age.total_seconds() / 3600 < max_age_hours:
                logger.debug(f"Data for {symbol} {timeframe.name} is current")
                return True
            
            # Update from last data point to now
            start_date = data_info.end_date
            end_date = datetime.now()
            
            return self.collect_symbol_data(symbol, timeframe, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error updating data for {symbol} {timeframe.name}: {e}")
            return False
    
    def get_data(self, symbol: str, timeframe: TimeFrame,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 auto_update: bool = True) -> Optional[pd.DataFrame]:
        """Get historical data with optional auto-update."""
        try:
            # Auto-update if requested
            if auto_update:
                self.update_symbol_data(symbol, timeframe)
            
            # Load data
            return self.storage.load_data(symbol, timeframe.name, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error getting data for {symbol} {timeframe.name}: {e}")
            return None
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        return self._collection_stats.copy()
    
    def list_available_data(self) -> List[DataInfo]:
        """List all available historical data."""
        return self.storage.list_stored_data()


# Global historical data collector instance
historical_collector = HistoricalDataCollector()

# Convenience functions
def collect_historical_data(symbols: Optional[List[str]] = None,
                           timeframes: Optional[List[TimeFrame]] = None,
                           days_back: Optional[int] = None) -> Dict[str, Dict[str, bool]]:
    """Collect historical data for specified symbols and timeframes."""
    if symbols:
        # Temporarily update config
        original_symbols = historical_collector.config.symbols
        historical_collector.config.symbols = symbols
        result = historical_collector.collect_all_symbols(timeframes, days_back)
        historical_collector.config.symbols = original_symbols
        return result
    else:
        return historical_collector.collect_all_symbols(timeframes, days_back)

def get_historical_data(symbol: str, timeframe: TimeFrame,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
    """Get historical data for a symbol and timeframe."""
    return historical_collector.get_data(symbol, timeframe, start_date, end_date)