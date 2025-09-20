#!/usr/bin/env python3
"""
ALGO Rate Calculator CLI

Main interface for calculating interest rates using all 6 Algorand-native engines.
"""

import asyncio
import json
import sys
from decimal import Decimal
from datetime import datetime
from pathlib import Path

import click
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from algosdk.v2client import algod, indexer

from interest_rate_determiner.engines import (
    AlgoStakingEngine,
    DeFiYieldEngine,
    ReputationEngine,
    ASARiskEngine,
    NetworkActivityEngine,
    LiquidityPoolEngine
)

app = typer.Typer(name="algo-rate-calculator", help="Algorand DeFi Interest Rate Calculator")
console = Console()

# Default configuration
DEFAULT_ALGOD_URL = "https://mainnet-api.algonode.cloud"
DEFAULT_INDEXER_URL = "https://mainnet-idx.algonode.cloud"

class RateCalculator:
    """Main rate calculation orchestrator"""

    def __init__(self, algod_url: str, indexer_url: str):
        self.algod_client = algod.AlgodClient("", algod_url)
        self.indexer_client = indexer.IndexerClient("", indexer_url)

        # Initialize all engines
        self.engines = {
            'staking': AlgoStakingEngine(self.algod_client),
            'defi': DeFiYieldEngine(self.algod_client, {}),
            'reputation': ReputationEngine(self.algod_client, self.indexer_client),
            'asa_risk': ASARiskEngine(self.algod_client, self.indexer_client, {}),
            'network': NetworkActivityEngine(self.algod_client),
            'liquidity': LiquidityPoolEngine(self.algod_client)
        }

    async def calculate_comprehensive_rate(
        self,
        loan_amount: Decimal,
        loan_term_days: int,
        borrower_address: str = None,
        collateral_asset_id: int = None
    ) -> dict:
        """Calculate comprehensive interest rate using all engines"""

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Step 1: Base rates
            task1 = progress.add_task("Analyzing ALGO staking yields...", total=None)
            staking_metrics = await self.engines['staking'].calculate_staking_rate()
            progress.update(task1, completed=True)

            task2 = progress.add_task("Aggregating DeFi protocol rates...", total=None)
            defi_metrics = await self.engines['defi'].calculate_defi_rates()
            progress.update(task2, completed=True)

            # Base rate calculation
            base_rate = (staking_metrics.current_apy + defi_metrics.weighted_avg_apy) / Decimal('2')

            # Step 2: Borrower reputation (if address provided)
            reputation_adjustment = Decimal('0')
            reputation_data = None
            if borrower_address:
                task3 = progress.add_task("Analyzing borrower reputation...", total=None)
                try:
                    reputation_data = await self.engines['reputation'].calculate_reputation(borrower_address)
                    reputation_adjustment = reputation_data.rate_discount() - reputation_data.rate_premium()
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not analyze reputation: {e}[/yellow]")
                progress.update(task3, completed=True)

            # Step 3: Collateral risk (if asset provided)
            collateral_adjustment = Decimal('0')
            collateral_data = None
            if collateral_asset_id:
                task4 = progress.add_task("Analyzing collateral risk...", total=None)
                try:
                    collateral_data = await self.engines['asa_risk'].analyze_asa_risk(collateral_asset_id)
                    collateral_adjustment = collateral_data.rate_adjustment()
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not analyze collateral: {e}[/yellow]")
                progress.update(task4, completed=True)

            # Step 4: Network conditions
            task5 = progress.add_task("Monitoring network activity...", total=None)
            network_adjustments = await self.engines['network'].get_rate_adjustments()
            network_adjustment = network_adjustments.get('congestion_adjustment', Decimal('0'))
            progress.update(task5, completed=True)

            # Step 5: Liquidity conditions
            task6 = progress.add_task("Analyzing liquidity pools...", total=None)
            liquidity_adjustments = await self.engines['liquidity'].get_liquidity_adjustments()
            liquidity_adjustment = liquidity_adjustments.get('liquidity_health_bonus', Decimal('0'))
            progress.update(task6, completed=True)

        # Calculate final rate
        final_rate = (
            base_rate +
            reputation_adjustment +
            collateral_adjustment +
            network_adjustment -
            liquidity_adjustment
        )

        # Apply bounds
        min_rate = Decimal('0.02')  # 2% minimum
        max_rate = Decimal('0.25')  # 25% maximum
        final_rate = max(min_rate, min(final_rate, max_rate))

        # Calculate loan terms
        annual_interest = loan_amount * final_rate
        monthly_payment = annual_interest / Decimal('12')

        return {
            'calculation_timestamp': datetime.utcnow().isoformat(),
            'loan_parameters': {
                'principal': float(loan_amount),
                'term_days': loan_term_days,
                'borrower_address': borrower_address,
                'collateral_asset_id': collateral_asset_id
            },
            'rate_components': {
                'base_rate': float(base_rate),
                'staking_apy': float(staking_metrics.current_apy),
                'defi_apy': float(defi_metrics.weighted_avg_apy),
                'reputation_adjustment': float(reputation_adjustment),
                'collateral_adjustment': float(collateral_adjustment),
                'network_adjustment': float(network_adjustment),
                'liquidity_adjustment': float(-liquidity_adjustment)
            },
            'final_rate': float(final_rate),
            'loan_terms': {
                'annual_interest_amount': float(annual_interest),
                'monthly_payment': float(monthly_payment),
                'effective_apr': float(final_rate)
            },
            'engine_data': {
                'staking_metrics': {
                    'participation_rate': float(staking_metrics.participation_rate),
                    'governance_participation': float(staking_metrics.governance_participation)
                } if staking_metrics else None,
                'defi_metrics': {
                    'protocol_count': defi_metrics.protocol_count,
                    'total_tvl': float(defi_metrics.total_tvl),
                    'volatility_score': float(defi_metrics.volatility_score)
                } if defi_metrics else None,
                'reputation_data': {
                    'overall_score': float(reputation_data.overall_score),
                    'tier': reputation_data.tier.value,
                    'confidence_level': float(reputation_data.confidence_level)
                } if reputation_data else None,
                'collateral_data': {
                    'risk_level': collateral_data.risk_level.value,
                    'collateral_factor': float(collateral_data.collateral_factor),
                    'volatility_score': float(collateral_data.volatility_score)
                } if collateral_data else None
            }
        }

