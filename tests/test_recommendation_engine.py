"""Unit tests for Recommendation Engine."""

import pytest
from datetime import datetime
from src.recommendation_engine import RecommendationEngine
from src.models import (
    SentimentData,
    SentimentSource,
    TechnicalIndicators,
    FundamentalMetrics,
    Recommendation
)
from src.config import Configuration


class TestRecommendationEngine:
    """Test suite for RecommendationEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create default configuration
        self.config = Configuration(
            sentiment_weight=0.5,
            technical_weight=0.3,
            fundamental_weight=0.2
        )
        self.engine = RecommendationEngine(self.config)
    
    # Test initialization and weight normalization
    
    def test_init_with_valid_weights(self):
        """Test initialization with valid weights."""
        config = Configuration(
            sentiment_weight=0.5,
            technical_weight=0.3,
            fundamental_weight=0.2
        )
        engine = RecommendationEngine(config)
        
        assert engine.config.sentiment_weight == 0.5
        assert engine.config.technical_weight == 0.3
        assert engine.config.fundamental_weight == 0.2
    
    def test_init_normalizes_weights(self):
        """Test that initialization normalizes weights if they don't sum to 1.0."""
        config = Configuration(
            sentiment_weight=0.6,
            technical_weight=0.6,
            fundamental_weight=0.6
        )
        engine = RecommendationEngine(config)
        
        # Weights should be normalized to sum to 1.0
        total = (engine.config.sentiment_weight + 
                engine.config.technical_weight + 
                engine.config.fundamental_weight)
        assert abs(total - 1.0) < 0.001
    
    # Test generate_recommendation method
    
    def test_generate_recommendation_buy(self):
        """Test BUY recommendation generation."""
        # Create bullish analysis results
        sentiment = SentimentData(
            symbol="TEST",
            sentiment_score=0.7,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=105.0,
            ma_50=100.0,
            ma_200=95.0,
            rsi=45.0,
            macd=1.5,
            macd_signal=1.0,
            support_levels=[90.0, 95.0],
            resistance_levels=[110.0, 115.0],
            technical_score=0.6
        )
        
        fundamental = FundamentalMetrics(
            symbol="TEST",
            pe_ratio=15.0,
            fundamental_score=0.5
        )
        
        current_price = 100.0
        
        recommendation = self.engine.generate_recommendation(
            sentiment, technical, fundamental, current_price
        )
        
        assert recommendation.symbol == "TEST"
        assert recommendation.action == "BUY"
        assert 0.0 <= recommendation.confidence <= 1.0
        assert recommendation.entry_price_low is not None
        assert recommendation.entry_price_high is not None
        assert recommendation.entry_price_low <= recommendation.entry_price_high
        assert recommendation.reasoning != ""
    
    def test_generate_recommendation_sell(self):
        """Test SELL recommendation generation."""
        # Create bearish analysis results
        sentiment = SentimentData(
            symbol="TEST",
            sentiment_score=-0.7,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=100.0,
            ma_200=105.0,
            rsi=75.0,
            macd=-1.5,
            macd_signal=-1.0,
            support_levels=[85.0, 90.0],
            resistance_levels=[100.0, 105.0],
            technical_score=-0.6
        )
        
        fundamental = FundamentalMetrics(
            symbol="TEST",
            pe_ratio=35.0,
            fundamental_score=-0.5
        )
        
        current_price = 100.0
        
        recommendation = self.engine.generate_recommendation(
            sentiment, technical, fundamental, current_price
        )
        
        assert recommendation.symbol == "TEST"
        assert recommendation.action == "SELL"
        assert 0.0 <= recommendation.confidence <= 1.0
        assert recommendation.exit_price_low is not None
        assert recommendation.exit_price_high is not None
        assert recommendation.exit_price_low <= recommendation.exit_price_high
        assert recommendation.reasoning != ""
    
    def test_generate_recommendation_hold(self):
        """Test HOLD recommendation generation."""
        # Create neutral analysis results
        sentiment = SentimentData(
            symbol="TEST",
            sentiment_score=0.1,
            confidence=0.7,
            sources=[],
            timestamp=datetime.now()
        )
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=100.0,
            ma_50=100.0,
            ma_200=100.0,
            rsi=50.0,
            macd=0.0,
            macd_signal=0.0,
            support_levels=[95.0],
            resistance_levels=[105.0],
            technical_score=0.0
        )
        
        fundamental = FundamentalMetrics(
            symbol="TEST",
            pe_ratio=20.0,
            fundamental_score=0.0
        )
        
        current_price = 100.0
        
        recommendation = self.engine.generate_recommendation(
            sentiment, technical, fundamental, current_price
        )
        
        assert recommendation.symbol == "TEST"
        assert recommendation.action == "HOLD"
        assert 0.0 <= recommendation.confidence <= 1.0
        assert recommendation.entry_price_low is None
        assert recommendation.entry_price_high is None
        assert recommendation.exit_price_low is None
        assert recommendation.exit_price_high is None
        assert recommendation.reasoning != ""
    
    def test_generate_recommendation_conflicting_signals(self):
        """Test recommendation with conflicting signals."""
        # Create conflicting analysis results
        sentiment = SentimentData(
            symbol="TEST",
            sentiment_score=0.8,  # Very bullish
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=100.0,
            ma_200=105.0,
            rsi=75.0,
            macd=-1.0,
            macd_signal=-0.5,
            support_levels=[90.0],
            resistance_levels=[100.0],
            technical_score=-0.7  # Very bearish
        )
        
        fundamental = FundamentalMetrics(
            symbol="TEST",
            pe_ratio=20.0,
            fundamental_score=0.0  # Neutral
        )
        
        current_price = 100.0
        
        recommendation = self.engine.generate_recommendation(
            sentiment, technical, fundamental, current_price
        )
        
        # With conflicting signals, should likely be HOLD
        # and confidence should be reduced
        assert recommendation.action == "HOLD"
        assert recommendation.confidence < 0.75  # Reduced confidence (adjusted threshold)
        assert "conflicting" in recommendation.reasoning.lower() or "conflict" in recommendation.reasoning.lower()
    
    def test_generate_recommendation_contributions(self):
        """Test that individual contributions are calculated correctly."""
        sentiment = SentimentData(
            symbol="TEST",
            sentiment_score=0.6,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=105.0,
            ma_50=100.0,
            ma_200=95.0,
            rsi=45.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[90.0],
            resistance_levels=[110.0],
            technical_score=0.4
        )
        
        fundamental = FundamentalMetrics(
            symbol="TEST",
            pe_ratio=18.0,
            fundamental_score=0.2
        )
        
        current_price = 100.0
        
        recommendation = self.engine.generate_recommendation(
            sentiment, technical, fundamental, current_price
        )
        
        # Check contributions
        expected_sentiment = 0.6 * 0.5  # score * weight
        expected_technical = 0.4 * 0.3
        expected_fundamental = 0.2 * 0.2
        
        assert abs(recommendation.sentiment_contribution - expected_sentiment) < 0.001
        assert abs(recommendation.technical_contribution - expected_technical) < 0.001
        assert abs(recommendation.fundamental_contribution - expected_fundamental) < 0.001
    
    # Test calculate_confidence method
    
    def test_calculate_confidence_high_agreement(self):
        """Test confidence calculation with high agreement."""
        from src.models import SentimentSource
        
        sentiment = SentimentData(
            symbol="TEST",
            sentiment_score=0.7,
            confidence=0.9,
            sources=[
                SentimentSource("news", "Positive news", 0.7, datetime.now()),
                SentimentSource("news", "Good earnings", 0.6, datetime.now()),
                SentimentSource("social", "Bullish", 0.8, datetime.now()),
            ],
            timestamp=datetime.now()
        )
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=105.0,
            ma_50=100.0,
            ma_200=95.0,
            rsi=45.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[],
            resistance_levels=[],
            technical_score=0.6
        )
        
        fundamental = FundamentalMetrics(
            symbol="TEST",
            fundamental_score=0.65
        )
        
        combined_score = 0.65
        
        confidence, breakdown = self.engine.calculate_confidence(
            sentiment, technical, fundamental, combined_score
        )
        
        # High agreement should result in high confidence
        assert confidence > 0.6
        assert 0.0 <= confidence <= 1.0
        # Check breakdown is returned
        assert breakdown is not None
        assert 0.0 <= breakdown.agreement_score <= 1.0
    
    def test_calculate_confidence_low_agreement(self):
        """Test confidence calculation with low agreement (conflicting signals)."""
        sentiment = SentimentData(
            symbol="TEST",
            sentiment_score=0.8,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=100.0,
            ma_200=105.0,
            rsi=75.0,
            macd=-1.0,
            macd_signal=-0.5,
            support_levels=[],
            resistance_levels=[],
            technical_score=-0.8
        )
        
        fundamental = FundamentalMetrics(
            symbol="TEST",
            fundamental_score=0.0
        )
        
        combined_score = 0.1
        
        confidence, breakdown = self.engine.calculate_confidence(
            sentiment, technical, fundamental, combined_score
        )
        
        # Low agreement should result in reduced confidence
        # (adjusted threshold since we use weighted average now)
        assert confidence < 0.7
        assert 0.0 <= confidence <= 1.0
        # Check breakdown is returned
        assert breakdown is not None
    
    def test_calculate_confidence_range(self):
        """Test that confidence is always within valid range."""
        # Test with various scenarios
        scenarios = [
            (0.9, 0.9, 0.9, 0.9),  # All very bullish
            (-0.9, -0.9, -0.9, -0.9),  # All very bearish
            (0.0, 0.0, 0.0, 0.0),  # All neutral
            (0.8, -0.8, 0.0, 0.0),  # Conflicting
        ]
        
        for sent_score, tech_score, fund_score, combined in scenarios:
            sentiment = SentimentData(
                symbol="TEST",
                sentiment_score=sent_score,
                confidence=0.8,
                sources=[],
                timestamp=datetime.now()
            )
            
            technical = TechnicalIndicators(
                symbol="TEST",
                ma_20=100.0,
                ma_50=100.0,
                ma_200=100.0,
                rsi=50.0,
                macd=0.0,
                macd_signal=0.0,
                support_levels=[],
                resistance_levels=[],
                technical_score=tech_score
            )
            
            fundamental = FundamentalMetrics(
                symbol="TEST",
                fundamental_score=fund_score
            )
            
            confidence, breakdown = self.engine.calculate_confidence(
                sentiment, technical, fundamental, combined
            )
            
            assert 0.0 <= confidence <= 1.0
            assert breakdown is not None
    
    # Test suggest_price_range method
    
    def test_suggest_price_range_buy_with_support(self):
        """Test price range suggestion for BUY with support levels."""
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=105.0,
            ma_50=100.0,
            ma_200=95.0,
            rsi=45.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[90.0, 95.0, 98.0],
            resistance_levels=[110.0, 115.0],
            technical_score=0.6
        )
        
        current_price = 100.0
        
        price_low, price_high = self.engine.suggest_price_range(
            "BUY", current_price, technical
        )
        
        # Should use nearest support below current price
        assert price_low == 98.0  # Nearest support
        assert price_high == current_price * 1.02
        assert price_low < price_high
    
    def test_suggest_price_range_buy_without_support(self):
        """Test price range suggestion for BUY without support levels."""
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=105.0,
            ma_50=100.0,
            ma_200=95.0,
            rsi=45.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[],
            resistance_levels=[110.0],
            technical_score=0.6
        )
        
        current_price = 100.0
        
        price_low, price_high = self.engine.suggest_price_range(
            "BUY", current_price, technical
        )
        
        # Should use default range around current price
        assert price_low == current_price * 0.98
        assert price_high == current_price * 1.02
        assert price_low < price_high
    
    def test_suggest_price_range_sell_with_resistance(self):
        """Test price range suggestion for SELL with resistance levels."""
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=100.0,
            ma_200=105.0,
            rsi=75.0,
            macd=-1.0,
            macd_signal=-0.5,
            support_levels=[85.0, 90.0],
            resistance_levels=[102.0, 110.0, 115.0],
            technical_score=-0.6
        )
        
        current_price = 100.0
        
        price_low, price_high = self.engine.suggest_price_range(
            "SELL", current_price, technical
        )
        
        # Should use nearest resistance above current price
        assert price_low == current_price * 0.98
        assert price_high == 102.0  # Nearest resistance
        assert price_low < price_high
    
    def test_suggest_price_range_sell_without_resistance(self):
        """Test price range suggestion for SELL without resistance levels."""
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=100.0,
            ma_200=105.0,
            rsi=75.0,
            macd=-1.0,
            macd_signal=-0.5,
            support_levels=[85.0],
            resistance_levels=[],
            technical_score=-0.6
        )
        
        current_price = 100.0
        
        price_low, price_high = self.engine.suggest_price_range(
            "SELL", current_price, technical
        )
        
        # Should use default range around current price
        assert price_low == current_price * 0.98
        assert price_high == current_price * 1.02
        assert price_low < price_high
    
    # Test _generate_reasoning method
    
    def test_generate_reasoning_includes_all_components(self):
        """Test that reasoning includes all analysis components."""
        sentiment = SentimentData(
            symbol="TEST",
            sentiment_score=0.6,
            confidence=0.8,
            sources=[SentimentSource(
                source_type="news",
                content="Test",
                score=0.6,
                timestamp=datetime.now(),
                url="http://test.com"
            )],
            timestamp=datetime.now()
        )
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=105.0,
            ma_50=100.0,
            ma_200=95.0,
            rsi=45.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[90.0],
            resistance_levels=[110.0],
            technical_score=0.4
        )
        
        fundamental = FundamentalMetrics(
            symbol="TEST",
            pe_ratio=18.0,
            fundamental_score=0.2
        )
        
        reasoning = self.engine._generate_reasoning(
            "BUY", 0.46, sentiment, technical, fundamental, 0.75
        )
        
        # Check that reasoning includes key information
        assert "BUY" in reasoning
        assert "75%" in reasoning or "0.75" in reasoning  # Confidence
        assert "Sentiment" in reasoning
        assert "Technical" in reasoning
        assert "Fundamental" in reasoning
        assert "RSI" in reasoning
        assert "MACD" in reasoning
        assert "P/E" in reasoning
    
    def test_generate_reasoning_includes_conflict_warning(self):
        """Test that reasoning includes conflict warning when appropriate."""
        sentiment = SentimentData(
            symbol="TEST",
            sentiment_score=0.8,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=100.0,
            ma_200=105.0,
            rsi=75.0,
            macd=-1.0,
            macd_signal=-0.5,
            support_levels=[],
            resistance_levels=[],
            technical_score=-0.8
        )
        
        fundamental = FundamentalMetrics(
            symbol="TEST",
            fundamental_score=0.0
        )
        
        reasoning = self.engine._generate_reasoning(
            "HOLD", 0.1, sentiment, technical, fundamental, 0.3
        )
        
        # Should include conflict warning
        assert "conflict" in reasoning.lower() or "caution" in reasoning.lower()
    
    # Test _describe_score method
    
    def test_describe_score_labels(self):
        """Test score description labels."""
        test_cases = [
            (0.8, "Very bullish"),
            (0.3, "Bullish"),
            (0.0, "Neutral"),
            (-0.3, "Bearish"),
            (-0.8, "Very bearish"),
        ]
        
        for score, expected_label in test_cases:
            label = self.engine._describe_score(score, "test")
            assert label == expected_label


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
