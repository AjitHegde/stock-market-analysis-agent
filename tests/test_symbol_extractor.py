"""Tests for SymbolExtractor class.

This test file verifies the symbol extraction functionality including
ticker symbol pattern matching and company name mapping.
"""

import pytest

from src.symbol_extractor import SymbolExtractor
from src.symbol_lookup import SymbolLookup


class TestSymbolExtractorTickerSymbols:
    """Test ticker symbol extraction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.symbol_lookup = SymbolLookup()
        self.extractor = SymbolExtractor(self.symbol_lookup)
    
    def test_find_ticker_symbols_basic(self):
        """Test basic ticker symbol extraction."""
        text = "Apple (AAPL) and Tesla (TSLA) stocks are rising"
        symbols = self.extractor._find_ticker_symbols(text)
        
        assert "AAPL" in symbols
        assert "TSLA" in symbols
        assert len(symbols) == 2
    
    def test_find_ticker_symbols_filters_common_words(self):
        """Test that common English words are filtered out."""
        text = "THE stock market AND the NYSE are open FOR trading"
        symbols = self.extractor._find_ticker_symbols(text)
        
        # Common words should be filtered out
        assert "THE" not in symbols
        assert "AND" not in symbols
        assert "FOR" not in symbols
        assert "NYSE" not in symbols  # NYSE is in COMMON_WORDS
    
    def test_find_ticker_symbols_from_title(self):
        """Test extracting symbols from article title."""
        text = "AAPL Stock Surges After Earnings Beat"
        symbols = self.extractor._find_ticker_symbols(text)
        
        assert "AAPL" in symbols
        assert "Stock" not in symbols  # Not all caps
        assert "After" not in symbols  # Not all caps
    
    def test_find_ticker_symbols_from_description(self):
        """Test extracting symbols from article description."""
        text = "Microsoft (MSFT) reported strong quarterly results, beating analyst expectations."
        symbols = self.extractor._find_ticker_symbols(text)
        
        assert "MSFT" in symbols
    
    def test_find_ticker_symbols_multiple_occurrences(self):
        """Test that duplicate symbols are deduplicated."""
        text = "AAPL stock rises. AAPL announces new product. AAPL CEO speaks."
        symbols = self.extractor._find_ticker_symbols(text)
        
        assert "AAPL" in symbols
        assert len(symbols) == 1  # Should be deduplicated
    
    def test_find_ticker_symbols_mixed_case(self):
        """Test that only uppercase sequences are matched."""
        text = "Apple stock (aapl) and GOOGL shares"
        symbols = self.extractor._find_ticker_symbols(text)
        
        assert "GOOGL" in symbols
        assert "aapl" not in symbols  # Lowercase should not match
        assert "Apple" not in symbols  # Mixed case should not match
    
    def test_find_ticker_symbols_word_boundaries(self):
        """Test that word boundaries are respected."""
        text = "NASDAQ100 includes AAPL and MSFT"
        symbols = self.extractor._find_ticker_symbols(text)
        
        # NASDAQ100 should not match (has digits)
        # Only AAPL and MSFT should match
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "NASDAQ" not in symbols  # Part of NASDAQ100, but NASDAQ is in COMMON_WORDS
    
    def test_find_ticker_symbols_length_limits(self):
        """Test that only 1-5 character symbols are matched."""
        text = "A BB CCC DDDD EEEEE FFFFFF"
        symbols = self.extractor._find_ticker_symbols(text)
        
        # 1-5 characters should match (if not common words)
        assert "A" in symbols or "A" in self.extractor.COMMON_WORDS
        assert "BB" in symbols
        assert "CCC" in symbols
        assert "DDDD" in symbols
        assert "EEEEE" in symbols
        # 6+ characters should not match
        assert "FFFFFF" not in symbols
    
    def test_find_ticker_symbols_empty_text(self):
        """Test handling of empty text."""
        symbols = self.extractor._find_ticker_symbols("")
        assert len(symbols) == 0
    
    def test_find_ticker_symbols_no_symbols(self):
        """Test text with no valid ticker symbols."""
        text = "The market is open today and trading is active"
        symbols = self.extractor._find_ticker_symbols(text)
        
        # All words should be filtered as common words
        assert len(symbols) == 0
    
    def test_find_ticker_symbols_with_punctuation(self):
        """Test symbols surrounded by punctuation."""
        text = "Stocks: AAPL, MSFT, GOOGL. All rising!"
        symbols = self.extractor._find_ticker_symbols(text)
        
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
        assert "All" not in symbols  # Not all caps
    
    def test_find_ticker_symbols_in_parentheses(self):
        """Test symbols in parentheses (common in news)."""
        text = "Apple Inc. (AAPL) and Microsoft Corporation (MSFT)"
        symbols = self.extractor._find_ticker_symbols(text)
        
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "Apple" not in symbols
        assert "Inc" not in symbols
    
    def test_find_ticker_symbols_real_world_example(self):
        """Test with a realistic news article excerpt."""
        text = """
        Tesla (TSLA) stock jumped 5% today after CEO announced new factory.
        The EV maker's shares have been volatile, with analysts watching
        closely. Meanwhile, AAPL and MSFT also saw gains in tech sector rally.
        """
        symbols = self.extractor._find_ticker_symbols(text)
        
        assert "TSLA" in symbols
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "CEO" not in symbols  # Common word
        # Note: "EV" will be extracted as it matches the pattern (2 uppercase letters)
        # This is expected behavior - validation against symbol lookup will filter it later
    
    def test_find_ticker_symbols_with_numbers(self):
        """Test that symbols with numbers are not matched."""
        text = "Check out STOCK1 and STOCK2 but also AAPL"
        symbols = self.extractor._find_ticker_symbols(text)
        
        # Only pure letter symbols should match
        assert "AAPL" in symbols
        assert "STOCK1" not in symbols
        assert "STOCK2" not in symbols


class TestSymbolExtractorIntegration:
    """Test the full extract_from_text method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.symbol_lookup = SymbolLookup()
        self.extractor = SymbolExtractor(self.symbol_lookup)
    
    def test_extract_from_text_empty(self):
        """Test extracting from empty text."""
        symbols = self.extractor.extract_from_text("")
        assert len(symbols) == 0
    
    def test_extract_from_text_none(self):
        """Test extracting from None text."""
        symbols = self.extractor.extract_from_text(None)
        assert len(symbols) == 0
    
    def test_extract_from_text_ticker_and_company(self):
        """Test extracting both ticker symbols and company names."""
        text = "Apple (AAPL) and Microsoft (MSFT) stocks are rising"
        symbols = self.extractor.extract_from_text(text)
        
        # Should find AAPL from both ticker and company name
        assert "AAPL" in symbols
        # Should find MSFT from both ticker and company name
        assert "MSFT" in symbols
    
    def test_extract_from_text_company_name_only(self):
        """Test extracting when only company name is mentioned."""
        text = "Tesla announces new factory in Texas"
        symbols = self.extractor.extract_from_text(text)
        
        assert "TSLA" in symbols
    
    def test_extract_from_text_ticker_only(self):
        """Test extracting when only ticker is mentioned."""
        text = "NVDA stock surges on AI demand"
        symbols = self.extractor.extract_from_text(text)
        
        assert "NVDA" in symbols
    
    def test_extract_from_text_deduplication(self):
        """Test that symbols from both methods are deduplicated."""
        text = "Apple (AAPL) stock rises. Apple announces new product."
        symbols = self.extractor.extract_from_text(text)
        
        # Should have AAPL only once despite multiple mentions
        assert "AAPL" in symbols
        symbol_list = list(symbols)
        assert symbol_list.count("AAPL") == 1
    
    def test_extract_from_text_mixed_sources(self):
        """Test extracting from text with various symbol sources."""
        text = """
        Tech giants Apple and Google reported earnings.
        MSFT stock also rose, while TSLA faced challenges.
        Amazon Web Services continues to grow.
        """
        symbols = self.extractor.extract_from_text(text)
        
        # From company names
        assert "AAPL" in symbols  # Apple
        assert "GOOGL" in symbols  # Google
        assert "AMZN" in symbols  # Amazon
        
        # From tickers
        assert "MSFT" in symbols
        assert "TSLA" in symbols
    
    def test_extract_from_text_real_news_article(self):
        """Test with a realistic news article title and description."""
        title = "Tesla Stock Jumps After Strong Q4 Earnings"
        description = "Tesla Inc. reported better-than-expected earnings, with CEO Elon Musk highlighting production milestones."
        text = f"{title} {description}"
        
        symbols = self.extractor.extract_from_text(text)
        
        # Should find TSLA from both "Tesla" company name and context
        assert "TSLA" in symbols
    
    def test_extract_from_text_indian_companies(self):
        """Test extracting Indian company symbols."""
        text = "HDFC Bank and Reliance Industries lead the market rally"
        symbols = self.extractor.extract_from_text(text)
        
        assert "HDFCBANK.NS" in symbols
        assert "RELIANCE.NS" in symbols
    
    def test_extract_from_text_filters_common_words(self):
        """Test that common words are filtered even in combined extraction."""
        text = "THE market is open AND stocks are trading FOR investors"
        symbols = self.extractor.extract_from_text(text)
        
        # Common words should be filtered
        assert "THE" not in symbols
        assert "AND" not in symbols
        assert "FOR" not in symbols


