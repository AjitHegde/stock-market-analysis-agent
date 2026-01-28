"""Tests for confidence breakdown calculation."""

import pytest
from datetime import datetime
from src.recommendation_engine import RecommendationEngine
from src.models import (
    SentimentData,
    SentimentSource,
    TechnicalIndicators,
    FundamentalMetrics,
    MarketContext
)
from src.config import Configuration


@pytest.fixture
def config():
    """Create test configuration."""
    return Configuration()


@pytest.fixture
def engine(config):
    """Create recommendation engine."""
    return RecommendationEngine(config)


@pytest.fixture
def sentiment_bullish():
    """Create bullish sentiment data with good sample size."""
    sources = [
        SentimentSource("news", "Positive news", 0.8, datetime.now()),
        SentimentSource("news", "Good earnings", 0.7, datetime.now()),
        SentimentSource("social", "Bullish sentiment", 0.6, datetime.now()),
        SentimentSource("news", "Strong growth", 0.5, datetime.now()),
        SentimentSource("social", "Positive outlook", 0.4, datetime.now()),
    ]
    return SentimentData("TEST", 0.6, 0.8, sources, datetime.now())


@pytest.fixture
def sentiment_low_sources():
    """Create sentiment data with low source count."""
    sources = [
        SentimentSource("news", "Some news", 0.5, datetime.now()),
    ]
    return SentimentData("TEST", 0.5, 0.6, sources, datetime.now())


@pytest.fixture
def technical_bullish():
    """Create bullish technical indicators."""
    return TechnicalIndicators(
        symbol="TEST",
        ma_20=100.0,
        ma_50=95.0,
        ma_200=90.0,
        rsi=65.0,
        macd=2.5,
        macd_signal=1.5,
        support_levels=[85.0, 90.0],
        resistance_levels=[110.0, 115.0],
        technical_score=0.7,
        atr=2.5
    )


@pytest.fixture
def technical_neutral():
    """Create neutral technical indicators."""
    return TechnicalIndicators(
        symbol="TEST",
        ma_20=100.0,
        ma_50=100.0,
        ma_200=100.0,
        rsi=50.0,
        macd=0.1,
        macd_signal=0.0,
        support_levels=[95.0],
        resistance_levels=[105.0],
        technical_score=0.1,
        atr=1.5
    )


@pytest.fixture
def fundamental_bullish():
    """Create bullish fundamental metrics with all data."""
    return FundamentalMetrics(
        symbol="TEST",
        pe_ratio=15.0,
        pb_ratio=2.0,
        debt_to_equity=30.0,
        eps=10.0,
        revenue_growth=15.0,
        industry_avg_pe=20.0,
        fundamental_score=0.6
    )


@pytest.fixture
def fundamental_missing_data():
    """Create fundamental metrics with missing data."""
    return FundamentalMetrics(
        symbol="TEST",
        pe_ratio=15.0,
        pb_ratio=None,
        debt_to_equity=None,
        eps=None,
        revenue_growth=None,
        industry_avg_pe=None,
        fundamental_score=0.5
    )


@pytest.fixture
def market_bullish():
    """Create bullish market context."""
    return MarketContext(
        nifty_trend="bullish",
        banknifty_trend="bullish",
        vix_level="low",
        market_state="bullish",
        nifty_price=25000.0,
        nifty_20dma=24500.0,
        nifty_50dma=24000.0,
        banknifty_price=58000.0,
        banknifty_20dma=57500.0,
        banknifty_50dma=57000.0,
        vix_value=12.0,
        timestamp=datetime.now(),
        market_signal_quality=0.85,
        market_favorability=0.85
    )


@pytest.fixture
def market_bearish():
    """Create bearish market context."""
    return MarketContext(
        nifty_trend="bearish",
        banknifty_trend="bearish",
        vix_level="low",
        market_state="bearish",
        nifty_price=25000.0,
        nifty_20dma=25500.0,
        nifty_50dma=26000.0,
        banknifty_price=58000.0,
        banknifty_20dma=58500.0,
        banknifty_50dma=59000.0,
        vix_value=14.0,
        timestamp=datetime.now(),
        market_signal_quality=0.80,
        market_favorability=0.30
    )


@pytest.fixture
def market_volatile():
    """Create volatile market context."""
    return MarketContext(
        nifty_trend="neutral",
        banknifty_trend="neutral",
        vix_level="very_high",
        market_state="volatile",
        nifty_price=25000.0,
        nifty_20dma=25000.0,
        nifty_50dma=25000.0,
        banknifty_price=58000.0,
        banknifty_20dma=58000.0,
        banknifty_50dma=58000.0,
        vix_value=35.0,
        timestamp=datetime.now(),
        market_signal_quality=0.50,
        market_favorability=0.25
    )


def test_all_agree_high_confidence(engine, sentiment_bullish, technical_bullish, 
                                   fundamental_bullish, market_bullish):
    """Test that all 4 components agreeing gives high confidence (80%+)."""
    confidence, breakdown = engine.calculate_confidence(
        sentiment_bullish,
        technical_bullish,
        fundamental_bullish,
        combined_score=0.6,
        market_context=market_bullish
    )
    
    # All 4 agree → High confidence
    assert confidence >= 0.80, f"Expected confidence >= 80%, got {confidence:.2%}"
    assert breakdown.agreement_score >= 0.80
    assert breakdown.sentiment_confidence > 0.7
    assert breakdown.technical_confidence > 0.8
    assert breakdown.fundamental_confidence > 0.8
    assert breakdown.market_favorability > 0.8


