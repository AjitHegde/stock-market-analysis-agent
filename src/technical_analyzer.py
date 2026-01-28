"""Technical analysis component for Stock Market AI Agent.

This module implements technical analysis indicators including moving averages,
RSI, MACD, support/resistance levels, and generates an overall technical score.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from scipy.signal import argrelextrema
from src.models import PricePoint, TechnicalIndicators


class TechnicalAnalyzer:
    """Analyzes stock price data using technical indicators.
    
    This class calculates various technical indicators from historical price data
    and combines them into an overall technical score to assess bullish or bearish
    market conditions.
    """
    
    def calculate_moving_averages(self, prices: List[PricePoint]) -> Dict[str, float]:
        """Calculate 20, 50, and 200-day simple moving averages.
        
        Args:
            prices: List of historical price points (should have at least 200 points)
            
        Returns:
            Dictionary with keys 'ma_20', 'ma_50', 'ma_200' containing the moving averages
            
        Raises:
            ValueError: If insufficient data points are provided
        """
        if len(prices) < 20:
            raise ValueError("Need at least 20 price points to calculate moving averages")
        
        # Convert to pandas DataFrame for easier calculation
        df = pd.DataFrame([
            {'date': p.date, 'close': p.close}
            for p in prices
        ])
        df = df.sort_values('date')
        
        # Calculate moving averages
        result = {}
        
        # 20-day MA
        result['ma_20'] = df['close'].rolling(window=20).mean().iloc[-1]
        
        # 50-day MA (if enough data)
        if len(prices) >= 50:
            result['ma_50'] = df['close'].rolling(window=50).mean().iloc[-1]
        else:
            result['ma_50'] = result['ma_20']  # Fallback to 20-day if insufficient data
        
        # 200-day MA (if enough data)
        if len(prices) >= 200:
            result['ma_200'] = df['close'].rolling(window=200).mean().iloc[-1]
        else:
            result['ma_200'] = result['ma_50']  # Fallback to 50-day if insufficient data
        
        return result
    
    def calculate_rsi(self, prices: List[PricePoint], period: int = 14) -> float:
        """Calculate Relative Strength Index (RSI).
        
        RSI is a momentum oscillator that measures the speed and magnitude of price changes.
        Values range from 0 to 100, with readings above 70 indicating overbought conditions
        and readings below 30 indicating oversold conditions.
        
        Args:
            prices: List of historical price points (should have at least period+1 points)
            period: RSI period (default: 14)
            
        Returns:
            RSI value between 0 and 100
            
        Raises:
            ValueError: If insufficient data points are provided
        """
        if len(prices) < period + 1:
            raise ValueError(f"Need at least {period + 1} price points to calculate RSI")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame([
            {'date': p.date, 'close': p.close}
            for p in prices
        ])
        df = df.sort_values('date')
        
        # Calculate price changes
        delta = df['close'].diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)
        
        # Calculate average gains and losses using exponential moving average
        avg_gains = gains.rolling(window=period, min_periods=period).mean()
        avg_losses = losses.rolling(window=period, min_periods=period).mean()
        
        # Calculate RS (Relative Strength)
        rs = avg_gains / avg_losses
        
        # Calculate RSI
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        # Return the most recent RSI value
        return rsi.iloc[-1]
    
    def calculate_macd(self, prices: List[PricePoint]) -> Tuple[float, float]:
        """Calculate MACD (Moving Average Convergence Divergence) and signal line.
        
        MACD is a trend-following momentum indicator that shows the relationship between
        two moving averages of a stock's price. The MACD line is the 12-day EMA minus
        the 26-day EMA. The signal line is the 9-day EMA of the MACD line.
        
        Args:
            prices: List of historical price points (should have at least 35 points)
            
        Returns:
            Tuple of (macd_line, signal_line)
            
        Raises:
            ValueError: If insufficient data points are provided
        """
        if len(prices) < 35:  # Need 26 for MACD + 9 for signal
            raise ValueError("Need at least 35 price points to calculate MACD")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame([
            {'date': p.date, 'close': p.close}
            for p in prices
        ])
        df = df.sort_values('date')
        
        # Calculate EMAs
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_12 - ema_26
        
        # Calculate signal line (9-day EMA of MACD)
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        
        # Return the most recent values
        return macd_line.iloc[-1], signal_line.iloc[-1]
    
    def calculate_atr(self, prices: List[PricePoint], period: int = 14) -> float:
        """Calculate Average True Range (ATR) for volatility measurement.
        
        ATR measures market volatility by decomposing the entire range of an asset
        price for that period. It's used for setting stop losses and position sizing.
        
        Args:
            prices: List of historical price points (should have at least period+1 points)
            period: ATR period (default: 14)
            
        Returns:
            ATR value
            
        Raises:
            ValueError: If insufficient data points are provided
        """
        if len(prices) < period + 1:
            return 0.0  # Return 0 if insufficient data
        
        # Convert to pandas DataFrame
        df = pd.DataFrame([
            {'date': p.date, 'high': p.high, 'low': p.low, 'close': p.close}
            for p in prices
        ])
        df = df.sort_values('date')
        
        # Calculate True Range
        # TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
        df['prev_close'] = df['close'].shift(1)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate ATR as moving average of True Range
        atr = df['true_range'].rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else 0.0
    
    def find_support_resistance(self, prices: List[PricePoint]) -> Tuple[List[float], List[float]]:
        """Identify support and resistance levels using local minima and maxima.
        
        Support levels are price points where buying pressure is strong enough to prevent
        further decline. Resistance levels are price points where selling pressure prevents
        further increase. This method identifies these levels by finding local extrema in
        the price data.
        
        Args:
            prices: List of historical price points (should have at least 20 points)
            
        Returns:
            Tuple of (support_levels, resistance_levels) as lists of price values
            
        Raises:
            ValueError: If insufficient data points are provided
        """
        if len(prices) < 20:
            raise ValueError("Need at least 20 price points to find support/resistance")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame([
            {'date': p.date, 'low': p.low, 'high': p.high, 'close': p.close}
            for p in prices
        ])
        df = df.sort_values('date')
        
        # Find local minima (support levels) using low prices
        # Order parameter determines how many points on each side to compare
        order = max(5, len(prices) // 20)  # Adaptive order based on data length
        local_min_indices = argrelextrema(df['low'].values, np.less_equal, order=order)[0]
        
        # Find local maxima (resistance levels) using high prices
        local_max_indices = argrelextrema(df['high'].values, np.greater_equal, order=order)[0]
        
        # Extract support levels from local minima
        support_levels = df.iloc[local_min_indices]['low'].tolist()
        
        # Extract resistance levels from local maxima
        resistance_levels = df.iloc[local_max_indices]['high'].tolist()
        
        # Cluster nearby levels to reduce noise
        support_levels = self._cluster_levels(support_levels)
        resistance_levels = self._cluster_levels(resistance_levels)
        
        # Sort levels
        support_levels.sort()
        resistance_levels.sort()
        
        # Return the most significant levels (up to 5 each)
        return support_levels[-5:], resistance_levels[-5:]
    
    def _cluster_levels(self, levels: List[float], threshold_pct: float = 0.02) -> List[float]:
        """Cluster nearby price levels to reduce noise.
        
        Groups price levels that are within threshold_pct of each other and
        returns the average of each cluster.
        
        Args:
            levels: List of price levels
            threshold_pct: Percentage threshold for clustering (default: 2%)
            
        Returns:
            List of clustered price levels
        """
        if not levels:
            return []
        
        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            # Check if this level is within threshold of the cluster average
            cluster_avg = sum(current_cluster) / len(current_cluster)
            if abs(level - cluster_avg) / cluster_avg <= threshold_pct:
                current_cluster.append(level)
            else:
                # Start a new cluster
                clustered.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]
        
        # Add the last cluster
        if current_cluster:
            clustered.append(sum(current_cluster) / len(current_cluster))
        
        return clustered
    
    def classify_regime(
        self,
        current_price: float,
        indicators: TechnicalIndicators
    ) -> str:
        """Classify the current technical regime.
        
        Regimes:
        1. Bullish Trend: Price > MA20 > MA50 > MA200, MACD > 0, RSI 50-70
        2. Bearish Trend: Price < MA20 < MA50 < MA200, MACD < 0, RSI 30-50
        3. Oversold Zone: RSI < 25, MACD < 0, Price < MA20
        4. Overbought Zone: RSI > 75, MACD > 0, Price > MA20
        5. Consolidation: None of the above (sideways movement)
        
        Args:
            current_price: Current stock price
            indicators: Technical indicators
            
        Returns:
            Regime classification string
        """
        rsi = indicators.rsi
        macd = indicators.macd
        ma_20 = indicators.ma_20
        ma_50 = indicators.ma_50
        ma_200 = indicators.ma_200
        
        # Check for Oversold Zone (highest priority - potential reversal)
        if rsi < 25 and macd < 0 and current_price < ma_20:
            return "oversold-zone"
        
        # Check for Overbought Zone (highest priority - potential reversal)
        if rsi > 75 and macd > 0 and current_price > ma_20:
            return "overbought-zone"
        
        # Check for Bullish Trend
        # Price > MA20 > MA50 > MA200, MACD > 0, RSI 50-70
        bullish_ma_alignment = (
            current_price > ma_20 and
            ma_20 > ma_50 and
            ma_50 > ma_200
        )
        bullish_momentum = macd > 0 and 50 <= rsi <= 70
        
        if bullish_ma_alignment and bullish_momentum:
            return "bullish-trend"
        
        # Check for Bearish Trend
        # Price < MA20 < MA50 < MA200, MACD < 0, RSI 30-50
        bearish_ma_alignment = (
            current_price < ma_20 and
            ma_20 < ma_50 and
            ma_50 < ma_200
        )
        bearish_momentum = macd < 0 and 30 <= rsi <= 50
        
        if bearish_ma_alignment and bearish_momentum:
            return "bearish-trend"
        
        # Check for partial trend conditions (relaxed criteria)
        # Bullish bias: Price above MAs, positive MACD
        if current_price > ma_20 and macd > 0:
            return "bullish-trend"
        
        # Bearish bias: Price below MAs, negative MACD
        if current_price < ma_20 and macd < 0:
            return "bearish-trend"
        
        # Default to consolidation (sideways movement)
        return "consolidation"
    
    def map_regime_to_direction(self, regime: str) -> tuple[str, float]:
        """Map technical regime to direction and strength.
        
        Args:
            regime: Technical regime classification
            
        Returns:
            Tuple of (direction, strength_multiplier)
        """
        regime_mapping = {
            "bullish-trend": ("bullish", 1.0),
            "bearish-trend": ("bearish", 1.0),
            "oversold-zone": ("bearish-exhaustion", 0.8),  # Potential reversal
            "overbought-zone": ("bullish-exhaustion", 0.8),  # Potential reversal
            "consolidation": ("neutral", 0.5),
            "neutral": ("neutral", 0.5)
        }
        
        return regime_mapping.get(regime, ("neutral", 0.5))
    
    def generate_technical_score(self, indicators: TechnicalIndicators) -> float:
        """Generate overall technical score from indicators.
        
        Combines multiple technical indicators into a single score ranging from
        -1.0 (very bearish) to +1.0 (very bullish). The score is calculated using
        weighted contributions from moving averages, RSI, and MACD.
        
        Weighting:
        - Moving Averages: 30%
        - RSI: 30%
        - MACD: 40%
        
        Args:
            indicators: TechnicalIndicators object with calculated values
            
        Returns:
            Technical score between -1.0 and 1.0
        """
        scores = []
        weights = []
        
        # 1. Moving Average Score (30% weight)
        ma_score = self._calculate_ma_score(indicators)
        scores.append(ma_score)
        weights.append(0.30)
        
        # 2. RSI Score (30% weight)
        rsi_score = self._calculate_rsi_score(indicators.rsi)
        scores.append(rsi_score)
        weights.append(0.30)
        
        # 3. MACD Score (40% weight)
        macd_score = self._calculate_macd_score(indicators.macd, indicators.macd_signal)
        scores.append(macd_score)
        weights.append(0.40)
        
        # Calculate weighted average
        technical_score = sum(s * w for s, w in zip(scores, weights))
        
        # Ensure score is within valid range
        technical_score = max(-1.0, min(1.0, technical_score))
        
        return technical_score
    
    def _calculate_ma_score(self, indicators: TechnicalIndicators) -> float:
        """Calculate score based on moving average relationships.
        
        Bullish signals:
        - Short-term MA > Long-term MA (golden cross)
        - Price trending above MAs
        
        Bearish signals:
        - Short-term MA < Long-term MA (death cross)
        - Price trending below MAs
        
        Args:
            indicators: TechnicalIndicators object
            
        Returns:
            Score between -1.0 and 1.0
        """
        score = 0.0
        
        # Check MA alignment (bullish when short > long)
        if indicators.ma_20 > indicators.ma_50:
            score += 0.33
        else:
            score -= 0.33
        
        if indicators.ma_50 > indicators.ma_200:
            score += 0.33
        else:
            score -= 0.33
        
        # Check if MAs are trending upward (bullish) or downward (bearish)
        # We approximate this by checking the relationship between consecutive MAs
        if indicators.ma_20 > indicators.ma_50 > indicators.ma_200:
            score += 0.34  # Strong bullish alignment
        elif indicators.ma_20 < indicators.ma_50 < indicators.ma_200:
            score -= 0.34  # Strong bearish alignment
        
        return score
    
    def _calculate_rsi_score(self, rsi: float) -> float:
        """Calculate score based on RSI value.
        
        RSI interpretation:
        - RSI > 70: Overbought (bearish signal)
        - RSI < 30: Oversold (bullish signal)
        - 30 <= RSI <= 70: Neutral
        
        Args:
            rsi: RSI value (0-100)
            
        Returns:
            Score between -1.0 and 1.0
        """
        if rsi > 70:
            # Overbought - bearish signal
            # Scale from 70-100 to 0 to -1
            return -(rsi - 70) / 30
        elif rsi < 30:
            # Oversold - bullish signal
            # Scale from 0-30 to 1 to 0
            return (30 - rsi) / 30
        else:
            # Neutral zone - slight bias toward 50 (equilibrium)
            # Scale from 30-70 to slight positive/negative
            return (rsi - 50) / 100  # Small bias, max ±0.2
    
    def _calculate_macd_score(self, macd: float, signal: float) -> float:
        """Calculate score based on MACD and signal line relationship.
        
        MACD interpretation:
        - MACD > Signal: Bullish (upward momentum)
        - MACD < Signal: Bearish (downward momentum)
        - Magnitude of difference indicates strength
        
        Args:
            macd: MACD line value
            signal: Signal line value
            
        Returns:
            Score between -1.0 and 1.0
        """
        # Calculate the difference between MACD and signal
        diff = macd - signal
        
        # Normalize the difference to a score
        # We use a sigmoid-like function to map the difference to [-1, 1]
        # Larger differences indicate stronger signals
        
        # Scale factor - adjust based on typical MACD values
        # This ensures the score reaches ±1 for significant differences
        scale = 2.0
        
        score = np.tanh(diff / scale)
        
        return score
    
    def analyze(self, symbol: str, prices: List[PricePoint]) -> TechnicalIndicators:
        """Perform complete technical analysis on price data.
        
        This is the main entry point for technical analysis. It calculates all
        technical indicators and generates an overall technical score.
        
        Args:
            symbol: Stock ticker symbol
            prices: List of historical price points
            
        Returns:
            TechnicalIndicators object with all calculated values
            
        Raises:
            ValueError: If insufficient data is provided
        """
        if len(prices) < 200:
            raise ValueError("Need at least 200 price points for complete technical analysis")
        
        # Get current price
        current_price = prices[-1].close
        
        # Calculate all indicators
        mas = self.calculate_moving_averages(prices)
        rsi = self.calculate_rsi(prices)
        macd, macd_signal = self.calculate_macd(prices)
        atr = self.calculate_atr(prices)
        support, resistance = self.find_support_resistance(prices)
        
        # Create TechnicalIndicators object (without score first)
        indicators = TechnicalIndicators(
            symbol=symbol,
            ma_20=mas['ma_20'],
            ma_50=mas['ma_50'],
            ma_200=mas['ma_200'],
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            support_levels=support,
            resistance_levels=resistance,
            technical_score=0.0,  # Placeholder
            atr=atr
        )
        
        # Classify technical regime
        regime = self.classify_regime(current_price, indicators)
        
        # Map regime to direction and get strength multiplier
        direction, strength_multiplier = self.map_regime_to_direction(regime)
        
        # Calculate technical score
        technical_score = self.generate_technical_score(indicators)
        
        # Update the score
        indicators.technical_score = technical_score
        
        # Calculate strength based on regime and score
        base_strength = abs(technical_score)
        strength = base_strength * strength_multiplier
        
        # Adjust direction based on regime
        # For exhaustion zones, we keep the direction but note it's exhaustion
        if regime == "oversold-zone":
            # Oversold = bearish exhaustion (potential bullish reversal)
            direction = "bearish"  # Current state is bearish
            strength = strength * 0.7  # Reduce strength due to exhaustion
        elif regime == "overbought-zone":
            # Overbought = bullish exhaustion (potential bearish reversal)
            direction = "bullish"  # Current state is bullish
            strength = strength * 0.7  # Reduce strength due to exhaustion
        elif regime == "consolidation":
            direction = "neutral"
            strength = strength * 0.3  # Reduced strength for neutral
        elif technical_score > 0.2:
            direction = "bullish"
        elif technical_score < -0.2:
            direction = "bearish"
        else:
            direction = "neutral"
            strength = strength * 0.3  # Reduced strength for neutral
        
        # Calculate confidence based on signal strength and regime clarity
        if abs(technical_score) < 0.2:
            confidence = 0.5  # Weak signal
        elif abs(technical_score) > 0.6:
            confidence = 0.95  # Strong signal
        else:
            confidence = 0.8  # Default high confidence for technical
        
        # Boost confidence for clear regime identification
        if regime in ["bullish-trend", "bearish-trend"]:
            confidence = min(1.0, confidence * 1.1)
        elif regime in ["oversold-zone", "overbought-zone"]:
            confidence = min(1.0, confidence * 1.05)
        
        indicators.direction = direction
        indicators.strength = min(1.0, strength)  # Cap at 1.0
        indicators.confidence = confidence
        indicators.regime = regime
        
        return indicators
