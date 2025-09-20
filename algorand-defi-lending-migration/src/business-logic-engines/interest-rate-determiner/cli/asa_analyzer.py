#!/usr/bin/env python3
"""ASA Analyzer CLI - Analyze ASA risk and volatility"""

import asyncio
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from algosdk.v2client import algod, indexer
from interest_rate_determiner.engines import ASARiskEngine

app = typer.Typer(name="asa-analyzer", help="ASA Risk and Volatility Analysis")
console = Console()

@app.command()
def analyze(
    asset_id: int = typer.Argument(..., help="ASA ID to analyze"),
    analysis_period: int = typer.Option(90, "--period", help="Analysis period in days"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json")
):
    """Analyze ASA risk metrics and volatility"""
    
    async def run_analysis():
        algod_client = algod.AlgodClient("", "https://mainnet-api.algonode.cloud")
        indexer_client = indexer.IndexerClient("", "https://mainnet-idx.algonode.cloud")
        engine = ASARiskEngine(algod_client, indexer_client, {})
        
        console.print(Panel.fit(f"🪙 ASA Risk Analysis for Asset {asset_id}", title="ASA Analysis"))
        
        try:
            risk_metrics = await engine.analyze_asa_risk(asset_id, analysis_period)
            
            if output_format == "json":
                result = {
                    'asset_id': asset_id,
                    'name': risk_metrics.name,
                    'risk_level': risk_metrics.risk_level.value,
                    'overall_risk_score': float(risk_metrics.overall_risk_score),
                    'volatility_score': float(risk_metrics.volatility_score),
                    'liquidity_score': float(risk_metrics.liquidity_score),
                    'governance_score': float(risk_metrics.governance_score),
                    'adoption_score': float(risk_metrics.adoption_score),
                    'technical_score': float(risk_metrics.technical_score),
                    'collateral_factor': float(risk_metrics.collateral_factor),
                    'interest_rate_premium': float(risk_metrics.interest_rate_premium),
                    'recommended_ltv': float(risk_metrics.recommended_ltv()),
                    'confidence_level': float(risk_metrics.confidence_level),
                    'risk_factors': risk_metrics.risk_factors,
                    'strengths': risk_metrics.strengths
                }
                console.print(json.dumps(result, indent=2))
            else:
                # Risk scores table
                table = Table(title=f"📈 Risk Analysis for {risk_metrics.name} (ID: {asset_id})")
                table.add_column("Component", style="cyan")
                table.add_column("Score", style="green")
                table.add_column("Weight", style="yellow")
                
                table.add_row("Overall Risk Score", f"{risk_metrics.overall_risk_score:.3f}", "100%")
                table.add_row("├─ Volatility", f"{risk_metrics.volatility_score:.3f}", "30%")
                table.add_row("├─ Liquidity", f"{1-risk_metrics.liquidity_score:.3f}", "25%")
                table.add_row("├─ Governance", f"{1-risk_metrics.governance_score:.3f}", "20%")
                table.add_row("├─ Adoption", f"{1-risk_metrics.adoption_score:.3f}", "15%")
                table.add_row("└─ Technical", f"{1-risk_metrics.technical_score:.3f}", "10%")
                table.add_row("", "", "")
                table.add_row("Risk Level", risk_metrics.risk_level.value.title(), "")
                table.add_row("Confidence", f"{risk_metrics.confidence_level:.3f}", "")
                
                console.print(table)
                
                # Lending parameters
                lending_table = Table(title="🏦 Lending Parameters")
                lending_table.add_column("Parameter", style="cyan")
                lending_table.add_column("Value", style="green")
                lending_table.add_column("Description", style="dim")
                
                lending_table.add_row("Collateral Factor", f"{risk_metrics.collateral_factor:.3f}", "Max loan-to-value ratio")
                lending_table.add_row("Recommended LTV", f"{risk_metrics.recommended_ltv():.1%}", "Suggested LTV ratio")
                lending_table.add_row("Rate Premium", f"+{risk_metrics.interest_rate_premium*100:.2f}%", "Additional interest rate")
                
                console.print(lending_table)
                
                # Risk factors and strengths
                if risk_metrics.risk_factors:
                    console.print(f"\n[red]⚠ Risk Factors:[/red] {', '.join(risk_metrics.risk_factors)}")
                if risk_metrics.strengths:
                    console.print(f"\n[green]✓ Strengths:[/green] {', '.join(risk_metrics.strengths)}")
                    
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            
    asyncio.run(run_analysis())

if __name__ == "__main__":
    app()