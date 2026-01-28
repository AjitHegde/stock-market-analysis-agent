"""Basic unit tests for Sentiment Analyzer component."""

import pytest
from datetime import datetime, timedelta
from src.sentiment_analyzer import SentimentAnalyzer
from src.data_provider import NewsArticle, SocialPost
from src.models import SentimentSource, SentimentData


class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Note: This will download the FinBERT model on first run
        self.analyzer = SentimentAnalyzer()
    
    def test_preprocess_text_basic(self):
        """Test basic text preprocessing."""
        text = "Apple announces record earnings! http://example.com @user #stocks"
        
        processed = self.analyzer.preprocess_text(text)
        
        # URLs, mentions, and hashtags should be removed
        assert "http" not in processed
        assert "@user" not in processed
        assert "#stocks" not in processed
        assert "Apple" in processed
        assert "earnings" in processed
    
    def test_extract_sentiment_positive(self):
        """Test sentiment extraction for positive text."""
        text = "Company reports excellent earnings and strong growth prospects"
        
        score, confidence = self.analyzer.extract_sentiment(text)
        
        # Should be positive
        assert score > 0
        assert 0.0 <= confidence <= 1.0
    
    def test_extract_sentiment_negative(self):
        """Test sentiment extraction for negative text."""
        text = "Company faces bankruptcy and massive losses"
        
        score, confidence = self.analyzer.extract_sentiment(text)
        
        # Should be negative
        assert score < 0
        assert 0.0 <= confidence <= 1.0
    
    def test_extract_sentiment_empty(self):
        """Test sentiment extraction for empty text."""
        score, confidence = self.analyzer.extract_sentiment("")
        
        assert score == 0.0
        assert confidence == 0.0
    
    def test_calculate_temporal_weight_recent(self):
        """Test temporal weight for recent content."""
        recent_time = datetime.now() - timedelta(hours=2)
        
        weight = self.analyzer.calculate_temporal_weight(recent_time)
        
        assert weight == 1.0  # Full weight for < 6 hours
    
    def test_calculate_temporal_weight_old(self):
        """Test temporal weight for old content."""
        old_time = datetime.now() - timedelta(hours=30)
        
        weight = self.analyzer.calculate_temporal_weight(old_time)
        
        assert weight == 0.0  # No weight for > 24 hours
    
    def test_calculate_temporal_weight_medium(self):
        """Test temporal weight for medium-age content."""
        medium_time = datetime.now() - timedelta(hours=12)
        
        weight = self.analyzer.calculate_temporal_weight(medium_time)
        
        assert 0.0 < weight < 1.0  # Partial weight
    
    def test_calculate_source_weight_news(self):
        """Test source weight for news."""
        source = SentimentSource(
            source_type="news",
            content="Test",
            score=0.5,
            timestamp=datetime.now(),
            url="http://example.com"
        )
        
        weight = self.analyzer.calculate_source_weight(source)
        
        assert weight == 1.0  # News has full weight
    
    def test_calculate_source_weight_social(self):
        """Test source weight for social media."""
        source = SentimentSource(
            source_type="social",
            content="Test",
            score=0.5,
            timestamp=datetime.now(),
            url="http://example.com"
        )
        
        weight = self.analyzer.calculate_source_weight(source)
        
        assert weight == 0.5  # Social has reduced weight
    
    def test_analyze_news_basic(self):
        """Test news analysis."""
        articles = [
            NewsArticle(
                title="Company reports strong earnings",
                content="The company exceeded expectations with record profits.",
                published_at=datetime.now(),
                url="http://example.com/1"
            )
        ]
        
        sources = self.analyzer.analyze_news(articles)
        
        assert len(sources) == 1
        assert sources[0].source_type == "news"
        assert -1.0 <= sources[0].score <= 1.0
    
    def test_analyze_social_basic(self):
        """Test social media analysis."""
        posts = [
            SocialPost(
                content="Great company with amazing products!",
                author="user123",
                created_at=datetime.now(),
                url="http://example.com/post/1"
            )
        ]
        
        sources = self.analyzer.analyze_social(posts)
        
        assert len(sources) == 1
        assert sources[0].source_type == "social"
        assert -1.0 <= sources[0].score <= 1.0
    
    def test_aggregate_sentiment_empty(self):
        """Test sentiment aggregation with no sources."""
        result = self.analyzer.aggregate_sentiment([], "TEST")
        
        assert result.symbol == "TEST"
        assert result.sentiment_score == 0.0
        assert result.confidence == 0.0
        assert len(result.sources) == 0
    
    def test_aggregate_sentiment_basic(self):
        """Test sentiment aggregation with sources."""
        sources = [
            SentimentSource(
                source_type="news",
                content="Positive news",
                score=0.8,
                timestamp=datetime.now(),
                url="http://example.com/1"
            ),
            SentimentSource(
                source_type="news",
                content="More positive news",
                score=0.6,
                timestamp=datetime.now(),
                url="http://example.com/2"
            )
        ]
        
        result = self.analyzer.aggregate_sentiment(sources, "TEST")
        
        assert result.symbol == "TEST"
        assert -1.0 <= result.sentiment_score <= 1.0
        assert 0.0 <= result.confidence <= 1.0
        assert result.sentiment_score > 0  # Should be positive
    
    def test_aggregate_sentiment_filters_old_sources(self):
        """Test that old sources are filtered out."""
        sources = [
            SentimentSource(
                source_type="news",
                content="Recent news",
                score=0.8,
                timestamp=datetime.now(),
                url="http://example.com/1"
            ),
            SentimentSource(
                source_type="news",
                content="Old news",
                score=-0.8,
                timestamp=datetime.now() - timedelta(hours=30),
                url="http://example.com/2"
            )
        ]
        
        result = self.analyzer.aggregate_sentiment(sources, "TEST")
        
        # Should only use recent source
        assert result.sentiment_score > 0
    
    def test_detect_sentiment_shift_significant(self):
        """Test detection of significant sentiment shift."""
        previous = SentimentData(
            symbol="TEST",
            sentiment_score=0.2,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now() - timedelta(hours=12)
        )
        
        current = SentimentData(
            symbol="TEST",
            sentiment_score=0.6,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        
        shift = self.analyzer.detect_sentiment_shift(current, previous)
        
        assert shift is True  # Change of 0.4 > 0.3 threshold
    
    def test_detect_sentiment_shift_insignificant(self):
        """Test detection when shift is not significant."""
        previous = SentimentData(
            symbol="TEST",
            sentiment_score=0.5,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now() - timedelta(hours=12)
        )
        
        current = SentimentData(
            symbol="TEST",
            sentiment_score=0.6,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        
        shift = self.analyzer.detect_sentiment_shift(current, previous)
        
        assert shift is False  # Change of 0.1 < 0.3 threshold
    
    def test_detect_sentiment_shift_too_old(self):
        """Test that shifts are not detected for old data."""
        previous = SentimentData(
            symbol="TEST",
            sentiment_score=0.0,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now() - timedelta(hours=30)
        )
        
        current = SentimentData(
            symbol="TEST",
            sentiment_score=0.8,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        
        shift = self.analyzer.detect_sentiment_shift(current, previous)
        
        assert shift is False  # Too much time has passed
    
    def test_analyze_complete_workflow(self):
        """Test complete analysis workflow."""
        news = [
            NewsArticle(
                title="Strong earnings report",
                content="Company beats expectations",
                published_at=datetime.now(),
                url="http://example.com/1"
            )
        ]
        
        social = [
            SocialPost(
                content="Love this stock!",
                author="user1",
                created_at=datetime.now(),
                url="http://example.com/post/1"
            )
        ]
        
        result = self.analyzer.analyze(news, social, "TEST")
        
        assert result.symbol == "TEST"
        assert -1.0 <= result.sentiment_score <= 1.0
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.sources) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
