#!/usr/bin/env python3
"""
CLI for Digital Asset Valuation Engine.

Provides command-line interface for real-time digital asset valuation.
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
    """Main entry point for asset valuation CLI."""
    parser = argparse.ArgumentParser(
        description="Digital Asset Valuation Engine - Real-time cryptocurrency valuation"
    )

    parser.add_argument(
        "--asset-id",
        required=True,
        help="Asset ID or symbol to valuate (e.g., ALGO, 31566704 for USDC)"
    )

    parser.add_argument(
        "--amount",
        type=float,
        default=1.0,
        help="Amount of the asset to valuate (default: 1.0)"
    )

    parser.add_argument(
        "--currency",
        default="USD",
        choices=["USD", "EUR", "BTC", "ETH"],
        help="Target currency for valuation (default: USD)"
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
        "--include-metadata",
        action="store_true",
        help="Include asset metadata in output"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Import the engine
        try:
            from digital_asset_valuation.core.engine import DigitalAssetValuationEngine
        except ImportError as e:
            logger.error(f"Failed to import DigitalAssetValuationEngine: {e}")
            print("Error: Digital Asset Valuation Engine is not available.")
            print("Please ensure the engine is properly installed.")
            return 1

        # Initialize the engine
        logger.info("Initializing Digital Asset Valuation Engine...")

        config = {}
        if args.config_file:
            try:
                with open(args.config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                return 1

        engine = DigitalAssetValuationEngine(config=config)

        # Perform valuation
        logger.info(f"Valuating {args.amount} {args.asset_id} in {args.currency}...")

        result = engine.valuate_asset(
            asset_id=args.asset_id,
            amount=args.amount,
            target_currency=args.currency,
            include_metadata=args.include_metadata
        )

        # Output results
        if args.output_format == "json":
            print(json.dumps(result, indent=2, default=str))
        elif args.output_format == "csv":
            if isinstance(result, dict):
                print("asset_id,amount,value,currency,timestamp")
                print(f"{args.asset_id},{args.amount},{result.get('value', 'N/A')},{args.currency},{result.get('timestamp', 'N/A')}")
            else:
                print("asset_id,amount,value,currency")
                print(f"{args.asset_id},{args.amount},{result},{args.currency}")
        else:  # text format
            if isinstance(result, dict):
                print(f"Asset Valuation Results:")
                print(f"  Asset ID: {args.asset_id}")
                print(f"  Amount: {args.amount}")
                print(f"  Value: {result.get('value', 'N/A')} {args.currency}")
                print(f"  Timestamp: {result.get('timestamp', 'N/A')}")

                if args.include_metadata and 'metadata' in result:
                    print(f"  Metadata:")
                    for key, value in result['metadata'].items():
                        print(f"    {key}: {value}")
            else:
                print(f"Asset: {args.asset_id}")
                print(f"Amount: {args.amount}")
                print(f"Value: {result} {args.currency}")

        logger.info("Valuation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during asset valuation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)