"""
Enhanced Signal Performance Tracking System
Analyzes the real-world performance of enhanced signals for ML/AI training data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class SignalPerformance:
    """Performance metrics for an individual enhanced signal."""
    signal_id: str
    timestamp: datetime
    signal_type: str  # 'buy' or 'sell'
    entry_price: float
    stop_loss: float
    take_profit: float
    fibonacci_level: float
    pattern_type: str
    pattern_strength: str
    confluence_score: float
    quality: str
    factors: List[str]
    
    # Performance tracking
    max_favorable_move: float = 0.0  # Best price reached in signal direction
    max_adverse_move: float = 0.0    # Worst price reached against signal
    bars_to_target: Optional[int] = None
    bars_to_stop: Optional[int] = None
    final_outcome: Optional[str] = None  # 'target_hit', 'stop_hit', 'timeout'
    actual_pnl: Optional[float] = None
    
    # Time-based performance
    performance_1h: Optional[float] = None
    performance_4h: Optional[float] = None
    performance_24h: Optional[float] = None
    
    # Quality metrics
    signal_efficiency: Optional[float] = None  # How quickly signal moved to target
    drawdown_ratio: Optional[float] = None     # Max adverse / favorable ratio

@dataclass
class PatternPerformanceStats:
    """Aggregate performance statistics for a specific pattern type."""
    pattern_type: str
    pattern_strength: str
    total_signals: int
    win_rate: float
    avg_confluence_score: float
    avg_actual_pnl: float
    avg_bars_to_target: float
    avg_bars_to_stop: float
    best_performing_factors: List[str]
    fibonacci_level_performance: Dict[float, float]  # fib_level -> avg_pnl

class SignalPerformanceTracker:
    """
    Tracks and analyzes enhanced signal performance for ML/AI development.
    """
    
    def __init__(self):
        self.active_signals: Dict[str, SignalPerformance] = {}
        self.completed_signals: List[SignalPerformance] = []
        self.performance_stats: Dict[str, PatternPerformanceStats] = {}
        
    def track_new_signal(self, enhanced_signal: Dict[str, Any]) -> str:
        """
        Start tracking a new enhanced signal.
        
        Args:
            enhanced_signal: Enhanced signal data from strategy
            
        Returns:
            signal_id: Unique identifier for tracking
        """
        signal_id = f"{enhanced_signal['timestamp']}_{enhanced_signal['price']}"
        
        performance = SignalPerformance(
            signal_id=signal_id,
            timestamp=pd.to_datetime(enhanced_signal['timestamp']),
            signal_type=enhanced_signal['signal_type'],
            entry_price=enhanced_signal['price'],
            stop_loss=enhanced_signal['stop_loss'],
            take_profit=enhanced_signal['take_profit'],
            fibonacci_level=enhanced_signal['fibonacci_level'],
            pattern_type=enhanced_signal['pattern_type'],
            pattern_strength=enhanced_signal['pattern_strength'],
            confluence_score=enhanced_signal['confluence_score'],
            quality=enhanced_signal['quality'],
            factors=enhanced_signal['factors']
        )
        
        self.active_signals[signal_id] = performance
        logger.info(f"Started tracking signal {signal_id}: {enhanced_signal['signal_type']} at {enhanced_signal['price']}")
        
        return signal_id
    
    def update_signal_performance(self, signal_id: str, current_price: float, 
                                 current_time: datetime, bars_elapsed: int):
        """
        Update performance metrics for an active signal.
        
        Args:
            signal_id: Signal identifier
            current_price: Current market price
            current_time: Current timestamp
            bars_elapsed: Bars since signal generation
        """
        if signal_id not in self.active_signals:
            return
            
        signal = self.active_signals[signal_id]
        
        # Calculate current performance
        if signal.signal_type == 'buy':
            current_pnl = current_price - signal.entry_price
            favorable_move = max(0, current_price - signal.entry_price)
            adverse_move = min(0, current_price - signal.entry_price)
        else:  # sell
            current_pnl = signal.entry_price - current_price
            favorable_move = max(0, signal.entry_price - current_price)
            adverse_move = min(0, signal.entry_price - current_price)
        
        # Update max moves
        signal.max_favorable_move = max(signal.max_favorable_move, favorable_move)
        signal.max_adverse_move = min(signal.max_adverse_move, adverse_move)
        
        # Check for target/stop hit
        target_hit = False
        stop_hit = False
        
        if signal.signal_type == 'buy':
            target_hit = current_price >= signal.take_profit
            stop_hit = current_price <= signal.stop_loss
        else:  # sell
            target_hit = current_price <= signal.take_profit
            stop_hit = current_price >= signal.stop_loss
        
        # Update time-based performance
        time_elapsed = current_time - signal.timestamp
        if time_elapsed >= timedelta(hours=1) and signal.performance_1h is None:
            signal.performance_1h = current_pnl
        if time_elapsed >= timedelta(hours=4) and signal.performance_4h is None:
            signal.performance_4h = current_pnl
        if time_elapsed >= timedelta(hours=24) and signal.performance_24h is None:
            signal.performance_24h = current_pnl
        
        # Complete signal if target/stop hit
        if target_hit and signal.final_outcome is None:
            signal.final_outcome = 'target_hit'
            signal.bars_to_target = bars_elapsed
            signal.actual_pnl = signal.take_profit - signal.entry_price if signal.signal_type == 'buy' else signal.entry_price - signal.take_profit
            self._complete_signal(signal_id)
            logger.info(f"Signal {signal_id} hit target after {bars_elapsed} bars")
            
        elif stop_hit and signal.final_outcome is None:
            signal.final_outcome = 'stop_hit'
            signal.bars_to_stop = bars_elapsed
            signal.actual_pnl = signal.stop_loss - signal.entry_price if signal.signal_type == 'buy' else signal.entry_price - signal.stop_loss
            self._complete_signal(signal_id)
            logger.info(f"Signal {signal_id} hit stop loss after {bars_elapsed} bars")
    
    def _complete_signal(self, signal_id: str):
        """Move signal from active to completed tracking."""
        if signal_id in self.active_signals:
            signal = self.active_signals[signal_id]
            
            # Calculate final metrics
            if signal.max_favorable_move > 0:
                signal.signal_efficiency = signal.max_favorable_move / (signal.bars_to_target or signal.bars_to_stop or 1)
                signal.drawdown_ratio = abs(signal.max_adverse_move) / signal.max_favorable_move if signal.max_favorable_move > 0 else 0
            
            self.completed_signals.append(signal)
            del self.active_signals[signal_id]
            
            # Update pattern statistics
            self._update_pattern_stats(signal)
    
    def _update_pattern_stats(self, signal: SignalPerformance):
        """Update aggregate statistics for the signal's pattern type."""
        pattern_key = f"{signal.pattern_type}_{signal.pattern_strength}"
        
        if pattern_key not in self.performance_stats:
            self.performance_stats[pattern_key] = PatternPerformanceStats(
                pattern_type=signal.pattern_type,
                pattern_strength=signal.pattern_strength,
                total_signals=0,
                win_rate=0.0,
                avg_confluence_score=0.0,
                avg_actual_pnl=0.0,
                avg_bars_to_target=0.0,
                avg_bars_to_stop=0.0,
                best_performing_factors=[],
                fibonacci_level_performance={}
            )
        
        # Get all completed signals for this pattern
        pattern_signals = [s for s in self.completed_signals 
                          if s.pattern_type == signal.pattern_type and s.pattern_strength == signal.pattern_strength]
        
        if pattern_signals:
            stats = self.performance_stats[pattern_key]
            stats.total_signals = len(pattern_signals)
            
            # Calculate win rate
            wins = len([s for s in pattern_signals if s.final_outcome == 'target_hit'])
            stats.win_rate = wins / len(pattern_signals)
            
            # Calculate averages
            stats.avg_confluence_score = np.mean([s.confluence_score for s in pattern_signals])
            stats.avg_actual_pnl = np.mean([s.actual_pnl for s in pattern_signals if s.actual_pnl is not None])
            
            target_bars = [s.bars_to_target for s in pattern_signals if s.bars_to_target is not None]
            stop_bars = [s.bars_to_stop for s in pattern_signals if s.bars_to_stop is not None]
            
            stats.avg_bars_to_target = np.mean(target_bars) if target_bars else 0
            stats.avg_bars_to_stop = np.mean(stop_bars) if stop_bars else 0
            
            # Fibonacci level performance
            fib_performance = {}
            for fib_level in [0.236, 0.382, 0.5, 0.618, 0.786]:
                fib_signals = [s for s in pattern_signals if s.fibonacci_level == fib_level]
                if fib_signals:
                    fib_performance[fib_level] = np.mean([s.actual_pnl for s in fib_signals if s.actual_pnl is not None])
            stats.fibonacci_level_performance = fib_performance
    
    def get_signal_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics for ML/AI model development.
        
        Returns:
            Analytics dictionary with performance metrics
        """
        total_signals = len(self.completed_signals)
        if total_signals == 0:
            return {"message": "No completed signals to analyze"}
        
        # Overall performance metrics
        wins = len([s for s in self.completed_signals if s.final_outcome == 'target_hit'])
        overall_win_rate = wins / total_signals
        
        # Quality-based performance
        quality_performance = {}
        for quality in ['weak', 'moderate', 'strong']:
            quality_signals = [s for s in self.completed_signals if s.quality == quality]
            if quality_signals:
                quality_wins = len([s for s in quality_signals if s.final_outcome == 'target_hit'])
                quality_performance[quality] = {
                    'count': len(quality_signals),
                    'win_rate': quality_wins / len(quality_signals),
                    'avg_confluence_score': np.mean([s.confluence_score for s in quality_signals]),
                    'avg_pnl': np.mean([s.actual_pnl for s in quality_signals if s.actual_pnl is not None])
                }
        
        # Pattern performance ranking
        pattern_ranking = []
        for pattern_stats in self.performance_stats.values():
            if pattern_stats.total_signals >= 3:  # Minimum sample size
                pattern_ranking.append({
                    'pattern': f"{pattern_stats.pattern_type}_{pattern_stats.pattern_strength}",
                    'win_rate': pattern_stats.win_rate,
                    'avg_pnl': pattern_stats.avg_actual_pnl,
                    'total_signals': pattern_stats.total_signals,
                    'avg_confluence_score': pattern_stats.avg_confluence_score
                })
        
        # Sort by win rate
        pattern_ranking.sort(key=lambda x: x['win_rate'], reverse=True)
        
        # Confluence score analysis
        score_ranges = {
            '0-40': [s for s in self.completed_signals if s.confluence_score < 40],
            '40-60': [s for s in self.completed_signals if 40 <= s.confluence_score < 60],
            '60-80': [s for s in self.completed_signals if 60 <= s.confluence_score < 80],
            '80-100': [s for s in self.completed_signals if s.confluence_score >= 80]
        }
        
        score_analysis = {}
        for range_name, signals in score_ranges.items():
            if signals:
                wins = len([s for s in signals if s.final_outcome == 'target_hit'])
                score_analysis[range_name] = {
                    'count': len(signals),
                    'win_rate': wins / len(signals),
                    'avg_pnl': np.mean([s.actual_pnl for s in signals if s.actual_pnl is not None])
                }
        
        return {
            'overall_performance': {
                'total_signals': total_signals,
                'overall_win_rate': overall_win_rate,
                'active_signals': len(self.active_signals)
            },
            'quality_performance': quality_performance,
            'pattern_ranking': pattern_ranking[:10],  # Top 10 patterns
            'confluence_score_analysis': score_analysis,
            'ml_features': self._extract_ml_features()
        }
    
    def _extract_ml_features(self) -> Dict[str, Any]:
        """Extract features for ML model training."""
        if not self.completed_signals:
            return {}
        
        # Feature engineering for ML
        features = []
        labels = []
        
        for signal in self.completed_signals:
            if signal.actual_pnl is not None:
                feature_vector = {
                    'fibonacci_level': signal.fibonacci_level,
                    'confluence_score': signal.confluence_score,
                    'pattern_type_encoded': hash(signal.pattern_type) % 100,  # Simple encoding
                    'pattern_strength_encoded': {'weak': 1, 'moderate': 2, 'strong': 3}.get(signal.pattern_strength, 1),
                    'quality_encoded': {'weak': 1, 'moderate': 2, 'strong': 3}.get(signal.quality, 1),
                    'num_factors': len(signal.factors),
                    'signal_type_encoded': 1 if signal.signal_type == 'buy' else 0
                }
                features.append(feature_vector)
                labels.append(1 if signal.final_outcome == 'target_hit' else 0)
        
        return {
            'feature_count': len(features),
            'feature_names': list(features[0].keys()) if features else [],
            'label_distribution': {
                'wins': sum(labels),
                'losses': len(labels) - sum(labels)
            },
            'ready_for_ml': len(features) >= 50  # Minimum samples for ML
        }
    
    def export_performance_data(self) -> pd.DataFrame:
        """Export all signal performance data for external analysis."""
        if not self.completed_signals:
            return pd.DataFrame()
        
        data = []
        for signal in self.completed_signals:
            data.append(asdict(signal))
        
        return pd.DataFrame(data)
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics for dashboard display."""
        active_count = len(self.active_signals)
        completed_count = len(self.completed_signals)
        
        if completed_count == 0:
            return {
                'active_signals': active_count,
                'completed_signals': 0,
                'win_rate': 0,
                'avg_bars_to_resolution': 0
            }
        
        wins = len([s for s in self.completed_signals if s.final_outcome == 'target_hit'])
        win_rate = wins / completed_count
        
        # Average bars to resolution
        resolution_bars = []
        for signal in self.completed_signals:
            if signal.bars_to_target:
                resolution_bars.append(signal.bars_to_target)
            elif signal.bars_to_stop:
                resolution_bars.append(signal.bars_to_stop)
        
        avg_bars = np.mean(resolution_bars) if resolution_bars else 0
        
        return {
            'active_signals': active_count,
            'completed_signals': completed_count,
            'win_rate': round(win_rate * 100, 1),
            'avg_bars_to_resolution': round(avg_bars, 1)
        }