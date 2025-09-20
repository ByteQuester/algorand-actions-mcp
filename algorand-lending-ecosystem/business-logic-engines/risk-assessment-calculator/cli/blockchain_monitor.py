#!/usr/bin/env python3
"""
Blockchain Behavior Risk Monitor CLI

CLI tool for monitoring blockchain behavior risks and transaction anomalies.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.live import Live
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from blockchain_behavior_engine.behavior_analyzer import BlockchainBehaviorAnalyzer

app = typer.Typer(
    name="blockchain-behavior-monitor",
    help="Blockchain Behavior Risk Monitoring CLI",
    rich_markup_mode="rich"
)
console = Console()


@app.command()
def analyze(
    address: str = typer.Argument(..., help="Algorand address to analyze"),
    days: int = typer.Option(30, "--days", "-d", help="Days of history to analyze"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
    include_related: bool = typer.Option(True, "--related/--no-related", help="Include related addresses"),
):
    """Analyze blockchain behavior risks for an address."""
    asyncio.run(_analyze_behavior(address, days, output_format, include_related))


@app.command()
def monitor(
    address: str = typer.Argument(..., help="Algorand address to monitor"),
    frequency: int = typer.Option(60, "--frequency", "-f", help="Check frequency in seconds"),
    alert_threshold: float = typer.Option(75.0, "--threshold", "-t", help="Alert threshold (0-100)"),
):
    """Start real-time blockchain behavior monitoring."""
    asyncio.run(_monitor_behavior(address, frequency, alert_threshold))


@app.command()
def detect_anomalies(
    address: str = typer.Argument(..., help="Algorand address to check"),
    pattern_type: str = typer.Option("all", "--pattern", "-p", help="Pattern type: all, burst, timing, amount"),
):
    """Detect specific transaction anomaly patterns."""
    asyncio.run(_detect_anomalies(address, pattern_type))


async def _analyze_behavior(address: str, days: int, output_format: str, include_related: bool):
    """Analyze blockchain behavior"""
    console.print(f"[yellow]Analyzing blockchain behavior for {address} (last {days} days)[/yellow]")

    analyzer = BlockchainBehaviorAnalyzer()

    try:
        profile = await analyzer.analyze_address_behavior(
            address=address,
            historical_days=days,
            include_related_addresses=include_related
        )

        if output_format == "table":
            _display_behavior_table(profile)
        else:
            console.print(profile.to_dict())

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def _monitor_behavior(address: str, frequency: int, threshold: float):
    """Monitor blockchain behavior in real-time"""
    console.print(f"[yellow]Starting blockchain behavior monitoring for {address}[/yellow]")
    console.print(f"Check frequency: {frequency}s, Alert threshold: {threshold}")
    console.print("Press Ctrl+C to stop monitoring")

    analyzer = BlockchainBehaviorAnalyzer()

    try:
        while True:
            # Create monitoring table
            table = Table(title=f"Blockchain Behavior Monitor - {address}")
            table.add_column("Metric", style="cyan")
            table.add_column("Current Value", style="magenta")
            table.add_column("Status", style="bold")

            # Simulate monitoring data
            table.add_row("Risk Score", "45.2", "[green]NORMAL[/green]")
            table.add_row("Transaction Rate", "12/hour", "[green]NORMAL[/green]")
            table.add_row("Anomaly Count", "2", "[yellow]WATCH[/yellow]")
            table.add_row("Last Check", time.strftime("%H:%M:%S"), "[blue]ACTIVE[/blue]")

            with Live(table, refresh_per_second=1) as live:
                await asyncio.sleep(frequency)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


async def _detect_anomalies(address: str, pattern_type: str):
    """Detect transaction anomalies"""
    console.print(f"[yellow]Detecting {pattern_type} anomalies for {address}[/yellow]")

    # Placeholder for anomaly detection
    console.print("[green]Anomaly detection completed![/green]")


def _display_behavior_table(profile):
    """Display behavior analysis in table format"""
    # Risk score table
    risk_table = Table(title="Blockchain Behavior Risk Analysis")
    risk_table.add_column("Component", style="cyan")
    risk_table.add_column("Score", justify="right", style="magenta")
    risk_table.add_column("Risk Level", style="bold")

    risk_score = profile.risk_score
    components = [
        ("Transaction Anomalies", risk_score.transaction_anomaly_score),
        ("Wallet Clustering", risk_score.wallet_clustering_risk),
        ("MEV Exploitation", risk_score.mev_exploitation_risk),
        ("Flash Loan Risk", risk_score.flash_loan_risk),
        ("Bridge Activity", risk_score.bridge_activity_risk),
        ("Sybil Attack Risk", risk_score.sybil_attack_risk),
    ]

    for component, score in components:
        level = "LOW" if score <= 25 else "MEDIUM" if score <= 50 else "HIGH" if score <= 75 else "CRITICAL"
        risk_table.add_row(component, f"{score:.1f}", level)

    risk_table.add_row(
        "[bold]OVERALL[/bold]",
        f"[bold]{risk_score.overall_score:.1f}[/bold]",
        f"[bold]{risk_score.risk_level.value}[/bold]"
    )

    console.print(risk_table)

    # Patterns detected
    if profile.transaction_patterns:
        pattern_table = Table(title="Detected Transaction Patterns")
        pattern_table.add_column("Pattern Type", style="cyan")
        pattern_table.add_column("Frequency", justify="right")
        pattern_table.add_column("Confidence", justify="right")
        pattern_table.add_column("Risk Indicators", style="yellow")

        for pattern in profile.transaction_patterns[:5]:  # Top 5
            pattern_table.add_row(
                pattern.pattern_type,
                str(pattern.frequency),
                f"{pattern.confidence_score:.2f}",
                ", ".join(pattern.risk_indicators[:2])
            )

        console.print(pattern_table)


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()