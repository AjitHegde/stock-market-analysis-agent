# Market Context Analyzer Feature

## Overview

Added a new `MarketContextAnalyzer` module that provides broader market context to improve stock recommendations by considering overall market conditions.

## Implementation

### New Module: `src/market_context_analyzer.py`

**Responsibilities:**
- Fetch Nifty 50, Bank Nifty, and India VIX data
- Calculate 20-day and 50-day moving averages for indices
- Determine market trends and state
- Cache results for 15 minutes to reduce API calls

**Market State Determination:**
- **Bullish**: Both Nifty 50 and Bank Nifty above their 20DMA and 50DMA
- **Bearish**: Both indices below their 20DMA and 50DMA
- **Neutral**: Mixed signals (one bullish, one bearish)
- **Volatile**: VIX above high threshold (overrides other signals)

**VIX Levels:**
- Low: < 15.0
- Moderate: 15.0 - 20.0
- High: 20.0 - 25.0
- Very High: > 25.0

### Integration Points

#### 1. Agent Core (`src/agent_core.py`)
- Added `MarketContextAnalyzer` initialization
- Integrated market context fetching in `analyze_stock()` method
- Passes market context to `RecommendationEngine` and `RiskManager`

#### 2. Recommendation Engine (`src/recommendation_engine.py`)
- Updated `generate_recommendation()` to accept `market_context` parameter
- Added market context adjustment logic:
  - **Volatile markets**: Downgrade weak BUY/SELL to HOLD
  - **Bearish markets**: Downgrade weak BUY to HOLD (requires higher confidence)
- Adjusted confidence scores based on VIX levels
- Added market context description to reasoning text

#### 3. Models (`src/models.py`)
- Added `MarketContext` dataclass with all market state information
- Updated `AnalysisResult` to include optional `market_context` field

#### 4. CLI (`src/cli.py`)
- Added "🌍 Market Context" section to output
- Displays:
  - Nifty 50 trend and price
  - Bank Nifty trend and price
  - India VIX level and value
  - Overall market state

## Example Output

```
🌍 Market Context
                                        
  Nifty 50:       🔴 Bearish (₹25,049)  
  Bank Nifty:     🔴 Bearish (₹58,473)  
  India VIX:      🟢 Low (14.19)        
  Market State:   🔴 BEARISH            
```

## Behavior Examples

### Example 1: Bearish Market Adjustment
**Scenario**: Stock has positive signals (+0.49 combined score) but market is bearish

**Without Market Context**: BUY recommendation
**With Market Context**: HOLD recommendation (downgraded due to bearish market)

**Reasoning**: In bearish markets, the system requires stronger signals (>0.6) for BUY recommendations to reduce risk.

### Example 2: Volatile Market Adjustment
**Scenario**: Stock has moderate signals but VIX is very high (>25)

**Without Market Context**: BUY/SELL based on score
**With Market Context**: HOLD recommendation (downgraded due to high volatility)

**Reasoning**: High volatility increases risk, so the system becomes more conservative.

### Example 3: Bullish Market
**Scenario**: Stock has positive signals and market is bullish

**Behavior**: No adjustment needed, recommendation proceeds normally
**Confidence**: May be slightly boosted due to favorable market conditions

## Testing

Created comprehensive test suite in `tests/test_market_context_analyzer.py`:
- ✅ Bullish market detection
- ✅ Bearish market detection
- ✅ Volatile market detection (high VIX)
- ✅ Neutral market detection (mixed signals)
- ✅ VIX level classification
- ✅ Trend determination logic
- ✅ Caching mechanism
- ✅ Error handling

All tests pass successfully.

## Performance Considerations

1. **Caching**: Market context is cached for 15 minutes to reduce API calls
2. **Parallel Fetching**: Could be optimized to fetch indices in parallel (future enhancement)
3. **Error Handling**: Gracefully handles API failures with neutral default values

## Future Enhancements

1. **Sector-Specific Context**: Add sector indices (IT, Pharma, Auto, etc.)
2. **Global Markets**: Include US indices (S&P 500, Nasdaq) for global context
3. **Historical Correlation**: Track how stock correlates with market movements
4. **Market Regime Detection**: Identify bull/bear market regimes over longer periods
5. **Adaptive Thresholds**: Adjust BUY/SELL thresholds based on market volatility

## Files Modified

- `src/market_context_analyzer.py` (NEW)
- `src/agent_core.py`
- `src/recommendation_engine.py`
- `src/models.py`
- `src/cli.py`
- `tests/test_market_context_analyzer.py` (NEW)
- `tests/test_recommendation_engine.py` (updated thresholds)

## Impact

This feature significantly improves the quality of recommendations by:
1. **Reducing false positives**: Prevents BUY recommendations in bearish/volatile markets
2. **Risk management**: Automatically adjusts for market conditions
3. **Context awareness**: Provides users with broader market perspective
4. **Transparency**: Shows market context in reasoning and output
