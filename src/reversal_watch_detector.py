"""Reversal Watch Detector for Stock Market AI Agent.

This module detects potential reversal setups when stocks are oversold
but have solid fundamentals and market conditions are not in panic mode.
"""

from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

from src.models import (
    TechnicalIndicators,
    FundamentalMetrics,
    MarketContext,
    PricePoint
)


logger = logging.getLogger(__name__)


@dataclass
class ReversalTrigger:
    """Represents a reversal trigger condition.
    
    Attributes:
        name: Name of the trigger
        met: Whether the trigger condition is met
        value: Current value of the trigger metric
        threshold: Threshold value for the trigger
        description: Human-readable description
    """
    name: str
    met: bool
    value: float
    threshold: float
    description: str


@dataclass
class ReversalWatch:
    """Represents a potential reversal setup.
    
    Attributes:
        symbol: Stock ticker symbol
        is_reversal_setup: Whether this is a valid reversal setup
        status: Status of the reversal watch ("watch-only", "triggered", "not-applicable")
        triggers: List of reversal triggers and their status
        confidence: Confidence in the reversal setup (0.0 to 1.0)
        reasoning: Explanation of why this is/isn't a reversal setup
        timestamp: When the analysis was performed
    """
    symbol: str
    is_reversal_setup: bool
    status: str
    triggers: List[ReversalTrigger]
    confidence: float
    reasoning: str
    timestamp: datetime


