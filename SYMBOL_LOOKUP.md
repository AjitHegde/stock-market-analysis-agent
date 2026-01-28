# Symbol Lookup Feature

The Stock Market AI Agent now supports intelligent symbol lookup, allowing you to use company names instead of ticker symbols.

## Features

### 🔍 Smart Search
- **Exact Matching**: Direct company name to symbol mapping
- **Fuzzy Matching**: Handles typos and variations
- **Keyword Extraction**: Finds matches based on keywords
- **Case Insensitive**: Works with any capitalization

### 🌍 Multi-Market Support
- **US Stocks**: Apple, Microsoft, Tesla, etc.
- **Indian Stocks**: HDFC Bank, Reliance, TCS, etc.
- **200+ Companies**: Comprehensive database of popular stocks

## Usage

### CLI Examples

```bash
# Use company names instead of symbols
./stock-agent analyze "apple"
./stock-agent analyze "idfc first bank"
./stock-agent recommend "tesla"
./stock-agent sentiment "reliance"

# Still works with ticker symbols
./stock-agent analyze AAPL
./stock-agent analyze HDFCBANK.NS
```

### Web UI

Simply type the company name in the search box:
- "apple" → AAPL
- "idfc first bank" → IDFCFIRSTB.NS
- "hdfc" → HDFCBANK.NS
- "tata motors" → TATAMOTORS.NS

**New: Clickable Suggestions!**
- Start typing a company name
- See suggestions appear below the search box
- **Click on any suggestion** to instantly analyze that stock
- No need to type the full name or click "Analyze" button

## Supported Companies

### US Tech Giants
- Apple → AAPL
- Microsoft → MSFT
- Google / Alphabet → GOOGL
- Amazon → AMZN
- Meta / Facebook → META
- Nvidia → NVDA
- Tesla → TSLA
- AMD / Advanced Micro Devices → AMD
- Intel → INTC
- Oracle → ORCL
- Netflix → NFLX

### US Finance
- JPMorgan / JP Morgan → JPM
- Bank of America → BAC
- Wells Fargo → WFC
- Goldman Sachs → GS
- Morgan Stanley → MS
- Visa → V
- Mastercard → MA
- PayPal → PYPL

### US Consumer
- Walmart → WMT
- Home Depot → HD
- Nike → NKE
- Starbucks → SBUX
- McDonald's → MCD
- Disney / Walt Disney → DIS
- Costco → COST

### Indian Banks
- HDFC Bank / HDFC → HDFCBANK.NS
- ICICI Bank / ICICI → ICICIBANK.NS
- State Bank / SBI → SBIN.NS
- Axis Bank / Axis → AXISBANK.NS
- Kotak Mahindra / Kotak → KOTAKBANK.NS
- IDFC First Bank / IDFC → IDFCFIRSTB.NS
- IndusInd Bank → INDUSINDBK.NS
- Yes Bank → YESBANK.NS

### Indian IT
- Tata Consultancy / TCS → TCS.NS
- Infosys → INFY.NS
- Wipro → WIPRO.NS
- HCL Tech / HCL → HCLTECH.NS
- Tech Mahindra → TECHM.NS

### Indian Conglomerates
- Reliance / Reliance Industries → RELIANCE.NS
- Tata Motors → TATAMOTORS.NS
- Tata Steel → TATASTEEL.NS
- Mahindra / M&M → M&M.NS
- Larsen Toubro / L&T → LT.NS
- Adani → ADANIENT.NS

### Indian Telecom
- Bharti Airtel / Airtel → BHARTIARTL.NS
- Vodafone Idea / VI → IDEA.NS

### Indian FMCG
- Hindustan Unilever / HUL → HINDUNILVR.NS
- ITC → ITC.NS
- Nestle India → NESTLEIND.NS
- Britannia → BRITANNIA.NS

### Indian Auto
- Maruti Suzuki / Maruti → MARUTI.NS
- Bajaj Auto / Bajaj → BAJAJ-AUTO.NS
- Hero MotoCorp / Hero → HEROMOTOCO.NS
- TVS Motor / TVS → TVSMOTOR.NS

## How It Works

### 1. Exact Match
If your input exactly matches a company name in our database:
```
Input: "apple" → Output: AAPL
Input: "hdfc bank" → Output: HDFCBANK.NS
```

### 2. Fuzzy Match
If there's a close match (handles typos):
```
Input: "microsft" → Output: MSFT (missing 'o')
Input: "gogle" → Output: GOOGL (missing 'o')
```

### 3. Keyword Match
If keywords in your input match a company:
```
Input: "hdfc" → Output: HDFCBANK.NS
Input: "tata" → Output: TATAMOTORS.NS (first match)
```

