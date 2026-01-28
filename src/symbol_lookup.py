"""
Symbol lookup utility for converting company names to ticker symbols.

This module provides fuzzy matching and keyword-based lookup to help users
find stock symbols using company names or keywords. Falls back to online
search via yfinance when local map doesn't have a match.
"""

from typing import Optional, List, Tuple, Dict
from difflib import SequenceMatcher
import re
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SymbolLookup:
    """Lookup stock symbols from company names or keywords."""
    
    # Path to user's custom symbol map (persisted across sessions)
    USER_MAP_PATH = Path.home() / ".stock-agent" / "user_symbols.json"
    
    # Comprehensive mapping of company names/keywords to ticker symbols
    SYMBOL_MAP = {
        # US Tech Giants
        "apple": "AAPL",
        "microsoft": "MSFT",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "amazon": "AMZN",
        "meta": "META",
        "facebook": "META",
        "nvidia": "NVDA",
        "tesla": "TSLA",
        "amd": "AMD",
        "advanced micro devices": "AMD",
        "intel": "INTC",
        "oracle": "ORCL",
        "netflix": "NFLX",
        "adobe": "ADBE",
        "salesforce": "CRM",
        "cisco": "CSCO",
        "ibm": "IBM",
        "qualcomm": "QCOM",
        "broadcom": "AVGO",
        "servicenow": "NOW",
        "snowflake": "SNOW",
        "palantir": "PLTR",
        "uber": "UBER",
        "lyft": "LYFT",
        "airbnb": "ABNB",
        "spotify": "SPOT",
        "zoom": "ZM",
        "docusign": "DOCU",
        "shopify": "SHOP",
        "square": "SQ",
        "block": "SQ",
        "coinbase": "COIN",
        "robinhood": "HOOD",
        
        # US Finance
        "jpmorgan": "JPM",
        "jp morgan": "JPM",
        "bank of america": "BAC",
        "wells fargo": "WFC",
        "goldman sachs": "GS",
        "morgan stanley": "MS",
        "citigroup": "C",
        "visa": "V",
        "mastercard": "MA",
        "american express": "AXP",
        "paypal": "PYPL",
        "square": "SQ",
        "block": "SQ",
        
        # US Consumer
        "walmart": "WMT",
        "home depot": "HD",
        "nike": "NKE",
        "starbucks": "SBUX",
        "mcdonalds": "MCD",
        "mcdonald's": "MCD",
        "disney": "DIS",
        "walt disney": "DIS",
        "costco": "COST",
        "target": "TGT",
        "coca cola": "KO",
        "pepsi": "PEP",
        "pepsico": "PEP",
        "procter gamble": "PG",
        "p&g": "PG",
        "chipotle": "CMG",
        "chipotle mexican grill": "CMG",
        "dominos": "DPZ",
        "domino's pizza": "DPZ",
        "dominos pizza": "DPZ",
        "lululemon": "LULU",
        "lulu": "LULU",
        "crocs": "CROX",
        "yeti": "YETI",
        "peloton": "PTON",
        "draftkings": "DKNG",
        "roblox": "RBLX",
        "unity": "U",
        "unity software": "U",
        "twilio": "TWLO",
        "datadog": "DDOG",
        "crowdstrike": "CRWD",
        "mongodb": "MDB",
        "mongo": "MDB",
        
        # US Healthcare
        "johnson johnson": "JNJ",
        "j&j": "JNJ",
        "unitedhealth": "UNH",
        "pfizer": "PFE",
        "abbvie": "ABBV",
        "merck": "MRK",
        "eli lilly": "LLY",
        "lilly": "LLY",
        "bristol myers": "BMY",
        "abbott": "ABT",
        "moderna": "MRNA",
        
        # US Industrial & Energy
        "boeing": "BA",
        "caterpillar": "CAT",
        "general electric": "GE",
        "ge": "GE",
        "exxon": "XOM",
        "exxonmobil": "XOM",
        "chevron": "CVX",
        "conocophillips": "COP",
        "schlumberger": "SLB",
        
        # US Communication
        "at&t": "T",
        "att": "T",
        "verizon": "VZ",
        "comcast": "CMCSA",
        "t-mobile": "TMUS",
        "tmobile": "TMUS",
        
        # International Tech & Auto
        "samsung": "005930.KS",
        "tsmc": "TSM",
        "taiwan semiconductor": "TSM",
        "asml": "ASML",
        "sony": "SONY",
        "toyota": "TM",
        "honda": "HMC",
        "volkswagen": "VWAGY",
        "bmw": "BMWYY",
        "mercedes": "DDAIF",
        "daimler": "DDAIF",
        "ferrari": "RACE",
        "porsche": "POAHY",
        
        # International Finance & Pharma
        "hsbc": "HSBC",
        "barclays": "BCS",
        "deutsche bank": "DB",
        "ubs": "UBS",
        "credit suisse": "CS",
        "ing": "ING",
        "santander": "SAN",
        "novartis": "NVS",
        "roche": "RHHBY",
        "astrazeneca": "AZN",
        "glaxosmithkline": "GSK",
        "gsk": "GSK",
        "sanofi": "SNY",
        "bayer": "BAYRY",
        
        # International Consumer
        "nestle": "NSRGY",
        "unilever": "UL",
        "diageo": "DEO",
        "lvmh": "LVMUY",
        "louis vuitton": "LVMUY",
        "hermes": "HESAY",
        "adidas": "ADDYY",
        "puma": "PUMSY",
        "heineken": "HEINY",
        "anheuser busch": "BUD",
        "ab inbev": "BUD",
        
        # Chinese & Asian Tech
        "alibaba": "BABA",
        "baba": "BABA",
        "tencent": "TCEHY",
        "baidu": "BIDU",
        "jd": "JD",
        "jd.com": "JD",
        "jingdong": "JD",
        "pinduoduo": "PDD",
        "pdd": "PDD",
        "sea limited": "SE",
        "sea": "SE",
        "grab": "GRAB",
        "grab holdings": "GRAB",
        "nio": "NIO",
        "xpeng": "XPEV",
        "li auto": "LI",
        "bilibili": "BILI",
        "netease": "NTES",
        "meituan": "MEITUAN",
        
        # Indian Banks
        "hdfc bank": "HDFCBANK.NS",
        "hdfcbank": "HDFCBANK.NS",
        "hdfc": "HDFCBANK.NS",
        "icici bank": "ICICIBANK.NS",
        "icicibank": "ICICIBANK.NS",
        "icici": "ICICIBANK.NS",
        "state bank": "SBIN.NS",
        "sbi": "SBIN.NS",
        "axis bank": "AXISBANK.NS",
        "axisbank": "AXISBANK.NS",
        "axis": "AXISBANK.NS",
        "kotak mahindra": "KOTAKBANK.NS",
        "kotak bank": "KOTAKBANK.NS",
        "kotak": "KOTAKBANK.NS",
        "indusind bank": "INDUSINDBK.NS",
        "indusind": "INDUSINDBK.NS",
        "yes bank": "YESBANK.NS",
        "yesbank": "YESBANK.NS",
        "idfc first bank": "IDFCFIRSTB.NS",
        "idfc first": "IDFCFIRSTB.NS",
        "idfcfirstb": "IDFCFIRSTB.NS",
        "idfc": "IDFCFIRSTB.NS",
        "bandhan bank": "BANDHANBNK.NS",
        "bandhan": "BANDHANBNK.NS",
        "federal bank": "FEDERALBNK.NS",
        "federal": "FEDERALBNK.NS",
        
        # Indian IT
        "tata consultancy": "TCS.NS",
        "tcs": "TCS.NS",
        "infosys": "INFY.NS",
        "infy": "INFY.NS",
        "wipro": "WIPRO.NS",
        "hcl tech": "HCLTECH.NS",
        "hcltech": "HCLTECH.NS",
        "hcl": "HCLTECH.NS",
        "tech mahindra": "TECHM.NS",
        "techm": "TECHM.NS",
        "ltimindtree": "LTIM.NS",
        "lti": "LTIM.NS",
        "mindtree": "LTIM.NS",
        
        # Indian Conglomerates
        "reliance": "RELIANCE.NS",
        "reliance industries": "RELIANCE.NS",
        "ril": "RELIANCE.NS",
        "tata motors": "TATAMOTORS.NS",
        "tatamotors": "TATAMOTORS.NS",
        "tata steel": "TATASTEEL.NS",
        "tatasteel": "TATASTEEL.NS",
        "tata power": "TATAPOWER.NS",
        "tatapower": "TATAPOWER.NS",
        "mahindra": "M&M.NS",
        "m&m": "M&M.NS",
        "mahindra and mahindra": "M&M.NS",
        "larsen toubro": "LT.NS",
        "l&t": "LT.NS",
        "lt": "LT.NS",
        "adani enterprises": "ADANIENT.NS",
        "adani": "ADANIENT.NS",
        "adani ports": "ADANIPORTS.NS",
        "adani green": "ADANIGREEN.NS",
        
        # Indian Telecom
        "bharti airtel": "BHARTIARTL.NS",
        "airtel": "BHARTIARTL.NS",
        "bharti": "BHARTIARTL.NS",
        "vodafone idea": "IDEA.NS",
        "vi": "IDEA.NS",
        "idea": "IDEA.NS",
        
        # Indian FMCG
        "hindustan unilever": "HINDUNILVR.NS",
        "hul": "HINDUNILVR.NS",
        "itc": "ITC.NS",
        "itc limited": "ITC.NS",
        "nestle india": "NESTLEIND.NS",
        "nestle": "NESTLEIND.NS",
        "britannia": "BRITANNIA.NS",
        "dabur": "DABUR.NS",
        "godrej consumer": "GODREJCP.NS",
        "godrej": "GODREJCP.NS",
        "asian paints": "ASIANPAINT.NS",
        "asianpaint": "ASIANPAINT.NS",
        "asian paint": "ASIANPAINT.NS",
        "pidilite": "PIDILITIND.NS",
        "pidilite industries": "PIDILITIND.NS",
        "havells": "HAVELLS.NS",
        "havells india": "HAVELLS.NS",
        "crompton": "CROMPTON.NS",
        "crompton greaves": "CROMPTON.NS",
        "tata consumer": "TATACONSUM.NS",
        "tata consumer products": "TATACONSUM.NS",
        
        # Indian Pharma
        "sun pharma": "SUNPHARMA.NS",
        "sunpharma": "SUNPHARMA.NS",
        "dr reddy": "DRREDDY.NS",
        "dr. reddy": "DRREDDY.NS",
        "cipla": "CIPLA.NS",
        "lupin": "LUPIN.NS",
        "aurobindo pharma": "AUROPHARMA.NS",
        "aurobindo": "AUROPHARMA.NS",
        "divi's lab": "DIVISLAB.NS",
        "divis": "DIVISLAB.NS",
        
        # Indian Auto
        "maruti suzuki": "MARUTI.NS",
        "maruti": "MARUTI.NS",
        "bajaj auto": "BAJAJ-AUTO.NS",
        "bajaj": "BAJAJ-AUTO.NS",
        "hero motocorp": "HEROMOTOCO.NS",
        "hero": "HEROMOTOCO.NS",
        "tvs motor": "TVSMOTOR.NS",
        "tvs": "TVSMOTOR.NS",
        "eicher motors": "EICHERMOT.NS",
        "eicher": "EICHERMOT.NS",
        "royal enfield": "EICHERMOT.NS",
        
        # Indian Energy & PSU
        "ongc": "ONGC.NS",
        "oil and natural gas": "ONGC.NS",
        "oil and natural gas corporation": "ONGC.NS",
        "ntpc": "NTPC.NS",
        "ntpc limited": "NTPC.NS",
        "power grid": "POWERGRID.NS",
        "powergrid": "POWERGRID.NS",
        "power grid corporation": "POWERGRID.NS",
        "coal india": "COALINDIA.NS",
        "coalindia": "COALINDIA.NS",
        "coal india limited": "COALINDIA.NS",
        "ioc": "IOC.NS",
        "indian oil": "IOC.NS",
        "indian oil corporation": "IOC.NS",
        "bpcl": "BPCL.NS",
        "bharat petroleum": "BPCL.NS",
        "bharat petroleum corporation": "BPCL.NS",
        "hpcl": "HPCL.NS",
        "hindustan petroleum": "HPCL.NS",
        "hindustan petroleum corporation": "HPCL.NS",
        "gail": "GAIL.NS",
        "gail india": "GAIL.NS",
        "gail india limited": "GAIL.NS",
        
        # Indian Steel & Metals
        "sail": "SAIL.NS",
        "steel authority": "SAIL.NS",
        "steel authority of india": "SAIL.NS",
        "steel authority of india limited": "SAIL.NS",
        "tata steel": "TATASTEEL.NS",
        "tatasteel": "TATASTEEL.NS",
        "jswsteel": "JSWSTEEL.NS",
        "jsw steel": "JSWSTEEL.NS",
        "jsw": "JSWSTEEL.NS",
        "hindalco": "HINDALCO.NS",
        "hindalco industries": "HINDALCO.NS",
        "vedanta": "VEDL.NS",
        "vedanta limited": "VEDL.NS",
        "nmdc": "NMDC.NS",
        "nmdc limited": "NMDC.NS",
        "jindal steel": "JINDALSTEL.NS",
        "jindal steel and power": "JINDALSTEL.NS",
        
        # Indian Infrastructure & Construction
        "larsen toubro": "LT.NS",
        "l&t": "LT.NS",
        "lt": "LT.NS",
        "larsen and toubro": "LT.NS",
        "ultratech cement": "ULTRACEMCO.NS",
        "ultratech": "ULTRACEMCO.NS",
        "ambuja cement": "AMBUJACEM.NS",
        "ambuja": "AMBUJACEM.NS",
        "acc": "ACC.NS",
        "acc limited": "ACC.NS",
        "grasim": "GRASIM.NS",
        "grasim industries": "GRASIM.NS",
        
        # Indian Railways & Defense
        "irctc": "IRCTC.NS",
        "indian railway catering": "IRCTC.NS",
        "bhel": "BHEL.NS",
        "bharat heavy electricals": "BHEL.NS",
        "hal": "HAL.NS",
        "hindustan aeronautics": "HAL.NS",
        "bel": "BEL.NS",
        "bharat electronics": "BEL.NS",
        
        # Indian Financial Services
        "sbi life": "SBILIFE.NS",
        "sbi life insurance": "SBILIFE.NS",
        "hdfc life": "HDFCLIFE.NS",
        "hdfc life insurance": "HDFCLIFE.NS",
        "icici prudential": "ICICIPRULI.NS",
        "icici prudential life": "ICICIPRULI.NS",
        "bajaj finance": "BAJFINANCE.NS",
        "bajaj finserv": "BAJAJFINSV.NS",
        "lic": "LICI.NS",
        "lic india": "LICI.NS",
        "life insurance corporation": "LICI.NS",
        "shriram finance": "SHRIRAMFIN.NS",
        "shriram": "SHRIRAMFIN.NS",
        
        # Indian New-Age Tech & E-commerce
        "zomato": "ZOMATO.NS",
        "paytm": "PAYTM.NS",
        "one97": "PAYTM.NS",
        "one97 communications": "PAYTM.NS",
        "nykaa": "NYKAA.NS",
        "fsnl": "NYKAA.NS",
        "fsn e-commerce": "NYKAA.NS",
        "delhivery": "DELHIVERY.NS",
        "policybazaar": "POLICYBZR.NS",
        "pb fintech": "POLICYBZR.NS",
        "cartrade": "CARTRADE.NS",
        "cartrade tech": "CARTRADE.NS",
    }
    
    @classmethod
    def lookup(cls, query: str) -> Optional[str]:
        """
        Lookup a stock symbol from a company name or keyword.
        
        Uses exact matching, fuzzy matching, and keyword extraction to find
        the best matching symbol.
        
        Args:
            query: Company name, keyword, or partial name
            
        Returns:
            Stock ticker symbol or None if no match found
            
        Examples:
            >>> SymbolLookup.lookup("apple")
            'AAPL'
            >>> SymbolLookup.lookup("idfc first bank")
            'IDFCFIRSTB.NS'
            >>> SymbolLookup.lookup("hdfc")
            'HDFCBANK.NS'
        """
        if not query:
            return None
        
        # Normalize query
        query = query.lower().strip()
        
        # If it looks like a symbol already (all caps, short), return as-is
        if query.isupper() and len(query) <= 10:
            return query.upper()
        
        # Check for exact match
        if query in cls.SYMBOL_MAP:
            return cls.SYMBOL_MAP[query]
        
        # Try fuzzy matching
        best_match = cls._fuzzy_match(query)
        if best_match:
            return best_match
        
        # Try keyword extraction
        keyword_match = cls._keyword_match(query)
        if keyword_match:
            return keyword_match
        
        # If nothing found, return the original query uppercased
        # (might be a valid symbol we don't have in our map)
        return query.upper()
    
    @classmethod
    def search(cls, query: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        """
        Search for multiple matching symbols with similarity scores.
        
        Args:
            query: Company name or keyword
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (company_name, symbol, similarity_score)
            sorted by similarity score (highest first)
            
        Examples:
            >>> SymbolLookup.search("bank", limit=3)
            [('hdfc bank', 'HDFCBANK.NS', 0.85),
             ('icici bank', 'ICICIBANK.NS', 0.82),
             ('axis bank', 'AXISBANK.NS', 0.80)]
        """
        if not query:
            return []
        
        query = query.lower().strip()
        results = []
        
        for name, symbol in cls.SYMBOL_MAP.items():
            similarity = cls._calculate_similarity(query, name)
            if similarity > 0.3:  # Minimum threshold
                results.append((name, symbol, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results[:limit]
    
    @classmethod
    def _fuzzy_match(cls, query: str) -> Optional[str]:
        """
        Find the best fuzzy match for a query.
        
        Uses SequenceMatcher to find similar company names.
        """
        best_match = None
        best_score = 0.0
        threshold = 0.6  # Minimum similarity threshold
        
        for name, symbol in cls.SYMBOL_MAP.items():
            score = SequenceMatcher(None, query, name).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = symbol
        
        return best_match
    
    @classmethod
    def _keyword_match(cls, query: str) -> Optional[str]:
        """
        Match based on keywords in the query.
        
        Extracts important keywords and finds matches.
        """
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        keywords = [word for word in query.split() if word not in stop_words]
        
        if not keywords:
            return None
        
        # Try to find a name that contains all keywords
        for name, symbol in cls.SYMBOL_MAP.items():
            if all(keyword in name for keyword in keywords):
                return symbol
        
        # Try to find a name that contains any keyword
        for name, symbol in cls.SYMBOL_MAP.items():
            if any(keyword in name for keyword in keywords):
                return symbol
        
        return None
    
    @classmethod
    def _calculate_similarity(cls, query: str, name: str) -> float:
        """Calculate similarity score between query and name."""
        # Exact match
        if query == name:
            return 1.0
        
        # Substring match
        if query in name or name in query:
            return 0.9
        
        # Fuzzy match
        return SequenceMatcher(None, query, name).ratio()
    
    @classmethod
    def suggest_symbols(cls, query: str) -> List[str]:
        """
        Get symbol suggestions for a query.
        
        Args:
            query: Partial company name or keyword
            
        Returns:
            List of suggested symbols
            
        Examples:
            >>> SymbolLookup.suggest_symbols("bank")
            ['HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', ...]
        """
        results = cls.search(query, limit=10)
        return [symbol for _, symbol, _ in results]
    
    @classmethod
    def get_company_name(cls, symbol: str) -> Optional[str]:
        """
        Get company name from symbol (reverse lookup).
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Company name or None if not found
        """
        symbol = symbol.upper()
        
        # Check user map first
        user_map = cls._load_user_map()
        for name, sym in user_map.items():
            if sym.upper() == symbol:
                return name.title()
        
        # Then check built-in map
        for name, sym in cls.SYMBOL_MAP.items():
            if sym.upper() == symbol:
                return name.title()
        
        return None
    
    @classmethod
    def search_online(cls, query: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        """
        Search for symbols online using yfinance when local map doesn't have results.
        
        Args:
            query: Company name or keyword
            limit: Maximum number of results
            
        Returns:
            List of tuples (company_name, symbol, similarity_score)
        """
        try:
            import yfinance as yf
            
            # Try to find the ticker using yfinance search
            # yfinance doesn't have a direct search API, so we'll try common patterns
            results = []
            
            # Try the query as-is (might be a symbol)
            query_upper = query.upper()
            try:
                ticker = yf.Ticker(query_upper)
                info = ticker.info
                if info and 'symbol' in info:
                    company_name = info.get('longName') or info.get('shortName') or query
                    results.append((company_name.lower(), info['symbol'], 1.0))
            except:
                pass
            
            # Try with common exchange suffixes for international stocks
            if not results and len(query_upper) <= 10:
                suffixes = ['.NS', '.BO', '.L', '.TO', '.AX', '.HK', '.SS', '.SZ']
                for suffix in suffixes:
                    try:
                        test_symbol = query_upper + suffix
                        ticker = yf.Ticker(test_symbol)
                        info = ticker.info
                        if info and 'symbol' in info and info.get('regularMarketPrice'):
                            company_name = info.get('longName') or info.get('shortName') or query
                            results.append((company_name.lower(), info['symbol'], 0.9))
                            if len(results) >= limit:
                                break
                    except:
                        continue
            
            return results[:limit]
            
        except ImportError:
            logger.warning("yfinance not installed - online search unavailable")
            return []
        except Exception as e:
            logger.error(f"Error searching online: {e}")
            return []
    
    @classmethod
    def search_with_fallback(cls, query: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        """
        Search for symbols in local map first, then fall back to online search.
        
        Args:
            query: Company name or keyword
            limit: Maximum number of results
            
        Returns:
            List of tuples (company_name, symbol, similarity_score)
        """
        # First try local search (built-in + user maps)
        local_results = cls.search(query, limit)
        
        # If we have excellent local results (similarity > 0.8), return them
        # Lower threshold means we're more likely to search online
        if local_results and local_results[0][2] > 0.8:
            return local_results
        
        # Otherwise, try online search
        logger.info(f"No excellent local matches for '{query}' (best: {local_results[0][2] if local_results else 0:.2f}), searching online...")
        online_results = cls.search_online(query, limit)
        
        # Combine results, prioritizing online matches (they're more likely to be what user wants)
        combined = online_results + local_results
        
        # Remove duplicates (same symbol)
        seen_symbols = set()
        unique_results = []
        for name, symbol, score in combined:
            if symbol.upper() not in seen_symbols:
                seen_symbols.add(symbol.upper())
                unique_results.append((name, symbol, score))
        
        return unique_results[:limit]
    
    @classmethod
    def save_user_symbol(cls, company_name: str, symbol: str) -> None:
        """
        Save a user-selected symbol mapping for future use.
        
        Args:
            company_name: Company name or search term
            symbol: Stock ticker symbol
        """
        try:
            # Load existing user map
            user_map = cls._load_user_map()
            
            # Add new mapping (normalized to lowercase)
            user_map[company_name.lower().strip()] = symbol.upper()
            
            # Save to file
            cls.USER_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.USER_MAP_PATH, 'w') as f:
                json.dump(user_map, f, indent=2)
            
            logger.info(f"Saved user symbol mapping: {company_name} -> {symbol}")
            
        except Exception as e:
            logger.error(f"Error saving user symbol: {e}")
    
    @classmethod
    def _load_user_map(cls) -> Dict[str, str]:
        """Load user's custom symbol mappings from disk."""
        try:
            if cls.USER_MAP_PATH.exists():
                with open(cls.USER_MAP_PATH, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading user map: {e}")
        
        return {}
    
    @classmethod
    def search(cls, query: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        """
        Search for multiple matching symbols with similarity scores.
        
        Searches both built-in map and user's custom mappings.
        
        Args:
            query: Company name or keyword
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (company_name, symbol, similarity_score)
            sorted by similarity score (highest first)
            
        Examples:
            >>> SymbolLookup.search("bank", limit=3)
            [('hdfc bank', 'HDFCBANK.NS', 0.85),
             ('icici bank', 'ICICIBANK.NS', 0.82),
             ('axis bank', 'AXISBANK.NS', 0.80)]
        """
        if not query:
            return []
        
        query = query.lower().strip()
        results = []
        
        # Search user map first (higher priority)
        user_map = cls._load_user_map()
        for name, symbol in user_map.items():
            similarity = cls._calculate_similarity(query, name)
            if similarity > 0.3:  # Minimum threshold
                results.append((name, symbol, similarity + 0.1))  # Boost user mappings
        
        # Then search built-in map
        for name, symbol in cls.SYMBOL_MAP.items():
            similarity = cls._calculate_similarity(query, name)
            if similarity > 0.3:  # Minimum threshold
                results.append((name, symbol, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results[:limit]


# Convenience functions
def lookup_symbol(query: str) -> Optional[str]:
    """Lookup a stock symbol from company name or keyword."""
    return SymbolLookup.lookup(query)


def search_symbols(query: str, limit: int = 5) -> List[Tuple[str, str, float]]:
    """Search for matching symbols with similarity scores."""
    return SymbolLookup.search(query, limit)


def suggest_symbols(query: str) -> List[str]:
    """Get symbol suggestions for a query."""
    return SymbolLookup.suggest_symbols(query)
