# Machine Learning & AI Integration Preparation Guide

## Overview
This guide outlines how to prepare for and implement machine learning enhancements to the Fibonacci trading strategy. It builds upon the visual verification system and leverages the data stored in PostgreSQL.

## ML/AI Enhancement Philosophy
1. **Start Simple**: Begin with interpretable models
2. **Enhance, Don't Replace**: ML augments the proven Fibonacci strategy
3. **Maintain Explainability**: Always understand why the model makes decisions
4. **Continuous Learning**: Models improve with more data
5. **Risk-First Approach**: Never compromise risk management

## Prerequisites
- ✅ Visual verification system operational
- ✅ At least 6 months of backtested data
- ✅ PostgreSQL database with historical trades
- ✅ Baseline strategy performance metrics
- ✅ Clean, validated data pipeline

## Phase 1: Data Preparation

### Feature Engineering
Create meaningful features from raw market data:

#### Price-Based Features
```python
# src/ml/features/price_features.py
class PriceFeatures:
    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = pd.DataFrame()
        
        # Basic price features
        features['price_change'] = df['close'].pct_change()
        features['high_low_ratio'] = df['high'] / df['low']
        features['close_to_high'] = (df['high'] - df['close']) / df['high']
        
        # Rolling statistics
        for period in [5, 10, 20, 50]:
            features[f'sma_{period}'] = df['close'].rolling(period).mean()
            features[f'std_{period}'] = df['close'].rolling(period).std()
            features[f'rsi_{period}'] = self.calculate_rsi(df['close'], period)
        
        # Microstructure
        features['spread'] = df['ask'] - df['bid']
        features['mid_price'] = (df['ask'] + df['bid']) / 2
        
        return features
```

#### Fibonacci-Specific Features
```python
# src/ml/features/fibonacci_features.py
class FibonacciFeatures:
    def calculate_features(self, swings: pd.DataFrame) -> pd.DataFrame:
        features = pd.DataFrame()
        
        # Retracement features
        features['retracement_depth'] = swings['retracement_level']
        features['time_at_level'] = swings['bars_at_fibonacci']
        features['bounce_strength'] = swings['bounce_magnitude']
        
        # Swing characteristics
        features['swing_length_pips'] = swings['swing_magnitude']
        features['swing_duration_bars'] = swings['swing_duration']
        features['swing_angle'] = swings['swing_angle']
        
        # Context features
        features['prev_swing_ratio'] = swings['current_swing'] / swings['prev_swing']
        features['fib_cluster_nearby'] = swings['other_fibs_within_20_pips']
        
        return features
```

#### Market Context Features
```python
# src/ml/features/market_features.py
class MarketFeatures:
    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = pd.DataFrame()
        
        # Volatility
        features['atr_14'] = self.calculate_atr(df, 14)
        features['volatility_regime'] = self.classify_volatility(features['atr_14'])
        
        # Market structure
        features['trend_strength'] = self.calculate_adx(df, 14)
        features['market_regime'] = self.classify_regime(df)
        
        # Time-based
        features['hour_of_day'] = df.index.hour
        features['day_of_week'] = df.index.dayofweek
        features['session'] = self.get_trading_session(df.index)
        
        # Correlation features
        features['corr_with_dxy'] = self.get_correlation('DXY', window=20)
        
        return features
```

### Data Pipeline
```python
# src/ml/data_pipeline.py
class MLDataPipeline:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    def prepare_training_data(self, 
                            symbol: str, 
                            start_date: datetime,
                            end_date: datetime) -> pd.DataFrame:
        """Prepare complete dataset for ML training"""
        
        # 1. Load raw data
        market_data = self.db.get_historical_data(symbol, 'H1', start_date, end_date)
        
        # 2. Load strategy signals
        fractals = self.db.get_fractals(symbol, 'H1', start_date, end_date)
        swings = self.db.get_swings(symbol, 'H1', start_date, end_date)
        signals = self.db.get_signals(symbol, start_date, end_date)
        
        # 3. Calculate features
        price_features = PriceFeatures().calculate_features(market_data)
        fib_features = FibonacciFeatures().calculate_features(swings)
        market_features = MarketFeatures().calculate_features(market_data)
        
        # 4. Merge all features
        features = pd.concat([price_features, fib_features, market_features], axis=1)
        
        # 5. Add labels (trade outcomes)
        features['signal'] = signals['signal_type']  # buy/sell/none
        features['outcome'] = signals['outcome']     # win/loss/breakeven
        features['profit_pips'] = signals['profit_loss']
        
        # 6. Clean and validate
        features = self.clean_dataset(features)
        
        return features
```

