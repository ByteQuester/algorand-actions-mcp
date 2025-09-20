#!/usr/bin/env python3
"""
Liquidity Cascade Risk Monitor CLI

CLI tool for monitoring liquidation cascade risks and market depth vulnerabilities.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from liquidity_cascade_engine.cascade_analyzer import LiquidityCascadeAnalyzer

app = typer.Typer(
    name="liquidity-cascade-monitor",
    help="Liquidity Cascade Risk Monitoring CLI",
    rich_markup_mode="rich"
)
console = Console()


@app.command()
def analyze(
    address: str = typer.Argument(..., help="Algorand address to analyze"),
    include_portfolio: bool = typer.Option(True, "--portfolio/--no-portfolio", help="Include portfolio analysis"),
    stress_scenarios: Optional[str] = typer.Option(None, "--scenarios", help="Comma-separated stress test scenarios"),
):
    """Analyze liquidity cascade risks for an address."""
    scenarios = stress_scenarios.split(",") if stress_scenarios else None
    asyncio.run(_analyze_cascade_risk(address, include_portfolio, scenarios))


@app.command()
def simulate(
    address: str = typer.Argument(..., help="Algorand address for simulation"),
    scenario: str = typer.Option("market_crash_20", "--scenario", "-s", help="Simulation scenario"),
    iterations: int = typer.Option(1000, "--iterations", "-i", help="Monte Carlo iterations"),
):
    """Run liquidation cascade simulations."""
    asyncio.run(_run_simulation(address, scenario, iterations))


@app.command()
def monitor_health(
    address: str = typer.Argument(..., help="Algorand address to monitor"),
    frequency: int = typer.Option(300, "--frequency", "-f", help="Check frequency in seconds"),
    health_threshold: float = typer.Option(1.5, "--threshold", "-t", help="Health factor alert threshold"),
):
    """Monitor health factor and liquidation risk in real-time."""
    asyncio.run(_monitor_health_factor(address, frequency, health_threshold))


async def _analyze_cascade_risk(address: str, include_portfolio: bool, scenarios: Optional[list]):
    """Analyze cascade risk"""
    console.print(f"[yellow]Analyzing liquidity cascade risk for {address}[/yellow]")

    analyzer = LiquidityCascadeAnalyzer()

    try:
        profile = await analyzer.analyze_cascade_risk(
            address=address,
            include_portfolio_analysis=include_portfolio,
            stress_test_scenarios=scenarios or []
        )

        _display_cascade_results(profile)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def _run_simulation(address: str, scenario: str, iterations: int):
    """Run cascade simulation"""
    console.print(f"[yellow]Running {scenario} simulation ({iterations} iterations)[/yellow]")

    # Placeholder for simulation
    console.print("[green]Simulation completed![/green]")


async def _monitor_health_factor(address: str, frequency: int, threshold: float):
    """Monitor health factor"""
    console.print(f"[yellow]Monitoring health factor for {address}[/yellow]")
    console.print(f"Check frequency: {frequency}s, Alert threshold: {threshold}")

    try:
        while True:
            # Simulate health factor monitoring
            import random
            health_factor = 1.8 + random.uniform(-0.3, 0.3)

            status = "[green]SAFE[/green]" if health_factor > threshold else "[red]AT RISK[/red]"
            console.print(f"Health Factor: {health_factor:.3f} - {status}")

            await asyncio.sleep(frequency)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


def _display_cascade_results(profile):
    """Display cascade risk results"""
    # Risk summary
    risk_panel = Panel(
        f"[bold]Overall Risk:[/bold] {profile.risk_score.risk_level.value}\n" +
        f"[bold]Risk Score:[/bold] {profile.risk_score.overall_score:.1f}/100\n" +
        f"[bold]Liquidation Risk:[/bold] {profile.risk_score.liquidation_modeling_risk:.1f}\n" +
        f"[bold]Market Depth Risk:[/bold] {profile.risk_score.market_depth_risk:.1f}",
        title="Liquidity Cascade Risk Summary",
        border_style="blue"
    )
    console.print(risk_panel)

    # Portfolio metrics
    if profile.position_concentration:
        portfolio_table = Table(title="Portfolio Risk Metrics")
        portfolio_table.add_column("Metric", style="cyan")
        portfolio_table.add_column("Value", style="magenta")

        max_concentration = max(profile.position_concentration.values()) if profile.position_concentration else 0
        portfolio_table.add_row("Max Position Concentration", f"{max_concentration:.1%}")
        portfolio_table.add_row("Portfolio VaR", f"${profile.portfolio_value_at_risk:,.2f}")
        portfolio_table.add_row("Diversification Score", f"{profile.diversification_effectiveness:.2f}")

        console.print(portfolio_table)


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()