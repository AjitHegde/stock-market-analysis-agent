"""Tests for dynamic weight adjustment based on market conditions."""

import pytest
from datetime import datetime
from src.recommendation_engine import RecommendationEngine
from src.config import Configuration
from src.models import (
    SentimentData, TechnicalIndicators, FundamentalMetrics,
    MarketContext, SentimentSource
)


class TestDynamicWeights:
    """Test dynamic weight adjustment based on market conditions."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Configuration()
    
    @pytest.fixture
    def engine(self, config):
        """Create recommendation engine."""
        return RecommendationEngine(config)
    
    @pytest.fixture
    def sentiment(self):
        """Create test sentiment data."""
        return SentimentData(
            symbol="TEST",
            sentiment_score=0.5,
            confidence=0.8,
            sources=[
                SentimentSource(
                    source_type="news",
                    content="Test article",
                    score=0.5,
                    timestamp=datetime.now()
                )
            ],
            timestamp=datetime.now(),
            direction="bullish",
            strength=0.5
        )
    
    @pytest.fixture
    def technical(self):
        """Create test technical indicators."""
        return TechnicalIndicators(
            symbol="TEST",
            ma_20=100.0,
            ma_50=95.0,
            ma_200=90.0,
            rsi=60.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[85.0],
            resistance_levels=[105.0],
            technical_score=0.3,
            atr=2.0,
            direction="bullish",
            strength=0.3,
            confidence=0.8,
            regime="bullish-trend"
        )
    
    @pytest.fixture
    def fundamental(self):
        """Create test fundamental metrics."""
        return FundamentalMetrics(
            symbol="TEST",
            pe_ratio=15.0,
            pb_ratio=2.0,
            fundamental_score=0.4,
            direction="bullish",
            strength=0.4,
            confidence=0.9
        )
    
    def test_bullish_market_weights(self, engine, sentiment, technical, fundamental):
        """Test weights in bullish market."""
        market_context = MarketContext(
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
            market_signal_quality=0.9,
            market_favorability=0.9
        )
        
        recommendation = engine.generate_recommendation(
            sentiment, technical, fundamental, 100.0, market_context
        )
        
        # Check weights
        assert recommendation.runtime_weights['sentiment'] == 0.30
        assert recommendation.runtime_weights['technical'] == 0.40
        assert recommendation.runtime_weights['fundamental'] == 0.30
        assert recommendation.runtime_weights['source'] == 'dynamic-bullish'
        
        # Verify calculation
        expected_score = (
            sentiment.sentiment_score * 0.30 +
            technical.technical_score * 0.40 +
            fundamental.fundamental_score * 0.30
        )
        
        actual_score = (
            recommendation.sentiment_contribution +
            recommendation.technical_contribution +
            recommendation.fundamental_contribution
        )
        
        assert abs(actual_score - expected_score) < 0.001
    
    def test_neutral_market_weights(self, engine, sentiment, technical, fundamental):
        """Test weights in neutral market."""
        market_context = MarketContext(
            nifty_trend="neutral",
            banknifty_trend="neutral",
            vix_level="moderate",
            market_state="neutral",
            nifty_price=25000.0,
            nifty_20dma=25000.0,
            nifty_50dma=25000.0,
            banknifty_price=58000.0,
            banknifty_20dma=58000.0,
            banknifty_50dma=58000.0,
            vix_value=18.0,
            timestamp=datetime.now(),
            market_signal_quality=0.7,
            market_favorability=0.7
        )
        
        recommendation = engine.generate_recommendation(
            sentiment, technical, fundamental, 100.0, market_context
        )
        
        # Check weights
        assert recommendation.runtime_weights['sentiment'] == 0.25
        assert recommendation.runtime_weights['technical'] == 0.35
        assert recommendation.runtime_weights['fundamental'] == 0.40
        assert recommendation.runtime_weights['source'] == 'dynamic-neutral'
        
        # Verify calculation
        expected_score = (
            sentiment.sentiment_score * 0.25 +
            technical.technical_score * 0.35 +
            fundamental.fundamental_score * 0.40
        )
        
        actual_score = (
            recommendation.sentiment_contribution +
            recommendation.technical_contribution +
            recommendation.fundamental_contribution
        )
        
        assert abs(actual_score - expected_score) < 0.001
    
    def test_bearish_market_weights(self, engine, sentiment, technical, fundamental):
        """Test weights in bearish market."""
        market_context = MarketContext(
            nifty_trend="bearish",
            banknifty_trend="bearish",
            vix_level="moderate",
            market_state="bearish",
            nifty_price=24000.0,
            nifty_20dma=24500.0,
            nifty_50dma=25000.0,
            banknifty_price=57000.0,
            banknifty_20dma=57500.0,
            banknifty_50dma=58000.0,
            vix_value=20.0,
            timestamp=datetime.now(),
            market_signal_quality=0.6,
            market_favorability=0.4
        )
        
        recommendation = engine.generate_recommendation(
            sentiment, technical, fundamental, 100.0, market_context
        )
        
        # Check weights
        assert recommendation.runtime_weights['sentiment'] == 0.15
        assert recommendation.runtime_weights['technical'] == 0.35
        assert recommendation.runtime_weights['fundamental'] == 0.50
        assert recommendation.runtime_weights['source'] == 'dynamic-bearish'
        
        # Verify calculation
        expected_score = (
            sentiment.sentiment_score * 0.15 +
            technical.technical_score * 0.35 +
            fundamental.fundamental_score * 0.50
        )
        
        actual_score = (
            recommendation.sentiment_contribution +
            recommendation.technical_contribution +
            recommendation.fundamental_contribution
        )
        
        assert abs(actual_score - expected_score) < 0.001
    
    def test_volatile_market_weights(self, engine, sentiment, technical, fundamental):
        """Test weights in volatile market."""
        market_context = MarketContext(
            nifty_trend="neutral",
            banknifty_trend="neutral",
            vix_level="high",
            market_state="volatile",
            nifty_price=25000.0,
            nifty_20dma=25000.0,
            nifty_50dma=25000.0,
            banknifty_price=58000.0,
            banknifty_20dma=58000.0,
            banknifty_50dma=58000.0,
            vix_value=28.0,
            timestamp=datetime.now(),
            market_signal_quality=0.5,
            market_favorability=0.3
        )
        
        recommendation = engine.generate_recommendation(
            sentiment, technical, fundamental, 100.0, market_context
        )
        
        # Check weights (volatile uses same as bearish)
        assert recommendation.runtime_weights['sentiment'] == 0.15
        assert recommendation.runtime_weights['technical'] == 0.35
        assert recommendation.runtime_weights['fundamental'] == 0.50
        assert recommendation.runtime_weights['source'] == 'dynamic-volatile'
    
    def test_no_market_context_fallback(self, engine, sentiment, technical, fundamental):
        """Test fallback to static weights when no market context."""
        recommendation = engine.generate_recommendation(
            sentiment, technical, fundamental, 100.0, None
        )
        
        # Should use static config weights
        assert recommendation.runtime_weights['sentiment'] == engine.config.sentiment_weight
        assert recommendation.runtime_weights['technical'] == engine.config.technical_weight
        assert recommendation.runtime_weights['fundamental'] == engine.config.fundamental_weight
        assert recommendation.runtime_weights['source'] == 'static'
    
    def test_weights_sum_to_one(self, engine, sentiment, technical, fundamental):
        """Test that weights always sum to 1.0."""
        market_states = ["bullish", "neutral", "bearish", "volatile"]
        
        for state in market_states:
            market_context = MarketContext(
                nifty_trend=state,
                banknifty_trend=state,
                vix_level="moderate",
                market_state=state,
                nifty_price=25000.0,
                nifty_20dma=25000.0,
                nifty_50dma=25000.0,
                banknifty_price=58000.0,
                banknifty_20dma=58000.0,
                banknifty_50dma=58000.0,
                vix_value=18.0,
                timestamp=datetime.now(),
                market_signal_quality=0.7,
                market_favorability=0.7
            )
            
            recommendation = engine.generate_recommendation(
                sentiment, technical, fundamental, 100.0, market_context
            )
            
            total_weight = (
                recommendation.runtime_weights['sentiment'] +
                recommendation.runtime_weights['technical'] +
                recommendation.runtime_weights['fundamental']
            )
            
            assert abs(total_weight - 1.0) < 0.001, f"Weights don't sum to 1.0 for {state} market"
    
    def test_bearish_market_emphasizes_fundamentals(self, engine, sentiment, technical, fundamental):
        """Test that bearish market gives more weight to fundamentals."""
        # Create bearish market context
        bearish_context = MarketContext(
            nifty_trend="bearish",
            banknifty_trend="bearish",
            vix_level="moderate",
            market_state="bearish",
            nifty_price=24000.0,
            nifty_20dma=24500.0,
            nifty_50dma=25000.0,
            banknifty_price=57000.0,
            banknifty_20dma=57500.0,
            banknifty_50dma=58000.0,
            vix_value=20.0,
            timestamp=datetime.now(),
            market_signal_quality=0.6,
            market_favorability=0.4
        )
        
        # Create bullish market context
        bullish_context = MarketContext(
            nifty_trend="bullish",
            banknifty_trend="bullish",
            vix_level="low",
            market_state="bullish",
            nifty_price=26000.0,
            nifty_20dma=25500.0,
            nifty_50dma=25000.0,
            banknifty_price=59000.0,
            banknifty_20dma=58500.0,
            banknifty_50dma=58000.0,
            vix_value=12.0,
            timestamp=datetime.now(),
            market_signal_quality=0.9,
            market_favorability=0.9
        )
        
        bearish_rec = engine.generate_recommendation(
            sentiment, technical, fundamental, 100.0, bearish_context
        )
        
        bullish_rec = engine.generate_recommendation(
            sentiment, technical, fundamental, 100.0, bullish_context
        )
        
        # Bearish should have higher fundamental weight
        assert bearish_rec.runtime_weights['fundamental'] > bullish_rec.runtime_weights['fundamental']
        
        # Bearish should have lower sentiment weight
        assert bearish_rec.runtime_weights['sentiment'] < bullish_rec.runtime_weights['sentiment']
