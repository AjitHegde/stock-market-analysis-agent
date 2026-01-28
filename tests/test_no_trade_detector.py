"""Tests for NoTradeDetector module."""

import pytest
from datetime import datetime
from src.no_trade_detector import NoTradeDetector, NoTradeSignal
from src.models import MarketContext


@pytest.fixture
def detector():
    """Create a NoTradeDetector instance with default settings."""
    return NoTradeDetector(
        vix_spike_threshold=25.0,
        nifty_drop_threshold=0.03,
        enable_no_trade=True
    )


@pytest.fixture
def bullish_market():
    """Create a bullish market context."""
    return MarketContext(
        nifty_trend="bullish",
        banknifty_trend="bullish",
        vix_level="low",
        market_state="bullish",
        nifty_price=22000.0,
        nifty_20dma=21800.0,
        nifty_50dma=21500.0,
        banknifty_price=48000.0,
        banknifty_20dma=47500.0,
        banknifty_50dma=47000.0,
        vix_value=12.5,
        timestamp=datetime.now(),
        market_signal_quality=0.85,
        market_favorability=0.85
    )


@pytest.fixture
def bearish_volatile_market():
    """Create a bearish and volatile market context (should trigger no-trade)."""
    return MarketContext(
        nifty_trend="bearish",
        banknifty_trend="bearish",
        vix_level="high",
        market_state="bearish",
        nifty_price=20000.0,
        nifty_20dma=20500.0,
        nifty_50dma=21000.0,
        banknifty_price=44000.0,
        banknifty_20dma=45000.0,
        banknifty_50dma=46000.0,
        vix_value=28.0,
        timestamp=datetime.now(),
        market_signal_quality=0.75,
        market_favorability=0.25
    )


@pytest.fixture
def vix_spike_market():
    """Create a market with VIX spike (should trigger no-trade)."""
    return MarketContext(
        nifty_trend="neutral",
        banknifty_trend="neutral",
        vix_level="very_high",
        market_state="volatile",
        nifty_price=21500.0,
        nifty_20dma=21400.0,
        nifty_50dma=21300.0,
        banknifty_price=47000.0,
        banknifty_20dma=46800.0,
        banknifty_50dma=46500.0,
        vix_value=32.0,
        timestamp=datetime.now(),
        market_signal_quality=0.50,
        market_favorability=0.20
    )


@pytest.fixture
def nifty_below_50dma_market():
    """Create a market with Nifty significantly below 50DMA (should trigger no-trade)."""
    return MarketContext(
        nifty_trend="bearish",
        banknifty_trend="neutral",
        vix_level="moderate",
        market_state="bearish",
        nifty_price=20500.0,  # 4.65% below 50DMA
        nifty_20dma=20700.0,
        nifty_50dma=21500.0,
        banknifty_price=47000.0,
        banknifty_20dma=46800.0,
        banknifty_50dma=46500.0,
        vix_value=18.0,
        timestamp=datetime.now(),
        market_signal_quality=0.70,
        market_favorability=0.30
    )


class TestNoTradeDetectorInitialization:
    """Test NoTradeDetector initialization."""
    
    def test_default_initialization(self):
        """Test detector initializes with default values."""
        detector = NoTradeDetector()
        assert detector.vix_spike_threshold == 25.0
        assert detector.nifty_drop_threshold == 0.03
        assert detector.enable_no_trade is True
    
    def test_custom_initialization(self):
        """Test detector initializes with custom values."""
        detector = NoTradeDetector(
            vix_spike_threshold=30.0,
            nifty_drop_threshold=0.05,
            enable_no_trade=False
        )
        assert detector.vix_spike_threshold == 30.0
        assert detector.nifty_drop_threshold == 0.05
        assert detector.enable_no_trade is False


