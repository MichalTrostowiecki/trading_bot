#!/usr/bin/env python3
"""
Minimal dashboard to test basic functionality
Start with bare minimum and add features incrementally
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Minimal Fractal Dashboard")

@app.get("/")
async def root():
    """Minimal dashboard homepage"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Minimal Fractal Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        button { padding: 10px 20px; margin: 10px; background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .results { margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 5px; }
        pre { background: #e9ecef; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Minimal Fractal Dashboard</h1>
        <p>Testing basic fractal detection functionality</p>
        
        <button onclick="testFractals()">Test Fractal Detection</button>
        <button onclick="clearResults()">Clear Results</button>
        
        <div id="results" class="results" style="display: none;">
            <h3>Results:</h3>
            <pre id="output"></pre>
        </div>
    </div>

    <script>
        async function testFractals() {
            const resultsDiv = document.getElementById('results');
            const outputPre = document.getElementById('output');
            
            resultsDiv.style.display = 'block';
            outputPre.textContent = 'Testing fractal detection...';
            
            try {
                const response = await fetch('/api/test-fractals');
                const data = await response.json();
                
                if (data.success) {
                    outputPre.textContent = `✅ SUCCESS!\\n\\nFractals detected: ${data.fractal_count}\\n\\nDetails:\\n${JSON.stringify(data.fractals, null, 2)}`;
                } else {
                    outputPre.textContent = `❌ FAILED: ${data.error}`;
                }
            } catch (error) {
                outputPre.textContent = `❌ REQUEST FAILED: ${error.message}`;
            }
        }
        
        function clearResults() {
            document.getElementById('results').style.display = 'none';
        }
    </script>
</body>
</html>
    """)

@app.get("/api/test-fractals")
async def test_fractals():
    """Test fractal detection endpoint"""
    try:
        import sys
        import os
        import pandas as pd
        
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        from src.core.fractal_detection import FractalDetector, FractalDetectionConfig, FractalType
        from src.data.database import DatabaseManager
        
        # Get test data
        db = DatabaseManager()
        db.connect()
        
        df = db.get_historical_data(
            symbol="DJ30",
            timeframe="M1", 
            limit=50
        )
        
        if df.empty:
            return {"success": False, "error": "No test data found"}
        
        # Ensure uppercase columns
        df.columns = df.columns.str.upper()
        
        # Detect fractals
        config = FractalDetectionConfig(periods=5)
        detector = FractalDetector(config)
        fractals = detector.detect_fractals(df)
        
        # Format results
        fractal_data = []
        for fractal in fractals:
            fractal_data.append({
                "index": fractal.index,
                "timestamp": fractal.timestamp.strftime("%Y-%m-%d %H:%M"),
                "type": "HIGH" if fractal.type == FractalType.UP else "LOW",
                "price": fractal.price
            })
        
        return {
            "success": True,
            "fractal_count": len(fractals),
            "fractals": fractal_data,
            "data_bars": len(df)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting Minimal Fractal Dashboard")
    print("🌐 Dashboard: http://localhost:8002")
    print("⏹️  Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")