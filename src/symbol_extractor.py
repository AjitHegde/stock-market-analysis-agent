"""Symbol extraction module for identifying stock symbols in news text.

This module provides functionality to extract stock ticker symbols and company
names from news article text using regex patterns and symbol lookup mapping.
"""

import logging
import re
from typing import Set

from src.symbol_lookup import SymbolLookup


logger = logging.getLogger(__name__)


class SymbolExtractor:
    """Extracts stock symbols from news text.
    
    This class identifies stock symbols in two ways:
    1. Explicit ticker symbols using regex pattern matching (e.g., "AAPL", "TSLA")
    2. Company names mapped to symbols using SymbolLookup (e.g., "Apple" -> "AAPL")
    """
    
    # Common English words to filter out (not stock symbols)
    COMMON_WORDS = {
        'THE', 'AND', 'OR', 'BUT', 'FOR', 'NOR', 'YET', 'SO',
        'AT', 'BY', 'IN', 'OF', 'ON', 'TO', 'UP', 'AS', 'IT',
        'AN', 'BE', 'DO', 'IF', 'NO', 'WE', 'HE', 'SHE', 'YOU',
        'ALL', 'ANY', 'CAN', 'HAD', 'HAS', 'HER', 'HIM', 'HIS',
        'HOW', 'ITS', 'MAY', 'NEW', 'NOT', 'NOW', 'OLD', 'OUR',
        'OUT', 'OWN', 'SAY', 'SEE', 'SHE', 'TOO', 'TWO', 'USE',
        'WAS', 'WAY', 'WHO', 'WHY', 'WILL', 'WITH', 'WOULD',
        'ABOUT', 'AFTER', 'AGAIN', 'ALSO', 'BACK', 'BEEN',
        'BEFORE', 'BEING', 'BETWEEN', 'BOTH', 'COULD', 'EACH',
        'EVEN', 'FIRST', 'FROM', 'GOOD', 'GREAT', 'HAVE', 'HERE',
        'INTO', 'JUST', 'KNOW', 'LAST', 'LIKE', 'LONG', 'MADE',
        'MAKE', 'MANY', 'MORE', 'MOST', 'MUCH', 'MUST', 'NEVER',
        'NEXT', 'ONLY', 'OTHER', 'OVER', 'SAID', 'SAME', 'SHOULD',
        'SINCE', 'SOME', 'STILL', 'SUCH', 'TAKE', 'THAN', 'THAT',
        'THEIR', 'THEM', 'THEN', 'THERE', 'THESE', 'THEY', 'THIS',
        'THOSE', 'THROUGH', 'TIME', 'UNDER', 'UNTIL', 'VERY',
        'WANT', 'WELL', 'WERE', 'WHAT', 'WHEN', 'WHERE', 'WHICH',
        'WHILE', 'YEAR', 'YOUR', 'YEARS', 'WEEK', 'MONTH', 'DAY',
        'DAYS', 'WEEKS', 'MONTHS', 'TODAY', 'TOMORROW', 'YESTERDAY',
        'MARKET', 'STOCK', 'STOCKS', 'SHARE', 'SHARES', 'PRICE',
        'PRICES', 'TRADE', 'TRADING', 'TRADER', 'TRADERS', 'INVEST',
        'INVESTOR', 'INVESTORS', 'WALL', 'STREET', 'NYSE', 'NASDAQ',
        'DOW', 'INDEX', 'INDICES', 'FUND', 'FUNDS', 'ETF', 'ETFS',
        'CEO', 'CFO', 'CTO', 'COO', 'IPO', 'IPOS', 'SEC', 'FED',
        'GDP', 'CPI', 'USA', 'US', 'UK', 'EU', 'CHINA', 'INDIA',
        'JAPAN', 'ASIA', 'EUROPE', 'AMERICA', 'AMERICAN', 'GLOBAL',
        'WORLD', 'INTERNATIONAL', 'NATIONAL', 'LOCAL', 'STATE',
        'FEDERAL', 'GOVERNMENT', 'BANK', 'BANKS', 'BANKING',
        'FINANCE', 'FINANCIAL', 'ECONOMY', 'ECONOMIC', 'BUSINESS',
        'COMPANY', 'COMPANIES', 'CORP', 'CORPORATION', 'INC',
        'LTD', 'LLC', 'GROUP', 'HOLDINGS', 'CAPITAL', 'PARTNERS',
        'MANAGEMENT', 'SERVICES', 'SOLUTIONS', 'SYSTEMS', 'TECH',
        'TECHNOLOGY', 'TECHNOLOGIES', 'SOFTWARE', 'HARDWARE',
        'INTERNET', 'ONLINE', 'DIGITAL', 'CLOUD', 'DATA', 'AI',
        'BILLION', 'MILLION', 'TRILLION', 'PERCENT', 'QUARTER',
        'ANNUAL', 'REVENUE', 'PROFIT', 'LOSS', 'EARNINGS', 'SALES',
        # Single letters that are commonly used as words (not stock symbols)
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 
        'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 
        'Y', 'Z',
        # Common acronyms that are not stock symbols
        'NFL', 'NBA', 'MLB', 'NHL', 'MLS', 'NCAA', 'FIFA', 'UEFA',
        'MVP', 'CEO', 'CFO', 'CTO', 'COO', 'CMO', 'CIO', 'VP',
        'HR', 'IT', 'PR', 'RD', 'QA', 'UI', 'UX', 'API', 'SDK',
        'HTML', 'CSS', 'XML', 'JSON', 'SQL', 'HTTP', 'HTTPS', 'FTP',
        'PDF', 'JPG', 'PNG', 'GIF', 'MP3', 'MP4', 'ZIP', 'RAR',
        'USA', 'UK', 'EU', 'UN', 'NATO', 'WHO', 'IMF', 'WTO',
        'GOP', 'DNC', 'FBI', 'CIA', 'NSA', 'IRS', 'FDA', 'EPA',
        'COVID', 'AIDS', 'HIV', 'DNA', 'RNA', 'MRI', 'CT', 'ER',
        'AM', 'PM', 'EST', 'PST', 'GMT', 'UTC', 'BC', 'AD',
        'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG',
        'SEP', 'OCT', 'NOV', 'DEC', 'MON', 'TUE', 'WED', 'THU',
        'FRI', 'SAT', 'SUN', 'ASAP', 'FYI', 'FAQ', 'TBD', 'TBA'
    }
    
    def __init__(self, symbol_lookup: SymbolLookup):
        """Initialize with symbol lookup service.
        
        Args:
            symbol_lookup: SymbolLookup instance for company name mapping
        """
        self.symbol_lookup = symbol_lookup
        
        # Compile regex pattern for ticker symbols (1-5 uppercase letters)
        # Pattern: word boundary + 1-5 uppercase letters + word boundary
        self.ticker_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        
        logger.info("SymbolExtractor initialized")
    
    def extract_from_text(self, text: str) -> Set[str]:
        """Extract symbols from text.
        
        Combines ticker symbol extraction and company name mapping to find
        all stock symbols mentioned in the text.
        
        Args:
            text: Article title or content to parse
            
        Returns:
            Set of discovered stock symbols (deduplicated)
            
        Validates: Requirements 2.1, 2.2, 2.3
        """
        if not text:
            return set()
        
        symbols = set()
        
        # Phase 1: Find explicit ticker symbols
        ticker_symbols = self._find_ticker_symbols(text)
        symbols.update(ticker_symbols)
        
        # Phase 2: Find company names and map to symbols
        company_symbols = self._find_company_names(text)
        symbols.update(company_symbols)
        
        logger.debug(f"Extracted {len(symbols)} symbols from text")
        return symbols
    
    def _find_ticker_symbols(self, text: str) -> Set[str]:
        """Find explicit ticker symbols using regex.
        
        Uses regex pattern to find 1-5 uppercase letter sequences that look
        like ticker symbols. Filters out common English words.
        
        Args:
            text: Text to search for ticker symbols
            
        Returns:
            Set of ticker symbols found
            
        Validates: Requirements 2.2
        """
        if not text:
            return set()
        
        # Find all matches using the regex pattern
        matches = self.ticker_pattern.findall(text)
        
        # Filter out common English words
        symbols = {match for match in matches if match not in self.COMMON_WORDS}
        
        logger.debug(f"Found {len(symbols)} ticker symbols after filtering")
        return symbols
    
    def _find_company_names(self, text: str) -> Set[str]:
        """Find company names and map to symbols.
        
        Searches for known company names from the symbol lookup registry
        and maps them to their corresponding stock symbols using case-insensitive
        matching.
        
        Args:
            text: Text to search for company names
            
        Returns:
            Set of symbols mapped from company names
            
        Validates: Requirements 2.3, 2.4
        """
        if not text:
            return set()
        
        symbols = set()
        text_lower = text.lower()
        
        # Search for each company name in the symbol lookup map
        for company_name, symbol in self.symbol_lookup.SYMBOL_MAP.items():
            # Use case-insensitive matching
            # Check if the company name appears as a whole word or phrase in the text
            if company_name in text_lower:
                symbols.add(symbol)
                logger.debug(f"Found company name '{company_name}' -> {symbol}")
        
        logger.debug(f"Found {len(symbols)} symbols from company names")
        return symbols
