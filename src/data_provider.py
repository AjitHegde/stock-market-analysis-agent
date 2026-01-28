"""Data provider for fetching market data from external APIs."""

import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import requests

from cachetools import TTLCache
import yfinance as yf

from .models import StockData, PricePoint
from .config import Configuration


logger = logging.getLogger(__name__)


class NewsArticle:
    """Represents a news article."""
    
    def __init__(self, title: str, content: str, url: str, published_at: datetime):
        self.title = title
        self.content = content
        self.url = url
        self.published_at = published_at


class SocialPost:
    """Represents a social media post."""
    
    def __init__(self, content: str, author: str, url: str, created_at: datetime, engagement_score: int = 0):
        self.content = content
        self.author = author
        self.url = url
        self.created_at = created_at
        self.engagement_score = engagement_score


class CompanyFinancials:
    """Represents company financial data."""
    
    def __init__(
        self,
        symbol: str,
        market_cap: Optional[float] = None,
        pe_ratio: Optional[float] = None,
        pb_ratio: Optional[float] = None,
        debt_to_equity: Optional[float] = None,
        eps: Optional[float] = None,
        revenue: Optional[float] = None,
        revenue_growth: Optional[float] = None,
        book_value: Optional[float] = None,
    ):
        self.symbol = symbol
        self.market_cap = market_cap
        self.pe_ratio = pe_ratio
        self.pb_ratio = pb_ratio
        self.debt_to_equity = debt_to_equity
        self.eps = eps
        self.revenue = revenue
        self.revenue_growth = revenue_growth
        self.book_value = book_value


