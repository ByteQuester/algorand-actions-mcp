#!/usr/bin/env python3
"""
DeFi Yields CLI - Monitor DeFi protocol yields across Algorand ecosystem
"""

import asyncio
import json
from decimal import Decimal

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from algosdk.v2client import algod
from interest_rate_determiner.engines import DeFiYieldEngine

app = typer.Typer(name="defi-yields", help="DeFi Protocol Yield Analysis")
console = Console()

@app.command()
def analyze(
    algod_url: str = typer.Option("https://mainnet-api.algonode.cloud", "--algod-url", help="Algorand node URL"),
    protocols: str = typer.Option("all", "--protocols", help="Comma-separated protocol names or 'all'"),
    risk_threshold: float = typer.Option(0.7, "--risk-threshold", help="Maximum risk score (0-1)"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json")
):
    """Analyze DeFi protocol yields across Algorand"""

    async def run_analysis():
        algod_client = algod.AlgodClient("", algod_url)
        engine = DeFiYieldEngine(algod_client, {})

        console.print(Panel.fit("🌊 DeFi Protocol Yield Analysis", title="DeFi Analysis"))

        try:
            protocol_list = None if protocols == "all" else protocols.split(',')

            metrics = await engine.calculate_defi_rates(
                include_protocols=protocol_list,
                risk_threshold=Decimal(str(risk_threshold))
            )

            if output_format == "json":
                result = {
                    'weighted_avg_apy': float(metrics.weighted_avg_apy),
                    'median_apy': float(metrics.median_apy),
                    'top_quartile_apy': float(metrics.top_quartile_apy),
                    'total_tvl': float(metrics.total_tvl),
                    'protocol_count': metrics.protocol_count,
                    'risk_adjusted_apy': float(metrics.risk_adjusted_apy),
                    'volatility_score': float(metrics.volatility_score)
                }
                console.print(json.dumps(result, indent=2))
            else:
                table = Table(title="🏆 DeFi Protocol Metrics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                table.add_column("Description", style="dim")

                table.add_row("Weighted Avg APY", f"{metrics.weighted_avg_apy*100:.2f}%", "TVL-weighted average")
                table.add_row("Median APY", f"{metrics.median_apy*100:.2f}%", "Middle value across protocols")
                table.add_row("Top Quartile APY", f"{metrics.top_quartile_apy*100:.2f}%", "75th percentile")
                table.add_row("Total TVL", f"${metrics.total_tvl:,.0f}", "Total value locked")
                table.add_row("Protocol Count", f"{metrics.protocol_count}", "Analyzed protocols")
                table.add_row("Risk-Adjusted APY", f"{metrics.risk_adjusted_apy*100:.2f}%", "Risk-weighted yield")
                table.add_row("Volatility Score", f"{metrics.volatility_score:.3f}", "Market volatility (0-1)")

                console.print(table)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(run_analysis())

@app.command()
def competitive_rates(
    loan_amount: float = typer.Argument(..., help="Loan amount in USD"),
    target_utilization: float = typer.Option(0.8, "--utilization", help="Target utilization rate"),
    algod_url: str = typer.Option("https://mainnet-api.algonode.cloud", "--algod-url", help="Algorand node URL")
):
    """Get competitive rates based on DeFi market conditions"""

    async def run_competitive_analysis():
        algod_client = algod.AlgodClient("", algod_url)
        engine = DeFiYieldEngine(algod_client, {})

        try:
            rates = await engine.get_competitive_rates(
                loan_amount=Decimal(str(loan_amount)),
                target_utilization=Decimal(str(target_utilization))
            )

            table = Table(title="🎯 Competitive Rate Analysis")
            table.add_column("Component", style="cyan")
            table.add_column("Rate", style="green")
            table.add_column("Description", style="dim")

            table.add_row("Market Avg APY", f"{rates['market_avg_apy']*100:.3f}%", "DeFi market average")
            table.add_row("Risk-Adjusted APY", f"{rates['risk_adjusted_apy']*100:.3f}%", "Risk-weighted market rate")
            table.add_row("Competitive Rate", f"{rates['competitive_rate']*100:.3f}%", "Below-market competitive rate")
            table.add_row("Volatility Adjustment", f"{rates['volatility_adjustment']*100:+.3f}%", "Market volatility impact")
            table.add_row("Utilization Adjustment", f"{rates['utilization_adjustment']*100:+.3f}%", f"{target_utilization*100:.0f}% target utilization")
            table.add_row("[bold]Final Rate[/bold]", f"[bold]{rates['final_rate']*100:.3f}%[/bold]", "Recommended lending rate")
            table.add_row("Market Volatility", f"{rates['market_volatility']:.3f}", "Current market stability")

            console.print(table)

            # Calculate loan terms
            annual_interest = loan_amount * rates['final_rate']
            monthly_payment = annual_interest / 12

            terms_table = Table(title="💰 Loan Terms")
            terms_table.add_column("Term", style="cyan")
            terms_table.add_column("Amount", style="green")

            terms_table.add_row("Principal", f"${loan_amount:,.2f}")
            terms_table.add_row("Annual Interest", f"${annual_interest:,.2f}")
            terms_table.add_row("Monthly Payment", f"${monthly_payment:,.2f}")

            console.print(terms_table)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(run_competitive_analysis())

@app.command()
def protocols(
    algod_url: str = typer.Option("https://mainnet-api.algonode.cloud", "--algod-url", help="Algorand node URL")
):
    """List available DeFi protocols and their current yields"""

    async def list_protocols():
        algod_client = algod.AlgodClient("", algod_url)
        engine = DeFiYieldEngine(algod_client, {})

        console.print(Panel.fit("📋 Available DeFi Protocols", title="Protocol List"))

        # Mock protocol data for demonstration
        protocols = [
            {"name": "Tinyman", "type": "DEX", "apy": "12.5%", "tvl": "$50M", "risk": "Low"},
            {"name": "Pact", "type": "DEX", "apy": "15.2%", "tvl": "$25M", "risk": "Medium"},
            {"name": "Humble", "type": "DEX", "apy": "18.7%", "tvl": "$15M", "risk": "Medium-High"},
            {"name": "Algofi", "type": "Lending", "apy": "8.3%", "tvl": "$100M", "risk": "Low"},
            {"name": "Folks Finance", "type": "Lending", "apy": "9.1%", "tvl": "$75M", "risk": "Low-Medium"}
        ]

        table = Table(title="🌊 Algorand DeFi Protocols")
        table.add_column("Protocol", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("APY", style="green")
        table.add_column("TVL", style="blue")
        table.add_column("Risk Level", style="red")

        for protocol in protocols:
            table.add_row(
                protocol["name"],
                protocol["type"],
                protocol["apy"],
                protocol["tvl"],
                protocol["risk"]
            )

        console.print(table)

    asyncio.run(list_protocols())

if __name__ == "__main__":
    app()