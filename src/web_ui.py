"""
Interactive web UI for the Stock Market AI Agent using Streamlit.

This module provides a web-based interface for analyzing stocks, viewing recommendations,
checking sentiment, and assessing portfolio risk.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.agent_core import AgentCore
from src.config import Configuration
from src.models import Position
from src.symbol_lookup import SymbolLookup
from src.auth import Authenticator, show_logout_button


# Page configuration
st.set_page_config(
    page_title="Stock Market AI Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .disclaimer-box {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .buy-action {
        color: #28a745;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .sell-action {
        color: #dc3545;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .hold-action {
        color: #ffc107;
        font-weight: bold;
        font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


def display_disclaimer():
    """Display startup disclaimer."""
    st.markdown("""
    <div class="disclaimer-box">
        <h3>⚠️ IMPORTANT DISCLAIMER</h3>
        <p>This Stock Market AI Agent is provided for <strong>EDUCATIONAL and INFORMATIONAL PURPOSES ONLY</strong>.</p>
        <ul>
            <li>This tool is NOT financial advice</li>
            <li>Past performance does not guarantee future results</li>
            <li>All investment decisions carry risk</li>
            <li>Consult with qualified financial professionals before making investment decisions</li>
            <li>The creators assume no liability for financial losses</li>
        </ul>
        <p><em>By using this tool, you acknowledge these limitations and agree to use it responsibly.</em></p>
    </div>
    """, unsafe_allow_html=True)


def get_action_color(action: str) -> str:
    """Get color for action."""
    colors = {
        "BUY": "#28a745",
        "SELL": "#dc3545",
        "HOLD": "#ffc107"
    }
    return colors.get(action, "#6c757d")


def get_currency_symbol(symbol: str) -> tuple:
    """Get currency symbol and name based on stock symbol."""
    if symbol.endswith('.NS') or symbol.endswith('.BO'):
        return "₹", "INR"
    return "$", "USD"


def create_price_chart(historical_prices, symbol: str):
    """Create interactive price chart with technical indicators."""
    if not historical_prices:
        return None
    
    # Prepare data
    dates = [p.date for p in historical_prices]
    closes = [p.close for p in historical_prices]
    volumes = [p.volume for p in historical_prices]
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{symbol} Price History', 'Volume'),
        row_heights=[0.7, 0.3]
    )
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=dates,
            open=[p.open for p in historical_prices],
            high=[p.high for p in historical_prices],
            low=[p.low for p in historical_prices],
            close=closes,
            name='Price'
        ),
        row=1, col=1
    )
    
    # Add volume bars
    fig.add_trace(
        go.Bar(x=dates, y=volumes, name='Volume', marker_color='lightblue'),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=600,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig


def generate_plain_english_summary(result) -> str:
    """Generate a plain English summary of the analysis."""
    action = result.recommendation.action
    confidence = result.recommendation.confidence
    sentiment_score = result.sentiment.sentiment_score
    technical_score = result.technical.technical_score
    fundamental_score = result.fundamental.fundamental_score
    
    # Determine action phrase
    if action == "BUY":
        action_phrase = "Consider buying"
        action_advice = "This looks like a good opportunity to enter a position."
    elif action == "SELL":
        action_phrase = "Consider selling"
        action_advice = "This might be a good time to exit or reduce your position."
    else:  # HOLD
        action_phrase = "Hold off for now"
        action_advice = "Wait for clearer signals before making a move."
    
    # Determine confidence phrase
    if confidence > 0.7:
        confidence_phrase = "high confidence"
    elif confidence > 0.4:
        confidence_phrase = "moderate confidence"
    else:
        confidence_phrase = "low confidence"
    
    # Analyze sentiment
    if sentiment_score > 0.3:
        sentiment_phrase = "News and social media are positive"
    elif sentiment_score < -0.3:
        sentiment_phrase = "News and social media are negative"
    else:
        sentiment_phrase = "News sentiment is neutral"
    
    # Analyze technicals
    if technical_score > 0.3:
        technical_phrase = "price momentum is strong"
    elif technical_score < -0.3:
        technical_phrase = "price momentum is weak"
    else:
        technical_phrase = "price action is mixed"
    
    # Analyze fundamentals
    if fundamental_score > 0.3:
        fundamental_phrase = "fundamentals look solid"
    elif fundamental_score < -0.3:
        fundamental_phrase = "fundamentals are concerning"
    else:
        fundamental_phrase = "fundamentals are average"
    
    # Build summary
    summary = f"{action_phrase} {result.recommendation.symbol} with {confidence_phrase} ({confidence:.0%}).\n\n"
    summary += f"{sentiment_phrase}, {technical_phrase}, and {fundamental_phrase}. "
    summary += f"{action_advice}"
    
    # Add specific concerns or highlights
    if action == "HOLD":
        if abs(sentiment_score - technical_score) > 0.5 or abs(sentiment_score - fundamental_score) > 0.5:
            summary += "\n\nThe signals are mixed - some indicators are positive while others are negative. "
            summary += "It's best to wait for more alignment before taking action."
    
    return summary


def analyze_stock_page():
    """Stock analysis page."""
    st.markdown('<h1 class="main-header">📊 Stock Analysis</h1>', unsafe_allow_html=True)
    
    # Initialize session state for selected symbol
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = ""
    if 'trigger_analysis' not in st.session_state:
        st.session_state.trigger_analysis = False
    
    # Input section
    col1, col2 = st.columns([3, 1])
    with col1:
        # Use session state for the input value
        user_input = st.text_input(
            "Enter Stock Symbol or Company Name",
            value=st.session_state.selected_symbol,
            placeholder="e.g., AAPL, Tesla, HDFC Bank, Reliance",
            help="Enter a stock ticker symbol or company name. For Indian stocks, you can use company names like 'HDFC Bank' or 'Reliance'.",
            key="stock_input"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    # Show suggestions if user is typing
    if user_input and not analyze_button and not st.session_state.trigger_analysis:
        # Use search_with_fallback to include online results
        suggestions = SymbolLookup.search_with_fallback(user_input, limit=5)
        if suggestions and len(user_input) > 2:
            # Check if we have online results (indicated by lower scores or specific markers)
            has_online = any(score < 0.6 for _, _, score in suggestions)
            if has_online:
                st.info("💡 **Suggestions (including online search):**")
            else:
                st.info("💡 **Click on a suggestion to analyze:**")
            
            # Create clickable buttons for each suggestion
            cols = st.columns(1)
            for idx, (name, symbol, score) in enumerate(suggestions):
                with cols[0]:
                    # Create a button for each suggestion with unique key using index
                    button_label = f"📊 {name.title()} → {symbol} (match: {score:.0%})"
                    if st.button(button_label, key=f"suggest_{idx}_{symbol}", use_container_width=True):
                        # Save this user selection for future searches
                        SymbolLookup.save_user_symbol(user_input, symbol)
                        
                        # Set the selected symbol and trigger analysis
                        st.session_state.selected_symbol = symbol
                        st.session_state.selected_company_name = name
                        st.session_state.trigger_analysis = True
                        st.rerun()
    
    # Check if we should analyze (either button clicked or suggestion selected)
    should_analyze = analyze_button or st.session_state.trigger_analysis
    
    if should_analyze and user_input:
        # Reset trigger flag
        st.session_state.trigger_analysis = False
        
        # If a suggestion was selected, use the selected symbol directly
        # Otherwise, lookup symbol from user input
        if st.session_state.selected_symbol and st.session_state.selected_symbol != user_input:
            # User clicked a suggestion - use the pre-selected symbol
            symbol = st.session_state.selected_symbol
        else:
            # User typed and clicked analyze - lookup the symbol
            symbol = SymbolLookup.lookup(user_input)
        
        if not symbol:
            st.error("❌ Could not find a matching stock symbol. Please try a different search term.")
            return
        
        # Show what we're analyzing
        company_name = SymbolLookup.get_company_name(symbol)
        if company_name and company_name.lower() != user_input.lower():
            st.info(f"🔍 Analyzing **{company_name.title()}** ({symbol})")
        
        try:
            # Load configuration and create agent
            config = Configuration()
            agent = AgentCore(config)
            
            # Show progress
            with st.spinner(f"Analyzing {symbol}... This may take a moment."):
                result = agent.analyze_stock(symbol)
            
            # Get currency info
            currency_symbol, currency_name = get_currency_symbol(symbol)
            
            # Success message
            st.success(f"✅ Analysis complete for {symbol}")
            
            # Display data quality banner if issues exist
            if result.data_quality_report and result.data_quality_report.issues:
                report = result.data_quality_report
                
                # Determine banner color based on severity
                if report.has_critical_issues:
                    banner_color = "#dc3545"  # red
                    banner_emoji = "🔴"
                    banner_title = "CRITICAL DATA ISSUES"
                elif any(i.severity == "major" for i in report.issues):
                    banner_color = "#ff8c00"  # orange
                    banner_emoji = "⚠️"
                    banner_title = "DATA QUALITY ISSUES"
                else:
                    banner_color = "#0dcaf0"  # blue
                    banner_emoji = "ℹ️"
                    banner_title = "MINOR DATA ISSUES"
                
                # Build banner HTML
                st.markdown(
                    f'<div style="background-color: {banner_color}20; border: 2px solid {banner_color}; '
                    f'border-radius: 10px; padding: 20px; margin: 20px 0;">'
                    f'<h3 style="color: {banner_color}; margin-top: 0;">{banner_emoji} {banner_title}</h3>'
                    f'<p><strong>Total Confidence Penalty:</strong> <span style="color: {banner_color};">-{report.total_confidence_penalty:.0%}</span></p>'
                    f'<h4>Issues Found:</h4>'
                    f'<ul>',
                    unsafe_allow_html=True
                )
                
                for issue in report.issues:
                    # Severity emoji and color
                    severity_emoji = {"critical": "🔴", "major": "⚠️", "minor": "ℹ️"}.get(issue.severity, "•")
                    severity_color = {"critical": "#dc3545", "major": "#ff8c00", "minor": "#0dcaf0"}.get(issue.severity, "#6c757d")
                    
                    st.markdown(
                        f'<li><strong style="color: {severity_color};">{severity_emoji} {issue.source}</strong><br>'
                        f'<em>Reason:</em> {issue.reason}<br>'
                        f'<em>Impact:</em> {issue.impact}<br>'
                        f'<em>Penalty:</em> -{issue.confidence_penalty:.0%}</li>',
                        unsafe_allow_html=True
                    )
                
                st.markdown('</ul></div>', unsafe_allow_html=True)
            
            # Add help section explaining key concepts
            with st.expander("ℹ️ Understanding the Analysis", expanded=False):
                st.markdown("""
                **Key Concepts:**
                
                - **Score**: Indicates directional bias (positive = bullish, negative = bearish). Measures the strength and direction of the signal.
                
                - **Confidence**: Measures the reliability and data quality of the signal, NOT profit potential. High confidence means we have good data and clear signals, but doesn't guarantee success.
                
                - **Adjusted Score**: The final risk-adjusted directional bias after applying market penalties, no-trade penalties, and volatility adjustments.
                
                - **Agreement Score**: How well the three analyzers (sentiment, technical, fundamental) align with each other.
                
                **Remember**: High confidence + low score = reliable signal to avoid. Low confidence + high score = uncertain opportunity.
                """)
            
            # Display current price
            st.markdown("### 💰 Current Price")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Price", f"{currency_symbol}{result.current_price:.2f} {currency_name}")
            with col2:
                st.metric("Volume", f"{result.volume:,}")
            with col3:
                st.metric("Timestamp", result.stock_data.timestamp.strftime("%Y-%m-%d %H:%M"))
            
            st.divider()
            
            # Display recommendation prominently
            st.markdown("### 🎯 Recommendation")
            action_color = get_action_color(result.recommendation.action)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(
                    f'<div style="background-color: {action_color}20; border-left: 5px solid {action_color}; '
                    f'padding: 20px; border-radius: 5px; text-align: center;">'
                    f'<h1 style="color: {action_color}; margin: 0;">{result.recommendation.action}</h1>'
                    f'<p style="font-size: 1.2rem; margin: 10px 0 0 0;">Confidence: {result.recommendation.confidence:.0%}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                # Add tooltip explanation for confidence
                st.caption("ℹ️ Confidence measures reliability of this signal, not profit potential.")
            
            with col2:
                st.markdown("**Plain English Summary:**")
                st.info(generate_plain_english_summary(result))
            
            st.markdown("**Reasoning:**")
            st.write(result.recommendation.reasoning)
            
            st.divider()
            
            # Three column layout for analysis
            col1, col2, col3 = st.columns(3)
            
            # Sentiment Analysis
            with col1:
                st.markdown("### 📊 Sentiment Analysis")
                sentiment_score = result.sentiment.sentiment_score
                sentiment_color = "#28a745" if sentiment_score > 0.3 else "#dc3545" if sentiment_score < -0.3 else "#ffc107"
                
                st.markdown(
                    f'<div style="background-color: {sentiment_color}20; padding: 15px; border-radius: 5px; border-left: 5px solid {sentiment_color};">'
                    f'<h2 style="color: {sentiment_color}; margin: 0;">{sentiment_score:+.2f}</h2>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                st.metric("Confidence", f"{result.sentiment.confidence:.0%}")
                st.caption("ℹ️ Data quality & reliability")
                st.metric("Sources", len(result.sentiment.sources))
                
                # Source breakdown
                news_count = sum(1 for s in result.sentiment.sources if s.source_type == "news")
                social_count = sum(1 for s in result.sentiment.sources if s.source_type == "social")
                st.write(f"📰 News: {news_count} | 💬 Social: {social_count}")
            
            # Technical Analysis
            with col2:
                st.markdown("### 📈 Technical Analysis")
                tech_score = result.technical.technical_score
                tech_color = "#28a745" if tech_score > 0.3 else "#dc3545" if tech_score < -0.3 else "#ffc107"
                
                st.markdown(
                    f'<div style="background-color: {tech_color}20; padding: 15px; border-radius: 5px; border-left: 5px solid {tech_color};">'
                    f'<h2 style="color: {tech_color}; margin: 0;">{tech_score:+.2f}</h2>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # Market Regime
                regime_emoji_map = {
                    "bullish-trend": "🟢",
                    "bearish-trend": "🔴",
                    "oversold-zone": "🟦",
                    "overbought-zone": "🟧",
                    "consolidation": "🟡"
                }
                regime_name_map = {
                    "bullish-trend": "Bullish Trend",
                    "bearish-trend": "Bearish Trend",
                    "oversold-zone": "Oversold Zone (Potential Reversal)",
                    "overbought-zone": "Overbought Zone (Potential Reversal)",
                    "consolidation": "Consolidation"
                }
                regime = result.technical.regime
                regime_emoji = regime_emoji_map.get(regime, "🟡")
                regime_name = regime_name_map.get(regime, regime.replace("-", " ").title())
                st.metric("Market Regime", f"{regime_emoji} {regime_name}")
                
                # RSI
                rsi_value = result.technical.rsi
                if rsi_value > 70:
                    rsi_label = f"{rsi_value:.2f} (Overbought)"
                elif rsi_value < 30:
                    rsi_label = f"{rsi_value:.2f} (Oversold)"
                else:
                    rsi_label = f"{rsi_value:.2f}"
                st.metric("RSI", rsi_label)
                
                # MACD
                macd_value = result.technical.macd
                macd_label = f"{macd_value:.2f} ({'Bullish' if macd_value > 0 else 'Bearish'})"
                st.metric("MACD", macd_label)
                
                st.caption("RSI: >70 overbought, <30 oversold | MACD: >0 bullish, <0 bearish")
            
            # Fundamental Analysis
            with col3:
                st.markdown("### 💼 Fundamental Analysis")
                fund_score = result.fundamental.fundamental_score
                fund_color = "#28a745" if fund_score > 0.3 else "#dc3545" if fund_score < -0.3 else "#ffc107"
                
                st.markdown(
                    f'<div style="background-color: {fund_color}20; padding: 15px; border-radius: 5px; border-left: 5px solid {fund_color};">'
                    f'<h2 style="color: {fund_color}; margin: 0;">{fund_score:+.2f}</h2>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # P/E Ratio
                if result.fundamental.pe_ratio:
                    pe_value = result.fundamental.pe_ratio
                    if pe_value < 15:
                        pe_label = f"{pe_value:.2f} (Cheap)"
                    elif pe_value > 30:
                        pe_label = f"{pe_value:.2f} (Expensive)"
                    else:
                        pe_label = f"{pe_value:.2f} (Fair)"
                    st.metric("P/E Ratio", pe_label)
                
                # P/B Ratio
                if result.fundamental.pb_ratio:
                    pb_value = result.fundamental.pb_ratio
                    if pb_value < 1:
                        pb_label = f"{pb_value:.2f} (Undervalued)"
                    elif pb_value > 3:
                        pb_label = f"{pb_value:.2f} (Expensive)"
                    else:
                        pb_label = f"{pb_value:.2f} (Fair)"
                    st.metric("P/B Ratio", pb_label)
                
                # Revenue Growth
                if result.fundamental.revenue_growth is not None:
                    growth_value = result.fundamental.revenue_growth
                    if growth_value > 15:
                        growth_label = f"+{growth_value:.1f}% (Strong)"
                    elif growth_value < -10:
                        growth_label = f"{growth_value:.1f}% (Declining)"
                    else:
                        growth_label = f"{growth_value:+.1f}%"
                    st.metric("Revenue Growth", growth_label)
                
                st.caption("P/E: <15 cheap, >30 expensive | P/B: <1 undervalued, >3 expensive")
            
            st.divider()
            
            # Market Context
            if result.market_context:
                st.markdown("### 🌍 Market Context")
                mc = result.market_context
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    nifty_emoji = "🟢" if mc.nifty_trend == "bullish" else "🔴" if mc.nifty_trend == "bearish" else "🟡"
                    st.metric("Nifty 50", f"{nifty_emoji} {mc.nifty_trend.title()}", f"₹{mc.nifty_price:,.0f}")
                
                with col2:
                    bank_emoji = "🟢" if mc.banknifty_trend == "bullish" else "🔴" if mc.banknifty_trend == "bearish" else "🟡"
                    st.metric("Bank Nifty", f"{bank_emoji} {mc.banknifty_trend.title()}", f"₹{mc.banknifty_price:,.0f}")
                
                with col3:
                    vix_emoji = "🟢" if mc.vix_level == "low" else "🟡" if mc.vix_level == "moderate" else "🔴"
                    vix_label = mc.vix_level.replace("_", " ").title()
                    st.metric("India VIX", f"{vix_emoji} {vix_label}", f"{mc.vix_value:.2f}")
                
                with col4:
                    state_emoji = "🟢" if mc.market_state == "BULLISH" else "🔴" if mc.market_state == "BEARISH" else "🟡" if mc.market_state == "NEUTRAL" else "⚠️"
                    st.metric("Market State", f"{state_emoji} {mc.market_state}")
                
                st.divider()
            
            # No-Trade Zone Warning
            if result.no_trade_signal and result.no_trade_signal.is_no_trade:
                severity_color = "#dc3545" if result.no_trade_signal.severity == "high" else "#ff8c00" if result.no_trade_signal.severity == "medium" else "#ffc107"
                
                st.markdown(
                    f'<div style="background-color: {severity_color}20; border: 2px solid {severity_color}; '
                    f'border-radius: 10px; padding: 20px; margin: 20px 0;">'
                    f'<h3 style="color: {severity_color}; margin-top: 0;">⚠️ NO TRADE ZONE ⚠️</h3>'
                    f'<h4>🚫 TRADING DISABLED TODAY</h4>'
                    f'<p><strong>Dangerous Market Conditions Detected:</strong></p>'
                    f'<ul>',
                    unsafe_allow_html=True
                )
                
                for reason in result.no_trade_signal.reasons:
                    st.markdown(f'<li>{reason}</li>', unsafe_allow_html=True)
                
                st.markdown(
                    f'</ul>'
                    f'<p><strong>Suggested Action:</strong></p>'
                    f'<p>{result.no_trade_signal.suggested_action}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                st.divider()
            
            # Confidence Breakdown
            st.markdown("### 🔍 Confidence Breakdown")
            
            # Calculate net impacts for each analyzer (same logic as CLI)
            # Sentiment
            sentiment_impact = result.sentiment.strength * result.sentiment.confidence
            if result.sentiment.direction == "bearish":
                sentiment_impact = -sentiment_impact
            elif result.sentiment.direction == "neutral":
                sentiment_impact = sentiment_impact * 0.3
            
            # Technical
            technical_impact = result.technical.strength * result.technical.confidence
            if result.technical.direction == "bearish":
                technical_impact = -technical_impact
            elif result.technical.direction == "neutral":
                technical_impact = technical_impact * 0.3
            
            # Fundamental
            fundamental_impact = result.fundamental.strength * result.fundamental.confidence
            if result.fundamental.direction == "bearish":
                fundamental_impact = -fundamental_impact
            elif result.fundamental.direction == "neutral":
                fundamental_impact = fundamental_impact * 0.3
            
            # Create DataFrame for the table
            breakdown_data = []
            
            # Sentiment
            sent_dir = result.sentiment.direction
            sent_emoji = "🟢" if sent_dir == "bullish" else "🔴" if sent_dir == "bearish" else "🟡"
            breakdown_data.append({
                "Analyzer": "Sentiment",
                "Direction": f"{sent_emoji} {sent_dir.title()}",
                "Strength": f"{result.sentiment.strength:.0%}",
                "Confidence": f"{result.sentiment.confidence:.0%}",
                "Net Impact": f"{sentiment_impact:+.2f}"
            })
            
            # Technical
            tech_dir = result.technical.direction
            tech_emoji = "🟢" if tech_dir == "bullish" else "🔴" if tech_dir == "bearish" else "🟡"
            breakdown_data.append({
                "Analyzer": "Technical",
                "Direction": f"{tech_emoji} {tech_dir.title()}",
                "Strength": f"{result.technical.strength:.0%}",
                "Confidence": f"{result.technical.confidence:.0%}",
                "Net Impact": f"{technical_impact:+.2f}"
            })
            
            # Fundamental
            fund_dir = result.fundamental.direction
            fund_emoji = "🟢" if fund_dir == "bullish" else "🔴" if fund_dir == "bearish" else "🟡"
            breakdown_data.append({
                "Analyzer": "Fundamental",
                "Direction": f"{fund_emoji} {fund_dir.title()}",
                "Strength": f"{result.fundamental.strength:.0%}",
                "Confidence": f"{result.fundamental.confidence:.0%}",
                "Net Impact": f"{fundamental_impact:+.2f}"
            })
            
            df_breakdown = pd.DataFrame(breakdown_data)
            st.dataframe(df_breakdown, use_container_width=True, hide_index=True)
            
            # Agreement metrics (from confidence_breakdown)
            if result.recommendation.confidence_breakdown:
                breakdown = result.recommendation.confidence_breakdown
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Agreement Score", f"{breakdown.agreement_score:.0%}")
                with col2:
                    st.metric("Market Signal Quality", f"{breakdown.market_signal_quality:.0%}")
                with col3:
                    st.metric("Market Favorability", f"{breakdown.market_favorability:.0%}")
            
            st.divider()
            
            # Active Weights
            st.markdown("### ⚖️ Active Weights")
            
            if result.recommendation.runtime_weights:
                weights = result.recommendation.runtime_weights
                source = weights.get('source', 'unknown')
                
                # Determine display label
                if source.startswith('dynamic-'):
                    market_mode = source.replace('dynamic-', '').title()
                    weight_label = f"{market_mode} Market - Dynamic"
                elif source == 'static':
                    weight_label = "Static (Config Default)"
                else:
                    weight_label = source.title()
                
                st.markdown(f"**{weight_label}**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Sentiment", f"{weights.get('sentiment', 0):.0%}")
                with col2:
                    st.metric("Technical", f"{weights.get('technical', 0):.0%}")
                with col3:
                    st.metric("Fundamental", f"{weights.get('fundamental', 0):.0%}")
            
            st.divider()
            
            # Risk Adjustments
            st.markdown("### 📉 Risk Adjustments")
            
            # Calculate penalties (same logic as CLI)
            breakdown = result.recommendation.confidence_breakdown
            
            # Calculate raw score
            raw_score = (
                result.recommendation.sentiment_contribution +
                result.recommendation.technical_contribution +
                result.recommendation.fundamental_contribution
            )
            
            # Calculate market penalty
            market_penalty = 0.0
            if result.market_context and breakdown:
                if result.market_context.market_state == "BEARISH":
                    market_penalty = -(1.0 - breakdown.market_favorability) * 0.5
                elif result.market_context.market_state == "VOLATILE":
                    market_penalty = -(1.0 - breakdown.market_favorability) * 0.3
                elif result.market_context.market_state == "NEUTRAL":
                    market_penalty = -(1.0 - breakdown.market_favorability) * 0.2
            
            # Calculate no-trade penalty
            no_trade_penalty = 0.0
            if result.no_trade_signal and result.no_trade_signal.is_no_trade:
                if result.no_trade_signal.severity == "high":
                    no_trade_penalty = -0.30
                elif result.no_trade_signal.severity == "medium":
                    no_trade_penalty = -0.20
                else:  # low
                    no_trade_penalty = -0.10
            
            # Calculate volatility penalty
            volatility_penalty = 0.0
            if result.market_context:
                if result.market_context.vix_level == "very_high":
                    volatility_penalty = -0.25
                elif result.market_context.vix_level == "high":
                    volatility_penalty = -0.15
                elif result.market_context.vix_level == "moderate":
                    volatility_penalty = -0.05
            
            # Data quality penalty
            data_penalty = 0.0
            if breakdown:
                data_penalty = -breakdown.data_quality_penalty
            
            penalties = []
            
            # Market penalty
            if market_penalty != 0:
                market_state = result.market_context.market_state if result.market_context else "Unknown"
                penalties.append(("Market Penalty", market_penalty, f"{market_state.title()} regime"))
            
            # No-trade penalty
            if no_trade_penalty != 0:
                severity = result.no_trade_signal.severity if result.no_trade_signal else "unknown"
                penalties.append(("No-Trade Penalty", no_trade_penalty, f"{severity.title()} severity"))
            
            # Volatility penalty
            if volatility_penalty != 0:
                vix_level = result.market_context.vix_level.replace("_", " ") if result.market_context else "unknown"
                penalties.append(("Volatility Penalty", volatility_penalty, f"{vix_level.title()} VIX"))
            
            # Data penalty
            if data_penalty != 0:
                penalties.append(("Data Penalty", data_penalty, "Missing data"))
            
            if penalties:
                for name, value, reason in penalties:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**{name}:** {reason}")
                    with col2:
                        st.metric("", f"{value:+.2f}")
            
            # Score calculation
            st.markdown("---")
            adjusted_score = raw_score + market_penalty + no_trade_penalty + volatility_penalty + data_penalty
            total_penalties = market_penalty + no_trade_penalty + volatility_penalty + data_penalty
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Raw Score", f"{raw_score:+.2f}")
            with col2:
                st.metric("Total Penalties", f"{total_penalties:+.2f}")
            with col3:
                st.metric("Adjusted Score", f"{adjusted_score:+.2f}")
            
            # Add tooltip explanation for adjusted score
            st.caption("ℹ️ Adjusted score reflects risk-adjusted directional bias. Positive = bullish, Negative = bearish.")
            
            st.divider()
            
            # Reversal Watch
            if result.reversal_watch:
                rw = result.reversal_watch
                
                # Determine status color
                if rw.status == "triggered":
                    status_color = "#28a745"
                    status_emoji = "🎯"
                    status_text = "TRIGGERED"
                else:
                    status_color = "#ffc107"
                    status_emoji = "📌"
                    status_text = "WATCH ONLY"
                
                st.markdown(
                    f'<div style="background-color: {status_color}20; border: 2px solid {status_color}; '
                    f'border-radius: 10px; padding: 20px; margin: 20px 0;">'
                    f'<h3 style="color: {status_color}; margin-top: 0;">{status_emoji} POTENTIAL REVERSAL SETUP</h3>'
                    f'<p><strong>Status:</strong> {status_text}</p>'
                    f'<p><strong>Confidence:</strong> {rw.confidence:.0%}</p>'
                    f'<h4>Reversal Triggers:</h4>'
                    f'<ul>',
                    unsafe_allow_html=True
                )
                
                # Display triggers
                for trigger in rw.triggers:
                    check_mark = "✓" if trigger.met else "○"
                    st.markdown(f'<li>{check_mark} {trigger.description}</li>', unsafe_allow_html=True)
                
                st.markdown(
                    f'</ul>'
                    f'<h4>Analysis:</h4>'
                    f'<p>{rw.reasoning}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                st.divider()
            
            # Price chart
            st.markdown("### 📉 Price History")
            chart = create_price_chart(result.stock_data.historical_prices, symbol)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            
            # Technical details in expander
            with st.expander("📊 Detailed Technical Indicators"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**MA-20 (20-day avg):** {currency_symbol}{result.technical.ma_20:.2f}")
                    st.write(f"**MA-50 (50-day avg):** {currency_symbol}{result.technical.ma_50:.2f}")
                    st.write(f"**MA-200 (200-day avg):** {currency_symbol}{result.technical.ma_200:.2f}")
                with col2:
                    if result.technical.support_levels:
                        st.write(f"**Support (floor):** {currency_symbol}{min(result.technical.support_levels):.2f}")
                    if result.technical.resistance_levels:
                        st.write(f"**Resistance (ceiling):** {currency_symbol}{max(result.technical.resistance_levels):.2f}")
            
            # Recent news in expander
            with st.expander(f"📰 Recent News ({len(result.sentiment.sources)} articles)"):
                recent_sources = sorted(result.sentiment.sources, key=lambda s: s.timestamp, reverse=True)[:10]
                for source in recent_sources:
                    time_ago = (datetime.now() - source.timestamp).total_seconds() / 3600
                    time_str = f"{int(time_ago)}h ago" if time_ago >= 1 else f"{int(time_ago * 60)}m ago"
                    
                    score_emoji = "🟢" if source.score > 0 else "🔴" if source.score < 0 else "🟡"
                    st.markdown(f"**{score_emoji} {source.score:+.2f}** | {time_str} | {source.source_type.capitalize()}")
                    st.write(source.content[:200] + "..." if len(source.content) > 200 else source.content)
                    st.divider()
            
        except ValueError as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Make sure you're using a valid stock ticker symbol. For Indian stocks, add .NS (NSE) or .BO (BSE) suffix.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            st.info("💡 Please check your configuration and try again.")


def scan_stocks_page():
    """Stock scanning page with news-driven discovery."""
    st.markdown('<h1 class="main-header">🔍 Stock Scanner</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    Discover stocks from recent market news and find trading opportunities based on comprehensive analysis.
    The scanner automatically identifies stocks mentioned in news articles and analyzes them for actionable recommendations.
    """)
    
    # Configuration
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        hours_back = st.number_input("Hours of News", 1, 72, 24, help="How many hours of news to fetch")
    with col2:
        min_mentions = st.number_input("Min Mentions", 1, 20, 2, help="Minimum news mentions required")
    with col3:
        top_k = st.number_input("Top K Stocks", 1, 20, 5, help="Analyze only top K stocks by mentions")
    with col4:
        min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.6, 0.05)
    with col5:
        st.write("")
        st.write("")
        scan_button = st.button("🚀 Start News Scan", type="primary", use_container_width=True)
    
    if scan_button:
        config = Configuration()
        agent = AgentCore(config)
        
        # Import news discovery components
        from src.news_discovery import NewsDiscovery
        from src.symbol_lookup import SymbolLookup
        from src.agent_core import analyze_discovered_stocks, filter_actionable_recommendations
        
        # Phase 1: Discover stocks from news
        st.info("📰 Fetching and analyzing recent market news...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Discovering stocks from news...")
            progress_bar.progress(0.2)
            
            discovery = NewsDiscovery(
                data_provider=agent.data_provider,
                symbol_lookup=SymbolLookup(),
                max_symbols=50
            )
            
            discovered_stocks = discovery.discover_stocks(hours_back=hours_back)
            progress_bar.progress(0.4)
            
            if not discovered_stocks:
                status_text.empty()
                progress_bar.empty()
                st.warning("⚠️ No stocks discovered from recent news. Try increasing the hours or check your API keys.")
                return
            
            # Filter by minimum mentions
            filtered_stocks = [s for s in discovered_stocks if s.mention_count >= min_mentions]
            
            if not filtered_stocks:
                status_text.empty()
                progress_bar.empty()
                st.warning(f"⚠️ No stocks found with at least {min_mentions} mentions. Discovered {len(discovered_stocks)} stocks total, but none meet the mention threshold. Try lowering the minimum mentions.")
                
                # Show what was discovered
                with st.expander("📋 Discovered Symbols (Below Threshold)", expanded=True):
                    import pandas as pd
                    df_data = []
                    for stock in discovered_stocks[:20]:
                        df_data.append({
                            'Symbol': stock.symbol,
                            'Mentions': stock.mention_count,
                            'Sources': len(stock.sources)
                        })
                    if df_data:
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                return
            
            # Sort by mention count (descending) and take top K
            filtered_stocks_sorted = sorted(filtered_stocks, key=lambda s: s.mention_count, reverse=True)
            top_k_stocks = filtered_stocks_sorted[:top_k]
            
            st.success(f"✅ Discovered {len(discovered_stocks)} stocks from news ({len(filtered_stocks)} with ≥{min_mentions} mentions)")
            
            # Display discovered symbols
            with st.expander("📋 Top Stocks by Mentions (To Be Analyzed)", expanded=True):
                # Create a dataframe for better display
                import pandas as pd
                df_data = []
                for stock in top_k_stocks:
                    df_data.append({
                        'Symbol': stock.symbol,
                        'Mentions': stock.mention_count,
                        'Sources': len(stock.sources)
                    })
                
                if df_data:
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Show remaining stocks if any
            if len(filtered_stocks) > top_k:
                with st.expander(f"📋 Other Stocks Meeting Threshold ({len(filtered_stocks) - top_k} not analyzed)", expanded=False):
                    df_data = []
                    for stock in filtered_stocks_sorted[top_k:]:
                        df_data.append({
                            'Symbol': stock.symbol,
                            'Mentions': stock.mention_count,
                            'Sources': len(stock.sources)
                        })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Phase 2: Analyze only top K stocks
            status_text.text(f"Analyzing top {len(top_k_stocks)} stocks by mentions...")
            progress_bar.progress(0.6)
            
            analysis_results = analyze_discovered_stocks(top_k_stocks, agent)
            progress_bar.progress(0.8)
            
            st.success(f"✅ Analyzed {len(analysis_results)} stocks successfully")
            
            # Phase 3: Filter for actionable recommendations
            status_text.text("Filtering for actionable recommendations...")
            actionable_results = filter_actionable_recommendations(analysis_results, top_k_stocks)
            progress_bar.progress(1.0)
            
            status_text.empty()
            progress_bar.empty()
            
            # Filter by minimum confidence
            filtered_results = [
                r for r in actionable_results
                if r.recommendation.confidence >= min_confidence
            ]
            
            # Display results
            if filtered_results:
                st.success(f"✅ Found {len(filtered_results)} actionable recommendation(s)!")
                
                # Display summary statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Stocks Discovered", len(discovered_stocks))
                with col2:
                    st.metric("Meeting Mention Threshold", len(filtered_stocks))
                with col3:
                    st.metric("Top K Analyzed", len(top_k_stocks))
                with col4:
                    st.metric("Actionable Recommendations", len(filtered_results))
                
                st.markdown("---")
                
                # Display each opportunity
                for result in filtered_results:
                    symbol = result.symbol
                    rec = result.recommendation
                    
                    # Get mention count
                    mention_count = 0
                    for stock in top_k_stocks:
                        if stock.symbol == symbol:
                            mention_count = stock.mention_count
                            break
                    
                    # Determine action color
                    action_color = "🟢" if rec.action == "BUY" else "🔴"
                    
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
                        
                        with col1:
                            st.markdown(f"### {symbol}")
                            st.metric("Price", f"${result.current_price:.2f}")
                            if mention_count > 0:
                                st.caption(f"📰 {mention_count} news mentions")
                        
                        with col2:
                            st.markdown(f"### {action_color} {rec.action}")
                            st.metric("Confidence", f"{rec.confidence:.0%}")
                        
                        with col3:
                            st.write("**Scores:**")
                            st.write(f"Sentiment: {result.sentiment.sentiment_score:+.2f}")
                            st.write(f"Technical: {result.technical.technical_score:+.2f}")
                            st.write(f"Fundamental: {result.fundamental.fundamental_score:+.2f}")
                        
                        with col4:
                            st.write("**Summary:**")
                            summary = generate_plain_english_summary(result)
                            st.write(summary[:150] + "..." if len(summary) > 150 else summary)
                            
                            # Add button to view detailed analysis
                            if st.button(f"View Details", key=f"details_{symbol}"):
                                # Set the symbol to analyze
                                st.session_state.selected_symbol = symbol
                                st.session_state.trigger_analysis = True
                                # Navigate to the analysis page
                                st.session_state.current_page = "📊 Stock Analysis"
                                st.rerun()
                        
                        st.divider()
            else:
                if actionable_results:
                    st.warning(f"⚠️ Found {len(actionable_results)} actionable recommendations, but none meet the confidence threshold of {min_confidence:.0%}. Try lowering the threshold.")
                else:
                    st.warning("⚠️ No actionable recommendations found (all stocks received HOLD recommendations). Try again later or adjust the time range.")
        
        except Exception as e:
            status_text.empty()
            progress_bar.empty()
            st.error(f"❌ Error during scan: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())


def main():
    """Main application."""
    # Initialize authenticator
    auth = Authenticator()
    
    # Require authentication before showing app
    if not auth.require_authentication():
        return
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=📈", width=150)
        st.title("Stock Market AI Agent")
        st.markdown("---")
        
        # Initialize page in session state if not present
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "📊 Stock Analysis"
        
        page = st.radio(
            "Navigation",
            ["📊 Stock Analysis", "🔍 Stock Scanner", "ℹ️ About"],
            key="current_page",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        st.info("Configuration loaded from config file or environment variables.")
        
        # Show logout button
        show_logout_button()
        
        st.markdown("---")
        display_disclaimer()
    
    # Main content
    if page == "📊 Stock Analysis":
        analyze_stock_page()
    elif page == "🔍 Stock Scanner":
        scan_stocks_page()
    elif page == "ℹ️ About":
        st.markdown('<h1 class="main-header">ℹ️ About</h1>', unsafe_allow_html=True)
        st.markdown("""
        ## Stock Market AI Agent
        
        A comprehensive stock analysis tool that combines:
        
        - **Sentiment Analysis**: Analyzes news articles and social media to gauge market sentiment
        - **Technical Analysis**: Evaluates price patterns, momentum indicators, and support/resistance levels
        - **Fundamental Analysis**: Assesses company financials, valuation metrics, and growth potential
        
        ### Features
        
        - 📊 **Comprehensive Analysis**: Get detailed insights on any stock
        - 🔍 **Stock Scanner**: Automatically find BUY opportunities
        - 📈 **Interactive Charts**: Visualize price history and technical indicators
        - 💡 **Plain English Summaries**: Understand recommendations without jargon
        
        ### Data Sources
        
        - Yahoo Finance (price data and news)
        - Finnhub (company news)
        - NewsAPI (comprehensive news coverage)
        
        ### Version
        
        1.0.0
        
        ---
        
        **Remember**: This tool is for educational purposes only. Always consult with qualified financial professionals before making investment decisions.
        """)


if __name__ == "__main__":
    main()
