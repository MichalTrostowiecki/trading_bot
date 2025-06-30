"""
MT5 Data Importer
Imports historical data from MetaTrader 5 for backtesting.
Uses existing MT5 connection from the trading system.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

from src.data.database import DatabaseManager
from src.monitoring import get_logger

try:
    from src.data.mt5_interface import get_connection
except ImportError:
    def get_connection():
        return None

logger = get_logger("mt5_importer")


class MT5DataImporter:
    """Imports historical data from MT5 platform."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize MT5 data importer.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.mt5_connection = None
        logger.info("MT5 importer initialized")
    
    def connect(self) -> bool:
        """
        Connect to MT5 platform.
        
        Returns:
            True if connected successfully
        """
        if not MT5_AVAILABLE:
            logger.error("MetaTrader5 module not available")
            return False
            
        try:
            # Try to use existing connection first
            self.mt5_connection = get_connection()
            if self.mt5_connection and hasattr(self.mt5_connection, 'is_connected') and self.mt5_connection.is_connected():
                logger.info("Using existing MT5 connection")
                return True
            
            # Initialize new connection
            if not mt5.initialize():
                logger.error("Failed to initialize MT5")
                return False
            
            # Get account info to verify connection
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get MT5 account info")
                mt5.shutdown()
                return False
            
            logger.info(f"Connected to MT5 account: {account_info.login}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MT5: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5 platform."""
        try:
            if hasattr(mt5, 'shutdown'):
                mt5.shutdown()
            logger.info("Disconnected from MT5")
        except Exception as e:
            logger.error(f"Error disconnecting from MT5: {e}")
    
    def get_available_symbols(self) -> List[str]:
        """
        Get list of available symbols from MT5.
        
        Returns:
            List of symbol names
        """
        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                logger.error("Failed to get symbols from MT5")
                return []
            
            symbol_names = [symbol.name for symbol in symbols if symbol.visible]
            logger.info(f"Found {len(symbol_names)} available symbols")
            return sorted(symbol_names)
            
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol information from MT5.
        
        Args:
            symbol: Symbol name
            
        Returns:
            Symbol info dictionary or None
        """
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Symbol not found: {symbol}")
                return None
            
            return {
                'name': symbol_info.name,
                'currency_base': symbol_info.currency_base,
                'currency_profit': symbol_info.currency_profit,
                'point': symbol_info.point,
                'digits': symbol_info.digits,
                'trade_mode': symbol_info.trade_mode,
                'min_lot': symbol_info.volume_min,
                'max_lot': symbol_info.volume_max,
                'lot_step': symbol_info.volume_step,
                'spread': symbol_info.spread
            }
            
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return None
    
    def download_rates(self, symbol: str, timeframe: str, 
                      start_date: datetime, end_date: datetime = None,
                      count: int = None) -> pd.DataFrame:
        """
        Download historical rates from MT5.
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
            start_date: Start date
            end_date: End date (optional)
            count: Number of bars to download (optional)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Convert timeframe to MT5 constant
            timeframe_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1,
                'W1': mt5.TIMEFRAME_W1,
                'MN1': mt5.TIMEFRAME_MN1
            }
            
            mt5_timeframe = timeframe_map.get(timeframe)
            if mt5_timeframe is None:
                logger.error(f"Unsupported timeframe: {timeframe}")
                return pd.DataFrame()
            
            # Download rates
            if count:
                # Download specific number of bars from start_date
                rates = mt5.copy_rates_from(symbol, mt5_timeframe, start_date, count)
            elif end_date:
                # Download between two dates
                rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)
            else:
                # Download from start_date to now
                rates = mt5.copy_rates_from(symbol, mt5_timeframe, start_date, 100000)  # Large number
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No rates downloaded for {symbol} {timeframe}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            
            # Convert time column to datetime
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Rename columns to match our standard format
            df.rename(columns={
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            }, inplace=True)
            
            # Keep only OHLCV columns
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"Downloaded {len(df)} rates for {symbol} {timeframe}")
            logger.info(f"Date range: {df.index[0]} to {df.index[-1]}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to download rates for {symbol} {timeframe}: {e}")
            return pd.DataFrame()
    
    def validate_data(self, df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Validate and clean downloaded data.
        
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
        df = df[~df.index.duplicated(keep='last')]
        
        # Sort by time
        df.sort_index(inplace=True)
        
        # Fill missing volume with 0
        df['volume'] = df['volume'].fillna(0)
        
        removed_count = original_count - len(df)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} invalid records from {symbol} {timeframe}")
        
        return df
    
    def import_symbol_data(self, symbol: str, timeframe: str,
                          start_date: datetime, end_date: datetime = None,
                          force_reimport: bool = False) -> bool:
        """
        Import data for a specific symbol and timeframe.
        
        Args:
            symbol: Symbol to import
            timeframe: Timeframe to import
            start_date: Start date
            end_date: End date (optional, defaults to now)
            force_reimport: Whether to reimport existing data
            
        Returns:
            True if successful
        """
        try:
            # Check if data already exists
            if not force_reimport:
                existing_data = self.db_manager.get_historical_data(
                    symbol, timeframe, start_date, end_date, limit=1
                )
                if not existing_data.empty:
                    logger.info(f"Data already exists for {symbol} {timeframe}, skipping")
                    return True
            
            # Ensure MT5 connection
            if not self.connect():
                return False
            
            # Verify symbol is available
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                logger.error(f"Symbol {symbol} not available in MT5")
                return False
            
            # Download data
            logger.info(f"Downloading {symbol} {timeframe} from {start_date}")
            df = self.download_rates(symbol, timeframe, start_date, end_date)
            
            if df.empty:
                logger.warning(f"No data downloaded for {symbol} {timeframe}")
                return False
            
            # Validate data
            df = self.validate_data(df, symbol, timeframe)
            
            if df.empty:
                logger.warning(f"No valid data after cleaning for {symbol} {timeframe}")
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
    
    def import_multiple_symbols(self, symbols: List[str], timeframes: List[str],
                               start_date: datetime, end_date: datetime = None,
                               force_reimport: bool = False) -> Dict[str, Dict[str, bool]]:
        """
        Import data for multiple symbols and timeframes.
        
        Args:
            symbols: List of symbols to import
            timeframes: List of timeframes to import
            start_date: Start date
            end_date: End date (optional)
            force_reimport: Whether to reimport existing data
            
        Returns:
            Dictionary of results {symbol: {timeframe: success}}
        """
        results = {}
        
        # Ensure MT5 connection
        if not self.connect():
            logger.error("Cannot connect to MT5")
            return results
        
        total_combinations = len(symbols) * len(timeframes)
        current = 0
        
        for symbol in symbols:
            results[symbol] = {}
            
            for timeframe in timeframes:
                current += 1
                logger.info(f"Importing {symbol} {timeframe} ({current}/{total_combinations})")
                
                success = self.import_symbol_data(
                    symbol, timeframe, start_date, end_date, force_reimport
                )
                results[symbol][timeframe] = success
        
        # Summary
        successful = sum(1 for symbol_results in results.values() 
                        for success in symbol_results.values() if success)
        
        logger.info(f"Import complete: {successful}/{total_combinations} combinations imported successfully")
        
        return results
    
    def get_latest_data_dates(self) -> Dict[str, Dict[str, datetime]]:
        """
        Get the latest available dates for all symbols/timeframes in database.
        
        Returns:
            Dictionary {symbol: {timeframe: latest_date}}
        """
        # This would query the database to find the latest dates
        # Implementation depends on database schema
        try:
            # For now, return empty dict - would need database query implementation
            return {}
        except Exception as e:
            logger.error(f"Failed to get latest data dates: {e}")
            return {}
    
    def update_to_latest(self, symbols: List[str] = None, 
                        timeframes: List[str] = None) -> Dict[str, Dict[str, bool]]:
        """
        Update data to latest available from MT5.
        
        Args:
            symbols: Optional list of symbols (defaults to all in database)
            timeframes: Optional list of timeframes (defaults to all in database)
            
        Returns:
            Dictionary of results {symbol: {timeframe: success}}
        """
        try:
            # Get current latest dates from database
            latest_dates = self.get_latest_data_dates()
            
            if not latest_dates:
                logger.warning("No existing data found in database")
                return {}
            
            results = {}
            
            for symbol, timeframe_dates in latest_dates.items():
                if symbols and symbol not in symbols:
                    continue
                    
                results[symbol] = {}
                
                for timeframe, latest_date in timeframe_dates.items():
                    if timeframes and timeframe not in timeframes:
                        continue
                    
                    # Start from day after latest date
                    start_date = latest_date + timedelta(days=1)
                    
                    logger.info(f"Updating {symbol} {timeframe} from {start_date}")
                    success = self.import_symbol_data(symbol, timeframe, start_date)
                    results[symbol][timeframe] = success
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to update to latest: {e}")
            return {}