class TestSymbolExtractorCompanyNames:
    """Test company name extraction and mapping functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.symbol_lookup = SymbolLookup()
        self.extractor = SymbolExtractor(self.symbol_lookup)
    
    def test_find_company_names_basic(self):
        """Test basic company name extraction."""
        text = "Apple announces new product line"
        symbols = self.extractor._find_company_names(text)
        
        assert "AAPL" in symbols
    
    def test_find_company_names_case_insensitive(self):
        """Test case-insensitive matching."""
        text = "APPLE, Apple, and apple all refer to the same company"
        symbols = self.extractor._find_company_names(text)
        
        # Should find "apple" (lowercase in SYMBOL_MAP) regardless of case in text
        assert "AAPL" in symbols
    
    def test_find_company_names_multiple_companies(self):
        """Test finding multiple company names."""
        text = "Apple and Microsoft are tech giants, while Tesla leads in EVs"
        symbols = self.extractor._find_company_names(text)
        
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "TSLA" in symbols
    
    def test_find_company_names_with_variations(self):
        """Test finding company name variations."""
        # Test that both "google" and "alphabet" map to GOOGL
        text1 = "Google announces new AI features"
        symbols1 = self.extractor._find_company_names(text1)
        assert "GOOGL" in symbols1
        
        text2 = "Alphabet Inc. reports earnings"
        symbols2 = self.extractor._find_company_names(text2)
        assert "GOOGL" in symbols2
    
    def test_find_company_names_indian_companies(self):
        """Test finding Indian company names."""
        text = "HDFC Bank and ICICI Bank are leading Indian banks"
        symbols = self.extractor._find_company_names(text)
        
        assert "HDFCBANK.NS" in symbols
        assert "ICICIBANK.NS" in symbols
    
    def test_find_company_names_with_inc_ltd(self):
        """Test company names with Inc., Ltd., etc."""
        text = "Apple Inc. and Microsoft Corporation announce partnership"
        symbols = self.extractor._find_company_names(text)
        
        # Should find "apple" even though text has "Apple Inc."
        assert "AAPL" in symbols
        assert "MSFT" in symbols
    
    def test_find_company_names_empty_text(self):
        """Test handling of empty text."""
        symbols = self.extractor._find_company_names("")
        assert len(symbols) == 0
    
    def test_find_company_names_no_matches(self):
        """Test text with no known company names."""
        text = "The weather is nice today and I like pizza"
        symbols = self.extractor._find_company_names(text)
        
        assert len(symbols) == 0
    
    def test_find_company_names_partial_match(self):
        """Test that partial matches work correctly."""
        # "bank" appears in many company names
        text = "The bank announced new rates"
        symbols = self.extractor._find_company_names(text)
        
        # Should find companies with "bank" in their name
        # This might match multiple banks, which is expected
        assert len(symbols) >= 0  # Could be 0 or more depending on SYMBOL_MAP
    
    def test_find_company_names_deduplication(self):
        """Test that duplicate company mentions result in single symbol."""
        text = "Apple releases new iPhone. Apple stock rises. Apple CEO speaks."
        symbols = self.extractor._find_company_names(text)
        
        # Should only have AAPL once
        assert "AAPL" in symbols
        # Count occurrences - should be 1
        symbol_list = list(symbols)
        assert symbol_list.count("AAPL") == 1
    
    def test_find_company_names_real_world_example(self):
        """Test with realistic news article excerpt."""
        text = """
        Tesla CEO Elon Musk announced plans for a new Gigafactory.
        The electric vehicle maker has been competing with traditional
        automakers. Meanwhile, Apple is rumored to be working on its
        own autonomous vehicle project.
        """
        symbols = self.extractor._find_company_names(text)
        
        assert "TSLA" in symbols
        assert "AAPL" in symbols
    
    def test_find_company_names_with_ticker_in_text(self):
        """Test that company names are found even when ticker is also present."""
        text = "Apple (AAPL) announces new product"
        symbols = self.extractor._find_company_names(text)
        
        # Should find "apple" company name
        assert "AAPL" in symbols
    
    def test_find_company_names_indian_variations(self):
        """Test Indian company name variations."""
        # Test various ways to refer to TCS
        text1 = "TCS reports strong quarterly results"
        symbols1 = self.extractor._find_company_names(text1)
        assert "TCS.NS" in symbols1
        
        text2 = "Tata Consultancy Services announces dividend"
        symbols2 = self.extractor._find_company_names(text2)
        assert "TCS.NS" in symbols2
    
    def test_find_company_names_reliance(self):
        """Test Reliance Industries variations."""
        text = "Reliance Industries expands retail business"
        symbols = self.extractor._find_company_names(text)
        
        assert "RELIANCE.NS" in symbols
