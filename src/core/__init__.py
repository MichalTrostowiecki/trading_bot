"""
Core Module
Core trading algorithms and strategy components.
"""

from .fractal_detection import (
    Fractal,
    FractalType,
    FractalDetectionConfig,
    FractalDetector,
    MultiTimeframeFractalDetector,
    detect_fractals_simple,
    detect_fractals_with_strength
)

__all__ = [
    "Fractal",
    "FractalType",
    "FractalDetectionConfig", 
    "FractalDetector",
    "MultiTimeframeFractalDetector",
    "detect_fractals_simple",
    "detect_fractals_with_strength"
]