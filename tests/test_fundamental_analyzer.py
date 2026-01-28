"""Unit tests for Fundamental Analyzer."""

import pytest
from src.fundamental_analyzer import FundamentalAnalyzer
from src.data_provider import CompanyFinancials
from src.models import FundamentalMetrics


class TestFundamentalAnalyzer:
    """Test suite for FundamentalAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = FundamentalAnalyzer()
    
    # Test calculate_ratios method
    
    def test_calculate_ratios_with_complete_data(self):
        """Test ratio calculation with all data available."""
        financials = CompanyFinancials(
            symbol="AAPL",
            eps=6.0,
            book_value=4.0,
            debt_to_equity=1.5,
            revenue_growth=15.0
        )
        current_price = 150.0
        
        metrics = self.analyzer.calculate_ratios(financials, current_price)
        
        assert metrics.symbol == "AAPL"
        assert metrics.pe_ratio == 25.0  # 150 / 6
        assert metrics.pb_ratio == 37.5  # 150 / 4
        assert metrics.debt_to_equity == 1.5
        assert metrics.eps == 6.0
        assert metrics.revenue_growth == 15.0
    
    def test_calculate_ratios_with_precalculated_pe(self):
        """Test that pre-calculated P/E ratio is used when EPS is missing."""
        financials = CompanyFinancials(
            symbol="MSFT",
            pe_ratio=30.0,
            eps=None,
            book_value=5.0,
            debt_to_equity=0.5
        )
        current_price = 300.0
        
        metrics = self.analyzer.calculate_ratios(financials, current_price)
        
        assert metrics.pe_ratio == 30.0  # Uses pre-calculated value
        assert metrics.pb_ratio == 60.0  # 300 / 5
    
    def test_calculate_ratios_with_precalculated_pb(self):
        """Test that pre-calculated P/B ratio is used when book value is missing."""
        financials = CompanyFinancials(
            symbol="GOOGL",
            eps=10.0,
            pb_ratio=5.0,
            book_value=None,
            debt_to_equity=0.3
        )
        current_price = 2000.0
        
        metrics = self.analyzer.calculate_ratios(financials, current_price)
        
        assert metrics.pe_ratio == 200.0  # 2000 / 10
        assert metrics.pb_ratio == 5.0  # Uses pre-calculated value
    
    def test_calculate_ratios_with_missing_eps(self):
        """Test ratio calculation when EPS is missing."""
        financials = CompanyFinancials(
            symbol="TSLA",
            eps=None,
            book_value=10.0,
            debt_to_equity=2.0
        )
        current_price = 200.0
        
        metrics = self.analyzer.calculate_ratios(financials, current_price)
        
        assert metrics.pe_ratio is None  # Cannot calculate without EPS
        assert metrics.pb_ratio == 20.0  # 200 / 10
        assert metrics.debt_to_equity == 2.0
    
    def test_calculate_ratios_with_zero_eps(self):
        """Test ratio calculation when EPS is zero (no P/E ratio)."""
        financials = CompanyFinancials(
            symbol="LOSS",
            eps=0.0,
            book_value=5.0,
            debt_to_equity=1.0
        )
        current_price = 50.0
        
        metrics = self.analyzer.calculate_ratios(financials, current_price)
        
        assert metrics.pe_ratio is None  # Cannot divide by zero
        assert metrics.pb_ratio == 10.0
    
    def test_calculate_ratios_with_negative_eps(self):
        """Test ratio calculation when EPS is negative (company losing money)."""
        financials = CompanyFinancials(
            symbol="LOSS",
            eps=-2.0,
            book_value=5.0,
            debt_to_equity=3.0
        )
        current_price = 50.0
        
        metrics = self.analyzer.calculate_ratios(financials, current_price)
        
        assert metrics.pe_ratio is None  # P/E not meaningful for negative earnings
        assert metrics.pb_ratio == 10.0
        assert metrics.eps == -2.0  # Preserved for reference
    
    def test_calculate_ratios_with_missing_book_value(self):
        """Test ratio calculation when book value is missing."""
        financials = CompanyFinancials(
            symbol="AMZN",
            eps=5.0,
            book_value=None,
            debt_to_equity=0.8
        )
        current_price = 100.0
        
        metrics = self.analyzer.calculate_ratios(financials, current_price)
        
        assert metrics.pe_ratio == 20.0  # 100 / 5
        assert metrics.pb_ratio is None  # Cannot calculate without book value
    
    def test_calculate_ratios_with_zero_book_value(self):
        """Test ratio calculation when book value is zero."""
        financials = CompanyFinancials(
            symbol="ZERO",
            eps=3.0,
            book_value=0.0,
            debt_to_equity=0.5
        )
        current_price = 60.0
        
        metrics = self.analyzer.calculate_ratios(financials, current_price)
        
        assert metrics.pe_ratio == 20.0
        assert metrics.pb_ratio is None  # Cannot divide by zero
    
    def test_calculate_ratios_with_all_missing_data(self):
        """Test ratio calculation when all optional data is missing."""
        financials = CompanyFinancials(
            symbol="EMPTY",
            eps=None,
            book_value=None,
            debt_to_equity=None,
            revenue_growth=None
        )
        current_price = 100.0
        
        metrics = self.analyzer.calculate_ratios(financials, current_price)
        
        assert metrics.symbol == "EMPTY"
        assert metrics.pe_ratio is None
        assert metrics.pb_ratio is None
        assert metrics.debt_to_equity is None
        assert metrics.eps is None
        assert metrics.revenue_growth is None
    
    # Test compare_to_industry method
    
    def test_compare_to_industry_technology(self):
        """Test industry comparison for technology sector."""
        metrics = FundamentalMetrics(
            symbol="AAPL",
            pe_ratio=25.0,
            fundamental_score=0.0
        )
        
        updated_metrics = self.analyzer.compare_to_industry(metrics, "Technology")
        
        assert updated_metrics.industry_avg_pe == 25.0
    
    def test_compare_to_industry_healthcare(self):
        """Test industry comparison for healthcare sector."""
        metrics = FundamentalMetrics(
            symbol="JNJ",
            pe_ratio=18.0,
            fundamental_score=0.0
        )
        
        updated_metrics = self.analyzer.compare_to_industry(metrics, "Healthcare")
        
        assert updated_metrics.industry_avg_pe == 20.0
    
    def test_compare_to_industry_finance(self):
        """Test industry comparison for finance sector."""
        metrics = FundamentalMetrics(
            symbol="JPM",
            pe_ratio=12.0,
            fundamental_score=0.0
        )
        
        updated_metrics = self.analyzer.compare_to_industry(metrics, "Finance")
        
        assert updated_metrics.industry_avg_pe == 15.0
    
    def test_compare_to_industry_unknown_sector(self):
        """Test industry comparison for unknown sector (uses default)."""
        metrics = FundamentalMetrics(
            symbol="XYZ",
            pe_ratio=20.0,
            fundamental_score=0.0
        )
        
        updated_metrics = self.analyzer.compare_to_industry(metrics, "UnknownSector")
        
        assert updated_metrics.industry_avg_pe == 18.0  # Default market average
    
    # Test generate_fundamental_score method
    
    def test_generate_fundamental_score_excellent_fundamentals(self):
        """Test score generation for company with excellent fundamentals."""
        metrics = FundamentalMetrics(
            symbol="STRONG",
            pe_ratio=14.0,  # Undervalued (industry avg 20.0)
            pb_ratio=0.8,   # Below book value
            debt_to_equity=0.2,  # Low debt
            revenue_growth=25.0,  # Strong growth
            industry_avg_pe=20.0
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert 0.7 <= score <= 1.0  # Should be strongly positive
    
    def test_generate_fundamental_score_poor_fundamentals(self):
        """Test score generation for company with poor fundamentals."""
        metrics = FundamentalMetrics(
            symbol="WEAK",
            pe_ratio=30.0,  # Overvalued (industry avg 20.0)
            pb_ratio=6.0,   # High valuation
            debt_to_equity=2.5,  # High debt
            revenue_growth=-10.0,  # Declining revenue
            industry_avg_pe=20.0
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert -1.0 <= score <= -0.5  # Should be strongly negative
    
    def test_generate_fundamental_score_mixed_fundamentals(self):
        """Test score generation for company with mixed fundamentals."""
        metrics = FundamentalMetrics(
            symbol="MIXED",
            pe_ratio=20.0,  # Fair value (industry avg 20.0)
            pb_ratio=2.5,   # Moderate valuation
            debt_to_equity=0.9,  # Moderate debt
            revenue_growth=5.0,  # Modest growth
            industry_avg_pe=20.0
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert -0.3 <= score <= 0.3  # Should be near neutral
    
    def test_generate_fundamental_score_undervalued_pe(self):
        """Test score with significantly undervalued P/E ratio."""
        metrics = FundamentalMetrics(
            symbol="UNDER",
            pe_ratio=10.0,  # 50% of industry average
            industry_avg_pe=20.0
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert score > 0.0  # Should be positive
    
    def test_generate_fundamental_score_overvalued_pe(self):
        """Test score with significantly overvalued P/E ratio."""
        metrics = FundamentalMetrics(
            symbol="OVER",
            pe_ratio=30.0,  # 150% of industry average
            industry_avg_pe=20.0
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert score < 0.0  # Should be negative
    
    def test_generate_fundamental_score_low_pb_ratio(self):
        """Test score with low P/B ratio (undervalued)."""
        metrics = FundamentalMetrics(
            symbol="VALUE",
            pb_ratio=0.7  # Below book value
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert score > 0.0  # Should be positive
    
    def test_generate_fundamental_score_high_pb_ratio(self):
        """Test score with high P/B ratio (overvalued)."""
        metrics = FundamentalMetrics(
            symbol="EXPENSIVE",
            pb_ratio=6.0  # Very high valuation
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert score < 0.0  # Should be negative
    
    def test_generate_fundamental_score_low_debt(self):
        """Test score with low debt-to-equity ratio."""
        metrics = FundamentalMetrics(
            symbol="SAFE",
            debt_to_equity=0.1  # Very low debt
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert score > 0.0  # Should be positive
    
    def test_generate_fundamental_score_high_debt(self):
        """Test score with high debt-to-equity ratio."""
        metrics = FundamentalMetrics(
            symbol="RISKY",
            debt_to_equity=3.0  # Very high debt
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert score < 0.0  # Should be negative
    
    def test_generate_fundamental_score_strong_growth(self):
        """Test score with strong revenue growth."""
        metrics = FundamentalMetrics(
            symbol="GROWTH",
            revenue_growth=30.0  # Strong growth
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert score > 0.0  # Should be positive
    
    def test_generate_fundamental_score_declining_revenue(self):
        """Test score with declining revenue."""
        metrics = FundamentalMetrics(
            symbol="DECLINE",
            revenue_growth=-15.0  # Significant decline
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert score < 0.0  # Should be negative
    
    def test_generate_fundamental_score_no_metrics(self):
        """Test score generation when no metrics are available."""
        metrics = FundamentalMetrics(
            symbol="EMPTY",
            pe_ratio=None,
            pb_ratio=None,
            debt_to_equity=None,
            revenue_growth=None
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert score == 0.0  # Should return neutral score
    
    def test_generate_fundamental_score_partial_metrics(self):
        """Test score generation with only some metrics available."""
        metrics = FundamentalMetrics(
            symbol="PARTIAL",
            pe_ratio=15.0,
            pb_ratio=None,  # Missing
            debt_to_equity=0.5,
            revenue_growth=None,  # Missing
            industry_avg_pe=20.0
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        # Should calculate based on available metrics
        assert -1.0 <= score <= 1.0
        assert score > 0.0  # Should be positive (good P/E, low debt)
    
    def test_generate_fundamental_score_range_validation(self):
        """Test that score is always within valid range."""
        # Test with extreme values
        metrics = FundamentalMetrics(
            symbol="EXTREME",
            pe_ratio=1.0,  # Extremely undervalued
            pb_ratio=0.1,  # Extremely undervalued
            debt_to_equity=0.01,  # Almost no debt
            revenue_growth=100.0,  # Extreme growth
            industry_avg_pe=50.0
        )
        
        score = self.analyzer.generate_fundamental_score(metrics)
        
        assert -1.0 <= score <= 1.0  # Must be within valid range
    
    # Test analyze method (integration)
    
    def test_analyze_complete_workflow(self):
        """Test complete analysis workflow."""
        financials = CompanyFinancials(
            symbol="AAPL",
            eps=6.0,
            book_value=4.0,
            debt_to_equity=1.5,
            revenue_growth=15.0
        )
        current_price = 150.0
        
        metrics = self.analyzer.analyze(financials, current_price, "Technology")
        
        # Verify all steps completed
        assert metrics.symbol == "AAPL"
        assert metrics.pe_ratio == 25.0
        assert metrics.pb_ratio == 37.5
        assert metrics.debt_to_equity == 1.5
        assert metrics.industry_avg_pe == 25.0
        assert -1.0 <= metrics.fundamental_score <= 1.0
    
    def test_analyze_with_missing_data(self):
        """Test analysis workflow with missing data."""
        financials = CompanyFinancials(
            symbol="PARTIAL",
            eps=None,
            book_value=5.0,
            debt_to_equity=None,
            revenue_growth=10.0
        )
        current_price = 100.0
        
        metrics = self.analyzer.analyze(financials, current_price, "Healthcare")
        
        # Should handle missing data gracefully
        assert metrics.symbol == "PARTIAL"
        assert metrics.pe_ratio is None
        assert metrics.pb_ratio == 20.0
        assert metrics.debt_to_equity is None
        assert metrics.industry_avg_pe == 20.0
        assert -1.0 <= metrics.fundamental_score <= 1.0
    
    def test_analyze_different_industries(self):
        """Test analysis with different industry sectors."""
        financials = CompanyFinancials(
            symbol="TEST",
            eps=5.0,
            book_value=10.0,
            debt_to_equity=0.5,
            revenue_growth=8.0
        )
        current_price = 100.0
        
        # Test multiple industries
        tech_metrics = self.analyzer.analyze(financials, current_price, "Technology")
        finance_metrics = self.analyzer.analyze(financials, current_price, "Finance")
        
        assert tech_metrics.industry_avg_pe == 25.0
        assert finance_metrics.industry_avg_pe == 15.0
        # Scores should differ based on industry comparison
        assert tech_metrics.fundamental_score != finance_metrics.fundamental_score
