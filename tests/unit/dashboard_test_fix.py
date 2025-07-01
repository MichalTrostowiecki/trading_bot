"""
Quick test to understand the timestamp format issue
"""
import pandas as pd
from datetime import datetime

# Test timestamp conversions
test_timestamp = "2025-01-27T19:00:00"
dt = pd.Timestamp(test_timestamp)

print("Original:", test_timestamp)
print("Pandas Timestamp:", dt)
print("ISO format:", dt.isoformat())
print("Unix timestamp (seconds):", int(dt.timestamp()))
print("Unix timestamp (ms):", int(dt.timestamp() * 1000))
print("Date from unix:", datetime.fromtimestamp(int(dt.timestamp())))