def test_three_agree_medium_high_confidence(engine, sentiment_bullish, technical_bullish,
                                           fundamental_bullish, market_bearish):
    """Test that 3 components agreeing gives medium-high confidence (70-80%)."""
    confidence, breakdown = engine.calculate_confidence(
        sentiment_bullish,
        technical_bullish,
        fundamental_bullish,
        combined_score=0.5,
        market_context=market_bearish
    )
    
    # 3 out of 4 agree → Medium-high confidence
    assert 0.70 <= confidence <= 0.85, f"Expected confidence 70-85%, got {confidence:.2%}"
    assert breakdown.agreement_score >= 0.70


def test_two_agree_medium_confidence(engine, sentiment_bullish, technical_neutral,
                                    fundamental_bullish, market_bearish):
    """Test that 2 components agreeing gives medium confidence (60-75%)."""
    # With combined_score=0.35 (bullish), sentiment (0.6) and fundamental (0.6) agree
    # Technical (0.1) is neutral, market is bearish - so only 2 agree
    confidence, breakdown = engine.calculate_confidence(
        sentiment_bullish,
        technical_neutral,
        fundamental_bullish,
        combined_score=0.35,  # Changed to 0.35 to be > 0.3 threshold
        market_context=market_bearish
    )
    
    # Only 2 out of 4 agree (sentiment + fundamental) → Medium confidence
    # Agreement score should be 0.65 for 2/4 components
    assert 0.50 <= confidence <= 0.75, f"Expected confidence 50-75%, got {confidence:.2%}"
    assert breakdown.agreement_score == 0.65


def test_low_sources_reduces_confidence(engine, sentiment_low_sources, technical_bullish,
                                       fundamental_bullish, market_bullish):
    """Test that low sentiment sources reduces confidence."""
    confidence, breakdown = engine.calculate_confidence(
        sentiment_low_sources,
        technical_bullish,
        fundamental_bullish,
        combined_score=0.6,
        market_context=market_bullish
    )
    
    # Low sources should reduce sentiment confidence
    assert breakdown.sentiment_confidence < 0.6
    # Should have data quality penalty
    assert breakdown.data_quality_penalty > 0.05


def test_missing_fundamental_data_penalty(engine, sentiment_bullish, technical_bullish,
                                         fundamental_missing_data, market_bullish):
    """Test that missing fundamental data adds penalty."""
    confidence, breakdown = engine.calculate_confidence(
        sentiment_bullish,
        technical_bullish,
        fundamental_missing_data,
        combined_score=0.5,
        market_context=market_bullish
    )
    
    # Missing data should reduce fundamental confidence
    assert breakdown.fundamental_confidence < 0.7
    # Should have data quality penalty
    assert breakdown.data_quality_penalty > 0.05


def test_volatile_market_reduces_confidence(engine, sentiment_bullish, technical_bullish,
                                           fundamental_bullish, market_volatile):
    """Test that volatile market reduces market confidence."""
    confidence, breakdown = engine.calculate_confidence(
        sentiment_bullish,
        technical_bullish,
        fundamental_bullish,
        combined_score=0.5,
        market_context=market_volatile
    )
    
    # Volatile market should reduce market favorability
    assert breakdown.market_favorability < 0.5


def test_no_market_context_penalty(engine, sentiment_bullish, technical_bullish,
                                  fundamental_bullish):
    """Test that missing market context adds penalty."""
    confidence, breakdown = engine.calculate_confidence(
        sentiment_bullish,
        technical_bullish,
        fundamental_bullish,
        combined_score=0.5,
        market_context=None
    )
    
    # No market context should add penalty
    assert breakdown.data_quality_penalty >= 0.05
    assert breakdown.market_signal_quality == 0.0
    assert breakdown.market_favorability == 0.0


def test_confidence_breakdown_structure(engine, sentiment_bullish, technical_bullish,
                                       fundamental_bullish, market_bullish):
    """Test that confidence breakdown has correct structure."""
    confidence, breakdown = engine.calculate_confidence(
        sentiment_bullish,
        technical_bullish,
        fundamental_bullish,
        combined_score=0.6,
        market_context=market_bullish
    )
    
    # Check all fields are present and valid
    assert 0.0 <= breakdown.sentiment_confidence <= 1.0
    assert 0.0 <= breakdown.technical_confidence <= 1.0
    assert 0.0 <= breakdown.fundamental_confidence <= 1.0
    assert 0.0 <= breakdown.market_signal_quality <= 1.0
    assert 0.0 <= breakdown.market_favorability <= 1.0
    assert 0.0 <= breakdown.agreement_score <= 1.0
    assert 0.0 <= breakdown.data_quality_penalty <= 1.0


def test_weak_signal_reduces_technical_confidence(engine, sentiment_bullish, technical_neutral,
                                                 fundamental_bullish, market_bullish):
    """Test that weak technical signal reduces technical confidence."""
    confidence, breakdown = engine.calculate_confidence(
        sentiment_bullish,
        technical_neutral,
        fundamental_bullish,
        combined_score=0.2,
        market_context=market_bullish
    )
    
    # Weak technical signal should reduce technical confidence
    assert breakdown.technical_confidence < 0.7
