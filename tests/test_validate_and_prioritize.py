"""Unit tests for NewsDiscovery._validate_and_prioritize method.

Tests the validation, deduplication, prioritization, and limiting logic
for discovered stock symbols.
"""

import pytest
from datetime import datetime
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
    return NewsDiscovery(data_provider, symbol_lookup, max_symbols=50)


@pytest.fixture
def sample_article():
    """Create a sample news article."""
    return NewsArticle(
        title="Test Article",
        content="Test content",
        url="https://example.com",
        published_at=datetime.now()
    )


def test_validate_and_prioritize_basic(news_discovery, sample_article):
    """Test basic validation and prioritization with valid symbols."""
    mentions = {
        'AAPL': SymbolMention(
            symbol='AAPL',
            mention_count=5,
            sources={'newsapi.org', 'yahoo.com'},
            articles=[sample_article]
        ),
        'GOOGL': SymbolMention(
            symbol='GOOGL',
            mention_count=3,
            sources={'newsapi.org'},
            articles=[sample_article]
        ),
        'TSLA': SymbolMention(
            symbol='TSLA',
            mention_count=4,
            sources={'yahoo.com', 'finnhub.io', 'reuters.com'},
            articles=[sample_article]
        )
    }
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    # All symbols should be valid
    assert len(result) == 3
    assert 'AAPL' in result
    assert 'GOOGL' in result
    assert 'TSLA' in result


def test_validate_and_prioritize_ordering(news_discovery, sample_article):
    """Test that symbols are ordered by priority score correctly.
    
    Priority score = (mention_count * 2) + (unique_sources * 3)
    """
    mentions = {
        'AAPL': SymbolMention(
            symbol='AAPL',
            mention_count=5,  # score = 5*2 + 2*3 = 16
            sources={'newsapi.org', 'yahoo.com'},
            articles=[sample_article]
        ),
        'GOOGL': SymbolMention(
            symbol='GOOGL',
            mention_count=3,  # score = 3*2 + 1*3 = 9
            sources={'newsapi.org'},
            articles=[sample_article]
        ),
        'TSLA': SymbolMention(
            symbol='TSLA',
            mention_count=4,  # score = 4*2 + 3*3 = 17
            sources={'yahoo.com', 'finnhub.io', 'reuters.com'},
            articles=[sample_article]
        )
    }
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    # Should be ordered: TSLA (17), AAPL (16), GOOGL (9)
    assert result[0] == 'TSLA'
    assert result[1] == 'AAPL'
    assert result[2] == 'GOOGL'


def test_validate_and_prioritize_filters_invalid(news_discovery, sample_article):
    """Test that invalid symbols are filtered out."""
    mentions = {
        'AAPL': SymbolMention(
            symbol='AAPL',
            mention_count=5,
            sources={'newsapi.org'},
            articles=[sample_article]
        ),
        'INVALID123': SymbolMention(
            symbol='INVALID123',
            mention_count=10,
            sources={'newsapi.org'},
            articles=[sample_article]
        ),
        'XYZ': SymbolMention(  # Valid format but not in registry
            symbol='XYZ',
            mention_count=3,
            sources={'newsapi.org'},
            articles=[sample_article]
        )
    }
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    # AAPL and XYZ should be valid (XYZ matches ticker pattern)
    # INVALID123 should be filtered out
    assert 'AAPL' in result
    assert 'XYZ' in result
    assert 'INVALID123' not in result


def test_validate_and_prioritize_limits_to_max_symbols(sample_article):
    """Test that results are limited to max_symbols."""
    config = Configuration()
    data_provider = DataProvider(config)
    symbol_lookup = SymbolLookup()
    news_discovery = NewsDiscovery(data_provider, symbol_lookup, max_symbols=3)
    
    # Create 5 valid symbols
    mentions = {}
    for i, symbol in enumerate(['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN']):
        mentions[symbol] = SymbolMention(
            symbol=symbol,
            mention_count=5 - i,  # Decreasing mention counts
            sources={'newsapi.org'},
            articles=[sample_article]
        )
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    # Should only return top 3
    assert len(result) == 3
    # Should be the ones with highest mention counts
    assert 'AAPL' in result
    assert 'GOOGL' in result
    assert 'TSLA' in result


