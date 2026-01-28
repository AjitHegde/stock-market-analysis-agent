"""
Command-line interface for the Stock Market AI Agent.

This module provides CLI commands for analyzing stocks, viewing recommendations,
checking sentiment, and assessing portfolio risk.
"""

import click
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from datetime import datetime
import sys

from src.agent_core import AgentCore
from src.config import Configuration
from src.models import Position
from src.symbol_lookup import SymbolLookup


console = Console()


def _generate_plain_english_summary(result) -> str:
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


def display_startup_disclaimer():
    """Display startup disclaimer about educational purposes."""
    disclaimer_text = """
[bold yellow]⚠️  IMPORTANT DISCLAIMER[/bold yellow]

This Stock Market AI Agent is provided for [bold]EDUCATIONAL and INFORMATIONAL PURPOSES ONLY[/bold].

• This tool is NOT financial advice
• Past performance does not guarantee future results
• All investment decisions carry risk
• Consult with qualified financial professionals before making investment decisions
• The creators assume no liability for financial losses

By using this tool, you acknowledge these limitations and agree to use it responsibly.
    """
    console.print(Panel(disclaimer_text, border_style="yellow", box=box.DOUBLE))
    console.print()


def display_recommendation_disclaimer():
    """Display disclaimer for recommendations."""
    return "\n[dim]⚠️  This recommendation is not financial advice. Consult a financial professional before making investment decisions.[/dim]"


def display_past_performance_warning():
    """Display warning about past performance."""
    return "\n[dim]⚠️  Past performance does not guarantee future results.[/dim]"


