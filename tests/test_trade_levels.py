"""Tests for Trade Levels calculation."""

import pytest
from datetime import datetime

from src.recommendation_engine import RecommendationEngine
from src.config import Configuration
from src.models import TechnicalIndicators, TradeLevels


@pytest.fixture
def engine():
    """Create a recommendation engine."""
    config = Configuration()
    return RecommendationEngine(config)


class TestTradeLevels:
    """Test suite for trade levels calculation."""
    
    def test_calculate_trade_levels_basic(self, engine):
        """Test basic trade levels calculation."""
        current_price = 100.0
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=90.0,
            ma_200=85.0,
            rsi=50.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[90.0, 85.0],
            resistance_levels=[110.0, 120.0],
            technical_score=0.5,
            atr=2.0
        )
        
        levels = engine.calculate_trade_levels(current_price, technical, "BUY")
        
        # Verify basic structure
        assert isinstance(levels, TradeLevels)
        assert levels.ideal_entry > 0
        assert levels.stop_loss > 0
        assert levels.target > 0
        
        # Verify relationships
        assert levels.stop_loss < levels.ideal_entry < levels.target
        assert levels.ideal_entry <= current_price
        
        # Verify risk management
        assert levels.risk_per_trade_percent <= 1.5
        assert levels.risk_reward_ratio >= 2.0
        assert 0 < levels.position_size_percent <= 10.0
    
    def test_trade_levels_with_support(self, engine):
        """Test that entry is placed near support."""
        current_price = 100.0
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=90.0,
            ma_200=85.0,
            rsi=50.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[92.0, 85.0],  # Support at 92
            resistance_levels=[110.0],
            technical_score=0.5,
            atr=2.0
        )
        
        levels = engine.calculate_trade_levels(current_price, technical, "BUY")
        
        # Entry should be near support (92) with small buffer
        assert 92.0 <= levels.ideal_entry <= 93.0
    
    def test_trade_levels_with_resistance(self, engine):
        """Test that target considers resistance."""
        current_price = 100.0
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=90.0,
            ma_200=85.0,
            rsi=50.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[90.0],
            resistance_levels=[115.0, 125.0],  # Resistance at 115
            technical_score=0.5,
            atr=2.0
        )
        
        levels = engine.calculate_trade_levels(current_price, technical, "BUY")
        
        # Target should consider resistance
        # Either at resistance or beyond minimum 2x risk
        assert levels.target >= levels.ideal_entry + (levels.ideal_entry - levels.stop_loss) * 2
    
    def test_trade_levels_atr_based_stop(self, engine):
        """Test ATR-based stop loss calculation."""
        current_price = 100.0
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=90.0,
            ma_200=85.0,
            rsi=50.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[],  # No support
            resistance_levels=[],
            technical_score=0.5,
            atr=3.0  # 3% ATR
        )
        
        levels = engine.calculate_trade_levels(current_price, technical, "BUY")
        
        # Stop should be based on ATR (1.5x ATR below entry)
        expected_stop_range = levels.ideal_entry - (3.0 * 1.5)
        # Allow some tolerance
        assert abs(levels.stop_loss - expected_stop_range) < 2.0
    
    def test_trade_levels_minimum_rr_ratio(self, engine):
        """Test that minimum 1:2 R:R ratio is enforced."""
        current_price = 100.0
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=90.0,
            ma_200=85.0,
            rsi=50.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[90.0],
            resistance_levels=[105.0],  # Close resistance
            technical_score=0.5,
            atr=2.0
        )
        
        levels = engine.calculate_trade_levels(current_price, technical, "BUY")
        
        # R:R ratio must be at least 1:2
        assert levels.risk_reward_ratio >= 2.0
        
        # Verify calculation
        risk = levels.ideal_entry - levels.stop_loss
        reward = levels.target - levels.ideal_entry
        calculated_rr = reward / risk
        assert abs(calculated_rr - levels.risk_reward_ratio) < 0.1
    
    def test_trade_levels_position_sizing(self, engine):
        """Test position sizing calculation."""
        current_price = 100.0
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=90.0,
            ma_200=85.0,
            rsi=50.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[90.0],
            resistance_levels=[120.0],
            technical_score=0.5,
            atr=2.0
        )
        
        levels = engine.calculate_trade_levels(current_price, technical, "BUY")
        
        # Position size should be reasonable
        assert 0 < levels.position_size_percent <= 10.0
        
        # Risk per trade should be 1.5%
        assert levels.risk_per_trade_percent == 1.5
    
    def test_trade_levels_no_support_fallback(self, engine):
        """Test fallback when no support levels available."""
        current_price = 100.0
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=90.0,
            ma_200=85.0,
            rsi=50.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[],  # No support
            resistance_levels=[],  # No resistance
            technical_score=0.5,
            atr=2.0
        )
        
        levels = engine.calculate_trade_levels(current_price, technical, "BUY")
        
        # Should still generate valid levels
        assert levels.ideal_entry > 0
        assert levels.stop_loss > 0
        assert levels.target > 0
        assert levels.stop_loss < levels.ideal_entry < levels.target
    
    def test_trade_levels_only_for_buy(self, engine):
        """Test that trade levels only work for BUY action."""
        current_price = 100.0
        
        technical = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,
            ma_50=90.0,
            ma_200=85.0,
            rsi=50.0,
            macd=1.0,
            macd_signal=0.5,
            support_levels=[90.0],
            resistance_levels=[110.0],
            technical_score=0.5,
            atr=2.0
        )
        
        # Should raise error for SELL
        with pytest.raises(ValueError, match="only supported for BUY"):
            engine.calculate_trade_levels(current_price, technical, "SELL")
