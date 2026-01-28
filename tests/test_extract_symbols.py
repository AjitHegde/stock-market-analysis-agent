"""Tests for NewsDiscovery._extract_symbols method.

This test file verifies the symbol extraction functionality including:
- Parsing articles and extracting symbols
- Tracking mention counts per symbol
- Tracking sources that mentioned each symbol
- Graceful error handling for extraction failures
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.news_discovery import NewsDiscovery, SymbolMention
from src.data_provider import NewsArticle, DataProvider
from src.symbol_lookup import SymbolLookup
from src.config import Configuration


class TestExtractSymbols:
    """Test the _extract_symbols method."""
    
    @pytest.fixture
    def discovery(self):
        """Create a NewsDiscovery instance for testing."""
        config = Configuration()
        data_provider = DataProvider(config)
        symbol_lookup = SymbolLookup()
        return NewsDiscovery(data_provider, symbol_lookup)
    
    def test_extract_symbols_from_single_article(self, discovery):
        """Test extracting symbols from a single article."""
        article = NewsArticle(
            title="Apple announces new iPhone",
            content="Apple Inc. (AAPL) revealed the new iPhone today",
            url="https://techcrunch.com/article",
            published_at=datetime.now()
        )
        
        mentions = discovery._extract_symbols([article])
        
        # Should extract AAPL
        assert "AAPL" in mentions
        assert mentions["AAPL"].symbol == "AAPL"
        assert mentions["AAPL"].mention_count == 1
        assert len(mentions["AAPL"].articles) == 1
        assert mentions["AAPL"].articles[0] == article
    
    def test_extract_symbols_from_multiple_articles(self, discovery):
        """Test extracting symbols from multiple articles."""
        articles = [
            NewsArticle(
                title="Apple stock rises",
                content="AAPL shares up 5%",
                url="https://example.com/1",
                published_at=datetime.now()
            ),
            NewsArticle(
                title="Tesla announces new model",
                content="TSLA unveils new vehicle",
                url="https://example.com/2",
                published_at=datetime.now()
            ),
            NewsArticle(
                title="Microsoft earnings beat expectations",
                content="MSFT reports strong quarter",
                url="https://example.com/3",
                published_at=datetime.now()
            )
        ]
        
        mentions = discovery._extract_symbols(articles)
        
        # Should extract all three symbols
        assert len(mentions) >= 3
        assert "AAPL" in mentions
        assert "TSLA" in mentions
        assert "MSFT" in mentions
    
    def test_track_mention_count_across_articles(self, discovery):
        """Test that mention count is tracked correctly when symbol appears in multiple articles."""
        articles = [
            NewsArticle(
                title="Apple announces new product",
                content="AAPL stock rises",
                url="https://source1.com/article1",
                published_at=datetime.now()
            ),
            NewsArticle(
                title="Apple earnings report",
                content="AAPL beats expectations",
                url="https://source2.com/article2",
                published_at=datetime.now()
            ),
            NewsArticle(
                title="Apple market analysis",
                content="AAPL continues growth",
                url="https://source3.com/article3",
                published_at=datetime.now()
            )
        ]
        
        mentions = discovery._extract_symbols(articles)
        
        # AAPL should appear in all three articles
        assert "AAPL" in mentions
        assert mentions["AAPL"].mention_count == 3
        assert len(mentions["AAPL"].articles) == 3
    
    def test_track_sources_for_each_symbol(self, discovery):
        """Test that sources are tracked for each symbol."""
        articles = [
            NewsArticle(
                title="Apple news",
                content="AAPL stock update",
                url="https://techcrunch.com/article1",
                published_at=datetime.now()
            ),
            NewsArticle(
                title="Apple analysis",
                content="AAPL market position",
                url="https://bloomberg.com/article2",
                published_at=datetime.now()
            ),
            NewsArticle(
                title="Apple report",
                content="AAPL financial results",
                url="https://reuters.com/article3",
                published_at=datetime.now()
            )
        ]
        
        mentions = discovery._extract_symbols(articles)
        
        # AAPL should have three different sources
        assert "AAPL" in mentions
        assert len(mentions["AAPL"].sources) == 3
        assert "techcrunch.com" in mentions["AAPL"].sources
        assert "bloomberg.com" in mentions["AAPL"].sources
        assert "reuters.com" in mentions["AAPL"].sources
    
    def test_extract_from_title_and_content(self, discovery):
        """Test that symbols are extracted from both title and content."""
        articles = [
            NewsArticle(
                title="AAPL stock rises",
                content="Apple announces new product",
                url="https://example.com/1",
                published_at=datetime.now()
            ),
            NewsArticle(
                title="Tesla news",
                content="TSLA shares jump 10%",
                url="https://example.com/2",
                published_at=datetime.now()
            )
        ]
        
        mentions = discovery._extract_symbols(articles)
        
        # Both symbols should be extracted (one from title, one from content)
        assert "AAPL" in mentions
        assert "TSLA" in mentions
    
    def test_handle_extraction_error_gracefully(self, discovery):
        """Test that extraction errors for individual articles don't stop processing."""
        # Create articles where one will cause an error
        articles = [
            NewsArticle(
                title="Apple announces new iPhone",
                content="AAPL stock rises",
                url="https://example.com/1",
                published_at=datetime.now()
            ),
            NewsArticle(
                title="Tesla news",
                content="TSLA shares up",
                url="https://example.com/2",
                published_at=datetime.now()
            )
        ]
        
        # Mock the extractor to raise an error for the first article
        original_extract = discovery.extractor.extract_from_text
        call_count = [0]
        
        def mock_extract(text):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("Simulated extraction error")
            return original_extract(text)
        
        with patch.object(discovery.extractor, 'extract_from_text', side_effect=mock_extract):
            mentions = discovery._extract_symbols(articles)
        
        # Should still extract from the second article
        assert "TSLA" in mentions
        # First article should have been skipped due to error
        assert mentions["TSLA"].mention_count == 1
    
    def test_empty_articles_list(self, discovery):
        """Test handling of empty articles list."""
        mentions = discovery._extract_symbols([])
        
        assert mentions == {}
    
    def test_article_with_no_symbols(self, discovery):
        """Test article with no recognizable symbols."""
        article = NewsArticle(
            title="Market news today",
            content="The market was active today with many trades",
            url="https://example.com/article",
            published_at=datetime.now()
        )
        
        mentions = discovery._extract_symbols([article])
        
        # Should return empty or minimal results (no valid symbols)
        # Note: Might extract some common words that pass through filters
        # The key is it shouldn't crash
        assert isinstance(mentions, dict)
    
    def test_article_with_multiple_symbols(self, discovery):
        """Test article mentioning multiple symbols."""
        article = NewsArticle(
            title="Tech stocks rally",
            content="AAPL, MSFT, and GOOGL all rose today in trading",
            url="https://example.com/article",
            published_at=datetime.now()
        )
        
        mentions = discovery._extract_symbols([article])
        
        # Should extract all three symbols
        assert "AAPL" in mentions
        assert "MSFT" in mentions
        assert "GOOGL" in mentions
        
        # Each should have mention_count of 1
        assert mentions["AAPL"].mention_count == 1
        assert mentions["MSFT"].mention_count == 1
        assert mentions["GOOGL"].mention_count == 1
    
    def test_article_without_url(self, discovery):
        """Test handling of article without URL (source tracking should handle gracefully)."""
        article = NewsArticle(
            title="Apple announces new product",
            content="AAPL stock rises",
            url="",  # Empty URL
            published_at=datetime.now()
        )
        
        mentions = discovery._extract_symbols([article])
        
        # Should still extract the symbol
        assert "AAPL" in mentions
        assert mentions["AAPL"].mention_count == 1
        # Sources might be empty or have a default value
        assert isinstance(mentions["AAPL"].sources, set)
    
    def test_article_with_malformed_url(self, discovery):
        """Test handling of article with malformed URL."""
        article = NewsArticle(
            title="Apple news",
            content="AAPL update",
            url="not-a-valid-url",
            published_at=datetime.now()
        )
        
        mentions = discovery._extract_symbols([article])
        
        # Should still extract the symbol despite URL parsing issues
        assert "AAPL" in mentions
        assert mentions["AAPL"].mention_count == 1
    
    def test_same_source_multiple_articles(self, discovery):
        """Test that same source appearing multiple times is tracked correctly."""
        articles = [
            NewsArticle(
                title="Apple news 1",
                content="AAPL rises",
                url="https://techcrunch.com/article1",
                published_at=datetime.now()
            ),
            NewsArticle(
                title="Apple news 2",
                content="AAPL continues growth",
                url="https://techcrunch.com/article2",
                published_at=datetime.now()
            )
        ]
        
        mentions = discovery._extract_symbols(articles)
        
        # Should have 2 mentions but only 1 unique source
        assert "AAPL" in mentions
        assert mentions["AAPL"].mention_count == 2
        assert len(mentions["AAPL"].sources) == 1
        assert "techcrunch.com" in mentions["AAPL"].sources
    
    def test_company_name_extraction(self, discovery):
        """Test that company names are mapped to symbols."""
        article = NewsArticle(
            title="Apple announces new product",
            content="Apple Inc. revealed a new iPhone today",
            url="https://example.com/article",
            published_at=datetime.now()
        )
        
        mentions = discovery._extract_symbols([article])
        
        # Should extract AAPL from "Apple" company name
        assert "AAPL" in mentions
        assert mentions["AAPL"].mention_count == 1
    
    def test_mixed_ticker_and_company_name(self, discovery):
        """Test article with both ticker symbol and company name."""
        article = NewsArticle(
            title="Apple (AAPL) stock rises",
            content="Apple Inc. shares increased 5% today",
            url="https://example.com/article",
            published_at=datetime.now()
        )
        
        mentions = discovery._extract_symbols([article])
        
        # Should extract AAPL (might count as 1 or more mentions depending on implementation)
        assert "AAPL" in mentions
        assert mentions["AAPL"].mention_count >= 1
