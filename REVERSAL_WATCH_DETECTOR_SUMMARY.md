# Reversal Watch Detector Summary

## Overview
Added a ReversalWatchDetector that identifies potential reversal setups when stocks are oversold but have solid fundamentals and market conditions are not in panic mode.

## Detection Criteria

### Primary Conditions (All Must Be Met)
1. **Technical Regime = Oversold Zone**
   - RSI < 25
   - MACD < 0
   - Price < MA-20

2. **Fundamentals ≥ Fair**
   - Fundamental score ≥ 0
   - P/E ratio < 30 (not overvalued)
   - P/B ratio < 5 (not extremely expensive)
   - Debt-to-equity < 2.0 (manageable debt)
   - Revenue growth > -10% (not declining rapidly)

3. **Market State ≠ PANIC**
   - VIX ≤ 30 (not extreme fear)
   - Not volatile market with VIX > 25

### Reversal Triggers (Confirmation Signals)
Once primary conditions are met, monitor these triggers:

1. **RSI Recovery**: RSI > 30
   - Stock recovering from oversold levels
   - Momentum starting to shift

2. **MACD Histogram Positive**: MACD > MACD Signal
   - Momentum turning positive
   - Potential trend reversal

3. **Volume Spike**: Current volume > 1.5x average (20-day)
   - Increased buying interest
   - Institutional participation

## Status Levels

### 📌 Watch Only (0-2 triggers met)
- **Confidence**: 45-65%
- **Action**: Monitor closely, wait for more triggers
- **Description**: Early stage reversal setup, not ready to act

### 🎯 Triggered (All 3 triggers met)
- **Confidence**: 85%
- **Action**: Strong reversal signal, consider entry
- **Description**: All confirmation signals present, high probability setup

## Implementation

### New Component: `src/reversal_watch_detector.py`

#### Classes:
1. **ReversalTrigger**: Represents a single trigger condition
   - name, met, value, threshold, description

2. **ReversalWatch**: Complete reversal analysis result
   - is_reversal_setup, status, triggers, confidence, reasoning

3. **ReversalWatchDetector**: Main detection logic
   - `check_fundamental_quality()`: Validates fundamentals
   - `check_market_panic()`: Checks for panic conditions
   - `check_reversal_triggers()`: Evaluates trigger conditions
   - `detect()`: Main detection method

### Integration Points

#### 1. Agent Core (`src/agent_core.py`)
- Added `ReversalWatchDetector` initialization
- Integrated detection after technical analysis
- Only runs when `technical.regime == "oversold-zone"`
- Adds result to `AnalysisResult.reversal_watch`

#### 2. Models (`src/models.py`)
- Added `reversal_watch` field to `AnalysisResult`

#### 3. CLI Display (`src/cli.py`)
- Added reversal watch panel after trade levels
- Shows status, confidence, triggers, and reasoning
- Color-coded: green for triggered, yellow for watch-only

## Example Output

### HDFC Bank (Current State)
```
╭───────────────────────────────────── 📌 Reversal Watch ─────────────────────────────────────╮
│ 📌 POTENTIAL REVERSAL SETUP                                                                 │
│                                                                                             │
│ Status: WATCH ONLY                                                                          │
│ Confidence: 45%                                                                             │
│                                                                                             │
│ Reversal Triggers:                                                                          │
│   ○ RSI recovering from oversold (current: 11.7)                                            │
│   ○ MACD histogram negative (-2.28)                                                         │
│   ○ Volume normal (1.1x average)                                                            │
│                                                                                             │
│ Analysis:                                                                                   │
│ ✓ In oversold zone                                                                          │
│ ✓ Fair fundamentals: P/E: 20.8, P/B: 2.5, Revenue growth: 0.3%                              │
│ ✓ Market not in panic (VIX: 14.2)                                                           │
│ ⏳ 0/3 reversal triggers met - early stage                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Interpretation
- **Primary Conditions**: All met ✓
  - Oversold zone (RSI 11.7)
  - Fair fundamentals (P/E 20.8, P/B 2.5)
  - No market panic (VIX 14.2)

- **Triggers**: 0/3 met (early stage)
  - RSI still below 30 (11.7)
  - MACD histogram still negative
  - Volume normal (no spike)

- **Action**: Watch closely, wait for triggers to confirm reversal

## Use Cases

### 1. Contrarian Entry Opportunities
- Identify oversold stocks with solid fundamentals
- Wait for confirmation triggers before entry
- Avoid catching falling knives (poor fundamentals)

### 2. Risk Management
- Avoid reversals during market panic (VIX > 30)
- Ensure fundamental quality before considering entry
- Wait for multiple confirmation signals

### 3. Timing Optimization
- Early detection (watch-only) allows preparation
- Triggered status provides high-confidence entry signal
- Volume spike confirms institutional interest

## Testing Results

### Test Scenarios
1. ✅ Valid reversal setup (watch-only): 45% confidence
2. ✅ Triggered reversal (all triggers): 85% confidence
3. ✅ Not oversold: Correctly rejected
4. ✅ Poor fundamentals: Correctly rejected
5. ✅ Market panic: Correctly rejected

### Real-World Example: HDFC Bank
- **Regime**: Oversold Zone ✓
- **Fundamentals**: Fair (P/E 20.8, P/B 2.5) ✓
- **Market**: Not panic (VIX 14.2) ✓
- **Status**: Watch Only (0/3 triggers)
- **Confidence**: 45%

## Benefits

### For Traders
1. **Early Warning**: Identifies potential reversals before they happen
2. **Risk Reduction**: Filters out poor fundamentals and panic conditions
3. **Confirmation**: Multiple triggers reduce false signals
4. **Clarity**: Clear status (watch vs triggered) guides action

### For System
1. **Modular**: Self-contained detector, easy to maintain
2. **Configurable**: Thresholds can be adjusted
3. **Extensible**: Easy to add new triggers or conditions
4. **Tested**: Comprehensive test coverage

## Future Enhancements

### Potential Additions
1. **Historical Success Rate**: Track reversal success rate over time
2. **Sector-Specific Thresholds**: Adjust criteria by sector
3. **Additional Triggers**: 
   - Price crossing above MA-20
   - Bullish candlestick patterns
   - Relative strength vs market
4. **Alert System**: Notify when status changes to triggered
5. **Backtesting**: Validate reversal signals against historical data

## Configuration

### Current Thresholds
```python
# Primary Conditions
OVERSOLD_RSI = 25
FAIR_PE_RATIO = 30
FAIR_PB_RATIO = 5
FAIR_DEBT_EQUITY = 2.0
FAIR_REVENUE_GROWTH = -10
PANIC_VIX = 30

# Reversal Triggers
RSI_RECOVERY = 30
MACD_HISTOGRAM = 0
VOLUME_SPIKE = 1.5x
```

These can be adjusted based on market conditions and backtesting results.

## Conclusion

The ReversalWatchDetector adds a powerful contrarian analysis tool that:
- Identifies oversold stocks with solid fundamentals
- Filters out dangerous conditions (poor fundamentals, market panic)
- Provides clear confirmation signals for entry timing
- Integrates seamlessly with existing technical regime classification

This enhancement helps users identify potential reversal opportunities with high confidence while managing risk through multiple validation layers.
