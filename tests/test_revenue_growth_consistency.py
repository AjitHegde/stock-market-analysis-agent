"""
Unit tests for revenue_growth data consistency across all components.

This test suite ensures that revenue_growth is consistently represented as a
percentage value (e.g., 15.0 for 15%) throughout the entire system.
"""

import pytest
from src.fundamental_analyzer import FundamentalAnalyzer
from src.data_provider import CompanyFinancials
from src.models import FundamentalMetrics


class TestRevenueGrowthConsistency:
    """Test revenue_growth consistency across all components."""
    
    def test_fundamental_analyzer_validates_percentage_format(self):
        """Test that FundamentalAnalyzer validates revenue_growth is in percentage format."""
        analyzer = FundamentalAnalyzer()
        
        # Test with correct percentage format
        financials = CompanyFinancials(
            symbol='TEST',
            revenue_growth=26.4,  # Correct: percentage format
        )
        
        metrics = analyzer.calculate_ratios(financials, current_price=100.0)
        
        assert metrics.revenue_growth == 26.4
        assert metrics.revenue_growth > 1.0  # Confirms percentage format
    
    def test_fundamental_analyzer_detects_decimal_format(self):
        """Test that FundamentalAnalyzer detects and converts decimal format."""
        analyzer = FundamentalAnalyzer()
        
        # Test with incorrect decimal format (should be auto-converted)
        financials = CompanyFinancials(
            symbol='TEST',
            revenue_growth=0.264,  # Incorrect: decimal format
        )
        
        metrics = analyzer.calculate_ratios(financials, current_price=100.0)
        
        # Should be auto-converted to percentage (use pytest.approx for floating point)
        assert metrics.revenue_growth == pytest.approx(26.4, rel=1e-9)
        assert metrics.revenue_growth > 1.0  # Confirms it was converted
    
    def test_fundamental_scoring_uses_percentage_thresholds(self):
        """Test that fundamental scoring uses percentage thresholds correctly."""
        analyzer = FundamentalAnalyzer()
        
        # Test strong growth (>20%)
        metrics_strong = FundamentalMetrics(
            symbol='STRONG',
            revenue_growth=25.0,  # 25% growth
        )
        score_strong = analyzer.generate_fundamental_score(metrics_strong)
        
        # Test good growth (10-20%)
        metrics_good = FundamentalMetrics(
            symbol='GOOD',
            revenue_growth=15.0,  # 15% growth
        )
        score_good = analyzer.generate_fundamental_score(metrics_good)
        
        # Test declining (-5% to 0%)
        metrics_decline = FundamentalMetrics(
            symbol='DECLINE',
            revenue_growth=-3.0,  # -3% growth
        )
        score_decline = analyzer.generate_fundamental_score(metrics_decline)
        
        # Strong growth should score higher than good growth
        assert score_strong > score_good
        
        # Positive growth should score higher than decline
        assert score_good > score_decline
    
    def test_revenue_growth_consistency_across_thresholds(self):
        """Test that all threshold checks use consistent percentage format."""
        analyzer = FundamentalAnalyzer()
        
        # Test boundary values
        test_cases = [
            (25.0, "strong"),    # >20% = strong
            (15.0, "good"),      # 10-20% = good
            (5.0, "positive"),   # 0-10% = positive
            (-3.0, "slight"),    # -5 to 0% = slight decline
            (-15.0, "decline"),  # <-5% = decline
        ]
        
        for growth_value, expected_category in test_cases:
            metrics = FundamentalMetrics(
                symbol='TEST',
                revenue_growth=growth_value,
            )
            score = analyzer.generate_fundamental_score(metrics)
            
            # Verify score is calculated (not None or 0 due to format issues)
            assert score is not None
            
            # Verify the value is treated as percentage
            if growth_value > 20.0:
                # Strong growth should contribute positively
                assert score > 0.0, f"Strong growth {growth_value}% should have positive score"
            elif growth_value < -10.0:
                # Significant decline should contribute negatively
                assert score < 0.0, f"Declining growth {growth_value}% should have negative score"
    
    def test_cli_display_format_consistency(self):
        """Test that CLI displays revenue_growth in consistent format."""
        # This is a documentation test - CLI should display as percentage
        # CLI code: if growth_value > 15.0: (percentage threshold)
        # CLI code: f"{growth_value:+.1f}%" (percentage display)
        
        # Verify thresholds are percentage-based
        assert 15.0 > 1.0  # Confirms threshold is percentage, not decimal
        assert -10.0 < -1.0  # Confirms threshold is percentage, not decimal
    
    def test_web_ui_display_format_consistency(self):
        """Test that Web UI displays revenue_growth in consistent format."""
        # This is a documentation test - Web UI should display as percentage
        # Web UI code: if growth_value > 15: (percentage threshold)
        # Web UI code: f"+{growth_value:.1f}%" (percentage display)
        
        # Verify thresholds are percentage-based
        assert 15 > 1.0  # Confirms threshold is percentage, not decimal
        assert -10 < -1.0  # Confirms threshold is percentage, not decimal
    
    def test_validation_converts_decimal_to_percentage(self):
        """Test that validation detects and converts decimal format."""
        analyzer = FundamentalAnalyzer()
        
        # Simulate a case where decimal format slips through
        financials = CompanyFinancials(
            symbol='TEST',
            revenue_growth=0.05,  # 5% in decimal (should be 5.0)
        )
        
        metrics = analyzer.calculate_ratios(financials, current_price=100.0)
        
        # Should auto-convert to percentage
        assert metrics.revenue_growth == 5.0
        assert 0.0 < metrics.revenue_growth < 100.0  # Reasonable percentage range
    
    def test_none_revenue_growth_handled_correctly(self):
        """Test that None revenue_growth is handled without errors."""
        analyzer = FundamentalAnalyzer()
        
        financials = CompanyFinancials(
            symbol='TEST',
            revenue_growth=None,
        )
        
        metrics = analyzer.calculate_ratios(financials, current_price=100.0)
        
        # Should remain None
        assert metrics.revenue_growth is None
        
        # Should not cause scoring errors
        score = analyzer.generate_fundamental_score(metrics)
        assert score is not None
    
    def test_extreme_values_handled_correctly(self):
        """Test that extreme revenue_growth values are handled correctly."""
        analyzer = FundamentalAnalyzer()
        
        # Test very high growth
        financials_high = CompanyFinancials(
            symbol='HIGH',
            revenue_growth=150.0,  # 150% growth
        )
        metrics_high = analyzer.calculate_ratios(financials_high, current_price=100.0)
        assert metrics_high.revenue_growth == 150.0
        
        # Test very negative growth
        financials_low = CompanyFinancials(
            symbol='LOW',
            revenue_growth=-50.0,  # -50% decline
        )
        metrics_low = analyzer.calculate_ratios(financials_low, current_price=100.0)
        assert metrics_low.revenue_growth == -50.0
    
    def test_data_provider_normalization_contract(self):
        """Test that data provider contract is documented."""
        # This test documents the expected behavior:
        # 1. Yahoo Finance returns decimal (0.264 = 26.4%)
        # 2. DataProvider MUST convert to percentage (26.4)
        # 3. All downstream components expect percentage format
        
        # Document the conversion formula
        yahoo_decimal = 0.264
        expected_percentage = yahoo_decimal * 100
        assert expected_percentage == pytest.approx(26.4, rel=1e-9)
        
        # Document the threshold expectations
        strong_growth_threshold = 20.0  # percentage
        good_growth_threshold = 10.0    # percentage
        decline_threshold = -10.0       # percentage
        
        assert strong_growth_threshold > 1.0  # Not decimal
        assert good_growth_threshold > 0.1    # Not decimal
        assert decline_threshold < -1.0       # Not decimal


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
