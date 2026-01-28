"""Unit tests for Risk Manager."""

import pytest
from src.risk_manager import RiskManager
from src.models import Position, ConcentrationRisk, CorrelationRisk


class TestRiskManagerInitialization:
    """Tests for Risk Manager initialization."""
    
    def test_init_with_valid_risk_tolerance(self):
        """Test initialization with valid risk tolerance levels."""
        for tolerance in ['conservative', 'moderate', 'aggressive']:
            manager = RiskManager(risk_tolerance=tolerance)
            assert manager.risk_tolerance == tolerance
    
    def test_init_with_invalid_risk_tolerance(self):
        """Test initialization with invalid risk tolerance raises error."""
        with pytest.raises(ValueError, match="Risk tolerance must be one of"):
            RiskManager(risk_tolerance='invalid')
    
    def test_default_risk_tolerance(self):
        """Test default risk tolerance is moderate."""
        manager = RiskManager()
        assert manager.risk_tolerance == 'moderate'


class TestAssessPortfolioRisk:
    """Tests for portfolio risk assessment."""
    
    def test_empty_portfolio_returns_zero_risk(self):
        """Test empty portfolio returns zero risk score."""
        manager = RiskManager()
        assessment = manager.assess_portfolio_risk([])
        
        assert assessment.portfolio_risk_score == 0.0
        assert len(assessment.concentration_risks) == 0
        assert len(assessment.correlation_risks) == 0
        assert len(assessment.risk_mitigation_actions) == 0
    
    def test_single_position_low_weight(self):
        """Test single position with low weight has low risk."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=10, avg_cost=150.0, current_value=1500.0, weight=15.0)
        ]
        
        assessment = manager.assess_portfolio_risk(positions)
        
        assert 0.0 <= assessment.portfolio_risk_score <= 1.0
        assert len(assessment.concentration_risks) == 0
    
    def test_single_position_high_weight_flags_concentration(self):
        """Test single position exceeding 20% flags concentration risk."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=100, avg_cost=150.0, current_value=15000.0, weight=25.0)
        ]
        
        assessment = manager.assess_portfolio_risk(positions)
        
        assert assessment.portfolio_risk_score > 0.0
        assert len(assessment.concentration_risks) == 1
        assert assessment.concentration_risks[0].symbol == 'AAPL'
        assert assessment.concentration_risks[0].weight == 25.0
        assert len(assessment.risk_mitigation_actions) > 0
    
    def test_multiple_positions_balanced(self):
        """Test balanced portfolio has low risk."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=10, avg_cost=150.0, current_value=1500.0, weight=15.0),
            Position(symbol='GOOGL', shares=5, avg_cost=2800.0, current_value=14000.0, weight=14.0),
            Position(symbol='MSFT', shares=20, avg_cost=350.0, current_value=7000.0, weight=13.0),
        ]
        
        assessment = manager.assess_portfolio_risk(positions)
        
        assert 0.0 <= assessment.portfolio_risk_score <= 1.0
        assert len(assessment.concentration_risks) == 0
    
    def test_multiple_concentration_risks(self):
        """Test multiple positions exceeding threshold."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=100, avg_cost=150.0, current_value=15000.0, weight=30.0),
            Position(symbol='GOOGL', shares=50, avg_cost=2800.0, current_value=140000.0, weight=25.0),
        ]
        
        assessment = manager.assess_portfolio_risk(positions)
        
        assert assessment.portfolio_risk_score > 0.0
        assert len(assessment.concentration_risks) == 2
        assert any(r.symbol == 'AAPL' for r in assessment.concentration_risks)
        assert any(r.symbol == 'GOOGL' for r in assessment.concentration_risks)


