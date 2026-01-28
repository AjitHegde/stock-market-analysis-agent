# Implementation Plan: News-Driven Stock Discovery

## Overview

This implementation plan converts the news-driven stock discovery design into discrete coding tasks. The approach focuses on building the core news discovery module first, then integrating it with the existing CLI and Web UI interfaces. Each task builds incrementally on previous work, with testing integrated throughout to catch errors early.

## Tasks

- [x] 1. Create news discovery module structure
  - Create `src/news_discovery.py` file with NewsDiscovery class skeleton
  - Create `src/symbol_extractor.py` file with SymbolExtractor class skeleton
  - Define data models: NewsArticle (if not exists), SymbolMention, DiscoveredStock
  - _Requirements: 1.1, 2.1_

- [ ] 2. Implement news fetching functionality
  - [x] 2.1 Implement NewsDiscovery._fetch_news method
    - Query NewsAPI, Yahoo Finance, and Finnhub using existing DataProvider methods
    - Handle provider failures gracefully (log and continue)
    - Normalize article formats from different providers into unified NewsArticle format
    - Filter articles by time range (hours_back parameter)
    - _Requirements: 1.1, 1.2, 1.3, 1.5_
  
  - [ ]* 2.2 Write property test for news fetching
    - **Property 1: News Time Range Accuracy**
    - **Validates: Requirements 1.1**
  
  - [ ]* 2.3 Write property test for multi-provider query
    - **Property 2: Multi-Provider Query**
    - **Validates: Requirements 1.2**
  
  - [ ]* 2.4 Write property test for provider failure resilience
    - **Property 3: Provider Failure Resilience**
    - **Validates: Requirements 1.3, 9.1**
  
  - [ ]* 2.5 Write unit tests for news fetching edge cases
    - Test empty news results from all providers
    - Test NewsAPI rate limit error handling
    - Test all providers failing scenario
    - _Requirements: 1.3, 1.5, 9.4_

- [ ] 3. Implement symbol extraction functionality
  - [x] 3.1 Implement SymbolExtractor._find_ticker_symbols method
    - Use regex pattern `\b[A-Z]{1,5}\b` to find ticker symbols
    - Filter out common English words (THE, AND, OR, etc.)
    - Extract from both title and description fields
    - _Requirements: 2.1, 2.2, 2.5_
  
  - [x] 3.2 Implement SymbolExtractor._find_company_names method
    - Search for known company names from SymbolLookup
    - Use case-insensitive matching
    - Map company names to stock symbols
    - _Requirements: 2.3, 2.4_
  
  - [x] 3.3 Implement SymbolExtractor.extract_from_text method
    - Combine ticker symbol and company name extraction
    - Return deduplicated set of symbols
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ]* 3.4 Write property test for comprehensive text extraction
    - **Property 4: Comprehensive Text Extraction**
    - **Validates: Requirements 2.1, 2.5**
  
  - [ ]* 3.5 Write property test for ticker symbol pattern recognition
    - **Property 5: Ticker Symbol Pattern Recognition**
    - **Validates: Requirements 2.2**
  
  - [ ]* 3.6 Write property test for company name mapping
    - **Property 6: Company Name to Symbol Mapping**
    - **Validates: Requirements 2.3, 2.4**
  
  - [ ]* 3.7 Write unit tests for symbol extraction edge cases
    - Test article with no symbols returns empty set
    - Test symbol in title but not description is extracted
    - Test common English words are filtered out
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 4. Checkpoint - Ensure extraction tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement symbol validation and prioritization
  - [x] 5.1 Implement NewsDiscovery._extract_symbols method
    - Parse all articles and extract symbols using SymbolExtractor
    - Track mention count per symbol
    - Track which sources mentioned each symbol
    - Handle extraction errors gracefully (skip article and continue)
    - _Requirements: 2.1, 3.3, 9.2_
  
  - [x] 5.2 Implement NewsDiscovery._validate_and_prioritize method
    - Deduplicate symbols
    - Validate symbols against SymbolLookup registry
    - Calculate priority score: (mention_count * 2) + (unique_sources * 3)
    - Sort by priority score descending
    - Limit to max_symbols (default 50)
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 6.1, 6.2_
  
  - [ ]* 5.3 Write property test for symbol deduplication
    - **Property 7: Symbol Deduplication**
    - **Validates: Requirements 3.1**
  
  - [ ]* 5.4 Write property test for symbol validation
    - **Property 8: Symbol Validation Filter**
    - **Validates: Requirements 3.2, 3.5**
  
  - [ ]* 5.5 Write property test for mention count accuracy
    - **Property 9: Mention Count Accuracy**
    - **Validates: Requirements 3.3**
  
  - [ ]* 5.6 Write property test for mention-based prioritization
    - **Property 10: Mention-Based Prioritization**
    - **Validates: Requirements 3.4**
  
  - [ ]* 5.7 Write property test for symbol limit enforcement
    - **Property 15: Symbol Limit Enforcement**
    - **Validates: Requirements 6.1**
  
  - [ ]* 5.8 Write unit tests for validation edge cases
    - Test all invalid symbols are filtered out
    - Test prioritization with equal mention counts
    - Test limiting to max_symbols when more are discovered
    - _Requirements: 3.2, 3.4, 6.1, 6.2_

