"""News-driven stock discovery module.

This module orchestrates the news-to-symbols workflow, fetching news from multiple
providers, extracting stock symbols, validating and prioritizing them, and returning
a list of discovered stocks ready for analysis.
"""

import logging
import os
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set
from dataclasses import dataclass

from src.data_provider import DataProvider, NewsArticle
from src.symbol_lookup import SymbolLookup


logger = logging.getLogger(__name__)


@dataclass
class SymbolMention:
    """Tracks symbol mentions across articles.
    
    Attributes:
        symbol: Stock ticker symbol
        mention_count: Total number of times symbol was mentioned
        sources: Set of news providers that mentioned the symbol
        articles: List of articles mentioning the symbol
    """
    symbol: str
    mention_count: int
    sources: Set[str]
    articles: List[NewsArticle]


@dataclass
class DiscoveredStock:
    """Represents a discovered stock with metadata.
    
    Attributes:
        symbol: Stock ticker symbol
        mention_count: Total number of mentions across all articles
        sources: List of news providers that mentioned the symbol
        sample_articles: Up to 3 sample articles mentioning the symbol
    """
    symbol: str
    mention_count: int
    sources: List[str]
    sample_articles: List[NewsArticle]


class NoNewsAvailableError(Exception):
    """Raised when all news providers fail to return articles."""
    pass


