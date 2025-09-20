#!/usr/bin/env python3
"""
Market Analyzer CLI

Command-line interface specifically for the Market Rate Analysis Engine.
"""

import asyncio
import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .. import MarketRateAnalysisEngine

app = typer.Typer(
    name="market-analyzer",
    help="Market Rate Analysis CLI for Algorand DeFi Lending",
    add_completion=False
)
console = Console()


@app.command()
def analyze(
    asset: str = typer.Option("ALGO", "--asset", "-a", help="Asset to analyze"),
    hours: int = typer.Option(24, "--hours", "-h", help="Analysis period in hours"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json")
):
    """Analyze market rates for the specified asset."""

    async def _analyze():
        try:
            if not MarketRateAnalysisEngine:
                rprint("[bold red]Market Rate Analysis Engine not available[/bold red]")
                raise typer.Exit(1)

            rprint(f"[cyan]Analyzing market rates for {asset} over {hours} hours...[/cyan]")

            engine = MarketRateAnalysisEngine()
            analysis = await engine.analyze_market_rates(asset, hours)

            if output_format == "json":
                result = {
                    'asset': asset,
                    'base_rate': float(analysis.base_rate),
                    'market_sentiment': analysis.market_sentiment,
                    'volatility_score': analysis.volatility_score,
                    'liquidity_score': analysis.liquidity_score,
                    'confidence': analysis.confidence,
                    'recommendation': analysis.recommendation,
                    'risk_factors': analysis.risk_factors,
                    'timestamp': analysis.analysis_timestamp.isoformat()
                }
                print(json.dumps(result, indent=2))
            else:
                # Display results in table format
                table = Table(title=f"Market Analysis Results for {asset}")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Base Rate", f"{analysis.base_rate:.4%}")
                table.add_row("Market Sentiment", analysis.market_sentiment)
                table.add_row("Volatility Score", f"{analysis.volatility_score:.2f}")
                table.add_row("Liquidity Score", f"{analysis.liquidity_score:.2f}")
                table.add_row("Confidence", f"{analysis.confidence:.2%}")

                console.print(table)

                if analysis.recommendation:
                    rprint(f"\n[bold]Recommendation:[/bold] {analysis.recommendation}")

                if analysis.risk_factors:
                    rprint(f"\n[bold red]Risk Factors:[/bold red]")
                    for factor in analysis.risk_factors:
                        rprint(f"  • {factor}")

        except Exception as e:
            rprint(f"[bold red]Error in market analysis: {e}[/bold red]")
            raise typer.Exit(1)

    asyncio.run(_analyze())


@app.command()
def monitor(
    asset: str = typer.Option("ALGO", "--asset", "-a", help="Asset to monitor"),
    interval: int = typer.Option(300, "--interval", "-i", help="Monitoring interval in seconds")
):
    """Monitor market rates continuously."""

    async def _monitor():
        rprint(f"[cyan]Monitoring market rates for {asset} (interval: {interval}s)[/cyan]")
        rprint("[dim]Press Ctrl+C to stop monitoring[/dim]")

        try:
            engine = MarketRateAnalysisEngine()

            while True:
                analysis = await engine.analyze_market_rates(asset, 1)  # 1 hour analysis

                rprint(f"\n[bold blue]{analysis.analysis_timestamp.strftime('%H:%M:%S')}[/bold blue] "
                      f"Rate: {analysis.base_rate:.4%} | "
                      f"Sentiment: {analysis.market_sentiment} | "
                      f"Volatility: {analysis.volatility_score:.2f}")

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            rprint("\n[yellow]Monitoring stopped[/yellow]")
        except Exception as e:
            rprint(f"[bold red]Error in monitoring: {e}[/bold red]")
            raise typer.Exit(1)

    asyncio.run(_monitor())


def main():
    """Main entry point for market analyzer CLI."""
    app()


if __name__ == "__main__":
    main()