class TestNoTradeDetection:
    """Test no-trade condition detection."""
    
    def test_bullish_market_allows_trading(self, detector, bullish_market):
        """Test that bullish market allows trading."""
        signal = detector.check_market_conditions(bullish_market)
        
        assert signal.is_no_trade is False
        assert len(signal.reasons) == 0
        assert signal.severity == "low"
        assert "allow trading" in signal.suggested_action.lower()
    
    def test_bearish_volatile_market_blocks_trading(self, detector, bearish_volatile_market):
        """Test that bearish + volatile market blocks trading."""
        signal = detector.check_market_conditions(bearish_volatile_market)
        
        assert signal.is_no_trade is True
        assert len(signal.reasons) > 0
        assert signal.severity == "high"
        assert any("bearish" in reason.lower() for reason in signal.reasons)
        assert "stay in cash" in signal.suggested_action.lower()
    
    def test_vix_spike_blocks_trading(self, detector, vix_spike_market):
        """Test that VIX spike blocks trading."""
        signal = detector.check_market_conditions(vix_spike_market)
        
        assert signal.is_no_trade is True
        assert len(signal.reasons) > 0
        assert signal.severity == "high"
        assert any("vix spike" in reason.lower() for reason in signal.reasons)
    
    def test_nifty_below_50dma_blocks_trading(self, detector, nifty_below_50dma_market):
        """Test that Nifty significantly below 50DMA blocks trading."""
        signal = detector.check_market_conditions(nifty_below_50dma_market)
        
        assert signal.is_no_trade is True
        assert len(signal.reasons) > 0
        assert any("50-day moving average" in reason.lower() for reason in signal.reasons)
    
    def test_no_market_context_allows_trading(self, detector):
        """Test that missing market context allows trading (fail-safe)."""
        signal = detector.check_market_conditions(None)
        
        assert signal.is_no_trade is False
        assert signal.severity == "low"
    
    def test_disabled_detector_allows_trading(self, bearish_volatile_market):
        """Test that disabled detector always allows trading."""
        detector = NoTradeDetector(enable_no_trade=False)
        signal = detector.check_market_conditions(bearish_volatile_market)
        
        assert signal.is_no_trade is False
        assert "enabled" in signal.suggested_action.lower()


class TestRecommendationBlocking:
    """Test recommendation blocking logic."""
    
    def test_buy_blocked_in_dangerous_conditions(self, detector, bearish_volatile_market):
        """Test that BUY recommendations are blocked in dangerous conditions."""
        should_block = detector.should_block_recommendation("BUY", bearish_volatile_market)
        assert should_block is True
    
    def test_sell_not_blocked(self, detector, bearish_volatile_market):
        """Test that SELL recommendations are NOT blocked."""
        should_block = detector.should_block_recommendation("SELL", bearish_volatile_market)
        assert should_block is False
    
    def test_hold_not_blocked(self, detector, bearish_volatile_market):
        """Test that HOLD recommendations are NOT blocked."""
        should_block = detector.should_block_recommendation("HOLD", bearish_volatile_market)
        assert should_block is False
    
    def test_buy_allowed_in_safe_conditions(self, detector, bullish_market):
        """Test that BUY recommendations are allowed in safe conditions."""
        should_block = detector.should_block_recommendation("BUY", bullish_market)
        assert should_block is False


class TestMarketSafetyScore:
    """Test market safety score calculation."""
    
    def test_bullish_market_high_safety(self, detector, bullish_market):
        """Test that bullish market has high safety score."""
        safety_score = detector.get_market_safety_score(bullish_market)
        assert safety_score >= 0.7
        assert safety_score <= 1.0
    
    def test_bearish_volatile_market_low_safety(self, detector, bearish_volatile_market):
        """Test that bearish + volatile market has low safety score."""
        safety_score = detector.get_market_safety_score(bearish_volatile_market)
        assert safety_score <= 0.3
    
    def test_vix_spike_reduces_safety(self, detector, vix_spike_market):
        """Test that VIX spike reduces safety score."""
        safety_score = detector.get_market_safety_score(vix_spike_market)
        assert safety_score <= 0.4
    
    def test_nifty_below_50dma_reduces_safety(self, detector, nifty_below_50dma_market):
        """Test that Nifty below 50DMA reduces safety score."""
        safety_score = detector.get_market_safety_score(nifty_below_50dma_market)
        assert safety_score <= 0.5
    
    def test_no_market_context_neutral_safety(self, detector):
        """Test that missing market context returns neutral safety score."""
        safety_score = detector.get_market_safety_score(None)
        assert safety_score == 0.5
    
    def test_safety_score_bounds(self, detector, bearish_volatile_market):
        """Test that safety score is always between 0.0 and 1.0."""
        safety_score = detector.get_market_safety_score(bearish_volatile_market)
        assert 0.0 <= safety_score <= 1.0


