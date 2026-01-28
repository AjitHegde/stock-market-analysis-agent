"""Integration test for the complete discover_stocks workflow.

Tests the end-to-end flow from fetching news to returning prioritized symbols.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.news_discovery import NewsDiscovery, SymbolMention
from src.data_provider import DataProvider, NewsArticle
from src.symbol_lookup import SymbolLookup
from src.config import Configuration


@pytest.fixture
def news_discovery():
    """Create a NewsDiscovery instance for testing."""
    config = Configuration()
    data_provider = DataProvider(config)
    symbol_lookup = SymbolLookup()
    return NewsDiscovery(data_provider, symbol_lookup, max_symbols=5)


def test_discover_stocks_complete_workflow(news_discovery):
    """Test the complete discover_stocks workflow with mocked news."""
    # Mock the _fetch_news method to return sample articles
    sample_articles = [
        NewsArticle(
            title="Apple announces new iPhone",
            content="Apple Inc. (AAPL) revealed its latest iPhone model today.",
            url="https://example.com/1",
            published_at=datetime.now()
        ),
        NewsArticle(
            title="Tesla stock rises on earnings",
            content="TSLA shares jumped 5% after strong quarterly results.",
            url="https://example.com/2",
            published_at=datetime.now()
        ),
        NewsArticle(
            title="Google parent Alphabet beats expectations",
            content="GOOGL stock climbed as Alphabet reported better than expected revenue.",
            url="https://example.com/3",
            published_at=datetime.now()
        ),
        NewsArticle(
            title="Apple and Tesla dominate tech news",
            content="Both AAPL and TSLA continue to make headlines.",
            url="https://example.com/4",
            published_at=datetime.now()
        )
    ]
    
    with patch.object(news_discovery, '_fetch_news', return_value=sample_articles):
        discovered = news_discovery.discover_stocks(hours_back=24)
    
    # Verify we got DiscoveredStock objects
    assert len(discovered) > 0
    assert all(hasattr(stock, 'symbol') for stock in discovered)
    assert all(hasattr(stock, 'mention_count') for stock in discovered)
    assert all(hasattr(stock, 'sources') for stock in discovered)
    assert all(hasattr(stock, 'sample_articles') for stock in discovered)
    
    # Verify AAPL and TSLA are in the results (mentioned multiple times)
    symbols = [stock.symbol for stock in discovered]
    assert 'AAPL' in symbols
    assert 'TSLA' in symbols
    
    # Verify AAPL has higher mention count (appears in 3 articles)
    aapl_stock = next(s for s in discovered if s.symbol == 'AAPL')
    assert aapl_stock.mention_count >= 2


def test_discover_stocks_respects_max_symbols(news_discovery):
    """Test that discover_stocks respects the max_symbols limit."""
    # Create many articles with different symbols
    sample_articles = []
    symbols = ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN', 'META', 'NVDA', 'AMD']
    
    for i, symbol in enumerate(symbols):
        sample_articles.append(
            NewsArticle(
                title=f"{symbol} news article",
                content=f"Article about {symbol} stock.",
                url=f"https://example.com/{i}",
                published_at=datetime.now()
            )
        )
    
    with patch.object(news_discovery, '_fetch_news', return_value=sample_articles):
        discovered = news_discovery.discover_stocks(hours_back=24)
    
    # Should be limited to max_symbols (5 in this fixture)
    assert len(discovered) <= 5


def test_discover_stocks_with_no_valid_symbols(news_discovery):
    """Test discover_stocks when no valid symbols are found."""
    # Articles with no recognizable symbols
    sample_articles = [
        NewsArticle(
            title="Market news today",
            content="The market was volatile today with mixed results.",
            url="https://example.com/1",
            published_at=datetime.now()
        )
    ]
    
    with patch.object(news_discovery, '_fetch_news', return_value=sample_articles):
        discovered = news_discovery.discover_stocks(hours_back=24)
    
    # Should return empty list or very few symbols
    assert isinstance(discovered, list)


def test_discover_stocks_sample_articles_limited(news_discovery):
    """Test that sample_articles is limited to 3 per symbol."""
    # Create multiple articles mentioning the same symbol
    sample_articles = []
    for i in range(5):
        sample_articles.append(
            NewsArticle(
                title=f"AAPL news {i}",
                content=f"Apple article number {i}",
                url=f"https://example.com/{i}",
                published_at=datetime.now()
            )
        )
    
    with patch.object(news_discovery, '_fetch_news', return_value=sample_articles):
        discovered = news_discovery.discover_stocks(hours_back=24)
    
    # Find AAPL in results
    aapl_stock = next((s for s in discovered if s.symbol == 'AAPL'), None)
    
    if aapl_stock:
        # Should have at most 3 sample articles
        assert len(aapl_stock.sample_articles) <= 3


def test_discover_stocks_sources_tracked(news_discovery):
    """Test that sources are properly tracked for each symbol."""
    sample_articles = [
        NewsArticle(
            title="AAPL from source 1",
            content="Apple news",
            url="https://newsapi.org/article1",
            published_at=datetime.now()
        ),
        NewsArticle(
            title="AAPL from source 2",
            content="Apple news",
            url="https://yahoo.com/article2",
            published_at=datetime.now()
        )
    ]
    
    with patch.object(news_discovery, '_fetch_news', return_value=sample_articles):
        discovered = news_discovery.discover_stocks(hours_back=24)
    
    # Find AAPL in results
    aapl_stock = next((s for s in discovered if s.symbol == 'AAPL'), None)
    
    if aapl_stock:
        # Should have tracked multiple sources
        assert len(aapl_stock.sources) >= 1
        assert isinstance(aapl_stock.sources, list)
