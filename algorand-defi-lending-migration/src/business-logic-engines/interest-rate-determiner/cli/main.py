#!/usr/bin/env python3
"""
Main CLI for Interest Rate Determiner

Unified command-line interface for all interest rate determination functionality.
Provides access to all 6 engines through a single command-line tool.
"""

import asyncio
import json
import sys
from decimal import Decimal
from typing import Optional

import click
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .. import (
    MarketRateAnalysisEngine, RiskAssessmentEngine, CreditScoringEngine,
    RegulatoryComplianceEngine, DynamicPricingEngine, RateOptimizationEngine,
    get_available_engines, check_engine_availability
)

app = typer.Typer(
    name="rate-calculator",
    help="Comprehensive Interest Rate Determiner for Algorand DeFi Lending",
    add_completion=False
)
console = Console()


@app.command()
def status():
    """Check the status and availability of all engines."""
    rprint("[bold blue]Interest Rate Determiner - Engine Status[/bold blue]")
    rprint("")

    available_engines = get_available_engines()
    total_engines = 6

    if len(available_engines) == total_engines:
        rprint("[bold green]✓ All engines are available and ready![/bold green]")
    else:
        rprint(f"[yellow]⚠ {len(available_engines)}/{total_engines} engines available[/yellow]")

    rprint("")
    check_engine_availability()