## Phase 2: Model Selection

### 1. Signal Quality Enhancement
**Purpose**: Improve entry signal accuracy

```python
# src/ml/models/signal_enhancer.py
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

class SignalEnhancer:
    """Enhance Fibonacci signals with ML confidence scores"""
    
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1
        )
        
    def train(self, features: pd.DataFrame, labels: pd.Series):
        """Train model to predict signal success"""
        self.model.fit(features, labels)
        
    def get_confidence(self, features: pd.DataFrame) -> float:
        """Return confidence score for current setup"""
        return self.model.predict_proba(features)[0, 1]
```

### 2. Risk Management Optimization
**Purpose**: Dynamic position sizing and stop loss

```python
# src/ml/models/risk_optimizer.py
class RiskOptimizer:
    """ML-based dynamic risk management"""
    
    def predict_optimal_stop(self, features: pd.DataFrame) -> float:
        """Predict optimal stop loss distance"""
        # Model trained on historical max adverse excursion data
        return self.stop_loss_model.predict(features)[0]
        
    def predict_position_size(self, features: pd.DataFrame) -> float:
        """Predict optimal position size based on confidence"""
        base_risk = 0.01  # 1% base risk
        confidence = self.confidence_model.predict(features)[0]
        return base_risk * confidence  # Scale by confidence
```

### 3. Exit Timing Optimization
**Purpose**: Improve exit timing

```python
# src/ml/models/exit_optimizer.py
class ExitOptimizer:
    """Optimize trade exits with ML"""
    
    def should_exit_early(self, features: pd.DataFrame) -> bool:
        """Predict if trade should exit before target"""
        exit_probability = self.exit_model.predict_proba(features)[0, 1]
        return exit_probability > 0.7
        
    def predict_max_profit_time(self, features: pd.DataFrame) -> int:
        """Predict bars until maximum profit"""
        return int(self.timing_model.predict(features)[0])
```

## Phase 3: Implementation Strategy

### Integration Architecture
```python
# src/ml/ml_trading_engine.py
class MLEnhancedTradingEngine(TradingEngine):
    """Trading engine with ML enhancements"""
    
    def __init__(self):
        super().__init__()
        self.signal_enhancer = SignalEnhancer()
        self.risk_optimizer = RiskOptimizer()
        self.exit_optimizer = ExitOptimizer()
        
    def evaluate_signal(self, signal: TradingSignal) -> bool:
        """Enhance signal evaluation with ML"""
        
        # 1. Get base Fibonacci signal
        if not super().evaluate_signal(signal):
            return False
            
        # 2. Calculate ML features
        features = self.calculate_current_features()
        
        # 3. Get ML confidence
        confidence = self.signal_enhancer.get_confidence(features)
        
        # 4. Apply threshold
        return confidence > 0.65  # Only take high-confidence trades
        
    def calculate_position_size(self, signal: TradingSignal) -> float:
        """ML-enhanced position sizing"""
        features = self.calculate_current_features()
        return self.risk_optimizer.predict_position_size(features)
```

### A/B Testing Framework
```python
# src/ml/ab_testing.py
class ABTestingFramework:
    """Compare ML-enhanced vs baseline strategy"""
    
    def run_test(self, data: pd.DataFrame, test_period: int = 30):
        # Split traffic
        baseline_trades = []
        ml_enhanced_trades = []
        
        for signal in self.generate_signals(data):
            if random.random() < 0.5:
                # Baseline strategy
                trade = self.baseline_engine.execute(signal)
                baseline_trades.append(trade)
            else:
                # ML-enhanced strategy
                trade = self.ml_engine.execute(signal)
                ml_enhanced_trades.append(trade)
                
        # Compare results
        return self.calculate_statistics(baseline_trades, ml_enhanced_trades)
```

## Phase 4: Advanced ML Techniques

### 1. Deep Learning for Pattern Recognition
```python
# src/ml/models/pattern_recognition.py
import torch
import torch.nn as nn

class ChartPatternCNN(nn.Module):
    """CNN for chart pattern recognition"""
    
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3)
        self.fc1 = nn.Linear(64 * 28 * 28, 128)
        self.fc2 = nn.Linear(128, 3)  # buy/sell/hold
        
    def forward(self, x):
        # CNN for 32x32 price chart images
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        return torch.softmax(self.fc2(x), dim=1)
```

