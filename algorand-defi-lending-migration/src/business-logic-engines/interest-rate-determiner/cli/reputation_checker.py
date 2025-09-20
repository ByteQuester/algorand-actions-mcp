#!/usr/bin/env python3
"""Reputation Checker CLI - Analyze on-chain reputation for borrowers"""

import asyncio
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from algosdk.v2client import algod, indexer
from interest_rate_determiner.engines import ReputationEngine

app = typer.Typer(name="reputation-checker", help="On-chain Reputation Analysis")
console = Console()

@app.command()
def analyze(
    address: str = typer.Argument(..., help="Algorand address to analyze"),
    analysis_period: int = typer.Option(365, "--period", help="Analysis period in days"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json")
):
    """Analyze on-chain reputation for an Algorand address"""
    
    async def run_analysis():
        algod_client = algod.AlgodClient("", "https://mainnet-api.algonode.cloud")
        indexer_client = indexer.IndexerClient("", "https://mainnet-idx.algonode.cloud")
        engine = ReputationEngine(algod_client, indexer_client)
        
        console.print(Panel.fit(f"👤 Reputation Analysis for {address[:10]}...", title="Reputation Check"))
        
        try:
            reputation = await engine.calculate_reputation(address, analysis_period)
            
            if output_format == "json":
                result = {
                    'address': address,
                    'overall_score': float(reputation.overall_score),
                    'tier': reputation.tier.value,
                    'activity_score': float(reputation.activity_score),
                    'reliability_score': float(reputation.reliability_score),
                    'sophistication_score': float(reputation.sophistication_score),
                    'governance_score': float(reputation.governance_score),
                    'defi_score': float(reputation.defi_score),
                    'confidence_level': float(reputation.confidence_level),
                    'rate_discount': float(reputation.rate_discount()),
                    'rate_premium': float(reputation.rate_premium()),
                    'strengths': reputation.strengths,
                    'risk_flags': reputation.risk_flags
                }
                console.print(json.dumps(result, indent=2))
            else:
                # Score table
                table = Table(title="🏆 Reputation Scores")
                table.add_column("Component", style="cyan")
                table.add_column("Score", style="green")
                table.add_column("Weight", style="yellow")
                
                table.add_row("Overall Score", f"{reputation.overall_score:.3f}", "100%")
                table.add_row("├─ Activity", f"{reputation.activity_score:.3f}", "25%")
                table.add_row("├─ Reliability", f"{reputation.reliability_score:.3f}", "30%")
                table.add_row("├─ Sophistication", f"{reputation.sophistication_score:.3f}", "20%")
                table.add_row("├─ Governance", f"{reputation.governance_score:.3f}", "15%")
                table.add_row("└─ DeFi Experience", f"{reputation.defi_score:.3f}", "10%")
                table.add_row("", "", "")
                table.add_row("Reputation Tier", reputation.tier.value.title(), "")
                table.add_row("Confidence Level", f"{reputation.confidence_level:.3f}", "")
                
                console.print(table)
                
                # Rate impact
                discount = reputation.rate_discount()
                premium = reputation.rate_premium()
                net_impact = discount - premium
                
                impact_table = Table(title="💰 Rate Impact")
                impact_table.add_column("Type", style="cyan")
                impact_table.add_column("Value", style="green")
                
                if discount > 0:
                    impact_table.add_row("Rate Discount", f"-{discount*100:.2f}%")
                if premium > 0:
                    impact_table.add_row("Rate Premium", f"+{premium*100:.2f}%")
                impact_table.add_row("Net Impact", f"{net_impact*100:+.2f}%")
                
                console.print(impact_table)
                
                # Strengths and flags
                if reputation.strengths:
                    console.print(f"\n[green]✓ Strengths:[/green] {', '.join(reputation.strengths)}")
                if reputation.risk_flags:
                    console.print(f"\n[red]⚠ Risk Flags:[/red] {', '.join(reputation.risk_flags)}")
                    
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            
    asyncio.run(run_analysis())

if __name__ == "__main__":
    app()