def main():
    """CLI interface for MT5 data import."""
    import argparse
    from src.data.database import initialize_database
    
    parser = argparse.ArgumentParser(description='Import MT5 historical data')
    parser.add_argument('--symbol', help='Symbol to import')
    parser.add_argument('--timeframe', help='Timeframe to import')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--list-symbols', action='store_true', help='List available symbols')
    parser.add_argument('--force', action='store_true', help='Force reimport existing data')
    parser.add_argument('--update', action='store_true', help='Update to latest data')
    
    args = parser.parse_args()
    
    # Initialize database
    db_manager = initialize_database()
    if not db_manager:
        print("Failed to initialize database")
        return
    
    # Initialize importer
    importer = MT5DataImporter(db_manager)
    
    # Connect to MT5
    if not importer.connect():
        print("Failed to connect to MT5")
        return
    
    try:
        # List symbols if requested
        if args.list_symbols:
            symbols = importer.get_available_symbols()
            print(f"\nFound {len(symbols)} available symbols:")
            for i, symbol in enumerate(symbols, 1):
                print(f"{i:3d}. {symbol}")
                if i % 50 == 0:  # Pause every 50 symbols
                    input("Press Enter to continue...")
            return
        
        # Update to latest if requested
        if args.update:
            symbols = [args.symbol] if args.symbol else None
            timeframes = [args.timeframe] if args.timeframe else None
            results = importer.update_to_latest(symbols, timeframes)
            
            print("\nUpdate Results:")
            for symbol, timeframe_results in results.items():
                for timeframe, success in timeframe_results.items():
                    status = "SUCCESS" if success else "FAILED"
                    print(f"{symbol} {timeframe}: {status}")
            return
        
        # Parse dates
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = None
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
        elif args.symbol:
            # Import all timeframes for symbol
            timeframes = ['M1', 'M5', 'M15', 'H1', 'H4', 'D1']
            results = importer.import_multiple_symbols(
                [args.symbol], timeframes, start_date, end_date, args.force
            )
            
            print(f"\nImport Results for {args.symbol}:")
            for timeframe, success in results[args.symbol].items():
                status = "SUCCESS" if success else "FAILED"
                print(f"{timeframe}: {status}")
        else:
            print("Please specify --symbol and optionally --timeframe")
    
    finally:
        importer.disconnect()


if __name__ == "__main__":
    main()