@app.command()
def calculate(
    loan_amount: float = typer.Option(..., "--amount", "-a", help="Loan amount"),
    duration_days: int = typer.Option(..., "--duration", "-d", help="Loan duration in days"),
    borrower_id: str = typer.Option("default", "--borrower", "-b", help="Borrower ID"),
    jurisdiction: str = typer.Option("us_federal", "--jurisdiction", "-j", help="Regulatory jurisdiction"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json")
):
    """Calculate comprehensive interest rate using all available engines."""

    async def _calculate():
        try:
            rprint(f"[bold blue]Calculating interest rate for ${loan_amount:,.2f} over {duration_days} days[/bold blue]")
            rprint("")

            loan_decimal = Decimal(str(loan_amount))
            results = {}

            available_engines = get_available_engines()

            # Market Rate Analysis
            if 'market_rate_analysis' in available_engines:
                rprint("[cyan]Running market rate analysis...[/cyan]")
                market_engine = available_engines['market_rate_analysis']()
                market_analysis = await market_engine.analyze_market_rates()
                results['market_analysis'] = {
                    'base_rate': float(market_analysis.base_rate),
                    'market_sentiment': market_analysis.market_sentiment,
                    'volatility_score': market_analysis.volatility_score,
                    'confidence': market_analysis.confidence
                }
                rprint(f"  Base rate: {market_analysis.base_rate:.4%}")

            # Risk Assessment
            if 'risk_assessment' in available_engines:
                rprint("[cyan]Running risk assessment...[/cyan]")
                risk_engine = available_engines['risk_assessment']()
                # Create mock data for demonstration
                from ..risk_assessment.core.risk_engine import BorrowerProfile, MarketRiskFactors

                borrower_profile = BorrowerProfile(
                    borrower_id=borrower_id,
                    credit_score=720,
                    debt_to_income_ratio=0.3,
                    employment_status="employed"
                )
                market_factors = MarketRiskFactors(
                    asset_volatility=0.4,
                    liquidity_risk=0.3,
                    regulatory_risk=0.2
                )

                risk_assessment = await risk_engine.assess_risk(
                    borrower_profile, market_factors, loan_decimal, duration_days
                )
                results['risk_assessment'] = {
                    'risk_level': risk_assessment.overall_risk_level.value,
                    'risk_premium': float(risk_assessment.risk_premium),
                    'risk_score': risk_assessment.risk_score,
                    'confidence': risk_assessment.confidence
                }
                rprint(f"  Risk premium: {risk_assessment.risk_premium:.4%}")

            # Regulatory Compliance
            if 'regulatory_compliance' in available_engines:
                rprint("[cyan]Checking regulatory compliance...[/cyan]")
                compliance_engine = available_engines['regulatory_compliance']()
                from ..regulatory_compliance.core.compliance_engine import Jurisdiction

                # Calculate preliminary rate for compliance check
                base_rate = results.get('market_analysis', {}).get('base_rate', 0.05)
                risk_premium = results.get('risk_assessment', {}).get('risk_premium', 0.02)
                proposed_rate = Decimal(str(base_rate + risk_premium))

                jurisdiction_enum = getattr(Jurisdiction, jurisdiction.upper(), Jurisdiction.US_FEDERAL)
                compliance_check = await compliance_engine.verify_compliance(
                    proposed_rate, loan_decimal, duration_days, jurisdiction_enum
                )
                results['compliance'] = {
                    'is_compliant': compliance_check.is_compliant,
                    'applied_rate': float(compliance_check.applied_rate),
                    'max_allowed_rate': float(compliance_check.max_allowed_rate),
                    'violations': compliance_check.violations
                }
                rprint(f"  Compliance: {'✓' if compliance_check.is_compliant else '✗'}")

            # Calculate final rate
            final_rate = Decimal('0.05')  # Default fallback
            if results.get('compliance', {}).get('applied_rate'):
                final_rate = Decimal(str(results['compliance']['applied_rate']))
            elif results.get('market_analysis') and results.get('risk_assessment'):
                final_rate = Decimal(str(
                    results['market_analysis']['base_rate'] +
                    results['risk_assessment']['risk_premium']
                ))

            results['final_rate'] = {
                'annual_rate': float(final_rate),
                'monthly_rate': float(final_rate / 12),
                'daily_rate': float(final_rate / 365)
            }

            # Calculate payment details
            monthly_rate = final_rate / 12
            num_months = duration_days / 30.0
            if monthly_rate > 0:
                monthly_payment = loan_decimal * (monthly_rate * (1 + monthly_rate) ** num_months) / ((1 + monthly_rate) ** num_months - 1)
            else:
                monthly_payment = loan_decimal / Decimal(str(num_months))

            total_payment = monthly_payment * Decimal(str(num_months))
            total_interest = total_payment - loan_decimal

            results['payment_details'] = {
                'monthly_payment': float(monthly_payment),
                'total_payment': float(total_payment),
                'total_interest': float(total_interest)
            }

            rprint("")

            if output_format == "json":
                print(json.dumps(results, indent=2))
            else:
                # Display results in table format
                table = Table(title="Interest Rate Calculation Results")
                table.add_column("Component", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Final Annual Rate", f"{final_rate:.4%}")
                table.add_row("Monthly Payment", f"${monthly_payment:,.2f}")
                table.add_row("Total Interest", f"${total_interest:,.2f}")
                table.add_row("Total Payment", f"${total_payment:,.2f}")

                console.print(table)

                # Display component breakdown
                if results.get('market_analysis'):
                    ma = results['market_analysis']
                    rprint(f"\n[bold]Market Analysis:[/bold]")
                    rprint(f"  Base Rate: {ma['base_rate']:.4%}")
                    rprint(f"  Sentiment: {ma['market_sentiment']}")
                    rprint(f"  Confidence: {ma['confidence']:.2%}")

                if results.get('risk_assessment'):
                    ra = results['risk_assessment']
                    rprint(f"\n[bold]Risk Assessment:[/bold]")
                    rprint(f"  Risk Level: {ra['risk_level']}")
                    rprint(f"  Risk Premium: {ra['risk_premium']:.4%}")
                    rprint(f"  Risk Score: {ra['risk_score']:.1f}/100")

        except Exception as e:
            rprint(f"[bold red]Error calculating interest rate: {e}[/bold red]")
            raise typer.Exit(1)

    asyncio.run(_calculate())


@app.command()
def market_analysis(
    asset: str = typer.Option("ALGO", "--asset", "-a", help="Asset to analyze"),
    hours: int = typer.Option(24, "--hours", "-h", help="Analysis period in hours")
):
    """Run market rate analysis."""

    async def _analyze():
        available_engines = get_available_engines()
        if 'market_rate_analysis' not in available_engines:
            rprint("[bold red]Market Rate Analysis Engine not available[/bold red]")
            raise typer.Exit(1)

        engine = available_engines['market_rate_analysis']()
        analysis = await engine.analyze_market_rates(asset, hours)

        rprint(f"[bold blue]Market Analysis for {asset}[/bold blue]")
        rprint(f"Base Rate: {analysis.base_rate:.4%}")
        rprint(f"Market Sentiment: {analysis.market_sentiment}")
        rprint(f"Volatility Score: {analysis.volatility_score:.2f}")
        rprint(f"Liquidity Score: {analysis.liquidity_score:.2f}")
        rprint(f"Confidence: {analysis.confidence:.2%}")
        rprint(f"Recommendation: {analysis.recommendation}")

    asyncio.run(_analyze())


@app.command()
def risk_assessment(
    borrower_id: str = typer.Option(..., "--borrower", "-b", help="Borrower ID"),
    loan_amount: float = typer.Option(..., "--amount", "-a", help="Loan amount"),
    duration_days: int = typer.Option(..., "--duration", "-d", help="Loan duration in days")
):
    """Run risk assessment for a borrower."""

    async def _assess():
        available_engines = get_available_engines()
        if 'risk_assessment' not in available_engines:
            rprint("[bold red]Risk Assessment Engine not available[/bold red]")
            raise typer.Exit(1)

        engine = available_engines['risk_assessment']()

        # Create mock borrower profile and market factors
        from ..risk_assessment.core.risk_engine import BorrowerProfile, MarketRiskFactors

        borrower_profile = BorrowerProfile(
            borrower_id=borrower_id,
            credit_score=720,  # Mock data
            debt_to_income_ratio=0.3
        )
        market_factors = MarketRiskFactors(
            asset_volatility=0.4,
            liquidity_risk=0.3,
            regulatory_risk=0.2
        )

        assessment = await engine.assess_risk(
            borrower_profile, market_factors, Decimal(str(loan_amount)), duration_days
        )

        rprint(f"[bold blue]Risk Assessment for {borrower_id}[/bold blue]")
        rprint(f"Risk Level: {assessment.overall_risk_level.value}")
        rprint(f"Risk Premium: {assessment.risk_premium:.4%}")
        rprint(f"Risk Score: {assessment.risk_score:.1f}/100")
        rprint(f"Confidence: {assessment.confidence:.2%}")

        if assessment.risk_factors:
            rprint("\n[bold red]Risk Factors:[/bold red]")
            for factor in assessment.risk_factors:
                rprint(f"  • {factor}")

        if assessment.mitigation_recommendations:
            rprint("\n[bold green]Recommendations:[/bold green]")
            for rec in assessment.mitigation_recommendations:
                rprint(f"  • {rec}")

    asyncio.run(_assess())


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()