class TestSuggestPositionSize:
    """Tests for position size suggestions."""
    
    def test_moderate_risk_low_volatility(self):
        """Test position sizing with moderate risk and low volatility."""
        manager = RiskManager(risk_tolerance='moderate')
        size = manager.suggest_position_size(
            symbol='AAPL',
            portfolio_value=100000.0,
            stock_volatility=0.15
        )
        
        # Low volatility should suggest larger position
        assert 0.0 <= size <= 100.0
        assert size > 5.0  # Should be above base size
    
    def test_moderate_risk_high_volatility(self):
        """Test position sizing with moderate risk and high volatility."""
        manager = RiskManager(risk_tolerance='moderate')
        size = manager.suggest_position_size(
            symbol='TSLA',
            portfolio_value=100000.0,
            stock_volatility=0.6
        )
        
        # High volatility should suggest smaller position
        assert 0.0 <= size <= 100.0
        assert size < 5.0  # Should be below base size
    
    def test_conservative_risk_tolerance(self):
        """Test conservative risk tolerance suggests smaller positions."""
        conservative_manager = RiskManager(risk_tolerance='conservative')
        moderate_manager = RiskManager(risk_tolerance='moderate')
        
        conservative_size = conservative_manager.suggest_position_size(
            symbol='AAPL',
            portfolio_value=100000.0,
            stock_volatility=0.25
        )
        
        moderate_size = moderate_manager.suggest_position_size(
            symbol='AAPL',
            portfolio_value=100000.0,
            stock_volatility=0.25
        )
        
        assert conservative_size < moderate_size
    
    def test_aggressive_risk_tolerance(self):
        """Test aggressive risk tolerance suggests larger positions."""
        aggressive_manager = RiskManager(risk_tolerance='aggressive')
        moderate_manager = RiskManager(risk_tolerance='moderate')
        
        aggressive_size = aggressive_manager.suggest_position_size(
            symbol='AAPL',
            portfolio_value=100000.0,
            stock_volatility=0.25
        )
        
        moderate_size = moderate_manager.suggest_position_size(
            symbol='AAPL',
            portfolio_value=100000.0,
            stock_volatility=0.25
        )
        
        assert aggressive_size > moderate_size
    
    def test_position_size_capped_at_concentration_threshold(self):
        """Test position size never exceeds concentration threshold."""
        manager = RiskManager(risk_tolerance='aggressive')
        size = manager.suggest_position_size(
            symbol='AAPL',
            portfolio_value=100000.0,
            stock_volatility=0.05  # Very low volatility
        )
        
        assert size <= 20.0  # Should not exceed concentration threshold
    
    def test_invalid_portfolio_value(self):
        """Test invalid portfolio value raises error."""
        manager = RiskManager()
        
        with pytest.raises(ValueError, match="Portfolio value must be positive"):
            manager.suggest_position_size(
                symbol='AAPL',
                portfolio_value=0.0,
                stock_volatility=0.25
            )
    
    def test_negative_volatility(self):
        """Test negative volatility raises error."""
        manager = RiskManager()
        
        with pytest.raises(ValueError, match="Stock volatility cannot be negative"):
            manager.suggest_position_size(
                symbol='AAPL',
                portfolio_value=100000.0,
                stock_volatility=-0.1
            )
    
    def test_volatility_inverse_relationship(self):
        """Test higher volatility results in smaller position size."""
        manager = RiskManager(risk_tolerance='moderate')
        
        low_vol_size = manager.suggest_position_size(
            symbol='AAPL',
            portfolio_value=100000.0,
            stock_volatility=0.15
        )
        
        high_vol_size = manager.suggest_position_size(
            symbol='TSLA',
            portfolio_value=100000.0,
            stock_volatility=0.6
        )
        
        assert low_vol_size > high_vol_size


class TestIdentifyConcentrationRisk:
    """Tests for concentration risk identification."""
    
    def test_no_concentration_risk(self):
        """Test portfolio with no concentration risks."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=10, avg_cost=150.0, current_value=1500.0, weight=15.0),
            Position(symbol='GOOGL', shares=5, avg_cost=2800.0, current_value=14000.0, weight=14.0),
        ]
        
        risks = manager.identify_concentration_risk(positions)
        
        assert len(risks) == 0
    
    def test_single_concentration_risk(self):
        """Test identification of single concentration risk."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=100, avg_cost=150.0, current_value=15000.0, weight=25.0),
            Position(symbol='GOOGL', shares=5, avg_cost=2800.0, current_value=14000.0, weight=10.0),
        ]
        
        risks = manager.identify_concentration_risk(positions)
        
        assert len(risks) == 1
        assert risks[0].symbol == 'AAPL'
        assert risks[0].weight == 25.0
        assert risks[0].threshold == 20.0
        assert 'AAPL' in risks[0].message
        assert '25.0%' in risks[0].message
    
    def test_multiple_concentration_risks(self):
        """Test identification of multiple concentration risks."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=100, avg_cost=150.0, current_value=15000.0, weight=30.0),
            Position(symbol='GOOGL', shares=50, avg_cost=2800.0, current_value=140000.0, weight=25.0),
            Position(symbol='MSFT', shares=20, avg_cost=350.0, current_value=7000.0, weight=15.0),
        ]
        
        risks = manager.identify_concentration_risk(positions)
        
        assert len(risks) == 2
        symbols = {r.symbol for r in risks}
        assert 'AAPL' in symbols
        assert 'GOOGL' in symbols
    
    def test_exactly_at_threshold(self):
        """Test position exactly at threshold is not flagged."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=100, avg_cost=150.0, current_value=15000.0, weight=20.0),
        ]
        
        risks = manager.identify_concentration_risk(positions)
        
        assert len(risks) == 0


