// ABC PATTERN DASHBOARD VISUALIZATION BACKUP
// Saved before reverting to working commit e717107
// Date: July 5, 2025

/*
This file contains the ABC pattern visualization code from research_api.py
Re-add this to the dashboard after revert to restore ABC pattern visualization.
*/

// =============================================================================
// ACCUMULATED ABC PATTERNS ARRAY (Add around line 870)
// =============================================================================
let accumulatedABCPatterns = [];

// =============================================================================
// ABC PATTERN MANAGER CLASS (Add around line 1650)
// =============================================================================
class ABCPatternManager {
    constructor(candlestickSeries) {
        this.candlestickSeries = candlestickSeries;
        this.abcLines = [];
        this.abcLabels = [];
        
        // ABC wave styling
        this.waveStyles = {
            A: { color: '#FF6B6B', width: 2, style: 0 }, // Solid red
            B: { color: '#4ECDC4', width: 2, style: 0 }, // Solid teal
            C: { color: '#45B7D1', width: 2, style: 0 }  // Solid blue
        };
        
        console.log('📊 ABCPatternManager initialized');
    }

    // Main method to display ABC patterns
    displayABCPatterns(abcPatterns) {
        try {
            if (!abcPatterns || abcPatterns.length === 0) {
                return;
            }

            console.log('🔄 Processing', abcPatterns.length, 'ABC patterns');

            // Clear existing ABC patterns first
            this.clearABCPatterns();

            // Add each ABC pattern
            abcPatterns.forEach((pattern, index) => {
                this.addABCPatternToChart(pattern, index);
            });

        } catch (error) {
            console.error('❌ Error displaying ABC patterns:', error);
        }
    }

    // Add individual ABC pattern to chart
    addABCPatternToChart(pattern, index) {
        try {
            if (!chart || !pattern) return;

            // Wave A line (fractal A to fractal B)
            this.addWaveLine('A', pattern.wave_a, index);
            
            // Wave B line (fractal B to fractal C)
            this.addWaveLine('B', pattern.wave_b, index);
            
            // Wave C line (fractal C to current position)
            this.addWaveLine('C', pattern.wave_c, index);

            // Add labels for each wave
            this.addWaveLabels(pattern, index);

            console.log('✅ ABC pattern added:', {
                index: index,
                type: pattern.pattern_type,
                complete: pattern.is_complete,
                confluence: pattern.fibonacci_confluence
            });

        } catch (error) {
            console.error('❌ Error adding ABC pattern to chart:', error);
        }
    }

    // Add line for individual wave
    addWaveLine(waveType, waveData, patternIndex) {
        try {
            const style = this.waveStyles[waveType];
            
            // Convert timestamps to chart time format
            const startTime = new Date(waveData.start_timestamp).getTime() / 1000;
            const endTime = new Date(waveData.end_timestamp).getTime() / 1000;
            
            // Validate timestamps
            if (isNaN(startTime) || isNaN(endTime)) {
                console.warn('⚠️ Invalid timestamps for wave', waveType);
                return;
            }

            // Create line data
            const lineData = [
                { time: startTime, value: waveData.start_price },
                { time: endTime, value: waveData.end_price }
            ];

            // Create line series
            const lineSeries = chart.addLineSeries({
                color: style.color,
                lineWidth: style.width,
                lineStyle: style.style,
                priceLineVisible: false,
                lastValueVisible: false,
                title: `ABC-${waveType}-${patternIndex}`
            });

            lineSeries.setData(lineData);
            this.abcLines.push(lineSeries);

        } catch (error) {
            console.error('❌ Error adding ABC wave line:', error);
        }
    }

    // Add wave labels
    addWaveLabels(pattern, index) {
        try {
            // Add labels for A, B, C waves
            ['A', 'B', 'C'].forEach(waveType => {
                const waveData = pattern[`wave_${waveType.toLowerCase()}`];
                const labelTime = new Date(waveData.end_timestamp).getTime() / 1000;
                
                if (!isNaN(labelTime)) {
                    const marker = {
                        time: labelTime,
                        position: 'inBar',
                        color: this.waveStyles[waveType].color,
                        shape: 'circle',
                        text: waveType,
                        size: 1
                    };
                    
                    this.abcLabels.push(marker);
                }
            });

            // Update markers on chart
            this.updateChartMarkers();

        } catch (error) {
            console.error('❌ Error adding ABC wave labels:', error);
        }
    }

    // Update chart markers
    updateChartMarkers() {
        if (this.candlestickSeries && this.abcLabels.length > 0) {
            const existingMarkers = this.candlestickSeries.markers() || [];
            const allMarkers = [...existingMarkers, ...this.abcLabels];
            this.candlestickSeries.setMarkers(allMarkers);
        }
    }

