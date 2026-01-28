# Confidence Calculation Refactor Summary

## Overview
Refactored the confidence calculation to use a weighted agreement score between all four analysis components (Sentiment, Technical, Fundamental, and Market Context).

## Changes Made

### 1. New Confidence Calculation Logic

**Agreement-Based Scoring:**
- All 4 components agree → High confidence (80%+)
- 3 components agree → Medium-high (70-80%)
- 2 components agree → Medium (60-75%)
- 1 component agrees → Low (<50%)

**Agreement Determination:**
- For bullish signals: component score > 0.2
- For bearish signals: component score < -0.2
- For neutral signals: -0.2 ≤ component score ≤ 0.2
- Market context: checks if market state aligns with signal direction

### 2. Individual Component Confidence

**Sentiment Confidence:**
- Base: Uses sentiment.confidence value
- Penalty: -30% for < 2 sources
- Boost: +10% for ≥ 5 sources

**Technical Confidence:**
- Strong signal (|score| > 0.6): 95%
- Moderate signal (|score| > 0.2): 80%
- Weak signal (|score| ≤ 0.2): 50%

**Fundamental Confidence:**
- All metrics available: 90%
- Some metrics missing: 70%
- Many metrics missing (≥2): 50%

**Market Confidence:**
- Low VIX (calm): 90%
- Moderate VIX: 75%
- High VIX: 60%
- Very high VIX (volatile): 40%

### 3. Data Quality Penalties

Reduces confidence for:
- Missing market context: -5%
- Low sentiment sources (< 2): -10%
- Low sentiment sources (< 3): -5%
- Missing fundamental data (≥2 metrics): -10%
- Missing fundamental data (1 metric): -5%
- API failures (zero sentiment with no sources): -15%

Maximum penalty capped at 30%.

### 4. Final Confidence Formula

```
confidence = (
    agreement_score * 0.6 +      # Agreement is most important
    sentiment_conf * 0.15 +       # Individual confidences
    technical_conf * 0.10 +
    fundamental_conf * 0.10 +
    market_conf * 0.05
) * (1.0 - data_quality_penalty)
```

### 5. New Data Models

**ConfidenceBreakdown** (added to `src/models.py`):
```python
@dataclass
class ConfidenceBreakdown:
    sentiment_confidence: float
    technical_confidence: float
    fundamental_confidence: float
    market_confidence: float
    agreement_score: float
    data_quality_penalty: float
```

**Updated Recommendation** model:
- Added `confidence_breakdown: Optional[ConfidenceBreakdown]` field

### 6. CLI Display

New "🔍 Confidence Breakdown" section shows:
- Sentiment: XX%
- Technical: XX%
- Fundamental: XX%
- Market: XX%
- Agreement Score: XX% (color-coded: green ≥75%, yellow ≥60%, red <60%)
- Data Quality Penalty: -XX% (if any)

## Example Output

```
🎯 Recommendation
  Action:       HOLD
  Confidence:   70.30%

🔍 Confidence Breakdown
  Sentiment:              40%
  Technical:              95%
  Fundamental:            90%
  Market:                 90%
  Agreement Score:        75%
  Data Quality Penalty:   -5%
```

## Test Coverage

Created comprehensive test suite (`tests/test_confidence_breakdown.py`) with 9 tests:
1. All 4 components agree → High confidence
2. 3 components agree → Medium-high confidence
3. 2 components agree → Medium confidence
4. Low sentiment sources reduces confidence
5. Missing fundamental data adds penalty
6. Volatile market reduces market confidence
7. Missing market context adds penalty
8. Confidence breakdown structure validation
9. Weak technical signal reduces technical confidence

All tests passing ✅

## Benefits

1. **Transparency**: Users can see exactly why confidence is high or low
2. **Agreement-based**: More intuitive than standard deviation approach
3. **Data quality awareness**: Explicitly penalizes missing data and API failures
4. **Component visibility**: Shows individual component confidence levels
5. **Market integration**: Market context now properly influences confidence

## Files Modified

- `src/models.py` - Added ConfidenceBreakdown, updated Recommendation
- `src/recommendation_engine.py` - Refactored calculate_confidence method
- `src/cli.py` - Added confidence breakdown display
- `tests/test_confidence_breakdown.py` - New comprehensive test suite
- `tests/test_recommendation_engine.py` - Updated existing tests

## Test Results

- Total tests: 248
- Passed: 245
- Failed: 3 (unrelated to confidence refactoring)
- Success rate: 98.8%