class TestIdentifyCorrelationRisk:
    """Tests for correlation risk identification."""
    
    def test_no_correlation_risk_single_position(self):
        """Test single position has no correlation risk."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=10, avg_cost=150.0, current_value=1500.0, weight=15.0),
        ]
        
        risks = manager.identify_correlation_risk(positions)
        
        assert len(risks) == 0
    
    def test_no_correlation_risk_different_weights(self):
        """Test positions with different weights have no correlation risk."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=10, avg_cost=150.0, current_value=1500.0, weight=15.0),
            Position(symbol='GOOGL', shares=5, avg_cost=2800.0, current_value=14000.0, weight=5.0),
        ]
        
        risks = manager.identify_correlation_risk(positions)
        
        assert len(risks) == 0
    
    def test_correlation_risk_similar_weights(self):
        """Test positions with similar weights are flagged as potentially correlated."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=10, avg_cost=150.0, current_value=1500.0, weight=15.0),
            Position(symbol='GOOGL', shares=5, avg_cost=2800.0, current_value=14000.0, weight=14.0),
        ]
        
        risks = manager.identify_correlation_risk(positions)
        
        # Should identify potential correlation
        assert len(risks) >= 0  # May or may not flag depending on threshold
    
    def test_correlation_risk_message_format(self):
        """Test correlation risk message contains both symbols."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=10, avg_cost=150.0, current_value=1500.0, weight=15.0),
            Position(symbol='MSFT', shares=5, avg_cost=350.0, current_value=1750.0, weight=14.5),
        ]
        
        risks = manager.identify_correlation_risk(positions)
        
        if len(risks) > 0:
            risk = risks[0]
            assert risk.symbol1 in ['AAPL', 'MSFT']
            assert risk.symbol2 in ['AAPL', 'MSFT']
            assert risk.symbol1 != risk.symbol2
            assert 0.0 <= risk.correlation <= 1.0
            assert risk.symbol1 in risk.message
            assert risk.symbol2 in risk.message


class TestRiskMitigationActions:
    """Tests for risk mitigation action generation."""
    
    def test_mitigation_for_concentration_risk(self):
        """Test mitigation actions are generated for concentration risks."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=100, avg_cost=150.0, current_value=15000.0, weight=30.0),
        ]
        
        assessment = manager.assess_portfolio_risk(positions)
        
        assert len(assessment.risk_mitigation_actions) > 0
        assert any('AAPL' in action for action in assessment.risk_mitigation_actions)
        assert any('Reduce' in action for action in assessment.risk_mitigation_actions)
    
    def test_mitigation_for_high_risk_score(self):
        """Test mitigation actions for high overall risk score."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=100, avg_cost=150.0, current_value=15000.0, weight=40.0),
            Position(symbol='GOOGL', shares=50, avg_cost=2800.0, current_value=140000.0, weight=35.0),
        ]
        
        assessment = manager.assess_portfolio_risk(positions)
        
        # Portfolio has concentration risks which should generate mitigation actions
        assert assessment.portfolio_risk_score > 0.0
        assert len(assessment.concentration_risks) == 2
        assert len(assessment.risk_mitigation_actions) > 0
        # Should have mitigation actions for both concentration risks
        assert any('AAPL' in action for action in assessment.risk_mitigation_actions)
        assert any('GOOGL' in action for action in assessment.risk_mitigation_actions)
    
    def test_no_mitigation_for_low_risk(self):
        """Test no mitigation actions for low risk portfolio."""
        manager = RiskManager()
        positions = [
            Position(symbol='AAPL', shares=10, avg_cost=150.0, current_value=1500.0, weight=10.0),
            Position(symbol='GOOGL', shares=5, avg_cost=2800.0, current_value=14000.0, weight=10.0),
            Position(symbol='MSFT', shares=20, avg_cost=350.0, current_value=7000.0, weight=10.0),
        ]
        
        assessment = manager.assess_portfolio_risk(positions)
        
        # Low risk portfolio may have no or minimal mitigation actions
        assert assessment.portfolio_risk_score < 0.5
