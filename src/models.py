"""Data models for Stock Market AI Agent."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict


@dataclass
class PricePoint:
    """Represents a single price data point for a stock.
    
    Attributes:
        date: Date of the price point
        open: Opening price
        high: Highest price during the period
        low: Lowest price during the period
        close: Closing price
        volume: Trading volume
    """
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    def __post_init__(self):
        """Validate price data."""
        if self.open < 0 or self.high < 0 or self.low < 0 or self.close < 0:
            raise ValueError("Prices cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        if self.high < self.low:
            raise ValueError("High price cannot be less than low price")
        if not (self.low <= self.open <= self.high):
            raise ValueError("Open price must be between low and high")
        if not (self.low <= self.close <= self.high):
            raise ValueError("Close price must be between low and high")


@dataclass
class StockData:
    """Represents current and historical stock data.
    
    Attributes:
        symbol: Stock ticker symbol
        current_price: Current stock price
        volume: Current trading volume
        timestamp: Timestamp of current data
        historical_prices: List of historical price points (200+ days)
    """
    symbol: str
    current_price: float
    volume: int
    timestamp: datetime
    historical_prices: List[PricePoint] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate stock data."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.current_price < 0:
            raise ValueError("Current price cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")


@dataclass
class SentimentSource:
    """Represents a single sentiment source (news article or social post).
    
    Attributes:
        source_type: Type of source ("news" or "social")
        content: Text content of the source
        score: Sentiment score for this source (-1.0 to +1.0)
        timestamp: When the content was published
        url: Optional URL to the source
    """
    source_type: str
    content: str
    score: float
    timestamp: datetime
    url: Optional[str] = None
    
    def __post_init__(self):
        """Validate sentiment source."""
        if self.source_type not in ["news", "social"]:
            raise ValueError("Source type must be 'news' or 'social'")
        if not -1.0 <= self.score <= 1.0:
            raise ValueError("Sentiment score must be between -1.0 and 1.0")


@dataclass
class SentimentData:
    """Represents aggregated sentiment analysis results.
    
    Attributes:
        symbol: Stock ticker symbol
        sentiment_score: Overall sentiment score (-1.0 to +1.0)
        confidence: Confidence level (0.0 to 1.0)
        sources: List of individual sentiment sources
        timestamp: When the analysis was performed
        direction: Signal direction ("bullish", "bearish", "neutral")
        strength: Signal strength (0.0 to 1.0)
    """
    symbol: str
    sentiment_score: float
    confidence: float
    sources: List[SentimentSource]
    timestamp: datetime
    direction: str = "neutral"
    strength: float = 0.0
    
    def __post_init__(self):
        """Validate sentiment data."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not -1.0 <= self.sentiment_score <= 1.0:
            raise ValueError("Sentiment score must be between -1.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.direction not in ["bullish", "bearish", "neutral"]:
            raise ValueError("Direction must be 'bullish', 'bearish', or 'neutral'")
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Strength must be between 0.0 and 1.0")


@dataclass
class TechnicalIndicators:
    """Represents technical analysis indicators.
    
    Attributes:
        symbol: Stock ticker symbol
        ma_20: 20-day moving average
        ma_50: 50-day moving average
        ma_200: 200-day moving average
        rsi: Relative Strength Index (0-100)
        macd: MACD line value
        macd_signal: MACD signal line value
        support_levels: List of identified support price levels
        resistance_levels: List of identified resistance price levels
        technical_score: Overall technical score (-1.0 to +1.0)
        atr: Average True Range (14-day) for volatility measurement
        direction: Signal direction ("bullish", "bearish", "neutral")
        strength: Signal strength (0.0 to 1.0)
        confidence: Analysis confidence (0.0 to 1.0)
        regime: Technical regime classification
    """
    symbol: str
    ma_20: float
    ma_50: float
    ma_200: float
    rsi: float
    macd: float
    macd_signal: float
    support_levels: List[float]
    resistance_levels: List[float]
    technical_score: float
    atr: float = 0.0
    direction: str = "neutral"
    strength: float = 0.0
    confidence: float = 0.0
    regime: str = "neutral"
    
    def __post_init__(self):
        """Validate technical indicators."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not 0.0 <= self.rsi <= 100.0:
            raise ValueError("RSI must be between 0 and 100")
        if not -1.0 <= self.technical_score <= 1.0:
            raise ValueError("Technical score must be between -1.0 and 1.0")
        if self.direction not in ["bullish", "bearish", "neutral"]:
            raise ValueError("Direction must be 'bullish', 'bearish', or 'neutral'")
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Strength must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        valid_regimes = [
            "bullish-trend", "bearish-trend", "oversold-zone", 
            "overbought-zone", "neutral", "consolidation"
        ]
        if self.regime not in valid_regimes:
            raise ValueError(f"Regime must be one of {valid_regimes}")


@dataclass
class FundamentalMetrics:
    """Represents fundamental analysis metrics.
    
    Attributes:
        symbol: Stock ticker symbol
        pe_ratio: Price-to-Earnings ratio (optional)
        pb_ratio: Price-to-Book ratio (optional)
        debt_to_equity: Debt-to-Equity ratio (optional)
        eps: Earnings Per Share (optional)
        revenue_growth: Revenue growth percentage (optional)
        industry_avg_pe: Industry average P/E ratio (optional)
        fundamental_score: Overall fundamental score (-1.0 to +1.0)
        direction: Signal direction ("bullish", "bearish", "neutral")
        strength: Signal strength (0.0 to 1.0)
        confidence: Analysis confidence (0.0 to 1.0)
    """
    symbol: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    eps: Optional[float] = None
    revenue_growth: Optional[float] = None
    industry_avg_pe: Optional[float] = None
    fundamental_score: float = 0.0
    direction: str = "neutral"
    strength: float = 0.0
    confidence: float = 0.0
    
    def __post_init__(self):
        """Validate fundamental metrics."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not -1.0 <= self.fundamental_score <= 1.0:
            raise ValueError("Fundamental score must be between -1.0 and 1.0")
        if self.direction not in ["bullish", "bearish", "neutral"]:
            raise ValueError("Direction must be 'bullish', 'bearish', or 'neutral'")
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Strength must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class TradeLevels:
    """Represents precise trade entry, exit, and risk management levels.
    
    Attributes:
        ideal_entry: Ideal entry price (tight zone near support/breakout)
        stop_loss: Stop loss price (below recent swing low or ATR-based)
        target: Target price (minimum 2x risk)
        risk_per_trade_percent: Risk per trade as percentage of capital (≤1.5%)
        risk_reward_ratio: Risk to reward ratio (≥1:2)
        position_size_percent: Suggested position size as percentage of capital
    """
    ideal_entry: float
    stop_loss: float
    target: float
    risk_per_trade_percent: float
    risk_reward_ratio: float
    position_size_percent: float
    
    def __post_init__(self):
        """Validate trade levels."""
        if self.ideal_entry <= 0:
            raise ValueError("Ideal entry must be positive")
        if self.stop_loss <= 0:
            raise ValueError("Stop loss must be positive")
        if self.target <= 0:
            raise ValueError("Target must be positive")
        if self.stop_loss >= self.ideal_entry:
            raise ValueError("Stop loss must be below entry for long positions")
        if self.target <= self.ideal_entry:
            raise ValueError("Target must be above entry for long positions")
        if not 0.0 <= self.risk_per_trade_percent <= 1.5:
            raise ValueError("Risk per trade must be between 0 and 1.5%")
        if self.risk_reward_ratio < 2.0:
            raise ValueError("Risk:Reward ratio must be at least 1:2")


@dataclass
class ConfidenceBreakdown:
    """Represents detailed confidence breakdown by analysis component.
    
    Attributes:
        sentiment_confidence: Confidence from sentiment analysis (0.0 to 1.0)
        technical_confidence: Confidence from technical analysis (0.0 to 1.0)
        fundamental_confidence: Confidence from fundamental analysis (0.0 to 1.0)
        market_signal_quality: Quality/clarity of market trend signals (0.0 to 1.0)
        market_favorability: How favorable market is for long trades (0.0 to 1.0)
        agreement_score: Agreement score between components (0.0 to 1.0)
        data_quality_penalty: Penalty for missing data or API failures (0.0 to 1.0)
    """
    sentiment_confidence: float
    technical_confidence: float
    fundamental_confidence: float
    market_signal_quality: float
    market_favorability: float
    agreement_score: float
    data_quality_penalty: float
    
    def __post_init__(self):
        """Validate confidence breakdown."""
        for field_name in ['sentiment_confidence', 'technical_confidence', 
                          'fundamental_confidence', 'market_signal_quality',
                          'market_favorability', 'agreement_score', 
                          'data_quality_penalty']:
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass
class Recommendation:
    """Represents a trading recommendation.
    
    Attributes:
        symbol: Stock ticker symbol
        action: Recommended action ("BUY", "SELL", "HOLD")
        confidence: Confidence score (0.0 to 1.0)
        entry_price_low: Lower bound of entry price range (for BUY)
        entry_price_high: Upper bound of entry price range (for BUY)
        exit_price_low: Lower bound of exit price range (for SELL)
        exit_price_high: Upper bound of exit price range (for SELL)
        reasoning: Explanation for the recommendation
        sentiment_contribution: Contribution from sentiment analysis
        technical_contribution: Contribution from technical analysis
        fundamental_contribution: Contribution from fundamental analysis
        timestamp: When the recommendation was generated
        confidence_breakdown: Detailed confidence breakdown by component
        runtime_weights: Actual weights used at runtime (sentiment, technical, fundamental)
    """
    symbol: str
    action: str
    confidence: float
    reasoning: str
    sentiment_contribution: float
    technical_contribution: float
    fundamental_contribution: float
    timestamp: datetime
    entry_price_low: Optional[float] = None
    entry_price_high: Optional[float] = None
    exit_price_low: Optional[float] = None
    exit_price_high: Optional[float] = None
    trade_levels: Optional['TradeLevels'] = None
    confidence_breakdown: Optional['ConfidenceBreakdown'] = None
    runtime_weights: Optional[dict] = None
    
    def __post_init__(self):
        """Validate recommendation."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.action not in ["BUY", "SELL", "HOLD"]:
            raise ValueError("Action must be 'BUY', 'SELL', or 'HOLD'")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        # Validate price ranges for BUY recommendations
        if self.action == "BUY":
            if self.entry_price_low is None or self.entry_price_high is None:
                raise ValueError("BUY recommendations must have entry price range")
            if self.entry_price_low > self.entry_price_high:
                raise ValueError("Entry price low cannot exceed entry price high")
        
        # Validate price ranges for SELL recommendations
        if self.action == "SELL":
            if self.exit_price_low is None or self.exit_price_high is None:
                raise ValueError("SELL recommendations must have exit price range")
            if self.exit_price_low > self.exit_price_high:
                raise ValueError("Exit price low cannot exceed exit price high")


@dataclass
class Position:
    """Represents a portfolio position.
    
    Attributes:
        symbol: Stock ticker symbol
        shares: Number of shares held
        avg_cost: Average cost per share
        current_value: Current total value of position
        weight: Position weight as percentage of portfolio
    """
    symbol: str
    shares: int
    avg_cost: float
    current_value: float
    weight: float
    
    def __post_init__(self):
        """Validate position."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.shares < 0:
            raise ValueError("Shares cannot be negative")
        if self.avg_cost < 0:
            raise ValueError("Average cost cannot be negative")
        if self.current_value < 0:
            raise ValueError("Current value cannot be negative")
        if not 0.0 <= self.weight <= 100.0:
            raise ValueError("Weight must be between 0.0 and 100.0")


@dataclass
class ConcentrationRisk:
    """Represents a concentration risk in the portfolio.
    
    Attributes:
        symbol: Stock ticker symbol
        weight: Position weight as percentage
        threshold: Concentration threshold that was exceeded
        message: Description of the risk
    """
    symbol: str
    weight: float
    threshold: float
    message: str


@dataclass
class CorrelationRisk:
    """Represents a correlation risk between positions.
    
    Attributes:
        symbol1: First stock ticker symbol
        symbol2: Second stock ticker symbol
        correlation: Correlation coefficient (-1.0 to 1.0)
        message: Description of the risk
    """
    symbol1: str
    symbol2: str
    correlation: float
    message: str
    
    def __post_init__(self):
        """Validate correlation risk."""
        if not -1.0 <= self.correlation <= 1.0:
            raise ValueError("Correlation must be between -1.0 and 1.0")


@dataclass
class RiskAssessment:
    """Represents a portfolio risk assessment.
    
    Attributes:
        portfolio_risk_score: Overall risk score (0.0 to 1.0)
        concentration_risks: List of concentration risks
        correlation_risks: List of correlation risks
        suggested_position_size: Suggested position size as percentage
        risk_mitigation_actions: List of recommended actions
    """
    portfolio_risk_score: float
    concentration_risks: List[ConcentrationRisk]
    correlation_risks: List[CorrelationRisk]
    suggested_position_size: float
    risk_mitigation_actions: List[str]
    
    def __post_init__(self):
        """Validate risk assessment."""
        if not 0.0 <= self.portfolio_risk_score <= 1.0:
            raise ValueError("Portfolio risk score must be between 0.0 and 1.0")
        if not 0.0 <= self.suggested_position_size <= 100.0:
            raise ValueError("Suggested position size must be between 0.0 and 100.0")


@dataclass
class MarketContext:
    """Represents broader market context.
    
    Attributes:
        nifty_trend: Nifty 50 trend ("bullish", "neutral", "bearish")
        banknifty_trend: Bank Nifty trend ("bullish", "neutral", "bearish")
        vix_level: VIX level ("low", "moderate", "high", "very_high")
        market_state: Overall market state ("bullish", "neutral", "bearish", "volatile")
        nifty_price: Current Nifty 50 price
        nifty_20dma: Nifty 50 20-day moving average
        nifty_50dma: Nifty 50 50-day moving average
        banknifty_price: Current Bank Nifty price
        banknifty_20dma: Bank Nifty 20-day moving average
        banknifty_50dma: Bank Nifty 50-day moving average
        vix_value: Current VIX value
        timestamp: When the context was captured
        market_signal_quality: Quality/clarity of market trend signals (0.0 to 1.0)
        market_favorability: How favorable market is for long trades (0.0 to 1.0)
    """
    nifty_trend: str
    banknifty_trend: str
    vix_level: str
    market_state: str
    nifty_price: float
    nifty_20dma: float
    nifty_50dma: float
    banknifty_price: float
    banknifty_20dma: float
    banknifty_50dma: float
    vix_value: float
    timestamp: datetime
    market_signal_quality: float
    market_favorability: float


@dataclass
class NoTradeSignal:
    """Represents a no-trade signal with reasons.
    
    Attributes:
        is_no_trade: Whether trading should be blocked
        reasons: List of reasons why trading is blocked
        suggested_action: What the user should do
        severity: Severity level ("high", "medium", "low")
    """
    is_no_trade: bool
    reasons: List[str]
    suggested_action: str
    severity: str = "medium"


@dataclass
class AnalysisResult:
    """Represents the complete analysis result for a stock.
    
    Attributes:
        symbol: Stock ticker symbol
        current_price: Current stock price
        volume: Current trading volume
        sentiment: Sentiment analysis results
        technical: Technical analysis results
        fundamental: Fundamental analysis results
        recommendation: Trading recommendation
        market_context: Broader market context (optional)
        risk_assessment: Risk assessment (optional)
        stock_data: Stock data with historical prices (optional)
        no_trade_signal: No-trade signal if dangerous conditions detected (optional)
        reversal_watch: Reversal watch signal if potential reversal detected (optional)
        data_quality_report: Data quality report if issues detected (optional)
    """
    symbol: str
    current_price: float
    volume: int
    sentiment: SentimentData
    technical: TechnicalIndicators
    fundamental: FundamentalMetrics
    recommendation: Recommendation
    market_context: Optional[MarketContext] = None
    risk_assessment: Optional[RiskAssessment] = None
    stock_data: Optional['StockData'] = None
    no_trade_signal: Optional['NoTradeSignal'] = None
    reversal_watch: Optional['ReversalWatch'] = None
    data_quality_report: Optional['DataQualityReport'] = None
    
    def __post_init__(self):
        """Validate analysis result."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if self.current_price < 0:
            raise ValueError("Current price cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