class TestSeverityLevels:
    """Test severity level assignment."""
    
    def test_high_severity_for_bearish_volatile(self, detector, bearish_volatile_market):
        """Test that bearish + volatile gets high severity."""
        signal = detector.check_market_conditions(bearish_volatile_market)
        assert signal.severity == "high"
    
    def test_high_severity_for_vix_spike(self, detector, vix_spike_market):
        """Test that VIX spike gets high severity."""
        signal = detector.check_market_conditions(vix_spike_market)
        assert signal.severity == "high"
    
    def test_medium_severity_for_nifty_below_50dma(self, detector, nifty_below_50dma_market):
        """Test that Nifty below 50DMA gets medium severity."""
        signal = detector.check_market_conditions(nifty_below_50dma_market)
        # Should be at least medium severity
        assert signal.severity in ["medium", "high"]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_vix_exactly_at_threshold(self, detector):
        """Test VIX exactly at threshold."""
        market = MarketContext(
            nifty_trend="neutral",
            banknifty_trend="neutral",
            vix_level="high",
            market_state="neutral",
            nifty_price=21500.0,
            nifty_20dma=21400.0,
            nifty_50dma=21300.0,
            banknifty_price=47000.0,
            banknifty_20dma=46800.0,
            banknifty_50dma=46500.0,
            vix_value=25.0,  # Exactly at threshold
            timestamp=datetime.now(),
            market_signal_quality=0.60,
            market_favorability=0.40
        )
        
        signal = detector.check_market_conditions(market)
        # Should NOT trigger (threshold is >, not >=)
        assert signal.is_no_trade is False
    
    def test_vix_just_above_threshold(self, detector):
        """Test VIX just above threshold."""
        market = MarketContext(
            nifty_trend="neutral",
            banknifty_trend="neutral",
            vix_level="high",
            market_state="neutral",
            nifty_price=21500.0,
            nifty_20dma=21400.0,
            nifty_50dma=21300.0,
            banknifty_price=47000.0,
            banknifty_20dma=46800.0,
            banknifty_50dma=46500.0,
            vix_value=25.1,  # Just above threshold
            timestamp=datetime.now(),
            market_signal_quality=0.60,
            market_favorability=0.40
        )
        
        signal = detector.check_market_conditions(market)
        # Should trigger
        assert signal.is_no_trade is True
    
    def test_nifty_exactly_at_threshold(self, detector):
        """Test Nifty exactly at 3% below 50DMA."""
        market = MarketContext(
            nifty_trend="bearish",
            banknifty_trend="neutral",
            vix_level="low",
            market_state="bearish",
            nifty_price=20850.0,  # Exactly 3% below 21500
            nifty_20dma=20900.0,
            nifty_50dma=21500.0,
            banknifty_price=47000.0,
            banknifty_20dma=46800.0,
            banknifty_50dma=46500.0,
            vix_value=15.0,
            timestamp=datetime.now(),
            market_signal_quality=0.70,
            market_favorability=0.35
        )
        
        signal = detector.check_market_conditions(market)
        # Should trigger because -3.0% < -3.0% threshold
        assert signal.is_no_trade is True
        assert signal.severity in ["medium", "high"]


class TestNoTradeSignalDataclass:
    """Test NoTradeSignal dataclass."""
    
    def test_no_trade_signal_creation(self):
        """Test creating a NoTradeSignal."""
        signal = NoTradeSignal(
            is_no_trade=True,
            reasons=["Market is bearish", "VIX is high"],
            suggested_action="Stay in cash",
            severity="high"
        )
        
        assert signal.is_no_trade is True
        assert len(signal.reasons) == 2
        assert signal.suggested_action == "Stay in cash"
        assert signal.severity == "high"
    
    def test_no_trade_signal_default_severity(self):
        """Test NoTradeSignal default severity."""
        signal = NoTradeSignal(
            is_no_trade=False,
            reasons=[],
            suggested_action="Trading allowed"
        )
        
        assert signal.severity == "medium"  # Default value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
