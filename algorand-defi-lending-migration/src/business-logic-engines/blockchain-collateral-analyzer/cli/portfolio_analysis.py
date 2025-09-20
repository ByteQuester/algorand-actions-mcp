#!/usr/bin/env python3
"""
CLI for Portfolio Diversification Engine.

Provides command-line interface for portfolio diversification analysis.
"""

import argparse
import sys
import logging
import json
from typing import Optional

# Add the parent directory to the path to allow imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    """Main entry point for portfolio analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Portfolio Diversification Engine - Analyze portfolio diversification and risk"
    )

    parser.add_argument(
        "--portfolio-file",
        required=True,
        help="Path to portfolio configuration file (JSON/YAML)"
    )

    parser.add_argument(
        "--analysis-type",
        choices=["diversification", "correlation", "risk", "optimization", "all"],
        default="all",
        help="Type of analysis to perform (default: all)"
    )

    parser.add_argument(
        "--rebalance",
        action="store_true",
        help="Generate portfolio rebalancing recommendations"
    )

    parser.add_argument(
        "--target-allocation",
        help="Path to target allocation file for rebalancing"
    )

    parser.add_argument(
        "--output-format",
        choices=["json", "text", "csv", "report"],
        default="text",
        help="Output format (default: text)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--config-file",
        help="Path to configuration file"
    )

    parser.add_argument(
        "--include-charts",
        action="store_true",
        help="Generate portfolio analysis charts"
    )

    parser.add_argument(
        "--save-report",
        help="Save detailed report to specified file"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Import the engine
        try:
            from portfolio_diversification.core.portfolio_engine import PortfolioEngine
        except ImportError as e:
            logger.error(f"Failed to import PortfolioEngine: {e}")
            print("Error: Portfolio Diversification Engine is not available.")
            print("Please ensure the engine is properly installed.")
            return 1

        # Initialize the engine
        logger.info("Initializing Portfolio Diversification Engine...")

        config = {}
        if args.config_file:
            try:
                with open(args.config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                return 1

        engine = PortfolioEngine(config=config)

        # Load portfolio data
        logger.info(f"Loading portfolio from {args.portfolio_file}...")

        try:
            portfolio_data = engine.load_portfolio(args.portfolio_file)
        except Exception as e:
            logger.error(f"Failed to load portfolio file: {e}")
            return 1

        # Load target allocation if provided
        target_allocation = None
        if args.target_allocation:
            try:
                with open(args.target_allocation, 'r') as f:
                    if args.target_allocation.endswith('.json'):
                        target_allocation = json.load(f)
                    else:  # Assume YAML
                        import yaml
                        target_allocation = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Failed to load target allocation file: {e}")
                return 1

        # Perform portfolio analysis
        logger.info(f"Performing portfolio analysis...")

        result = engine.analyze_portfolio(
            portfolio_data=portfolio_data,
            analysis_type=args.analysis_type,
            rebalance=args.rebalance,
            target_allocation=target_allocation,
            include_charts=args.include_charts
        )

        # Output results
        if args.output_format == "json":
            print(json.dumps(result, indent=2, default=str))
        elif args.output_format == "csv":
            _output_csv(result, args)
        elif args.output_format == "report":
            _generate_detailed_report(result, args)
        else:  # text format
            _display_analysis_results(result, args)

        # Save report if requested
        if args.save_report:
            logger.info(f"Saving detailed report to {args.save_report}...")
            _save_report(result, args.save_report, args)

        logger.info("Portfolio analysis completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during portfolio analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def _display_analysis_results(result, args):
    """Display analysis results in text format."""
    if not isinstance(result, dict):
        print(f"Portfolio Analysis Result: {result}")
        return

    print(f"Portfolio Diversification Analysis")
    print("=" * 50)

    # Portfolio overview
    if 'overview' in result:
        overview = result['overview']
        print(f"\nPortfolio Overview:")
        print(f"  Total Value: ${overview.get('total_value', 'N/A'):,.2f}")
        print(f"  Number of Assets: {overview.get('asset_count', 'N/A')}")
        print(f"  Portfolio Currency: {overview.get('currency', 'USD')}")

    # Diversification metrics
    if 'diversification' in result:
        div = result['diversification']
        print(f"\nDiversification Metrics:")
        print(f"  Diversification Score: {div.get('score', 'N/A'):.2f}/10")
        print(f"  Concentration Risk: {div.get('concentration_risk', 'N/A')}")
        print(f"  Herfindahl Index: {div.get('herfindahl_index', 'N/A'):.4f}")

        if 'largest_positions' in div:
            print(f"\n  Largest Positions:")
            for i, position in enumerate(div['largest_positions'][:5], 1):
                asset = position.get('asset', 'N/A')
                weight = position.get('weight', 0)
                value = position.get('value', 0)
                print(f"    {i}. {asset}: {weight:.1%} (${value:,.2f})")

    # Risk analysis
    if 'risk' in result:
        risk = result['risk']
        print(f"\nRisk Analysis:")
        print(f"  Portfolio Volatility: {risk.get('volatility', 'N/A'):.2%}")
        print(f"  Value at Risk (95%): {risk.get('var_95', 'N/A'):.2%}")
        print(f"  Expected Shortfall: {risk.get('expected_shortfall', 'N/A'):.2%}")
        print(f"  Beta: {risk.get('beta', 'N/A'):.2f}")

    # Correlation analysis
    if 'correlation' in result:
        corr = result['correlation']
        print(f"\nCorrelation Analysis:")
        print(f"  Average Correlation: {corr.get('average_correlation', 'N/A'):.2f}")
        print(f"  Max Correlation: {corr.get('max_correlation', 'N/A'):.2f}")

        if 'high_correlations' in corr:
            print(f"\n  High Correlations (>0.7):")
            for pair in corr['high_correlations'][:5]:
                asset1 = pair.get('asset1', 'N/A')
                asset2 = pair.get('asset2', 'N/A')
                correlation = pair.get('correlation', 0)
                print(f"    {asset1} - {asset2}: {correlation:.2f}")

    # Optimization recommendations
    if 'optimization' in result:
        opt = result['optimization']
        print(f"\nOptimization Recommendations:")
        print(f"  Current Sharpe Ratio: {opt.get('current_sharpe', 'N/A'):.2f}")
        print(f"  Optimal Sharpe Ratio: {opt.get('optimal_sharpe', 'N/A'):.2f}")

        if 'recommended_weights' in opt:
            print(f"\n  Recommended Asset Allocation:")
            for asset, weight in opt['recommended_weights'].items():
                print(f"    {asset}: {weight:.1%}")

    # Rebalancing recommendations
    if args.rebalance and 'rebalancing' in result:
        rebal = result['rebalancing']
        print(f"\nRebalancing Recommendations:")

        if 'trades' in rebal:
            print(f"\n  Required Trades:")
            print(f"    {'Asset':<15} {'Action':<6} {'Amount':<12} {'Value'}")
            print(f"    {'-'*15} {'-'*6} {'-'*12} {'-'*12}")

            for trade in rebal['trades']:
                asset = trade.get('asset', 'N/A')
                action = trade.get('action', 'N/A')
                amount = trade.get('amount', 0)
                value = trade.get('value', 0)
                print(f"    {asset:<15} {action:<6} {amount:<12.4f} ${value:,.2f}")

        total_trades = rebal.get('total_trade_value', 0)
        print(f"\n  Total Trade Value: ${total_trades:,.2f}")

    # Charts
    if args.include_charts and 'charts' in result:
        print(f"\nCharts Generated:")
        for chart_type, path in result['charts'].items():
            print(f"  {chart_type}: {path}")

def _output_csv(result, args):
    """Output analysis results in CSV format."""
    if not isinstance(result, dict):
        print("analysis_type,result")
        print(f"{args.analysis_type},{result}")
        return

    # Asset allocation CSV
    if 'overview' in result and 'allocations' in result['overview']:
        print("asset,weight,value,allocation_type")
        for asset, data in result['overview']['allocations'].items():
            weight = data.get('weight', 0)
            value = data.get('value', 0)
            allocation_type = data.get('type', 'unknown')
            print(f"{asset},{weight},{value},{allocation_type}")

def _generate_detailed_report(result, args):
    """Generate a detailed text report."""
    print("PORTFOLIO DIVERSIFICATION ANALYSIS REPORT")
    print("=" * 60)
    print(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Portfolio File: {args.portfolio_file}")
    print(f"Analysis Type: {args.analysis_type}")
    print("=" * 60)

    _display_analysis_results(result, args)

    print("\n" + "=" * 60)
    print("END OF REPORT")

def _save_report(result, filename, args):
    """Save detailed report to file."""
    import sys
    from io import StringIO

    # Capture the output
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    _generate_detailed_report(result, args)

    # Restore stdout
    sys.stdout = old_stdout

    # Save to file
    with open(filename, 'w') as f:
        f.write(captured_output.getvalue())

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)