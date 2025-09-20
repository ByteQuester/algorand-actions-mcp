#!/usr/bin/env python3
"""
Holistic Loan Approver CLI - Master Loan Approval Interface

Command-line interface for processing loan applications through the
complete holistic decision orchestrator.
"""

import asyncio
import click
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..core.decision_orchestrator import (
    HolisticDecisionOrchestrator,
    LoanApplication,
    BorrowerProfile
)


@click.group()
@click.option('--config', '-c', help='Configuration file path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """Holistic Loan Approver - Master loan approval system for Algorand ecosystem"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--borrower', '-b', required=True, help='Borrower Algorand address')
@click.option('--amount', '-a', required=True, type=float, help='Loan amount in ALGO')
@click.option('--term', '-t', required=True, type=int, help='Loan term in days')
@click.option('--purpose', '-p', default='general', help='Loan purpose')
@click.option('--collateral', '-col', help='Collateral specification (JSON file)', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file for decision', type=click.Path())
@click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'text']), default='text', help='Output format')
@click.pass_context
def approve(ctx, borrower, amount, term, purpose, collateral, output, format):
    """Process a loan application through holistic approval system"""

    async def process_application():
        # Initialize orchestrator
        orchestrator = HolisticDecisionOrchestrator(ctx.obj.get('config'))

        # Load collateral data if provided
        collateral_assets = []
        if collateral:
            with open(collateral, 'r') as f:
                collateral_data = json.load(f)
                collateral_assets = collateral_data.get('assets', [])

        # Create loan application
        application = LoanApplication(
            application_id=f"APP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            borrower_address=borrower,
            loan_amount=amount,
            requested_term=term,
            collateral_assets=collateral_assets,
            purpose=purpose,
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.2},
            network_health={'health_score': 0.9}
        )

        # Process application
        decision = await orchestrator.process_loan_application(application)

        # Format output
        if format == 'json':
            output_data = _decision_to_dict(decision)
            result = json.dumps(output_data, indent=2, default=str)
        elif format == 'yaml':
            output_data = _decision_to_dict(decision)
            result = yaml.dump(output_data, default_flow_style=False)
        else:
            result = _format_decision_text(decision)

        # Save or display result
        if output:
            with open(output, 'w') as f:
                f.write(result)
            click.echo(f"Decision saved to {output}")
        else:
            click.echo(result)

    asyncio.run(process_application())


@cli.command()
@click.option('--borrower', '-b', required=True, help='Borrower Algorand address')
@click.option('--output', '-o', help='Output file for profile', type=click.Path())
@click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'text']), default='text', help='Output format')
@click.pass_context
def profile(ctx, borrower, output, format):
    """Generate comprehensive borrower profile"""

    async def generate_profile():
        orchestrator = HolisticDecisionOrchestrator(ctx.obj.get('config'))

        # Build borrower profile
        profile = await orchestrator._build_borrower_profile(borrower)

        # Format output
        if format == 'json':
            output_data = _profile_to_dict(profile)
            result = json.dumps(output_data, indent=2, default=str)
        elif format == 'yaml':
            output_data = _profile_to_dict(profile)
            result = yaml.dump(output_data, default_flow_style=False)
        else:
            result = _format_profile_text(profile)

        # Save or display result
        if output:
            with open(output, 'w') as f:
                f.write(result)
            click.echo(f"Profile saved to {output}")
        else:
            click.echo(result)

    asyncio.run(generate_profile())


@cli.command()
@click.option('--borrower', '-b', required=True, help='Borrower Algorand address')
@click.option('--amount', '-a', required=True, type=float, help='Loan amount in ALGO')
@click.option('--output', '-o', help='Output file for alternatives', type=click.Path())
@click.pass_context
def alternatives(ctx, borrower, amount, output):
    """Generate alternative loan terms for rejected application"""

    async def generate_alternatives():
        orchestrator = HolisticDecisionOrchestrator(ctx.obj.get('config'))

        # Create mock application for alternatives
        application = LoanApplication(
            application_id=f"ALT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            borrower_address=borrower,
            loan_amount=amount,
            requested_term=365,
            collateral_assets=[],
            purpose="general",
            timestamp=datetime.now(),
            market_conditions={'volatility': 0.2},
            network_health={'health_score': 0.9}
        )

        # Build profile and generate alternatives
        profile = await orchestrator._build_borrower_profile(borrower)
        holistic_scores = await orchestrator.scorer.calculate_holistic_scores(profile, application)

        alternatives = await orchestrator.alternative_proposer.propose_alternatives(
            holistic_scores, application, profile
        )

        # Format and display
        result = _format_alternatives_text(alternatives)

        if output:
            with open(output, 'w') as f:
                f.write(json.dumps(alternatives, indent=2, default=str))
            click.echo(f"Alternatives saved to {output}")
        else:
            click.echo(result)

    asyncio.run(generate_alternatives())


