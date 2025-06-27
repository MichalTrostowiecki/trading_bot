"""
Configuration Management System
Handles loading and validation of configuration files for the trading bot.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from pydantic import ValidationError


class MT5Config(BaseModel):
    """MetaTrader 5 configuration."""
    server: str
    login: int
    password: str
    timeout: int = 10000
    
    @validator('login')
    def validate_login(cls, v):
        if v <= 0:
            raise ValueError('MT5 login must be positive')
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1000 or v > 60000:
            raise ValueError('MT5 timeout must be between 1000 and 60000 ms')
        return v


class DataConfig(BaseModel):
    """Data management configuration."""
    symbols: List[str]
    timeframes: List[str]
    history_days: int = 365
    cache_enabled: bool = True
    cache_ttl: int = 3600
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('At least one symbol must be specified')
        # Validate symbol format (basic check)
        for symbol in v:
            if not symbol.isalnum():
                raise ValueError(f'Invalid symbol format: {symbol}')
        return v
    
    @validator('timeframes')
    def validate_timeframes(cls, v):
        valid_timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1']
        for tf in v:
            if tf not in valid_timeframes:
                raise ValueError(f'Invalid timeframe: {tf}')
        return v
    
    @validator('history_days')
    def validate_history_days(cls, v):
        if v < 1 or v > 3650:  # Max 10 years
            raise ValueError('History days must be between 1 and 3650')
        return v


class TradingConfig(BaseModel):
    """Trading strategy configuration."""
    risk_per_trade: float = 0.01
    max_positions: int = 5
    max_daily_loss: float = 0.06
    fibonacci_levels: Dict[str, List[float]]
    
    @validator('risk_per_trade')
    def validate_risk_per_trade(cls, v):
        if v <= 0 or v > 0.1:  # Max 10% risk per trade
            raise ValueError('Risk per trade must be between 0 and 0.1 (10%)')
        return v
    
    @validator('max_positions')
    def validate_max_positions(cls, v):
        if v < 1 or v > 20:
            raise ValueError('Max positions must be between 1 and 20')
        return v
    
    @validator('max_daily_loss')
    def validate_max_daily_loss(cls, v):
        if v <= 0 or v > 0.5:  # Max 50% daily loss
            raise ValueError('Max daily loss must be between 0 and 0.5 (50%)')
        return v
    
    @validator('fibonacci_levels')
    def validate_fibonacci_levels(cls, v):
        required_keys = ['retracements', 'extensions']
        for key in required_keys:
            if key not in v:
                raise ValueError(f'Missing fibonacci levels key: {key}')
            if not isinstance(v[key], list):
                raise ValueError(f'Fibonacci {key} must be a list')
            for level in v[key]:
                if not isinstance(level, (int, float)) or level < 0:
                    raise ValueError(f'Invalid fibonacci level: {level}')
        return v


class MLConfig(BaseModel):
    """Machine Learning configuration."""
    model_retrain_days: int = 30
    feature_lookback: int = 100
    validation_split: float = 0.2
    random_state: int = 42
    
    @validator('model_retrain_days')
    def validate_model_retrain_days(cls, v):
        if v < 1 or v > 365:
            raise ValueError('Model retrain days must be between 1 and 365')
        return v
    
    @validator('feature_lookback')
    def validate_feature_lookback(cls, v):
        if v < 10 or v > 1000:
            raise ValueError('Feature lookback must be between 10 and 1000')
        return v
    
    @validator('validation_split')
    def validate_validation_split(cls, v):
        if v <= 0 or v >= 1:
            raise ValueError('Validation split must be between 0 and 1')
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    file: str = "data/logs/trading_bot.log"
    max_size: str = "100MB"
    backup_count: int = 5
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level: {v}')
        return v.upper()
    
    @validator('backup_count')
    def validate_backup_count(cls, v):
        if v < 1 or v > 50:
            raise ValueError('Backup count must be between 1 and 50')
        return v


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str
    echo: bool = False
    pool_size: Optional[int] = None
    max_overflow: Optional[int] = None
    
    @validator('pool_size')
    def validate_pool_size(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError('Pool size must be between 1 and 100')
        return v
    
    @validator('max_overflow')
    def validate_max_overflow(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Max overflow must be between 0 and 100')
        return v


class APIConfig(BaseModel):
    """API configuration."""
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    
    @validator('port')
    def validate_port(cls, v):
        if v < 1024 or v > 65535:
            raise ValueError('Port must be between 1024 and 65535')
        return v


class SecurityConfig(BaseModel):
    """Security configuration."""
    secret_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 24  # hours
    
    @validator('jwt_expiration')
    def validate_jwt_expiration(cls, v):
        if v < 1 or v > 168:  # Max 1 week
            raise ValueError('JWT expiration must be between 1 and 168 hours')
        return v


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    prometheus_port: Optional[int] = None
    health_check_port: int = 8080
    alert_webhook: Optional[str] = None
    
    @validator('prometheus_port')
    def validate_prometheus_port(cls, v):
        if v is not None and (v < 1024 or v > 65535):
            raise ValueError('Prometheus port must be between 1024 and 65535')
        return v
    
    @validator('health_check_port')
    def validate_health_check_port(cls, v):
        if v < 1024 or v > 65535:
            raise ValueError('Health check port must be between 1024 and 65535')
        return v


class Config(BaseModel):
    """Main configuration class."""
    environment: str
    mt5: MT5Config
    data: DataConfig
    trading: TradingConfig
    ml: MLConfig
    logging: LoggingConfig
    database: DatabaseConfig
    api: APIConfig
    security: Optional[SecurityConfig] = None
    monitoring: Optional[MonitoringConfig] = None
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_environments = ['development', 'staging', 'production', 'testing']
        if v not in valid_environments:
            raise ValueError(f'Invalid environment: {v}. Must be one of {valid_environments}')
        return v
    
    class Config:
        """Pydantic config."""
        extra = "forbid"  # Don't allow extra fields


class ConfigManager:
    """Configuration manager for loading and validating configurations."""
    
    def __init__(self):
        self.config: Optional[Config] = None
        self.config_path: Optional[Path] = None
    
    def load_config(self, env: str = None) -> Config:
        """Load configuration for specified environment."""
        if env is None:
            env = os.getenv("ENVIRONMENT", "development")
        
        config_file = f"{env}.yaml"
        
        # Look for config file in multiple locations
        possible_paths = [
            Path(f"config/{config_file}"),
            Path(__file__).parent.parent.parent / "config" / config_file,
            Path.cwd() / "config" / config_file,
        ]
        
        config_path = None
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
        
        if config_path is None:
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}. "
                f"Looked in: {[str(p) for p in possible_paths]}"
            )
        
        self.config_path = config_path
        
        try:
            with open(config_path, 'r') as file:
                config_data = yaml.safe_load(file)
            
            # Replace environment variables
            config_data = self._substitute_env_vars(config_data)
            
            # Validate and create config
            self.config = Config(**config_data)
            
            return self.config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {config_path}: {e}")
        except ValidationError as e:
            raise ValueError(f"Invalid configuration in {config_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config from {config_path}: {e}")
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute environment variables in configuration data."""
        if isinstance(data, dict):
            return {key: self._substitute_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Handle ${VAR_NAME} pattern
            if data.startswith("${") and data.endswith("}"):
                var_name = data[2:-1]
                env_value = os.getenv(var_name)
                if env_value is None:
                    raise ValueError(f"Environment variable not found: {var_name}")
                
                # Try to convert to appropriate type
                if env_value.isdigit():
                    return int(env_value)
                elif env_value.lower() in ('true', 'false'):
                    return env_value.lower() == 'true'
                else:
                    return env_value
            return data
        else:
            return data
    
    def get_config(self) -> Config:
        """Get the current configuration."""
        if self.config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self.config
    
    def reload_config(self) -> Config:
        """Reload configuration from file."""
        if self.config_path is None:
            raise RuntimeError("No configuration file loaded")
        
        env = self.config.environment if self.config else "development"
        return self.load_config(env)
    
    def validate_config_file(self, config_file: Path) -> bool:
        """Validate a configuration file without loading it."""
        try:
            with open(config_file, 'r') as file:
                config_data = yaml.safe_load(file)
            
            config_data = self._substitute_env_vars(config_data)
            Config(**config_data)
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False


# Global configuration manager instance
config_manager = ConfigManager()

# Convenience function to get config
def get_config() -> Config:
    """Get the current configuration."""
    return config_manager.get_config()

# Load config automatically if ENVIRONMENT is set
try:
    config = config_manager.load_config()
except Exception:
    # Config will be loaded when needed
    config = None