def display_risk_estimate_clarification():
    """Display clarification about risk estimates."""
    return "\n[dim]⚠️  Risk calculations are estimates based on historical data and may not reflect actual future risk.[/dim]"


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Stock Market AI Agent - Your personal trading assistant.
    
    Analyzes stocks using sentiment analysis, technical indicators, and fundamental metrics
    to provide actionable trading recommendations.
    
    Commands:
      analyze    - Comprehensive analysis of a stock
      recommend  - Get trading recommendation for a stock
      sentiment  - View detailed sentiment analysis
      portfolio  - Assess portfolio risk
      scan       - Scan multiple stocks and find BUY opportunities
    """
    display_startup_disclaimer()


@cli.command()
@click.argument('symbol')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def analyze(symbol: str, config: Optional[str]):
    """
    Perform comprehensive analysis on a stock.
    
    SYMBOL: Stock ticker symbol or company name (e.g., AAPL, Tesla, HDFC Bank)
    
    Examples:
        stock-agent analyze AAPL
        stock-agent analyze "idfc first bank"
        stock-agent analyze tesla
    """
    try:
        # Lookup symbol from user input
        original_input = symbol
        symbol = SymbolLookup.lookup(symbol)
        
        if not symbol:
            console.print(f"[bold red]Error:[/bold red] Could not find a matching stock symbol for '{original_input}'", style="red")
            console.print("\n[dim]Try using the exact ticker symbol or a more specific company name.[/dim]")
            sys.exit(1)
        
        # Show what we're analyzing if it was converted
        company_name = SymbolLookup.get_company_name(symbol)
        if company_name and company_name.lower() != original_input.lower():
            console.print(f"\n[cyan]Analyzing {company_name.title()} ({symbol})...[/cyan]\n")
        else:
            console.print(f"\n[bold cyan]Analyzing {symbol}...[/bold cyan]\n")
        
        # Load configuration
        cfg = Configuration.load(config) if config else Configuration()
        agent = AgentCore(cfg)
        
        # Run analysis with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching data and running analysis...", total=None)
            result = agent.analyze_stock(symbol)
            progress.update(task, completed=True)
        
        console.print()
        
        # Display data quality banner if issues exist
        if result.data_quality_report and result.data_quality_report.issues:
            console.print()
            report = result.data_quality_report
            
            # Determine banner color based on severity
            if report.has_critical_issues:
                banner_color = "red"
                banner_emoji = "🔴"
            elif any(i.severity == "major" for i in report.issues):
                banner_color = "yellow"
                banner_emoji = "⚠️"
            else:
                banner_color = "blue"
                banner_emoji = "ℹ️"
            
            # Build banner message
            banner_text = f"[bold {banner_color}]{banner_emoji} DATA QUALITY ISSUES DETECTED[/bold {banner_color}]\n\n"
            banner_text += f"[bold]Total Confidence Penalty:[/bold] [{banner_color}]-{report.total_confidence_penalty:.0%}[/{banner_color}]\n\n"
            banner_text += "[bold]Issues Found:[/bold]\n"
            
            for issue in report.issues:
                # Severity emoji
                severity_emoji = {"critical": "🔴", "major": "⚠️", "minor": "ℹ️"}.get(issue.severity, "•")
                severity_color = {"critical": "red", "major": "yellow", "minor": "blue"}.get(issue.severity, "white")
                
                banner_text += f"  [{severity_color}]{severity_emoji} {issue.source}[/{severity_color}]\n"
                banner_text += f"     Reason: {issue.reason}\n"
                banner_text += f"     Impact: {issue.impact}\n"
                banner_text += f"     Penalty: -{issue.confidence_penalty:.0%}\n"
            
            console.print(Panel(
                banner_text,
                title=f"{banner_emoji} Data Quality Alert",
                border_style=banner_color,
                box=box.DOUBLE
            ))
            console.print()
        
        # Display current price
        console.print("[bold]💰 Current Price[/bold]")
        price_table = Table(show_header=False, box=box.SIMPLE)
        
        # Detect currency based on symbol suffix
        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            currency_symbol = "₹"
            currency_name = "INR"
        else:
            currency_symbol = "$"
            currency_name = "USD"
        
        price_table.add_row("Price:", f"{currency_symbol}{result.current_price:.2f} {currency_name}")
        price_table.add_row("Volume:", f"{result.volume:,}")
        console.print(price_table)
        console.print()
        
        # Display sentiment analysis
        console.print("[bold]📊 Sentiment Analysis[/bold]")
        sentiment_table = Table(show_header=False, box=box.SIMPLE)
        sentiment_table.add_row("Score:", f"{result.sentiment.sentiment_score:+.2f}")
        sentiment_table.add_row("Confidence:", f"{result.sentiment.confidence:.2%}")
        sentiment_table.add_row("Sources:", f"{len(result.sentiment.sources)}")
        console.print(sentiment_table)
        console.print()
        
        # Display technical analysis
        console.print("[bold]📈 Technical Analysis[/bold]")
        tech_table = Table(show_header=False, box=box.SIMPLE)
        tech_table.add_row("Technical Score:", f"{result.technical.technical_score:+.2f}")
        
        # Display regime with emoji and color
        regime = result.technical.regime
        regime_display = {
            "bullish-trend": "🟢 Bullish Trend",
            "bearish-trend": "🔴 Bearish Trend",
            "oversold-zone": "🟦 Oversold Zone (Potential Reversal)",
            "overbought-zone": "🟧 Overbought Zone (Potential Reversal)",
            "consolidation": "🟡 Consolidation (Sideways)",
            "neutral": "⚪ Neutral"
        }
        regime_text = regime_display.get(regime, regime.replace("-", " ").title())
        tech_table.add_row("Market Regime:", regime_text)
        
        # RSI with interpretation
        rsi_value = result.technical.rsi
        if rsi_value > 70:
            rsi_label = f"{rsi_value:.2f} [red](Overbought)[/red]"
        elif rsi_value < 30:
            rsi_label = f"{rsi_value:.2f} [green](Oversold)[/green]"
        else:
            rsi_label = f"{rsi_value:.2f} [yellow](Neutral)[/yellow]"
        tech_table.add_row("RSI:", rsi_label)
        
        # MACD with interpretation
        macd_value = result.technical.macd
        if macd_value > 0:
            macd_label = f"{macd_value:.2f} [green](Bullish)[/green]"
        else:
            macd_label = f"{macd_value:.2f} [red](Bearish)[/red]"
        tech_table.add_row("MACD:", macd_label)
        
        # Detect currency for moving averages
        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            currency_symbol = "₹"
        else:
            currency_symbol = "$"
        
        tech_table.add_row("MA-20 (20-day avg):", f"{currency_symbol}{result.technical.ma_20:.2f}")
        tech_table.add_row("MA-50 (50-day avg):", f"{currency_symbol}{result.technical.ma_50:.2f}")
        tech_table.add_row("MA-200 (200-day avg):", f"{currency_symbol}{result.technical.ma_200:.2f}")
        if result.technical.support_levels:
            tech_table.add_row("Support (floor):", f"{currency_symbol}{min(result.technical.support_levels):.2f}")
        if result.technical.resistance_levels:
            tech_table.add_row("Resistance (ceiling):", f"{currency_symbol}{max(result.technical.resistance_levels):.2f}")
        console.print(tech_table)
        console.print("[dim]RSI: >70 overbought, <30 oversold | MACD: >0 bullish, <0 bearish[/dim]")
        console.print()
        
        # Display fundamental analysis
        console.print("[bold]💼 Fundamental Analysis[/bold]")
        fund_table = Table(show_header=False, box=box.SIMPLE)
        fund_table.add_row("Fundamental Score:", f"{result.fundamental.fundamental_score:+.2f}")
        
        # P/E Ratio with interpretation
        if result.fundamental.pe_ratio:
            pe_value = result.fundamental.pe_ratio
            if pe_value < 15:
                pe_label = f"{pe_value:.2f} [green](Undervalued)[/green]"
            elif pe_value > 30:
                pe_label = f"{pe_value:.2f} [red](Overvalued)[/red]"
            else:
                pe_label = f"{pe_value:.2f} [yellow](Fair)[/yellow]"
            fund_table.add_row("P/E Ratio (Price/Earnings):", pe_label)
        
        # P/B Ratio with interpretation
        if result.fundamental.pb_ratio:
            pb_value = result.fundamental.pb_ratio
            if pb_value < 1:
                pb_label = f"{pb_value:.2f} [green](Undervalued)[/green]"
            elif pb_value > 3:
                pb_label = f"{pb_value:.2f} [red](Expensive)[/red]"
            else:
                pb_label = f"{pb_value:.2f} [yellow](Fair)[/yellow]"
            fund_table.add_row("P/B Ratio (Price/Book):", pb_label)
        
        # Debt to Equity with interpretation
        if result.fundamental.debt_to_equity:
            de_value = result.fundamental.debt_to_equity
            if de_value < 50:
                de_label = f"{de_value:.2f} [green](Low debt)[/green]"
            elif de_value > 100:
                de_label = f"{de_value:.2f} [red](High debt)[/red]"
            else:
                de_label = f"{de_value:.2f} [yellow](Moderate)[/yellow]"
            fund_table.add_row("Debt/Equity:", de_label)
        
        # Revenue Growth
        if result.fundamental.revenue_growth is not None:
            growth_value = result.fundamental.revenue_growth
            if growth_value > 15.0:
                growth_label = f"{growth_value:+.1f}% [green](Strong)[/green]"
            elif growth_value < -10.0:
                growth_label = f"{growth_value:+.1f}% [red](Declining)[/red]"
            else:
                growth_label = f"{growth_value:+.1f}%"
            fund_table.add_row("Revenue Growth:", growth_label)
        
        console.print(fund_table)
        console.print("[dim]P/E: <15 cheap, >30 expensive | P/B: <1 undervalued, >3 expensive | Debt/Equity: <50 low, >100 high[/dim]")
        console.print()
        
        # Display market context (if available)
        if result.market_context:
            console.print("[bold]🌍 Market Context[/bold]")
            market_table = Table(show_header=False, box=box.SIMPLE)
            
            # Nifty 50
            nifty_emoji = {"bullish": "🟢", "neutral": "🟡", "bearish": "🔴"}.get(result.market_context.nifty_trend, "")
            market_table.add_row(
                "Nifty 50:",
                f"{nifty_emoji} {result.market_context.nifty_trend.capitalize()} "
                f"(₹{result.market_context.nifty_price:,.0f})"
            )
            
            # Bank Nifty
            banknifty_emoji = {"bullish": "🟢", "neutral": "🟡", "bearish": "🔴"}.get(result.market_context.banknifty_trend, "")
            market_table.add_row(
                "Bank Nifty:",
                f"{banknifty_emoji} {result.market_context.banknifty_trend.capitalize()} "
                f"(₹{result.market_context.banknifty_price:,.0f})"
            )
            
            # VIX
            vix_emoji = {"low": "🟢", "moderate": "🟡", "high": "🟠", "very_high": "🔴"}.get(result.market_context.vix_level, "")
            market_table.add_row(
                "India VIX:",
                f"{vix_emoji} {result.market_context.vix_level.replace('_', ' ').capitalize()} "
                f"({result.market_context.vix_value:.2f})"
            )
            
            # Overall market state
            state_emoji = {"bullish": "🟢", "neutral": "🟡", "bearish": "🔴", "volatile": "⚠️"}.get(result.market_context.market_state, "")
            state_color = {"bullish": "green", "neutral": "yellow", "bearish": "red", "volatile": "red"}.get(result.market_context.market_state, "white")
            market_table.add_row(
                "Market State:",
                f"{state_emoji} [bold {state_color}]{result.market_context.market_state.upper()}[/bold {state_color}]"
            )
            
            console.print(market_table)
            console.print()
        
        # Display no-trade warning if active (BEFORE recommendation)
        if result.no_trade_signal and result.no_trade_signal.is_no_trade:
            console.print()
            severity_color = {
                "high": "red",
                "medium": "yellow",
                "low": "blue"
            }.get(result.no_trade_signal.severity, "yellow")
            
            warning_text = f"[bold {severity_color}]🚫 TRADING DISABLED TODAY[/bold {severity_color}]\n\n"
            warning_text += "[bold]Dangerous Market Conditions Detected:[/bold]\n"
            for reason in result.no_trade_signal.reasons:
                warning_text += f"  • {reason}\n"
            warning_text += f"\n[bold]Suggested Action:[/bold]\n{result.no_trade_signal.suggested_action}"
            
            console.print(Panel(
                warning_text,
                title="⚠️  NO TRADE ZONE ⚠️",
                border_style=severity_color,
                box=box.DOUBLE
            ))
            console.print()
        
        # Display recommendation
        console.print("[bold]🎯 Recommendation[/bold]")
        action_color = {
            "BUY": "green",
            "SELL": "red",
            "HOLD": "yellow"
        }.get(result.recommendation.action, "white")
        
        rec_table = Table(show_header=False, box=box.SIMPLE)
        rec_table.add_row("Action:", f"[bold {action_color}]{result.recommendation.action}[/bold {action_color}]")
        rec_table.add_row("Confidence:", f"{result.recommendation.confidence:.2%}")
        
        if result.recommendation.entry_price_low and result.recommendation.entry_price_high:
            rec_table.add_row(
                "Entry Range:",
                f"${result.recommendation.entry_price_low:.2f} - ${result.recommendation.entry_price_high:.2f}"
            )
        if result.recommendation.exit_price_low and result.recommendation.exit_price_high:
            rec_table.add_row(
                "Exit Range:",
                f"${result.recommendation.exit_price_low:.2f} - ${result.recommendation.exit_price_high:.2f}"
            )
        
        console.print(rec_table)
        console.print()
        
        # Display confidence breakdown if available
        if result.recommendation.confidence_breakdown:
            console.print("[bold]🔍 Confidence Breakdown[/bold]")
            breakdown = result.recommendation.confidence_breakdown
            
            conf_table = Table(show_header=True, box=box.SIMPLE)
            conf_table.add_column("Analyzer", style="bold")
            conf_table.add_column("Direction", justify="center")
            conf_table.add_column("Strength", justify="right")
            conf_table.add_column("Confidence", justify="right")
            conf_table.add_column("Net Impact", justify="right")
            
            # Calculate net impacts for each analyzer
            # Sentiment
            sentiment_impact = result.sentiment.strength * result.sentiment.confidence
            if result.sentiment.direction == "bearish":
                sentiment_impact = -sentiment_impact
            elif result.sentiment.direction == "neutral":
                sentiment_impact = sentiment_impact * 0.3
            
            sentiment_dir_emoji = "🟢" if result.sentiment.direction == "bullish" else "🔴" if result.sentiment.direction == "bearish" else "🟡"
            sentiment_impact_color = "green" if sentiment_impact > 0 else "red" if sentiment_impact < 0 else "yellow"
            
            conf_table.add_row(
                "Sentiment",
                f"{sentiment_dir_emoji} {result.sentiment.direction.capitalize()}",
                f"{result.sentiment.strength:.0%}",
                f"{result.sentiment.confidence:.0%}",
                f"[{sentiment_impact_color}]{sentiment_impact:+.2f}[/{sentiment_impact_color}]"
            )
            
            # Technical
            technical_impact = result.technical.strength * result.technical.confidence
            if result.technical.direction == "bearish":
                technical_impact = -technical_impact
            elif result.technical.direction == "neutral":
                technical_impact = technical_impact * 0.3
            
            technical_dir_emoji = "🟢" if result.technical.direction == "bullish" else "🔴" if result.technical.direction == "bearish" else "🟡"
            technical_impact_color = "green" if technical_impact > 0 else "red" if technical_impact < 0 else "yellow"
            
            conf_table.add_row(
                "Technical",
                f"{technical_dir_emoji} {result.technical.direction.capitalize()}",
                f"{result.technical.strength:.0%}",
                f"{result.technical.confidence:.0%}",
                f"[{technical_impact_color}]{technical_impact:+.2f}[/{technical_impact_color}]"
            )
            
            # Fundamental
            fundamental_impact = result.fundamental.strength * result.fundamental.confidence
            if result.fundamental.direction == "bearish":
                fundamental_impact = -fundamental_impact
            elif result.fundamental.direction == "neutral":
                fundamental_impact = fundamental_impact * 0.3
            
            fundamental_dir_emoji = "🟢" if result.fundamental.direction == "bullish" else "🔴" if result.fundamental.direction == "bearish" else "🟡"
            fundamental_impact_color = "green" if fundamental_impact > 0 else "red" if fundamental_impact < 0 else "yellow"
            
            conf_table.add_row(
                "Fundamental",
                f"{fundamental_dir_emoji} {result.fundamental.direction.capitalize()}",
                f"{result.fundamental.strength:.0%}",
                f"{result.fundamental.confidence:.0%}",
                f"[{fundamental_impact_color}]{fundamental_impact:+.2f}[/{fundamental_impact_color}]"
            )
            
            console.print(conf_table)
            console.print()
            
            # Display additional metrics
            metrics_table = Table(show_header=False, box=box.SIMPLE)
            
            # Agreement score
            agreement_color = "green" if breakdown.agreement_score >= 0.75 else "yellow" if breakdown.agreement_score >= 0.60 else "red"
            metrics_table.add_row(
                "Agreement Score:",
                f"[{agreement_color}]{breakdown.agreement_score:.0%}[/{agreement_color}]"
            )
            
            # Market metrics (split into quality and favorability)
            metrics_table.add_row("Market Signal Quality:", f"{breakdown.market_signal_quality:.0%}")
            metrics_table.add_row("Market Favorability:", f"{breakdown.market_favorability:.0%}")
            
            # Data quality penalty (if any)
            if breakdown.data_quality_penalty > 0:
                metrics_table.add_row(
                    "Data Quality Penalty:",
                    f"[red]-{breakdown.data_quality_penalty:.0%}[/red]"
                )
            
            console.print(metrics_table)
            console.print()
            
            # Display runtime weights
            if result.recommendation.runtime_weights:
                console.print("[bold]⚖️  Active Weights[/bold]")
                
                # Determine mode based on market context and weights source
                weights_source = result.recommendation.runtime_weights.get('source', 'unknown')
                mode_desc = ""
                
                if weights_source.startswith('dynamic'):
                    if result.market_context:
                        market_state = result.market_context.market_state.capitalize()
                        mode_desc = f" ({market_state} Market - Dynamic)"
                    else:
                        mode_desc = " (Dynamic)"
                elif weights_source == 'static':
                    mode_desc = " (Static Config)"
                elif weights_source == 'static-fallback':
                    mode_desc = " (Static Fallback - No Market Data)"
                
                weights_table = Table(show_header=False, box=box.SIMPLE)
                weights = result.recommendation.runtime_weights
                weights_table.add_row("Sentiment:", f"{weights['sentiment']:.0%}")
                weights_table.add_row("Technical:", f"{weights['technical']:.0%}")
                weights_table.add_row("Fundamental:", f"{weights['fundamental']:.0%}")
                
                if mode_desc:
                    console.print(f"[dim]{mode_desc}[/dim]")
                console.print(weights_table)
                console.print()
            
            # Display risk adjustments section
            console.print("[bold]📉 Risk Adjustments[/bold]")
            
            # Calculate raw score (before penalties)
            raw_score = (
                result.recommendation.sentiment_contribution +
                result.recommendation.technical_contribution +
                result.recommendation.fundamental_contribution
            )
            
            # Calculate market penalty
            market_penalty = 0.0
            if result.market_context:
                # Market penalty based on market state and favorability
                if result.market_context.market_state == "bearish":
                    # Bearish market reduces confidence
                    market_penalty = -(1.0 - breakdown.market_favorability) * 0.5
                elif result.market_context.market_state == "volatile":
                    # Volatile market reduces confidence
                    market_penalty = -(1.0 - breakdown.market_favorability) * 0.3
                elif result.market_context.market_state == "neutral":
                    # Neutral market has small penalty
                    market_penalty = -(1.0 - breakdown.market_favorability) * 0.2
                # Bullish market has no penalty (or small bonus)
            
            # Calculate no-trade penalty
            no_trade_penalty = 0.0
            if result.no_trade_signal and result.no_trade_signal.is_no_trade:
                # Penalty based on severity
                if result.no_trade_signal.severity == "high":
                    no_trade_penalty = -0.30
                elif result.no_trade_signal.severity == "medium":
                    no_trade_penalty = -0.20
                else:  # low
                    no_trade_penalty = -0.10
            
            # Calculate volatility penalty (from VIX)
            volatility_penalty = 0.0
            if result.market_context:
                if result.market_context.vix_level == "very_high":
                    volatility_penalty = -0.25
                elif result.market_context.vix_level == "high":
                    volatility_penalty = -0.15
                elif result.market_context.vix_level == "moderate":
                    volatility_penalty = -0.05
                # Low VIX has no penalty
            
            # Data quality penalty (already in breakdown)
            data_penalty = -breakdown.data_quality_penalty
            
            # Calculate adjusted score
            adjusted_score = raw_score + market_penalty + no_trade_penalty + volatility_penalty + data_penalty
            
            # Display penalties
            risk_table = Table(show_header=False, box=box.SIMPLE)
            
            # Market penalty
            if market_penalty != 0:
                market_desc = ""
                if result.market_context:
                    market_desc = f"({result.market_context.market_state.capitalize()} regime)"
                penalty_color = "red" if market_penalty < 0 else "green"
                risk_table.add_row(
                    "Market Penalty:",
                    f"[{penalty_color}]{market_penalty:+.2f}[/{penalty_color}] {market_desc}"
                )
            
            # No-trade penalty
            if no_trade_penalty != 0:
                severity_desc = f"({result.no_trade_signal.severity.capitalize()} severity)"
                risk_table.add_row(
                    "No-Trade Penalty:",
                    f"[red]{no_trade_penalty:+.2f}[/red] {severity_desc}"
                )
            
            # Volatility penalty
            if volatility_penalty != 0:
                vix_desc = ""
                if result.market_context:
                    vix_desc = f"(VIX: {result.market_context.vix_value:.1f})"
                risk_table.add_row(
                    "Volatility Penalty:",
                    f"[red]{volatility_penalty:+.2f}[/red] {vix_desc}"
                )
            
            # Data penalty
            if data_penalty != 0:
                risk_table.add_row(
                    "Data Penalty:",
                    f"[red]{data_penalty:+.2f}[/red]"
                )
            
            # Show calculation if any penalties exist
            if market_penalty != 0 or no_trade_penalty != 0 or volatility_penalty != 0 or data_penalty != 0:
                console.print(risk_table)
                console.print()
                
                # Show score calculation
                calc_table = Table(show_header=False, box=box.SIMPLE)
                calc_table.add_row("Raw Score:", f"{raw_score:+.2f}")
                total_penalties = market_penalty + no_trade_penalty + volatility_penalty + data_penalty
                penalty_color = "red" if total_penalties < 0 else "green"
                calc_table.add_row("Total Penalties:", f"[{penalty_color}]{total_penalties:+.2f}[/{penalty_color}]")
                calc_table.add_row("Adjusted Score:", f"[bold]{adjusted_score:+.2f}[/bold]")
                console.print(calc_table)
                console.print()
            else:
                console.print("[dim]No risk penalties applied[/dim]")
                console.print()
        
        # Display trade levels if available (for BUY recommendations)
        if result.recommendation.trade_levels:
            console.print("[bold]📍 Trade Levels[/bold]")
            levels = result.recommendation.trade_levels
            
            # Detect currency
            if symbol.endswith('.NS') or symbol.endswith('.BO'):
                currency_symbol = "₹"
            else:
                currency_symbol = "$"
            
            trade_table = Table(show_header=False, box=box.SIMPLE)
            trade_table.add_row(
                "Ideal Entry:",
                f"[green]{currency_symbol}{levels.ideal_entry:.2f}[/green]"
            )
            trade_table.add_row(
                "Stop Loss:",
                f"[red]{currency_symbol}{levels.stop_loss:.2f}[/red]"
            )
            trade_table.add_row(
                "Target:",
                f"[cyan]{currency_symbol}{levels.target:.2f}[/cyan]"
            )
            trade_table.add_row(
                "Risk per Trade:",
                f"{levels.risk_per_trade_percent:.1f}% of capital"
            )
            trade_table.add_row(
                "R:R Ratio:",
                f"[bold]1:{levels.risk_reward_ratio:.1f}[/bold]"
            )
            trade_table.add_row(
                "Position Size:",
                f"{levels.position_size_percent:.1f}% of capital"
            )
            console.print(trade_table)
            console.print()
        
        # Display reversal watch if detected
        if result.reversal_watch:
            console.print()
            reversal = result.reversal_watch
            
            # Determine status styling
            if reversal.status == "triggered":
                status_emoji = "🎯"
                status_color = "green"
                status_text = "TRIGGERED"
            else:  # watch-only
                status_emoji = "📌"
                status_color = "yellow"
                status_text = "WATCH ONLY"
            
            reversal_text = f"[bold {status_color}]{status_emoji} POTENTIAL REVERSAL SETUP[/bold {status_color}]\n\n"
            reversal_text += f"[bold]Status:[/bold] [{status_color}]{status_text}[/{status_color}]\n"
            reversal_text += f"[bold]Confidence:[/bold] {reversal.confidence:.0%}\n\n"
            
            # Display triggers
            reversal_text += "[bold]Reversal Triggers:[/bold]\n"
            for trigger in reversal.triggers:
                check_mark = "✓" if trigger.met else "○"
                trigger_color = "green" if trigger.met else "dim"
                reversal_text += f"  [{trigger_color}]{check_mark} {trigger.description}[/{trigger_color}]\n"
            
            reversal_text += f"\n[bold]Analysis:[/bold]\n{reversal.reasoning}"
            
            console.print(Panel(
                reversal_text,
                title=f"{status_emoji} Reversal Watch",
                border_style=status_color,
                box=box.ROUNDED
            ))
            console.print()
        
        console.print("[bold]Reasoning:[/bold]")
        console.print(result.recommendation.reasoning)
        
        # Display plain English summary
        console.print()
        console.print(Panel(
            _generate_plain_english_summary(result),
            title="📝 Plain English Summary",
            border_style="cyan"
        ))
        
        # Display risk assessment if available
        if result.risk_assessment:
            console.print()
            console.print("[bold]⚠️  Risk Assessment[/bold]")
            risk_table = Table(show_header=False, box=box.SIMPLE)
            risk_table.add_row("Portfolio Risk:", f"{result.risk_assessment.portfolio_risk_score:.2%}")
            risk_table.add_row("Suggested Position:", f"{result.risk_assessment.suggested_position_size:.2%}")
            console.print(risk_table)
            
            if result.risk_assessment.concentration_risks:
                console.print("\n[yellow]Concentration Risks:[/yellow]")
                for risk in result.risk_assessment.concentration_risks:
                    console.print(f"  • {risk}")
            
            if result.risk_assessment.risk_mitigation_actions:
                console.print("\n[cyan]Risk Mitigation:[/cyan]")
                for action in result.risk_assessment.risk_mitigation_actions:
                    console.print(f"  • {action}")
            
            console.print(display_risk_estimate_clarification())
        
        # Display disclaimers
        console.print(display_recommendation_disclaimer())
        console.print(display_past_performance_warning())
        
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        console.print("\n[dim]Example usage: stock-agent analyze AAPL[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}", style="red")
        console.print("\n[dim]Please check your configuration and try again.[/dim]")
        sys.exit(1)


@cli.command()
@click.argument('symbol')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def recommend(symbol: str, config: Optional[str]):
    """
    Get trading recommendation for a stock.
    
    SYMBOL: Stock ticker symbol or company name (e.g., AAPL, Tesla, HDFC Bank)
    
    Examples:
        stock-agent recommend TSLA
        stock-agent recommend "reliance"
    """
    try:
        # Lookup symbol from user input
        original_input = symbol
        symbol = SymbolLookup.lookup(symbol)
        
        if not symbol:
            console.print(f"[bold red]Error:[/bold red] Could not find a matching stock symbol for '{original_input}'", style="red")
            sys.exit(1)
        
        # Show what we're analyzing if it was converted
        company_name = SymbolLookup.get_company_name(symbol)
        if company_name and company_name.lower() != original_input.lower():
            console.print(f"\n[cyan]Getting recommendation for {company_name.title()} ({symbol})...[/cyan]\n")
        else:
            console.print(f"\n[bold cyan]Getting recommendation for {symbol}...[/bold cyan]\n")
        
        # Load configuration
        cfg = Configuration.load(config) if config else Configuration()
        agent = AgentCore(cfg)
        
        # Run analysis with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing...", total=None)
            result = agent.analyze_stock(symbol)
            progress.update(task, completed=True)
        
        console.print()
        
        # Display recommendation
        action_color = {
            "BUY": "green",
            "SELL": "red",
            "HOLD": "yellow"
        }.get(result.recommendation.action, "white")
        
        console.print(Panel(
            f"[bold {action_color}]{result.recommendation.action}[/bold {action_color}]",
            title=f"Recommendation for {symbol}",
            border_style=action_color
        ))
        
        console.print()
        
        # Display current price
        price_table = Table(show_header=False, box=box.SIMPLE)
        
        # Detect currency based on symbol suffix
        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            currency_symbol = "₹"
        else:
            currency_symbol = "$"
        
        price_table.add_row("Current Price:", f"{currency_symbol}{result.current_price:.2f}")
        console.print(price_table)
        
        console.print()
        rec_table = Table(show_header=False, box=box.SIMPLE)
        rec_table.add_row("Confidence:", f"{result.recommendation.confidence:.2%}")
        
        if result.recommendation.entry_price_low and result.recommendation.entry_price_high:
            rec_table.add_row(
                "Entry Range:",
                f"${result.recommendation.entry_price_low:.2f} - ${result.recommendation.entry_price_high:.2f}"
            )
        if result.recommendation.exit_price_low and result.recommendation.exit_price_high:
            rec_table.add_row(
                "Exit Range:",
                f"${result.recommendation.exit_price_low:.2f} - ${result.recommendation.exit_price_high:.2f}"
            )
        
        rec_table.add_row("Sentiment:", f"{result.recommendation.sentiment_contribution:+.2f}")
        rec_table.add_row("Technical:", f"{result.recommendation.technical_contribution:+.2f}")
        rec_table.add_row("Fundamental:", f"{result.recommendation.fundamental_contribution:+.2f}")
        
        console.print(rec_table)
        console.print()
        console.print("[bold]Reasoning:[/bold]")
        console.print(result.recommendation.reasoning)
        
        # Display plain English summary
        console.print()
        console.print(Panel(
            _generate_plain_english_summary(result),
            title="📝 Plain English Summary",
            border_style="cyan"
        ))
        
        # Display disclaimers
        console.print(display_recommendation_disclaimer())
        console.print(display_past_performance_warning())
        
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        console.print("\n[dim]Example usage: stock-agent recommend TSLA[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}", style="red")
        console.print("\n[dim]Please check your configuration and try again.[/dim]")
        sys.exit(1)


@cli.command()
@click.argument('symbol')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def sentiment(symbol: str, config: Optional[str]):
    """
    View detailed sentiment analysis for a stock.
    
    SYMBOL: Stock ticker symbol or company name (e.g., AAPL, Tesla, HDFC Bank)
    
    Examples:
        stock-agent sentiment AAPL
        stock-agent sentiment "tata motors"
    """
    try:
        # Lookup symbol from user input
        original_input = symbol
        symbol = SymbolLookup.lookup(symbol)
        
        if not symbol:
            console.print(f"[bold red]Error:[/bold red] Could not find a matching stock symbol for '{original_input}'", style="red")
            sys.exit(1)
        
        # Show what we're analyzing if it was converted
        company_name = SymbolLookup.get_company_name(symbol)
        if company_name and company_name.lower() != original_input.lower():
            console.print(f"\n[cyan]Analyzing sentiment for {company_name.title()} ({symbol})...[/cyan]\n")
        else:
            console.print(f"\n[bold cyan]Analyzing sentiment for {symbol}...[/bold cyan]\n")
        
        # Load configuration
        cfg = Configuration.load(config) if config else Configuration()
        agent = AgentCore(cfg)
        
        # Run analysis with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching sentiment data...", total=None)
            result = agent.analyze_stock(symbol)
            progress.update(task, completed=True)
        
        console.print()
        
        # Display overall sentiment
        sentiment_score = result.sentiment.sentiment_score
        sentiment_label = "Positive" if sentiment_score > 0.3 else "Negative" if sentiment_score < -0.3 else "Neutral"
        sentiment_color = "green" if sentiment_score > 0.3 else "red" if sentiment_score < -0.3 else "yellow"
        
        console.print(Panel(
            f"[bold {sentiment_color}]{sentiment_label}[/bold {sentiment_color}] ({sentiment_score:+.2f})",
            title=f"Sentiment for {symbol}",
            border_style=sentiment_color
        ))
        
        console.print()
        summary_table = Table(show_header=False, box=box.SIMPLE)
        summary_table.add_row("Sentiment Score:", f"{sentiment_score:+.2f}")
        summary_table.add_row("Confidence:", f"{result.sentiment.confidence:.2%}")
        summary_table.add_row("Total Sources:", f"{len(result.sentiment.sources)}")
        
        # Count by source type
        news_count = sum(1 for s in result.sentiment.sources if s.source_type == "news")
        social_count = sum(1 for s in result.sentiment.sources if s.source_type == "social")
        summary_table.add_row("News Articles:", f"{news_count}")
        summary_table.add_row("Social Posts:", f"{social_count}")
        
        console.print(summary_table)
        console.print()
        
        # Display recent sources
        console.print("[bold]Recent Sources:[/bold]")
        sources_table = Table(box=box.SIMPLE_HEAD)
        sources_table.add_column("Type", style="cyan")
        sources_table.add_column("Score", justify="right")
        sources_table.add_column("Time", style="dim")
        sources_table.add_column("Preview", max_width=60)
        
        # Show up to 10 most recent sources
        recent_sources = sorted(result.sentiment.sources, key=lambda s: s.timestamp, reverse=True)[:10]
        for source in recent_sources:
            score_color = "green" if source.score > 0 else "red" if source.score < 0 else "yellow"
            time_ago = (datetime.now() - source.timestamp).total_seconds() / 3600
            time_str = f"{int(time_ago)}h ago" if time_ago >= 1 else f"{int(time_ago * 60)}m ago"
            preview = source.content[:60] + "..." if len(source.content) > 60 else source.content
            
            sources_table.add_row(
                source.source_type.capitalize(),
                f"[{score_color}]{source.score:+.2f}[/{score_color}]",
                time_str,
                preview
            )
        
        console.print(sources_table)
        
        # Display disclaimers
        console.print(display_past_performance_warning())
        
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
        console.print("\n[dim]Example usage: stock-agent sentiment AAPL[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}", style="red")
        console.print("\n[dim]Please check your configuration and try again.[/dim]")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def portfolio(config: Optional[str]):
    """
    Assess portfolio risk and get recommendations.
    
    Requires portfolio configuration in config file.
    
    Example:
        stock-agent portfolio --config my_config.json
    """
    try:
        console.print("\n[bold cyan]Assessing portfolio risk...[/bold cyan]\n")
        
        # Load configuration
        cfg = Configuration.load(config) if config else Configuration()
        
        if not hasattr(cfg, 'portfolio') or not cfg.portfolio:
            console.print("[yellow]No portfolio configured.[/yellow]")
            console.print("\n[dim]Add portfolio positions to your configuration file to use this feature.[/dim]")
            sys.exit(0)
        
        # Create agent and assess risk
        agent = AgentCore(cfg)
        risk_assessment = agent.risk_manager.assess_portfolio_risk(cfg.portfolio)
        
        # Display risk score
        risk_level = "Low" if risk_assessment.portfolio_risk_score < 0.3 else "Moderate" if risk_assessment.portfolio_risk_score < 0.7 else "High"
        risk_color = "green" if risk_assessment.portfolio_risk_score < 0.3 else "yellow" if risk_assessment.portfolio_risk_score < 0.7 else "red"
        
        console.print(Panel(
            f"[bold {risk_color}]{risk_level}[/bold {risk_color}] ({risk_assessment.portfolio_risk_score:.2%})",
            title="Portfolio Risk",
            border_style=risk_color
        ))
        
        console.print()
        
        # Display portfolio positions
        console.print("[bold]Portfolio Positions:[/bold]")
        positions_table = Table(box=box.SIMPLE_HEAD)
        positions_table.add_column("Symbol", style="cyan")
        positions_table.add_column("Shares", justify="right")
        positions_table.add_column("Value", justify="right")
        positions_table.add_column("Weight", justify="right")
        
        for position in cfg.portfolio:
            positions_table.add_row(
                position.symbol,
                f"{position.shares:,}",
                f"${position.current_value:,.2f}",
                f"{position.weight:.2%}"
            )
        
        console.print(positions_table)
        console.print()
        
        # Display concentration risks
        if risk_assessment.concentration_risks:
            console.print("[bold yellow]⚠️  Concentration Risks:[/bold yellow]")
            for risk in risk_assessment.concentration_risks:
                console.print(f"  • {risk}")
            console.print()
        
        # Display correlation risks
        if risk_assessment.correlation_risks:
            console.print("[bold yellow]⚠️  Correlation Risks:[/bold yellow]")
            for risk in risk_assessment.correlation_risks:
                console.print(f"  • {risk}")
            console.print()
        
        # Display mitigation actions
        if risk_assessment.risk_mitigation_actions:
            console.print("[bold cyan]💡 Risk Mitigation Recommendations:[/bold cyan]")
            for action in risk_assessment.risk_mitigation_actions:
                console.print(f"  • {action}")
            console.print()
        
        # Display disclaimers
        console.print(display_risk_estimate_clarification())
        console.print(display_recommendation_disclaimer())
        
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}", style="red")
        console.print("\n[dim]Please check your configuration and try again.[/dim]")
        sys.exit(1)


@cli.command()
@click.option('--symbols', '-s', multiple=True, help='Specific symbols to scan (bypasses news discovery)')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
@click.option('--min-confidence', '-m', type=float, default=0.6, help='Minimum confidence threshold (default: 0.6)')
@click.option('--limit', '-l', type=int, default=5, help='Maximum number of recommendations to show (default: 5)')
@click.option('--hours-back', '-h', type=int, default=24, help='Hours of news to fetch (default: 24)')
def scan(symbols: tuple, config: Optional[str], min_confidence: float, limit: int, hours_back: int):
    """
    Scan stocks for trading opportunities using news-driven discovery.
    
    By default, discovers stocks from recent market news and analyzes them.
    Use --symbols to analyze specific stocks instead (backward compatibility).
    
    Examples:
        stock-agent scan
        stock-agent scan --hours-back 48 --limit 10
        stock-agent scan --symbols AAPL TSLA GOOGL
    """
    try:
        # Load configuration
        cfg = Configuration.load(config) if config else Configuration()
        agent = AgentCore(cfg)
        
        # Check if explicit symbols provided (backward compatibility)
        if symbols:
            # Use provided symbols (old behavior)
            console.print(f"[bold cyan]Scanning {len(symbols)} specified stocks...[/bold cyan]")
            console.print(f"[dim]Minimum confidence: {min_confidence:.0%}[/dim]")
            console.print(f"[dim]Will show top {limit} recommendations[/dim]\n")
            
            # Analyze specified symbols
            from src.agent_core import analyze_discovered_stocks, filter_actionable_recommendations
            
            # Create mock discovered stocks for backward compatibility
            class MockDiscoveredStock:
                def __init__(self, symbol):
                    self.symbol = symbol
                    self.mention_count = 0
                    self.sources = []
                    self.sample_articles = []
            
            discovered_stocks = [MockDiscoveredStock(s) for s in symbols]
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing stocks...", total=None)
                analysis_results = analyze_discovered_stocks(discovered_stocks, agent)
                progress.update(task, completed=True)
            
            # Filter for actionable recommendations
            actionable_results = filter_actionable_recommendations(analysis_results)
            
        else:
            # Use news-driven discovery (new default behavior)
            console.print(f"[bold cyan]Discovering stocks from recent market news...[/bold cyan]")
            console.print(f"[dim]Fetching news from last {hours_back} hours[/dim]")
            console.print(f"[dim]Minimum confidence: {min_confidence:.0%}[/dim]")
            console.print(f"[dim]Will show top {limit} recommendations[/dim]\n")
            
            # Import news discovery components
            from src.news_discovery import NewsDiscovery
            from src.agent_core import analyze_discovered_stocks, filter_actionable_recommendations
            
            # Phase 1: Discover stocks from news
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Fetching and analyzing news...", total=None)
                
                discovery = NewsDiscovery(
                    data_provider=agent.data_provider,
                    symbol_lookup=SymbolLookup(),
                    max_symbols=50
                )
                
                discovered_stocks = discovery.discover_stocks(hours_back=hours_back)
                progress.update(task, completed=True)
            
            console.print()
            console.print(f"[green]✓[/green] Discovered {len(discovered_stocks)} stocks from news")
            
            # Display discovered symbols
            if discovered_stocks:
                console.print("\n[bold]Discovered Symbols:[/bold]")
                symbols_table = Table(box=box.SIMPLE_HEAD)
                symbols_table.add_column("Symbol", style="cyan")
                symbols_table.add_column("Mentions", justify="right")
                symbols_table.add_column("Sources", justify="right")
                
                for stock in discovered_stocks[:10]:  # Show top 10
                    symbols_table.add_row(
                        stock.symbol,
                        str(stock.mention_count),
                        str(len(stock.sources))
                    )
                
                if len(discovered_stocks) > 10:
                    symbols_table.add_row("...", "...", "...")
                
                console.print(symbols_table)
                console.print()
            
            # Phase 2: Analyze discovered stocks
            console.print("[bold cyan]Analyzing discovered stocks...[/bold cyan]\n")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running analysis pipeline...", total=None)
                analysis_results = analyze_discovered_stocks(discovered_stocks, agent)
                progress.update(task, completed=True)
            
            console.print()
            console.print(f"[green]✓[/green] Analyzed {len(analysis_results)} stocks successfully")
            console.print()
            
            # Phase 3: Filter for actionable recommendations
            actionable_results = filter_actionable_recommendations(analysis_results, discovered_stocks)
        
        # Display results
        if not actionable_results:
            console.print(Panel(
                f"[yellow]No actionable recommendations found (BUY/SELL with confidence >= {min_confidence:.0%})[/yellow]\n\n"
                f"Try lowering the minimum confidence threshold with --min-confidence 0.5",
                title="⚠️  No Opportunities Found",
                border_style="yellow"
            ))
        else:
            # Filter by minimum confidence
            filtered_results = [
                r for r in actionable_results
                if r.recommendation.confidence >= min_confidence
            ]
            
            if not filtered_results:
                console.print(Panel(
                    f"[yellow]No recommendations found with confidence >= {min_confidence:.0%}[/yellow]\n\n"
                    f"Found {len(actionable_results)} actionable recommendations with lower confidence.\n"
                    f"Try lowering the threshold with --min-confidence 0.5",
                    title="⚠️  No High-Confidence Opportunities",
                    border_style="yellow"
                ))
            else:
                # Limit results
                filtered_results = filtered_results[:limit]
                
                console.print(Panel(
                    f"[bold green]Found {len(filtered_results)} actionable recommendation(s)[/bold green]",
                    title="✅ Top Stock Recommendations",
                    border_style="green"
                ))
                console.print()
                
                # Display each opportunity
                for i, result in enumerate(filtered_results, 1):
                    symbol = result.symbol
                    rec = result.recommendation
                    
                    # Determine action color
                    action_color = "green" if rec.action == "BUY" else "red"
                    
                    console.print(f"[bold cyan]{i}. {symbol}[/bold cyan]")
                    
                    # Create summary table
                    summary_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
                    summary_table.add_row("Action:", f"[bold {action_color}]{rec.action}[/bold {action_color}]")
                    summary_table.add_row("Confidence:", f"{rec.confidence:.0%}")
                    
                    # Get mention count if available
                    mention_count = 0
                    if not symbols:  # Only show mentions for news-driven discovery
                        for stock in discovered_stocks:
                            if stock.symbol == symbol:
                                mention_count = stock.mention_count
                                break
                        if mention_count > 0:
                            summary_table.add_row("News Mentions:", str(mention_count))
                    
                    if rec.entry_price_low and rec.entry_price_high:
                        summary_table.add_row(
                            "Entry Range:",
                            f"${rec.entry_price_low:.2f} - ${rec.entry_price_high:.2f}"
                        )
                    
                    if rec.exit_price_low and rec.exit_price_high:
                        summary_table.add_row(
                            "Exit Range:",
                            f"${rec.exit_price_low:.2f} - ${rec.exit_price_high:.2f}"
                        )
                    
                    summary_table.add_row("Sentiment:", f"{result.sentiment.sentiment_score:+.2f} ({len(result.sentiment.sources)} sources)")
                    summary_table.add_row("Technical:", f"{result.technical.technical_score:+.2f} (RSI: {result.technical.rsi:.1f})")
                    summary_table.add_row("Fundamental:", f"{result.fundamental.fundamental_score:+.2f}")
                    
                    console.print(summary_table)
                    
                    # Show plain English summary
                    console.print(Panel(
                        _generate_plain_english_summary(result),
                        border_style="cyan",
                        padding=(0, 1)
                    ))
                    
                    if i < len(filtered_results):
                        console.print()
                
                # Display summary
                console.print()
                console.print(f"[dim]Summary: Discovered {len(discovered_stocks) if not symbols else len(symbols)} stocks, "
                             f"analyzed {len(analysis_results)}, found {len(actionable_results)} actionable recommendations[/dim]")
        
        # Display disclaimers
        console.print()
        console.print(display_recommendation_disclaimer())
        console.print(display_past_performance_warning())
        
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}", style="red")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        console.print("\n[dim]Please check your configuration and try again.[/dim]")
        sys.exit(1)


@cli.command()
@click.argument('trade_id')
@click.argument('exit_price', type=float)
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
@click.option('--notes', '-n', type=str, default='', help='Optional notes about the exit')
def close_trade(trade_id: str, exit_price: float, config: Optional[str], notes: str):
    """
    Close an open trade and record the exit.
    
    TRADE_ID: Trade ID to close
    EXIT_PRICE: Exit price for the trade
    
    Examples:
        stock-agent close-trade AAPL_20250125_143000 155.50
        stock-agent close-trade TSLA_20250120_100000 245.75 --notes "Target reached"
    """
    try:
        console.print(f"\n[bold cyan]Closing trade {trade_id}...[/bold cyan]\n")
        
        # Load configuration
        cfg = Configuration.load(config) if config else Configuration()
        
        if not cfg.performance_tracking_enabled:
            console.print("[yellow]Performance tracking is not enabled in configuration.[/yellow]")
            sys.exit(0)
        
        # Initialize performance tracker
        from src.performance_tracker import PerformanceTracker
        tracker = PerformanceTracker(cfg.performance_storage_path)
        
        # Close the trade
        trade = tracker.record_exit(trade_id, exit_price, notes)
        
        if not trade:
            console.print(f"[bold red]Error:[/bold red] Trade not found: {trade_id}", style="red")
            sys.exit(1)
        
        # Display trade summary
        console.print(Panel(
            f"[bold green]Trade Closed Successfully[/bold green]",
            border_style="green"
        ))
        
        console.print()
        trade_table = Table(show_header=False, box=box.SIMPLE)
        trade_table.add_row("Symbol:", trade.symbol)
        trade_table.add_row("Action:", trade.action)
        trade_table.add_row("Entry Price:", f"${trade.entry_price:.2f}")
        trade_table.add_row("Exit Price:", f"${trade.exit_price:.2f}")
        trade_table.add_row("Quantity:", str(trade.quantity))
        
        # Color-code P/L
        pl_color = "green" if trade.profit_loss_percent > 0 else "red"
        trade_table.add_row(
            "Profit/Loss:",
            f"[{pl_color}]{trade.profit_loss_percent:+.2f}%[/{pl_color}] (${trade.profit_loss:+.2f})"
        )
        trade_table.add_row("Holding Period:", f"{trade.holding_period_days} days")
        trade_table.add_row("Entry Date:", trade.entry_date[:10])
        trade_table.add_row("Exit Date:", trade.exit_date[:10])
        
        console.print(trade_table)
        
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
@click.option('--month', '-m', type=int, help='Month (1-12), defaults to last month')
@click.option('--year', '-y', type=int, help='Year, defaults to current year')
def performance(config: Optional[str], month: Optional[int], year: Optional[int]):
    """
    Generate and display performance report.
    
    Examples:
        stock-agent performance
        stock-agent performance --month 12 --year 2024
    """
    try:
        console.print("\n[bold cyan]Generating Performance Report...[/bold cyan]\n")
        
        # Load configuration
        cfg = Configuration.load(config) if config else Configuration()
        
        if not cfg.performance_tracking_enabled:
            console.print("[yellow]Performance tracking is not enabled in configuration.[/yellow]")
            sys.exit(0)
        
        # Initialize performance tracker
        from src.performance_tracker import PerformanceTracker
        tracker = PerformanceTracker(cfg.performance_storage_path)
        
        # Generate report
        report = tracker.generate_monthly_report(month, year)
        
        # Display report
        period_str = f"{report.period_start[:7]} to {report.period_end[:7]}"
        console.print(Panel(
            f"[bold]Performance Report[/bold]\n{period_str}",
            border_style="cyan"
        ))
        
        console.print()
        
        # Overall metrics
        console.print("[bold]📊 Overall Performance[/bold]")
        overall_table = Table(show_header=False, box=box.SIMPLE)
        overall_table.add_row("Total Trades:", str(report.total_trades))
        overall_table.add_row("Open Trades:", str(report.open_trades))
        overall_table.add_row("Closed Trades:", str(report.closed_trades))
        overall_table.add_row("Winning Trades:", f"[green]{report.winning_trades}[/green]")
        overall_table.add_row("Losing Trades:", f"[red]{report.losing_trades}[/red]")
        
        win_rate_color = "green" if report.win_rate >= 60 else "yellow" if report.win_rate >= 50 else "red"
        overall_table.add_row("Win Rate:", f"[{win_rate_color}]{report.win_rate:.1f}%[/{win_rate_color}]")
        
        pl_color = "green" if report.total_profit_loss > 0 else "red"
        overall_table.add_row("Total P/L:", f"[{pl_color}]{report.total_profit_loss:+.2f}%[/{pl_color}]")
        overall_table.add_row("Avg P/L:", f"[{pl_color}]{report.avg_profit_loss:+.2f}%[/{pl_color}]")
        
        console.print(overall_table)
        console.print()
        
        # Best and worst trades
        if report.best_trade:
            console.print("[bold]🏆 Best Trade[/bold]")
            best_table = Table(show_header=False, box=box.SIMPLE)
            best_table.add_row("Symbol:", report.best_trade['symbol'])
            best_table.add_row("P/L:", f"[green]{report.best_trade['profit_loss_percent']:+.2f}%[/green]")
            best_table.add_row("Date:", f"{report.best_trade['entry_date'][:10]} → {report.best_trade['exit_date'][:10]}")
            console.print(best_table)
            console.print()
        
        if report.worst_trade:
            console.print("[bold]📉 Worst Trade[/bold]")
            worst_table = Table(show_header=False, box=box.SIMPLE)
            worst_table.add_row("Symbol:", report.worst_trade['symbol'])
            worst_table.add_row("P/L:", f"[red]{report.worst_trade['profit_loss_percent']:+.2f}%[/red]")
            worst_table.add_row("Date:", f"{report.worst_trade['entry_date'][:10]} → {report.worst_trade['exit_date'][:10]}")
            console.print(worst_table)
            console.print()
        
        # Module performance
        console.print("[bold]🔍 Module Performance Analysis[/bold]")
        module_table = Table(box=box.SIMPLE_HEAD)
        module_table.add_column("Module", style="cyan")
        module_table.add_column("Trades", justify="right")
        module_table.add_column("Win Rate", justify="right")
        module_table.add_column("Avg P/L", justify="right")
        module_table.add_column("Accuracy", justify="right")
        module_table.add_column("Weight", justify="right")
        
        for module_name, perf in report.module_performance.items():
            win_rate_color = "green" if perf.win_rate >= 60 else "yellow" if perf.win_rate >= 50 else "red"
            pl_color = "green" if perf.avg_profit_loss > 0 else "red"
            accuracy_color = "green" if perf.accuracy_score >= 0.7 else "yellow" if perf.accuracy_score >= 0.5 else "red"
            
            module_table.add_row(
                module_name.capitalize(),
                str(perf.total_trades),
                f"[{win_rate_color}]{perf.win_rate:.1f}%[/{win_rate_color}]",
                f"[{pl_color}]{perf.avg_profit_loss:+.2f}%[/{pl_color}]",
                f"[{accuracy_color}]{perf.accuracy_score:.2f}[/{accuracy_color}]",
                f"{perf.recommended_weight:.2f}"
            )
        
        console.print(module_table)
        console.print()
        
        # Recommended weights
        console.print("[bold]⚖️  Recommended Weights for Next Period[/bold]")
        weights_table = Table(show_header=False, box=box.SIMPLE)
        for module_name, weight in report.recommended_weights.items():
            weights_table.add_row(f"{module_name.capitalize()}:", f"{weight:.2f} ({weight*100:.0f}%)")
        console.print(weights_table)
        
        console.print()
        console.print("[dim]💡 Tip: Enable auto_adjust_weights in config to automatically apply these weights.[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}", style="red")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def open_trades(config: Optional[str]):
    """
    List all open trades.
    
    Example:
        stock-agent open-trades
    """
    try:
        console.print("\n[bold cyan]Open Trades[/bold cyan]\n")
        
        # Load configuration
        cfg = Configuration.load(config) if config else Configuration()
        
        if not cfg.performance_tracking_enabled:
            console.print("[yellow]Performance tracking is not enabled in configuration.[/yellow]")
            sys.exit(0)
        
        # Initialize performance tracker
        from src.performance_tracker import PerformanceTracker
        tracker = PerformanceTracker(cfg.performance_storage_path)
        
        # Get open trades
        trades = tracker.get_open_trades()
        
        if not trades:
            console.print("[yellow]No open trades found.[/yellow]")
            sys.exit(0)
        
        # Display trades
        trades_table = Table(box=box.SIMPLE_HEAD)
        trades_table.add_column("Trade ID", style="cyan")
        trades_table.add_column("Symbol")
        trades_table.add_column("Action")
        trades_table.add_column("Entry Price", justify="right")
        trades_table.add_column("Quantity", justify="right")
        trades_table.add_column("Entry Date")
        trades_table.add_column("Days Held", justify="right")
        
        for trade in trades:
            entry_date = datetime.fromisoformat(trade.entry_date)
            days_held = (datetime.now() - entry_date).days
            
            action_color = "green" if trade.action == "BUY" else "red"
            
            trades_table.add_row(
                trade.trade_id,
                trade.symbol,
                f"[{action_color}]{trade.action}[/{action_color}]",
                f"${trade.entry_price:.2f}",
                str(trade.quantity),
                trade.entry_date[:10],
                str(days_held)
            )
        
        console.print(trades_table)
        console.print()
        console.print(f"[dim]Total: {len(trades)} open trade(s)[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}", style="red")
        sys.exit(1)


if __name__ == '__main__':
    cli()
