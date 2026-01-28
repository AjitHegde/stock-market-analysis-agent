# Bug Fix: View Details Button Not Working in Scanner ✅ FIXED

## Issue Description
In the web UI scanner page, after stocks are discovered from news, each stock card has a "View Details" button. Clicking this button does nothing - it should navigate to the stock analysis page or display detailed information about the selected stock.

## Status: ✅ FIXED - READY FOR TESTING

## Solution Implemented
Fixed the "View Details" button by:

1. **Added page navigation key**: Added `key="current_page"` to the `st.radio` navigation widget to make it controllable via session state
2. **Updated button callback**: Modified the "View Details" button to:
   - Set `st.session_state.selected_symbol` to the clicked stock symbol
   - Set `st.session_state.trigger_analysis = True` to trigger analysis
   - Set `st.session_state.current_page = "📊 Stock Analysis"` to navigate to analysis page
   - Call `st.rerun()` to refresh the UI

## Changes Made
**File**: `src/web_ui.py`

**Change 1** (Lines ~677-686): Added session state key to navigation radio
```python
# Initialize page in session state if not present
if 'current_page' not in st.session_state:
    st.session_state.current_page = "📊 Stock Analysis"

page = st.radio(
    "Navigation",
    ["📊 Stock Analysis", "🔍 Stock Scanner", "ℹ️ About"],
    key="current_page",  # Added this key
    label_visibility="collapsed"
)
```

**Change 2** (Lines ~649-655): Fixed View Details button callback
```python
if st.button(f"View Details", key=f"details_{symbol}"):
    # Set the symbol to analyze
    st.session_state.selected_symbol = symbol
    st.session_state.trigger_analysis = True
    # Navigate to the analysis page
    st.session_state.current_page = "📊 Stock Analysis"
    st.rerun()
```

## Location
- **File**: `src/web_ui.py`
- **Function**: `scan_stocks_page()` 
- **Component**: Stock recommendation cards in the scanner results

## Expected Behavior
When a user clicks "View Details" on a discovered stock:
1. Should navigate to the stock analysis page with that symbol pre-loaded
2. OR display a detailed analysis modal/expander with full stock information
3. Should provide the same level of detail as the main "Analyze Stock" page

## Current Behavior
- Button click has no effect
- No navigation occurs
- No error messages displayed

## Root Cause (To Investigate)
Likely causes:
1. Button callback not properly connected to navigation logic
2. Missing session state update to trigger analysis
3. Button key conflicts causing Streamlit to ignore the click
4. Missing `st.rerun()` after state change

## Proposed Solution
1. Find the "View Details" button in `scan_stocks_page()`
2. Add proper session state management:
   ```python
   if st.button("View Details", key=f"view_{symbol}"):
       st.session_state.selected_symbol = symbol
       st.session_state.trigger_analysis = True
       st.session_state.page = "analyze"  # If using page navigation
       st.rerun()
   ```
3. Ensure the button navigates to the analysis page or triggers full analysis

## Testing Steps
1. ✅ Web UI restarted with updated code (running at http://localhost:8501)
2. Go to "🔍 Stock Scanner" page
3. Click "🚀 Start News Scan" to discover stocks
4. Click "View Details" on any discovered stock
5. Verify that:
   - Navigation switches to "📊 Stock Analysis" page
   - The selected stock symbol is loaded
   - Analysis is triggered automatically

## Next Steps
- User needs to test the "View Details" button functionality
- If still not working, investigate:
  * Check browser console for JavaScript errors
  * Verify session state is persisting correctly
  * Add debug logging to button callback
  * Consider alternative navigation approach

## Priority
**Medium** - Feature exists but is non-functional, impacts user experience

## Related Files
- `src/web_ui.py` - Main web UI file with scanner page
- `src/agent_core.py` - Stock analysis logic (may need to be called)

## Notes
- This is part of the news-driven stock discovery feature
- The scanner successfully discovers and displays stocks
- Only the "View Details" interaction is broken
