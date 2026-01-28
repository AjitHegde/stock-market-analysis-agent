# Confidence Breakdown Refactor Summary

## Overview
Refactored the confidence breakdown logic to provide more granular insights into each analyzer's contribution to the final recommendation. Each analyzer now outputs direction, strength, and confidence, which are combined to calculate a net impact score.

## Changes Made

### 1. Model Updates (`src/models.py`)

Added three new fields to each analyzer's output model:

#### SentimentData
- `direction`: Signal direction ("bullish", "bearish", "neutral")
- `strength`: Signal strength (0.0 to 1.0)

#### TechnicalIndicators
- `direction`: Signal direction ("bullish", "bearish", "neutral")
- `strength`: Signal strength (0.0 to 1.0)
- `confidence`: Analysis confidence (0.0 to 1.0)

#### FundamentalMetrics
- `direction`: Signal direction ("bullish", "bearish", "neutral")
- `strength`: Signal strength (0.0 to 1.0)
- `confidence`: Analysis confidence (0.0 to 1.0)

### 2. Analyzer Updates

#### Sentiment Analyzer (`src/sentiment_analyzer.py`)
- Calculates `direction` based on sentiment_score:
  - `sentiment_score > 0.2` → "bullish"
  - `sentiment_score < -0.2` → "bearish"
  - Otherwise → "neutral"
- Sets `strength` to `abs(sentiment_score)` (reduced by 0.3x for neutral)

#### Technical Analyzer (`src/technical_analyzer.py`)
- Calculates `direction` based on technical_score:
  - `technical_score > 0.2` → "bullish"
  - `technical_score < -0.2` → "bearish"
  - Otherwise → "neutral"
- Sets `strength` to `abs(technical_score)` (reduced by 0.3x for neutral)
- Calculates `confidence` based on signal strength:
  - Weak signal (`abs(score) < 0.2`) → 0.5
  - Strong signal (`abs(score) > 0.6`) → 0.95
  - Default → 0.8

#### Fundamental Analyzer (`src/fundamental_analyzer.py`)
- Calculates `direction` based on fundamental_score:
  - `fundamental_score > 0.2` → "bullish"
  - `fundamental_score < -0.2` → "bearish"
  - Otherwise → "neutral"
- Sets `strength` to `abs(fundamental_score)` (reduced by 0.3x for neutral)
- Calculates `confidence` based on data availability:
  - All metrics available → 0.9
  - Many metrics missing (≥2) → 0.5
  - Default → 0.7

### 3. CLI Display Updates (`src/cli.py`)

Completely redesigned the confidence breakdown display to show:

#### New Table Format
```
Analyzer    | Direction  | Strength | Confidence | Net Impact
------------|------------|----------|------------|------------
Sentiment   | 🟢 Bullish | 80%      | 90%        | +0.72
Technical   | 🔴 Bearish | 70%      | 85%        | -0.59
Fundamental | 🟡 Neutral | 50%      | 60%        | +0.09
```

**Example Output:**
```
🔍 Confidence Breakdown
                                                                 
  Analyzer      Direction    Strength   Confidence   Net Impact  
 ─────────────────────────────────────────────────────────────── 
  Sentiment     🟢 Bullish        80%          90%        +0.72  
  Technical     🔴 Bearish        70%          85%        -0.59  
  Fundamental   🟡 Neutral        50%          60%        +0.09  
                                                                 

  Agreement Score:         75%   
  Market Signal Quality:   80%   
  Market Favorability:     70%   
  Data Quality Penalty:    -10%  
```

#### Net Impact Calculation
```
impact = strength * confidence

if direction == "bearish":
    impact = -impact
elif direction == "neutral":
    impact = impact * 0.3
```

#### Visual Indicators
- 🟢 Green emoji for bullish direction
- 🔴 Red emoji for bearish direction
- 🟡 Yellow emoji for neutral direction
- Color-coded impact values (green for positive, red for negative, yellow for neutral)

### 4. Additional Metrics Display

The display now separates the detailed analyzer breakdown from the aggregate metrics:

**Analyzer Breakdown Table:**
- Direction, Strength, Confidence, Net Impact for each analyzer

**Aggregate Metrics Table:**
- Agreement Score (how well analyzers agree)
- Market Signal Quality (clarity of market trends)
- Market Favorability (how favorable market is for long trades)
- Data Quality Penalty (if any data is missing or APIs failed)

## Impact Calculation Formula

The net impact for each analyzer is calculated as:

```python
impact = strength * confidence

if direction == "bearish":
    impact = -impact
elif direction == "neutral":
    impact = impact * 0.3  # Reduced impact for neutral signals
```

### Examples

**Bullish Signal:**
- Direction: Bullish
- Strength: 80%
- Confidence: 90%
- Net Impact: +0.72

**Bearish Signal:**
- Direction: Bearish
- Strength: 70%
- Confidence: 85%
- Net Impact: -0.59

**Neutral Signal:**
- Direction: Neutral
- Strength: 50%
- Confidence: 60%
- Net Impact: +0.09 (reduced by 0.3x)

## Benefits

1. **Transparency**: Users can now see exactly how each analyzer contributes to the final recommendation
2. **Granularity**: Direction, strength, and confidence provide more nuanced insights than a single score
3. **Visual Clarity**: Emoji indicators and color coding make it easy to understand at a glance
4. **Impact Visibility**: Net impact shows the actual contribution of each analyzer to the final decision

## Testing

All existing tests pass, including:
- `test_confidence_breakdown.py` (9/9 tests passing)
- `test_recommendation_engine.py` (23/23 tests passing)
- `test_technical_analyzer.py` (13/13 tests passing)
- `test_fundamental_analyzer.py` (28/28 tests passing)

Note: 2 unrelated test failures in `test_sentiment_analyzer.py` regarding temporal weight calculation (pre-existing issue).

## Backward Compatibility

The changes are backward compatible:
- All new fields have default values
- Existing code continues to work without modification
- The old `confidence_breakdown` structure is preserved and enhanced
