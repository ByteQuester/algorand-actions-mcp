#!/usr/bin/env python3
"""
Collateral Requirements CLI

Simple command-line interface for analyzing digital asset collateral requirements.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add core module to path
sys.path.append(str(Path(__file__).parent))
from core import CollateralRequirementsEngine


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Analyze digital asset collateral requirements for DeFi lending",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze ALGO collateral for $50k loan
  python3 analyze_collateral.py --loan-amount 50000 --collateral "0:ALGO:300000"

  # Mixed collateral analysis
  python3 analyze_collateral.py --loan-amount 100000 \\
    --collateral "0:ALGO:200000" "31566704:USDC:50000" \\
    --market-conditions volatile

  # Quick ALGO analysis
  python3 analyze_collateral.py --quick-algo --amount 300000 --loan 25000

  # View recent analyses
  python3 analyze_collateral.py --history --limit 10
        """
    )

    # Main analysis options
    parser.add_argument(
        '--loan-amount',
        type=float,
        help='Loan amount in USD'
    )

    parser.add_argument(
        '--collateral',
        nargs='+',
        help='Collateral positions in format "asset_id:symbol:amount"'
    )

    parser.add_argument(
        '--market-conditions',
        choices=['bull', 'normal', 'bear', 'volatile'],
        default='normal',
        help='Current market conditions (default: normal)'
    )

    parser.add_argument(
        '--loan-id',
        help='Optional loan identifier'
    )

    parser.add_argument(
        '--borrower',
        help='Optional borrower address'
    )

    # Quick ALGO analysis
    parser.add_argument(
        '--quick-algo',
        action='store_true',
        help='Quick ALGO collateral analysis'
    )

    parser.add_argument(
        '--amount',
        type=float,
        help='Amount of ALGO tokens (for quick analysis)'
    )

    parser.add_argument(
        '--loan',
        type=float,
        help='Loan amount in USD (for quick analysis)'
    )

    # History and stats
    parser.add_argument(
        '--history',
        action='store_true',
        help='Show recent analysis history'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Limit for history results (default: 10)'
    )

    # Output options
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output with detailed metrics'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (defaults to config.yaml)'
    )

    return parser


def parse_collateral_positions(collateral_strings):
    """Parse collateral position strings"""
    positions = []

    for pos_str in collateral_strings:
        try:
            parts = pos_str.split(':')
            if len(parts) != 3:
                raise ValueError(f"Invalid format: {pos_str}")

            asset_id, symbol, amount = parts
            positions.append({
                'asset_id': asset_id,
                'asset_symbol': symbol,
                'amount': float(amount)
            })
        except Exception as e:
            print(f"❌ Error parsing collateral position '{pos_str}': {e}")
            sys.exit(1)

    return positions


async def run_analysis(engine, loan_amount, positions, market_conditions, loan_id, borrower, verbose=False):
    """Run collateral analysis"""
    print(f"🔍 Analyzing collateral requirements...")
    print(f"💰 Loan Amount: ${loan_amount:,}")
    print(f"📊 Market Conditions: {market_conditions}")
    print(f"🏦 Collateral Positions: {len(positions)} assets")
    print()

    try:
        result = await engine.analyze_collateral_requirement(
            loan_amount_usd=loan_amount,
            collateral_positions=positions,
            loan_id=loan_id,
            borrower_address=borrower,
            market_conditions=market_conditions
        )

        return result

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None


def format_result_json(result):
    """Format result as JSON"""
    if not result:
        return "{}"

    output = {
        'loan_id': result.loan_id,
        'loan_amount_usd': result.loan_amount_usd,
        'required_collateral_ratio': result.required_collateral_ratio,
        'total_collateral_value_usd': result.total_collateral_value_usd,
        'risk_level': result.risk_level,
        'confidence_score': result.confidence_score,
        'market_conditions': result.market_conditions,
        'analysis_timestamp': result.analysis_timestamp.isoformat(),
        'collateral_positions': [
            {
                'asset_id': pos.asset_id,
                'asset_symbol': pos.asset_symbol,
                'asset_type': pos.asset_type.value,
                'position_size': pos.position_size,
                'current_price_usd': pos.current_price_usd,
                'position_value_usd': pos.position_value_usd
            }
            for pos in result.collateral_positions
        ],
        'liquidation_scenarios': result.liquidation_scenarios,
        'recommendations': result.recommendations
    }

    return json.dumps(output, indent=2)


