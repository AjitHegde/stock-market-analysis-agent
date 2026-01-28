"""Agent Core orchestration for Stock Market AI Agent.

This module provides the main orchestration layer that coordinates the entire
analysis workflow, managing data acquisition, parallel analysis execution,
recommendation generation, and error handling.
"""

import logging
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from src.config import Configuration
from src.data_provider import DataProvider
from src.sentiment_analyzer import SentimentAnalyzer
from src.technical_analyzer import TechnicalAnalyzer
from src.fundamental_analyzer import FundamentalAnalyzer
from src.recommendation_engine import RecommendationEngine
from src.risk_manager import RiskManager
from src.market_context_analyzer import MarketContextAnalyzer
from src.no_trade_detector import NoTradeDetector
from src.reversal_watch_detector import ReversalWatchDetector
from src.performance_tracker import PerformanceTracker
from src.data_quality_monitor import DataQualityMonitor
from src.models import (
    AnalysisResult,
    SentimentData,
    TechnicalIndicators,
    FundamentalMetrics,
    Recommendation,
    RiskAssessment,
    Position,
    MarketContext,
    TradeLevels
)


logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Exception raised when analysis fails."""
    pass


def analyze_discovered_stocks(
    discovered_stocks: List,
    agent_core: 'AgentCore',
    portfolio: Optional[List[Position]] = None
) -> List[AnalysisResult]:
    """Analyze a list of discovered stocks using the existing analysis pipeline.
    
    This function accepts a list of DiscoveredStock objects from news discovery
    and analyzes each symbol using the existing analyze_stock method. Individual
    stock analysis failures are isolated and don't prevent other stocks from
    being analyzed.
    
    Args:
        discovered_stocks: List of DiscoveredStock objects from news discovery
        agent_core: AgentCore instance to use for analysis
        portfolio: Optional list of portfolio positions for risk assessment
        
    Returns:
        List of AnalysisResult objects for successfully analyzed stocks
        
    Validates: Requirements 4.1, 9.3
    """
    logger.info(f"Analyzing {len(discovered_stocks)} discovered stocks")
    
    results = []
    failed_count = 0
    
    for stock in discovered_stocks:
        try:
            logger.info(f"Analyzing {stock.symbol} (mentions: {stock.mention_count})")
            
            # Call existing analyze_stock method
            result = agent_core.analyze_stock(stock.symbol, portfolio)
            results.append(result)
            
            logger.info(f"Successfully analyzed {stock.symbol}: {result.recommendation.action}")
            
        except Exception as e:
            # Log error but continue with remaining stocks (graceful error handling)
            failed_count += 1
            logger.error(f"Failed to analyze {stock.symbol}: {str(e)}")
            continue
    
    logger.info(
        f"Analysis complete: {len(results)} successful, {failed_count} failed"
    )
    
    return results


def filter_actionable_recommendations(
    analysis_results: List[AnalysisResult],
    discovered_stocks: Optional[List] = None
) -> List[AnalysisResult]:
    """Filter analysis results to include only actionable recommendations.
    
    Filters results to include only BUY or SELL recommendations, excluding HOLD
    recommendations. Sorts results by confidence score descending, then by
    mention count descending (if discovered_stocks provided).
    
    Args:
        analysis_results: List of AnalysisResult objects from analysis
        discovered_stocks: Optional list of DiscoveredStock objects for mention count sorting
        
    Returns:
        List of AnalysisResult objects with only BUY/SELL recommendations,
        sorted by confidence and mention count
        
    Validates: Requirements 5.1, 5.2, 5.3, 5.5
    """
    logger.info(f"Filtering {len(analysis_results)} analysis results for actionable recommendations")
    
    # Step 1: Filter to include only BUY or SELL recommendations
    actionable_results = [
        result for result in analysis_results
        if result.recommendation.action in ['BUY', 'SELL']
    ]
    
    hold_count = len(analysis_results) - len(actionable_results)
    logger.info(f"Filtered to {len(actionable_results)} actionable recommendations (excluded {hold_count} HOLD)")
    
    # Step 2: Create mention count lookup if discovered_stocks provided
    mention_counts = {}
    if discovered_stocks:
        mention_counts = {
            stock.symbol: stock.mention_count
            for stock in discovered_stocks
        }
    
    # Step 3: Sort by confidence score descending, then by mention count descending
    def sort_key(result: AnalysisResult):
        confidence = result.recommendation.confidence
        mention_count = mention_counts.get(result.symbol, 0)
        # Return tuple for multi-criteria sorting (higher values first)
        return (-confidence, -mention_count)
    
    actionable_results.sort(key=sort_key)
    
    logger.info(f"Sorted {len(actionable_results)} results by confidence and mention count")
    
    return actionable_results


class AgentCore:
    """Main orchestration layer for the Stock Market AI Agent.
    
    The Agent Core coordinates the entire analysis workflow:
    1. Fetches data from external APIs
    2. Runs analyzers in parallel
    3. Generates recommendations
    4. Assesses risk (if portfolio provided)
    5. Handles errors gracefully
    """
    
    def __init__(self, config: Configuration):
        """Initialize the Agent Core with all components.
        
        Args:
            config: Configuration object with settings and API keys
        """
        self.config = config
        
        # Initialize all components
        logger.info("Initializing Agent Core components...")
        
        self.data_provider = DataProvider(config)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.recommendation_engine = RecommendationEngine(config)
        self.risk_manager = RiskManager(config.risk_tolerance)
        self.market_context_analyzer = MarketContextAnalyzer(self.data_provider)
        self.no_trade_detector = NoTradeDetector(
            vix_spike_threshold=25.0,
            nifty_drop_threshold=0.03,
            enable_no_trade=True
        )
        self.reversal_watch_detector = ReversalWatchDetector()
        self.data_quality_monitor = DataQualityMonitor()
        
        # Initialize performance tracker if enabled
        self.performance_tracker = None
        if config.performance_tracking_enabled:
            self.performance_tracker = PerformanceTracker(
                storage_path=config.performance_storage_path
            )
            logger.info("Performance tracking enabled")
            
            # Auto-adjust weights if enabled and sufficient data exists
            if config.auto_adjust_weights:
                self._auto_adjust_weights()
        
        logger.info("Agent Core initialized successfully")
    
    def analyze_stock(
        self,
        symbol: str,
        portfolio: Optional[List[Position]] = None
    ) -> AnalysisResult:
        """Main entry point for stock analysis.
        
        Orchestrates the complete analysis workflow:
        1. Data Acquisition: Fetch stock data, news, social media, financials
        2. Parallel Analysis: Run sentiment, technical, fundamental analyzers
        3. Recommendation: Generate trading recommendation
        4. Risk Assessment: Evaluate portfolio risk (if portfolio provided)
        
        Args:
            symbol: Stock ticker symbol to analyze
            portfolio: Optional list of portfolio positions for risk assessment
            
        Returns:
            AnalysisResult with complete analysis
            
        Raises:
            AnalysisError: If critical analysis steps fail
            
        Validates: Requirements 9.4, 9.5, 9.6
        """
        logger.info(f"Starting analysis for {symbol}")
        
        # Reset data quality monitor for new analysis
        self.data_quality_monitor.reset()
        
        try:
            # Phase 1: Data Acquisition
            logger.info(f"Phase 1: Fetching data for {symbol}")
            stock_data, news, social, financials = self._fetch_all_data(symbol)
            
            # Monitor data quality after fetching
            self._monitor_data_quality(stock_data, news, social, financials)
            
            # Phase 2: Parallel Analysis
            logger.info(f"Phase 2: Running analyzers for {symbol}")
            sentiment, technical, fundamental = self._run_analyzers(
                symbol, stock_data, news, social, financials
            )
            
            # Phase 2.5: Get Market Context
            logger.info(f"Phase 2.5: Fetching market context")
            market_context = self.market_context_analyzer.get_market_context()
            
            # Phase 2.6: Check No-Trade Conditions
            logger.info(f"Phase 2.6: Checking no-trade conditions")
            no_trade_signal = self.no_trade_detector.check_market_conditions(market_context)
            
            if no_trade_signal.is_no_trade:
                logger.warning(
                    f"No-trade signal active: severity={no_trade_signal.severity}, "
                    f"reasons={len(no_trade_signal.reasons)}"
                )
            
            # Generate data quality report
            data_quality_report = self.data_quality_monitor.generate_report()
            
            # Apply confidence penalties from data quality issues
            if data_quality_report.total_confidence_penalty > 0:
                sentiment.confidence = self.data_quality_monitor.apply_confidence_penalty(
                    sentiment.confidence, data_quality_report
                )
                technical.confidence = self.data_quality_monitor.apply_confidence_penalty(
                    technical.confidence, data_quality_report
                )
                fundamental.confidence = self.data_quality_monitor.apply_confidence_penalty(
                    fundamental.confidence, data_quality_report
                )
            
            # Phase 3: Generate Recommendation
            logger.info(f"Phase 3: Generating recommendation for {symbol}")
            recommendation = self.recommendation_engine.generate_recommendation(
                sentiment=sentiment,
                technical=technical,
                fundamental=fundamental,
                current_price=stock_data.current_price,
                market_context=market_context
            )
            
            # Apply confidence penalty to recommendation
            if data_quality_report.total_confidence_penalty > 0:
                recommendation.confidence = self.data_quality_monitor.apply_confidence_penalty(
                    recommendation.confidence, data_quality_report
                )
            
            # Override BUY recommendations if no-trade signal is active
            if no_trade_signal.is_no_trade and recommendation.action == "BUY":
                logger.info(f"Overriding BUY recommendation to HOLD due to no-trade signal")
                # Keep the original recommendation but change action to HOLD
                # This preserves the analysis while blocking the trade
                original_action = recommendation.action
                recommendation.action = "HOLD"
                recommendation.reasoning = (
                    f"🚫 TRADING BLOCKED - Original recommendation: {original_action}\n\n"
                    f"Dangerous market conditions detected:\n" +
                    "\n".join(f"• {reason}" for reason in no_trade_signal.reasons) +
                    f"\n\n{no_trade_signal.suggested_action}\n\n"
                    f"--- Original Analysis ---\n\n{recommendation.reasoning}"
                )
            
            # Phase 4: Risk Assessment (optional)
            risk_assessment = None
            if portfolio:
                logger.info(f"Phase 4: Assessing portfolio risk for {symbol}")
                risk_assessment = self._assess_risk(
                    symbol, stock_data, recommendation, portfolio, market_context
                )
            
            # Detect reversal watch setup
            reversal_watch = None
            if technical.regime == "oversold-zone":
                reversal_watch = self.reversal_watch_detector.detect(
                    symbol=symbol,
                    technical=technical,
                    fundamental=fundamental,
                    market_context=market_context,
                    prices=stock_data.historical_prices
                )
                if reversal_watch.is_reversal_setup:
                    logger.info(
                        f"Reversal watch detected for {symbol}: "
                        f"status={reversal_watch.status}, confidence={reversal_watch.confidence:.0%}"
                    )
            
            # Create final result
            result = AnalysisResult(
                symbol=symbol,
                current_price=stock_data.current_price,
                volume=stock_data.volume,
                sentiment=sentiment,
                technical=technical,
                fundamental=fundamental,
                recommendation=recommendation,
                market_context=market_context,
                risk_assessment=risk_assessment,
                stock_data=stock_data,
                no_trade_signal=no_trade_signal if no_trade_signal.is_no_trade else None,
                reversal_watch=reversal_watch if reversal_watch and reversal_watch.is_reversal_setup else None,
                data_quality_report=data_quality_report if data_quality_report.issues else None
            )
            
            logger.info(f"Analysis complete for {symbol}: {recommendation.action}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {str(e)}", exc_info=True)
            raise AnalysisError(f"Failed to analyze {symbol}: {str(e)}") from e
    
    def _monitor_data_quality(self, stock_data, news, social, financials):
        """Monitor data quality and record issues.
        
        Args:
            stock_data: Stock data object
            news: List of news articles
            social: List of social media posts
            financials: Company financials object
        """
        # Check news availability
        total_sources = len(news) + len(social)
        self.data_quality_monitor.check_news_availability(
            news_sources=news + social,
            expected_minimum=5
        )
        
        # Check price freshness
        self.data_quality_monitor.check_price_freshness(
            price_timestamp=stock_data.timestamp,
            max_age_hours=24
        )
        
        # Check technical indicator completeness
        if stock_data.historical_prices:
            required_indicators = ['rsi', 'macd', 'ma_20', 'ma_50', 'ma_200']
            available_indicators = {
                'rsi': len(stock_data.historical_prices) >= 14,
                'macd': len(stock_data.historical_prices) >= 26,
                'ma_20': len(stock_data.historical_prices) >= 20,
                'ma_50': len(stock_data.historical_prices) >= 50,
                'ma_200': len(stock_data.historical_prices) >= 200,
            }
            self.data_quality_monitor.check_indicator_completeness(
                technical_indicators=available_indicators,
                required_indicators=required_indicators
            )
        
        # Check fundamental completeness
        required_fundamentals = ['pe_ratio', 'pb_ratio', 'revenue_growth']
        available_fundamentals = {
            'pe_ratio': financials.pe_ratio,
            'pb_ratio': financials.pb_ratio,
            'revenue_growth': financials.revenue_growth,
        }
        self.data_quality_monitor.check_fundamental_completeness(
            fundamental_metrics=available_fundamentals,
            required_metrics=required_fundamentals
        )
    
    def _fetch_all_data(self, symbol: str):
        """Fetch all required data for analysis.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Tuple of (stock_data, news, social, financials)
            
        Raises:
            AnalysisError: If critical data fetching fails
        """
        try:
            # Fetch stock data (critical)
            stock_data = self.data_provider.get_stock_data(symbol)
            logger.info(f"Fetched stock data for {symbol}: ${stock_data.current_price:.2f}")
            
            # Fetch news (non-critical)
            try:
                news = self.data_provider.get_news(symbol)
                logger.info(f"Fetched {len(news)} news articles for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to fetch news for {symbol}: {str(e)}")
                self.data_quality_monitor.check_api_failures("News API", str(e))
                news = []
            
            # Fetch social media (non-critical)
            try:
                social = self.data_provider.get_social_media(symbol)
                logger.info(f"Fetched {len(social)} social posts for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to fetch social media for {symbol}: {str(e)}")
                self.data_quality_monitor.check_api_failures("Social Media API", str(e))
                social = []
            
            # Fetch financials (critical)
            try:
                financials = self.data_provider.get_company_financials(symbol)
                logger.info(f"Fetched financials for {symbol}")
            except Exception as e:
                logger.error(f"Failed to fetch financials for {symbol}: {str(e)}")
                self.data_quality_monitor.check_api_failures("Yahoo Finance API", str(e))
                raise AnalysisError(f"Failed to fetch financials: {str(e)}") from e
            
            return stock_data, news, social, financials
            
        except ValueError as e:
            # Invalid symbol or insufficient data
            logger.error(f"Invalid symbol or insufficient data for {symbol}: {str(e)}")
            raise AnalysisError(f"Invalid symbol or insufficient data: {str(e)}") from e
        except AnalysisError:
            # Re-raise AnalysisError as-is
            raise
        except Exception as e:
            # Other critical errors
            logger.error(f"Failed to fetch data for {symbol}: {str(e)}")
            self.data_quality_monitor.check_api_failures("Data Provider", str(e))
            raise AnalysisError(f"Data fetching failed: {str(e)}") from e
    
    def _run_analyzers(
        self,
        symbol: str,
        stock_data,
        news,
        social,
        financials
    ):
        """Run all analyzers in parallel.
        
        Args:
            symbol: Stock ticker symbol
            stock_data: Stock price data
            news: News articles
            social: Social media posts
            financials: Company financials
            
        Returns:
            Tuple of (sentiment, technical, fundamental)
            
        Validates: Requirements 9.4 (graceful degradation)
        """
        sentiment = None
        technical = None
        fundamental = None
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all analysis tasks
            futures = {}
            
            # Sentiment analysis (non-critical)
            futures['sentiment'] = executor.submit(
                self._run_sentiment_analysis,
                symbol, news, social
            )
            
            # Technical analysis (critical)
            futures['technical'] = executor.submit(
                self._run_technical_analysis,
                symbol, stock_data.historical_prices
            )
            
            # Fundamental analysis (critical)
            futures['fundamental'] = executor.submit(
                self._run_fundamental_analysis,
                financials, stock_data.current_price
            )
            
            # Collect results as they complete
            for future_name, future in futures.items():
                try:
                    result = future.result()
                    
                    if future_name == 'sentiment':
                        sentiment = result
                    elif future_name == 'technical':
                        technical = result
                    elif future_name == 'fundamental':
                        fundamental = result
                        
                except Exception as e:
                    logger.error(
                        f"{future_name.capitalize()} analysis failed for {symbol}: {str(e)}",
                        exc_info=True
                    )
                    
                    # Handle graceful degradation
                    if future_name == 'sentiment':
                        # Sentiment is non-critical, create neutral sentiment
                        logger.warning(f"Using neutral sentiment for {symbol} due to analysis failure")
                        sentiment = self._create_neutral_sentiment(symbol)
                    elif future_name == 'technical':
                        # Technical is critical, re-raise
                        raise AnalysisError(f"Technical analysis failed: {str(e)}") from e
                    elif future_name == 'fundamental':
                        # Fundamental is critical, re-raise
                        raise AnalysisError(f"Fundamental analysis failed: {str(e)}") from e
        
        return sentiment, technical, fundamental
    
    def _run_sentiment_analysis(self, symbol: str, news, social):
        """Run sentiment analysis.
        
        Args:
            symbol: Stock ticker symbol
            news: News articles
            social: Social media posts
            
        Returns:
            SentimentData
        """
        logger.debug(f"Running sentiment analysis for {symbol}")
        return self.sentiment_analyzer.analyze(news, social, symbol)
    
    def _run_technical_analysis(self, symbol: str, historical_prices):
        """Run technical analysis.
        
        Args:
            symbol: Stock ticker symbol
            historical_prices: List of PricePoint objects
            
        Returns:
            TechnicalIndicators
        """
        logger.debug(f"Running technical analysis for {symbol}")
        return self.technical_analyzer.analyze(symbol, historical_prices)
    
    def _run_fundamental_analysis(self, financials, current_price):
        """Run fundamental analysis.
        
        Args:
            financials: CompanyFinancials object
            current_price: Current stock price
            
        Returns:
            FundamentalMetrics
        """
        logger.debug(f"Running fundamental analysis for {financials.symbol}")
        return self.fundamental_analyzer.analyze(financials, current_price)
    
    def _create_neutral_sentiment(self, symbol: str) -> SentimentData:
        """Create neutral sentiment data for graceful degradation.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            SentimentData with neutral values
        """
        return SentimentData(
            symbol=symbol,
            sentiment_score=0.0,
            confidence=0.0,
            sources=[],
            timestamp=datetime.now(),
            direction="neutral",
            strength=0.0
        )
    
    def _assess_risk(
        self,
        symbol: str,
        stock_data,
        recommendation: Recommendation,
        portfolio: List[Position],
        market_context: Optional[MarketContext] = None
    ) -> RiskAssessment:
        """Assess portfolio risk for new position.
        
        Args:
            symbol: Stock ticker symbol
            stock_data: Stock price data
            recommendation: Trading recommendation
            portfolio: Current portfolio positions
            
        Returns:
            RiskAssessment
        """
        try:
            # Calculate stock volatility from historical prices
            import numpy as np
            prices = [p.close for p in stock_data.historical_prices[-30:]]  # Last 30 days
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns)
            
            # Calculate total portfolio value
            portfolio_value = sum(p.current_value for p in portfolio)
            
            # Get position size suggestion
            suggested_size = self.risk_manager.suggest_position_size(
                symbol=symbol,
                portfolio_value=portfolio_value,
                stock_volatility=volatility
            )
            
            # Assess overall portfolio risk
            assessment = self.risk_manager.assess_portfolio_risk(portfolio)
            
            # Update suggested position size
            assessment.suggested_position_size = suggested_size
            
            return assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed for {symbol}: {str(e)}", exc_info=True)
            # Return minimal risk assessment
            return RiskAssessment(
                portfolio_risk_score=0.0,
                concentration_risks=[],
                correlation_risks=[],
                suggested_position_size=5.0,  # Default 5%
                risk_mitigation_actions=[]
            )
    
    def _auto_adjust_weights(self):
        """Automatically adjust recommendation weights based on performance."""
        if not self.performance_tracker:
            return
        
        # Get closed trades
        closed_trades = self.performance_tracker.get_closed_trades()
        
        # Check if we have enough trades
        if len(closed_trades) < self.config.min_trades_for_adjustment:
            logger.info(
                f"Not enough trades for weight adjustment: "
                f"{len(closed_trades)}/{self.config.min_trades_for_adjustment}"
            )
            return
        
        # Get latest recommended weights
        recommended_weights = self.performance_tracker.get_latest_recommended_weights()
        
        if not recommended_weights:
            logger.info("No recommended weights available yet")
            return
        
        # Apply recommended weights
        logger.info(f"Applying recommended weights: {recommended_weights}")
        self.config.apply_recommended_weights(recommended_weights)
        
        # Update recommendation engine with new weights
        self.recommendation_engine = RecommendationEngine(self.config)
        
        logger.info(
            f"Weights adjusted: sentiment={self.config.sentiment_weight:.2f}, "
            f"technical={self.config.technical_weight:.2f}, "
            f"fundamental={self.config.fundamental_weight:.2f}"
        )
