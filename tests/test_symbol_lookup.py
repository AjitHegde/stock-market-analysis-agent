"""Tests for symbol lookup functionality."""

import pytest
from src.symbol_lookup import SymbolLookup, lookup_symbol, search_symbols


class TestSymbolLookup:
    """Test cases for SymbolLookup class."""
    
    def test_exact_match_us_stock(self):
        """Test exact match for US stock."""
        assert SymbolLookup.lookup("apple") == "AAPL"
        assert SymbolLookup.lookup("microsoft") == "MSFT"
        assert SymbolLookup.lookup("google") == "GOOGL"
    
    def test_exact_match_indian_stock(self):
        """Test exact match for Indian stock."""
        assert SymbolLookup.lookup("hdfc bank") == "HDFCBANK.NS"
        assert SymbolLookup.lookup("reliance") == "RELIANCE.NS"
        assert SymbolLookup.lookup("tcs") == "TCS.NS"
        assert SymbolLookup.lookup("sail") == "SAIL.NS"
        assert SymbolLookup.lookup("steel authority of india limited") == "SAIL.NS"
    
    def test_fuzzy_match(self):
        """Test fuzzy matching."""
        assert SymbolLookup.lookup("idfc first bank") == "IDFCFIRSTB.NS"
        assert SymbolLookup.lookup("idfc first") == "IDFCFIRSTB.NS"
        assert SymbolLookup.lookup("tata motors") == "TATAMOTORS.NS"
    
    def test_keyword_match(self):
        """Test keyword-based matching."""
        # Should match based on keywords
        result = SymbolLookup.lookup("hdfc")
        assert result == "HDFCBANK.NS"
        
        result = SymbolLookup.lookup("icici")
        assert result == "ICICIBANK.NS"
    
    def test_case_insensitive(self):
        """Test case insensitive matching."""
        assert SymbolLookup.lookup("APPLE") == "AAPL"
        assert SymbolLookup.lookup("Apple") == "AAPL"
        assert SymbolLookup.lookup("aPpLe") == "AAPL"
    
    def test_symbol_passthrough(self):
        """Test that valid symbols are passed through."""
        # Already a symbol
        assert SymbolLookup.lookup("AAPL") == "AAPL"
        assert SymbolLookup.lookup("TSLA") == "TSLA"
    
    def test_search_multiple_results(self):
        """Test searching for multiple matches."""
        results = SymbolLookup.search("bank", limit=5)
        
        assert len(results) > 0
        assert len(results) <= 5
        
        # Results should be tuples of (name, symbol, score)
        for name, symbol, score in results:
            assert isinstance(name, str)
            assert isinstance(symbol, str)
            assert 0.0 <= score <= 1.0
        
        # Results should be sorted by score (highest first)
        scores = [score for _, _, score in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_search_specific_company(self):
        """Test searching for specific company."""
        results = SymbolLookup.search("hdfc bank", limit=3)
        
        assert len(results) > 0
        
        # First result should be HDFC Bank
        name, symbol, score = results[0]
        assert "hdfc" in name.lower()
        assert symbol == "HDFCBANK.NS"
        assert score > 0.8  # High similarity
    
    def test_suggest_symbols(self):
        """Test symbol suggestions."""
        suggestions = SymbolLookup.suggest_symbols("tech")
        
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)
    
    def test_get_company_name(self):
        """Test reverse lookup (symbol to company name)."""
        assert SymbolLookup.get_company_name("AAPL") == "Apple"
        assert SymbolLookup.get_company_name("HDFCBANK.NS") == "Hdfc Bank"
        assert SymbolLookup.get_company_name("RELIANCE.NS") == "Reliance"
    
    def test_get_company_name_not_found(self):
        """Test reverse lookup for unknown symbol."""
        assert SymbolLookup.get_company_name("UNKNOWN") is None
    
    def test_empty_query(self):
        """Test handling of empty query."""
        assert SymbolLookup.lookup("") is None
        assert SymbolLookup.lookup(None) is None
        assert SymbolLookup.search("") == []
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        assert lookup_symbol("apple") == "AAPL"
        
        results = search_symbols("bank", limit=3)
        assert len(results) <= 3
        assert all(len(r) == 3 for r in results)


class TestSymbolLookupEdgeCases:
    """Test edge cases for symbol lookup."""
    
    def test_partial_name(self):
        """Test partial company names."""
        # Should still find matches
        assert SymbolLookup.lookup("micro") == "MSFT"  # Microsoft
    
    def test_abbreviations(self):
        """Test common abbreviations."""
        assert SymbolLookup.lookup("sbi") == "SBIN.NS"
        assert SymbolLookup.lookup("l&t") == "LT.NS"
        assert SymbolLookup.lookup("m&m") == "M&M.NS"
    
    def test_multiple_word_names(self):
        """Test multi-word company names."""
        assert SymbolLookup.lookup("tata consultancy") == "TCS.NS"
        assert SymbolLookup.lookup("larsen toubro") == "LT.NS"
        assert SymbolLookup.lookup("bharti airtel") == "BHARTIARTL.NS"
    
    def test_special_characters(self):
        """Test names with special characters."""
        assert SymbolLookup.lookup("johnson johnson") == "JNJ"
        assert SymbolLookup.lookup("procter gamble") == "PG"
    
    def test_common_misspellings(self):
        """Test fuzzy matching handles minor misspellings."""
        # These should still match due to fuzzy matching
        result = SymbolLookup.lookup("microsft")  # Missing 'o'
        assert result == "MSFT"
        
        result = SymbolLookup.lookup("gogle")  # Missing 'o'
        assert result == "GOOGL"


class TestSymbolLookupPerformance:
    """Test performance characteristics."""
    
    def test_lookup_speed(self):
        """Test that lookup is reasonably fast."""
        import time
        
        start = time.time()
        for _ in range(100):
            SymbolLookup.lookup("apple")
        elapsed = time.time() - start
        
        # Should complete 100 lookups in less than 1 second
        assert elapsed < 1.0
    
    def test_search_speed(self):
        """Test that search is reasonably fast."""
        import time
        
        start = time.time()
        for _ in range(50):
            SymbolLookup.search("bank", limit=5)
        elapsed = time.time() - start
        
        # Should complete 50 searches in less than 2 seconds
        assert elapsed < 2.0