def format_result_text(result, verbose=False):
    """Format result as human-readable text"""
    if not result:
        return "No results to display"

    output = []
    output.append("🎯 Analysis Results")
    output.append("=" * 50)

    # Key metrics
    required_value = result.loan_amount_usd * result.required_collateral_ratio
    shortage = required_value - result.total_collateral_value_usd

    output.append(f"Required Collateral Ratio: {result.required_collateral_ratio:.2f}x")
    output.append(f"Current Collateral Value: ${result.total_collateral_value_usd:,.2f}")
    output.append(f"Required Collateral Value: ${required_value:,.2f}")
    output.append(f"Risk Level: {result.risk_level.upper()}")
    output.append(f"Confidence Score: {result.confidence_score:.1%}")

    if shortage > 0:
        output.append(f"⚠️  Collateral Shortage: ${shortage:,.2f}")
    else:
        output.append(f"✅ Collateral Sufficient (${-shortage:,.2f} excess)")

    output.append("")

    # Collateral breakdown
    output.append("📋 Collateral Breakdown:")
    for pos in result.collateral_positions:
        output.append(f"   {pos.asset_symbol}: {pos.position_size:,.0f} @ ${pos.current_price_usd:.4f} = ${pos.position_value_usd:,.2f}")
        if verbose and pos.volatility_metrics:
            output.append(f"     • Volatility (30d): {pos.volatility_metrics.volatility_30d:.1%}")
            output.append(f"     • VaR (95%): {pos.volatility_metrics.value_at_risk_95:.1%}")
        if verbose and pos.liquidity_metrics:
            output.append(f"     • Liquidity Tier: {pos.liquidity_metrics.liquidity_tier}")
            output.append(f"     • Daily Volume: ${pos.liquidity_metrics.daily_volume_usd:,.0f}")

    output.append("")

    # Liquidation scenarios
    output.append("⚠️  Liquidation Scenarios:")
    for scenario in result.liquidation_scenarios:
        output.append(f"   {scenario['scenario_name']}: {scenario['price_drop_percentage']:.1%} drop → "
                     f"${scenario['estimated_liquidation_value']:,.0f} recovery "
                     f"({scenario['scenario_probability']:.1%} probability)")

    output.append("")

    # Recommendations
    output.append("💡 Recommendations:")
    for rec in result.recommendations:
        output.append(f"   • {rec}")

    return "\n".join(output)


def show_history(engine, limit):
    """Show recent analysis history"""
    analyses = engine.db.get_recent_analyses(limit)

    if not analyses:
        print("📊 No analyses found in database")
        return

    print(f"📊 Recent Analyses (Last {len(analyses)})")
    print("=" * 60)

    for analysis in analyses:
        timestamp = analysis['analysis_timestamp']
        loan_id = analysis['loan_id'] or 'N/A'
        print(f"{timestamp} | Loan: {loan_id} | "
              f"${analysis['loan_amount_usd']:,.0f} | "
              f"Ratio: {analysis['required_collateral_ratio']:.2f}x | "
              f"Risk: {analysis['risk_level']}")


def show_stats(engine):
    """Show database statistics"""
    stats = engine.db.get_analysis_statistics()

    print("📈 Database Statistics")
    print("=" * 30)
    print(f"Total Analyses: {stats['total_analyses']}")
    print(f"Analyses Last 24h: {stats['analyses_last_24h']}")

    if stats['average_collateral_ratio']:
        print(f"Average Collateral Ratio: {stats['average_collateral_ratio']:.2f}x")

    if stats['risk_level_distribution']:
        print("\nRisk Level Distribution:")
        for risk_level, count in stats['risk_level_distribution'].items():
            print(f"  {risk_level}: {count}")


async def main():
    """Main CLI function"""
    parser = create_parser()
    args = parser.parse_args()

    # Initialize engine with config
    config_path = Path(args.config) if args.config else None
    engine = CollateralRequirementsEngine(config_path=config_path)

    # Handle different command modes
    if args.history:
        show_history(engine, args.limit)
        return

    if args.stats:
        show_stats(engine)
        return

    # Quick ALGO analysis
    if args.quick_algo:
        if not args.amount or not args.loan:
            print("❌ Quick ALGO analysis requires --amount and --loan")
            sys.exit(1)

        loan_amount = args.loan
        positions = [{
            'asset_id': '0',
            'asset_symbol': 'ALGO',
            'amount': args.amount
        }]
        market_conditions = args.market_conditions

        print(f"🚀 Quick ALGO Analysis: {args.amount:,} ALGO for ${loan_amount:,} loan")
        print()

    else:
        # Standard analysis
        if not args.loan_amount or not args.collateral:
            print("❌ Standard analysis requires --loan-amount and --collateral")
            parser.print_help()
            sys.exit(1)

        loan_amount = args.loan_amount
        positions = parse_collateral_positions(args.collateral)
        market_conditions = args.market_conditions

    # Run analysis
    result = await run_analysis(
        engine, loan_amount, positions, market_conditions,
        args.loan_id, args.borrower, args.verbose
    )

    if result:
        if args.json:
            print(format_result_json(result))
        else:
            print(format_result_text(result, args.verbose))


if __name__ == "__main__":
    asyncio.run(main())