- [ ] 6. Implement main discovery orchestration
  - [x] 6.1 Implement NewsDiscovery.discover_stocks method
    - Call _fetch_news to get articles
    - Call _extract_symbols to get symbol mentions
    - Call _validate_and_prioritize to get final symbol list
    - Return list of DiscoveredStock objects with metadata
    - _Requirements: 1.1, 2.1, 3.1, 3.2, 3.4_
  
  - [ ]* 6.2 Write property test for extraction error resilience
    - **Property 18: Extraction Error Resilience**
    - **Validates: Requirements 9.2**
  
  - [ ]* 6.3 Write unit tests for discovery orchestration
    - Test end-to-end discovery with mock news data
    - Test discovery with no valid symbols found
    - Test discovery with all providers failing
    - _Requirements: 1.1, 9.4_

- [x] 7. Checkpoint - Ensure discovery module tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement stock analysis integration
  - [x] 8.1 Create analyze_discovered_stocks function
    - Accept list of DiscoveredStock objects
    - Call agent_core.analyze_stock for each symbol
    - Handle analysis errors gracefully (log and continue)
    - Return list of AnalysisResult objects
    - _Requirements: 4.1, 9.3_
  
  - [x] 8.2 Implement recommendation filtering
    - Filter results to include only BUY or SELL recommendations
    - Exclude HOLD recommendations
    - Sort by confidence score descending, then mention count descending
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  
  - [ ]* 8.3 Write property test for analysis pipeline integration
    - **Property 11: Analysis Pipeline Integration**
    - **Validates: Requirements 4.1**
  
  - [ ]* 8.4 Write property test for actionable recommendation filtering
    - **Property 12: Actionable Recommendation Filtering**
    - **Validates: Requirements 5.1, 5.2**
  
  - [ ]* 8.5 Write property test for confidence-based sorting
    - **Property 13: Confidence-Based Sorting**
    - **Validates: Requirements 5.3**
  
  - [ ]* 8.6 Write property test for multi-criteria result sorting
    - **Property 14: Multi-Criteria Result Sorting**
    - **Validates: Requirements 5.5**
  
  - [ ]* 8.7 Write property test for analysis error resilience
    - **Property 19: Analysis Error Resilience**
    - **Validates: Requirements 9.3**
  
  - [ ]* 8.8 Write unit tests for analysis integration
    - Test filtering removes HOLD recommendations
    - Test sorting by confidence and mention count
    - Test handling of analysis failures for individual stocks
    - Test no actionable recommendations scenario
    - _Requirements: 5.1, 5.4, 9.3_

- [ ] 9. Integrate with CLI scan command
  - [x] 9.1 Modify cli.py scan command
    - Check if explicit symbols provided (backward compatibility)
    - If no symbols, use NewsDiscovery to discover stocks
    - Display discovered symbols before analysis
    - Show progress indicators during discovery and analysis
    - Display results in formatted table with symbol, recommendation, confidence, mention count
    - Show summary of total stocks discovered and analyzed
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 10.3_
  
  - [ ]* 9.2 Write property test for CLI output completeness
    - **Property 16: CLI Output Completeness**
    - **Validates: Requirements 7.4**
  
  - [ ]* 9.3 Write property test for summary count accuracy
    - **Property 17: Summary Count Accuracy**
    - **Validates: Requirements 7.5**
  
  - [ ]* 9.4 Write unit tests for CLI integration
    - Test scan with no arguments uses news discovery
    - Test scan with explicit symbols bypasses news discovery
    - Test CLI output contains all required fields
    - Test summary counts match actual discovered/analyzed stocks
    - _Requirements: 7.1, 7.4, 7.5, 10.3_

- [ ] 10. Integrate with Web UI scan page
  - [x] 10.1 Modify web_ui.py scan_stocks_page function
    - Add button to trigger news-driven discovery
    - Display loading indicator during scan
    - Show discovered symbols before analysis
    - Display results in sortable table with symbol, recommendation, confidence, mentions
    - Allow clicking on symbols for detailed analysis
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ]* 10.2 Write unit tests for Web UI integration
    - Test scan button triggers news discovery
    - Test results table contains all required fields
    - Test clicking symbol navigates to detailed analysis
    - _Requirements: 8.1, 8.4, 8.5_

- [ ] 11. Test backward compatibility
  - [ ]* 11.1 Write unit tests for existing commands
    - Test analyze command still works unchanged
    - Test recommend command still works unchanged
    - Test scan with explicit symbols still works
    - Test Web UI single-stock analysis still works
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The existing analysis pipeline (sentiment, technical, fundamental) remains unchanged
- Backward compatibility is maintained for all existing commands
