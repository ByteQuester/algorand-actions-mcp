#!/usr/bin/env python3
"""
Ecosystem Analyzer CLI - Algorand Ecosystem Participation Analysis

Command-line tool for analyzing borrower participation in the Algorand ecosystem.
"""

import asyncio
import click
import json
from datetime import datetime, timedelta
from typing import Dict, Any


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Ecosystem Analyzer - Analyze Algorand ecosystem participation"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--address', '-a', required=True, help='Algorand address to analyze')
@click.option('--days', '-d', default=365, help='Number of days to analyze')
@click.option('--output', '-o', help='Output file for analysis', type=click.Path())
@click.pass_context
def analyze(ctx, address, days, output):
    """Analyze ecosystem participation for an address"""

    async def perform_analysis():
        click.echo(f"Analyzing ecosystem participation for {address}")
        click.echo(f"Analysis period: {days} days")

        # Mock ecosystem analysis
        analysis = await _analyze_ecosystem_participation(address, days)

        # Format output
        result = _format_analysis_result(analysis)

        if output:
            with open(output, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            click.echo(f"Analysis saved to {output}")
        else:
            click.echo(result)

    asyncio.run(perform_analysis())


@cli.command()
@click.option('--address', '-a', required=True, help='Algorand address to analyze')
@click.pass_context
def dapps(ctx, address):
    """Show dApp interaction history"""
    click.echo(f"DApp interactions for {address}:")
    click.echo("=" * 50)

    # Mock dApp data
    dapps = [
        {'name': 'Tinyman', 'interactions': 45, 'volume': 12500, 'last_used': '2024-01-15'},
        {'name': 'Pact', 'interactions': 23, 'volume': 8200, 'last_used': '2024-01-12'},
        {'name': 'AlgoFi', 'interactions': 12, 'volume': 15600, 'last_used': '2024-01-10'},
        {'name': 'Yieldly', 'interactions': 8, 'volume': 3400, 'last_used': '2024-01-08'}
    ]

    for dapp in dapps:
        click.echo(f"{dapp['name']:<12} {dapp['interactions']:>3} interactions  "
                  f"{dapp['volume']:>8,.0f} ALGO  Last: {dapp['last_used']}")


@cli.command()
@click.option('--address', '-a', required=True, help='Algorand address to analyze')
@click.pass_context
def assets(ctx, address):
    """Show asset diversity and holdings"""
    click.echo(f"Asset portfolio for {address}:")
    click.echo("=" * 60)

    # Mock asset data
    assets = [
        {'asset': 'ALGO', 'amount': 15750.50, 'value': 15750.50, 'percentage': 62.3},
        {'asset': 'USDC', 'amount': 5200.00, 'value': 5200.00, 'percentage': 20.6},
        {'asset': 'OPUL', 'amount': 12500.00, 'value': 2500.00, 'percentage': 9.9},
        {'asset': 'PLANETS', 'amount': 8000.00, 'value': 1200.00, 'percentage': 4.7},
        {'asset': 'SMILE', 'amount': 5000.00, 'value': 625.00, 'percentage': 2.5}
    ]

    total_value = sum(asset['value'] for asset in assets)

    click.echo(f"{'Asset':<12} {'Amount':<15} {'Value (ALGO)':<15} {'Percentage'}")
    click.echo("-" * 60)

    for asset in assets:
        click.echo(f"{asset['asset']:<12} {asset['amount']:>14,.2f} "
                  f"{asset['value']:>14,.2f} {asset['percentage']:>9.1f}%")

    click.echo("-" * 60)
    click.echo(f"{'Total':<12} {'':<15} {total_value:>14,.2f} {'100.0%':>9}")

    # Diversity metrics
    click.echo(f"\nDiversity Metrics:")
    click.echo(f"  Asset Count: {len(assets)}")
    click.echo(f"  Concentration (top asset): {max(asset['percentage'] for asset in assets):.1f}%")
    click.echo(f"  Diversity Score: {min(1.0, len(assets) / 10.0):.2f}")


@cli.command()
@click.option('--address', '-a', required=True, help='Algorand address to analyze')
@click.option('--days', '-d', default=90, help='Number of days to analyze')
@click.pass_context
def activity(ctx, address, days):
    """Show transaction activity patterns"""
    click.echo(f"Activity pattern for {address} (last {days} days):")
    click.echo("=" * 50)

    # Mock activity data
    activity_data = {
        'total_transactions': 247,
        'daily_average': 2.7,
        'peak_day': '2024-01-12',
        'peak_transactions': 15,
        'asset_transfers': 89,
        'app_calls': 158,
        'payment_transactions': 67
    }

    click.echo(f"Total Transactions:    {activity_data['total_transactions']}")
    click.echo(f"Daily Average:         {activity_data['daily_average']:.1f}")
    click.echo(f"Peak Day:              {activity_data['peak_day']} ({activity_data['peak_transactions']} txns)")
    click.echo(f"Asset Transfers:       {activity_data['asset_transfers']}")
    click.echo(f"App Calls:             {activity_data['app_calls']}")
    click.echo(f"Payment Transactions:  {activity_data['payment_transactions']}")

    # Activity score
    score = min(1.0, activity_data['daily_average'] / 5.0)
    click.echo(f"\nActivity Score: {score:.3f}")


@cli.command()
@click.option('--address', '-a', required=True, help='Algorand address to analyze')
@click.pass_context
def score(ctx, address):
    """Calculate ecosystem participation score"""

    async def calculate_score():
        click.echo(f"Calculating ecosystem score for {address}")

        # Mock scoring
        score_data = await _calculate_ecosystem_score(address)

        click.echo("\nEcosystem Participation Score")
        click.echo("=" * 40)
        click.echo(f"Overall Score: {score_data['overall_score']:.3f}")
        click.echo(f"Confidence:    {score_data['confidence']:.3f}")
        click.echo("")

        click.echo("Component Scores:")
        for component, score in score_data['components'].items():
            click.echo(f"  {component:<20} {score:.3f}")

        click.echo("")
        click.echo("Interpretation:")
        if score_data['overall_score'] >= 0.8:
            click.echo("  Excellent ecosystem participation")
        elif score_data['overall_score'] >= 0.6:
            click.echo("  Good ecosystem engagement")
        elif score_data['overall_score'] >= 0.4:
            click.echo("  Moderate ecosystem activity")
        else:
            click.echo("  Limited ecosystem participation")

    asyncio.run(calculate_score())


async def _analyze_ecosystem_participation(address: str, days: int) -> Dict[str, Any]:
    """Perform comprehensive ecosystem analysis"""

    # Simulate API call delay
    await asyncio.sleep(0.5)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    return {
        'address': address,
        'analysis_period': {
            'start_date': start_date,
            'end_date': end_date,
            'days': days
        },
        'wallet_metrics': {
            'age_days': 456,
            'total_transactions': 1247,
            'asset_diversity': 12,
            'dapp_interactions': 8,
            'avg_balance_algo': 15750.50
        },
        'participation_metrics': {
            'smart_contract_usage': True,
            'defi_protocols_used': ['Tinyman', 'Pact', 'AlgoFi'],
            'nft_holdings': 23,
            'participation_consistency': 0.85
        },
        'activity_patterns': {
            'daily_avg_transactions': 2.7,
            'peak_activity_day': '2024-01-12',
            'transaction_types': {
                'payment': 67,
                'asset_transfer': 89,
                'app_call': 158
            }
        },
        'ecosystem_score': 0.75,
        'confidence': 0.90,
        'generated_at': datetime.now()
    }


async def _calculate_ecosystem_score(address: str) -> Dict[str, Any]:
    """Calculate detailed ecosystem participation score"""

    await asyncio.sleep(0.3)

    components = {
        'Wallet Age': 0.82,
        'Transaction Volume': 0.74,
        'Asset Diversity': 0.68,
        'DApp Usage': 0.71,
        'Smart Contract Interaction': 0.85,
        'Balance Stability': 0.79,
        'Activity Consistency': 0.77
    }

    overall_score = sum(components.values()) / len(components)

    return {
        'address': address,
        'overall_score': overall_score,
        'confidence': 0.90,
        'components': components,
        'calculated_at': datetime.now()
    }


def _format_analysis_result(analysis: Dict[str, Any]) -> str:
    """Format analysis result as human-readable text"""
    lines = []
    lines.append("=" * 60)
    lines.append("ALGORAND ECOSYSTEM ANALYSIS")
    lines.append("=" * 60)
    lines.append(f"Address: {analysis['address']}")
    lines.append(f"Analysis Period: {analysis['analysis_period']['days']} days")
    lines.append(f"Generated: {analysis['generated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("Wallet Metrics:")
    wallet = analysis['wallet_metrics']
    lines.append(f"  Age: {wallet['age_days']} days")
    lines.append(f"  Total Transactions: {wallet['total_transactions']:,}")
    lines.append(f"  Asset Diversity: {wallet['asset_diversity']}")
    lines.append(f"  DApp Interactions: {wallet['dapp_interactions']}")
    lines.append(f"  Average Balance: {wallet['avg_balance_algo']:,.2f} ALGO")
    lines.append("")

    lines.append("Participation Metrics:")
    participation = analysis['participation_metrics']
    lines.append(f"  Smart Contract Usage: {participation['smart_contract_usage']}")
    lines.append(f"  DeFi Protocols Used: {', '.join(participation['defi_protocols_used'])}")
    lines.append(f"  NFT Holdings: {participation['nft_holdings']}")
    lines.append(f"  Consistency Score: {participation['participation_consistency']:.2f}")
    lines.append("")

    lines.append("Overall Assessment:")
    lines.append(f"  Ecosystem Score: {analysis['ecosystem_score']:.3f}")
    lines.append(f"  Confidence: {analysis['confidence']:.3f}")

    return "\n".join(lines)


if __name__ == '__main__':
    cli()