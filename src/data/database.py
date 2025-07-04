"""
Database System
SQLAlchemy models and database management for trading bot data storage.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func, and_, or_
import uuid
import json
import pandas as pd

from src.utils.config import get_config
from src.monitoring import get_logger

logger = get_logger("database")

# Database base class
Base = declarative_base()


class HistoricalData(Base):
    """Table for storing historical price data."""
    __tablename__ = "historical_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite index for efficient queries
    __table_args__ = (
        {'comment': 'Historical market data storage'},
    )


class Trade(Base):
    """Table for storing trade records."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket = Column(String(20), unique=True, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    trade_type = Column(String(10), nullable=False)  # 'buy' or 'sell'
    volume = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    profit = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)
    
    # Timing
    open_time = Column(DateTime, nullable=False, index=True)
    close_time = Column(DateTime, nullable=True, index=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Strategy information
    strategy_name = Column(String(50), default="Fibonacci")
    signal_type = Column(String(20), nullable=True)  # Entry signal type
    fibonacci_level = Column(Float, nullable=True)
    fractal_period = Column(Integer, nullable=True)
    swing_direction = Column(String(10), nullable=True)  # 'up' or 'down'
    
    # Market context
    market_regime = Column(String(20), nullable=True)  # 'trending', 'ranging', etc.
    volatility_level = Column(String(10), nullable=True)  # 'low', 'medium', 'high'
    session = Column(String(20), nullable=True)  # 'london', 'new_york', 'asian'
    
    # AI enhancement data
    ai_confidence = Column(Float, nullable=True)
    pattern_recognition_score = Column(Float, nullable=True)
    
    # Status
    status = Column(String(20), default="open", index=True)  # 'open', 'closed', 'cancelled'
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradingSession(Base):
    """Table for storing daily trading session data."""
    __tablename__ = "trading_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    
    # Session metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_profit = Column(Float, default=0.0)
    max_profit = Column(Float, default=0.0)
    max_loss = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    
    # Risk metrics
    risk_taken = Column(Float, default=0.0)
    max_positions = Column(Integer, default=0)
    avg_hold_time_minutes = Column(Float, default=0.0)
    
    # Strategy performance
    fibonacci_trades = Column(Integer, default=0)
    fibonacci_wins = Column(Integer, default=0)
    avg_fibonacci_level = Column(Float, nullable=True)
    
    # AI performance
    ai_trades = Column(Integer, default=0)
    ai_wins = Column(Integer, default=0)
    avg_ai_confidence = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StrategyPerformance(Base):
    """Table for storing strategy performance metrics."""
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(50), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False)
    
    # Time period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    total_profit = Column(Float, default=0.0)
    avg_profit_per_trade = Column(Float, default=0.0)
    best_trade = Column(Float, default=0.0)
    worst_trade = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    
    # Strategy-specific metrics
    parameters = Column(Text, nullable=True)  # JSON string of parameters
    fibonacci_effectiveness = Column(Float, nullable=True)
    fractal_accuracy = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    """Table for storing system logs and events."""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(10), nullable=False, index=True)  # INFO, WARNING, ERROR, DEBUG
    component = Column(String(50), nullable=False, index=True)  # trading_engine, mt5_interface, etc.
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON string for additional details
    
    # Context information
    symbol = Column(String(10), nullable=True, index=True)
    trade_ticket = Column(String(20), nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class BacktestRun(Base):
    """Table for storing backtest run metadata."""
    __tablename__ = "backtest_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    strategy_name = Column(String(50), nullable=False, index=True)
    strategy_version = Column(String(20), nullable=False)
    parameters = Column(Text, nullable=True)  # JSON string
    
    # Data range
    date_range_start = Column(DateTime, nullable=False, index=True)
    date_range_end = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False, index=True)
    
    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    profit_factor = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, default=0.0)
    
    # Execution info
    execution_time_seconds = Column(Float, nullable=True)
    data_points_processed = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MarketFractal(Base):
    """Table for storing detected fractals."""
    __tablename__ = "market_fractals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(10), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Fractal properties
    fractal_type = Column(String(10), nullable=False, index=True)  # 'high' or 'low'
    price = Column(Float, nullable=False)
    strength = Column(Integer, default=2)  # Number of validation bars on each side
    validation_bars = Column(Integer, default=5)  # Total bars used for validation
    
    # Validation status
    is_valid = Column(Boolean, default=True, index=True)
    invalidation_reason = Column(String(100), nullable=True)
    
    # Context information
    bar_index = Column(Integer, nullable=True)  # Position in dataset
    surrounding_bars = Column(Text, nullable=True)  # JSON of surrounding OHLC data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite index for efficient queries
    __table_args__ = (
        {'comment': 'Market fractals for swing analysis'},
    )


