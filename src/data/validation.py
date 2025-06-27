"""
Data Validation and Quality Checks
Comprehensive data validation, quality assessment, and cleaning utilities.
"""

import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from scipy import stats
from src.monitoring import get_logger

logger = get_logger("data_validation")


class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = "strict"        # Fail on any issues
    MODERATE = "moderate"    # Warn on minor issues, fail on major
    LENIENT = "lenient"      # Warn on issues, don't fail


class ValidationSeverity(Enum):
    """Validation issue severity."""
    CRITICAL = "critical"    # Data unusable
    MAJOR = "major"         # Significant quality issues
    MINOR = "minor"         # Minor quality issues
    INFO = "info"           # Informational


@dataclass
class ValidationIssue:
    """Data validation issue."""
    severity: ValidationSeverity
    category: str
    description: str
    count: int = 1
    percentage: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"{self.severity.value.upper()}: {self.description} (Count: {self.count}, {self.percentage:.2f}%)"


@dataclass
class ValidationResult:
    """Data validation result."""
    is_valid: bool
    quality_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def critical_issues(self) -> List[ValidationIssue]:
        """Get critical issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL]
    
    @property
    def major_issues(self) -> List[ValidationIssue]:
        """Get major issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.MAJOR]
    
    @property
    def minor_issues(self) -> List[ValidationIssue]:
        """Get minor issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.MINOR]
    
    def get_summary(self) -> str:
        """Get validation summary."""
        status = "✅ VALID" if self.is_valid else "❌ INVALID"
        return f"{status} - Quality Score: {self.quality_score:.2f} - Issues: {len(self.issues)}"


class BaseValidator:
    """Base class for data validators."""
    
    def __init__(self, name: str, severity: ValidationSeverity = ValidationSeverity.MAJOR):
        self.name = name
        self.severity = severity
    
    def validate(self, data: pd.DataFrame) -> List[ValidationIssue]:
        """Validate data and return issues."""
        raise NotImplementedError
    
    def _create_issue(self, description: str, count: int = 1, 
                     percentage: float = 0.0, **kwargs) -> ValidationIssue:
        """Create a validation issue."""
        return ValidationIssue(
            severity=self.severity,
            category=self.name,
            description=description,
            count=count,
            percentage=percentage,
            details=kwargs
        )


class MissingDataValidator(BaseValidator):
    """Validator for missing data."""
    
    def __init__(self, max_missing_percent: float = 5.0):
        super().__init__("missing_data", ValidationSeverity.MAJOR)
        self.max_missing_percent = max_missing_percent
    
    def validate(self, data: pd.DataFrame) -> List[ValidationIssue]:
        issues = []
        
        if data.empty:
            issues.append(self._create_issue("Dataset is empty"))
            return issues
        
        total_cells = len(data) * len(data.columns)
        
        for column in data.columns:
            missing_count = data[column].isnull().sum()
            missing_percent = (missing_count / len(data)) * 100
            
            if missing_count > 0:
                severity = (ValidationSeverity.CRITICAL if missing_percent > self.max_missing_percent 
                          else ValidationSeverity.MINOR)
                
                issues.append(ValidationIssue(
                    severity=severity,
                    category=self.name,
                    description=f"Missing values in column '{column}'",
                    count=missing_count,
                    percentage=missing_percent,
                    details={'column': column}
                ))
        
        return issues


class DuplicateDataValidator(BaseValidator):
    """Validator for duplicate data."""
    
    def __init__(self, check_index: bool = True, check_rows: bool = True):
        super().__init__("duplicates", ValidationSeverity.MAJOR)
        self.check_index = check_index
        self.check_rows = check_rows
    
    def validate(self, data: pd.DataFrame) -> List[ValidationIssue]:
        issues = []
        
        if data.empty:
            return issues
        
        # Check duplicate indices (timestamps)
        if self.check_index and data.index.duplicated().any():
            duplicate_count = data.index.duplicated().sum()
            duplicate_percent = (duplicate_count / len(data)) * 100
            
            issues.append(self._create_issue(
                "Duplicate timestamps in index",
                count=duplicate_count,
                percentage=duplicate_percent
            ))
        
        # Check duplicate rows
        if self.check_rows and data.duplicated().any():
            duplicate_count = data.duplicated().sum()
            duplicate_percent = (duplicate_count / len(data)) * 100
            
            issues.append(self._create_issue(
                "Duplicate rows",
                count=duplicate_count,
                percentage=duplicate_percent
            ))
        
        return issues


class PriceDataValidator(BaseValidator):
    """Validator for price data consistency."""
    
    def __init__(self, max_price_change: float = 0.1, min_price: float = 0.0001):
        super().__init__("price_data", ValidationSeverity.MAJOR)
        self.max_price_change = max_price_change  # 10% max change
        self.min_price = min_price
    
    def validate(self, data: pd.DataFrame) -> List[ValidationIssue]:
        issues = []
        
        if data.empty:
            return issues
        
        price_columns = ['Open', 'High', 'Low', 'Close', 'open', 'high', 'low', 'close']
        available_price_cols = [col for col in price_columns if col in data.columns]
        
        if not available_price_cols:
            issues.append(self._create_issue("No price columns found"))
            return issues
        
        for col in available_price_cols:
            # Check for negative or zero prices
            invalid_prices = (data[col] <= self.min_price).sum()
            if invalid_prices > 0:
                issues.append(self._create_issue(
                    f"Invalid prices in {col} (≤ {self.min_price})",
                    count=invalid_prices,
                    percentage=(invalid_prices / len(data)) * 100,
                    column=col
                ))
            
            # Check for extreme price changes
            if len(data) > 1:
                price_changes = data[col].pct_change().abs()
                extreme_changes = (price_changes > self.max_price_change).sum()
                
                if extreme_changes > 0:
                    issues.append(self._create_issue(
                        f"Extreme price changes in {col} (> {self.max_price_change*100}%)",
                        count=extreme_changes,
                        percentage=(extreme_changes / len(data)) * 100,
                        column=col
                    ))
        
        # Check OHLC consistency
        if all(col in data.columns for col in ['Open', 'High', 'Low', 'Close']):
            # High should be >= Open, Low, Close
            high_violations = ((data['High'] < data[['Open', 'Low', 'Close']].max(axis=1))).sum()
            
            # Low should be <= Open, High, Close
            low_violations = ((data['Low'] > data[['Open', 'High', 'Close']].min(axis=1))).sum()
            
            if high_violations > 0:
                issues.append(self._create_issue(
                    "High price violations (High < max(Open, Low, Close))",
                    count=high_violations,
                    percentage=(high_violations / len(data)) * 100
                ))
            
            if low_violations > 0:
                issues.append(self._create_issue(
                    "Low price violations (Low > min(Open, High, Close))",
                    count=low_violations,
                    percentage=(low_violations / len(data)) * 100
                ))
        
        return issues


class VolumeDataValidator(BaseValidator):
    """Validator for volume data."""
    
    def __init__(self, max_zero_volume_percent: float = 20.0):
        super().__init__("volume_data", ValidationSeverity.MINOR)
        self.max_zero_volume_percent = max_zero_volume_percent
    
    def validate(self, data: pd.DataFrame) -> List[ValidationIssue]:
        issues = []
        
        if data.empty:
            return issues
        
        volume_columns = ['Volume', 'volume', 'tick_volume']
        available_vol_cols = [col for col in volume_columns if col in data.columns]
        
        for col in available_vol_cols:
            # Check for negative volumes
            negative_volumes = (data[col] < 0).sum()
            if negative_volumes > 0:
                issues.append(self._create_issue(
                    f"Negative volumes in {col}",
                    count=negative_volumes,
                    percentage=(negative_volumes / len(data)) * 100,
                    column=col
                ))
            
            # Check for excessive zero volumes
            zero_volumes = (data[col] == 0).sum()
            zero_percent = (zero_volumes / len(data)) * 100
            
            if zero_percent > self.max_zero_volume_percent:
                issues.append(self._create_issue(
                    f"Excessive zero volumes in {col} ({zero_percent:.1f}%)",
                    count=zero_volumes,
                    percentage=zero_percent,
                    column=col
                ))
        
        return issues


class TimeSeriesValidator(BaseValidator):
    """Validator for time series data."""
    
    def __init__(self, expected_frequency: Optional[str] = None):
        super().__init__("time_series", ValidationSeverity.MAJOR)
        self.expected_frequency = expected_frequency
    
    def validate(self, data: pd.DataFrame) -> List[ValidationIssue]:
        issues = []
        
        if data.empty:
            return issues
        
        if not isinstance(data.index, pd.DatetimeIndex):
            issues.append(self._create_issue("Index is not a DatetimeIndex"))
            return issues
        
        # Check for timezone information
        if data.index.tz is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category=self.name,
                description="No timezone information in timestamps"
            ))
        
        # Check for chronological order
        if not data.index.is_monotonic_increasing:
            issues.append(self._create_issue("Timestamps are not in chronological order"))
        
        # Check for expected frequency
        if self.expected_frequency and len(data) > 2:
            try:
                inferred_freq = pd.infer_freq(data.index)
                if inferred_freq != self.expected_frequency:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.MINOR,
                        category=self.name,
                        description=f"Frequency mismatch: expected {self.expected_frequency}, inferred {inferred_freq}"
                    ))
            except Exception:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.MINOR,
                    category=self.name,
                    description="Could not infer data frequency"
                ))
        
        # Check for gaps in data
        if len(data) > 1:
            time_diffs = data.index[1:] - data.index[:-1]
            median_diff = time_diffs.median()
            
            # Find gaps larger than 3x median interval
            large_gaps = time_diffs > (median_diff * 3)
            gap_count = large_gaps.sum()
            
            if gap_count > 0:
                issues.append(self._create_issue(
                    f"Data gaps detected (> 3x median interval)",
                    count=gap_count,
                    percentage=(gap_count / len(time_diffs)) * 100,
                    median_interval=str(median_diff)
                ))
        
        return issues


class StatisticalValidator(BaseValidator):
    """Validator for statistical properties."""
    
    def __init__(self, outlier_threshold: float = 3.0):
        super().__init__("statistical", ValidationSeverity.MINOR)
        self.outlier_threshold = outlier_threshold
    
    def validate(self, data: pd.DataFrame) -> List[ValidationIssue]:
        issues = []
        
        if data.empty:
            return issues
        
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            series = data[col].dropna()
            
            if len(series) < 3:
                continue
            
            # Check for outliers using Z-score
            z_scores = np.abs(stats.zscore(series))
            outliers = (z_scores > self.outlier_threshold).sum()
            
            if outliers > 0:
                outlier_percent = (outliers / len(series)) * 100
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category=self.name,
                    description=f"Statistical outliers in {col} (Z-score > {self.outlier_threshold})",
                    count=outliers,
                    percentage=outlier_percent,
                    details={'column': col, 'threshold': self.outlier_threshold}
                ))
            
            # Check for constant values
            if series.nunique() == 1:
                issues.append(self._create_issue(
                    f"Constant values in {col}",
                    column=col,
                    value=series.iloc[0]
                ))
        
        return issues


class DataValidator:
    """Main data validation orchestrator."""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.validation_level = validation_level
        self.validators: List[BaseValidator] = [
            MissingDataValidator(),
            DuplicateDataValidator(),
            PriceDataValidator(),
            VolumeDataValidator(),
            TimeSeriesValidator(),
            StatisticalValidator()
        ]
    
    def add_validator(self, validator: BaseValidator):
        """Add custom validator."""
        self.validators.append(validator)
    
    def validate(self, data: pd.DataFrame, symbol: str = "unknown") -> ValidationResult:
        """Validate data and return comprehensive result."""
        logger.debug(f"Validating data for {symbol}: {len(data)} records")
        
        all_issues = []
        metadata = {
            'symbol': symbol,
            'record_count': len(data),
            'column_count': len(data.columns) if not data.empty else 0,
            'validation_time': datetime.now(),
            'validation_level': self.validation_level.value
        }
        
        # Run all validators
        for validator in self.validators:
            try:
                issues = validator.validate(data)
                all_issues.extend(issues)
                logger.debug(f"{validator.name}: {len(issues)} issues found")
            except Exception as e:
                logger.error(f"Error in validator {validator.name}: {e}")
                all_issues.append(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    category="validation_error",
                    description=f"Validator {validator.name} failed: {str(e)}"
                ))
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(data, all_issues)
        
        # Determine if data is valid based on validation level
        is_valid = self._determine_validity(all_issues, quality_score)
        
        result = ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            issues=all_issues,
            metadata=metadata
        )
        
        logger.info(f"Validation complete for {symbol}: {result.get_summary()}")
        return result
    
    def _calculate_quality_score(self, data: pd.DataFrame, issues: List[ValidationIssue]) -> float:
        """Calculate overall data quality score (0.0 to 1.0)."""
        if data.empty:
            return 0.0
        
        base_score = 1.0
        
        # Deduct points based on issue severity and frequency
        for issue in issues:
            severity_weight = {
                ValidationSeverity.CRITICAL: 0.5,
                ValidationSeverity.MAJOR: 0.2,
                ValidationSeverity.MINOR: 0.05,
                ValidationSeverity.INFO: 0.01
            }
            
            weight = severity_weight.get(issue.severity, 0.1)
            deduction = weight * (issue.percentage / 100.0)
            base_score -= deduction
        
        return max(0.0, min(1.0, base_score))
    
    def _determine_validity(self, issues: List[ValidationIssue], quality_score: float) -> bool:
        """Determine if data is valid based on validation level."""
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        major_issues = [i for i in issues if i.severity == ValidationSeverity.MAJOR]
        
        if self.validation_level == ValidationLevel.STRICT:
            return len(issues) == 0
        elif self.validation_level == ValidationLevel.MODERATE:
            return len(critical_issues) == 0 and quality_score >= 0.7
        else:  # LENIENT
            return len(critical_issues) == 0 and quality_score >= 0.5


class DataCleaner:
    """Data cleaning utilities."""
    
    @staticmethod
    def remove_duplicates(data: pd.DataFrame, keep: str = 'first') -> pd.DataFrame:
        """Remove duplicate rows and indices."""
        # Remove duplicate rows
        data = data.drop_duplicates(keep=keep)
        
        # Remove duplicate indices
        data = data[~data.index.duplicated(keep=keep)]
        
        return data
    
    @staticmethod
    def fill_missing_values(data: pd.DataFrame, method: str = 'forward') -> pd.DataFrame:
        """Fill missing values using specified method."""
        if method == 'forward':
            return data.fillna(method='ffill')
        elif method == 'backward':
            return data.fillna(method='bfill')
        elif method == 'interpolate':
            return data.interpolate()
        elif method == 'mean':
            return data.fillna(data.mean())
        else:
            raise ValueError(f"Unknown fill method: {method}")
    
    @staticmethod
    def remove_outliers(data: pd.DataFrame, columns: List[str], threshold: float = 3.0) -> pd.DataFrame:
        """Remove statistical outliers using Z-score."""
        for col in columns:
            if col in data.columns:
                z_scores = np.abs(stats.zscore(data[col].dropna()))
                data = data[z_scores <= threshold]
        
        return data
    
    @staticmethod
    def resample_data(data: pd.DataFrame, frequency: str, method: str = 'last') -> pd.DataFrame:
        """Resample data to specified frequency."""
        if method == 'last':
            return data.resample(frequency).last()
        elif method == 'mean':
            return data.resample(frequency).mean()
        elif method == 'ohlc':
            # For OHLC data
            price_cols = ['Open', 'High', 'Low', 'Close']
            available_cols = [col for col in price_cols if col in data.columns]
            
            if available_cols:
                result = pd.DataFrame()
                if 'Open' in data.columns:
                    result['Open'] = data['Open'].resample(frequency).first()
                if 'High' in data.columns:
                    result['High'] = data['High'].resample(frequency).max()
                if 'Low' in data.columns:
                    result['Low'] = data['Low'].resample(frequency).min()
                if 'Close' in data.columns:
                    result['Close'] = data['Close'].resample(frequency).last()
                if 'Volume' in data.columns:
                    result['Volume'] = data['Volume'].resample(frequency).sum()
                
                return result
            else:
                return data.resample(frequency).last()
        else:
            raise ValueError(f"Unknown resampling method: {method}")


# Global validator instance
data_validator = DataValidator()

# Convenience functions
def validate_data(data: pd.DataFrame, symbol: str = "unknown", 
                 level: ValidationLevel = ValidationLevel.MODERATE) -> ValidationResult:
    """Validate data with specified level."""
    validator = DataValidator(level)
    return validator.validate(data, symbol)

def clean_data(data: pd.DataFrame, remove_duplicates: bool = True,
               fill_missing: bool = True, remove_outliers_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """Clean data using common operations."""
    cleaned_data = data.copy()
    
    if remove_duplicates:
        cleaned_data = DataCleaner.remove_duplicates(cleaned_data)
    
    if fill_missing:
        cleaned_data = DataCleaner.fill_missing_values(cleaned_data, method='forward')
    
    if remove_outliers_cols:
        cleaned_data = DataCleaner.remove_outliers(cleaned_data, remove_outliers_cols)
    
    return cleaned_data