@cli.command()
@click.option('--days', '-d', default=30, help='Number of days to look ahead')
@click.pass_context
def monitor(ctx, days):
    """Show monitoring schedule for active loans"""
    click.echo(f"Monitoring schedule for next {days} days:")
    click.echo("(This would show real monitoring data in production)")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show system statistics and performance metrics"""
    click.echo("Holistic Decision System Statistics:")
    click.echo("===================================")
    click.echo("Total applications processed: 0")
    click.echo("Approval rate: 0.0%")
    click.echo("Average processing time: 0.0s")
    click.echo("Engine availability: 100%")


def _decision_to_dict(decision) -> Dict[str, Any]:
    """Convert decision object to dictionary"""
    return {
        'application_id': decision.application_id,
        'decision': decision.decision.value,
        'confidence': decision.confidence.value,
        'overall_score': decision.overall_score,
        'engine_scores': {
            'ecosystem': decision.ecosystem_score,
            'defi': decision.defi_score,
            'collateral': decision.collateral_score,
            'governance': decision.governance_score,
            'risk': decision.risk_score
        },
        'loan_terms': {
            'approved_amount': decision.approved_amount,
            'interest_rate': decision.interest_rate,
            'loan_term': decision.loan_term,
            'ltv_ratio': decision.ltv_ratio
        },
        'conditions': decision.conditions,
        'monitoring': {
            'frequency': decision.monitoring_frequency,
            'parameters': decision.monitoring_parameters
        },
        'alternatives': decision.alternatives,
        'rationale': {
            'primary_factors': decision.primary_factors,
            'risk_factors': decision.risk_factors,
            'positive_factors': decision.positive_factors
        },
        'metadata': {
            'decision_timestamp': decision.decision_timestamp,
            'expires_at': decision.expires_at,
            'processing_time': decision.processing_time
        }
    }


def _profile_to_dict(profile) -> Dict[str, Any]:
    """Convert profile object to dictionary"""
    return {
        'address': profile.address,
        'scores': {
            'ecosystem': {'score': profile.ecosystem_score, 'confidence': profile.ecosystem_confidence},
            'defi': {'score': profile.defi_score, 'confidence': profile.defi_confidence},
            'collateral': {'score': profile.collateral_score, 'confidence': profile.collateral_confidence},
            'governance': {'score': profile.governance_score, 'confidence': profile.governance_confidence},
            'risk': {'score': profile.risk_score, 'confidence': profile.risk_confidence}
        },
        'data_completeness': profile.data_completeness,
        'timestamp': profile.timestamp
    }


def _format_decision_text(decision) -> str:
    """Format decision as human-readable text"""
    lines = []
    lines.append("=" * 60)
    lines.append("ALGORAND HOLISTIC LOAN DECISION")
    lines.append("=" * 60)
    lines.append(f"Application ID: {decision.application_id}")
    lines.append(f"Decision: {decision.decision.value.upper()}")
    lines.append(f"Confidence: {decision.confidence.value.upper()}")
    lines.append(f"Overall Score: {decision.overall_score:.3f}")
    lines.append("")

    lines.append("Engine Scores:")
    lines.append(f"  Ecosystem Analysis:     {decision.ecosystem_score:.3f}")
    lines.append(f"  DeFi Behavior:          {decision.defi_score:.3f}")
    lines.append(f"  Collateral Intelligence: {decision.collateral_score:.3f}")
    lines.append(f"  Governance Reputation:   {decision.governance_score:.3f}")
    lines.append(f"  Risk Assessment:         {decision.risk_score:.3f}")
    lines.append("")

    if decision.approved_amount:
        lines.append("Loan Terms:")
        lines.append(f"  Approved Amount:  {decision.approved_amount:,.0f} ALGO")
        lines.append(f"  Interest Rate:    {decision.interest_rate*100:.2f}%")
        lines.append(f"  Loan Term:        {decision.loan_term} days")
        lines.append(f"  LTV Ratio:        {decision.ltv_ratio:.2f}")
        lines.append("")

    if decision.conditions:
        lines.append("Loan Conditions:")
        for i, condition in enumerate(decision.conditions, 1):
            lines.append(f"  {i}. {condition}")
        lines.append("")

    lines.append("Decision Rationale:")
    lines.append("Primary Factors:")
    for factor in decision.primary_factors:
        lines.append(f"  • {factor}")

    if decision.risk_factors:
        lines.append("Risk Factors:")
        for factor in decision.risk_factors:
            lines.append(f"  • {factor}")

    if decision.positive_factors:
        lines.append("Positive Factors:")
        for factor in decision.positive_factors:
            lines.append(f"  • {factor}")

    lines.append("")
    lines.append(f"Processing Time: {decision.processing_time:.2f} seconds")
    lines.append(f"Decision Expires: {decision.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(lines)


def _format_profile_text(profile) -> str:
    """Format profile as human-readable text"""
    lines = []
    lines.append("=" * 60)
    lines.append("ALGORAND BORROWER PROFILE")
    lines.append("=" * 60)
    lines.append(f"Address: {profile.address}")
    lines.append(f"Data Completeness: {profile.data_completeness:.2f}")
    lines.append(f"Profile Generated: {profile.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("Engine Scores:")
    lines.append(f"  Ecosystem Analysis:      {profile.ecosystem_score:.3f} (confidence: {profile.ecosystem_confidence:.2f})")
    lines.append(f"  DeFi Behavior:           {profile.defi_score:.3f} (confidence: {profile.defi_confidence:.2f})")
    lines.append(f"  Collateral Intelligence: {profile.collateral_score:.3f} (confidence: {profile.collateral_confidence:.2f})")
    lines.append(f"  Governance Reputation:   {profile.governance_score:.3f} (confidence: {profile.governance_confidence:.2f})")
    lines.append(f"  Risk Assessment:         {profile.risk_score:.3f} (confidence: {profile.risk_confidence:.2f})")

    return "\n".join(lines)


def _format_alternatives_text(alternatives) -> str:
    """Format alternatives as human-readable text"""
    if not alternatives:
        return "No alternatives available."

    lines = []
    lines.append("=" * 60)
    lines.append("ALTERNATIVE LOAN OPTIONS")
    lines.append("=" * 60)

    for i, alt in enumerate(alternatives, 1):
        lines.append(f"{i}. {alt['title']}")
        lines.append(f"   {alt['description']}")
        lines.append(f"   Timeline: {alt['timeline']}")
        lines.append(f"   Improvement Probability: {alt['probability_improvement']:.1%}")
        lines.append("")

    return "\n".join(lines)


if __name__ == '__main__':
    cli()