### 2. Reinforcement Learning
```python
# src/ml/models/rl_trader.py
class DQNTrader:
    """Deep Q-Network for trading decisions"""
    
    def __init__(self, state_size: int, action_size: int = 3):
        self.state_size = state_size
        self.action_size = action_size  # buy/sell/hold
        self.memory = deque(maxlen=2000)
        self.model = self._build_model()
        
    def act(self, state: np.ndarray) -> int:
        """Choose action based on current state"""
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])
```

### 3. Ensemble Methods
```python
# src/ml/models/ensemble.py
class EnsemblePredictor:
    """Combine multiple models for robust predictions"""
    
    def __init__(self):
        self.models = {
            'xgboost': XGBClassifier(),
            'random_forest': RandomForestClassifier(),
            'neural_net': MLPClassifier(),
            'svm': SVC(probability=True)
        }
        
    def predict_ensemble(self, features: pd.DataFrame) -> float:
        """Weighted average of all model predictions"""
        predictions = []
        weights = [0.3, 0.3, 0.2, 0.2]  # Model weights
        
        for i, (name, model) in enumerate(self.models.items()):
            pred = model.predict_proba(features)[0, 1]
            predictions.append(pred * weights[i])
            
        return sum(predictions)
```

## Phase 5: Model Management

### Training Pipeline
```python
# src/ml/training_pipeline.py
class ModelTrainingPipeline:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.mlflow_tracking_uri = "http://localhost:5000"
        
    def train_models(self, symbol: str, start_date: datetime, end_date: datetime):
        # 1. Prepare data
        data = MLDataPipeline(self.db).prepare_training_data(
            symbol, start_date, end_date
        )
        
        # 2. Split data
        train, val, test = self.split_data(data)
        
        # 3. Train each model type
        models = {
            'signal_enhancer': self.train_signal_enhancer(train, val),
            'risk_optimizer': self.train_risk_optimizer(train, val),
            'exit_optimizer': self.train_exit_optimizer(train, val)
        }
        
        # 4. Evaluate on test set
        metrics = self.evaluate_models(models, test)
        
        # 5. Save models with versioning
        self.save_models(models, metrics)
        
        return models, metrics
```

### Model Monitoring
```python
# src/ml/monitoring.py
class ModelMonitor:
    """Monitor model performance in production"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    def track_prediction(self, 
                        model_name: str,
                        features: pd.DataFrame,
                        prediction: float,
                        actual_outcome: float):
        """Track each prediction for monitoring"""
        
        self.db.store_prediction({
            'model_name': model_name,
            'timestamp': datetime.now(),
            'features': features.to_json(),
            'prediction': prediction,
            'actual': actual_outcome,
            'error': abs(prediction - actual_outcome)
        })
        
    def check_model_drift(self, model_name: str, window_days: int = 7):
        """Check if model performance is degrading"""
        
        recent_predictions = self.db.get_recent_predictions(
            model_name, window_days
        )
        
        # Calculate performance metrics
        recent_accuracy = self.calculate_accuracy(recent_predictions)
        baseline_accuracy = self.get_baseline_accuracy(model_name)
        
        # Alert if significant degradation
        if recent_accuracy < baseline_accuracy * 0.9:
            self.alert_model_drift(model_name, recent_accuracy)
```

## Implementation Roadmap

### Month 1: Foundation
- Set up feature engineering pipeline
- Create training data from backtests
- Implement data validation
- Build ML infrastructure

### Month 2: Basic Models
- Train signal enhancement model
- Implement confidence scoring
- A/B testing framework
- Initial production deployment

### Month 3: Advanced Features
- Risk optimization models
- Exit timing optimization
- Ensemble methods
- Performance monitoring

### Month 4: Deep Learning
- CNN for pattern recognition
- LSTM for time series
- Reinforcement learning experiments
- Model interpretability tools

## Best Practices

### 1. Data Quality
- Clean outliers and anomalies
- Handle missing data properly
- Maintain data versioning
- Regular data audits

### 2. Model Development
- Start with simple models
- Use proper validation techniques
- Avoid overfitting
- Maintain interpretability

### 3. Production Deployment
- Gradual rollout with A/B testing
- Real-time monitoring
- Fallback mechanisms
- Regular retraining

### 4. Risk Management
- Never override stop losses
- Maintain position limits
- Monitor model confidence
- Have circuit breakers

## Conclusion
Machine learning should enhance, not replace, the proven Fibonacci trading strategy. Start with simple, interpretable models that improve specific aspects like signal quality and risk management. As confidence grows, introduce more sophisticated techniques while maintaining strict risk controls and monitoring.