class MarketSwing(Base):
    """Table for storing identified market swings."""
    __tablename__ = "market_swings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(10), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False, index=True)
    
    # Swing timing
    start_timestamp = Column(DateTime, nullable=False, index=True)
    end_timestamp = Column(DateTime, nullable=False, index=True)
    duration_bars = Column(Integer, nullable=False)
    
    # Swing properties
    start_price = Column(Float, nullable=False)
    end_price = Column(Float, nullable=False)
    direction = Column(String(10), nullable=False, index=True)  # 'up' or 'down'
    magnitude_pips = Column(Float, nullable=False)
    magnitude_percent = Column(Float, nullable=False)
    
    # Fibonacci levels (JSON array of level objects)
    fibonacci_levels = Column(Text, nullable=True)  # JSON: [{"level": 23.6, "price": 1.0920}, ...]
    
    # Swing relationships
    fractal_start_id = Column(String, ForeignKey('market_fractals.id'), nullable=True)
    fractal_end_id = Column(String, ForeignKey('market_fractals.id'), nullable=True)
    parent_swing_id = Column(String, ForeignKey('market_swings.id'), nullable=True)
    
    # Analysis metrics
    swing_angle = Column(Float, nullable=True)  # Angle in degrees
    volatility = Column(Float, nullable=True)  # ATR during swing
    volume_profile = Column(Text, nullable=True)  # JSON of volume data
    
    # Validation
    is_dominant = Column(Boolean, default=False, index=True)
    confidence_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fractal_start = relationship("MarketFractal", foreign_keys=[fractal_start_id])
    fractal_end = relationship("MarketFractal", foreign_keys=[fractal_end_id])


class BacktestSignal(Base):
    """Table for storing signals generated during backtesting."""
    __tablename__ = "backtest_signals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    backtest_run_id = Column(String, ForeignKey('backtest_runs.id'), nullable=False, index=True)
    
    # Signal timing and properties
    timestamp = Column(DateTime, nullable=False, index=True)
    signal_type = Column(String(10), nullable=False, index=True)  # 'entry', 'exit', 'stop', 'target'
    direction = Column(String(10), nullable=False, index=True)  # 'buy', 'sell'
    price = Column(Float, nullable=False)
    
    # Fibonacci context
    fibonacci_level = Column(Float, nullable=True)  # Which Fib level triggered
    fibonacci_price = Column(Float, nullable=True)  # Exact Fib level price
    swing_id = Column(String, ForeignKey('market_swings.id'), nullable=True, index=True)
    
    # ML/AI features
    confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    feature_vector = Column(Text, nullable=True)  # JSON of features at signal time
    
    # Risk management
    stop_loss_price = Column(Float, nullable=True)
    take_profit_price = Column(Float, nullable=True)
    position_size = Column(Float, nullable=True)
    risk_reward_ratio = Column(Float, nullable=True)
    
    # Execution tracking
    executed = Column(Boolean, default=False, index=True)
    execution_price = Column(Float, nullable=True)
    slippage = Column(Float, nullable=True)
    
    # Outcome tracking
    outcome = Column(String(20), nullable=True, index=True)  # 'win', 'loss', 'breakeven', 'cancelled'
    profit_loss_pips = Column(Float, nullable=True)
    profit_loss_percent = Column(Float, nullable=True)
    hold_time_bars = Column(Integer, nullable=True)
    max_adverse_excursion = Column(Float, nullable=True)
    max_favorable_excursion = Column(Float, nullable=True)
    
    # Context information
    market_regime = Column(String(20), nullable=True)  # 'trending', 'ranging', 'volatile'
    session = Column(String(20), nullable=True)  # 'london', 'new_york', 'asian'
    news_impact = Column(String(10), nullable=True)  # 'low', 'medium', 'high'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    backtest_run = relationship("BacktestRun")
    swing = relationship("MarketSwing")


