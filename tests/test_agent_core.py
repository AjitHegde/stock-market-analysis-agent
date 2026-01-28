"""Unit tests for Agent Core."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.agent_core import AgentCore, AnalysisError
from src.config import Configuration
from src.models import (
    StockData,
    PricePoint,
    SentimentData,
    SentimentSource,
    TechnicalIndicators,
    FundamentalMetrics,
    Recommendation,
    Position
)
from src.data_provider import CompanyFinancials


@pytest.fixture
def config():
    """Create test configuration."""
    return Configuration(
        sentiment_weight=0.5,
        technical_weight=0.3,
        fundamental_weight=0.2,
        risk_tolerance='moderate'
    )


@pytest.fixture
def mock_stock_data():
    """Create mock stock data."""
    # Create 250 days of price data
    prices = []
    base_price = 150.0
    for i in range(250):
        date = datetime.now() - timedelta(days=250-i)
        price = base_price + (i * 0.1)  # Trending up
        prices.append(PricePoint(
            date=date,
            open=price,
            high=price * 1.02,
            low=price * 0.98,
            close=price,
            volume=1000000
        ))
    
    return StockData(
        symbol='AAPL',
        current_price=175.0,
        volume=5000000,
        timestamp=datetime.now(),
        historical_prices=prices
    )


@pytest.fixture
def mock_financials():
    """Create mock company financials."""
    return CompanyFinancials(
        symbol='AAPL',
        pe_ratio=25.0,
        pb_ratio=10.0,
        debt_to_equity=0.5,
        eps=6.0,
        revenue_growth=15.0
    )


class TestAgentCoreInitialization:
    """Tests for Agent Core initialization."""
    
    def test_init_creates_all_components(self, config):
        """Test that initialization creates all required components."""
        agent = AgentCore(config)
        
        assert agent.config == config
        assert agent.data_provider is not None
        assert agent.sentiment_analyzer is not None
        assert agent.technical_analyzer is not None
        assert agent.fundamental_analyzer is not None
        assert agent.recommendation_engine is not None
        assert agent.risk_manager is not None


class TestAnalyzeStock:
    """Tests for stock analysis workflow."""
    
    @patch('src.agent_core.DataProvider')
    @patch('src.agent_core.SentimentAnalyzer')
    @patch('src.agent_core.TechnicalAnalyzer')
    @patch('src.agent_core.FundamentalAnalyzer')
    @patch('src.agent_core.RecommendationEngine')
    def test_successful_analysis_without_portfolio(
        self,
        mock_rec_engine,
        mock_fund_analyzer,
        mock_tech_analyzer,
        mock_sent_analyzer,
        mock_data_provider,
        config,
        mock_stock_data,
        mock_financials
    ):
        """Test successful analysis without portfolio."""
        # Setup mocks
        data_provider_instance = Mock()
        data_provider_instance.get_stock_data.return_value = mock_stock_data
        data_provider_instance.get_news.return_value = []
        data_provider_instance.get_social_media.return_value = []
        data_provider_instance.get_company_financials.return_value = mock_financials
        mock_data_provider.return_value = data_provider_instance
        
        sentiment_data = SentimentData(
            symbol='AAPL',
            sentiment_score=0.5,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        sent_analyzer_instance = Mock()
        sent_analyzer_instance.analyze.return_value = sentiment_data
        mock_sent_analyzer.return_value = sent_analyzer_instance
        
        technical_indicators = TechnicalIndicators(
            symbol='AAPL',
            ma_20=170.0,
            ma_50=165.0,
            ma_200=160.0,
            rsi=55.0,
            macd=1.5,
            macd_signal=1.0,
            support_levels=[160.0, 165.0],
            resistance_levels=[180.0, 185.0],
            technical_score=0.4
        )
        tech_analyzer_instance = Mock()
        tech_analyzer_instance.analyze.return_value = technical_indicators
        mock_tech_analyzer.return_value = tech_analyzer_instance
        
        fundamental_metrics = FundamentalMetrics(
            symbol='AAPL',
            pe_ratio=25.0,
            fundamental_score=0.3
        )
        fund_analyzer_instance = Mock()
        fund_analyzer_instance.analyze.return_value = fundamental_metrics
        mock_fund_analyzer.return_value = fund_analyzer_instance
        
        recommendation = Recommendation(
            symbol='AAPL',
            action='BUY',
            confidence=0.75,
            reasoning='Test reasoning',
            sentiment_contribution=0.25,
            technical_contribution=0.12,
            fundamental_contribution=0.06,
            timestamp=datetime.now(),
            entry_price_low=170.0,
            entry_price_high=180.0
        )
        rec_engine_instance = Mock()
        rec_engine_instance.generate_recommendation.return_value = recommendation
        mock_rec_engine.return_value = rec_engine_instance
        
        # Create agent and analyze
        agent = AgentCore(config)
        result = agent.analyze_stock('AAPL')
        
        # Verify result
        assert result.symbol == 'AAPL'
        assert result.sentiment == sentiment_data
        assert result.technical == technical_indicators
        assert result.fundamental == fundamental_metrics
        assert result.recommendation == recommendation
        assert result.risk_assessment is None
    
    @patch('src.agent_core.DataProvider')
    def test_analysis_with_invalid_symbol(self, mock_data_provider, config):
        """Test analysis with invalid stock symbol."""
        # Setup mock to raise ValueError
        data_provider_instance = Mock()
        data_provider_instance.get_stock_data.side_effect = ValueError("Invalid symbol: INVALID")
        mock_data_provider.return_value = data_provider_instance
        
        # Create agent
        agent = AgentCore(config)
        
        # Verify error is raised
        with pytest.raises(AnalysisError, match="Invalid symbol or insufficient data"):
            agent.analyze_stock('INVALID')
    
    @patch('src.agent_core.DataProvider')
    @patch('src.agent_core.SentimentAnalyzer')
    @patch('src.agent_core.TechnicalAnalyzer')
    @patch('src.agent_core.FundamentalAnalyzer')
    def test_graceful_degradation_sentiment_failure(
        self,
        mock_fund_analyzer,
        mock_tech_analyzer,
        mock_sent_analyzer,
        mock_data_provider,
        config,
        mock_stock_data,
        mock_financials
    ):
        """Test graceful degradation when sentiment analysis fails."""
        # Setup mocks
        data_provider_instance = Mock()
        data_provider_instance.get_stock_data.return_value = mock_stock_data
        data_provider_instance.get_news.return_value = []
        data_provider_instance.get_social_media.return_value = []
        data_provider_instance.get_company_financials.return_value = mock_financials
        mock_data_provider.return_value = data_provider_instance
        
        # Sentiment analyzer fails
        sent_analyzer_instance = Mock()
        sent_analyzer_instance.analyze.side_effect = Exception("Sentiment analysis failed")
        mock_sent_analyzer.return_value = sent_analyzer_instance
        
        # Technical analyzer succeeds
        technical_indicators = TechnicalIndicators(
            symbol='AAPL',
            ma_20=170.0,
            ma_50=165.0,
            ma_200=160.0,
            rsi=55.0,
            macd=1.5,
            macd_signal=1.0,
            support_levels=[160.0],
            resistance_levels=[180.0],
            technical_score=0.4
        )
        tech_analyzer_instance = Mock()
        tech_analyzer_instance.analyze.return_value = technical_indicators
        mock_tech_analyzer.return_value = tech_analyzer_instance
        
        # Fundamental analyzer succeeds
        fundamental_metrics = FundamentalMetrics(
            symbol='AAPL',
            fundamental_score=0.3
        )
        fund_analyzer_instance = Mock()
        fund_analyzer_instance.analyze.return_value = fundamental_metrics
        mock_fund_analyzer.return_value = fund_analyzer_instance
        
        # Create agent and analyze
        agent = AgentCore(config)
        result = agent.analyze_stock('AAPL')
        
        # Verify neutral sentiment was used
        assert result.sentiment.sentiment_score == 0.0
        assert result.sentiment.confidence == 0.0
        assert len(result.sentiment.sources) == 0
        
        # Other analyses should succeed
        assert result.technical == technical_indicators
        assert result.fundamental == fundamental_metrics


class TestDataFetching:
    """Tests for data fetching."""
    
    @patch('src.agent_core.DataProvider')
    def test_fetch_all_data_success(
        self,
        mock_data_provider,
        config,
        mock_stock_data,
        mock_financials
    ):
        """Test successful data fetching."""
        # Setup mocks
        data_provider_instance = Mock()
        data_provider_instance.get_stock_data.return_value = mock_stock_data
        data_provider_instance.get_news.return_value = []
        data_provider_instance.get_social_media.return_value = []
        data_provider_instance.get_company_financials.return_value = mock_financials
        mock_data_provider.return_value = data_provider_instance
        
        # Create agent
        agent = AgentCore(config)
        
        # Fetch data
        stock_data, news, social, financials = agent._fetch_all_data('AAPL')
        
        # Verify
        assert stock_data == mock_stock_data
        assert news == []
        assert social == []
        assert financials == mock_financials
    
    @patch('src.agent_core.DataProvider')
    def test_fetch_data_news_failure_non_critical(
        self,
        mock_data_provider,
        config,
        mock_stock_data,
        mock_financials
    ):
        """Test that news fetching failure is non-critical."""
        # Setup mocks
        data_provider_instance = Mock()
        data_provider_instance.get_stock_data.return_value = mock_stock_data
        data_provider_instance.get_news.side_effect = Exception("News API failed")
        data_provider_instance.get_social_media.return_value = []
        data_provider_instance.get_company_financials.return_value = mock_financials
        mock_data_provider.return_value = data_provider_instance
        
        # Create agent
        agent = AgentCore(config)
        
        # Fetch data - should not raise exception
        stock_data, news, social, financials = agent._fetch_all_data('AAPL')
        
        # Verify news is empty but other data is present
        assert stock_data == mock_stock_data
        assert news == []
        assert financials == mock_financials


class TestRiskAssessment:
    """Tests for risk assessment."""
    
    @patch('src.agent_core.DataProvider')
    @patch('src.agent_core.SentimentAnalyzer')
    @patch('src.agent_core.TechnicalAnalyzer')
    @patch('src.agent_core.FundamentalAnalyzer')
    @patch('src.agent_core.RecommendationEngine')
    @patch('src.agent_core.RiskManager')
    def test_analysis_with_portfolio(
        self,
        mock_risk_manager,
        mock_rec_engine,
        mock_fund_analyzer,
        mock_tech_analyzer,
        mock_sent_analyzer,
        mock_data_provider,
        config,
        mock_stock_data,
        mock_financials
    ):
        """Test analysis with portfolio risk assessment."""
        # Setup mocks (similar to successful analysis test)
        data_provider_instance = Mock()
        data_provider_instance.get_stock_data.return_value = mock_stock_data
        data_provider_instance.get_news.return_value = []
        data_provider_instance.get_social_media.return_value = []
        data_provider_instance.get_company_financials.return_value = mock_financials
        mock_data_provider.return_value = data_provider_instance
        
        sentiment_data = SentimentData(
            symbol='AAPL',
            sentiment_score=0.5,
            confidence=0.8,
            sources=[],
            timestamp=datetime.now()
        )
        sent_analyzer_instance = Mock()
        sent_analyzer_instance.analyze.return_value = sentiment_data
        mock_sent_analyzer.return_value = sent_analyzer_instance
        
        technical_indicators = TechnicalIndicators(
            symbol='AAPL',
            ma_20=170.0,
            ma_50=165.0,
            ma_200=160.0,
            rsi=55.0,
            macd=1.5,
            macd_signal=1.0,
            support_levels=[160.0],
            resistance_levels=[180.0],
            technical_score=0.4
        )
        tech_analyzer_instance = Mock()
        tech_analyzer_instance.analyze.return_value = technical_indicators
        mock_tech_analyzer.return_value = tech_analyzer_instance
        
        fundamental_metrics = FundamentalMetrics(
            symbol='AAPL',
            fundamental_score=0.3
        )
        fund_analyzer_instance = Mock()
        fund_analyzer_instance.analyze.return_value = fundamental_metrics
        mock_fund_analyzer.return_value = fund_analyzer_instance
        
        recommendation = Recommendation(
            symbol='AAPL',
            action='BUY',
            confidence=0.75,
            reasoning='Test reasoning',
            sentiment_contribution=0.25,
            technical_contribution=0.12,
            fundamental_contribution=0.06,
            timestamp=datetime.now(),
            entry_price_low=170.0,
            entry_price_high=180.0
        )
        rec_engine_instance = Mock()
        rec_engine_instance.generate_recommendation.return_value = recommendation
        mock_rec_engine.return_value = rec_engine_instance
        
        # Setup risk manager mock
        risk_manager_instance = Mock()
        risk_manager_instance.suggest_position_size.return_value = 7.5
        risk_manager_instance.assess_portfolio_risk.return_value = Mock(
            portfolio_risk_score=0.3,
            concentration_risks=[],
            correlation_risks=[],
            suggested_position_size=7.5,
            risk_mitigation_actions=[]
        )
        mock_risk_manager.return_value = risk_manager_instance
        
        # Create portfolio
        portfolio = [
            Position(symbol='GOOGL', shares=10, avg_cost=2800.0, current_value=28000.0, weight=15.0),
            Position(symbol='MSFT', shares=50, avg_cost=350.0, current_value=17500.0, weight=10.0),
        ]
        
        # Create agent and analyze
        agent = AgentCore(config)
        result = agent.analyze_stock('AAPL', portfolio=portfolio)
        
        # Verify risk assessment is present
        assert result.risk_assessment is not None
        assert result.risk_assessment.suggested_position_size == 7.5


class TestErrorHandling:
    """Tests for error handling."""
    
    @patch('src.agent_core.DataProvider')
    def test_data_provider_exception_handling(self, mock_data_provider, config):
        """Test handling of data provider exceptions."""
        # Setup mock to raise exception
        data_provider_instance = Mock()
        data_provider_instance.get_stock_data.side_effect = Exception("Network error")
        mock_data_provider.return_value = data_provider_instance
        
        # Create agent
        agent = AgentCore(config)
        
        # Verify error is raised and logged
        with pytest.raises(AnalysisError, match="Data fetching failed"):
            agent.analyze_stock('AAPL')
