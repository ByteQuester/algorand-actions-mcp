#!/usr/bin/env python3
"""
CLI for Oracle Price Integration Engine.

Provides command-line interface for oracle price feed integration and analysis.
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
    """Main entry point for oracle integration CLI."""
    parser = argparse.ArgumentParser(
        description="Oracle Price Integration Engine - Integrate with multiple oracle price feeds"
    )

    parser.add_argument(
        "--asset-id",
        required=True,
        help="Asset ID or symbol to get oracle price for"
    )

    parser.add_argument(
        "--oracle-type",
        choices=["chainlink", "pyth", "algorand", "coingecko", "all"],
        default="all",
        help="Oracle type to use (default: all)"
    )

    parser.add_argument(
        "--compare-sources",
        action="store_true",
        help="Compare prices from multiple oracle sources"
    )

    parser.add_argument(
        "--historical-data",
        type=int,
        help="Fetch historical data for N days"
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
        "--refresh-interval",
        type=int,
        default=0,
        help="Refresh price data every N seconds (0 for one-time fetch)"
    )

    parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Include oracle metadata in output"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Import the engine
        try:
            from oracle_price_integration.core.oracle_engine import OraclePriceIntegrationEngine
        except ImportError as e:
            logger.error(f"Failed to import OraclePriceIntegrationEngine: {e}")
            print("Error: Oracle Price Integration Engine is not available.")
            print("Please ensure the engine is properly installed.")
            return 1

        # Initialize the engine
        logger.info("Initializing Oracle Price Integration Engine...")

        config = {}
        if args.config_file:
            try:
                with open(args.config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                return 1

        engine = OraclePriceIntegrationEngine(config=config)

        if args.refresh_interval > 0:
            # Continuous price monitoring
            logger.info(f"Starting continuous price monitoring for {args.asset_id} (refresh every {args.refresh_interval}s)...")
            import time

            try:
                while True:
                    result = engine.get_price_data(
                        asset_id=args.asset_id,
                        oracle_type=args.oracle_type,
                        compare_sources=args.compare_sources,
                        include_metadata=args.include_metadata
                    )

                    # Clear screen and show updated data
                    os.system('clear' if os.name == 'posix' else 'cls')
                    print(f"Oracle Price Data for {args.asset_id} (updating every {args.refresh_interval}s)")
                    print("=" * 60)

                    if args.output_format == "json":
                        print(json.dumps(result, indent=2, default=str))
                    else:
                        _display_price_data(result, args)

                    print(f"\nPress Ctrl+C to stop monitoring...")
                    time.sleep(args.refresh_interval)

            except KeyboardInterrupt:
                print("\nMonitoring stopped.")
                return 0

        else:
            # One-time price fetch
            logger.info(f"Fetching oracle price data for {args.asset_id}...")

            if args.historical_data:
                result = engine.get_historical_prices(
                    asset_id=args.asset_id,
                    days=args.historical_data,
                    oracle_type=args.oracle_type
                )
            else:
                result = engine.get_price_data(
                    asset_id=args.asset_id,
                    oracle_type=args.oracle_type,
                    compare_sources=args.compare_sources,
                    include_metadata=args.include_metadata
                )

            # Output results
            if args.output_format == "json":
                print(json.dumps(result, indent=2, default=str))
            elif args.output_format == "csv":
                _output_csv(result, args)
            else:  # text format
                _display_price_data(result, args)

        logger.info("Oracle price data fetch completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during oracle price integration: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def _display_price_data(result, args):
    """Display price data in text format."""
    if isinstance(result, dict):
        if args.historical_data:
            # Historical data display
            print(f"Historical Oracle Price Data:")
            print(f"  Asset ID: {args.asset_id}")
            print(f"  Period: {args.historical_data} days")
            print(f"  Oracle: {args.oracle_type}")

            if 'prices' in result:
                print(f"\n  Historical Prices:")
                print(f"    {'Date':<12} {'Price':<12} {'Source'}")
                print(f"    {'-'*12} {'-'*12} {'-'*12}")
                for price_data in result['prices'][-10:]:  # Show last 10 entries
                    date = price_data.get('date', 'N/A')
                    price = price_data.get('price', 'N/A')
                    source = price_data.get('source', 'N/A')
                    print(f"    {date:<12} ${price:<11.4f} {source}")

        else:
            # Current price data display
            print(f"Oracle Price Data:")
            print(f"  Asset ID: {args.asset_id}")

            if args.compare_sources and 'sources' in result:
                print(f"\n  Price Comparison:")
                print(f"    {'Oracle':<15} {'Price':<12} {'Timestamp':<20} {'Status'}")
                print(f"    {'-'*15} {'-'*12} {'-'*20} {'-'*10}")

                for source, data in result['sources'].items():
                    price = data.get('price', 'N/A')
                    timestamp = data.get('timestamp', 'N/A')
                    status = data.get('status', 'N/A')
                    print(f"    {source:<15} ${price:<11.4f} {str(timestamp):<20} {status}")

                if 'aggregated' in result:
                    agg = result['aggregated']
                    print(f"\n  Aggregated Price: ${agg.get('price', 'N/A'):.4f}")
                    print(f"  Confidence Score: {agg.get('confidence', 'N/A'):.2%}")
                    print(f"  Price Deviation: {agg.get('deviation', 'N/A'):.2%}")

            else:
                print(f"  Current Price: ${result.get('price', 'N/A'):.4f}")
                print(f"  Oracle Source: {result.get('source', 'N/A')}")
                print(f"  Timestamp: {result.get('timestamp', 'N/A')}")

            if args.include_metadata and 'metadata' in result:
                print(f"\n  Oracle Metadata:")
                for key, value in result['metadata'].items():
                    print(f"    {key}: {value}")

    else:
        print(f"Asset: {args.asset_id}")
        print(f"Oracle Price Result: {result}")

def _output_csv(result, args):
    """Output price data in CSV format."""
    if args.historical_data and isinstance(result, dict) and 'prices' in result:
        print("date,price,source,asset_id")
        for price_data in result['prices']:
            date = price_data.get('date', 'N/A')
            price = price_data.get('price', 'N/A')
            source = price_data.get('source', 'N/A')
            print(f"{date},{price},{source},{args.asset_id}")
    elif args.compare_sources and isinstance(result, dict) and 'sources' in result:
        print("oracle,price,timestamp,status,asset_id")
        for source, data in result['sources'].items():
            price = data.get('price', 'N/A')
            timestamp = data.get('timestamp', 'N/A')
            status = data.get('status', 'N/A')
            print(f"{source},{price},{timestamp},{status},{args.asset_id}")
    else:
        print("asset_id,price,source,timestamp")
        if isinstance(result, dict):
            price = result.get('price', 'N/A')
            source = result.get('source', 'N/A')
            timestamp = result.get('timestamp', 'N/A')
            print(f"{args.asset_id},{price},{source},{timestamp}")
        else:
            print(f"{args.asset_id},{result},unknown,N/A")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)