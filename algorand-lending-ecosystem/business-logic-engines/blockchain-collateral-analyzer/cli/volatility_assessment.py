#!/usr/bin/env python3
"""
CLI for Volatility Assessment Engine.

Provides command-line interface for cryptocurrency volatility analysis and VaR calculations.
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
    """Main entry point for volatility assessment CLI."""
    parser = argparse.ArgumentParser(
        description="Volatility Assessment Engine - Cryptocurrency volatility analysis and VaR calculations"
    )

    parser.add_argument(
        "--asset-id",
        required=True,
        help="Asset ID or symbol to assess (e.g., ALGO, 31566704 for USDC)"
    )

    parser.add_argument(
        "--period",
        type=int,
        default=30,
        help="Assessment period in days (default: 30)"
    )

    parser.add_argument(
        "--confidence-level",
        type=float,
        default=0.95,
        help="Confidence level for VaR calculation (default: 0.95)"
    )

    parser.add_argument(
        "--method",
        choices=["historical", "parametric", "monte_carlo"],
        default="historical",
        help="VaR calculation method (default: historical)"
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
        help="Generate volatility charts (requires matplotlib)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Import the engine
        try:
            from volatility_assessment.core.volatility_engine import VolatilityAssessmentEngine
        except ImportError as e:
            logger.error(f"Failed to import VolatilityAssessmentEngine: {e}")
            print("Error: Volatility Assessment Engine is not available.")
            print("Please ensure the engine is properly installed.")
            return 1

        # Initialize the engine
        logger.info("Initializing Volatility Assessment Engine...")

        config = {}
        if args.config_file:
            try:
                with open(args.config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                return 1

        engine = VolatilityAssessmentEngine(config=config)

        # Perform volatility assessment
        logger.info(f"Assessing volatility for {args.asset_id} over {args.period} days...")

        result = engine.assess_volatility(
            asset_id=args.asset_id,
            period_days=args.period,
            confidence_level=args.confidence_level,
            method=args.method,
            include_charts=args.include_charts
        )

        # Output results
        if args.output_format == "json":
            print(json.dumps(result, indent=2, default=str))
        elif args.output_format == "csv":
            if isinstance(result, dict):
                print("asset_id,period_days,volatility,var,confidence_level,method")
                print(f"{args.asset_id},{args.period},{result.get('volatility', 'N/A')},{result.get('var', 'N/A')},{args.confidence_level},{args.method}")
            else:
                print("asset_id,period_days,result")
                print(f"{args.asset_id},{args.period},{result}")
        else:  # text format
            if isinstance(result, dict):
                print(f"Volatility Assessment Results:")
                print(f"  Asset ID: {args.asset_id}")
                print(f"  Assessment Period: {args.period} days")
                print(f"  Volatility: {result.get('volatility', 'N/A'):.4f}")
                print(f"  Value at Risk ({args.confidence_level*100:.1f}%): {result.get('var', 'N/A'):.4f}")
                print(f"  Method: {args.method}")
                print(f"  Timestamp: {result.get('timestamp', 'N/A')}")

                if 'risk_metrics' in result:
                    print(f"  Risk Metrics:")
                    for metric, value in result['risk_metrics'].items():
                        print(f"    {metric}: {value}")

                if args.include_charts and 'chart_path' in result:
                    print(f"  Chart saved to: {result['chart_path']}")
            else:
                print(f"Asset: {args.asset_id}")
                print(f"Period: {args.period} days")
                print(f"Volatility Result: {result}")

        logger.info("Volatility assessment completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during volatility assessment: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)