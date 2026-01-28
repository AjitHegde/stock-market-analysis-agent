"""No Trade Detector for Stock Market AI Agent.

This module detects dangerous market conditions and blocks trading recommendations
to protect capital during high-risk periods.
"""

from dataclasses import dataclass
from typing import Optional, List
import logging

from src.models import MarketContext


logger = logging.getLogger(__name__)


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


class NoTradeDetector:
    """Detects dangerous market conditions and blocks trading.
    
    This class analyzes market context to identify conditions where trading
    should be avoided to protect capital.
    """
    
    def __init__(
        self,
        vix_spike_threshold: float = 25.0,
        nifty_drop_threshold: float = 0.03,  # 3% drop
        enable_no_trade: bool = True
    ):
        """Initialize the no-trade detector.
        
        Args:
            vix_spike_threshold: VIX level above which trading is blocked
            nifty_drop_threshold: Percentage drop in Nifty to trigger no-trade
            enable_no_trade: Whether to enable no-trade detection
        """
        self.vix_spike_threshold = vix_spike_threshold
        self.nifty_drop_threshold = nifty_drop_threshold
        self.enable_no_trade = enable_no_trade
        
        logger.info(
            f"NoTradeDetector initialized: VIX threshold={vix_spike_threshold}, "
            f"Nifty drop threshold={nifty_drop_threshold:.1%}, "
            f"enabled={enable_no_trade}"
        )
    
    def check_market_conditions(
        self,
        market_context: Optional[MarketContext] = None
    ) -> NoTradeSignal:
        """Check if market conditions warrant blocking trades.
        
        Conditions for NO TRADE:
        1. Market is both bearish AND volatile
        2. Nifty is below 50-day moving average by significant margin
        3. VIX spike above threshold (extreme fear)
        4. Combination of bearish indices and high volatility
        
        Args:
            market_context: Current market context
            
        Returns:
            NoTradeSignal indicating whether to block trading
        """
        # If no-trade detection is disabled, always allow trading
        if not self.enable_no_trade:
            return NoTradeSignal(
                is_no_trade=False,
                reasons=[],
                suggested_action="Trading enabled",
                severity="low"
            )
        
        # If no market context available, allow trading (fail-safe)
        if not market_context:
            logger.warning("No market context available, allowing trading")
            return NoTradeSignal(
                is_no_trade=False,
                reasons=["No market context available"],
                suggested_action="Proceed with caution",
                severity="low"
            )
        
        reasons = []
        severity = "low"
        
        # Check 1: Market is bearish AND volatile (highest priority)
        if (market_context.market_state == "bearish" and 
            market_context.vix_level in ["high", "very_high"]):
            reasons.append(
                f"Market is bearish with {market_context.vix_level.replace('_', ' ')} "
                f"volatility (VIX: {market_context.vix_value:.1f})"
            )
            severity = "high"
        
        # Check 2: Nifty significantly below 50DMA
        nifty_below_50dma = (market_context.nifty_price - market_context.nifty_50dma) / market_context.nifty_50dma
        if nifty_below_50dma < -self.nifty_drop_threshold:
            reasons.append(
                f"Nifty 50 is {abs(nifty_below_50dma):.1%} below its 50-day moving average "
                f"(₹{market_context.nifty_price:,.0f} vs ₹{market_context.nifty_50dma:,.0f})"
            )
            if severity == "low":
                severity = "medium"
        
        # Check 3: VIX spike above threshold (extreme fear)
        if market_context.vix_value > self.vix_spike_threshold:
            reasons.append(
                f"VIX spike detected: {market_context.vix_value:.1f} "
                f"(threshold: {self.vix_spike_threshold:.1f}) - extreme market fear"
            )
            severity = "high"
        
        # Check 4: Both major indices bearish with elevated volatility
        if (market_context.nifty_trend == "bearish" and 
            market_context.banknifty_trend == "bearish" and
            market_context.vix_level in ["moderate", "high", "very_high"]):
            reasons.append(
                "Both Nifty 50 and Bank Nifty are bearish with elevated volatility"
            )
            if severity == "low":
                severity = "medium"
        
        # Check 5: Volatile market state (catch-all)
        if market_context.market_state == "volatile" and market_context.vix_value > 20:
            reasons.append(
                f"Market is highly volatile (VIX: {market_context.vix_value:.1f})"
            )
            if severity == "low":
                severity = "medium"
        
        # Determine if trading should be blocked
        is_no_trade = len(reasons) > 0 and severity in ["high", "medium"]
        
        # Generate suggested action
        if is_no_trade:
            if severity == "high":
                suggested_action = (
                    "🚫 Stay in cash. Avoid all new positions. "
                    "Consider reducing existing positions if possible."
                )
            else:  # medium
                suggested_action = (
                    "⚠️ Exercise extreme caution. Only consider high-conviction trades "
                    "with tight stop losses. Prefer cash."
                )
        else:
            suggested_action = "✅ Market conditions allow trading, but remain vigilant"
        
        if is_no_trade:
            logger.warning(
                f"NO TRADE signal triggered: severity={severity}, "
                f"reasons={len(reasons)}"
            )
        
        return NoTradeSignal(
            is_no_trade=is_no_trade,
            reasons=reasons,
            suggested_action=suggested_action,
            severity=severity
        )
    
    def should_block_recommendation(
        self,
        action: str,
        market_context: Optional[MarketContext] = None
    ) -> bool:
        """Check if a recommendation should be blocked.
        
        Args:
            action: Recommended action ("BUY", "SELL", "HOLD")
            market_context: Current market context
            
        Returns:
            True if recommendation should be blocked, False otherwise
        """
        # Only block BUY recommendations in dangerous conditions
        # Allow SELL and HOLD recommendations
        if action != "BUY":
            return False
        
        signal = self.check_market_conditions(market_context)
        
        # Block BUY recommendations if no-trade signal is active
        if signal.is_no_trade:
            logger.info(f"Blocking BUY recommendation due to no-trade signal")
            return True
        
        return False
    
    def get_market_safety_score(
        self,
        market_context: Optional[MarketContext] = None
    ) -> float:
        """Calculate a market safety score (0.0 = dangerous, 1.0 = safe).
        
        Args:
            market_context: Current market context
            
        Returns:
            Safety score between 0.0 and 1.0
        """
        if not market_context:
            return 0.5  # Neutral if no context
        
        safety_score = 1.0
        
        # Reduce safety for bearish market
        if market_context.market_state == "bearish":
            safety_score -= 0.3
        elif market_context.market_state == "volatile":
            safety_score -= 0.4
        
        # Reduce safety for high VIX
        if market_context.vix_level == "very_high":
            safety_score -= 0.4
        elif market_context.vix_level == "high":
            safety_score -= 0.3
        elif market_context.vix_level == "moderate":
            safety_score -= 0.1
        
        # Reduce safety if Nifty below 50DMA
        nifty_below_50dma = (market_context.nifty_price - market_context.nifty_50dma) / market_context.nifty_50dma
        if nifty_below_50dma < -0.05:  # More than 5% below
            safety_score -= 0.3
        elif nifty_below_50dma < -0.03:  # More than 3% below
            safety_score -= 0.2
        
        # Ensure score is within valid range
        safety_score = max(0.0, min(1.0, safety_score))
        
        return safety_score
