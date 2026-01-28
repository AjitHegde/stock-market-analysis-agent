"""
Market Context Analyzer for Indian Stock Market.

This module analyzes broader market conditions by tracking major indices
(Nifty 50, Bank Nifty) and volatility (India VIX) to provide market context
for stock recommendations.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import logging

from src.data_provider import DataProvider


logger = logging.getLogger(__name__)


@dataclass
class MarketContext:
    """Market context information."""
    nifty_trend: str  # "bullish", "neutral", "bearish"
    banknifty_trend: str  # "bullish", "neutral", "bearish"
    vix_level: str  # "low", "moderate", "high"
    market_state: str  # "bullish", "neutral", "bearish", "volatile"
    nifty_price: float
    nifty_20dma: float
    nifty_50dma: float
    banknifty_price: float
    banknifty_20dma: float
    banknifty_50dma: float
    vix_value: float
    timestamp: datetime
    market_signal_quality: float  # 0.0 to 1.0 - reliability/clarity of market trend
    market_favorability: float  # 0.0 to 1.0 - how favorable for long trades


class MarketContextAnalyzer:
    """
    Analyzes broader market conditions for Indian stock market.
    
    Tracks Nifty 50, Bank Nifty, and India VIX to determine overall
    market sentiment and volatility.
    """
    
    # Index symbols
    NIFTY_50 = "^NSEI"
    BANK_NIFTY = "^NSEBANK"
    INDIA_VIX = "^INDIAVIX"
    
    # VIX thresholds
    VIX_LOW = 15.0
    VIX_MODERATE = 20.0
    VIX_HIGH = 25.0
    
    def __init__(self, data_provider: DataProvider):
        """
        Initialize the market context analyzer.
        
        Args:
            data_provider: Data provider for fetching market data
        """
        self.data_provider = data_provider
        self._cache: Optional[MarketContext] = None
        self._cache_time: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=15)  # Cache for 15 minutes
    
    def get_market_context(self, use_cache: bool = True) -> MarketContext:
        """
        Get current market context.
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            MarketContext with current market state
        """
        # Check cache
        if use_cache and self._cache and self._cache_time:
            if datetime.now() - self._cache_time < self._cache_duration:
                logger.info("Using cached market context")
                return self._cache
        
        logger.info("Fetching fresh market context...")
        
        # Fetch Nifty 50 data
        nifty_data = self._fetch_index_data(self.NIFTY_50)
        nifty_trend = self._determine_trend(
            nifty_data['price'],
            nifty_data['ma_20'],
            nifty_data['ma_50']
        )
        
        # Fetch Bank Nifty data
        banknifty_data = self._fetch_index_data(self.BANK_NIFTY)
        banknifty_trend = self._determine_trend(
            banknifty_data['price'],
            banknifty_data['ma_20'],
            banknifty_data['ma_50']
        )
        
        # Fetch VIX data
        vix_value = self._fetch_vix()
        vix_level = self._determine_vix_level(vix_value)
        
        # Determine overall market state
        market_state = self._determine_market_state(
            nifty_trend,
            banknifty_trend,
            vix_level
        )
        
        # Calculate market signal quality (reliability/clarity of trend)
        market_signal_quality = self._calculate_signal_quality(
            nifty_data['price'],
            nifty_data['ma_20'],
            nifty_data['ma_50'],
            banknifty_data['price'],
            banknifty_data['ma_20'],
            banknifty_data['ma_50'],
            nifty_data.get('volume', 0)
        )
        
        # Calculate market favorability (how good for long trades)
        market_favorability = self._calculate_favorability(
            market_state,
            vix_level,
            nifty_trend,
            banknifty_trend
        )
        
        # Create market context
        context = MarketContext(
            nifty_trend=nifty_trend,
            banknifty_trend=banknifty_trend,
            vix_level=vix_level,
            market_state=market_state,
            nifty_price=nifty_data['price'],
            nifty_20dma=nifty_data['ma_20'],
            nifty_50dma=nifty_data['ma_50'],
            banknifty_price=banknifty_data['price'],
            banknifty_20dma=banknifty_data['ma_20'],
            banknifty_50dma=banknifty_data['ma_50'],
            vix_value=vix_value,
            timestamp=datetime.now(),
            market_signal_quality=market_signal_quality,
            market_favorability=market_favorability
        )
        
        # Update cache
        self._cache = context
        self._cache_time = datetime.now()
        
        logger.info(f"Market context: {market_state} (Nifty: {nifty_trend}, BankNifty: {banknifty_trend}, VIX: {vix_level})")
        
        return context
    
    def _fetch_index_data(self, symbol: str) -> dict:
        """
        Fetch index data and calculate moving averages.
        
        Args:
            symbol: Index symbol
            
        Returns:
            Dictionary with price and moving averages
        """
        try:
            # Get stock data (includes historical prices)
            stock_data = self.data_provider.get_stock_data(symbol)
            
            # Get current price
            current_price = stock_data.current_price
            
            # Calculate moving averages from historical data
            if len(stock_data.historical_prices) >= 50:
                prices = [p.close for p in stock_data.historical_prices[-50:]]
                ma_20 = sum(prices[-20:]) / 20
                ma_50 = sum(prices) / 50
            elif len(stock_data.historical_prices) >= 20:
                prices = [p.close for p in stock_data.historical_prices[-20:]]
                ma_20 = sum(prices) / 20
                ma_50 = ma_20  # Fallback to 20DMA if not enough data
            else:
                # Not enough data, use current price as fallback
                ma_20 = current_price
                ma_50 = current_price
            
            return {
                'price': current_price,
                'ma_20': ma_20,
                'ma_50': ma_50
            }
            
        except Exception as e:
            logger.warning(f"Error fetching {symbol} data: {e}")
            # Return neutral values on error
            return {
                'price': 0.0,
                'ma_20': 0.0,
                'ma_50': 0.0
            }
    
    def _fetch_vix(self) -> float:
        """
        Fetch India VIX value.
        
        Returns:
            Current VIX value
        """
        try:
            stock_data = self.data_provider.get_stock_data(self.INDIA_VIX)
            return stock_data.current_price
        except Exception as e:
            logger.warning(f"Error fetching VIX data: {e}")
            # Return moderate VIX on error
            return 18.0
    
    def _determine_trend(self, price: float, ma_20: float, ma_50: float) -> str:
        """
        Determine trend based on price vs moving averages.
        
        Args:
            price: Current price
            ma_20: 20-day moving average
            ma_50: 50-day moving average
            
        Returns:
            Trend: "bullish", "neutral", or "bearish"
        """
        if price == 0 or ma_20 == 0 or ma_50 == 0:
            return "neutral"
        
        # Bullish: Price above both MAs
        if price > ma_20 and price > ma_50:
            return "bullish"
        
        # Bearish: Price below both MAs
        elif price < ma_20 and price < ma_50:
            return "bearish"
        
        # Neutral: Mixed signals
        else:
            return "neutral"
    
    def _determine_vix_level(self, vix: float) -> str:
        """
        Determine VIX level.
        
        Args:
            vix: VIX value
            
        Returns:
            VIX level: "low", "moderate", or "high"
        """
        if vix < self.VIX_LOW:
            return "low"
        elif vix < self.VIX_MODERATE:
            return "moderate"
        elif vix < self.VIX_HIGH:
            return "high"
        else:
            return "very_high"
    
    def _determine_market_state(
        self,
        nifty_trend: str,
        banknifty_trend: str,
        vix_level: str
    ) -> str:
        """
        Determine overall market state.
        
        Args:
            nifty_trend: Nifty 50 trend
            banknifty_trend: Bank Nifty trend
            vix_level: VIX level
            
        Returns:
            Market state: "bullish", "neutral", "bearish", or "volatile"
        """
        # High volatility overrides other signals
        if vix_level in ["high", "very_high"]:
            return "volatile"
        
        # Both indices bullish
        if nifty_trend == "bullish" and banknifty_trend == "bullish":
            return "bullish"
        
        # Both indices bearish
        elif nifty_trend == "bearish" and banknifty_trend == "bearish":
            return "bearish"
        
        # Mixed signals or neutral
        else:
            return "neutral"
    
    def _calculate_signal_quality(
        self,
        nifty_price: float,
        nifty_20dma: float,
        nifty_50dma: float,
        banknifty_price: float,
        banknifty_20dma: float,
        banknifty_50dma: float,
        volume: float
    ) -> float:
        """
        Calculate market signal quality (0.0 to 1.0).
        
        Measures reliability/clarity of market trend based on:
        - Distance from moving averages (clear trend vs choppy)
        - Volume confirmation (high volume = more reliable)
        - Trend consistency (both indices aligned)
        
        Args:
            nifty_price: Current Nifty price
            nifty_20dma: Nifty 20-day MA
            nifty_50dma: Nifty 50-day MA
            banknifty_price: Current Bank Nifty price
            banknifty_20dma: Bank Nifty 20-day MA
            banknifty_50dma: Bank Nifty 50-day MA
            volume: Trading volume
            
        Returns:
            Signal quality score (0.0 to 1.0)
        """
        quality_score = 0.0
        
        # 1. Distance from moving averages (40% weight)
        # Clear trend = price far from MAs, choppy = price near MAs
        if nifty_20dma > 0 and nifty_50dma > 0:
            nifty_distance_20 = abs(nifty_price - nifty_20dma) / nifty_20dma
            nifty_distance_50 = abs(nifty_price - nifty_50dma) / nifty_50dma
            
            # Average distance (normalized to 0-1, assuming 5% is strong signal)
            avg_distance = (nifty_distance_20 + nifty_distance_50) / 2
            distance_score = min(1.0, avg_distance / 0.05)
            quality_score += distance_score * 0.4
        else:
            quality_score += 0.5 * 0.4  # Neutral if no data
        
        # 2. Volume confirmation (20% weight)
        # Higher volume = more reliable signal
        # This is a placeholder - in real implementation, compare to average volume
        # For now, assume moderate volume
        volume_score = 0.7
        quality_score += volume_score * 0.2
        
        # 3. Trend consistency between indices (40% weight)
        # Both indices showing same trend = high quality
        nifty_trend = self._determine_trend(nifty_price, nifty_20dma, nifty_50dma)
        banknifty_trend = self._determine_trend(banknifty_price, banknifty_20dma, banknifty_50dma)
        
        if nifty_trend == banknifty_trend:
            if nifty_trend in ["bullish", "bearish"]:
                consistency_score = 1.0  # Strong agreement on direction
            else:
                consistency_score = 0.6  # Both neutral
        else:
            consistency_score = 0.3  # Conflicting signals
        
        quality_score += consistency_score * 0.4
        
        return min(1.0, max(0.0, quality_score))
    
    def _calculate_favorability(
        self,
        market_state: str,
        vix_level: str,
        nifty_trend: str,
        banknifty_trend: str
    ) -> float:
        """
        Calculate market favorability for long trades (0.0 to 1.0).
        
        Measures how good the environment is for long trades based on:
        - Bullish/Bearish state
        - Volatility level
        - Breadth indicators (both indices)
        
        Rules:
        - Bearish market → Favorability ≤ 40%
        - Panic (very high VIX) → Favorability ≤ 25%
        - Bullish → Favorability ≥ 70%
        
        Args:
            market_state: Overall market state
            vix_level: VIX level
            nifty_trend: Nifty 50 trend
            banknifty_trend: Bank Nifty trend
            
        Returns:
            Favorability score (0.0 to 1.0)
        """
        favorability = 0.5  # Start neutral
        
        # 1. Base favorability from market state (60% weight)
        if market_state == "bullish":
            base_score = 0.85  # Very favorable
        elif market_state == "neutral":
            base_score = 0.55  # Slightly favorable
        elif market_state == "bearish":
            base_score = 0.30  # Unfavorable (≤40%)
        else:  # volatile
            base_score = 0.35  # Unfavorable
        
        favorability = base_score * 0.6
        
        # 2. Volatility adjustment (25% weight)
        if vix_level == "low":
            vix_score = 0.9  # Very favorable
        elif vix_level == "moderate":
            vix_score = 0.7  # Moderately favorable
        elif vix_level == "high":
            vix_score = 0.4  # Unfavorable
        else:  # very_high (panic)
            vix_score = 0.2  # Very unfavorable (≤25%)
        
        favorability += vix_score * 0.25
        
        # 3. Breadth indicators (15% weight)
        # Both indices bullish = strong breadth
        if nifty_trend == "bullish" and banknifty_trend == "bullish":
            breadth_score = 1.0
        elif nifty_trend == "bearish" and banknifty_trend == "bearish":
            breadth_score = 0.2
        else:
            breadth_score = 0.5  # Mixed
        
        favorability += breadth_score * 0.15
        
        # Ensure constraints are met
        if market_state == "bearish":
            favorability = min(favorability, 0.40)
        if vix_level == "very_high":
            favorability = min(favorability, 0.25)
        if market_state == "bullish":
            favorability = max(favorability, 0.70)
        
        return min(1.0, max(0.0, favorability))