class ReversalWatchDetector:
    """Detects potential reversal setups in oversold stocks with good fundamentals."""
    
    def __init__(self):
        """Initialize the reversal watch detector."""
        pass
    
    def check_fundamental_quality(self, fundamental: FundamentalMetrics) -> tuple[bool, str]:
        """Check if fundamentals are at least fair quality.
        
        Criteria for "fair" fundamentals:
        - P/E ratio < 30 (not overvalued)
        - P/B ratio < 5 (not extremely expensive)
        - Debt-to-equity < 2.0 (manageable debt)
        - Revenue growth > -10% (not declining rapidly)
        - Fundamental score >= 0 (neutral or better)
        
        Args:
            fundamental: Fundamental metrics
            
        Returns:
            Tuple of (is_fair, reason)
        """
        reasons = []
        
        # Check fundamental score first
        if fundamental.fundamental_score < 0:
            return False, "Fundamental score is negative (poor fundamentals)"
        
        # Check P/E ratio
        if fundamental.pe_ratio is not None:
            if fundamental.pe_ratio > 30:
                return False, f"P/E ratio too high ({fundamental.pe_ratio:.1f} > 30)"
            reasons.append(f"P/E: {fundamental.pe_ratio:.1f}")
        
        # Check P/B ratio
        if fundamental.pb_ratio is not None:
            if fundamental.pb_ratio > 5:
                return False, f"P/B ratio too high ({fundamental.pb_ratio:.1f} > 5)"
            reasons.append(f"P/B: {fundamental.pb_ratio:.1f}")
        
        # Check debt-to-equity
        if fundamental.debt_to_equity is not None:
            if fundamental.debt_to_equity > 2.0:
                return False, f"Debt-to-equity too high ({fundamental.debt_to_equity:.1f} > 2.0)"
            reasons.append(f"D/E: {fundamental.debt_to_equity:.1f}")
        
        # Check revenue growth
        if fundamental.revenue_growth is not None:
            if fundamental.revenue_growth < -10:
                return False, f"Revenue declining rapidly ({fundamental.revenue_growth:.1f}% < -10%)"
            reasons.append(f"Revenue growth: {fundamental.revenue_growth:.1f}%")
        
        reason_text = "Fair fundamentals: " + ", ".join(reasons) if reasons else "Fundamentals are acceptable"
        return True, reason_text
    
    def check_market_panic(self, market_context: Optional[MarketContext]) -> tuple[bool, str]:
        """Check if market is in panic mode.
        
        Panic indicators:
        - VIX > 30 (extreme fear)
        - Market state is "volatile" with very high VIX
        
        Args:
            market_context: Market context (optional)
            
        Returns:
            Tuple of (is_panic, reason)
        """
        if not market_context:
            return False, "No market context available (assuming not panic)"
        
        # Check VIX level
        if market_context.vix_value > 30:
            return True, f"VIX extremely high ({market_context.vix_value:.1f} > 30) - market panic"
        
        # Check for volatile market with high VIX
        if market_context.market_state == "volatile" and market_context.vix_value > 25:
            return True, f"Volatile market with high VIX ({market_context.vix_value:.1f})"
        
        return False, f"Market not in panic (VIX: {market_context.vix_value:.1f})"
    
    def check_reversal_triggers(
        self,
        technical: TechnicalIndicators,
        prices: List[PricePoint]
    ) -> List[ReversalTrigger]:
        """Check reversal trigger conditions.
        
        Triggers:
        1. RSI > 30 (recovering from oversold)
        2. MACD Histogram turns positive (momentum shift)
        3. Volume spike (increased interest)
        
        Args:
            technical: Technical indicators
            prices: Recent price data for volume analysis
            
        Returns:
            List of ReversalTrigger objects
        """
        triggers = []
        
        # Trigger 1: RSI > 30
        rsi_met = technical.rsi > 30
        triggers.append(ReversalTrigger(
            name="RSI Recovery",
            met=rsi_met,
            value=technical.rsi,
            threshold=30.0,
            description=f"RSI recovering from oversold (current: {technical.rsi:.1f})"
        ))
        
        # Trigger 2: MACD Histogram turns positive
        macd_histogram = technical.macd - technical.macd_signal
        macd_met = macd_histogram > 0
        triggers.append(ReversalTrigger(
            name="MACD Momentum",
            met=macd_met,
            value=macd_histogram,
            threshold=0.0,
            description=f"MACD histogram {'positive' if macd_met else 'negative'} ({macd_histogram:.2f})"
        ))
        
        # Trigger 3: Volume spike (current volume > 1.5x average)
        if len(prices) >= 20:
            recent_volumes = [p.volume for p in prices[-20:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes)
            current_volume = prices[-1].volume
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            volume_met = volume_ratio > 1.5
            
            triggers.append(ReversalTrigger(
                name="Volume Spike",
                met=volume_met,
                value=volume_ratio,
                threshold=1.5,
                description=f"Volume {'spike' if volume_met else 'normal'} ({volume_ratio:.1f}x average)"
            ))
        else:
            # Not enough data for volume analysis
            triggers.append(ReversalTrigger(
                name="Volume Spike",
                met=False,
                value=0.0,
                threshold=1.5,
                description="Insufficient data for volume analysis"
            ))
        
        return triggers
    
    def detect(
        self,
        symbol: str,
        technical: TechnicalIndicators,
        fundamental: FundamentalMetrics,
        market_context: Optional[MarketContext],
        prices: List[PricePoint]
    ) -> ReversalWatch:
        """Detect potential reversal setup.
        
        Conditions for reversal setup:
        1. Technical regime is "oversold-zone"
        2. Fundamentals are at least fair
        3. Market is not in panic mode
        
        If all conditions met, check reversal triggers:
        - RSI > 30
        - MACD Histogram > 0
        - Volume spike (> 1.5x average)
        
        Args:
            symbol: Stock ticker symbol
            technical: Technical indicators
            fundamental: Fundamental metrics
            market_context: Market context (optional)
            prices: Recent price data
            
        Returns:
            ReversalWatch object with analysis results
        """
        logger.info(f"Checking reversal setup for {symbol}")
        
        reasons = []
        
        # Check condition 1: Oversold zone
        is_oversold = technical.regime == "oversold-zone"
        if not is_oversold:
            return ReversalWatch(
                symbol=symbol,
                is_reversal_setup=False,
                status="not-applicable",
                triggers=[],
                confidence=0.0,
                reasoning=f"Not in oversold zone (current regime: {technical.regime})",
                timestamp=datetime.now()
            )
        
        reasons.append("✓ In oversold zone")
        
        # Check condition 2: Fair fundamentals
        fundamentals_ok, fund_reason = self.check_fundamental_quality(fundamental)
        if not fundamentals_ok:
            return ReversalWatch(
                symbol=symbol,
                is_reversal_setup=False,
                status="not-applicable",
                triggers=[],
                confidence=0.0,
                reasoning=f"Oversold but poor fundamentals: {fund_reason}",
                timestamp=datetime.now()
            )
        
        reasons.append(f"✓ {fund_reason}")
        
        # Check condition 3: Market not in panic
        is_panic, panic_reason = self.check_market_panic(market_context)
        if is_panic:
            return ReversalWatch(
                symbol=symbol,
                is_reversal_setup=False,
                status="not-applicable",
                triggers=[],
                confidence=0.0,
                reasoning=f"Oversold with fair fundamentals but {panic_reason}",
                timestamp=datetime.now()
            )
        
        reasons.append(f"✓ {panic_reason}")
        
        # All conditions met - this is a reversal setup!
        # Now check reversal triggers
        triggers = self.check_reversal_triggers(technical, prices)
        
        # Count how many triggers are met
        triggers_met = sum(1 for t in triggers if t.met)
        total_triggers = len(triggers)
        
        # Determine status
        if triggers_met == total_triggers:
            status = "triggered"
            confidence = 0.85  # High confidence when all triggers met
            reasons.append(f"🎯 All {total_triggers} reversal triggers met!")
        elif triggers_met >= 2:
            status = "watch-only"
            confidence = 0.65  # Medium confidence with 2/3 triggers
            reasons.append(f"⏳ {triggers_met}/{total_triggers} reversal triggers met - watch closely")
        else:
            status = "watch-only"
            confidence = 0.45  # Lower confidence with only 1 trigger
            reasons.append(f"⏳ {triggers_met}/{total_triggers} reversal triggers met - early stage")
        
        reasoning = "\n".join(reasons)
        
        logger.info(
            f"Reversal setup detected for {symbol}: status={status}, "
            f"triggers={triggers_met}/{total_triggers}, confidence={confidence:.0%}"
        )
        
        return ReversalWatch(
            symbol=symbol,
            is_reversal_setup=True,
            status=status,
            triggers=triggers,
            confidence=confidence,
            reasoning=reasoning,
            timestamp=datetime.now()
        )
