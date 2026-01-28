"""Tests for news discovery module structure.

This test file verifies that the basic structure of the news discovery
module is correctly set up with all required classes and data models.
"""

import pytest
from datetime import datetime

from src.news_discovery import (
    NewsDiscovery,
    SymbolMention,
    DiscoveredStock,
    NoNewsAvailableError
)
from src.symbol_extractor import SymbolExtractor
from src.data_provider import NewsArticle, DataProvider
from src.symbol_lookup import SymbolLookup
from src.config import Configuration


class TestNewsDiscoveryStructure:
    """Test the basic structure of news discovery components."""
    
    def test_symbol_mention_dataclass(self):
        """Test SymbolMention dataclass can be instantiated."""
        article = NewsArticle(
            title="Apple announces new product",
            content="Apple Inc. revealed new iPhone",
            url="https://example.com/article",
            published_at=datetime.now()
        )
        
        mention = SymbolMention(
            symbol="AAPL",
            mention_count=3,
            sources={"NewsAPI", "Yahoo Finance"},
            articles=[article]
        )
        
        assert mention.symbol == "AAPL"
        assert mention.mention_count == 3
        assert len(mention.sources) == 2
        assert len(mention.articles) == 1
    
    def test_discovered_stock_dataclass(self):
        """Test DiscoveredStock dataclass can be instantiated."""
        article = NewsArticle(
            title="Tesla stock rises",
            content="Tesla shares up 5%",
            url="https://example.com/tesla",
            published_at=datetime.now()
        )
        
        stock = DiscoveredStock(
            symbol="TSLA",
            mention_count=5,
            sources=["NewsAPI", "Finnhub"],
            sample_articles=[article]
        )
        
        assert stock.symbol == "TSLA"
        assert stock.mention_count == 5
        assert len(stock.sources) == 2
        assert len(stock.sample_articles) == 1
    
    def test_news_discovery_initialization(self):
        """Test NewsDiscovery can be initialized."""
        config = Configuration()
        data_provider = DataProvider(config)
        symbol_lookup = SymbolLookup()
        
        discovery = NewsDiscovery(
            data_provider=data_provider,
            symbol_lookup=symbol_lookup,
            max_symbols=50
        )
        
        assert discovery.data_provider is data_provider
        assert discovery.symbol_lookup is symbol_lookup
        assert discovery.max_symbols == 50
        assert discovery.extractor is not None
    
    def test_symbol_extractor_initialization(self):
        """Test SymbolExtractor can be initialized."""
        symbol_lookup = SymbolLookup()
        extractor = SymbolExtractor(symbol_lookup)
        
        assert extractor.symbol_lookup is symbol_lookup
        assert extractor.ticker_pattern is not None
        assert len(extractor.COMMON_WORDS) > 0
    
    def test_news_discovery_has_required_methods(self):
        """Test NewsDiscovery has all required methods."""
        config = Configuration()
        data_provider = DataProvider(config)
        symbol_lookup = SymbolLookup()
        
        discovery = NewsDiscovery(data_provider, symbol_lookup)
        
        # Public methods
        assert hasattr(discovery, 'discover_stocks')
        assert callable(discovery.discover_stocks)
        
        # Private methods
        assert hasattr(discovery, '_fetch_news')
        assert callable(discovery._fetch_news)
        assert hasattr(discovery, '_extract_symbols')
        assert callable(discovery._extract_symbols)
        assert hasattr(discovery, '_validate_and_prioritize')
        assert callable(discovery._validate_and_prioritize)
    
    def test_symbol_extractor_has_required_methods(self):
        """Test SymbolExtractor has all required methods."""
        symbol_lookup = SymbolLookup()
        extractor = SymbolExtractor(symbol_lookup)
        
        # Public methods
        assert hasattr(extractor, 'extract_from_text')
        assert callable(extractor.extract_from_text)
        
        # Private methods
        assert hasattr(extractor, '_find_ticker_symbols')
        assert callable(extractor._find_ticker_symbols)
        assert hasattr(extractor, '_find_company_names')
        assert callable(extractor._find_company_names)
    
    def test_no_news_available_error(self):
        """Test NoNewsAvailableError can be raised and caught."""
        with pytest.raises(NoNewsAvailableError):
            raise NoNewsAvailableError("All news providers failed")
    
    def test_news_article_compatibility(self):
        """Test NewsArticle works with our data models."""
        article = NewsArticle(
            title="Test Article",
            content="Test content",
            url="https://example.com",
            published_at=datetime.now()
        )
        
        # Should work in SymbolMention
        mention = SymbolMention(
            symbol="TEST",
            mention_count=1,
            sources={"Test"},
            articles=[article]
        )
        assert mention.articles[0].title == "Test Article"
        
        # Should work in DiscoveredStock
        stock = DiscoveredStock(
            symbol="TEST",
            mention_count=1,
            sources=["Test"],
            sample_articles=[article]
        )
        assert stock.sample_articles[0].title == "Test Article"
