"""Sentiment analyzer using FinBERT for financial text analysis."""

import re
import math
from datetime import datetime, timedelta
from typing import List, Tuple
import logging

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from .models import SentimentData, SentimentSource
from .data_provider import NewsArticle, SocialPost


logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment from news and social media using FinBERT."""
    
    def __init__(self):
        """Initialize the sentiment analyzer with FinBERT model."""
        logger.info("Loading FinBERT model...")
        
        # Load FinBERT model and tokenizer
        model_name = "ProsusAI/finbert"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Set model to evaluation mode
        self.model.eval()
        
        logger.info("FinBERT model loaded successfully")
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for sentiment analysis.
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            Preprocessed text
        """
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove mentions and hashtags
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove special characters but keep financial symbols
        text = re.sub(r'[^\w\s$%.]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def extract_sentiment(self, text: str) -> Tuple[float, float]:
        """Extract sentiment score from text using FinBERT.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment_score, confidence)
            - sentiment_score: -1.0 (negative) to +1.0 (positive)
            - confidence: 0.0 to 1.0
        """
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        if not processed_text.strip():
            return 0.0, 0.0
        
        # Tokenize
        inputs = self.tokenizer(
            processed_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # FinBERT outputs: [positive, negative, neutral]
        positive_prob = predictions[0][0].item()
        negative_prob = predictions[0][1].item()
        neutral_prob = predictions[0][2].item()
        
        # Convert to sentiment score: -1.0 to +1.0
        sentiment_score = positive_prob - negative_prob
        
        # Confidence is the maximum probability
        confidence = max(positive_prob, negative_prob, neutral_prob)
        
        return sentiment_score, confidence
    
    def calculate_temporal_weight(self, timestamp: datetime) -> float:
        """Calculate temporal weight for a sentiment source.
        
        Recent content is weighted more heavily than older content.
        
        Args:
            timestamp: When the content was published
            
        Returns:
            Weight between 0.0 and 1.0
        """
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        
        # Exclude content older than 7 days (168 hours)
        if age_hours > 168:
            return 0.0
        
        # Full weight for very recent content (< 24 hours)
        if age_hours < 24:
            return 1.0
        
        # Exponential decay: weight = e^(-age/48)
        # Slower decay over 7 days instead of 24 hours
        return math.exp(-age_hours / 48)
    
    def calculate_source_weight(self, source: SentimentSource) -> float:
        """Calculate weight for a sentiment source based on reliability.
        
        Args:
            source: Sentiment source to weight
            
        Returns:
            Weight multiplier
        """
        # Base weights by source type
        base_weights = {
            'news': 1.0,    # Professional journalism
            'social': 0.5,  # Social media posts
        }
        
        weight = base_weights.get(source.source_type, 0.5)
        
        # Note: In production, you could boost for verified sources
        # or high-engagement content based on additional metadata
        
        return weight
    
    def analyze_news(self, articles: List[NewsArticle]) -> List[SentimentSource]:
        """Extract sentiment from news articles.
        
        Args:
            articles: List of news articles
            
        Returns:
            List of SentimentSource objects
        """
        sources = []
        
        for article in articles:
            # Combine title and content for analysis
            text = f"{article.title}. {article.content}"
            
            # Extract sentiment
            score, confidence = self.extract_sentiment(text)
            
            # Create sentiment source
            source = SentimentSource(
                source_type="news",
                content=text[:500],  # Store first 500 chars
                score=score,
                timestamp=article.published_at,
                url=article.url
            )
            
            sources.append(source)
            
            logger.debug(
                f"News sentiment: {score:.2f} (confidence: {confidence:.2f}) "
                f"from {article.url}"
            )
        
        return sources
    
    def analyze_social(self, posts: List[SocialPost]) -> List[SentimentSource]:
        """Extract sentiment from social media posts.
        
        Args:
            posts: List of social media posts
            
        Returns:
            List of SentimentSource objects
        """
        sources = []
        
        for post in posts:
            # Extract sentiment
            score, confidence = self.extract_sentiment(post.content)
            
            # Create sentiment source
            source = SentimentSource(
                source_type="social",
                content=post.content[:500],  # Store first 500 chars
                score=score,
                timestamp=post.created_at,
                url=post.url
            )
            
            sources.append(source)
            
            logger.debug(
                f"Social sentiment: {score:.2f} (confidence: {confidence:.2f}) "
                f"from {post.author}"
            )
        
        return sources
    
    def aggregate_sentiment(
        self,
        sources: List[SentimentSource],
        symbol: str
    ) -> SentimentData:
        """Combine multiple sentiment sources into overall score.
        
        Args:
            sources: List of sentiment sources
            symbol: Stock ticker symbol
            
        Returns:
            SentimentData with aggregated sentiment
        """
        if not sources:
            logger.warning(f"No sentiment sources for {symbol}")
            return SentimentData(
                symbol=symbol,
                sentiment_score=0.0,
                confidence=0.0,
                sources=[],
                timestamp=datetime.now()
            )
        
        # Apply confidence penalty for few sources
        confidence_penalty = 1.0 if len(sources) >= 5 else 0.5
        
        weighted_scores = []
        weighted_confidences = []
        total_weight = 0.0
        
        for source in sources:
            # Calculate weights
            temporal_weight = self.calculate_temporal_weight(source.timestamp)
            
            # Skip sources older than 24 hours
            if temporal_weight == 0.0:
                continue
            
            source_weight = self.calculate_source_weight(source)
            
            # Combined weight
            weight = temporal_weight * source_weight
            total_weight += weight
            
            # Weighted contributions
            weighted_scores.append(source.score * weight)
            # Assume confidence of 0.8 for each source (could be stored in source)
            weighted_confidences.append(0.8 * weight)
        
        # Calculate weighted averages
        if total_weight > 0:
            sentiment_score = sum(weighted_scores) / total_weight
            confidence = sum(weighted_confidences) / total_weight * confidence_penalty
        else:
            sentiment_score = 0.0
            confidence = 0.0
        
        # Clamp to valid ranges
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        confidence = max(0.0, min(1.0, confidence))
        
        # Calculate direction and strength
        if sentiment_score > 0.2:
            direction = "bullish"
            strength = abs(sentiment_score)
        elif sentiment_score < -0.2:
            direction = "bearish"
            strength = abs(sentiment_score)
        else:
            direction = "neutral"
            strength = abs(sentiment_score) * 0.3  # Reduced strength for neutral
        
        logger.info(
            f"Aggregated sentiment for {symbol}: {sentiment_score:.2f} "
            f"(direction: {direction}, strength: {strength:.2f}, confidence: {confidence:.2f}) "
            f"from {len(sources)} sources"
        )
        
        return SentimentData(
            symbol=symbol,
            sentiment_score=sentiment_score,
            confidence=confidence,
            sources=sources,
            timestamp=datetime.now(),
            direction=direction,
            strength=strength
        )
    
    def detect_sentiment_shift(
        self,
        current: SentimentData,
        previous: SentimentData
    ) -> bool:
        """Detect significant sentiment changes.
        
        Args:
            current: Current sentiment data
            previous: Previous sentiment data
            
        Returns:
            True if significant shift detected, False otherwise
        """
        # Check if data is from within 24 hours
        time_diff = (current.timestamp - previous.timestamp).total_seconds() / 3600
        if time_diff > 24:
            return False
        
        # Check if change exceeds threshold
        score_change = abs(current.sentiment_score - previous.sentiment_score)
        
        if score_change > 0.3:
            logger.info(
                f"Sentiment shift detected for {current.symbol}: "
                f"{previous.sentiment_score:.2f} -> {current.sentiment_score:.2f} "
                f"(change: {score_change:.2f})"
            )
            return True
        
        return False
    
    def analyze(
        self,
        news: List[NewsArticle],
        social: List[SocialPost],
        symbol: str
    ) -> SentimentData:
        """Perform complete sentiment analysis.
        
        Args:
            news: List of news articles
            social: List of social media posts
            symbol: Stock ticker symbol
            
        Returns:
            SentimentData with aggregated sentiment
        """
        logger.info(f"Analyzing sentiment for {symbol}")
        
        # Extract sentiment from all sources
        news_sources = self.analyze_news(news)
        social_sources = self.analyze_social(social)
        
        # Combine all sources
        all_sources = news_sources + social_sources
        
        # Aggregate into final sentiment
        sentiment_data = self.aggregate_sentiment(all_sources, symbol)
        
        return sentiment_data
