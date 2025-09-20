#!/usr/bin/env python3
"""
CLI for Liquidation Scenarios Engine.

Provides command-line interface for liquidation scenario modeling and analysis.
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
    """Main entry point for liquidation scenarios CLI."""
    parser = argparse.ArgumentParser(
        description="Liquidation Scenarios Engine - Model liquidation scenarios for collateralized loans"
    )

    parser.add_argument(
        "--collateral-value",
        type=float,
        required=True,
        help="Current collateral value in USD"
    )

    parser.add_argument(
        "--loan-value",
        type=float,
        required=True,
        help="Current loan value in USD"
    )

    parser.add_argument(
        "--liquidation-threshold",
        type=float,
        default=0.75,
        help="Liquidation threshold ratio (default: 0.75)"
    )

    parser.add_argument(
        "--price-scenarios",
        nargs="+",
        type=float,
        help="Price change scenarios to model (e.g., -0.1 -0.2 -0.3 for 10%, 20%, 30% drops)"
    )

    parser.add_argument(
        "--time-horizon",
        type=int,
        default=7,
        help="Time horizon for liquidation scenarios in days (default: 7)"
    )

    parser.add_argument(
        "--output-format",
        choices=["json", "text", "csv"],
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
        help="Generate liquidation scenario charts"
    )

    parser.add_argument(
        "--stress-test",
        action="store_true",
        help="Include stress test scenarios"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Import the engine
        try:
            from liquidation_scenarios.core.liquidation_engine import LiquidationEngine
        except ImportError as e:
            logger.error(f"Failed to import LiquidationEngine: {e}")
            print("Error: Liquidation Scenarios Engine is not available.")
            print("Please ensure the engine is properly installed.")
            return 1

        # Initialize the engine
        logger.info("Initializing Liquidation Scenarios Engine...")

        config = {}
        if args.config_file:
            try:
                with open(args.config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                return 1

        engine = LiquidationEngine(config=config)

        # Perform liquidation scenario modeling
        logger.info(f"Modeling liquidation scenarios...")

        # Default price scenarios if not provided
        if not args.price_scenarios:
            args.price_scenarios = [-0.05, -0.10, -0.15, -0.20, -0.25, -0.30, -0.40, -0.50]

        result = engine.model_liquidation_scenarios(
            collateral_value=args.collateral_value,
            loan_value=args.loan_value,
            liquidation_threshold=args.liquidation_threshold,
            price_scenarios=args.price_scenarios,
            time_horizon_days=args.time_horizon,
            include_stress_test=args.stress_test,
            include_charts=args.include_charts
        )

        # Output results
        if args.output_format == "json":
            print(json.dumps(result, indent=2, default=str))
        elif args.output_format == "csv":
            if isinstance(result, dict) and 'scenarios' in result:
                print("scenario,price_change,collateral_value,loan_value,ltv_ratio,liquidation_triggered")
                for i, scenario in enumerate(result['scenarios']):
                    print(f"{i+1},{scenario.get('price_change', 'N/A')},{scenario.get('collateral_value', 'N/A')},{scenario.get('loan_value', 'N/A')},{scenario.get('ltv_ratio', 'N/A')},{scenario.get('liquidation_triggered', 'N/A')}")
            else:
                print("collateral_value,loan_value,result")
                print(f"{args.collateral_value},{args.loan_value},{result}")
        else:  # text format
            if isinstance(result, dict):
                print(f"Liquidation Scenarios Analysis:")
                print(f"  Initial Collateral Value: ${args.collateral_value:,.2f}")
                print(f"  Initial Loan Value: ${args.loan_value:,.2f}")
                print(f"  Liquidation Threshold: {args.liquidation_threshold:.2%}")
                print(f"  Current LTV Ratio: {(args.loan_value / args.collateral_value):.2%}")
                print(f"  Time Horizon: {args.time_horizon} days")

                if 'scenarios' in result:
                    print(f"\n  Scenario Results:")
                    print(f"    {'Price Change':<12} {'Collateral':<12} {'LTV Ratio':<10} {'Liquidation'}")
                    print(f"    {'-'*12} {'-'*12} {'-'*10} {'-'*10}")

                    for scenario in result['scenarios']:
                        price_change = scenario.get('price_change', 0)
                        new_collateral = scenario.get('collateral_value', 0)
                        ltv_ratio = scenario.get('ltv_ratio', 0)
                        liquidated = scenario.get('liquidation_triggered', False)

                        print(f"    {price_change:>10.1%} ${new_collateral:>10,.0f} {ltv_ratio:>8.1%} {'YES' if liquidated else 'NO'}")

                if 'risk_metrics' in result:
                    print(f"\n  Risk Metrics:")
                    for metric, value in result['risk_metrics'].items():
                        print(f"    {metric}: {value}")

                if args.include_charts and 'chart_path' in result:
                    print(f"\n  Chart saved to: {result['chart_path']}")

                if args.stress_test and 'stress_test' in result:
                    print(f"\n  Stress Test Results:")
                    stress = result['stress_test']
                    print(f"    Worst Case Scenario: {stress.get('worst_case', 'N/A')}")
                    print(f"    Probability of Liquidation: {stress.get('liquidation_probability', 'N/A'):.2%}")
            else:
                print(f"Collateral Value: ${args.collateral_value:,.2f}")
                print(f"Loan Value: ${args.loan_value:,.2f}")
                print(f"Liquidation Analysis Result: {result}")

        logger.info("Liquidation scenario analysis completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during liquidation scenario analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)