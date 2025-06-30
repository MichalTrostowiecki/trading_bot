"""
MT4 Data Importer
Imports historical data from MetaTrader 4 history files for backtesting.
"""

import os
import struct
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np

from src.data.database import DatabaseManager
from src.monitoring import get_logger

logger = get_logger("mt4_importer")


class MT4DataImporter:
    """Imports historical data from MT4 HST files."""
    
    # MT4 HST file formats
    HST_HEADER_SIZE = 148
    HST_RECORD_SIZE = 44
    
    def __init__(self, mt4_history_path: str, db_manager: DatabaseManager):
        """
        Initialize MT4 data importer.
        
        Args:
            mt4_history_path: Path to MT4 history folder
            db_manager: Database manager instance
        """
        self.history_path = Path(mt4_history_path)
        self.db_manager = db_manager
        
        if not self.history_path.exists():
            raise ValueError(f"MT4 history path does not exist: {mt4_history_path}")
            
        logger.info(f"MT4 importer initialized with path: {mt4_history_path}")
    
    def find_hst_files(self, symbol: str = None) -> List[Tuple[str, str, Path]]:
        """
        Find all HST files in the history directory.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of (symbol, timeframe, file_path) tuples
        """
        hst_files = []
        
        # MT4 stores files in subdirectories by broker
        for broker_dir in self.history_path.iterdir():
            if not broker_dir.is_dir():
                continue
                
            for hst_file in broker_dir.glob("*.hst"):
                # Parse filename: SYMBOL_TIMEFRAME.hst (e.g., EURUSD240.hst)
                filename = hst_file.stem
                
                # Extract symbol and timeframe
                if filename.endswith(('1', '5', '15', '30', '60', '240', '1440', '10080', '43200')):
                    # Find where the timeframe starts
                    for i in range(len(filename) - 1, 0, -1):
                        if filename[i].isdigit() and filename[i-1].isalpha():
                            symbol_part = filename[:i]
                            timeframe_part = filename[i:]
                            break
                    else:
                        continue
                else:
                    continue
                
                # Convert timeframe number to standard format
                timeframe_map = {
                    '1': 'M1', '5': 'M5', '15': 'M15', '30': 'M30',
                    '60': 'H1', '240': 'H4', '1440': 'D1',
                    '10080': 'W1', '43200': 'MN1'
                }
                
                timeframe = timeframe_map.get(timeframe_part)
                if not timeframe:
                    continue
                
                # Filter by symbol if specified
                if symbol and symbol_part.upper() != symbol.upper():
                    continue
                
                hst_files.append((symbol_part.upper(), timeframe, hst_file))
                
        logger.info(f"Found {len(hst_files)} HST files")
        return hst_files
    
    def read_hst_file(self, file_path: Path) -> pd.DataFrame:
        """
        Read MT4 HST file and return DataFrame.
        
        Args:
            file_path: Path to HST file
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            with open(file_path, 'rb') as f:
                # Read header
                header = f.read(self.HST_HEADER_SIZE)
                if len(header) < self.HST_HEADER_SIZE:
                    raise ValueError("Invalid HST file: header too short")
                
                # Parse header (simplified - we mainly need the record count)
                version = struct.unpack('<I', header[0:4])[0]
                
                # Read all records
                records = []
                while True:
                    record_data = f.read(self.HST_RECORD_SIZE)
                    if len(record_data) < self.HST_RECORD_SIZE:
                        break
                    
                    # Parse record: timestamp, open, high, low, close, volume
                    timestamp, open_price, high_price, low_price, close_price, volume = struct.unpack('<Idddd2x', record_data)
                    
                    # Convert timestamp (MT4 uses seconds since 1970)
                    dt = datetime.fromtimestamp(timestamp)
                    
                    records.append({
                        'timestamp': dt,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'volume': volume
                    })
                
                if not records:
                    logger.warning(f"No records found in {file_path}")
                    return pd.DataFrame()
                
                # Create DataFrame
                df = pd.DataFrame(records)
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                
                logger.info(f"Read {len(df)} records from {file_path}")
                return df
                
        except Exception as e:
            logger.error(f"Failed to read HST file {file_path}: {e}")
            return pd.DataFrame()
    
    def validate_data(self, df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Validate and clean imported data.
        
        Args:
            df: Raw data DataFrame
            symbol: Symbol name
            timeframe: Timeframe
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
            
        original_count = len(df)
        
        # Remove invalid OHLC data
        df = df[
            (df['open'] > 0) & 
            (df['high'] > 0) & 
            (df['low'] > 0) & 
            (df['close'] > 0) &
            (df['high'] >= df['low']) &
            (df['high'] >= df['open']) &
            (df['high'] >= df['close']) &
            (df['low'] <= df['open']) &
            (df['low'] <= df['close'])
        ]
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Remove extreme outliers (prices that differ by more than 50% from previous)
        for col in ['open', 'high', 'low', 'close']:
            df[f'{col}_pct_change'] = df[col].pct_change().abs()
            df = df[df[f'{col}_pct_change'] <= 0.5]  # 50% max change
            df.drop(f'{col}_pct_change', axis=1, inplace=True)
        
        # Fill missing volume with 0
        df['volume'] = df['volume'].fillna(0)
        
        # Check for data gaps
        expected_intervals = {
            'M1': timedelta(minutes=1),
            'M5': timedelta(minutes=5),
            'M15': timedelta(minutes=15),
            'M30': timedelta(minutes=30),
            'H1': timedelta(hours=1),
            'H4': timedelta(hours=4),
            'D1': timedelta(days=1)
        }
        
        if timeframe in expected_intervals:
            interval = expected_intervals[timeframe]
            gaps = []
            
            for i in range(1, len(df)):
                time_diff = df.index[i] - df.index[i-1]
                if time_diff > interval * 2:  # Gap larger than 2 intervals
                    gaps.append((df.index[i-1], df.index[i], time_diff))
            
            if gaps:
                logger.warning(f"Found {len(gaps)} data gaps in {symbol} {timeframe}")
                for start, end, duration in gaps[:5]:  # Log first 5 gaps
                    logger.warning(f"Gap from {start} to {end} ({duration})")
        
        removed_count = original_count - len(df)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} invalid records from {symbol} {timeframe}")
        
        return df
    
    def import_symbol_data(self, symbol: str, timeframe: str, 
                          start_date: datetime = None, end_date: datetime = None,
                          force_reimport: bool = False) -> bool:
        """
        Import data for a specific symbol and timeframe.
        
        Args:
            symbol: Symbol to import
            timeframe: Timeframe to import
            start_date: Optional start date filter
            end_date: Optional end date filter
            force_reimport: Whether to reimport existing data
            
        Returns:
            True if successful
        """
        try:
            # Find HST file for this symbol/timeframe
            hst_files = self.find_hst_files(symbol)
            target_file = None
            
            for sym, tf, file_path in hst_files:
                if sym == symbol.upper() and tf == timeframe:
                    target_file = file_path
                    break
            
            if not target_file:
                logger.error(f"No HST file found for {symbol} {timeframe}")
                return False
            
            # Check if data already exists
            if not force_reimport:
                existing_data = self.db_manager.get_historical_data(
                    symbol, timeframe, limit=1
                )
                if not existing_data.empty:
                    logger.info(f"Data already exists for {symbol} {timeframe}, skipping")
                    return True
            
            # Read and validate data
            logger.info(f"Reading HST file: {target_file}")
            df = self.read_hst_file(target_file)
            
            if df.empty:
                logger.warning(f"No data read from {target_file}")
                return False
            
            # Validate data
            df = self.validate_data(df, symbol, timeframe)
            
            if df.empty:
                logger.warning(f"No valid data after cleaning for {symbol} {timeframe}")
                return False
            
            # Apply date filters
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            
            if df.empty:
                logger.warning(f"No data in specified date range for {symbol} {timeframe}")
                return False
            
            # Store in database
            logger.info(f"Storing {len(df)} records for {symbol} {timeframe}")
            success = self.db_manager.store_historical_data(symbol, timeframe, df)
            
            if success:
                logger.info(f"Successfully imported {symbol} {timeframe}: {len(df)} records")
                logger.info(f"Date range: {df.index[0]} to {df.index[-1]}")
            else:
                logger.error(f"Failed to store data for {symbol} {timeframe}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to import {symbol} {timeframe}: {e}")
            return False
    
    def import_all_available_data(self, symbols: List[str] = None, 
                                 timeframes: List[str] = None,
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Dict[str, bool]]:
        """
        Import all available data from MT4 history.
        
        Args:
            symbols: Optional list of symbols to import
            timeframes: Optional list of timeframes to import
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary of results {symbol: {timeframe: success}}
        """
        results = {}
        
        # Get all available HST files
        hst_files = self.find_hst_files()
        
        if not hst_files:
            logger.warning("No HST files found")
            return results
        
        # Filter by symbols and timeframes if specified
        if symbols:
            symbols = [s.upper() for s in symbols]
            hst_files = [(s, tf, path) for s, tf, path in hst_files if s in symbols]
        
        if timeframes:
            hst_files = [(s, tf, path) for s, tf, path in hst_files if tf in timeframes]
        
        logger.info(f"Importing {len(hst_files)} files")
        
        for symbol, timeframe, file_path in hst_files:
            if symbol not in results:
                results[symbol] = {}
            
            logger.info(f"Importing {symbol} {timeframe}...")
            success = self.import_symbol_data(
                symbol, timeframe, start_date, end_date
            )
            results[symbol][timeframe] = success
        
        # Summary
        total_files = len(hst_files)
        successful = sum(1 for symbol_results in results.values() 
                        for success in symbol_results.values() if success)
        
        logger.info(f"Import complete: {successful}/{total_files} files imported successfully")
        
        return results
    
    def get_available_data_info(self) -> List[Dict[str, any]]:
        """
        Get information about available data files.
        
        Returns:
            List of data file information
        """
        info = []
        hst_files = self.find_hst_files()
        
        for symbol, timeframe, file_path in hst_files:
            # Get file size and modification time
            stat = file_path.stat()
            
            # Estimate record count
            estimated_records = max(0, (stat.st_size - self.HST_HEADER_SIZE) // self.HST_RECORD_SIZE)
            
            info.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'file_path': str(file_path),
                'file_size_mb': round(stat.st_size / 1024 / 1024, 2),
                'modified_date': datetime.fromtimestamp(stat.st_mtime),
                'estimated_records': estimated_records
            })
        
        return sorted(info, key=lambda x: (x['symbol'], x['timeframe']))


def main():
    """CLI interface for MT4 data import."""
    import argparse
    from src.data.database import initialize_database
    
    parser = argparse.ArgumentParser(description='Import MT4 historical data')
    parser.add_argument('--mt4-path', required=True, help='Path to MT4 history folder')
    parser.add_argument('--symbol', help='Symbol to import (optional)')
    parser.add_argument('--timeframe', help='Timeframe to import (optional)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--list-files', action='store_true', help='List available files')
    parser.add_argument('--force', action='store_true', help='Force reimport existing data')
    
    args = parser.parse_args()
    
    # Initialize database
    db_manager = initialize_database()
    if not db_manager:
        print("Failed to initialize database")
        return
    
    # Initialize importer
    try:
        importer = MT4DataImporter(args.mt4_path, db_manager)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # List files if requested
    if args.list_files:
        info = importer.get_available_data_info()
        print(f"\nFound {len(info)} HST files:")
        print(f"{'Symbol':<10} {'TF':<4} {'Records':<10} {'Size (MB)':<10} {'Modified'}")
        print("-" * 60)
        for item in info:
            print(f"{item['symbol']:<10} {item['timeframe']:<4} {item['estimated_records']:<10} "
                  f"{item['file_size_mb']:<10} {item['modified_date'].strftime('%Y-%m-%d')}")
        return
    
    # Parse dates
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    # Import data
    if args.symbol and args.timeframe:
        # Import specific symbol/timeframe
        success = importer.import_symbol_data(
            args.symbol, args.timeframe, start_date, end_date, args.force
        )
        if success:
            print(f"Successfully imported {args.symbol} {args.timeframe}")
        else:
            print(f"Failed to import {args.symbol} {args.timeframe}")
    else:
        # Import all available data
        symbols = [args.symbol] if args.symbol else None
        timeframes = [args.timeframe] if args.timeframe else None
        
        results = importer.import_all_available_data(
            symbols, timeframes, start_date, end_date
        )
        
        print("\nImport Results:")
        for symbol, timeframe_results in results.items():
            for timeframe, success in timeframe_results.items():
                status = "SUCCESS" if success else "FAILED"
                print(f"{symbol} {timeframe}: {status}")


if __name__ == "__main__":
    main()