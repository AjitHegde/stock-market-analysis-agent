"""Recommendation Engine for Stock Market AI Agent.

This module generates trading recommendations by combining sentiment, technical,
and fundamental analysis results using configured weights.
"""

import numpy as np
from datetime import datetime
from typing import Tuple, Optional
import logging

from src.models import (
    SentimentData,
    TechnicalIndicators,
    FundamentalMetrics,
    Recommendation
)
from src.config import Configuration


logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates trading recommendations from analysis results.
    
    This class combines sentiment, technical, and fundamental analysis scores
    using configured weights to generate BUY, SELL, or HOLD recommendations
    with confidence scores and price ranges.
    """
    
    def __init__(self, config: Configuration):
        """Initialize the recommendation engine.
        
        Args:
            config: Configuration object with analysis weights
        """
        self.config = config
        
        # Ensure weights are normalized
        if not self.config.validate_weights():
            logger.warning("Invalid weights detected, normalizing...")
            self.config.normalize_weights()
        elif abs(sum([config.sentiment_weight, config.technical_weight, 
                      config.fundamental_weight]) - 1.0) > 0.001:
            logger.info("Weights don't sum to 1.0, normalizing...")
            self.config.normalize_weights()
    
    def _get_dynamic_weights(self, market_context: Optional['MarketContext']) -> dict:
        """Get dynamic weights based on market conditions.
        
        Rules:
        - BULLISH: sentiment 30%, technical 40%, fundamental 30%
        - NEUTRAL: sentiment 25%, technical 35%, fundamental 40%
        - BEARISH/VOLATILE: sentiment 15%, technical 35%, fundamental 50%
        - No market context: Use static config weights
        
        Args:
            market_context: Market context (optional)
            
        Returns:
            Dictionary with sentiment, technical, fundamental weights
        """
        if not market_context:
            logger.info("No market context - using static config weights")
            return {
                'sentiment': self.config.sentiment_weight,
                'technical': self.config.technical_weight,
                'fundamental': self.config.fundamental_weight,
                'source': 'static'
            }
        
        market_state = market_context.market_state.lower()
        
        if market_state == "bullish":
            weights = {
                'sentiment': 0.30,
                'technical': 0.40,
                'fundamental': 0.30,
                'source': 'dynamic-bullish'
            }
            logger.info("Using BULLISH market weights: S:30%, T:40%, F:30%")
        elif market_state == "neutral":
            weights = {
                'sentiment': 0.25,
                'technical': 0.35,
                'fundamental': 0.40,
                'source': 'dynamic-neutral'
            }
            logger.info("Using NEUTRAL market weights: S:25%, T:35%, F:40%")
        elif market_state == "bearish":
            weights = {
                'sentiment': 0.15,
                'technical': 0.35,
                'fundamental': 0.50,
                'source': 'dynamic-bearish'
            }
            logger.info("Using BEARISH market weights: S:15%, T:35%, F:50%")
        elif market_state == "volatile":
            weights = {
                'sentiment': 0.15,
                'technical': 0.35,
                'fundamental': 0.50,
                'source': 'dynamic-volatile'
            }
            logger.info("Using VOLATILE market weights: S:15%, T:35%, F:50%")
        else:
            # Unknown market state - fallback to static
            logger.warning(f"Unknown market state '{market_state}' - using static config weights")
            weights = {
                'sentiment': self.config.sentiment_weight,
                'technical': self.config.technical_weight,
                'fundamental': self.config.fundamental_weight,
                'source': 'static-fallback'
            }
        
        return weights
    
    def generate_recommendation(
        self,
        sentiment: SentimentData,
        technical: TechnicalIndicators,
        fundamental: FundamentalMetrics,
        current_price: float,
        market_context: Optional['MarketContext'] = None
    ) -> Recommendation:
        """Generate trading recommendation from all analyses.
        
        Combines sentiment, technical, and fundamental scores using dynamic
        market-based weights to determine the recommended action (BUY, SELL, HOLD).
        
        Args:
            sentiment: Sentiment analysis results
            technical: Technical analysis results
            fundamental: Fundamental analysis results
            current_price: Current stock price
            market_context: Market context for dynamic weight adjustment
            
        Returns:
            Recommendation object with action, confidence, and reasoning
            
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 10.6
        """
        # Get dynamic weights based on market conditions
        weights = self._get_dynamic_weights(market_context)
        sentiment_weight = weights['sentiment']
        technical_weight = weights['technical']
        fundamental_weight = weights['fundamental']
        weights_source = weights['source']
        
        logger.info(
            f"Active weights ({weights_source}): "
            f"sentiment={sentiment_weight:.0%}, "
            f"technical={technical_weight:.0%}, "
            f"fundamental={fundamental_weight:.0%}"
        )
        
        # Calculate weighted combined score using dynamic weights
        combined_score = (
            sentiment.sentiment_score * sentiment_weight +
            technical.technical_score * technical_weight +
            fundamental.fundamental_score * fundamental_weight
        )
        
        # Store individual contributions for transparency
        sentiment_contribution = sentiment.sentiment_score * sentiment_weight
        technical_contribution = technical.technical_score * technical_weight
        fundamental_contribution = fundamental.fundamental_score * fundamental_weight
        
        # Store runtime weights (actual weights used)
        runtime_weights = {
            'sentiment': sentiment_weight,
            'technical': technical_weight,
            'fundamental': fundamental_weight,
            'source': weights_source
        }
        
        # Determine action based on combined score
        if combined_score > 0.3:
            action = "BUY"
        elif combined_score < -0.3:
            action = "SELL"
        else:
            action = "HOLD"
        
        # Calculate confidence score
        confidence, confidence_breakdown = self.calculate_confidence(
            sentiment, technical, fundamental, combined_score, market_context
        )
        
        # Adjust action based on market context (if available)
        if market_context:
            action = self._adjust_for_market_context(action, combined_score, market_context)
        
        # Generate price ranges for BUY/SELL actions
        entry_price_low, entry_price_high = None, None
        exit_price_low, exit_price_high = None, None
        trade_levels = None
        
        if action == "BUY":
            entry_price_low, entry_price_high = self.suggest_price_range(
                action, current_price, technical
            )
            # Calculate precise trade levels for BUY recommendations
            trade_levels = self.calculate_trade_levels(
                current_price, technical, action
            )
        elif action == "SELL":
            exit_price_low, exit_price_high = self.suggest_price_range(
                action, current_price, technical
            )
        
        # Generate reasoning text
        reasoning = self._generate_reasoning(
            action,
            combined_score,
            sentiment,
            technical,
            fundamental,
            confidence,
            market_context
        )
        
        logger.info(
            f"Generated {action} recommendation for {sentiment.symbol} "
            f"with confidence {confidence:.2f}"
        )
        
        return Recommendation(
            symbol=sentiment.symbol,
            action=action,
            confidence=confidence,
            entry_price_low=entry_price_low,
            entry_price_high=entry_price_high,
            exit_price_low=exit_price_low,
            exit_price_high=exit_price_high,
            reasoning=reasoning,
            sentiment_contribution=sentiment_contribution,
            technical_contribution=technical_contribution,
            fundamental_contribution=fundamental_contribution,
            timestamp=datetime.now(),
            trade_levels=trade_levels,
            confidence_breakdown=confidence_breakdown,
            runtime_weights=runtime_weights
        )
    
    def calculate_confidence(
        self,
        sentiment: SentimentData,
        technical: TechnicalIndicators,
        fundamental: FundamentalMetrics,
        combined_score: float,
        market_context: Optional['MarketContext'] = None
    ) -> Tuple[float, 'ConfidenceBreakdown']:
        """Calculate confidence score based on weighted agreement between components.
        
        New confidence calculation:
        - All 4 components agree → High confidence (80%+)
        - 3 components agree → Medium-high (70-80%)
        - 2 components agree → Medium (60-75%)
        - 1 component agrees → Low (<50%)
        
        Reduces confidence for:
        - Missing data (low sentiment sources, no market context)
        - API failures (indicated by default/zero values)
        - Low sample size (few sentiment sources)
        
        Args:
            sentiment: Sentiment analysis results
            technical: Technical analysis results
            fundamental: Fundamental analysis results
            combined_score: Weighted combined score
            market_context: Market context (optional)
            
        Returns:
            Tuple of (confidence score, confidence breakdown)
            
        Validates: Requirements 4.4, 4.7
        """
        from src.models import ConfidenceBreakdown
        
        # 1. Determine signal direction from combined score
        if combined_score > 0.3:
            signal_direction = "bullish"
        elif combined_score < -0.3:
            signal_direction = "bearish"
        else:
            signal_direction = "neutral"
        
        # 2. Check agreement for each component
        def agrees_with_signal(score: float, direction: str) -> bool:
            """Check if a score agrees with the signal direction."""
            if direction == "bullish":
                return score > 0.2
            elif direction == "bearish":
                return score < -0.2
            else:  # neutral
                return -0.2 <= score <= 0.2
        
        sentiment_agrees = agrees_with_signal(sentiment.sentiment_score, signal_direction)
        technical_agrees = agrees_with_signal(technical.technical_score, signal_direction)
        fundamental_agrees = agrees_with_signal(fundamental.fundamental_score, signal_direction)
        
        # Market context agreement (if available)
        market_agrees = False
        if market_context:
            if signal_direction == "bullish":
                market_agrees = market_context.market_state in ["bullish", "neutral"]
            elif signal_direction == "bearish":
                market_agrees = market_context.market_state in ["bearish", "neutral"]
            else:  # neutral
                market_agrees = market_context.market_state == "neutral"
        
        # Count agreements
        agreements = sum([sentiment_agrees, technical_agrees, fundamental_agrees])
        if market_context:
            agreements += market_agrees
            total_components = 4
        else:
            total_components = 3
        
        # 3. Calculate base agreement score
        if total_components == 4:
            # All 4 components available
            if agreements == 4:
                agreement_score = 0.85  # All agree → High confidence
            elif agreements == 3:
                agreement_score = 0.75  # 3 agree → Medium-high
            elif agreements == 2:
                agreement_score = 0.65  # 2 agree → Medium
            else:
                agreement_score = 0.45  # 1 or 0 agree → Low
        else:
            # Only 3 components (no market context)
            if agreements == 3:
                agreement_score = 0.80  # All agree → High
            elif agreements == 2:
                agreement_score = 0.70  # 2 agree → Medium
            else:
                agreement_score = 0.50  # 1 or 0 agree → Low
        
        # 4. Calculate individual component confidence scores
        # Sentiment confidence: based on source count and sentiment confidence
        sentiment_conf = sentiment.confidence if sentiment.confidence > 0 else 0.5
        if len(sentiment.sources) < 2:
            sentiment_conf *= 0.7  # Penalty for low sample size
        elif len(sentiment.sources) >= 5:
            sentiment_conf = min(1.0, sentiment_conf * 1.1)  # Boost for good sample size
        
        # Technical confidence: based on signal strength
        technical_conf = 0.8  # Default high confidence for technical
        if abs(technical.technical_score) < 0.2:
            technical_conf = 0.5  # Weak signal
        elif abs(technical.technical_score) > 0.6:
            technical_conf = 0.95  # Strong signal
        
        # Fundamental confidence: based on data availability
        fundamental_conf = 0.7  # Default moderate confidence
        missing_metrics = sum([
            fundamental.pe_ratio is None,
            fundamental.pb_ratio is None,
            fundamental.revenue_growth is None
        ])
        if missing_metrics == 0:
            fundamental_conf = 0.9  # All metrics available
        elif missing_metrics >= 2:
            fundamental_conf = 0.5  # Many metrics missing
        
        # Market confidence: based on favorability for long trades
        market_signal_quality = 0.0
        market_favorability = 0.0
        if market_context:
            market_signal_quality = market_context.market_signal_quality
            market_favorability = market_context.market_favorability
        
        # 5. Calculate data quality penalty
        data_quality_penalty = 0.0
        
        # Penalty for missing market context
        if not market_context:
            data_quality_penalty += 0.05
        
        # Penalty for low sentiment sources
        if len(sentiment.sources) < 2:
            data_quality_penalty += 0.10
        elif len(sentiment.sources) < 3:
            data_quality_penalty += 0.05
        
        # Penalty for missing fundamental data
        if missing_metrics >= 2:
            data_quality_penalty += 0.10
        elif missing_metrics == 1:
            data_quality_penalty += 0.05
        
        # Penalty for API failures (indicated by zero/default values)
        if sentiment.sentiment_score == 0 and len(sentiment.sources) == 0:
            data_quality_penalty += 0.15  # Likely API failure
        
        # Cap penalty at 0.3 (30%)
        data_quality_penalty = min(0.3, data_quality_penalty)
        
        # 6. Calculate final confidence
        # Weight agreement score heavily, but factor in component confidences
        # Use market_favorability (not quality) in final confidence calculation
        confidence = (
            agreement_score * 0.6 +  # Agreement is most important
            sentiment_conf * 0.15 +  # Individual confidences
            technical_conf * 0.10 +
            fundamental_conf * 0.10 +
            market_favorability * 0.05  # Use favorability, not quality
        )
        
        # Apply data quality penalty
        confidence = confidence * (1.0 - data_quality_penalty)
        
        # Ensure confidence is within valid range
        confidence = max(0.0, min(1.0, confidence))
        
        # 7. Create confidence breakdown
        breakdown = ConfidenceBreakdown(
            sentiment_confidence=round(sentiment_conf, 2),
            technical_confidence=round(technical_conf, 2),
            fundamental_confidence=round(fundamental_conf, 2),
            market_signal_quality=round(market_signal_quality, 2),
            market_favorability=round(market_favorability, 2),
            agreement_score=round(agreement_score, 2),
            data_quality_penalty=round(data_quality_penalty, 2)
        )
        
        logger.debug(
            f"Confidence calculation: agreements={agreements}/{total_components}, "
            f"agreement_score={agreement_score:.2f}, "
            f"data_penalty={data_quality_penalty:.2f}, "
            f"final={confidence:.2f}"
        )
        
        return confidence, breakdown
    
    def suggest_price_range(
        self,
        action: str,
        current_price: float,
        technical: TechnicalIndicators
    ) -> Tuple[float, float]:
        """Suggest entry/exit price range based on technical levels.
        
        For BUY: Uses support levels and current price
        For SELL: Uses resistance levels and current price
        
        Args:
            action: Recommended action ("BUY" or "SELL")
            current_price: Current stock price
            technical: Technical analysis results
            
        Returns:
            Tuple of (price_low, price_high)
            
        Validates: Requirements 4.2, 4.3
        """
        if action == "BUY":
            # For BUY, suggest entry range around current price
            # Use nearest support level if available
            if technical.support_levels:
                # Find support level closest to but below current price
                supports_below = [s for s in technical.support_levels if s < current_price]
                if supports_below:
                    nearest_support = max(supports_below)
                    # Range from support to slightly above current price
                    price_low = nearest_support
                    price_high = current_price * 1.02
                else:
                    # No support below, use default range
                    price_low = current_price * 0.98
                    price_high = current_price * 1.02
            else:
                # No support levels, use default range around current price
                price_low = current_price * 0.98
                price_high = current_price * 1.02
        
        elif action == "SELL":
            # For SELL, suggest exit range around current price
            # Use nearest resistance level if available
            if technical.resistance_levels:
                # Find resistance level closest to but above current price
                resistances_above = [r for r in technical.resistance_levels if r > current_price]
                if resistances_above:
                    nearest_resistance = min(resistances_above)
                    # Range from slightly below current price to resistance
                    price_low = current_price * 0.98
                    price_high = nearest_resistance
                else:
                    # No resistance above, use default range
                    price_low = current_price * 0.98
                    price_high = current_price * 1.02
            else:
                # No resistance levels, use default range around current price
                price_low = current_price * 0.98
                price_high = current_price * 1.02
        
        else:
            # Should not reach here, but handle gracefully
            price_low = current_price * 0.98
            price_high = current_price * 1.02
        
        return price_low, price_high
    
    def _generate_reasoning(
        self,
        action: str,
        combined_score: float,
        sentiment: SentimentData,
        technical: TechnicalIndicators,
        fundamental: FundamentalMetrics,
        confidence: float,
        market_context: Optional['MarketContext'] = None
    ) -> str:
        """Generate human-readable reasoning for the recommendation.
        
        Args:
            action: Recommended action
            combined_score: Weighted combined score
            sentiment: Sentiment analysis results
            technical: Technical analysis results
            fundamental: Fundamental analysis results
            confidence: Confidence score
            
        Returns:
            Reasoning text explaining the recommendation
        """
        reasoning_parts = []
        
        # Overall recommendation
        reasoning_parts.append(
            f"Recommendation: {action} with {confidence:.0%} confidence "
            f"(combined score: {combined_score:+.2f})"
        )
        
        # Sentiment analysis contribution
        sentiment_desc = self._describe_score(sentiment.sentiment_score, "sentiment")
        reasoning_parts.append(
            f"Sentiment Analysis: {sentiment_desc} "
            f"(score: {sentiment.sentiment_score:+.2f}, "
            f"confidence: {sentiment.confidence:.0%}, "
            f"sources: {len(sentiment.sources)})"
        )
        
        # Technical analysis contribution
        technical_desc = self._describe_score(technical.technical_score, "technical")
        reasoning_parts.append(
            f"Technical Analysis: {technical_desc} "
            f"(score: {technical.technical_score:+.2f}, "
            f"RSI: {technical.rsi:.1f}, "
            f"MACD: {technical.macd:+.2f})"
        )
        
        # Fundamental analysis contribution
        fundamental_desc = self._describe_score(fundamental.fundamental_score, "fundamental")
        pe_info = f"P/E: {fundamental.pe_ratio:.1f}" if fundamental.pe_ratio else "P/E: N/A"
        reasoning_parts.append(
            f"Fundamental Analysis: {fundamental_desc} "
            f"(score: {fundamental.fundamental_score:+.2f}, {pe_info})"
        )
        
        # Check for conflicting signals
        scores = [
            sentiment.sentiment_score,
            technical.technical_score,
            fundamental.fundamental_score
        ]
        std_dev = np.std(scores)
        
        if std_dev > 0.5:
            reasoning_parts.append(
                "⚠️ Note: Conflicting signals detected between analyzers. "
                "Exercise caution and consider waiting for clearer signals."
            )
        
        # Add market context information (if available)
        if market_context:
            market_desc = self._describe_market_context(market_context)
            reasoning_parts.append(f"Market Context: {market_desc}")
        
        return "\n\n".join(reasoning_parts)
    
    def _describe_score(self, score: float, analysis_type: str) -> str:
        """Convert a numerical score to a descriptive label.
        
        Args:
            score: Score value (-1.0 to +1.0)
            analysis_type: Type of analysis (for context)
            
        Returns:
            Descriptive label for the score
        """
        if score > 0.5:
            return "Very bullish"
        elif score > 0.2:
            return "Bullish"
        elif score > -0.2:
            return "Neutral"
        elif score > -0.5:
            return "Bearish"
        else:
            return "Very bearish"

    def _adjust_for_market_context(
        self,
        action: str,
        combined_score: float,
        market_context: 'MarketContext'
    ) -> str:
        """Adjust recommendation action based on broader market context.
        
        Args:
            action: Original recommended action
            combined_score: Combined analysis score
            market_context: Market context information
            
        Returns:
            Adjusted action (may be same as original)
        """
        # In volatile markets, be more conservative
        if market_context.market_state == "volatile":
            # Downgrade BUY to HOLD if score is weak
            if action == "BUY" and combined_score < 0.5:
                logger.info(f"Downgrading BUY to HOLD due to volatile market (VIX: {market_context.vix_value:.1f})")
                return "HOLD"
            # Downgrade SELL to HOLD if score is weak
            elif action == "SELL" and combined_score > -0.5:
                logger.info(f"Downgrading SELL to HOLD due to volatile market (VIX: {market_context.vix_value:.1f})")
                return "HOLD"
        
        # In bearish markets, be more cautious with BUY recommendations
        if market_context.market_state == "bearish":
            if action == "BUY" and combined_score < 0.6:
                logger.info(f"Downgrading BUY to HOLD due to bearish market")
                return "HOLD"
        
        return action
    
    def _describe_market_context(self, market_context: 'MarketContext') -> str:
        """Generate description of market context.
        
        Args:
            market_context: Market context information
            
        Returns:
            Human-readable market context description
        """
        parts = []
        
        # Overall market state
        state_emoji = {
            "bullish": "🟢",
            "neutral": "🟡",
            "bearish": "🔴",
            "volatile": "⚠️"
        }
        emoji = state_emoji.get(market_context.market_state, "")
        parts.append(f"{emoji} Market is {market_context.market_state}")
        
        # Nifty trend
        parts.append(f"Nifty 50 is {market_context.nifty_trend}")
        
        # Bank Nifty trend
        parts.append(f"Bank Nifty is {market_context.banknifty_trend}")
        
        # VIX level
        vix_desc = {
            "low": "low (calm)",
            "moderate": "moderate",
            "high": "high (elevated)",
            "very_high": "very high (extreme)"
        }
        vix_text = vix_desc.get(market_context.vix_level, market_context.vix_level)
        parts.append(f"Volatility (VIX) is {vix_text} at {market_context.vix_value:.1f}")
        
        return ". ".join(parts) + "."

    def calculate_trade_levels(
        self,
        current_price: float,
        technical: 'TechnicalIndicators',
        action: str
    ) -> 'TradeLevels':
        """Calculate precise trade entry, stop loss, and target levels.
        
        Uses support/resistance, ATR, and recent price action to determine:
        - Ideal entry zone (tight range near support/breakout)
        - Stop loss (below recent swing low or ATR-based)
        - Target (minimum 2x risk for 1:2 R:R ratio)
        - Position sizing (risk ≤1.5% of capital)
        
        Args:
            current_price: Current stock price
            technical: Technical indicators including support, resistance, ATR
            action: Trading action ("BUY" or "SELL")
            
        Returns:
            TradeLevels object with entry, stop loss, target, and risk metrics
        """
        from src.models import TradeLevels
        
        if action != "BUY":
            # For now, only calculate trade levels for BUY recommendations
            # SELL levels would be inverse logic
            raise ValueError("Trade levels currently only supported for BUY recommendations")
        
        # 1. Calculate Ideal Entry
        # Use support level if available, otherwise use current price with small discount
        if technical.support_levels:
            # Find nearest support below current price
            supports_below = [s for s in technical.support_levels if s < current_price]
            if supports_below:
                nearest_support = max(supports_below)
                # Entry slightly above support (0.5% buffer)
                ideal_entry = nearest_support * 1.005
            else:
                # No support below, use current price with 2% discount
                ideal_entry = current_price * 0.98
        else:
            # No support levels, use current price with 2% discount
            ideal_entry = current_price * 0.98
        
        # Ensure entry is not above current price
        ideal_entry = min(ideal_entry, current_price * 0.99)
        
        # 2. Calculate Stop Loss
        # Use the lower of: ATR-based stop or support-based stop
        atr_stop = ideal_entry - (technical.atr * 1.5) if technical.atr > 0 else ideal_entry * 0.95
        
        if technical.support_levels:
            # Find support below entry
            supports_below_entry = [s for s in technical.support_levels if s < ideal_entry]
            if supports_below_entry:
                support_stop = max(supports_below_entry) * 0.995  # Slightly below support
                # Use the higher of ATR stop or support stop (tighter stop)
                stop_loss = max(atr_stop, support_stop)
            else:
                stop_loss = atr_stop
        else:
            stop_loss = atr_stop
        
        # Ensure stop loss is reasonable (not more than 8% below entry)
        min_stop = ideal_entry * 0.92
        stop_loss = max(stop_loss, min_stop)
        
        # 3. Calculate Risk per share
        risk_per_share = ideal_entry - stop_loss
        
        # 4. Calculate Target (minimum 2x risk for 1:2 R:R)
        min_reward = risk_per_share * 2.0
        target = ideal_entry + min_reward
        
        # Adjust target based on resistance if available
        if technical.resistance_levels:
            # Find resistance above entry
            resistances_above = [r for r in technical.resistance_levels if r > ideal_entry]
            if resistances_above:
                nearest_resistance = min(resistances_above)
                # If resistance is beyond our minimum target, use it
                if nearest_resistance > target:
                    target = nearest_resistance * 0.995  # Slightly below resistance
                # If resistance is before our minimum target, extend target beyond it
                elif nearest_resistance < target:
                    target = max(target, nearest_resistance * 1.02)
        
        # 5. Calculate actual Risk:Reward ratio
        actual_reward = target - ideal_entry
        risk_reward_ratio = actual_reward / risk_per_share if risk_per_share > 0 else 2.0
        
        # Ensure minimum 1:2 R:R ratio
        if risk_reward_ratio < 2.0:
            target = ideal_entry + (risk_per_share * 2.0)
            risk_reward_ratio = 2.0
        
        # 6. Calculate position sizing (risk ≤1.5% of capital)
        # Risk per trade = 1.5% of capital (conservative)
        risk_per_trade_percent = 1.5
        
        # Position size = (Capital * Risk%) / Risk per share
        # Expressed as percentage of capital
        position_size_percent = (risk_per_trade_percent / (risk_per_share / ideal_entry * 100))
        
        # Cap position size at 10% of capital (diversification)
        position_size_percent = min(position_size_percent, 10.0)
        
        return TradeLevels(
            ideal_entry=round(ideal_entry, 2),
            stop_loss=round(stop_loss, 2),
            target=round(target, 2),
            risk_per_trade_percent=risk_per_trade_percent,
            risk_reward_ratio=round(risk_reward_ratio, 2),
            position_size_percent=round(position_size_percent, 2)
        )
