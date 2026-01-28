# Dynamic Weighting System Documentation

## Overview
Implemented a market-adaptive dynamic weighting system that automatically adjusts analyzer weights based on current market conditions, replacing static configuration weights.

## Weight Distribution by Market State

### 1. Bullish Market 🟢
**Conditions**: Market trending upward, low volatility
```
Sentiment:     30%  (Moderate - news matters but not critical)
Technical:     40%  (High - momentum is key in bull markets)
Fundamental:   30%  (Moderate - valuations matter but momentum leads)
```

**Rationale**:
- Technical momentum is most important in bull markets
- Price action and trends drive decisions
- Sentiment provides confirmation
- Fundamentals prevent chasing overvalued stocks

### 2. Neutral Market 🟡
**Conditions**: Sideways movement, moderate volatility
```
Sentiment:     25%  (Lower - mixed signals)
Technical:     35%  (Moderate - range-bound trading)
Fundamental:   40%  (High - value becomes more important)
```

**Rationale**:
- Fundamentals become primary driver in sideways markets
- Technical analysis helps identify range boundaries
- Sentiment less reliable in directionless markets
- Focus shifts to intrinsic value

### 3. Bearish Market 🔴
**Conditions**: Market trending downward, elevated volatility
```
Sentiment:     15%  (Low - fear dominates, less reliable)
Technical:     35%  (Moderate - identify support/oversold)
Fundamental:   50%  (High - quality and value are critical)
```

**Rationale**:
- Fundamentals are most important in bear markets
- Strong fundamentals provide downside protection
- Sentiment often overly negative (contrarian indicator)
- Technical helps identify oversold opportunities
- Focus on quality companies at good valuations

### 4. Volatile Market ⚠️
**Conditions**: High VIX, erratic price movements
```
Sentiment:     15%  (Low - noise and panic)
Technical:     35%  (Moderate - identify extremes)
Fundamental:   50%  (High - anchor to intrinsic value)
```

**Rationale**:
- Same as bearish market - focus on fundamentals
- Volatility creates noise in sentiment
- Technical helps identify panic selling
- Strong fundamentals provide stability

## Implementation Details

### Weight Selection Logic

```python
def _get_dynamic_weights(market_context):
    if not market_context:
        return static_config_weights  # Fallback
    
    market_state = market_context.market_state.lower()
    
    if market_state == "bullish":
        return {
            'sentiment': 0.30,
            'technical': 0.40,
            'fundamental': 0.30,
            'source': 'dynamic-bullish'
        }
    elif market_state == "neutral":
        return {
            'sentiment': 0.25,
            'technical': 0.35,
            'fundamental': 0.40,
            'source': 'dynamic-neutral'
        }
    elif market_state == "bearish":
        return {
            'sentiment': 0.15,
            'technical': 0.35,
            'fundamental': 0.50,
            'source': 'dynamic-bearish'
        }
    elif market_state == "volatile":
        return {
            'sentiment': 0.15,
            'technical': 0.35,
            'fundamental': 0.50,
            'source': 'dynamic-volatile'
        }
    else:
        return static_config_weights  # Unknown state
```

### Weight Application

Dynamic weights are applied in:
1. **Raw Score Calculation**
   ```python
   raw_score = (
       sentiment_score * sentiment_weight +
       technical_score * technical_weight +
       fundamental_score * fundamental_weight
   )
   ```

2. **Individual Contributions**
   ```python
   sentiment_contribution = sentiment_score * sentiment_weight
   technical_contribution = technical_score * technical_weight
   fundamental_contribution = fundamental_score * fundamental_weight
   ```

3. **Net Impact Display**
   - Each analyzer's impact is calculated using dynamic weights
   - Displayed in confidence breakdown table

4. **Final Recommendation**
   - Action (BUY/SELL/HOLD) determined from weighted score
   - Confidence calculation uses weighted contributions

### Fallback Mechanism

Static config weights are used only when:
1. No market context available (API failure)
2. Unknown market state
3. Dynamic system fails

**Logging**: Always logs weight source:
- `dynamic-bullish` - Bullish market weights
- `dynamic-neutral` - Neutral market weights
- `dynamic-bearish` - Bearish market weights
- `dynamic-volatile` - Volatile market weights
- `static` - No market context
- `static-fallback` - Unknown market state

## Real-World Examples

### Example 1: SBI in Bearish Market

**Market Context**:
- Nifty 50: Bearish (₹25,049)
- Bank Nifty: Bearish (₹58,473)
- VIX: Low (14.19)
- Market State: BEARISH

**Analyzer Scores**:
- Sentiment: +0.30 (Bullish)
- Technical: +0.49 (Bullish)
- Fundamental: +0.59 (Bullish)

**Old Weights (50/30/20)**:
```
Sentiment:     +0.30 × 0.50 = +0.150
Technical:     +0.49 × 0.30 = +0.147
Fundamental:   +0.59 × 0.20 = +0.118
Raw Score:                    +0.415
```

**New Weights (15/35/50)**:
```
Sentiment:     +0.30 × 0.15 = +0.045
Technical:     +0.49 × 0.35 = +0.172
Fundamental:   +0.59 × 0.50 = +0.295
Raw Score:                    +0.512
```

**Impact**: Raw score increased from +0.415 to +0.512 because fundamentals (strongest signal) now have higher weight.

### Example 2: ICICI in Bearish Market

**Market Context**:
- Market State: BEARISH

**Analyzer Scores**:
- Sentiment: +0.19 (Neutral)
- Technical: -0.42 (Bearish)
- Fundamental: +0.22 (Bullish)

