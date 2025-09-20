#!/usr/bin/env python3
"""
CLI for Collateral Requirements Engine.

Provides command-line interface for final collateral requirement determination.
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
    """Main entry point for collateral requirements CLI."""
    parser = argparse.ArgumentParser(
        description="Collateral Requirements Engine - Determine final collateral requirements for lending"
    )

    parser.add_argument(
        "--loan-amount",
        type=float,
        required=True,
        help="Loan amount in USD"
    )

    parser.add_argument(
        "--asset-type",
        required=True,
        help="Type of collateral asset (e.g., ALGO, USDC, BTC)"
    )

    parser.add_argument(
        "--borrower-profile",
        choices=["conservative", "moderate", "aggressive"],
        default="moderate",
        help="Borrower risk profile (default: moderate)"
    )

    parser.add_argument(
        "--loan-term",
        type=int,
        default=30,
        help="Loan term in days (default: 30)"
    )

    parser.add_argument(
        "--custom-ltv",
        type=float,
        help="Custom LTV ratio override (0.0-1.0)"
    )

    parser.add_argument(
        "--include-analysis",
        action="store_true",
        help="Include detailed analysis breakdown"
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
        "--save-analysis",
        help="Save detailed analysis to specified file"
    )

    parser.add_argument(
        "--portfolio-file",
        help="Path to collateral portfolio file for multi-asset analysis"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Import the engine
        try:
            from collateral_requirements.core.collateral_engine import CollateralRequirementsEngine
        except ImportError as e:
            logger.error(f"Failed to import CollateralRequirementsEngine: {e}")
            print("Error: Collateral Requirements Engine is not available.")
            print("Please ensure the engine is properly installed.")
            return 1

        # Initialize the engine
        logger.info("Initializing Collateral Requirements Engine...")

        config = {}
        if args.config_file:
            try:
                with open(args.config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                return 1

        engine = CollateralRequirementsEngine(config=config)

        # Load portfolio if provided
        portfolio_data = None
        if args.portfolio_file:
            try:
                with open(args.portfolio_file, 'r') as f:
                    if args.portfolio_file.endswith('.json'):
                        portfolio_data = json.load(f)
                    else:  # Assume YAML
                        import yaml
                        portfolio_data = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Failed to load portfolio file: {e}")
                return 1

        # Calculate collateral requirements
        logger.info(f"Calculating collateral requirements...")

        if portfolio_data:
            # Multi-asset collateral analysis
            result = engine.calculate_portfolio_requirements(
                loan_amount=args.loan_amount,
                portfolio_data=portfolio_data,
                borrower_profile=args.borrower_profile,
                loan_term_days=args.loan_term,
                custom_ltv=args.custom_ltv,
                include_analysis=args.include_analysis
            )
        else:
            # Single asset collateral analysis
            result = engine.calculate_requirements(
                loan_amount=args.loan_amount,
                asset_type=args.asset_type,
                borrower_profile=args.borrower_profile,
                loan_term_days=args.loan_term,
                custom_ltv=args.custom_ltv,
                include_analysis=args.include_analysis
            )

        # Output results
        if args.output_format == "json":
            print(json.dumps(result, indent=2, default=str))
        elif args.output_format == "csv":
            _output_csv(result, args)
        else:  # text format
            _display_requirements(result, args)

        # Save detailed analysis if requested
        if args.save_analysis:
            logger.info(f"Saving detailed analysis to {args.save_analysis}...")
            _save_analysis(result, args.save_analysis, args)

        logger.info("Collateral requirements calculation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during collateral requirements calculation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def _display_requirements(result, args):
    """Display collateral requirements in text format."""
    if not isinstance(result, dict):
        print(f"Collateral Requirements Result: {result}")
        return

    print(f"Collateral Requirements Analysis")
    print("=" * 50)

    # Loan parameters
    print(f"\nLoan Parameters:")
    print(f"  Loan Amount: ${args.loan_amount:,.2f}")
    print(f"  Asset Type: {args.asset_type}")
    print(f"  Borrower Profile: {args.borrower_profile}")
    print(f"  Loan Term: {args.loan_term} days")

    # Core requirements
    if 'requirements' in result:
        req = result['requirements']
        print(f"\nCollateral Requirements:")
        print(f"  Required Collateral Value: ${req.get('collateral_value', 'N/A'):,.2f}")
        print(f"  LTV Ratio: {req.get('ltv_ratio', 'N/A'):.1%}")
        print(f"  Collateralization Ratio: {req.get('collateralization_ratio', 'N/A'):.1%}")

        if 'collateral_amount' in req:
            print(f"  Required {args.asset_type} Amount: {req['collateral_amount']:,.4f}")

    # Risk assessment
    if 'risk_assessment' in result:
        risk = result['risk_assessment']
        print(f"\nRisk Assessment:")
        print(f"  Risk Score: {risk.get('risk_score', 'N/A'):.1f}/10")
        print(f"  Volatility Factor: {risk.get('volatility_factor', 'N/A'):.2f}")
        print(f"  Liquidity Factor: {risk.get('liquidity_factor', 'N/A'):.2f}")
        print(f"  Credit Risk: {risk.get('credit_risk', 'N/A')}")

    # Detailed analysis
    if args.include_analysis and 'analysis' in result:
        analysis = result['analysis']
        print(f"\nDetailed Analysis:")

        if 'factors' in analysis:
            print(f"  Risk Factors:")
            for factor, value in analysis['factors'].items():
                print(f"    {factor}: {value}")

        if 'adjustments' in analysis:
            print(f"\n  LTV Adjustments:")
            for adjustment, value in analysis['adjustments'].items():
                print(f"    {adjustment}: {value:+.1%}")

        if 'stress_test' in analysis:
            stress = analysis['stress_test']
            print(f"\n  Stress Test Results:")
            print(f"    Liquidation Price: ${stress.get('liquidation_price', 'N/A'):.4f}")
            print(f"    Safety Margin: {stress.get('safety_margin', 'N/A'):.1%}")
            print(f"    Time to Liquidation: {stress.get('time_to_liquidation', 'N/A')} hours")

    # Portfolio analysis (if applicable)
    if args.portfolio_file and 'portfolio_analysis' in result:
        portfolio = result['portfolio_analysis']
        print(f"\nPortfolio Analysis:")
        print(f"  Total Portfolio Value: ${portfolio.get('total_value', 'N/A'):,.2f}")
        print(f"  Diversification Score: {portfolio.get('diversification_score', 'N/A'):.1f}/10")
        print(f"  Weighted Average LTV: {portfolio.get('weighted_ltv', 'N/A'):.1%}")

        if 'asset_breakdown' in portfolio:
            print(f"\n  Asset Breakdown:")
            print(f"    {'Asset':<10} {'Value':<12} {'Weight':<8} {'LTV':<6} {'Required'}")
            print(f"    {'-'*10} {'-'*12} {'-'*8} {'-'*6} {'-'*12}")

            for asset_data in portfolio['asset_breakdown']:
                asset = asset_data.get('asset', 'N/A')
                value = asset_data.get('value', 0)
                weight = asset_data.get('weight', 0)
                ltv = asset_data.get('ltv', 0)
                required = asset_data.get('required_amount', 0)
                print(f"    {asset:<10} ${value:<11,.0f} {weight:<7.1%} {ltv:<5.1%} {required:,.4f}")

    # Recommendations
    if 'recommendations' in result:
        rec = result['recommendations']
        print(f"\nRecommendations:")
        for i, recommendation in enumerate(rec, 1):
            print(f"  {i}. {recommendation}")

    # Warnings
    if 'warnings' in result:
        print(f"\nWarnings:")
        for warning in result['warnings']:
            print(f"  ⚠️  {warning}")

def _output_csv(result, args):
    """Output requirements in CSV format."""
    if not isinstance(result, dict):
        print("loan_amount,asset_type,result")
        print(f"{args.loan_amount},{args.asset_type},{result}")
        return

    if 'requirements' in result:
        req = result['requirements']
        print("loan_amount,asset_type,collateral_value,ltv_ratio,collateralization_ratio,collateral_amount")
        collateral_amount = req.get('collateral_amount', 'N/A')
        print(f"{args.loan_amount},{args.asset_type},{req.get('collateral_value', 'N/A')},{req.get('ltv_ratio', 'N/A')},{req.get('collateralization_ratio', 'N/A')},{collateral_amount}")
    else:
        print("loan_amount,asset_type,result")
        print(f"{args.loan_amount},{args.asset_type},calculation_failed")

def _save_analysis(result, filename, args):
    """Save detailed analysis to file."""
    import sys
    from io import StringIO

    # Capture the output
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    print("COLLATERAL REQUIREMENTS ANALYSIS REPORT")
    print("=" * 60)
    print(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Loan Amount: ${args.loan_amount:,.2f}")
    print(f"Asset Type: {args.asset_type}")
    if args.portfolio_file:
        print(f"Portfolio File: {args.portfolio_file}")
    print("=" * 60)

    _display_requirements(result, args)

    print("\n" + "=" * 60)
    print("END OF REPORT")

    # Restore stdout
    sys.stdout = old_stdout

    # Save to file
    with open(filename, 'w') as f:
        f.write(captured_output.getvalue())

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)