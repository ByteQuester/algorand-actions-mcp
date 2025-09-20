#!/usr/bin/env python3
"""
CLI Tool Integration Example

This demonstrates how to integrate the algorand-lending-business-logic package
into a command-line tool using Click framework.

Features:
- Multiple subcommands for different operations
- JSON input/output support
- Batch processing capabilities
- Configuration management
- Detailed output formatting

Usage:
    pip install click
    python cli_tool_example.py --help

Commands:
    analyze-loan - Complete loan analysis
    check-collateral - Analyze collateral only
    calculate-rate - Calculate interest rate
    evaluate-loan - Loan approval evaluation
    assess-risk - Risk assessment
    batch-process - Process multiple loan requests
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add the vendor package to Python path (if not installed)
vendor_path = Path(__file__).parent / "algorand_lending_bl"
if vendor_path.exists():
    sys.path.insert(0, str(vendor_path.parent))

try:
    import click
except ImportError:
    print("❌ Click not installed. Please run: pip install click")
    sys.exit(1)

# Import lending business logic
from algorand_lending_bl import (
    create_lending_service,
    LoanRequest,
    AlgorandAddress,
    ASAToken,
    VENDOR_INFO,
    create_testnet_config,
    create_mainnet_config,
    DEFAULT_CONFIG
)

# ============================================================================
# GLOBAL CLI STATE
# ============================================================================

class CLIState:
    """Shared state for CLI commands."""
    def __init__(self):
        self.lending_service = None
        self.config = None
        self.verbose = False

# Global state object
cli_state = CLIState()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def init_lending_service(network: str = "default", verbose: bool = False):
    """Initialize the lending service with specified network."""
    if verbose:
        click.echo(f"🔧 Initializing lending service for {network}...")

    if network == "testnet":
        config = create_testnet_config()
    elif network == "mainnet":
        config = create_mainnet_config()
    else:
        config = DEFAULT_CONFIG

    cli_state.config = config
    cli_state.lending_service = create_lending_service(config)
    cli_state.verbose = verbose

    if verbose:
        click.echo(f"✓ Service ready with {len(cli_state.lending_service)} engines")

def parse_collateral_json(collateral_str: str) -> List[ASAToken]:
    """Parse collateral JSON string into ASAToken objects."""
    try:
        collateral_data = json.loads(collateral_str)
        assets = []

        for asset_data in collateral_data:
            asset = ASAToken(
                asset_id=asset_data['asset_id'],
                amount=asset_data['amount']
            )
            assets.append(asset)

        return assets
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON in collateral: {e}")
    except KeyError as e:
        raise click.BadParameter(f"Missing required field in collateral: {e}")

def format_currency(amount: int, decimals: int = 6) -> str:
    """Format microALGO amount to ALGO."""
    return f"{amount / (10 ** decimals):.{decimals}f}"

def format_percentage(rate: float) -> str:
    """Format rate as percentage."""
    return f"{rate * 100:.2f}%"

def output_json(data: Dict[str, Any], pretty: bool = True):
    """Output data as JSON."""
    if pretty:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        click.echo(json.dumps(data, default=str))

def output_table(title: str, data: Dict[str, Any]):
    """Output data as formatted table."""
    click.echo(f"\n{title}")
    click.echo("=" * len(title))

    for key, value in data.items():
        if isinstance(value, dict):
            click.echo(f"{key}:")
            for sub_key, sub_value in value.items():
                click.echo(f"  {sub_key}: {sub_value}")
        else:
            click.echo(f"{key}: {value}")

# ============================================================================
# CLI COMMANDS
# ============================================================================

@click.group()
@click.option('--network', type=click.Choice(['default', 'testnet', 'mainnet']),
              default='default', help='Algorand network to use')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, network, verbose):
    """Algorand Lending Business Logic CLI Tool."""
    ctx.ensure_object(dict)

    # Initialize the lending service
    init_lending_service(network, verbose)

    if verbose:
        click.echo(f"🏦 Algorand Lending CLI v{VENDOR_INFO['version']}")
        click.echo(f"📡 Network: {network}")

@cli.command()
@click.option('--borrower', '-b', required=True, help='Borrower Algorand address')
@click.option('--amount', '-a', required=True, type=int, help='Loan amount in microALGOs')
@click.option('--collateral', '-c', required=True, help='Collateral assets (JSON array)')
@click.option('--duration', '-d', default=30, type=int, help='Loan duration in days')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.option('--json-file', help='Save results to JSON file')
def analyze_loan(borrower, amount, collateral, duration, output, json_file):
    """Perform complete loan analysis."""

    try:
        # Parse inputs
        borrower_addr = AlgorandAddress(borrower)
        collateral_assets = parse_collateral_json(collateral)

        loan_request = LoanRequest(
            borrower=borrower_addr,
            requested_amount=amount,
            collateral_assets=collateral_assets,
            loan_duration_days=duration
        )

        if cli_state.verbose:
            click.echo(f"🔍 Analyzing loan request...")
            click.echo(f"   Borrower: {borrower}")
            click.echo(f"   Amount: {format_currency(amount)} ALGO")
            click.echo(f"   Collateral: {len(collateral_assets)} assets")
            click.echo(f"   Duration: {duration} days")

        # Run all analyses
        collateral_analysis = cli_state.lending_service["collateral"].analyze_collateral(
            collateral_assets, borrower_addr
        )
        rate_calculation = cli_state.lending_service["interest_rates"].calculate_interest_rate(loan_request)
        loan_decision = cli_state.lending_service["loan_approval"].evaluate_loan(loan_request)
        risk_assessment = cli_state.lending_service["risk_assessment"].assess_risk(loan_request)

        # Prepare results
        results = {
            "loan_request": {
                "borrower": str(borrower_addr),
                "requested_amount_algo": format_currency(amount),
                "requested_amount_microalgos": amount,
                "collateral_count": len(collateral_assets),
                "duration_days": duration
            },
            "collateral_analysis": {
                "total_value_usd": f"${collateral_analysis.total_value:.2f}",
                "liquidity_tier": collateral_analysis.liquidity_tier.value,
                "portfolio_risk": collateral_analysis.portfolio_risk.value
            },
            "interest_rate": {
                "base_rate": format_percentage(rate_calculation.base_rate),
                "final_rate": format_percentage(rate_calculation.final_rate),
                "risk_premium": format_percentage(rate_calculation.risk_premium)
            },
            "loan_decision": {
                "decision": loan_decision.decision.value,
                "confidence": loan_decision.confidence.value,
                "approved_amount_algo": format_currency(loan_decision.approved_amount),
                "approved_amount_microalgos": loan_decision.approved_amount
            },
            "risk_assessment": {
                "overall_score": f"{risk_assessment.overall_score:.2f}",
                "risk_level": risk_assessment.risk_level.value,
                "borrower_risk": f"{risk_assessment.borrower_risk:.2f}",
                "collateral_risk": f"{risk_assessment.collateral_risk:.2f}"
            }
        }

        # Output results
        if output == 'json':
            output_json(results)
        else:
            output_table("Loan Analysis Results", results)

        # Save to file if requested
        if json_file:
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            click.echo(f"\n✓ Results saved to {json_file}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--borrower', '-b', required=True, help='Borrower Algorand address')
@click.option('--collateral', '-c', required=True, help='Collateral assets (JSON array)')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table')
def check_collateral(borrower, collateral, output):
    """Analyze collateral assets only."""

    try:
        borrower_addr = AlgorandAddress(borrower)
        collateral_assets = parse_collateral_json(collateral)

        if cli_state.verbose:
            click.echo(f"🔍 Analyzing collateral for {borrower}...")

        analysis = cli_state.lending_service["collateral"].analyze_collateral(
            collateral_assets, borrower_addr
        )

        results = {
            "borrower": str(borrower_addr),
            "total_value_usd": f"${analysis.total_value:.2f}",
            "liquidity_tier": analysis.liquidity_tier.value,
            "portfolio_risk": analysis.portfolio_risk.value,
            "asset_count": len(analysis.asset_valuations),
            "liquidation_scenarios": len(analysis.liquidation_scenarios)
        }

        if output == 'json':
            output_json(results)
        else:
            output_table("Collateral Analysis", results)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--borrower', '-b', required=True, help='Borrower Algorand address')
@click.option('--amount', '-a', required=True, type=int, help='Loan amount in microALGOs')
@click.option('--collateral', '-c', required=True, help='Collateral assets (JSON array)')
@click.option('--duration', '-d', default=30, type=int, help='Loan duration in days')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table')
def calculate_rate(borrower, amount, collateral, duration, output):
    """Calculate interest rate for a loan."""

    try:
        borrower_addr = AlgorandAddress(borrower)
        collateral_assets = parse_collateral_json(collateral)

        loan_request = LoanRequest(
            borrower=borrower_addr,
            requested_amount=amount,
            collateral_assets=collateral_assets,
            loan_duration_days=duration
        )

        if cli_state.verbose:
            click.echo(f"📊 Calculating interest rate...")

        rate_calculation = cli_state.lending_service["interest_rates"].calculate_interest_rate(loan_request)

        results = {
            "loan_amount_algo": format_currency(amount),
            "base_rate": format_percentage(rate_calculation.base_rate),
            "risk_premium": format_percentage(rate_calculation.risk_premium),
            "final_rate": format_percentage(rate_calculation.final_rate),
            "rate_factors": {
                "borrower_reputation": f"{rate_calculation.rate_factors.borrower_reputation:.2f}",
                "collateral_quality": f"{rate_calculation.rate_factors.collateral_quality:.2f}",
                "market_conditions": f"{rate_calculation.rate_factors.market_conditions:.2f}"
            }
        }

        if output == 'json':
            output_json(results)
        else:
            output_table("Interest Rate Calculation", results)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('requests_file', type=click.Path(exists=True))
@click.option('--output-file', '-o', help='Output file for results')
@click.option('--format', 'output_format', type=click.Choice(['json', 'csv']),
              default='json', help='Output format')
def batch_process(requests_file, output_file, output_format):
    """Process multiple loan requests from a JSON file."""

    try:
        # Load requests
        with open(requests_file, 'r') as f:
            requests_data = json.load(f)

        if not isinstance(requests_data, list):
            raise click.BadParameter("Requests file must contain a JSON array")

        results = []
        total_requests = len(requests_data)

        click.echo(f"🔄 Processing {total_requests} loan requests...")

        with click.progressbar(requests_data, label='Processing loans') as requests:
            for i, request_data in enumerate(requests):
                try:
                    # Parse request
                    borrower = AlgorandAddress(request_data['borrower'])
                    collateral_assets = []

                    for asset_data in request_data['collateral_assets']:
                        asset = ASAToken(
                            asset_id=asset_data['asset_id'],
                            amount=asset_data['amount']
                        )
                        collateral_assets.append(asset)

                    loan_request = LoanRequest(
                        borrower=borrower,
                        requested_amount=request_data['requested_amount'],
                        collateral_assets=collateral_assets,
                        loan_duration_days=request_data.get('loan_duration_days', 30)
                    )

                    # Analyze loan
                    decision = cli_state.lending_service["loan_approval"].evaluate_loan(loan_request)

                    result = {
                        "request_id": i + 1,
                        "borrower": str(borrower),
                        "requested_amount": request_data['requested_amount'],
                        "decision": decision.decision.value,
                        "confidence": decision.confidence.value,
                        "approved_amount": decision.approved_amount,
                        "processing_status": "success"
                    }

                except Exception as e:
                    result = {
                        "request_id": i + 1,
                        "borrower": request_data.get('borrower', 'unknown'),
                        "requested_amount": request_data.get('requested_amount', 0),
                        "decision": "error",
                        "error_message": str(e),
                        "processing_status": "failed"
                    }

                results.append(result)

        # Output results
        if output_file:
            if output_format == 'json':
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
            elif output_format == 'csv':
                import csv
                with open(output_file, 'w', newline='') as f:
                    if results:
                        writer = csv.DictWriter(f, fieldnames=results[0].keys())
                        writer.writeheader()
                        writer.writerows(results)

            click.echo(f"✓ Results saved to {output_file}")
        else:
            output_json(results)

        # Summary
        successful = sum(1 for r in results if r['processing_status'] == 'success')
        failed = total_requests - successful

        click.echo(f"\n📊 Batch Processing Summary:")
        click.echo(f"   Total requests: {total_requests}")
        click.echo(f"   Successful: {successful}")
        click.echo(f"   Failed: {failed}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
def info():
    """Display service information."""

    info_data = {
        "service": "Algorand Lending Business Logic CLI",
        "package_info": VENDOR_INFO,
        "available_engines": list(cli_state.lending_service.keys()),
        "network": cli_state.config.network.network_name if cli_state.config else "default",
        "commands": [
            "analyze-loan - Complete loan analysis",
            "check-collateral - Analyze collateral only",
            "calculate-rate - Calculate interest rate",
            "batch-process - Process multiple requests"
        ]
    }

    output_table("Service Information", info_data)

# ============================================================================
# SAMPLE DATA GENERATORS
# ============================================================================

@cli.command()
@click.option('--count', '-n', default=5, type=int, help='Number of sample requests')
@click.option('--output-file', '-o', required=True, help='Output file')
def generate_samples(count, output_file):
    """Generate sample loan requests for testing."""

    import random

    sample_addresses = [
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"
    ]

    samples = []
    for i in range(count):
        sample = {
            "borrower": random.choice(sample_addresses),
            "requested_amount": random.randint(100000, 10000000),  # 0.1 to 10 ALGO
            "collateral_assets": [
                {
                    "asset_id": 0,  # ALGO
                    "amount": random.randint(1000000, 20000000)  # 1 to 20 ALGO
                }
            ],
            "loan_duration_days": random.choice([7, 14, 30, 60, 90])
        }
        samples.append(sample)

    with open(output_file, 'w') as f:
        json.dump(samples, f, indent=2)

    click.echo(f"✓ Generated {count} sample requests in {output_file}")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    cli()