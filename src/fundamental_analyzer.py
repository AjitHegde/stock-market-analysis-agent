"""Fundamental Analyzer for Stock Market AI Agent.

This module provides fundamental analysis capabilities including:
- Calculation of financial ratios (P/E, P/B, debt-to-equity)
- Comparison against industry averages
- Generation of fundamental scores
"""

import logging
from typing import Optional
from src.models import FundamentalMetrics
from src.data_provider import CompanyFinancials

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """Analyzes company fundamentals and generates fundamental scores."""
    
    def __init__(self):
        """Initialize the fundamental analyzer."""
        pass
    
    def calculate_ratios(self, financials: CompanyFinancials, current_price: float) -> FundamentalMetrics:
        """Calculate fundamental ratios from company financial data.
        
        This method calculates P/E ratio, P/B ratio, and debt-to-equity ratio
        from the provided financial data. If any required data is missing,
        the corresponding ratio will be None.
        
        Args:
            financials: Company financial data
            current_price: Current stock price
            
        Returns:
            FundamentalMetrics object with calculated ratios
            
        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.6
        """
        # Calculate P/E ratio (Price-to-Earnings)
        # P/E = Current Price / Earnings Per Share
        pe_ratio = None
        if financials.eps is not None and financials.eps > 0:
            pe_ratio = current_price / financials.eps
        elif financials.pe_ratio is not None:
            # Use pre-calculated P/E if available
            pe_ratio = financials.pe_ratio
        
        # Calculate P/B ratio (Price-to-Book)
        # P/B = Current Price / Book Value Per Share
        pb_ratio = None
        if financials.book_value is not None and financials.book_value > 0:
            pb_ratio = current_price / financials.book_value
        elif financials.pb_ratio is not None:
            # Use pre-calculated P/B if available
            pb_ratio = financials.pb_ratio
        
        # Debt-to-Equity ratio is typically provided directly
        debt_to_equity = financials.debt_to_equity
        
        # Extract EPS and revenue growth
        eps = financials.eps
        revenue_growth = financials.revenue_growth
        
        # Validate revenue_growth format (should be percentage, not decimal)
        if revenue_growth is not None:
            # If value is between -1 and 1, it's likely a decimal that needs conversion
            if -1.0 <= revenue_growth <= 1.0:
                logger.error(
                    f"Revenue growth for {financials.symbol} appears to be in decimal format "
                    f"({revenue_growth:.4f}). Expected percentage format (e.g., 15.0 for 15%). "
                    f"This indicates a data normalization issue in the data provider."
                )
                # Convert to percentage for consistency
                revenue_growth = revenue_growth * 100
                logger.warning(f"Auto-converted revenue_growth to {revenue_growth:.2f}%")
        
        return FundamentalMetrics(
            symbol=financials.symbol,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            debt_to_equity=debt_to_equity,
            eps=eps,
            revenue_growth=revenue_growth,
            industry_avg_pe=None,  # Will be set by compare_to_industry
            fundamental_score=0.0  # Will be calculated by generate_fundamental_score
        )
    
    def compare_to_industry(
        self,
        metrics: FundamentalMetrics,
        industry: str
    ) -> FundamentalMetrics:
        """Compare fundamental metrics against industry averages.
        
        This method fetches industry average metrics and adds them to the
        FundamentalMetrics object for comparison. Currently implements a
        simplified version with hardcoded industry averages.
        
        Args:
            metrics: Fundamental metrics to compare
            industry: Industry sector (e.g., "Technology", "Healthcare")
            
        Returns:
            Updated FundamentalMetrics with industry comparison data
            
        Validates: Requirements 3.5
        """
        # Industry average P/E ratios (simplified for MVP)
        # In a production system, this would fetch from a financial data API
        industry_averages = {
            "Technology": 25.0,
            "Healthcare": 20.0,
            "Finance": 15.0,
            "Consumer": 18.0,
            "Energy": 12.0,
            "Utilities": 16.0,
            "Real Estate": 22.0,
            "Materials": 14.0,
            "Industrials": 17.0,
            "Telecommunications": 13.0,
        }
        
        # Default to a general market average if industry not found
        industry_avg_pe = industry_averages.get(industry, 18.0)
        
        # Update the metrics with industry average
        metrics.industry_avg_pe = industry_avg_pe
        
        return metrics
    
    def generate_fundamental_score(self, metrics: FundamentalMetrics) -> float:
        """Generate an overall fundamental score from metrics.
        
        The fundamental score is calculated by evaluating multiple metrics:
        - P/E ratio compared to industry average (lower is better)
        - P/B ratio (lower is better, indicates undervaluation)
        - Debt-to-Equity ratio (lower is better, indicates less leverage)
        - Revenue growth (higher is better)
        
        Each metric contributes to the score, which ranges from -1.0 (very poor
        fundamentals) to +1.0 (very strong fundamentals).
        
        Args:
            metrics: Fundamental metrics to score
            
        Returns:
            Fundamental score between -1.0 and +1.0
            
        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        score_components = []
        weights = []
        
        # 1. P/E Ratio Score (weight: 0.35)
        # Compare to industry average
        if metrics.pe_ratio is not None and metrics.industry_avg_pe is not None:
            # Ratio of company P/E to industry average
            # < 1.0 means undervalued (good), > 1.0 means overvalued (bad)
            pe_ratio_normalized = metrics.pe_ratio / metrics.industry_avg_pe
            
            if pe_ratio_normalized < 0.7:
                # Significantly undervalued
                pe_score = 1.0
            elif pe_ratio_normalized < 0.9:
                # Moderately undervalued
                pe_score = 0.5
            elif pe_ratio_normalized < 1.1:
                # Fairly valued
                pe_score = 0.0
            elif pe_ratio_normalized < 1.3:
                # Moderately overvalued
                pe_score = -0.5
            else:
                # Significantly overvalued
                pe_score = -1.0
            
            score_components.append(pe_score)
            weights.append(0.35)
        
        # 2. P/B Ratio Score (weight: 0.25)
        # Lower P/B indicates better value
        if metrics.pb_ratio is not None:
            if metrics.pb_ratio < 1.0:
                # Trading below book value (undervalued)
                pb_score = 1.0
            elif metrics.pb_ratio < 2.0:
                # Reasonable valuation
                pb_score = 0.5
            elif metrics.pb_ratio < 3.0:
                # Moderate valuation
                pb_score = 0.0
            elif metrics.pb_ratio < 5.0:
                # High valuation
                pb_score = -0.5
            else:
                # Very high valuation
                pb_score = -1.0
            
            score_components.append(pb_score)
            weights.append(0.25)
        
        # 3. Debt-to-Equity Score (weight: 0.20)
        # Lower debt-to-equity is better (less financial risk)
        if metrics.debt_to_equity is not None:
            if metrics.debt_to_equity < 0.3:
                # Very low debt (excellent)
                de_score = 1.0
            elif metrics.debt_to_equity < 0.5:
                # Low debt (good)
                de_score = 0.5
            elif metrics.debt_to_equity < 1.0:
                # Moderate debt (neutral)
                de_score = 0.0
            elif metrics.debt_to_equity < 2.0:
                # High debt (concerning)
                de_score = -0.5
            else:
                # Very high debt (risky)
                de_score = -1.0
            
            score_components.append(de_score)
            weights.append(0.20)
        
        # 4. Revenue Growth Score (weight: 0.20)
        # Higher revenue growth is better
        if metrics.revenue_growth is not None:
            # Revenue growth is typically expressed as a percentage
            if metrics.revenue_growth > 20.0:
                # Strong growth
                growth_score = 1.0
            elif metrics.revenue_growth > 10.0:
                # Good growth
                growth_score = 0.5
            elif metrics.revenue_growth > 0.0:
                # Positive growth
                growth_score = 0.0
            elif metrics.revenue_growth > -5.0:
                # Slight decline
                growth_score = -0.5
            else:
                # Significant decline
                growth_score = -1.0
            
            score_components.append(growth_score)
            weights.append(0.20)
        
        # Calculate weighted average score
        if not score_components:
            # No metrics available, return neutral score
            return 0.0
        
        total_weight = sum(weights)
        weighted_sum = sum(score * weight for score, weight in zip(score_components, weights))
        fundamental_score = weighted_sum / total_weight
        
        # Ensure score is within valid range
        fundamental_score = max(-1.0, min(1.0, fundamental_score))
        
        return fundamental_score
    
    def analyze(
        self,
        financials: CompanyFinancials,
        current_price: float,
        industry: str = "Technology"
    ) -> FundamentalMetrics:
        """Perform complete fundamental analysis.
        
        This is a convenience method that combines all analysis steps:
        1. Calculate financial ratios
        2. Compare to industry averages
        3. Generate fundamental score
        
        Args:
            financials: Company financial data
            current_price: Current stock price
            industry: Industry sector for comparison
            
        Returns:
            Complete FundamentalMetrics with all calculations
        """
        # Calculate ratios
        metrics = self.calculate_ratios(financials, current_price)
        
        # Compare to industry
        metrics = self.compare_to_industry(metrics, industry)
        
        # Generate score
        fundamental_score = self.generate_fundamental_score(metrics)
        metrics.fundamental_score = fundamental_score
        
        # Calculate direction and strength
        if fundamental_score > 0.2:
            direction = "bullish"
            strength = abs(fundamental_score)
        elif fundamental_score < -0.2:
            direction = "bearish"
            strength = abs(fundamental_score)
        else:
            direction = "neutral"
            strength = abs(fundamental_score) * 0.3  # Reduced strength for neutral
        
        # Calculate confidence based on data availability
        missing_metrics = sum([
            metrics.pe_ratio is None,
            metrics.pb_ratio is None,
            metrics.revenue_growth is None
        ])
        if missing_metrics == 0:
            confidence = 0.9  # All metrics available
        elif missing_metrics >= 2:
            confidence = 0.5  # Many metrics missing
        else:
            confidence = 0.7  # Default moderate confidence
        
        metrics.direction = direction
        metrics.strength = strength
        metrics.confidence = confidence
        
        return metrics
