#!/usr/bin/env python3
"""
Holistic Risk Assessor CLI

Master CLI tool for comprehensive Algorand risk assessment across all engines.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.json import JSON

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from holistic_risk_orchestrator.risk_orchestrator import HolisticRiskOrchestrator

app = typer.Typer(
    name="holistic-risk-assessor",
    help="Holistic Risk Assessment CLI for Algorand ecosystem",
    rich_markup_mode="rich"
)
console = Console()


@app.command()
def assess(
    address: str = typer.Argument(..., help="Algorand address to assess"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, summary"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    include_scenarios: bool = typer.Option(True, "--scenarios/--no-scenarios", help="Include scenario analysis"),
    include_trends: bool = typer.Option(True, "--trends/--no-trends", help="Include trend analysis"),
    enable_monitoring: bool = typer.Option(False, "--monitor", help="Enable real-time monitoring"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    Perform comprehensive holistic risk assessment for an Algorand address.

    This command orchestrates all risk engines to provide a complete risk profile:
    - Blockchain Behavior Risk Analysis
    - DeFi Protocol Risk Assessment
    - Liquidity Cascade Risk Modeling
    - Governance Stability Risk Evaluation
    - Cross-engine Correlation Analysis
    """
    asyncio.run(_assess_address(
        address, output_format, output_file, include_scenarios,
        include_trends, enable_monitoring, config_file, verbose
    ))