@app.command()
def calculate(
    loan_amount: float = typer.Argument(..., help="Loan amount in ALGO"),
    loan_term_days: int = typer.Argument(365, help="Loan term in days (default: 365)"),
    borrower_address: str = typer.Option(None, "--borrower", "-b", help="Borrower's Algorand address"),
    collateral_asset_id: int = typer.Option(None, "--collateral", "-c", help="Collateral ASA ID"),
    algod_url: str = typer.Option(DEFAULT_ALGOD_URL, "--algod-url", help="Algorand node URL"),
    indexer_url: str = typer.Option(DEFAULT_INDEXER_URL, "--indexer-url", help="Algorand indexer URL"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
    save_file: str = typer.Option(None, "--save", "-s", help="Save results to file")
):
    """Calculate interest rate for an Algorand DeFi loan"""

    console.print(Panel.fit(
        "[bold blue]ALGORAND DEFI INTEREST RATE CALCULATOR[/bold blue]\\n"
        "Analyzing blockchain data across 6 specialized engines...",
        title="🔥 Rate Calculation"
    ))

    async def run_calculation():
        calculator = RateCalculator(algod_url, indexer_url)

        try:
            result = await calculator.calculate_comprehensive_rate(
                loan_amount=Decimal(str(loan_amount)),
                loan_term_days=loan_term_days,
                borrower_address=borrower_address,
                collateral_asset_id=collateral_asset_id
            )

            if output_format == "json":
                output = json.dumps(result, indent=2)
                console.print(output)
            else:
                display_results_table(result)

            if save_file:
                with open(save_file, 'w') as f:
                    json.dump(result, f, indent=2)
                console.print(f"[green]Results saved to {save_file}[/green]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    asyncio.run(run_calculation())

def display_results_table(result: dict):
    """Display results in a formatted table"""

    # Main results table
    table = Table(title="🎯 Interest Rate Calculation Results", show_header=True)
    table.add_column("Component", style="cyan", width=25)
    table.add_column("Value", style="green", width=15)
    table.add_column("Impact", style="yellow", width=10)

    loan_params = result['loan_parameters']
    rate_components = result['rate_components']
    loan_terms = result['loan_terms']

    # Loan parameters
    table.add_row("💰 Loan Amount", f"{loan_params['principal']:,.0f} ALGO", "")
    table.add_row("📅 Loan Term", f"{loan_params['term_days']} days", "")
    table.add_row("", "", "")

    # Rate components
    table.add_row("🏦 Base Rate", f"{rate_components['base_rate']:.4f}", "")
    table.add_row("├─ ALGO Staking APY", f"{rate_components['staking_apy']:.4f}", "")
    table.add_row("└─ DeFi Market APY", f"{rate_components['defi_apy']:.4f}", "")
    table.add_row("", "", "")

    # Adjustments
    if rate_components['reputation_adjustment'] != 0:
        adj_type = "Discount" if rate_components['reputation_adjustment'] < 0 else "Premium"
        table.add_row(f"👤 Reputation {adj_type}", f"{rate_components['reputation_adjustment']:+.4f}",
                     f"{rate_components['reputation_adjustment']*100:+.2f}%")

    if rate_components['collateral_adjustment'] != 0:
        table.add_row("🔒 Collateral Risk", f"{rate_components['collateral_adjustment']:+.4f}",
                     f"{rate_components['collateral_adjustment']*100:+.2f}%")

    if rate_components['network_adjustment'] != 0:
        table.add_row("🌐 Network Conditions", f"{rate_components['network_adjustment']:+.4f}",
                     f"{rate_components['network_adjustment']*100:+.2f}%")

    if rate_components['liquidity_adjustment'] != 0:
        table.add_row("💧 Liquidity Bonus", f"{rate_components['liquidity_adjustment']:+.4f}",
                     f"{rate_components['liquidity_adjustment']*100:+.2f}%")

    table.add_row("", "", "")
    table.add_row("🎯 [bold]FINAL RATE[/bold]", f"[bold]{result['final_rate']:.4f}[/bold]",
                 f"[bold]{result['final_rate']*100:.2f}%[/bold]")

    console.print(table)

    # Loan terms table
    terms_table = Table(title="📊 Loan Terms", show_header=True)
    terms_table.add_column("Term", style="cyan")
    terms_table.add_column("Amount", style="green")

    terms_table.add_row("Annual Interest", f"{loan_terms['annual_interest_amount']:,.2f} ALGO")
    terms_table.add_row("Monthly Payment", f"{loan_terms['monthly_payment']:,.2f} ALGO")
    terms_table.add_row("Effective APR", f"{loan_terms['effective_apr']*100:.2f}%")

    console.print(terms_table)

@app.command()
def compare(
    loan_amount: float = typer.Argument(..., help="Loan amount in ALGO"),
    scenarios: str = typer.Option("standard,excellent,risky", "--scenarios", help="Comma-separated scenarios")
):
    """Compare rates across different borrower scenarios"""

    scenario_configs = {
        'excellent': {
            'borrower_address': 'EXCELLENTBORROWER1234567890123456789012345678901234567890',
            'collateral_asset_id': None,
            'description': 'Excellent borrower, no specific collateral'
        },
        'standard': {
            'borrower_address': None,
            'collateral_asset_id': None,
            'description': 'Standard borrower, no reputation data'
        },
        'risky': {
            'borrower_address': 'RISKYBORROWER1234567890123456789012345678901234567890123',
            'collateral_asset_id': 12345,
            'description': 'New borrower with volatile ASA collateral'
        }
    }

    console.print(Panel.fit(
        "[bold blue]SCENARIO COMPARISON[/bold blue]\\n"
        f"Comparing rates for {loan_amount:,.0f} ALGO loan",
        title="🔀 Rate Comparison"
    ))

    async def run_comparison():
        calculator = RateCalculator(DEFAULT_ALGOD_URL, DEFAULT_INDEXER_URL)

        comparison_table = Table(title="📈 Rate Comparison Across Scenarios")
        comparison_table.add_column("Scenario", style="cyan")
        comparison_table.add_column("Final Rate", style="green")
        comparison_table.add_column("Annual Interest", style="yellow")
        comparison_table.add_column("Description", style="dim")

        for scenario in scenarios.split(','):
            scenario = scenario.strip()
            if scenario in scenario_configs:
                config = scenario_configs[scenario]

                try:
                    result = await calculator.calculate_comprehensive_rate(
                        loan_amount=Decimal(str(loan_amount)),
                        loan_term_days=365,
                        borrower_address=config['borrower_address'],
                        collateral_asset_id=config['collateral_asset_id']
                    )

                    comparison_table.add_row(
                        scenario.title(),
                        f"{result['final_rate']*100:.2f}%",
                        f"{result['loan_terms']['annual_interest_amount']:,.0f} ALGO",
                        config['description']
                    )

                except Exception as e:
                    comparison_table.add_row(
                        scenario.title(),
                        "Error",
                        "N/A",
                        f"Error: {str(e)[:50]}..."
                    )

        console.print(comparison_table)

    asyncio.run(run_comparison())

@app.command()
def monitor(
    duration: int = typer.Option(60, "--duration", "-d", help="Monitoring duration in seconds"),
    interval: int = typer.Option(10, "--interval", "-i", help="Update interval in seconds")
):
    """Monitor real-time rate changes"""

    console.print(Panel.fit(
        "[bold blue]REAL-TIME RATE MONITORING[/bold blue]\\n"
        f"Monitoring for {duration}s with {interval}s intervals",
        title="📊 Live Monitoring"
    ))

    async def monitor_rates():
        calculator = RateCalculator(DEFAULT_ALGOD_URL, DEFAULT_INDEXER_URL)

        start_time = datetime.now()
        end_time = start_time.timestamp() + duration

        rates_history = []

        while datetime.now().timestamp() < end_time:
            try:
                result = await calculator.calculate_comprehensive_rate(
                    loan_amount=Decimal('100000'),  # Standard 100k ALGO loan
                    loan_term_days=365
                )

                rates_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'rate': result['final_rate'],
                    'base_rate': result['rate_components']['base_rate']
                })

                # Display current rate
                console.print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                             f"Rate: {result['final_rate']*100:.3f}% "
                             f"(Base: {result['rate_components']['base_rate']*100:.3f}%)")

                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                await asyncio.sleep(interval)

        # Show summary
        if rates_history:
            rates = [r['rate'] for r in rates_history]
            console.print(f"\\n[bold]Monitoring Summary:[/bold]")
            console.print(f"Min Rate: {min(rates)*100:.3f}%")
            console.print(f"Max Rate: {max(rates)*100:.3f}%")
            console.print(f"Avg Rate: {sum(rates)/len(rates)*100:.3f}%")
            console.print(f"Samples: {len(rates_history)}")

    asyncio.run(monitor_rates())

if __name__ == "__main__":
    app()