class NewsDiscovery:
    """Orchestrates news-driven stock discovery.
    
    This class coordinates the entire news-to-symbols workflow:
    1. Fetches news from multiple providers (NewsAPI, Yahoo Finance, Finnhub)
    2. Extracts stock symbols from article text
    3. Validates and deduplicates symbols
    4. Prioritizes symbols by mention count and source diversity
    5. Returns list of discovered stocks ready for analysis
    """
    
    def __init__(
        self,
        data_provider: DataProvider,
        symbol_lookup: SymbolLookup,
        max_symbols: int = 50
    ):
        """Initialize news discovery system.
        
        Args:
            data_provider: Provider for fetching news from multiple sources
            symbol_lookup: Symbol lookup service for validation and mapping
            max_symbols: Maximum number of symbols to analyze (default: 50)
        """
        self.data_provider = data_provider
        self.symbol_lookup = symbol_lookup
        self.max_symbols = max_symbols
        
        # Initialize symbol extractor
        from src.symbol_extractor import SymbolExtractor
        self.extractor = SymbolExtractor(symbol_lookup)
        
        logger.info(f"NewsDiscovery initialized with max_symbols={max_symbols}")
    
    def discover_stocks(self, hours_back: int = 24) -> List[DiscoveredStock]:
        """Discover stocks from recent news.
        
        This is the main entry point for news-driven discovery. It orchestrates
        the complete workflow from fetching news to returning validated symbols.
        
        Args:
            hours_back: How many hours of news to fetch (default: 24)
            
        Returns:
            List of DiscoveredStock objects with metadata, sorted by priority
            
        Raises:
            NoNewsAvailableError: If all news providers fail
            
        Validates: Requirements 1.1, 2.1, 3.1, 3.2, 3.4
        """
        logger.info(f"Starting stock discovery from news (last {hours_back} hours)")
        
        # Phase 1: Fetch news from all providers
        articles = self._fetch_news(hours_back)
        logger.info(f"Fetched {len(articles)} articles from all providers")
        
        # Phase 2: Extract symbols from articles
        mentions = self._extract_symbols(articles)
        logger.info(f"Extracted {len(mentions)} unique symbols from articles")
        
        # Phase 3: Validate and prioritize symbols
        prioritized_symbols = self._validate_and_prioritize(mentions)
        logger.info(f"Validated and prioritized {len(prioritized_symbols)} symbols")
        
        # Phase 4: Create DiscoveredStock objects
        discovered_stocks = []
        for symbol in prioritized_symbols:
            mention = mentions[symbol]
            discovered_stock = DiscoveredStock(
                symbol=symbol,
                mention_count=mention.mention_count,
                sources=list(mention.sources),
                sample_articles=mention.articles[:3]  # Up to 3 sample articles
            )
            discovered_stocks.append(discovered_stock)
        
        logger.info(f"Discovery complete: {len(discovered_stocks)} stocks ready for analysis")
        return discovered_stocks
    
    def _fetch_news(self, hours_back: int) -> List[NewsArticle]:
        """Fetch news from all providers with error handling.
        
        Queries NewsAPI, Yahoo Finance, and Finnhub for market news. Provider
        failures are logged but don't halt execution - the system continues
        with remaining providers.
        
        Deduplicates articles by URL to prevent counting the same article multiple times.
        
        Args:
            hours_back: How many hours of news to fetch
            
        Returns:
            List of unique NewsArticle objects from all successful providers
            
        Raises:
            NoNewsAvailableError: If all providers fail
            
        Validates: Requirements 1.1, 1.2, 1.3, 1.5, 9.1
        """
        logger.info(f"Fetching general market news from last {hours_back} hours")
        
        all_articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Define provider fetch functions
        providers = {
            'NewsAPI': lambda: self._fetch_newsapi_general(hours_back),
            'Yahoo Finance': lambda: self._fetch_yahoo_general(hours_back),
            'Finnhub': lambda: self._fetch_finnhub_general(hours_back)
        }
        
        # Try each provider
        for provider_name, fetch_func in providers.items():
            try:
                logger.info(f"Querying {provider_name}...")
                articles = fetch_func()
                
                # Filter by time range
                filtered_articles = [
                    article for article in articles
                    if article.published_at >= cutoff_time
                ]
                
                all_articles.extend(filtered_articles)
                logger.info(f"Fetched {len(filtered_articles)} articles from {provider_name}")
                
            except Exception as e:
                # Log error but continue with other providers
                logger.warning(f"Failed to fetch from {provider_name}: {str(e)}")
                continue
        
        # Check if we got any articles
        if not all_articles:
            raise NoNewsAvailableError("All news providers failed to return articles")
        
        # Deduplicate articles by URL
        # Some providers (like Yahoo Finance) may return the same article multiple times
        seen_urls = set()
        unique_articles = []
        duplicate_count = 0
        
        for article in all_articles:
            if article.url and article.url in seen_urls:
                duplicate_count += 1
                continue
            
            if article.url:
                seen_urls.add(article.url)
            unique_articles.append(article)
        
        if duplicate_count > 0:
            logger.info(f"Removed {duplicate_count} duplicate articles")
        
        logger.info(f"Total unique articles: {len(unique_articles)}")
        return unique_articles
    
    def _extract_symbols(self, articles: List[NewsArticle]) -> Dict[str, SymbolMention]:
        """Extract symbols from articles with per-article error handling.
        
        Parses each article to extract stock symbols and company names. Individual
        article extraction failures are isolated and don't prevent processing of
        other articles.
        
        Each article counts as 1 mention per symbol, regardless of how many times
        the symbol appears within that article. This prevents duplicate counting.
        
        Args:
            articles: List of news articles to parse
            
        Returns:
            Dictionary mapping symbols to SymbolMention objects
            
        Validates: Requirements 2.1, 3.3, 9.2
        """
        mentions: Dict[str, SymbolMention] = {}
        
        for article in articles:
            try:
                # Combine title and content for extraction
                text = f"{article.title} {article.content}"
                
                # Extract symbols using SymbolExtractor
                # This returns a list that may contain duplicates if symbol appears multiple times
                symbols = self.extractor.extract_from_text(text)
                
                # Deduplicate symbols within this article - each article counts as 1 mention per symbol
                unique_symbols = set(symbols)
                
                # Track each unique symbol from this article
                for symbol in unique_symbols:
                    if symbol not in mentions:
                        # First mention of this symbol
                        mentions[symbol] = SymbolMention(
                            symbol=symbol,
                            mention_count=1,
                            sources=set(),
                            articles=[article]
                        )
                    else:
                        # Additional mention of existing symbol from a different article
                        mentions[symbol].mention_count += 1
                        mentions[symbol].articles.append(article)
                    
                    # Track source (we don't have explicit source field in NewsArticle,
                    # so we'll infer from URL or use a generic identifier)
                    # For now, we'll use the domain from the URL as the source
                    if article.url:
                        try:
                            from urllib.parse import urlparse
                            domain = urlparse(article.url).netloc
                            if domain:
                                mentions[symbol].sources.add(domain)
                        except Exception:
                            # If URL parsing fails, just skip source tracking
                            pass
                
            except Exception as e:
                # Log error but continue with other articles (graceful error handling)
                logger.warning(f"Failed to extract symbols from article '{article.title[:50]}...': {str(e)}")
                continue
        
        return mentions
    
    def _validate_and_prioritize(
        self,
        mentions: Dict[str, SymbolMention]
    ) -> List[str]:
        """Validate, deduplicate, and prioritize symbols.
        
        Validates symbols against the symbol lookup registry, removes duplicates,
        calculates priority scores, and limits to max_symbols.
        
        Priority score formula: (mention_count * 2) + (unique_sources * 3)
        
        Args:
            mentions: Dictionary of symbol mentions
            
        Returns:
            List of validated symbols sorted by priority (highest first),
            limited to max_symbols
            
        Validates: Requirements 3.1, 3.2, 3.4, 3.5, 6.1, 6.2
        """
        logger.info(f"Validating and prioritizing {len(mentions)} symbols")
        
        # Step 1: Deduplicate symbols (already done by using dict keys)
        # The mentions dict already has unique symbols as keys
        
        # Step 2: Validate symbols against SymbolLookup registry
        validated_symbols = []
        invalid_count = 0
        
        for symbol, mention in mentions.items():
            # Check if symbol exists in the registry
            # A symbol is valid if it's in the SYMBOL_MAP values or if it's a known key
            is_valid = False
            
            # Check if it's a value in the map (actual symbol)
            if symbol.upper() in [s.upper() for s in self.symbol_lookup.SYMBOL_MAP.values()]:
                is_valid = True
            # Check if it's a key in the map (company name that maps to a symbol)
            elif symbol.lower() in self.symbol_lookup.SYMBOL_MAP:
                is_valid = True
            # For symbols not in our map, we'll be lenient and accept them
            # if they look like valid ticker symbols (1-5 uppercase letters)
            elif re.match(r'^[A-Z]{1,5}$', symbol):
                is_valid = True
            # Also accept symbols with exchange suffixes like .NS, .BO
            elif re.match(r'^[A-Z]{1,10}\.[A-Z]{1,3}$', symbol):
                is_valid = True
            
            if is_valid:
                validated_symbols.append((symbol, mention))
            else:
                invalid_count += 1
                logger.debug(f"Filtered out invalid symbol: {symbol}")
        
        logger.info(f"Validated {len(validated_symbols)} symbols, filtered out {invalid_count} invalid symbols")
        
        # Step 3: Calculate priority score for each symbol
        # Priority score = (mention_count * 2) + (unique_sources * 3)
        scored_symbols = []
        for symbol, mention in validated_symbols:
            priority_score = (mention.mention_count * 2) + (len(mention.sources) * 3)
            scored_symbols.append((symbol, priority_score, mention))
            logger.debug(f"Symbol {symbol}: mentions={mention.mention_count}, sources={len(mention.sources)}, score={priority_score}")
        
        # Step 4: Sort by priority score descending
        scored_symbols.sort(key=lambda x: x[1], reverse=True)
        
        # Step 5: Limit to max_symbols
        limited_symbols = scored_symbols[:self.max_symbols]
        
        if len(scored_symbols) > self.max_symbols:
            logger.info(f"Limited to top {self.max_symbols} symbols (from {len(scored_symbols)} total)")
        
        # Return just the symbol names
        result = [symbol for symbol, score, mention in limited_symbols]
        
        logger.info(f"Final prioritized list: {len(result)} symbols")
        return result
    
    def _fetch_newsapi_general(self, hours_back: int) -> List[NewsArticle]:
        """Fetch general market news from NewsAPI.
        
        Args:
            hours_back: How many hours of news to fetch
            
        Returns:
            List of NewsArticle objects from NewsAPI
        """
        articles = []
        
        # Check for API key
        newsapi_key = self.data_provider.config.api_keys.get('news_api') or os.getenv('NEWS_API_KEY')
        if not newsapi_key:
            logger.debug("NewsAPI key not configured - skipping NewsAPI")
            return articles
        
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # NewsAPI everything endpoint with market-related keywords
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': 'stock market OR trading OR stocks OR shares OR NYSE OR NASDAQ',
                'from': start_time.isoformat(),
                'to': end_time.isoformat(),
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': newsapi_key,
                'pageSize': 100  # Max results
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                news_items = data.get('articles', [])
                
                for item in news_items:
                    title = item.get('title', '')
                    description = item.get('description', '')
                    content = item.get('content', '')
                    url = item.get('url', '')
                    
                    # Parse timestamp
                    pub_date_str = item.get('publishedAt', '')
                    try:
                        published_at = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        published_at = published_at.replace(tzinfo=None)
                    except:
                        published_at = datetime.now()
                    
                    if not title:
                        continue
                    
                    # Use description or content, whichever is longer
                    description = description or ''
                    content = content or ''
                    article_content = description if len(description) > len(content) else content
                    if not article_content:
                        article_content = title
                    
                    article = NewsArticle(
                        title=title,
                        content=article_content,
                        url=url,
                        published_at=published_at
                    )
                    articles.append(article)
                
                logger.debug(f"Fetched {len(articles)} articles from NewsAPI")
                
            elif response.status_code == 401:
                logger.warning("Invalid NewsAPI key")
            elif response.status_code == 429:
                logger.warning("NewsAPI rate limit exceeded - skipping NewsAPI")
            else:
                logger.warning(f"NewsAPI returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("Timeout fetching from NewsAPI")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching from NewsAPI: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching from NewsAPI: {str(e)}")
        
        return articles
    
    def _fetch_yahoo_general(self, hours_back: int) -> List[NewsArticle]:
        """Fetch general market news from Yahoo Finance.
        
        Args:
            hours_back: How many hours of news to fetch
            
        Returns:
            List of NewsArticle objects from Yahoo Finance
        """
        articles = []
        
        try:
            import yfinance as yf
            
            # Yahoo Finance doesn't have a direct general news API
            # We'll fetch news for major market indices as a proxy for general market news
            indices = ['^GSPC', '^DJI', '^IXIC']  # S&P 500, Dow Jones, NASDAQ
            
            for index_symbol in indices:
                try:
                    ticker = yf.Ticker(index_symbol)
                    news_items = ticker.news
                    
                    if not news_items:
                        continue
                    
                    for item in news_items:
                        content = item.get('content', {})
                        
                        # Parse the timestamp
                        pub_date_str = content.get('pubDate', '')
                        try:
                            published_at = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                            published_at = published_at.replace(tzinfo=None)
                        except:
                            published_at = datetime.now()
                        
                        title = content.get('title', '')
                        summary = content.get('summary', content.get('description', ''))
                        url = content.get('canonicalUrl', {}).get('url', '')
                        
                        if not title:
                            continue
                        
                        article = NewsArticle(
                            title=title,
                            content=summary if summary else title,
                            url=url,
                            published_at=published_at
                        )
                        articles.append(article)
                        
                except Exception as e:
                    logger.debug(f"Error fetching Yahoo news for {index_symbol}: {str(e)}")
                    continue
            
            logger.debug(f"Fetched {len(articles)} articles from Yahoo Finance")
            
        except ImportError:
            logger.error("yfinance not installed - skipping Yahoo Finance")
        except Exception as e:
            logger.error(f"Unexpected error fetching from Yahoo Finance: {str(e)}")
        
        return articles
    
    def _fetch_finnhub_general(self, hours_back: int) -> List[NewsArticle]:
        """Fetch general market news from Finnhub.
        
        Args:
            hours_back: How many hours of news to fetch
            
        Returns:
            List of NewsArticle objects from Finnhub
        """
        articles = []
        
        # Check for API key
        finnhub_key = getattr(self.data_provider.config, 'finnhub_api_key', None)
        if not finnhub_key:
            logger.debug("Finnhub API key not configured - skipping Finnhub")
            return articles
        
        try:
            # Finnhub general market news endpoint
            url = "https://finnhub.io/api/v1/news"
            params = {
                'category': 'general',  # General market news
                'token': finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                news_items = response.json()
                
                for item in news_items:
                    headline = item.get('headline', '')
                    summary = item.get('summary', '')
                    url = item.get('url', '')
                    
                    # Parse timestamp (Unix timestamp)
                    timestamp = item.get('datetime', 0)
                    if timestamp:
                        published_at = datetime.fromtimestamp(timestamp)
                    else:
                        published_at = datetime.now()
                    
                    if not headline:
                        continue
                    
                    article = NewsArticle(
                        title=headline,
                        content=summary if summary else headline,
                        url=url,
                        published_at=published_at
                    )
                    articles.append(article)
                
                logger.debug(f"Fetched {len(articles)} articles from Finnhub")
                
            elif response.status_code == 401:
                logger.warning("Invalid Finnhub API key")
            elif response.status_code == 429:
                logger.warning("Finnhub rate limit exceeded - skipping Finnhub")
            else:
                logger.warning(f"Finnhub API returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("Timeout fetching from Finnhub")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching from Finnhub: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching from Finnhub: {str(e)}")
        
        return articles