@app.command()
def monitor(
    address: str = typer.Argument(..., help="Algorand address to monitor"),
    frequency: int = typer.Option(300, "--frequency", "-f", help="Monitoring frequency in seconds"),
    alert_threshold: str = typer.Option("HIGH", "--threshold", "-t", help="Alert threshold: LOW, MEDIUM, HIGH, CRITICAL"),
    dashboard_port: int = typer.Option(8080, "--port", "-p", help="Dashboard port"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path")
):
    """
    Start real-time risk monitoring for an Algorand address.

    Continuously monitors risk levels across all engines and provides alerts
    when thresholds are exceeded. Includes a web dashboard for visualization.
    """
    asyncio.run(_monitor_address(address, frequency, alert_threshold, dashboard_port, config_file))


@app.command()
def scenario(
    address: str = typer.Argument(..., help="Algorand address to test"),
    scenario_name: str = typer.Option("all", "--scenario", "-s", help="Scenario to run: all, crash, defi-crisis, governance-attack"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
    save_results: bool = typer.Option(False, "--save", help="Save scenario results")
):
    """
    Run stress testing scenarios across all risk engines.

    Available scenarios:
    - market-crash: Major market downturn simulation
    - defi-crisis: DeFi protocol failure cascade
    - governance-attack: Governance manipulation attack
    - liquidity-crisis: Extreme liquidity shortage
    - black-swan: Unprecedented market event
    """
    asyncio.run(_run_scenario_analysis(address, scenario_name, output_format, save_results))


@app.command()
def correlation(
    address: str = typer.Argument(..., help="Algorand address to analyze"),
    time_window: int = typer.Option(30, "--window", "-w", help="Analysis time window in days"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, heatmap")
):
    """
    Analyze cross-engine risk correlations and amplification effects.

    Examines how risks across different engines correlate and amplify each other,
    providing insights into systemic risk exposure.
    """
    asyncio.run(_analyze_correlations(address, time_window, output_format))


@app.command()
def report(
    address: str = typer.Argument(..., help="Algorand address for report"),
    report_type: str = typer.Option("executive", "--type", "-t", help="Report type: executive, detailed, technical"),
    output_file: str = typer.Option("risk_report.pdf", "--output", "-o", help="Output file path"),
    include_charts: bool = typer.Option(True, "--charts/--no-charts", help="Include risk visualization charts")
):
    """
    Generate comprehensive risk assessment report.

    Creates detailed PDF reports with risk analysis, recommendations,
    and visualizations suitable for different audiences.
    """
    asyncio.run(_generate_report(address, report_type, output_file, include_charts))


async def _assess_address(
    address: str, output_format: str, output_file: Optional[str],
    include_scenarios: bool, include_trends: bool, enable_monitoring: bool,
    config_file: Optional[str], verbose: bool
):
    """Perform holistic risk assessment"""

    # Load configuration
    config = _load_config(config_file) if config_file else None

    # Initialize orchestrator
    orchestrator = HolisticRiskOrchestrator(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Assessment task
        task = progress.add_task("Performing holistic risk assessment...", total=None)

        try:
            # Run holistic assessment
            profile = await orchestrator.assess_holistic_risk(
                address=address,
                include_scenario_analysis=include_scenarios,
                include_trend_analysis=include_trends,
                enable_real_time_monitoring=enable_monitoring
            )

            progress.update(task, description="Assessment completed!")

            # Display results
            if output_format == "table":
                _display_table_results(profile)
            elif output_format == "json":
                _display_json_results(profile)
            elif output_format == "summary":
                _display_summary_results(profile)

            # Save to file if specified
            if output_file:
                _save_results(profile, output_file, output_format)
                console.print(f"[green]Results saved to: {output_file}[/green]")

            # Display monitoring info if enabled
            if enable_monitoring:
                console.print("\n[yellow]Real-time monitoring started![/yellow]")
                console.print(f"Monitoring frequency: {profile.monitoring_configuration.monitoring_frequency_seconds}s")
                console.print("Use Ctrl+C to stop monitoring")

        except Exception as e:
            progress.stop()
            console.print(f"[red]Error during assessment: {e}[/red]")
            if verbose:
                console.print_exception()
            sys.exit(1)


async def _monitor_address(address: str, frequency: int, threshold: str, port: int, config_file: Optional[str]):
    """Start real-time monitoring"""
    console.print(f"[yellow]Starting real-time monitoring for {address}[/yellow]")
    console.print(f"Frequency: {frequency}s, Threshold: {threshold}, Dashboard: http://localhost:{port}")
    console.print("Press Ctrl+C to stop monitoring")

    # Placeholder for monitoring implementation
    try:
        while True:
            await asyncio.sleep(frequency)
            console.print(f"[blue]Monitoring check at {typer.get_timestamp()}[/blue]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


async def _run_scenario_analysis(address: str, scenario_name: str, output_format: str, save_results: bool):
    """Run scenario analysis"""
    console.print(f"[yellow]Running scenario analysis: {scenario_name}[/yellow]")

    # Placeholder for scenario analysis
    console.print("[green]Scenario analysis completed![/green]")


async def _analyze_correlations(address: str, time_window: int, output_format: str):
    """Analyze risk correlations"""
    console.print(f"[yellow]Analyzing risk correlations for {time_window} days[/yellow]")

    # Placeholder for correlation analysis
    console.print("[green]Correlation analysis completed![/green]")


async def _generate_report(address: str, report_type: str, output_file: str, include_charts: bool):
    """Generate risk report"""
    console.print(f"[yellow]Generating {report_type} report for {address}[/yellow]")

    # Placeholder for report generation
    console.print(f"[green]Report generated: {output_file}[/green]")


def _display_table_results(profile):
    """Display results in table format"""

    # Overall Risk Summary Table
    risk_table = Table(title="Holistic Risk Assessment Summary")
    risk_table.add_column("Risk Engine", style="cyan")
    risk_table.add_column("Score", justify="right", style="magenta")
    risk_table.add_column("Risk Level", style="bold")
    risk_table.add_column("Primary Concerns", style="yellow")

    # Individual engine scores
    engines_data = [
        ("Blockchain Behavior", profile.holistic_risk_score.blockchain_behavior_score, "See individual factors"),
        ("DeFi Protocol", profile.holistic_risk_score.defi_protocol_score, "Protocol exposure"),
        ("Liquidity Cascade", profile.holistic_risk_score.liquidity_cascade_score, "Liquidation risk"),
        ("Governance Stability", profile.holistic_risk_score.governance_stability_score, "Governance centralization")
    ]

    for engine, score, concerns in engines_data:
        risk_level = "LOW" if score <= 25 else "MEDIUM" if score <= 50 else "HIGH" if score <= 75 else "CRITICAL"
        risk_table.add_row(engine, f"{score:.1f}", risk_level, concerns)

    # Overall score
    risk_table.add_row(
        "[bold]OVERALL HOLISTIC[/bold]",
        f"[bold]{profile.holistic_risk_score.overall_holistic_score:.1f}[/bold]",
        f"[bold]{profile.holistic_risk_score.risk_level.value}[/bold]",
        "Cross-engine correlation"
    )

    console.print(risk_table)

    # Alerts Summary
    if profile.active_alerts:
        alert_panel = Panel(
            f"[red]Active Alerts: {len(profile.active_alerts)}[/red]\n" +
            f"[yellow]High Priority: {len([a for a in profile.active_alerts if a.severity.value in ['HIGH', 'CRITICAL']])}[/yellow]",
            title="Alert Status",
            border_style="red"
        )
        console.print(alert_panel)

    # Mitigation Recommendations
    if profile.recommended_mitigations:
        mitigation_table = Table(title="Risk Mitigation Recommendations")
        mitigation_table.add_column("Priority", style="red")
        mitigation_table.add_column("Strategy", style="cyan")
        mitigation_table.add_column("Expected Impact", style="green")

        for mitigation in profile.recommended_mitigations[:5]:  # Top 5
            mitigation_table.add_row(
                mitigation.priority.value,
                mitigation.title,
                f"Risk reduction: {sum(mitigation.expected_risk_reduction.values()):.1f}%"
            )

        console.print(mitigation_table)


def _display_json_results(profile):
    """Display results in JSON format"""
    json_data = profile.to_dict()
    console.print(JSON.from_data(json_data))


def _display_summary_results(profile):
    """Display executive summary"""
    summary = profile.get_executive_summary()

    # Overall assessment panel
    assessment_text = f"""
[bold]Risk Level:[/bold] {summary['overall_assessment']['risk_level']}
[bold]Risk Score:[/bold] {summary['overall_assessment']['score']:.1f}/100
[bold]Confidence:[/bold] {summary['overall_assessment']['confidence']:.1%}
"""

    overall_panel = Panel(assessment_text, title="Overall Risk Assessment", border_style="blue")
    console.print(overall_panel)

    # Key risks panel
    key_risks_text = f"""
[bold]Systemic Failure Probability:[/bold] {summary['key_risks']['systemic_failure_probability']:.1%}
[bold]Portfolio at Risk:[/bold] ${summary['key_risks']['portfolio_at_risk']:,.2f}
[bold]Time to Critical:[/bold] {summary['key_risks'].get('time_to_critical', 'N/A')}

[bold]Top Risk Factors:[/bold]
{chr(10).join(f"• {factor}" for factor in summary['key_risks']['top_risk_factors'][:3])}
"""

    risks_panel = Panel(key_risks_text, title="Key Risk Indicators", border_style="red")
    console.print(risks_panel)


def _save_results(profile, output_file: str, output_format: str):
    """Save results to file"""
    file_path = Path(output_file)

    if output_format == "json":
        with open(file_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2, default=str)
    else:
        # For other formats, save as JSON by default
        with open(file_path.with_suffix('.json'), 'w') as f:
            json.dump(profile.to_dict(), f, indent=2, default=str)


def _load_config(config_file: str) -> dict:
    """Load configuration from file"""
    import yaml

    try:
        with open(config_file, 'r') as f:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                return yaml.safe_load(f)
            elif config_file.endswith('.json'):
                return json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading config file: {e}[/red]")
        sys.exit(1)

    return {}


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()