"""Risk management for Stock Market AI Agent."""

from typing import List, Dict
import numpy as np
from src.models import (
    Position,
    RiskAssessment,
    ConcentrationRisk,
    CorrelationRisk
)


class RiskManager:
    """Manages portfolio risk assessment and position sizing.
    
    The Risk Manager evaluates portfolio risk, suggests position sizes,
    and identifies concentration and correlation risks.
    """
    
    # Risk tolerance multipliers for position sizing
    RISK_TOLERANCE_MULTIPLIERS = {
        'conservative': 0.5,
        'moderate': 1.0,
        'aggressive': 1.5
    }
    
    # Concentration threshold (20% of portfolio)
    CONCENTRATION_THRESHOLD = 20.0
    
    # High correlation threshold
    HIGH_CORRELATION_THRESHOLD = 0.7
    
    def __init__(self, risk_tolerance: str = 'moderate'):
        """Initialize Risk Manager.
        
        Args:
            risk_tolerance: Risk tolerance level (conservative, moderate, aggressive)
        """
        if risk_tolerance not in self.RISK_TOLERANCE_MULTIPLIERS:
            raise ValueError(
                f"Risk tolerance must be one of: {list(self.RISK_TOLERANCE_MULTIPLIERS.keys())}"
            )
        self.risk_tolerance = risk_tolerance
    
    def assess_portfolio_risk(self, positions: List[Position]) -> RiskAssessment:
        """Calculate overall portfolio risk score.
        
        Args:
            positions: List of portfolio positions
            
        Returns:
            RiskAssessment with overall risk score and identified risks
        """
        if not positions:
            return RiskAssessment(
                portfolio_risk_score=0.0,
                concentration_risks=[],
                correlation_risks=[],
                suggested_position_size=0.0,
                risk_mitigation_actions=[]
            )
        
        # Calculate base risk from position weights
        weights = [p.weight for p in positions]
        weight_variance = np.var(weights)
        
        # Identify concentration risks
        concentration_risks = self.identify_concentration_risk(positions)
        
        # Identify correlation risks
        correlation_risks = self.identify_correlation_risk(positions)
        
        # Calculate overall risk score (0.0 to 1.0)
        # Base risk from weight variance (normalized)
        base_risk = min(weight_variance / 100.0, 0.5)
        
        # Add risk from concentration (0.2 per concentration risk)
        concentration_penalty = min(len(concentration_risks) * 0.2, 0.3)
        
        # Add risk from correlation (0.1 per correlation risk)
        correlation_penalty = min(len(correlation_risks) * 0.1, 0.2)
        
        portfolio_risk_score = min(base_risk + concentration_penalty + correlation_penalty, 1.0)
        
        # Generate risk mitigation actions
        risk_mitigation_actions = self._generate_mitigation_actions(
            concentration_risks,
            correlation_risks,
            portfolio_risk_score
        )
        
        return RiskAssessment(
            portfolio_risk_score=portfolio_risk_score,
            concentration_risks=concentration_risks,
            correlation_risks=correlation_risks,
            suggested_position_size=0.0,  # Not applicable for portfolio assessment
            risk_mitigation_actions=risk_mitigation_actions
        )
    
    def suggest_position_size(
        self,
        symbol: str,
        portfolio_value: float,
        stock_volatility: float,
        risk_tolerance: str = None
    ) -> float:
        """Suggest position size based on volatility and risk tolerance.
        
        Args:
            symbol: Stock ticker symbol
            portfolio_value: Total portfolio value
            stock_volatility: Stock volatility (standard deviation of returns)
            risk_tolerance: Risk tolerance level (uses instance default if None)
            
        Returns:
            Suggested position size as percentage of portfolio (0.0 to 100.0)
        """
        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")
        if stock_volatility < 0:
            raise ValueError("Stock volatility cannot be negative")
        
        # Use provided risk tolerance or instance default
        tolerance = risk_tolerance or self.risk_tolerance
        if tolerance not in self.RISK_TOLERANCE_MULTIPLIERS:
            raise ValueError(
                f"Risk tolerance must be one of: {list(self.RISK_TOLERANCE_MULTIPLIERS.keys())}"
            )
        
        # Base position size (5% for moderate risk)
        base_size = 5.0
        
        # Adjust for risk tolerance
        tolerance_multiplier = self.RISK_TOLERANCE_MULTIPLIERS[tolerance]
        
        # Adjust for volatility (inverse relationship)
        # Low volatility (< 0.2): multiply by 1.5
        # Medium volatility (0.2-0.4): multiply by 1.0
        # High volatility (> 0.4): multiply by 0.5
        if stock_volatility < 0.2:
            volatility_multiplier = 1.5
        elif stock_volatility <= 0.4:
            volatility_multiplier = 1.0
        else:
            volatility_multiplier = 0.5
        
        # Calculate suggested size
        suggested_size = base_size * tolerance_multiplier * volatility_multiplier
        
        # Cap at 20% (concentration threshold)
        suggested_size = min(suggested_size, self.CONCENTRATION_THRESHOLD)
        
        # Ensure non-negative
        suggested_size = max(0.0, suggested_size)
        
        return suggested_size
    
    def identify_concentration_risk(self, positions: List[Position]) -> List[ConcentrationRisk]:
        """Identify positions exceeding concentration thresholds.
        
        Args:
            positions: List of portfolio positions
            
        Returns:
            List of concentration risks
        """
        concentration_risks = []
        
        for position in positions:
            if position.weight > self.CONCENTRATION_THRESHOLD:
                risk = ConcentrationRisk(
                    symbol=position.symbol,
                    weight=position.weight,
                    threshold=self.CONCENTRATION_THRESHOLD,
                    message=f"{position.symbol} represents {position.weight:.1f}% of portfolio, "
                           f"exceeding {self.CONCENTRATION_THRESHOLD:.1f}% concentration threshold"
                )
                concentration_risks.append(risk)
        
        return concentration_risks
    
    def identify_correlation_risk(self, positions: List[Position]) -> List[CorrelationRisk]:
        """Identify correlated positions using correlation matrix.
        
        Note: This is a simplified implementation that uses position weights
        as a proxy for correlation. In a real system, this would calculate
        actual price correlations using historical data.
        
        Args:
            positions: List of portfolio positions
            
        Returns:
            List of correlation risks
        """
        correlation_risks = []
        
        # Need at least 2 positions to have correlation
        if len(positions) < 2:
            return correlation_risks
        
        # Simplified correlation detection:
        # Positions with similar weights are considered potentially correlated
        # In a real system, we would calculate actual price correlations
        
        for i, pos1 in enumerate(positions):
            for pos2 in positions[i+1:]:
                # Calculate weight similarity as proxy for correlation
                weight_diff = abs(pos1.weight - pos2.weight)
                
                # If weights are very similar (within 5%), flag as potential correlation
                if weight_diff < 5.0 and pos1.weight > 10.0:
                    # Estimate correlation based on weight similarity
                    estimated_correlation = 1.0 - (weight_diff / 5.0)
                    
                    if estimated_correlation >= self.HIGH_CORRELATION_THRESHOLD:
                        risk = CorrelationRisk(
                            symbol1=pos1.symbol,
                            symbol2=pos2.symbol,
                            correlation=estimated_correlation,
                            message=f"{pos1.symbol} and {pos2.symbol} may be correlated "
                                   f"(estimated correlation: {estimated_correlation:.2f})"
                        )
                        correlation_risks.append(risk)
        
        return correlation_risks
    
    def _generate_mitigation_actions(
        self,
        concentration_risks: List[ConcentrationRisk],
        correlation_risks: List[CorrelationRisk],
        portfolio_risk_score: float
    ) -> List[str]:
        """Generate risk mitigation recommendations.
        
        Args:
            concentration_risks: List of concentration risks
            correlation_risks: List of correlation risks
            portfolio_risk_score: Overall portfolio risk score
            
        Returns:
            List of recommended mitigation actions
        """
        actions = []
        
        # Address concentration risks
        if concentration_risks:
            for risk in concentration_risks:
                actions.append(
                    f"Reduce {risk.symbol} position from {risk.weight:.1f}% to below "
                    f"{risk.threshold:.1f}% to decrease concentration risk"
                )
        
        # Address correlation risks
        if correlation_risks:
            symbols = set()
            for risk in correlation_risks:
                symbols.add(risk.symbol1)
                symbols.add(risk.symbol2)
            
            if len(symbols) > 0:
                actions.append(
                    f"Consider diversifying away from correlated positions: "
                    f"{', '.join(sorted(symbols))}"
                )
        
        # General risk reduction if score is high
        if portfolio_risk_score > 0.7:
            actions.append(
                "Overall portfolio risk is high. Consider rebalancing to reduce exposure "
                "to individual positions and increase diversification"
            )
        
        # If no specific risks but moderate risk score
        if not actions and portfolio_risk_score > 0.5:
            actions.append(
                "Portfolio risk is moderate. Monitor positions and consider gradual rebalancing"
            )
        
        return actions