**Old Weights (50/30/20)**:
```
Sentiment:     +0.19 × 0.50 = +0.095
Technical:     -0.42 × 0.30 = -0.126
Fundamental:   +0.22 × 0.20 = +0.044
Raw Score:                    +0.013
```

**New Weights (15/35/50)**:
```
Sentiment:     +0.19 × 0.15 = +0.029
Technical:     -0.42 × 0.35 = -0.147
Fundamental:   +0.22 × 0.50 = +0.110
Raw Score:                    -0.008
```

**Impact**: Raw score changed from +0.013 to -0.008, flipping from slightly positive to slightly negative. This is correct because:
- Technical is strongly bearish (-0.42)
- Fundamental is only weakly bullish (+0.22)
- In bearish markets, we trust fundamentals more, but weak fundamentals don't overcome strong bearish technicals

### Example 3: HDFC Bank (Oversold)

**Market Context**:
- Market State: BEARISH

**Analyzer Scores**:
- Sentiment: -0.11 (Neutral)
- Technical: -0.14 (Bearish, but oversold)
- Fundamental: +0.22 (Bullish)

**New Weights (15/35/50)**:
```
Sentiment:     -0.11 × 0.15 = -0.017
Technical:     -0.14 × 0.35 = -0.049
Fundamental:   +0.22 × 0.50 = +0.110
Raw Score:                    +0.044
```

**Impact**: Despite bearish technical and neutral sentiment, the strong fundamental weight (50%) keeps the raw score positive, identifying this as a potential value opportunity in oversold conditions.

## Display Format

### Active Weights Section
```
⚖️  Active Weights
 (Bearish Market - Dynamic)
                      
  Sentiment:     15%  
  Technical:     35%  
  Fundamental:   50%  
```

**Labels**:
- `(Bullish Market - Dynamic)` - Bullish weights applied
- `(Neutral Market - Dynamic)` - Neutral weights applied
- `(Bearish Market - Dynamic)` - Bearish weights applied
- `(Volatile Market - Dynamic)` - Volatile weights applied
- `(Static Config)` - No market context
- `(Static Fallback - No Market Data)` - Unknown state

## Benefits

### 1. Market-Adaptive Strategy
- Automatically adjusts to market conditions
- No manual intervention required
- Responds to regime changes

### 2. Risk Management
- Emphasizes fundamentals in risky markets
- Reduces sentiment weight during panic
- Focuses on quality during downturns

### 3. Opportunity Identification
- Leverages momentum in bull markets
- Identifies value in bear markets
- Balances factors in neutral markets

### 4. Transparency
- Shows exact weights being used
- Displays weight source (dynamic/static)
- Clear calculation trail

### 5. Consistency
- Same logic applied to all stocks
- Predictable behavior
- Easy to understand and validate

## Testing

### Test Coverage
1. ✅ Bullish market weights (30/40/30)
2. ✅ Neutral market weights (25/35/40)
3. ✅ Bearish market weights (15/35/50)
4. ✅ Volatile market weights (15/35/50)
5. ✅ No market context fallback (static)
6. ✅ Weights sum to 1.0 for all states
7. ✅ Bearish emphasizes fundamentals over sentiment

### Validation
- All 7 tests passing
- Real-world validation with SBI, ICICI, HDFC
- Calculations verified manually
- Logging confirms correct weight selection

## Configuration

### Static Fallback Weights
Defined in `src/config.py`:
```python
sentiment_weight: float = 0.50
technical_weight: float = 0.30
fundamental_weight: float = 0.20
```

**Used only when**:
- Market context unavailable
- Unknown market state
- Dynamic system fails

### Market State Detection
Defined in `src/market_context_analyzer.py`:
- Bullish: Nifty/Bank Nifty above MAs, low VIX
- Neutral: Mixed signals, moderate VIX
- Bearish: Nifty/Bank Nifty below MAs
- Volatile: High VIX (>25)

## Files Modified

### Core Components
- `src/recommendation_engine.py`
  - Added `_get_dynamic_weights()` method
  - Updated `generate_recommendation()` to use dynamic weights
  - Added weight source logging

- `src/models.py`
  - Added `source` field to runtime_weights dict

- `src/cli.py`
  - Updated weight display to show source
  - Enhanced labels with market context

### Testing
- `tests/test_dynamic_weights.py` (new)
  - 7 comprehensive test cases
  - All market states covered
  - Validation of calculations

### Documentation
- `DYNAMIC_WEIGHTING_SYSTEM.md` (this file)

## Future Enhancements

### Potential Improvements
1. **Sector-Specific Weights**: Different weights for different sectors
2. **Volatility-Adjusted Weights**: Fine-tune based on VIX levels
3. **Momentum Indicators**: Adjust technical weight based on trend strength
4. **Machine Learning**: Learn optimal weights from historical performance
5. **User Overrides**: Allow manual weight adjustment for specific scenarios

### Advanced Features
1. **Gradual Transitions**: Smooth weight changes during regime shifts
2. **Confidence-Based Adjustment**: Adjust weights based on analyzer confidence
3. **Historical Backtesting**: Validate weight effectiveness over time
4. **Multi-Timeframe Analysis**: Different weights for different timeframes

## Conclusion

The dynamic weighting system provides:
- ✅ Automatic market adaptation
- ✅ Risk-aware weight distribution
- ✅ Complete transparency
- ✅ Consistent application
- ✅ Comprehensive testing
- ✅ Clear documentation

This enhancement makes the recommendation engine more intelligent and adaptive, automatically adjusting its strategy based on market conditions without manual intervention.

**Key Principle**: In uncertain markets (bearish/volatile), trust fundamentals. In trending markets (bullish), follow momentum. In neutral markets, seek value.
