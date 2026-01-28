# Technical Regime Classification Enhancement

## Overview
Enhanced the TechnicalAnalyzer to classify market regimes and map them to trading directions. This provides clearer context about the current market state and potential reversals.

## Technical Regimes

### 1. Bullish Trend 🟢
**Conditions:**
- Price > MA20 > MA50 > MA200 (perfect alignment)
- MACD > 0 (positive momentum)
- RSI 50-70 (healthy bullish range)

**Mapping:**
- Direction: Bullish
- Strength Multiplier: 1.0 (full strength)

**Interpretation:** Strong uptrend with aligned moving averages and healthy momentum. Good for long positions.

### 2. Bearish Trend 🔴
**Conditions:**
- Price < MA20 < MA50 < MA200 (perfect bearish alignment)
- MACD < 0 (negative momentum)
- RSI 30-50 (healthy bearish range)

**Mapping:**
- Direction: Bearish
- Strength Multiplier: 1.0 (full strength)

**Interpretation:** Strong downtrend with aligned moving averages and negative momentum. Avoid long positions.

### 3. Oversold Zone 🟦
**Conditions:**
- RSI < 25 (extreme oversold)
- MACD < 0 (still negative)
- Price < MA20 (below short-term average)

**Mapping:**
- Direction: Bearish (current state)
- Strength Multiplier: 0.7 (reduced due to exhaustion)

**Interpretation:** Bearish exhaustion - potential bullish reversal zone. Price may bounce from oversold levels. Good for contrarian entries with tight stops.

### 4. Overbought Zone 🟧
**Conditions:**
- RSI > 75 (extreme overbought)
- MACD > 0 (still positive)
- Price > MA20 (above short-term average)

**Mapping:**
- Direction: Bullish (current state)
- Strength Multiplier: 0.7 (reduced due to exhaustion)

**Interpretation:** Bullish exhaustion - potential bearish reversal zone. Price may pull back from overbought levels. Consider taking profits or avoiding new longs.

### 5. Consolidation 🟡
**Conditions:**
- None of the above patterns match
- Typically: sideways price action, mixed signals

**Mapping:**
- Direction: Neutral
- Strength Multiplier: 0.5 (reduced strength)

**Interpretation:** Sideways movement, no clear trend. Wait for breakout or breakdown before taking positions.

## Implementation Details

### Model Changes (`src/models.py`)
Added `regime` field to `TechnicalIndicators`:
```python
regime: str = "neutral"  # One of: bullish-trend, bearish-trend, oversold-zone, overbought-zone, consolidation
```

### Analyzer Changes (`src/technical_analyzer.py`)

#### New Methods:

**1. `classify_regime(current_price, indicators)`**
- Classifies the current technical regime based on price, MAs, RSI, and MACD
- Priority order: Oversold/Overbought zones (highest) → Trends → Consolidation
- Returns regime string

**2. `map_regime_to_direction(regime)`**
- Maps regime to direction and strength multiplier
- Returns tuple of (direction, strength_multiplier)

#### Updated `analyze()` Method:
- Calls `classify_regime()` to determine current regime
- Maps regime to direction using `map_regime_to_direction()`
- Adjusts strength based on regime multiplier
- Boosts confidence for clear regime identification (trends and exhaustion zones)

### CLI Display (`src/cli.py`)
Added regime display in technical analysis section:
```
Market Regime: 🟦 Oversold Zone (Potential Reversal)
```

Visual indicators:
- 🟢 Bullish Trend
- 🔴 Bearish Trend
- 🟦 Oversold Zone (Potential Reversal)
- 🟧 Overbought Zone (Potential Reversal)
- 🟡 Consolidation (Sideways)
- ⚪ Neutral

## Example Output

### HDFC Bank Analysis
```
📈 Technical Analysis
                                                                 
  Technical Score:        -0.14                                  
  Market Regime:          🟦 Oversold Zone (Potential Reversal)  
  RSI:                    11.67 (Oversold)                       
  MACD:                   -18.39 (Bearish)                       
  MA-20 (20-day avg):     ₹950.58                                
  MA-50 (50-day avg):     ₹978.14                                
  MA-200 (200-day avg):   ₹974.13                                
  Support (floor):        ₹802.16                                
  Resistance (ceiling):   ₹1015.18                               
```

**Analysis:**
- RSI at 11.67 is extremely oversold (< 25)
- MACD at -18.39 is negative
- Price ₹916.10 is below MA-20 ₹950.58
- **Regime: Oversold Zone** - Potential reversal opportunity

## Regime Classification Logic

### Priority Order:
1. **Oversold/Overbought Zones** (highest priority - potential reversals)
2. **Strict Trend Conditions** (perfect MA alignment + momentum)
3. **Relaxed Trend Conditions** (price vs MA-20 + MACD direction)
4. **Consolidation** (default when no clear pattern)

### Confidence Adjustments:
- **Bullish/Bearish Trend**: +10% confidence boost (clear directional bias)
- **Oversold/Overbought Zone**: +5% confidence boost (clear exhaustion signal)
- **Consolidation**: No boost (unclear direction)

### Strength Adjustments:
- **Trends**: Full strength (1.0x multiplier)
- **Exhaustion Zones**: Reduced strength (0.7x multiplier due to potential reversal)
- **Consolidation**: Half strength (0.5x multiplier)

## Benefits

1. **Clearer Context**: Users immediately understand the current market regime
2. **Reversal Signals**: Oversold/Overbought zones highlight potential reversal opportunities
3. **Risk Management**: Exhaustion zones warn of potential trend changes
4. **Better Timing**: Helps identify optimal entry/exit points based on regime
5. **Visual Clarity**: Emoji indicators make regime instantly recognizable

## Testing

All existing tests pass:
- `test_technical_analyzer.py`: 15/15 tests passing
- Regime classification tested with 5 scenarios (bullish trend, bearish trend, oversold, overbought, consolidation)

## Backward Compatibility

Fully backward compatible:
- New `regime` field has default value "neutral"
- Existing code continues to work without modification
- All existing tests pass without changes
