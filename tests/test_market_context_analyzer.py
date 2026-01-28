"""Tests for Market Context Analyzer."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from src.market_context_analyzer import MarketContextAnalyzer, MarketContext
from src.data_provider import DataProvider
from src.models import StockData, PricePoint


@pytest.fixture
def mock_data_provider():
    """Create a mock data provider."""
    return Mock(spec=DataProvider)


@pytest.fixture
def analyzer(mock_data_provider):
    """Create a market context analyzer with mock data provider."""
    return MarketContextAnalyzer(mock_data_provider)


def create_mock_stock_data(symbol: str, current_price: float, historical_prices: list):
    """Helper to create mock stock data."""
    return StockData(
        symbol=symbol,
        current_price=current_price,
        volume=1000000,
        timestamp=datetime.now(),
        historical_prices=historical_prices
    )


def create_price_points(prices: list):
    """Helper to create price points from a list of prices."""
    return [
        PricePoint(
            date=datetime.now(),
            open=price,
            high=price * 1.01,
            low=price * 0.99,
            close=price,
            volume=1000000
        )
        for price in prices
    ]


class TestMarketContextAnalyzer:
    """Test suite for MarketContextAnalyzer."""
    
    def test_bullish_market_detection(self, analyzer, mock_data_provider):
        """Test detection of bullish market conditions."""
        # Setup: Nifty above both MAs, Bank Nifty above both MAs, low VIX
        nifty_prices = [20000] * 30 + [21000] * 20 + [22000]  # Uptrend
        banknifty_prices = [45000] * 30 + [46000] * 20 + [47000]  # Uptrend
        
        mock_data_provider.get_stock_data.side_effect = [
            create_mock_stock_data("^NSEI", 22000, create_price_points(nifty_prices)),
            create_mock_stock_data("^NSEBANK", 47000, create_price_points(banknifty_prices)),
            create_mock_stock_data("^INDIAVIX", 12.0, [])
        ]
        
        context = analyzer.get_market_context(use_cache=False)
        
        assert context.nifty_trend == "bullish"
        assert context.banknifty_trend == "bullish"
        assert context.vix_level == "low"
        assert context.market_state == "bullish"
    
    def test_bearish_market_detection(self, analyzer, mock_data_provider):
        """Test detection of bearish market conditions."""
        # Setup: Nifty below both MAs, Bank Nifty below both MAs, moderate VIX
        nifty_prices = [22000] * 30 + [21000] * 20 + [20000]  # Downtrend
        banknifty_prices = [47000] * 30 + [46000] * 20 + [45000]  # Downtrend
        
        mock_data_provider.get_stock_data.side_effect = [
            create_mock_stock_data("^NSEI", 20000, create_price_points(nifty_prices)),
            create_mock_stock_data("^NSEBANK", 45000, create_price_points(banknifty_prices)),
            create_mock_stock_data("^INDIAVIX", 18.0, [])
        ]
        
        context = analyzer.get_market_context(use_cache=False)
        
        assert context.nifty_trend == "bearish"
        assert context.banknifty_trend == "bearish"
        assert context.vix_level == "moderate"
        assert context.market_state == "bearish"
    
    def test_volatile_market_detection(self, analyzer, mock_data_provider):
        """Test detection of volatile market conditions."""
        # Setup: High VIX overrides other signals
        nifty_prices = [21000] * 50 + [21500]  # Slightly bullish
        banknifty_prices = [46000] * 50 + [46500]  # Slightly bullish
        
        mock_data_provider.get_stock_data.side_effect = [
            create_mock_stock_data("^NSEI", 21500, create_price_points(nifty_prices)),
            create_mock_stock_data("^NSEBANK", 46500, create_price_points(banknifty_prices)),
            create_mock_stock_data("^INDIAVIX", 26.0, [])  # Very high VIX
        ]
        
        context = analyzer.get_market_context(use_cache=False)
        
        assert context.vix_level == "very_high"
        assert context.market_state == "volatile"
    
    def test_neutral_market_detection(self, analyzer, mock_data_provider):
        """Test detection of neutral market conditions."""
        # Setup: Mixed signals - Nifty bullish, Bank Nifty bearish
        nifty_prices = [20000] * 30 + [21000] * 20 + [22000]  # Uptrend
        banknifty_prices = [47000] * 30 + [46000] * 20 + [45000]  # Downtrend
        
        mock_data_provider.get_stock_data.side_effect = [
            create_mock_stock_data("^NSEI", 22000, create_price_points(nifty_prices)),
            create_mock_stock_data("^NSEBANK", 45000, create_price_points(banknifty_prices)),
            create_mock_stock_data("^INDIAVIX", 16.0, [])
        ]
        
        context = analyzer.get_market_context(use_cache=False)
        
        assert context.nifty_trend == "bullish"
        assert context.banknifty_trend == "bearish"
        assert context.market_state == "neutral"
    
    def test_vix_level_classification(self, analyzer):
        """Test VIX level classification."""
        assert analyzer._determine_vix_level(12.0) == "low"
        assert analyzer._determine_vix_level(17.0) == "moderate"
        assert analyzer._determine_vix_level(22.0) == "high"
        assert analyzer._determine_vix_level(28.0) == "very_high"
    
    def test_trend_determination(self, analyzer):
        """Test trend determination logic."""
        # Bullish: price above both MAs
        assert analyzer._determine_trend(22000, 21000, 20000) == "bullish"
        
        # Bearish: price below both MAs
        assert analyzer._determine_trend(20000, 21000, 22000) == "bearish"
        
        # Neutral: mixed signals
        assert analyzer._determine_trend(21000, 20000, 22000) == "neutral"
        assert analyzer._determine_trend(21000, 22000, 20000) == "neutral"
    
    def test_caching(self, analyzer, mock_data_provider):
        """Test that market context is cached."""
        nifty_prices = [21000] * 51
        banknifty_prices = [46000] * 51
        
        mock_data_provider.get_stock_data.side_effect = [
            create_mock_stock_data("^NSEI", 21000, create_price_points(nifty_prices)),
            create_mock_stock_data("^NSEBANK", 46000, create_price_points(banknifty_prices)),
            create_mock_stock_data("^INDIAVIX", 16.0, [])
        ]
        
        # First call - should fetch data
        context1 = analyzer.get_market_context(use_cache=True)
        
        # Second call - should use cache
        context2 = analyzer.get_market_context(use_cache=True)
        
        # Should be the same object
        assert context1 is context2
        
        # Data provider should only be called once (3 times for 3 indices)
        assert mock_data_provider.get_stock_data.call_count == 3
    
    def test_error_handling(self, analyzer, mock_data_provider):
        """Test graceful error handling when data fetch fails."""
        # Setup: Data provider raises exception
        mock_data_provider.get_stock_data.side_effect = Exception("API Error")
        
        # Should not raise exception, should return neutral values
        context = analyzer.get_market_context(use_cache=False)
        
        # Should have neutral/default values
        assert context.nifty_trend == "neutral"
        assert context.banknifty_trend == "neutral"
        assert context.vix_value == 18.0  # Default moderate VIX