def test_validate_and_prioritize_empty_input(news_discovery):
    """Test with empty mentions dictionary."""
    mentions = {}
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    assert result == []


def test_validate_and_prioritize_indian_symbols(news_discovery, sample_article):
    """Test validation of Indian stock symbols with .NS suffix."""
    mentions = {
        'HDFCBANK.NS': SymbolMention(
            symbol='HDFCBANK.NS',
            mention_count=5,
            sources={'newsapi.org'},
            articles=[sample_article]
        ),
        'TCS.NS': SymbolMention(
            symbol='TCS.NS',
            mention_count=3,
            sources={'yahoo.com'},
            articles=[sample_article]
        )
    }
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    # Both Indian symbols should be valid
    assert len(result) == 2
    assert 'HDFCBANK.NS' in result
    assert 'TCS.NS' in result


def test_validate_and_prioritize_deduplication(news_discovery, sample_article):
    """Test that symbols are already deduplicated by dict keys."""
    # The mentions dict already ensures deduplication by using symbols as keys
    mentions = {
        'AAPL': SymbolMention(
            symbol='AAPL',
            mention_count=5,
            sources={'newsapi.org', 'yahoo.com'},
            articles=[sample_article, sample_article]  # Same symbol, multiple articles
        )
    }
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    # Should have exactly one AAPL
    assert result.count('AAPL') == 1


def test_validate_and_prioritize_equal_scores(news_discovery, sample_article):
    """Test behavior when multiple symbols have equal priority scores."""
    mentions = {
        'AAPL': SymbolMention(
            symbol='AAPL',
            mention_count=5,  # score = 5*2 + 1*3 = 13
            sources={'newsapi.org'},
            articles=[sample_article]
        ),
        'GOOGL': SymbolMention(
            symbol='GOOGL',
            mention_count=2,  # score = 2*2 + 3*3 = 13
            sources={'newsapi.org', 'yahoo.com', 'finnhub.io'},
            articles=[sample_article]
        )
    }
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    # Both should be included (order doesn't matter for equal scores)
    assert len(result) == 2
    assert 'AAPL' in result
    assert 'GOOGL' in result


def test_validate_and_prioritize_source_diversity_matters(news_discovery, sample_article):
    """Test that source diversity is weighted more than mention count.
    
    A symbol with fewer mentions but more sources should rank higher.
    """
    mentions = {
        'AAPL': SymbolMention(
            symbol='AAPL',
            mention_count=10,  # score = 10*2 + 1*3 = 23
            sources={'newsapi.org'},
            articles=[sample_article]
        ),
        'GOOGL': SymbolMention(
            symbol='GOOGL',
            mention_count=5,  # score = 5*2 + 5*3 = 25
            sources={'newsapi.org', 'yahoo.com', 'finnhub.io', 'reuters.com', 'bloomberg.com'},
            articles=[sample_article]
        )
    }
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    # GOOGL should rank higher despite fewer mentions
    assert result[0] == 'GOOGL'
    assert result[1] == 'AAPL'


def test_validate_and_prioritize_all_invalid(news_discovery, sample_article):
    """Test when all symbols are invalid."""
    mentions = {
        'INVALID123': SymbolMention(
            symbol='INVALID123',
            mention_count=10,
            sources={'newsapi.org'},
            articles=[sample_article]
        ),
        'NOTASYMBOL': SymbolMention(
            symbol='NOTASYMBOL',
            mention_count=5,
            sources={'yahoo.com'},
            articles=[sample_article]
        )
    }
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    # Should return empty list
    assert result == []


def test_validate_and_prioritize_single_symbol(news_discovery, sample_article):
    """Test with a single symbol."""
    mentions = {
        'AAPL': SymbolMention(
            symbol='AAPL',
            mention_count=1,
            sources={'newsapi.org'},
            articles=[sample_article]
        )
    }
    
    result = news_discovery._validate_and_prioritize(mentions)
    
    assert len(result) == 1
    assert result[0] == 'AAPL'
