#!/usr/bin/env python3
"""
Main CLI entry point for blockchain-collateral-analyzer.

This provides a unified command-line interface to access all collateral analysis engines.
"""

import argparse
import sys
import logging
from typing import Optional

# Add the parent directory to the path to allow imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try to import from parent package
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    import __init__ as analyzer_init
    get_available_engines = analyzer_init.get_available_engines
    check_engine_availability = analyzer_init.check_engine_availability
    __version__ = analyzer_init.__version__
except ImportError as e:
    # Fallback for when running as a script
    __version__ = "1.0.0"
    def get_available_engines():
        print("Warning: Engine availability check not available - engines may not be properly imported.")
        return {}
    def check_engine_availability():
        print("Engine availability check not available in script mode.")
        print("This is normal when running CLI tools directly.")
        return {}

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Blockchain Collateral Analyzer - Comprehensive DeFi collateral analysis for Algorand",
        epilog="Use 'collateral-analyzer <subcommand> --help' for detailed help on specific engines."
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"blockchain-collateral-analyzer {__version__}"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--check-engines",
        action="store_true",
        help="Check which analysis engines are available"
    )

    subparsers = parser.add_subparsers(
        dest="engine",
        title="Analysis Engines",
        description="Available collateral analysis engines",
        help="Choose an analysis engine to run"
    )

    # Asset Valuation Engine
    asset_parser = subparsers.add_parser(
        "asset-valuation",
        help="Digital asset valuation engine"
    )
    asset_parser.add_argument(
        "--asset-id",
        required=True,
        help="Asset ID to valuate"
    )
    asset_parser.add_argument(
        "--amount",
        type=float,
        default=1.0,
        help="Amount of the asset"
    )

    # Volatility Assessment Engine
    volatility_parser = subparsers.add_parser(
        "volatility-assessment",
        help="Volatility assessment and VaR calculation engine"
    )
    volatility_parser.add_argument(
        "--asset-id",
        required=True,
        help="Asset ID to assess volatility"
    )
    volatility_parser.add_argument(
        "--period",
        type=int,
        default=30,
        help="Assessment period in days"
    )

    # Liquidation Scenarios Engine
    liquidation_parser = subparsers.add_parser(
        "liquidation-scenarios",
        help="Liquidation scenario modeling engine"
    )
    liquidation_parser.add_argument(
        "--collateral-value",
        type=float,
        required=True,
        help="Current collateral value"
    )
    liquidation_parser.add_argument(
        "--loan-value",
        type=float,
        required=True,
        help="Current loan value"
    )

    # Oracle Integration Engine
    oracle_parser = subparsers.add_parser(
        "oracle-integration",
        help="Oracle price feed integration engine"
    )
    oracle_parser.add_argument(
        "--asset-id",
        required=True,
        help="Asset ID to get oracle price"
    )
    oracle_parser.add_argument(
        "--oracle-type",
        choices=["chainlink", "pyth", "algorand"],
        default="algorand",
        help="Oracle type to use"
    )

    # Portfolio Analysis Engine
    portfolio_parser = subparsers.add_parser(
        "portfolio-analysis",
        help="Portfolio diversification analysis engine"
    )
    portfolio_parser.add_argument(
        "--portfolio-file",
        required=True,
        help="Path to portfolio configuration file"
    )

    # Collateral Requirements Engine
    collateral_parser = subparsers.add_parser(
        "collateral-requirements",
        help="Final collateral requirement determination engine"
    )
    collateral_parser.add_argument(
        "--loan-amount",
        type=float,
        required=True,
        help="Loan amount to calculate requirements for"
    )
    collateral_parser.add_argument(
        "--asset-type",
        required=True,
        help="Type of collateral asset"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Check engines if requested
    if args.check_engines:
        check_engine_availability()
        return 0

    # If no subcommand is provided, show help
    if not args.engine:
        parser.print_help()
        return 1

    # Get available engines
    available_engines = get_available_engines()

    try:
        if args.engine == "asset-valuation":
            if 'digital_asset_valuation' not in available_engines:
                print("Error: Digital Asset Valuation Engine is not available.")
                print("Run 'collateral-analyzer --check-engines' to see available engines.")
                return 1

            engine_class = available_engines['digital_asset_valuation']
            engine = engine_class()
            result = engine.valuate_asset(args.asset_id, args.amount)
            print(f"Asset Valuation Result: {result}")

        elif args.engine == "volatility-assessment":
            if 'volatility_assessment' not in available_engines:
                print("Error: Volatility Assessment Engine is not available.")
                return 1

            engine_class = available_engines['volatility_assessment']
            engine = engine_class()
            result = engine.assess_volatility(args.asset_id, args.period)
            print(f"Volatility Assessment Result: {result}")

        elif args.engine == "liquidation-scenarios":
            if 'liquidation_scenarios' not in available_engines:
                print("Error: Liquidation Scenarios Engine is not available.")
                return 1

            engine_class = available_engines['liquidation_scenarios']
            engine = engine_class()
            result = engine.model_liquidation(args.collateral_value, args.loan_value)
            print(f"Liquidation Scenarios Result: {result}")

        elif args.engine == "oracle-integration":
            if 'oracle_price_integration' not in available_engines:
                print("Error: Oracle Price Integration Engine is not available.")
                return 1

            engine_class = available_engines['oracle_price_integration']
            engine = engine_class()
            result = engine.get_price(args.asset_id, args.oracle_type)
            print(f"Oracle Price Result: {result}")

        elif args.engine == "portfolio-analysis":
            if 'portfolio_diversification' not in available_engines:
                print("Error: Portfolio Diversification Engine is not available.")
                return 1

            engine_class = available_engines['portfolio_diversification']
            engine = engine_class()
            result = engine.analyze_portfolio(args.portfolio_file)
            print(f"Portfolio Analysis Result: {result}")

        elif args.engine == "collateral-requirements":
            if 'collateral_requirements' not in available_engines:
                print("Error: Collateral Requirements Engine is not available.")
                return 1

            engine_class = available_engines['collateral_requirements']
            engine = engine_class()
            result = engine.calculate_requirements(args.loan_amount, args.asset_type)
            print(f"Collateral Requirements Result: {result}")

        else:
            print(f"Unknown engine: {args.engine}")
            return 1

    except Exception as e:
        logging.error(f"Error running {args.engine} engine: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)