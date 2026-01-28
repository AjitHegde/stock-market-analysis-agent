"""Unit tests for Technical Analyzer component."""

import pytest
from datetime import datetime, timedelta
from src.technical_analyzer import TechnicalAnalyzer
from src.models import PricePoint, TechnicalIndicators


def create_sample_prices(num_days: int = 200, start_price: float = 100.0) -> list:
    """Create sample price data for testing.
    
    Args:
        num_days: Number of days of price data to generate
        start_price: Starting price
        
    Returns:
        List of PricePoint objects
    """
    prices = []
    current_price = start_price
    base_date = datetime.now() - timedelta(days=num_days)
    
    for i in range(num_days):
        # Simulate some price movement
        change = (i % 10 - 5) * 0.5  # Oscillating pattern
        current_price += change
        
        date = base_date + timedelta(days=i)
        prices.append(PricePoint(
            date=date,
            open=current_price - 0.5,
            high=current_price + 1.0,
            low=current_price - 1.0,
            close=current_price,
            volume=1000000
        ))
    
    return prices


class TestTechnicalAnalyzer:
    """Test suite for TechnicalAnalyzer class."""
    
    def test_calculate_moving_averages_basic(self):
        """Test basic moving average calculation."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(200)
        
        mas = analyzer.calculate_moving_averages(prices)
        
        assert 'ma_20' in mas
        assert 'ma_50' in mas
        assert 'ma_200' in mas
        assert mas['ma_20'] > 0
        assert mas['ma_50'] > 0
        assert mas['ma_200'] > 0
    
    def test_calculate_moving_averages_insufficient_data(self):
        """Test moving averages with insufficient data."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(10)
        
        with pytest.raises(ValueError, match="Need at least 20 price points"):
            analyzer.calculate_moving_averages(prices)
    
    def test_calculate_rsi_basic(self):
        """Test basic RSI calculation."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(50)
        
        rsi = analyzer.calculate_rsi(prices)
        
        assert 0 <= rsi <= 100
    
    def test_calculate_rsi_insufficient_data(self):
        """Test RSI with insufficient data."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(10)
        
        with pytest.raises(ValueError, match="Need at least 15 price points"):
            analyzer.calculate_rsi(prices)
    
    def test_calculate_macd_basic(self):
        """Test basic MACD calculation."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(50)
        
        macd, signal = analyzer.calculate_macd(prices)
        
        assert isinstance(macd, float)
        assert isinstance(signal, float)
    
    def test_calculate_macd_insufficient_data(self):
        """Test MACD with insufficient data."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(20)
        
        with pytest.raises(ValueError, match="Need at least 35 price points"):
            analyzer.calculate_macd(prices)
    
    def test_find_support_resistance_basic(self):
        """Test support and resistance level identification."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(100)
        
        support, resistance = analyzer.find_support_resistance(prices)
        
        assert isinstance(support, list)
        assert isinstance(resistance, list)
        assert len(support) <= 5
        assert len(resistance) <= 5
    
    def test_find_support_resistance_insufficient_data(self):
        """Test support/resistance with insufficient data."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(10)
        
        with pytest.raises(ValueError, match="Need at least 20 price points"):
            analyzer.find_support_resistance(prices)
    
    def test_generate_technical_score_range(self):
        """Test that technical score is within valid range."""
        analyzer = TechnicalAnalyzer()
        
        # Create a sample TechnicalIndicators object
        indicators = TechnicalIndicators(
            symbol="TEST",
            ma_20=105.0,
            ma_50=100.0,
            ma_200=95.0,
            rsi=55.0,
            macd=1.5,
            macd_signal=1.0,
            support_levels=[90.0, 92.0],
            resistance_levels=[108.0, 110.0],
            technical_score=0.0
        )
        
        score = analyzer.generate_technical_score(indicators)
        
        assert -1.0 <= score <= 1.0
    
    def test_generate_technical_score_bullish(self):
        """Test technical score for bullish indicators."""
        analyzer = TechnicalAnalyzer()
        
        # Create bullish indicators
        indicators = TechnicalIndicators(
            symbol="TEST",
            ma_20=110.0,  # Short MA > Long MA (bullish)
            ma_50=105.0,
            ma_200=100.0,
            rsi=25.0,  # Oversold (bullish)
            macd=2.0,  # MACD > Signal (bullish)
            macd_signal=1.0,
            support_levels=[90.0],
            resistance_levels=[115.0],
            technical_score=0.0
        )
        
        score = analyzer.generate_technical_score(indicators)
        
        assert score > 0  # Should be bullish
    
    def test_generate_technical_score_bearish(self):
        """Test technical score for bearish indicators."""
        analyzer = TechnicalAnalyzer()
        
        # Create bearish indicators
        indicators = TechnicalIndicators(
            symbol="TEST",
            ma_20=95.0,  # Short MA < Long MA (bearish)
            ma_50=100.0,
            ma_200=105.0,
            rsi=75.0,  # Overbought (bearish)
            macd=-2.0,  # MACD < Signal (bearish)
            macd_signal=-1.0,
            support_levels=[85.0],
            resistance_levels=[100.0],
            technical_score=0.0
        )
        
        score = analyzer.generate_technical_score(indicators)
        
        assert score < 0  # Should be bearish
    
    def test_analyze_complete(self):
        """Test complete analysis workflow."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(200)
        
        result = analyzer.analyze("TEST", prices)
        
        assert result.symbol == "TEST"
        assert result.ma_20 > 0
        assert result.ma_50 > 0
        assert result.ma_200 > 0
        assert 0 <= result.rsi <= 100
        assert isinstance(result.macd, float)
        assert isinstance(result.macd_signal, float)
        assert isinstance(result.support_levels, list)
        assert isinstance(result.resistance_levels, list)
        assert -1.0 <= result.technical_score <= 1.0
    
    def test_analyze_insufficient_data(self):
        """Test analyze with insufficient data."""
        analyzer = TechnicalAnalyzer()
        prices = create_sample_prices(100)
        
        with pytest.raises(ValueError, match="Need at least 200 price points"):
            analyzer.analyze("TEST", prices)
    
    def test_cluster_levels_basic(self):
        """Test level clustering functionality."""
        analyzer = TechnicalAnalyzer()
        
        # Levels that should be clustered
        levels = [100.0, 100.5, 101.0, 110.0, 110.2]
        
        clustered = analyzer._cluster_levels(levels)
        
        # Should cluster the first 3 and last 2
        assert len(clustered) == 2
        assert 100.0 <= clustered[0] <= 101.0
        assert 110.0 <= clustered[1] <= 110.2
    
    def test_cluster_levels_empty(self):
        """Test clustering with empty list."""
        analyzer = TechnicalAnalyzer()
        
        clustered = analyzer._cluster_levels([])
        
        assert clustered == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