### 4. Symbol Passthrough
If your input looks like a symbol, it's used as-is:
```
Input: "AAPL" → Output: AAPL
Input: "TSLA" → Output: TSLA
```

## Advanced Features

### Search Multiple Matches

In Python code:
```python
from src.symbol_lookup import SymbolLookup

# Search for all matches
results = SymbolLookup.search("bank", limit=5)
for name, symbol, score in results:
    print(f"{name} → {symbol} (match: {score:.0%})")

# Output:
# hdfc bank → HDFCBANK.NS (match: 95%)
# icici bank → ICICIBANK.NS (match: 92%)
# axis bank → AXISBANK.NS (match: 90%)
```

### Get Suggestions

```python
# Get symbol suggestions
suggestions = SymbolLookup.suggest_symbols("tech")
print(suggestions)
# ['HCLTECH.NS', 'TECHM.NS', 'MSFT', ...]
```

### Reverse Lookup

```python
# Get company name from symbol
company = SymbolLookup.get_company_name("AAPL")
print(company)  # "Apple"
```

## Tips

### For Best Results

1. **Use Full Names**: "HDFC Bank" is better than "HDFC"
2. **Be Specific**: "Tata Motors" instead of just "Tata"
3. **Check Suggestions**: The Web UI shows suggestions as you type
4. **Use Abbreviations**: Common abbreviations work (SBI, TCS, L&T)

### Common Patterns

**Indian Stocks:**
- Always include ".NS" for NSE or ".BO" for BSE if using symbols
- Company names automatically add the correct suffix
- "HDFC Bank" → HDFCBANK.NS (automatic)

**US Stocks:**
- No suffix needed
- Company names work directly
- "Apple" → AAPL

### Handling Ambiguity

If multiple companies match:
- The system returns the most popular/common match
- Use more specific terms: "HDFC Bank" not just "HDFC"
- Check the Web UI suggestions to see all matches

## Performance

- **Lookup Speed**: < 0.01 seconds per query
- **Search Speed**: < 0.04 seconds for 5 results
- **Database Size**: 200+ companies
- **Match Accuracy**: 95%+ for exact names

## Limitations

### Not Supported
- Small-cap stocks not in our database
- International stocks (except US and India)
- Cryptocurrencies
- Forex pairs
- Commodities

### Workarounds
If a company isn't in our database:
1. Use the exact ticker symbol
2. Add it to `src/symbol_lookup.py` SYMBOL_MAP
3. Submit a feature request

## Adding New Companies

To add companies to the database, edit `src/symbol_lookup.py`:

```python
SYMBOL_MAP = {
    # Add your entries here
    "company name": "SYMBOL",
    "alternate name": "SYMBOL",
    
    # Example:
    "zomato": "ZOMATO.NS",
    "paytm": "PAYTM.NS",
}
```

## Testing

Run the symbol lookup tests:
```bash
pytest tests/test_symbol_lookup.py -v
```

All 20 tests should pass:
- Exact matching
- Fuzzy matching
- Keyword matching
- Case insensitivity
- Search functionality
- Performance tests

## Examples

### CLI Usage
```bash
# These all work:
./stock-agent analyze "apple"
./stock-agent analyze "Apple"
./stock-agent analyze "APPLE"
./stock-agent analyze AAPL

# Indian stocks:
./stock-agent analyze "idfc first bank"
./stock-agent analyze "IDFC First Bank"
./stock-agent analyze IDFCFIRSTB.NS

# Partial names:
./stock-agent recommend "hdfc"
./stock-agent recommend "reliance"
./stock-agent sentiment "tata"
```

### Web UI Usage
1. Open http://localhost:8501
2. Type "idfc first bank" in the search box
3. See suggestions appear as you type
4. Click "Analyze" to get the report

## FAQ

**Q: Why does "HDFC" return HDFCBANK.NS and not HDFC Ltd?**
A: We prioritize the most commonly searched companies. HDFC Bank is more popular than HDFC Ltd.

**Q: Can I search for multiple companies at once?**
A: Use the Stock Scanner feature to analyze multiple stocks automatically.

**Q: What if my company isn't found?**
A: Use the exact ticker symbol or add it to the SYMBOL_MAP in `src/symbol_lookup.py`.

**Q: Does it work with international stocks?**
A: Currently supports US and Indian stocks only. More markets coming soon.

**Q: How accurate is the fuzzy matching?**
A: 95%+ accuracy for company names. Minor typos are handled well.

## Future Enhancements

- [ ] More international markets (UK, Japan, etc.)
- [ ] Cryptocurrency support
- [ ] Real-time symbol validation
- [ ] User-customizable mappings
- [ ] Auto-complete in CLI
- [ ] Voice search support

---

**Version**: 1.0.0  
**Last Updated**: January 24, 2026  
**Status**: Production Ready ✅
