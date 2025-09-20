#!/usr/bin/env python3
"""
ALGO Staking Yields CLI - Analyze ALGO staking rates and governance participation
"""

import asyncio
import json
from decimal import Decimal

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from algosdk.v2client import algod
from interest_rate_determiner.engines import AlgoStakingEngine

app = typer.Typer(name="staking-yields", help="ALGO Staking Yield Analysis")
console = Console()

@app.command()
def analyze(
    algod_url: str = typer.Option("https://mainnet-api.algonode.cloud", "--algod-url", help="Algorand node URL"),
    historical_periods: int = typer.Option(12, "--periods", help="Historical periods to analyze"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json")
):
    """Analyze current ALGO staking yields and participation"""

    async def run_analysis():
        algod_client = algod.AlgodClient("", algod_url)
        engine = AlgoStakingEngine(algod_client)

        console.print(Panel.fit("🏦 ALGO Staking Yield Analysis", title="Staking Analysis"))

        try:
            metrics = await engine.calculate_staking_rate(historical_periods=historical_periods)

            if output_format == "json":
                result = {
                    'current_apy': float(metrics.current_apy),
                    'historical_avg_apy': float(metrics.historical_avg_apy),
                    'participation_rate': float(metrics.participation_rate),
                    'total_staked_algo': float(metrics.total_staked_algo),
                    'governance_participation': float(metrics.governance_participation),
                    'validator_performance': float(metrics.validator_performance),
                    'risk_adjusted_yield': float(metrics.risk_adjusted_yield())
                }
                console.print(json.dumps(result, indent=2))
            else:
                table = Table(title="🏆 ALGO Staking Metrics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                table.add_column("Description", style="dim")

                table.add_row("Current APY", f"{metrics.current_apy*100:.2f}%", "Current staking yield")
                table.add_row("Historical Avg APY", f"{metrics.historical_avg_apy*100:.2f}%", f"Average over {historical_periods} periods")
                table.add_row("Participation Rate", f"{metrics.participation_rate*100:.1f}%", "Network participation")
                table.add_row("Total Staked", f"{metrics.total_staked_algo:,.0f} μALGO", "Total online stake")
                table.add_row("Governance Rate", f"{metrics.governance_participation*100:.1f}%", "Governance participation")
                table.add_row("Validator Performance", f"{metrics.validator_performance*100:.1f}%", "Average validator performance")
                table.add_row("[bold]Risk-Adjusted Yield[/bold]", f"[bold]{metrics.risk_adjusted_yield()*100:.2f}%[/bold]", "Final adjusted yield")

                console.print(table)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(run_analysis())

@app.command()
def recommendations(
    loan_amount: float = typer.Argument(..., help="Loan amount in ALGO"),
    loan_term_days: int = typer.Option(365, "--term", help="Loan term in days"),
    borrower_reputation: float = typer.Option(None, "--reputation", help="Borrower reputation score (0-1)")
):
    """Get rate recommendations based on staking yields"""

    async def run_recommendations():
        algod_client = algod.AlgodClient("", "https://mainnet-api.algonode.cloud")
        engine = AlgoStakingEngine(algod_client)

        try:
            recommendations = await engine.get_rate_recommendations(
                loan_amount=Decimal(str(loan_amount)),
                loan_term_days=loan_term_days,
                borrower_reputation=Decimal(str(borrower_reputation)) if borrower_reputation else None
            )

            table = Table(title="📊 Rate Recommendations Based on ALGO Staking")
            table.add_column("Component", style="cyan")
            table.add_column("Rate", style="green")
            table.add_column("Impact", style="yellow")

            table.add_row("Base Staking Rate", f"{recommendations['base_staking_rate']*100:.3f}%", "From current yields")
            table.add_row("Term Adjustment", f"{recommendations['term_adjustment']*100:+.3f}%", f"{loan_term_days} days")
            if 'reputation_adjustment' in recommendations:
                table.add_row("Reputation Adjustment", f"{recommendations['reputation_adjustment']*100:+.3f}%", "Borrower history")
            table.add_row("[bold]Recommended Rate[/bold]", f"[bold]{recommendations['recommended_rate']*100:.3f}%[/bold]", "Final recommendation")
            table.add_row("Rate Range", f"{recommendations['min_rate']*100:.3f}% - {recommendations['max_rate']*100:.3f}%", "Acceptable range")

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(run_recommendations())

if __name__ == "__main__":
    app()