class DataProvider:
    """Provides market data from external APIs with caching and retry logic."""
    
    def __init__(self, config: Configuration):
        """Initialize the data provider.
        
        Args:
            config: Configuration object with API keys and settings
        """
        self.config = config
        self.cache = TTLCache(maxsize=100, ttl=config.cache_ttl_seconds)
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff in seconds
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        
        raise last_exception
    
    def get_stock_data(self, symbol: str) -> StockData:
        """Fetch current and historical stock data.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            StockData object with current and historical prices
            
        Raises:
            ValueError: If symbol is invalid
            Exception: If data retrieval fails after retries
        """
        cache_key = f"stock_data_{symbol}"
        
        # Check cache first
        if cache_key in self.cache:
            logger.info(f"Cache hit for {symbol} stock data")
            return self.cache[cache_key]
        
        logger.info(f"Fetching stock data for {symbol}")
        
        def fetch_data():
            ticker = yf.Ticker(symbol)
            
            # Get current data
            info = ticker.info
            if not info or 'regularMarketPrice' not in info:
                raise ValueError(f"Invalid symbol: {symbol}")
            
            current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
            volume = info.get('volume', 0)
            
            # Get historical data (200+ days)
            hist = ticker.history(period="1y")  # Get 1 year of data
            
            if hist.empty or len(hist) < 200:
                raise ValueError(f"Insufficient historical data for {symbol}")
            
            # Convert to PricePoint objects
            historical_prices = []
            for date, row in hist.iterrows():
                price_point = PricePoint(
                    date=date.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
                historical_prices.append(price_point)
            
            stock_data = StockData(
                symbol=symbol.upper(),
                current_price=float(current_price),
                volume=int(volume),
                timestamp=datetime.now(),
                historical_prices=historical_prices
            )
            
            return stock_data
        
        # Fetch with retry logic
        stock_data = self._retry_with_backoff(fetch_data)
        
        # Cache the result
        self.cache[cache_key] = stock_data
        logger.info(f"Cached stock data for {symbol}")
        
        return stock_data
    
    def get_news(self, symbol: str, days: int = 7) -> List[NewsArticle]:
        """Fetch news articles for a stock from multiple sources.
        
        Combines news from:
        1. Yahoo Finance (free, no API key needed)
        2. Finnhub (free tier with API key)
        3. NewsAPI (requires API key)
        
        Args:
            symbol: Stock ticker symbol
            days: Number of days to look back (default: 7)
            
        Returns:
            List of NewsArticle objects from all sources
        """
        cache_key = f"news_{symbol}_{days}"
        
        # Check cache first
        if cache_key in self.cache:
            logger.info(f"Cache hit for {symbol} news")
            return self.cache[cache_key]
        
        logger.info(f"Fetching news for {symbol} from multiple sources")
        
        all_articles = []
        
        # Fetch from Yahoo Finance
        yahoo_articles = self._fetch_yahoo_news(symbol, days)
        all_articles.extend(yahoo_articles)
        
        # Fetch from Finnhub if API key is available
        finnhub_articles = self._fetch_finnhub_news(symbol, days)
        all_articles.extend(finnhub_articles)
        
        # Fetch from NewsAPI if API key is available
        newsapi_articles = self._fetch_newsapi_news(symbol, days)
        all_articles.extend(newsapi_articles)
        
        # Remove duplicates based on title similarity
        unique_articles = self._deduplicate_articles(all_articles)
        
        logger.info(f"Fetched {len(unique_articles)} unique news articles for {symbol} "
                   f"(Yahoo: {len(yahoo_articles)}, Finnhub: {len(finnhub_articles)}, NewsAPI: {len(newsapi_articles)})")
        
        # Cache the result
        self.cache[cache_key] = unique_articles
        
        return unique_articles
    
    def _fetch_yahoo_news(self, symbol: str, days: int) -> List[NewsArticle]:
        """Fetch news from Yahoo Finance."""
        def fetch_news():
            ticker = yf.Ticker(symbol)
            articles = []
            
            try:
                news_items = ticker.news
                
                if not news_items:
                    logger.debug(f"No Yahoo Finance news found for {symbol}")
                    return articles
                
                cutoff_date = datetime.now()
                
                for item in news_items:
                    content = item.get('content', {})
                    
                    # Parse the timestamp
                    pub_date_str = content.get('pubDate', '')
                    try:
                        published_at = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        published_at = published_at.replace(tzinfo=None)
                    except:
                        published_at = datetime.now()
                    
                    # Filter by date
                    age_days = (cutoff_date - published_at).days
                    if age_days > days:
                        continue
                    
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
                
                logger.debug(f"Fetched {len(articles)} articles from Yahoo Finance")
                
            except Exception as e:
                logger.error(f"Error fetching Yahoo Finance news for {symbol}: {str(e)}")
            
            return articles
        
        try:
            return self._retry_with_backoff(fetch_news)
        except Exception as e:
            logger.warning(f"Failed to fetch Yahoo Finance news: {str(e)}")
            return []
    
    def _fetch_finnhub_news(self, symbol: str, days: int) -> List[NewsArticle]:
        """Fetch news from Finnhub."""
        finnhub_key = getattr(self.config, 'finnhub_api_key', None)
        if not finnhub_key:
            logger.debug("Finnhub API key not configured - skipping Finnhub news")
            return []
        
        def fetch_news():
            articles = []
            
            try:
                # Calculate date range
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                # Finnhub company news endpoint
                url = f"https://finnhub.io/api/v1/company-news"
                params = {
                    'symbol': symbol,
                    'from': start_date,
                    'to': end_date,
                    'token': finnhub_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    news_items = response.json()
                    
                    for item in news_items:
                        # Extract article data
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
                elif response.status_code == 403:
                    # 403 is expected for stocks not supported by Finnhub (e.g., Indian stocks)
                    logger.debug(f"Finnhub doesn't support this stock (403)")
                elif response.status_code == 429:
                    logger.warning("Finnhub rate limit exceeded")
                else:
                    logger.warning(f"Finnhub API returned status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error fetching Finnhub news: {str(e)}")
            
            return articles
        
        try:
            return self._retry_with_backoff(fetch_news)
        except Exception as e:
            logger.debug(f"Failed to fetch Finnhub news: {str(e)}")
            return []
    
    def _fetch_newsapi_news(self, symbol: str, days: int) -> List[NewsArticle]:
        """Fetch news from NewsAPI."""
        newsapi_key = self.config.api_keys.get('news_api') or os.getenv('NEWS_API_KEY')
        if not newsapi_key:
            logger.debug("NewsAPI key not configured - skipping NewsAPI news")
            return []
        
        def fetch_news():
            articles = []
            
            try:
                # Calculate date range
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                # Create search query - remove exchange suffixes for better results
                search_query = symbol.replace('.NS', '').replace('.BO', '').replace('.', ' ')
                
                # Add common company name mappings for better Indian stock coverage
                company_mappings = {
                    'IDFCFIRSTB': 'IDFC First Bank',
                    'HDFCBANK': 'HDFC Bank',
                    'RELIANCE': 'Reliance Industries',
                    'TCS': 'Tata Consultancy Services',
                    'INFY': 'Infosys',
                    'ICICIBANK': 'ICICI Bank',
                    'WIPRO': 'Wipro',
                    'BHARTIARTL': 'Bharti Airtel',
                }
                
                # Use company name if available, otherwise use cleaned symbol
                search_query = company_mappings.get(search_query, search_query)
                
                # NewsAPI everything endpoint
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': search_query,  # Search query
                    'from': start_date,
                    'to': end_date,
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
                        # Extract article data
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
                        
                        # Use description or content, whichever is longer (handle None values)
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
                    
                    logger.debug(f"Fetched {len(articles)} articles from NewsAPI for query '{search_query}'")
                    
                elif response.status_code == 401:
                    logger.warning("Invalid NewsAPI key")
                elif response.status_code == 429:
                    logger.warning("NewsAPI rate limit exceeded")
                else:
                    logger.warning(f"NewsAPI returned status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error fetching NewsAPI news: {str(e)}")
            
            return articles
        
        try:
            return self._retry_with_backoff(fetch_news)
        except Exception as e:
            logger.warning(f"Failed to fetch NewsAPI news: {str(e)}")
            return []
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on title similarity."""
        if not articles:
            return articles
        
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # Normalize title for comparison (lowercase, remove extra spaces)
            normalized_title = ' '.join(article.title.lower().split())
            
            # Check if we've seen a very similar title
            is_duplicate = False
            for seen_title in seen_titles:
                # Simple similarity check: if titles share 80%+ words, consider duplicate
                title_words = set(normalized_title.split())
                seen_words = set(seen_title.split())
                
                if len(title_words) > 0 and len(seen_words) > 0:
                    overlap = len(title_words & seen_words)
                    similarity = overlap / max(len(title_words), len(seen_words))
                    
                    if similarity > 0.8:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.add(normalized_title)
        
        return unique_articles
    
    def get_social_media(self, symbol: str, hours: int = 24) -> List[SocialPost]:
        """Fetch social media sentiment from Finnhub.
        
        Uses Finnhub's social sentiment endpoint which aggregates data from
        Twitter, Reddit, and other sources. Requires FINNHUB_API_KEY in config.
        
        Free tier: 60 API calls/minute
        Endpoint: https://finnhub.io/api/v1/stock/social-sentiment
        
        Args:
            symbol: Stock ticker symbol
            hours: Number of hours to look back (default: 24)
            
        Returns:
            List of SocialPost objects with aggregated sentiment data
        """
        cache_key = f"social_{symbol}_{hours}"
        
        # Check cache first
        if cache_key in self.cache:
            logger.info(f"Cache hit for {symbol} social media")
            return self.cache[cache_key]
        
        logger.info(f"Fetching social sentiment for {symbol} from Finnhub")
        
        def fetch_social():
            posts = []
            
            # Check if Finnhub API key is configured
            finnhub_key = getattr(self.config, 'finnhub_api_key', None)
            if not finnhub_key:
                logger.info("Finnhub API key not configured - skipping social sentiment")
                return posts
            
            try:
                # Finnhub Social Sentiment endpoint
                url = f"https://finnhub.io/api/v1/stock/social-sentiment"
                
                params = {
                    'symbol': symbol,
                    'token': finnhub_key
                }
                
                headers = {
                    'User-Agent': 'StockMarketAIAgent/1.0'
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Finnhub returns aggregated sentiment data
                    # Structure: {"reddit": {...}, "twitter": {...}, "symbol": "AAPL"}
                    
                    reddit_data = data.get('reddit', {})
                    twitter_data = data.get('twitter', {})
                    
                    cutoff_time = datetime.now() - timedelta(hours=hours)
                    
                    # Process Reddit sentiment
                    if reddit_data:
                        mention = reddit_data.get('mention', 0)
                        positive_mention = reddit_data.get('positiveMention', 0)
                        negative_mention = reddit_data.get('negativeMention', 0)
                        score = reddit_data.get('score', 0)
                        
                        if mention > 0:
                            # Create aggregated post for Reddit
                            sentiment_score = (positive_mention - negative_mention) / mention if mention > 0 else 0
                            
                            post = SocialPost(
                                content=f"Reddit sentiment: {positive_mention} positive, {negative_mention} negative out of {mention} mentions",
                                author="reddit_aggregate",
                                url=f"https://reddit.com/r/stocks/search?q={symbol}",
                                created_at=datetime.now(),
                                engagement_score=int(mention * abs(sentiment_score) * 10)
                            )
                            posts.append(post)
                    
                    # Process Twitter sentiment
                    if twitter_data:
                        mention = twitter_data.get('mention', 0)
                        positive_mention = twitter_data.get('positiveMention', 0)
                        negative_mention = twitter_data.get('negativeMention', 0)
                        score = twitter_data.get('score', 0)
                        
                        if mention > 0:
                            # Create aggregated post for Twitter
                            sentiment_score = (positive_mention - negative_mention) / mention if mention > 0 else 0
                            
                            post = SocialPost(
                                content=f"Twitter sentiment: {positive_mention} positive, {negative_mention} negative out of {mention} mentions",
                                author="twitter_aggregate",
                                url=f"https://twitter.com/search?q=${symbol}",
                                created_at=datetime.now(),
                                engagement_score=int(mention * abs(sentiment_score) * 10)
                            )
                            posts.append(post)
                    
                    logger.info(f"Fetched {len(posts)} social sentiment sources for {symbol} from Finnhub")
                    
                elif response.status_code == 401:
                    logger.warning(f"Invalid Finnhub API key")
                elif response.status_code == 403:
                    # 403 is expected for free tier - social sentiment requires paid plan
                    logger.debug(f"Finnhub social sentiment not available (requires paid plan)")
                elif response.status_code == 429:
                    logger.warning(f"Finnhub rate limit exceeded")
                    raise Exception("Rate limit exceeded")
                else:
                    logger.warning(f"Finnhub API returned status {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout fetching social sentiment for {symbol}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error fetching social sentiment: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error fetching social sentiment: {str(e)}")
            
            return posts
        
        # Fetch with retry logic
        try:
            posts = self._retry_with_backoff(fetch_social)
        except Exception as e:
            logger.debug(f"Failed to fetch Finnhub social sentiment after retries: {str(e)}")
            posts = []
        
        # Cache the result
        self.cache[cache_key] = posts
        
        return posts
    
    def get_company_financials(self, symbol: str) -> CompanyFinancials:
        """Fetch company financial data.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            CompanyFinancials object
            
        Raises:
            ValueError: If symbol is invalid
            Exception: If data retrieval fails after retries
        """
        cache_key = f"financials_{symbol}"
        
        # Check cache first
        if cache_key in self.cache:
            logger.info(f"Cache hit for {symbol} financials")
            return self.cache[cache_key]
        
        logger.info(f"Fetching financials for {symbol}")
        
        def fetch_financials():
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                raise ValueError(f"Invalid symbol: {symbol}")
            
            # Extract financial metrics
            financials = CompanyFinancials(
                symbol=symbol.upper(),
                market_cap=info.get('marketCap'),
                pe_ratio=info.get('trailingPE') or info.get('forwardPE'),
                pb_ratio=info.get('priceToBook'),
                debt_to_equity=info.get('debtToEquity'),
                eps=info.get('trailingEps') or info.get('forwardEps'),
                revenue=info.get('totalRevenue'),
                # Normalize revenue_growth: Yahoo returns decimal (0.15), convert to percentage (15.0)
                revenue_growth=info.get('revenueGrowth') * 100 if info.get('revenueGrowth') is not None else None,
                book_value=info.get('bookValue'),
            )
            
            return financials
        
        # Fetch with retry logic
        financials = self._retry_with_backoff(fetch_financials)
        
        # Cache the result
        self.cache[cache_key] = financials
        logger.info(f"Cached financials for {symbol}")
        
        return financials