class MarketContext(Base):
    """Table for storing market context information."""
    __tablename__ = "market_context"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(5), nullable=False, index=True)
    
    # Market regime classification
    market_regime = Column(String(20), nullable=False, index=True)  # 'trending', 'ranging', 'volatile'
    trend_strength = Column(Float, nullable=True)  # ADX or similar
    trend_direction = Column(String(10), nullable=True)  # 'up', 'down', 'sideways'
    
    # Volatility metrics
    volatility_level = Column(Float, nullable=False)  # ATR normalized
    volatility_classification = Column(String(10), nullable=True)  # 'low', 'medium', 'high'
    
    # Session information
    session = Column(String(20), nullable=False, index=True)  # 'london', 'new_york', 'asian', 'overlap'
    session_volume = Column(Float, nullable=True)
    
    # Economic context
    major_news = Column(Boolean, default=False, index=True)
    news_impact = Column(String(10), nullable=True)  # 'low', 'medium', 'high'
    economic_events = Column(Text, nullable=True)  # JSON array of events
    
    # Technical context
    support_levels = Column(Text, nullable=True)  # JSON array of support prices
    resistance_levels = Column(Text, nullable=True)  # JSON array of resistance prices
    key_fibonacci_levels = Column(Text, nullable=True)  # JSON array of important Fib levels
    
    # Sentiment and correlation
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    correlation_usd_strength = Column(Float, nullable=True)
    correlation_risk_assets = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Database manager for trading bot data operations."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.SessionLocal = None
        
        logger.info("Database manager initialized")
    
    def _get_database_url(self) -> str:
        """Get database URL from configuration."""
        try:
            config = get_config()
            return config.database.url
        except Exception as e:
            logger.warning(f"Could not load database URL from config: {e}")
            return "sqlite:///data/trading_bot.db"
    
    def _get_database_echo(self) -> bool:
        """Get database echo setting from configuration."""
        try:
            config = get_config()
            return config.database.echo
        except Exception as e:
            logger.warning(f"Could not load database echo setting from config: {e}")
            return False
    
    def connect(self) -> bool:
        """Connect to the database."""
        try:
            self.engine = create_engine(
                self.database_url,
                echo=self._get_database_echo(),
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info("Database connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def get_session(self) -> Session:
        """Get a database session."""
        if not self.SessionLocal:
            raise Exception("Database not connected")
        return self.SessionLocal()
    
    def disconnect(self):
        """Disconnect from the database."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database disconnected")
    
    # Historical Data Operations
    def store_historical_data(self, symbol: str, timeframe: str, data: pd.DataFrame) -> bool:
        """Store historical market data."""
        try:
            with self.get_session() as session:
                records = []
                for index, row in data.iterrows():
                    record = HistoricalData(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=index,
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row.get('volume', 0)
                    )
                    records.append(record)
                
                # Use bulk insert for better performance
                session.bulk_save_objects(records)
                session.commit()
                
                logger.info(f"Stored {len(records)} historical data records for {symbol} {timeframe}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store historical data: {e}")
            return False
    
    def get_historical_data(self, symbol: str, timeframe: str, 
                          start_date: datetime = None, end_date: datetime = None,
                          limit: int = None) -> pd.DataFrame:
        """Retrieve historical market data."""
        try:
            with self.get_session() as session:
                query = session.query(HistoricalData).filter(
                    HistoricalData.symbol == symbol,
                    HistoricalData.timeframe == timeframe
                )
                
                if start_date:
                    query = query.filter(HistoricalData.timestamp >= start_date)
                if end_date:
                    query = query.filter(HistoricalData.timestamp <= end_date)
                
                query = query.order_by(HistoricalData.timestamp)
                
                if limit:
                    query = query.limit(limit)
                
                results = query.all()
                
                if not results:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                data = {
                    'open': [r.open for r in results],
                    'high': [r.high for r in results],
                    'low': [r.low for r in results],
                    'close': [r.close for r in results],
                    'volume': [r.volume for r in results]
                }
                
                df = pd.DataFrame(data, index=[r.timestamp for r in results])
                return df
                
        except Exception as e:
            logger.error(f"Failed to retrieve historical data: {e}")
            return pd.DataFrame()
    
    # Trade Operations
    def store_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Store a trade record."""
        try:
            with self.get_session() as session:
                trade = Trade(**trade_data)
                session.add(trade)
                session.commit()
                
                logger.info(f"Stored trade record: {trade_data.get('ticket', 'unknown')}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store trade: {e}")
            return False
    
    def update_trade(self, ticket: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing trade record."""
        try:
            with self.get_session() as session:
                trade = session.query(Trade).filter(Trade.ticket == ticket).first()
                if not trade:
                    logger.warning(f"Trade not found for ticket: {ticket}")
                    return False
                
                for key, value in update_data.items():
                    if hasattr(trade, key):
                        setattr(trade, key, value)
                
                trade.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info(f"Updated trade record: {ticket}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update trade: {e}")
            return False
    
    def get_trades(self, symbol: str = None, start_date: datetime = None, 
                   end_date: datetime = None, status: str = None) -> List[Trade]:
        """Retrieve trade records."""
        try:
            with self.get_session() as session:
                query = session.query(Trade)
                
                if symbol:
                    query = query.filter(Trade.symbol == symbol)
                if start_date:
                    query = query.filter(Trade.open_time >= start_date)
                if end_date:
                    query = query.filter(Trade.open_time <= end_date)
                if status:
                    query = query.filter(Trade.status == status)
                
                query = query.order_by(Trade.open_time.desc())
                
                return query.all()
                
        except Exception as e:
            logger.error(f"Failed to retrieve trades: {e}")
            return []
    
    # Performance Analytics
    def calculate_daily_performance(self, date: datetime, symbol: str = None) -> Dict[str, Any]:
        """Calculate daily performance metrics."""
        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            with self.get_session() as session:
                query = session.query(Trade).filter(
                    Trade.open_time >= start_of_day,
                    Trade.open_time < end_of_day
                )
                
                if symbol:
                    query = query.filter(Trade.symbol == symbol)
                
                trades = query.all()
                
                if not trades:
                    return {}
                
                # Calculate metrics
                total_trades = len(trades)
                winning_trades = len([t for t in trades if t.profit > 0])
                losing_trades = len([t for t in trades if t.profit < 0])
                total_profit = sum(t.profit for t in trades)
                
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                avg_profit = total_profit / total_trades if total_trades > 0 else 0
                
                best_trade = max((t.profit for t in trades), default=0)
                worst_trade = min((t.profit for t in trades), default=0)
                
                return {
                    'date': date.date(),
                    'symbol': symbol,
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': win_rate,
                    'total_profit': total_profit,
                    'avg_profit': avg_profit,
                    'best_trade': best_trade,
                    'worst_trade': worst_trade
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate daily performance: {e}")
            return {}
    
    def get_performance_summary(self, days: int = 30, symbol: str = None) -> Dict[str, Any]:
        """Get performance summary for the last N days."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            trades = self.get_trades(symbol=symbol, start_date=start_date, end_date=end_date)
            
            if not trades:
                return {}
            
            # Calculate comprehensive metrics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.profit > 0])
            losing_trades = len([t for t in trades if t.profit < 0])
            
            total_profit = sum(t.profit for t in trades)
            profits = [t.profit for t in trades if t.profit > 0]
            losses = [t.profit for t in trades if t.profit < 0]
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            avg_profit = total_profit / total_trades if total_trades > 0 else 0
            
            avg_win = sum(profits) / len(profits) if profits else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            
            profit_factor = (sum(profits) / abs(sum(losses))) if losses else float('inf') if profits else 0
            
            # Calculate maximum drawdown
            running_profit = 0
            peak = 0
            max_drawdown = 0
            
            for trade in sorted(trades, key=lambda x: x.open_time):
                running_profit += trade.profit
                if running_profit > peak:
                    peak = running_profit
                drawdown = peak - running_profit
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return {
                'period_days': days,
                'symbol': symbol,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'avg_profit': avg_profit,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'max_drawdown': max_drawdown,
                'best_trade': max((t.profit for t in trades), default=0),
                'worst_trade': min((t.profit for t in trades), default=0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}
    
    def log_system_event(self, level: str, component: str, message: str, 
                        details: Dict[str, Any] = None, symbol: str = None,
                        trade_ticket: str = None) -> bool:
        """Log a system event."""
        try:
            with self.get_session() as session:
                log_entry = SystemLog(
                    level=level,
                    component=component,
                    message=message,
                    details=json.dumps(details) if details else None,
                    symbol=symbol,
                    trade_ticket=trade_ticket
                )
                
                session.add(log_entry)
                session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")
            return False
    
    # Backtesting Operations
    def store_backtest_run(self, run_data: Dict[str, Any]) -> str:
        """Store a backtest run and return its ID."""
        try:
            with self.get_session() as session:
                backtest_run = BacktestRun(**run_data)
                session.add(backtest_run)
                session.commit()
                
                logger.info(f"Stored backtest run: {backtest_run.id}")
                return backtest_run.id
                
        except Exception as e:
            logger.error(f"Failed to store backtest run: {e}")
            return None
    
    def update_backtest_run(self, run_id: str, update_data: Dict[str, Any]) -> bool:
        """Update backtest run with results."""
        try:
            with self.get_session() as session:
                run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
                if not run:
                    logger.warning(f"Backtest run not found: {run_id}")
                    return False
                
                for key, value in update_data.items():
                    if hasattr(run, key):
                        setattr(run, key, value)
                
                run.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info(f"Updated backtest run: {run_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update backtest run: {e}")
            return False
    
    # Fractal Operations
    def store_fractal(self, fractal_data: Dict[str, Any]) -> str:
        """Store a market fractal and return its ID."""
        try:
            with self.get_session() as session:
                fractal = MarketFractal(**fractal_data)
                session.add(fractal)
                session.commit()
                
                return fractal.id
                
        except Exception as e:
            logger.error(f"Failed to store fractal: {e}")
            return None
    
    def store_fractals_batch(self, fractals_data: List[Dict[str, Any]]) -> bool:
        """Store multiple fractals in a batch."""
        try:
            with self.get_session() as session:
                fractals = [MarketFractal(**data) for data in fractals_data]
                session.bulk_save_objects(fractals)
                session.commit()
                
                logger.info(f"Stored {len(fractals)} fractals in batch")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store fractals batch: {e}")
            return False
    
    def get_fractals(self, symbol: str, timeframe: str, 
                    start_date: datetime = None, end_date: datetime = None) -> List[MarketFractal]:
        """Retrieve fractals for analysis."""
        try:
            with self.get_session() as session:
                query = session.query(MarketFractal).filter(
                    MarketFractal.symbol == symbol,
                    MarketFractal.timeframe == timeframe,
                    MarketFractal.is_valid == True
                )
                
                if start_date:
                    query = query.filter(MarketFractal.timestamp >= start_date)
                if end_date:
                    query = query.filter(MarketFractal.timestamp <= end_date)
                
                return query.order_by(MarketFractal.timestamp).all()
                
        except Exception as e:
            logger.error(f"Failed to retrieve fractals: {e}")
            return []
    
    # Swing Operations
    def store_swing(self, swing_data: Dict[str, Any]) -> str:
        """Store a market swing and return its ID."""
        try:
            with self.get_session() as session:
                swing = MarketSwing(**swing_data)
                session.add(swing)
                session.commit()
                
                return swing.id
                
        except Exception as e:
            logger.error(f"Failed to store swing: {e}")
            return None
    
    def get_swings(self, symbol: str, timeframe: str, 
                  start_date: datetime = None, end_date: datetime = None,
                  dominant_only: bool = False) -> List[MarketSwing]:
        """Retrieve swings for analysis."""
        try:
            with self.get_session() as session:
                query = session.query(MarketSwing).filter(
                    MarketSwing.symbol == symbol,
                    MarketSwing.timeframe == timeframe
                )
                
                if dominant_only:
                    query = query.filter(MarketSwing.is_dominant == True)
                
                if start_date:
                    query = query.filter(MarketSwing.start_timestamp >= start_date)
                if end_date:
                    query = query.filter(MarketSwing.end_timestamp <= end_date)
                
                return query.order_by(MarketSwing.start_timestamp).all()
                
        except Exception as e:
            logger.error(f"Failed to retrieve swings: {e}")
            return []
    
    # Signal Operations
    def store_signal(self, signal_data: Dict[str, Any]) -> str:
        """Store a backtest signal and return its ID."""
        try:
            with self.get_session() as session:
                signal = BacktestSignal(**signal_data)
                session.add(signal)
                session.commit()
                
                return signal.id
                
        except Exception as e:
            logger.error(f"Failed to store signal: {e}")
            return None
    
    def store_signals_batch(self, signals_data: List[Dict[str, Any]]) -> bool:
        """Store multiple signals in a batch."""
        try:
            with self.get_session() as session:
                signals = [BacktestSignal(**data) for data in signals_data]
                session.bulk_save_objects(signals)
                session.commit()
                
                logger.info(f"Stored {len(signals)} signals in batch")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store signals batch: {e}")
            return False
    
    def get_signals(self, backtest_run_id: str = None, symbol: str = None,
                   start_date: datetime = None, end_date: datetime = None) -> List[BacktestSignal]:
        """Retrieve signals for analysis."""
        try:
            with self.get_session() as session:
                query = session.query(BacktestSignal)
                
                if backtest_run_id:
                    query = query.filter(BacktestSignal.backtest_run_id == backtest_run_id)
                
                if symbol:
                    # Join with backtest run to filter by symbol
                    query = query.join(BacktestRun).filter(BacktestRun.symbol == symbol)
                
                if start_date:
                    query = query.filter(BacktestSignal.timestamp >= start_date)
                if end_date:
                    query = query.filter(BacktestSignal.timestamp <= end_date)
                
                return query.order_by(BacktestSignal.timestamp).all()
                
        except Exception as e:
            logger.error(f"Failed to retrieve signals: {e}")
            return []
    
    # Market Context Operations
    def store_market_context(self, context_data: Dict[str, Any]) -> str:
        """Store market context and return its ID."""
        try:
            with self.get_session() as session:
                context = MarketContext(**context_data)
                session.add(context)
                session.commit()
                
                return context.id
                
        except Exception as e:
            logger.error(f"Failed to store market context: {e}")
            return None
    
    def get_market_context(self, symbol: str, timestamp: datetime, 
                          timeframe: str = "H1") -> Optional[MarketContext]:
        """Get market context for a specific timestamp."""
        try:
            with self.get_session() as session:
                return session.query(MarketContext).filter(
                    MarketContext.symbol == symbol,
                    MarketContext.timeframe == timeframe,
                    MarketContext.timestamp == timestamp
                ).first()
                
        except Exception as e:
            logger.error(f"Failed to retrieve market context: {e}")
            return None
    
    # Analysis Operations
    def get_backtest_runs(self, symbol: str = None, strategy_name: str = None,
                         limit: int = 50) -> List[BacktestRun]:
        """Get list of backtest runs."""
        try:
            with self.get_session() as session:
                query = session.query(BacktestRun)
                
                if symbol:
                    query = query.filter(BacktestRun.symbol == symbol)
                if strategy_name:
                    query = query.filter(BacktestRun.strategy_name == strategy_name)
                
                return query.order_by(BacktestRun.run_date.desc()).limit(limit).all()
                
        except Exception as e:
            logger.error(f"Failed to retrieve backtest runs: {e}")
            return []
    
    def get_fibonacci_level_performance(self, symbol: str, timeframe: str,
                                      fibonacci_level: float) -> Dict[str, Any]:
        """Analyze performance of specific Fibonacci level."""
        try:
            with self.get_session() as session:
                signals = session.query(BacktestSignal).join(BacktestRun).filter(
                    BacktestRun.symbol == symbol,
                    BacktestRun.timeframe == timeframe,
                    BacktestSignal.fibonacci_level == fibonacci_level,
                    BacktestSignal.outcome.isnot(None)
                ).all()
                
                if not signals:
                    return {}
                
                total_signals = len(signals)
                wins = len([s for s in signals if s.outcome == 'win'])
                losses = len([s for s in signals if s.outcome == 'loss'])
                
                total_profit = sum(s.profit_loss_pips or 0 for s in signals)
                avg_profit = total_profit / total_signals if total_signals > 0 else 0
                
                win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
                
                return {
                    'fibonacci_level': fibonacci_level,
                    'total_signals': total_signals,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': win_rate,
                    'total_profit_pips': total_profit,
                    'avg_profit_pips': avg_profit
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze Fibonacci level performance: {e}")
            return {}


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> Optional[DatabaseManager]:
    """Get the global database manager instance."""
    return db_manager


def initialize_database() -> DatabaseManager:
    """Initialize the global database manager."""
    global db_manager
    db_manager = DatabaseManager()
    
    if db_manager.connect():
        logger.info("Database system initialized successfully")
        return db_manager
    else:
        logger.error("Failed to initialize database system")
        return None