    // Clear all ABC patterns
    clearABCPatterns() {
        try {
            // Remove all ABC line series
            this.abcLines.forEach(lineSeries => {
                if (chart && lineSeries) {
                    chart.removeSeries(lineSeries);
                }
            });
            this.abcLines = [];

            // Clear ABC labels
            this.abcLabels = [];

            console.log('🧹 ABC patterns cleared');

        } catch (error) {
            console.error('❌ Error clearing ABC patterns:', error);
        }
    }

    // Load all patterns (for accumulated display)
    loadAllPatterns(patterns) {
        this.displayABCPatterns(patterns);
    }

    // Clear patterns (alias for clearABCPatterns)
    clearPatterns() {
        this.clearABCPatterns();
    }
}

// =============================================================================
// ABC PATTERN CHECKBOX (Add to HTML around line 720)
// =============================================================================
/*
<div class="metric">
    <span class="metric-label">Show ABC Patterns:</span>
    <input type="checkbox" id="showABCPatterns" onchange="refreshChartElements()">
</div>
*/

// =============================================================================
// ABC PATTERN PROCESSING IN UPDATEALLMARKERS (Add around line 2900)
// =============================================================================
/*
// Handle ABC patterns
if (!document.getElementById('showABCPatterns').checked) {
    abcPatternManager.clearABCPatterns();
    console.log('ABC patterns hidden by checkbox');
} else {
    // Load all accumulated ABC patterns using proper pattern management
    if (accumulatedABCPatterns && accumulatedABCPatterns.length > 0) {
        abcPatternManager.displayABCPatterns(accumulatedABCPatterns);
        console.log(`🌊 Showing ${accumulatedABCPatterns.length} ABC patterns`);
    } else {
        console.log('No ABC patterns accumulated yet');
    }
}
*/

// =============================================================================
// ABC PATTERN REAL-TIME PROCESSING (Add to handleBacktestUpdate around line 2247)
// =============================================================================
/*
// Process ABC patterns from strategy results
if (data.strategy_results && data.strategy_results.abc_patterns) {
    const results = data.strategy_results;
    console.log('🌊 ABC Pattern check:', {
        'has_abc_patterns': !!(results.abc_patterns && results.abc_patterns.length > 0),
        'abc_patterns_count': results.abc_patterns ? results.abc_patterns.length : 0,
        'checkbox_checked': document.getElementById('showABCPatterns').checked,
        'abc_patterns_data': results.abc_patterns
    });
    
    if (results.abc_patterns && results.abc_patterns.length > 0) {
        accumulatedABCPatterns = results.abc_patterns;
        
        if (document.getElementById('showABCPatterns').checked) {
            console.log('✅ Calling abcPatternManager.displayABCPatterns with', results.abc_patterns.length, 'patterns');
            abcPatternManager.displayABCPatterns(results.abc_patterns);
        }
    }
}
*/

// =============================================================================
// ABC PATTERN MANAGER INITIALIZATION (Add around line 1800+)
// =============================================================================
/*
// Initialize ABC pattern manager
let abcPatternManager = null;
if (candlestickSeries) {
    abcPatternManager = new ABCPatternManager(candlestickSeries);
}
*/

// =============================================================================
// LOAD ALL STRATEGY ELEMENTS ABC INTEGRATION (Add around line 3600)
// =============================================================================
/*
// Load ABC patterns from database endpoint (if available)
try {
    const abcResponse = await fetch(`/api/abc-patterns?symbol=${symbol}&timeframe=${timeframe}&start_date=${startDate}&end_date=${endDate}`);
    if (abcResponse.ok) {
        const abcResult = await abcResponse.json();
        
        if (abcResult.success && abcResult.patterns) {
            console.log(`🌊 Loaded ${abcResult.patterns.length} ABC patterns from database`);
            
            // Always populate accumulated arrays regardless of checkbox state
            accumulatedABCPatterns = abcResult.patterns;
            
            // Display control based on checkbox
            if (abcResult.patterns.length > 0 && document.getElementById('showABCPatterns').checked) {
                console.log(`🌊 Displaying ${abcResult.patterns.length} ABC patterns using unified system`);
                abcPatternManager.loadAllPatterns(abcResult.patterns);
            } else {
                console.log('🌊 ABC patterns loaded but not displayed (checkbox unchecked):', {
                    patternCount: abcResult.patterns?.length || 0,
                    checkboxChecked: document.getElementById('showABCPatterns').checked
                });
            }
        } else {
            console.log('🌊 Failed to load ABC patterns:', abcResult.message);
        }
    }
} catch (error) {
    console.log('🌊 ABC patterns endpoint not available yet');
}
*/

// =============================================================================
// POSITION-AWARE ABC UPDATES (Add to updateMarkersForPosition around line 2810)
// =============================================================================
/*
// Update ABC patterns for current position
if (document.getElementById('showABCPatterns').checked) {
    abcPatternManager.loadAllPatterns(currentABCPatterns);
} else {
    abcPatternManager.clearPatterns();
}
*/