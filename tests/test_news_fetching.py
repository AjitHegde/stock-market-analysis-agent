"""Unit tests for news fetching functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests

from src.news_discovery import NewsDiscovery, NoNewsAvailableError
from src.data_provider import DataProvider, NewsArticle
from src.symbol_lookup import SymbolLookup
from src.config import Configuration


class TestNewsFetching:
    """Test news fetching from multiple providers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Configuration()
        self.data_provider = DataProvider(self.config)
        self.symbol_lookup = SymbolLookup()
        self.discovery = NewsDiscovery(
            self.data_provider,
            self.symbol_lookup,
            max_symbols=50
        )
    
    def test_fetch_news_all_providers_succeed(self):
        """Test fetching news when all providers succeed."""
        # Mock the provider methods
        with patch.object(self.discovery, '_fetch_newsapi_general') as mock_newsapi, \
             patch.object(self.discovery, '_fetch_yahoo_general') as mock_yahoo, \
             patch.object(self.discovery, '_fetch_finnhub_general') as mock_finnhub:
            
            # Create mock articles
            now = datetime.now()
            mock_newsapi.return_value = [
                NewsArticle("NewsAPI Article 1", "Content 1", "http://url1.com", now),
                NewsArticle("NewsAPI Article 2", "Content 2", "http://url2.com", now)
            ]
            mock_yahoo.return_value = [
                NewsArticle("Yahoo Article 1", "Content 3", "http://url3.com", now)
            ]
            mock_finnhub.return_value = [
                NewsArticle("Finnhub Article 1", "Content 4", "http://url4.com", now)
            ]
            
            # Fetch news
            articles = self.discovery._fetch_news(hours_back=24)
            
            # Verify all providers were called
            mock_newsapi.assert_called_once_with(24)
            mock_yahoo.assert_called_once_with(24)
            mock_finnhub.assert_called_once_with(24)
            
            # Verify we got all articles
            assert len(articles) == 4
            assert any("NewsAPI" in a.title for a in articles)
            assert any("Yahoo" in a.title for a in articles)
            assert any("Finnhub" in a.title for a in articles)
    
    def test_fetch_news_one_provider_fails(self):
        """Test fetching news when one provider fails."""
        with patch.object(self.discovery, '_fetch_newsapi_general') as mock_newsapi, \
             patch.object(self.discovery, '_fetch_yahoo_general') as mock_yahoo, \
             patch.object(self.discovery, '_fetch_finnhub_general') as mock_finnhub:
            
            now = datetime.now()
            # NewsAPI fails
            mock_newsapi.side_effect = Exception("NewsAPI error")
            # Other providers succeed
            mock_yahoo.return_value = [
                NewsArticle("Yahoo Article", "Content", "http://url.com", now)
            ]
            mock_finnhub.return_value = [
                NewsArticle("Finnhub Article", "Content", "http://url.com", now)
            ]
            
            # Should not raise exception, should continue with other providers
            articles = self.discovery._fetch_news(hours_back=24)
            
            # Verify we got articles from successful providers
            assert len(articles) == 2
            assert not any("NewsAPI" in a.title for a in articles)
    
    def test_fetch_news_all_providers_fail(self):
        """Test fetching news when all providers fail."""
        with patch.object(self.discovery, '_fetch_newsapi_general') as mock_newsapi, \
             patch.object(self.discovery, '_fetch_yahoo_general') as mock_yahoo, \
             patch.object(self.discovery, '_fetch_finnhub_general') as mock_finnhub:
            
            # All providers fail
            mock_newsapi.side_effect = Exception("NewsAPI error")
            mock_yahoo.side_effect = Exception("Yahoo error")
            mock_finnhub.side_effect = Exception("Finnhub error")
            
            # Should raise NoNewsAvailableError
            with pytest.raises(NoNewsAvailableError):
                self.discovery._fetch_news(hours_back=24)
    
    def test_fetch_news_filters_by_time_range(self):
        """Test that news is filtered by time range."""
        with patch.object(self.discovery, '_fetch_newsapi_general') as mock_newsapi, \
             patch.object(self.discovery, '_fetch_yahoo_general') as mock_yahoo, \
             patch.object(self.discovery, '_fetch_finnhub_general') as mock_finnhub:
            
            now = datetime.now()
            old_time = now - timedelta(hours=48)  # 48 hours ago
            
            # Return mix of old and new articles
            mock_newsapi.return_value = [
                NewsArticle("Recent Article", "Content", "http://url1.com", now),
                NewsArticle("Old Article", "Content", "http://url2.com", old_time)
            ]
            mock_yahoo.return_value = []
            mock_finnhub.return_value = []
            
            # Fetch news from last 24 hours
            articles = self.discovery._fetch_news(hours_back=24)
            
            # Should only get the recent article
            assert len(articles) == 1
            assert articles[0].title == "Recent Article"
    
    def test_fetch_newsapi_general_no_api_key(self):
        """Test NewsAPI fetching when API key is not configured."""
        # Clear API key
        self.discovery.data_provider.config.api_keys = {}
        
        with patch.dict('os.environ', {}, clear=True):
            articles = self.discovery._fetch_newsapi_general(hours_back=24)
            
            # Should return empty list, not raise exception
            assert articles == []
    
    def test_fetch_newsapi_general_rate_limit(self):
        """Test NewsAPI handling of rate limit error."""
        # Mock API key
        self.discovery.data_provider.config.api_keys = {'news_api': 'test_key'}
        
        with patch('requests.get') as mock_get:
            # Mock rate limit response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_get.return_value = mock_response
            
            articles = self.discovery._fetch_newsapi_general(hours_back=24)
            
            # Should return empty list and log warning
            assert articles == []
    
    def test_fetch_newsapi_general_success(self):
        """Test successful NewsAPI fetching."""
        self.discovery.data_provider.config.api_keys = {'news_api': 'test_key'}
        
        with patch('requests.get') as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'articles': [
                    {
                        'title': 'Test Article',
                        'description': 'Test description',
                        'content': 'Test content',
                        'url': 'http://test.com',
                        'publishedAt': '2025-01-15T10:00:00Z'
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            articles = self.discovery._fetch_newsapi_general(hours_back=24)
            
            assert len(articles) == 1
            assert articles[0].title == 'Test Article'
            assert articles[0].content == 'Test description'
    
    def test_fetch_yahoo_general_success(self):
        """Test successful Yahoo Finance fetching."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock ticker news
            mock_instance = Mock()
            now = datetime.now()
            mock_instance.news = [
                {
                    'content': {
                        'title': 'Yahoo Test Article',
                        'summary': 'Test summary',
                        'pubDate': now.isoformat() + 'Z',
                        'canonicalUrl': {'url': 'http://yahoo.com'}
                    }
                }
            ]
            mock_ticker.return_value = mock_instance
            
            articles = self.discovery._fetch_yahoo_general(hours_back=24)
            
            # Should get articles from all indices (3 indices)
            assert len(articles) >= 1
            assert any('Yahoo Test Article' in a.title for a in articles)
    
    def test_fetch_finnhub_general_no_api_key(self):
        """Test Finnhub fetching when API key is not configured."""
        # Clear API key
        self.discovery.data_provider.config.finnhub_api_key = None
        
        articles = self.discovery._fetch_finnhub_general(hours_back=24)
        
        # Should return empty list, not raise exception
        assert articles == []
    
    def test_fetch_finnhub_general_success(self):
        """Test successful Finnhub fetching."""
        self.discovery.data_provider.config.finnhub_api_key = 'test_key'
        
        with patch('requests.get') as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    'headline': 'Finnhub Test Article',
                    'summary': 'Test summary',
                    'url': 'http://finnhub.com',
                    'datetime': int(datetime.now().timestamp())
                }
            ]
            mock_get.return_value = mock_response
            
            articles = self.discovery._fetch_finnhub_general(hours_back=24)
            
            assert len(articles) == 1
            assert articles[0].title == 'Finnhub Test Article'
    
    def test_fetch_news_empty_results_from_providers(self):
        """Test when providers return empty lists."""
        with patch.object(self.discovery, '_fetch_newsapi_general') as mock_newsapi, \
             patch.object(self.discovery, '_fetch_yahoo_general') as mock_yahoo, \
             patch.object(self.discovery, '_fetch_finnhub_general') as mock_finnhub:
            
            # All providers return empty lists
            mock_newsapi.return_value = []
            mock_yahoo.return_value = []
            mock_finnhub.return_value = []
            
            # Should raise NoNewsAvailableError
            with pytest.raises(NoNewsAvailableError):
                self.discovery._fetch_news(hours_back=24)
    
    def test_fetch_news_network_timeout(self):
        """Test handling of network timeout."""
        with patch.object(self.discovery, '_fetch_newsapi_general') as mock_newsapi, \
             patch.object(self.discovery, '_fetch_yahoo_general') as mock_yahoo, \
             patch.object(self.discovery, '_fetch_finnhub_general') as mock_finnhub:
            
            now = datetime.now()
            # NewsAPI times out
            mock_newsapi.side_effect = requests.exceptions.Timeout("Timeout")
            # Other providers succeed
            mock_yahoo.return_value = [
                NewsArticle("Yahoo Article", "Content", "http://url.com", now)
            ]
            mock_finnhub.return_value = []
            
            # Should continue with other providers
            articles = self.discovery._fetch_news(hours_back=24)
            
            assert len(articles) == 1
            assert articles[0].title == "Yahoo Article"

