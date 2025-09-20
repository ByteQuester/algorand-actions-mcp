#!/usr/bin/env python3
"""Network Monitor CLI - Monitor Algorand network activity and health"""

import asyncio
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from datetime import datetime

from algosdk.v2client import algod
from interest_rate_determiner.engines import NetworkActivityEngine

app = typer.Typer(name="network-monitor", help="Algorand Network Activity Monitor")
console = Console()

@app.command()
def status(
    algod_url: str = typer.Option("https://mainnet-api.algonode.cloud", "--algod-url", help="Algorand node URL"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format: table, json")
):
    """Check current network status and health"""
    
    async def check_status():
        algod_client = algod.AlgodClient("", algod_url)
        engine = NetworkActivityEngine(algod_client)
        
        console.print(Panel.fit("🌐 Algorand Network Status", title="Network Monitor"))
        
        try:
            metrics = await engine.analyze_network_activity()
            adjustments = await engine.get_rate_adjustments()
            
            if output_format == "json":
                result = {
                    'tps_current': float(metrics.tps_current),
                    'tps_average': float(metrics.tps_average),
                    'block_time': float(metrics.block_time),
                    'pending_transactions': metrics.pending_transactions,
                    'network_health': metrics.network_health.value,
                    'congestion_score': float(metrics.congestion_score),
                    'fee_multiplier': float(metrics.fee_multiplier),
                    'rate_adjustments': {
                        'congestion_adjustment': float(adjustments['congestion_adjustment']),
                        'network_health_bonus': float(adjustments.get('network_health_bonus', 0))
                    }
                }
                console.print(json.dumps(result, indent=2))
            else:
                table = Table(title="📊 Network Metrics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                table.add_column("Status", style="yellow")
                
                # TPS status
                tps_status = "High" if metrics.tps_current > metrics.tps_average * 1.2 else "Normal"
                table.add_row("Current TPS", f"{metrics.tps_current:.0f}", tps_status)
                table.add_row("Average TPS", f"{metrics.tps_average:.0f}", "Baseline")
                
                # Block time status
                block_status = "Fast" if metrics.block_time < 4.0 else "Normal"
                table.add_row("Block Time", f"{metrics.block_time:.1f}s", block_status)
                
                # Queue status
                queue_status = "High" if metrics.pending_transactions > 1000 else "Normal"
                table.add_row("Pending Txns", f"{metrics.pending_transactions:,}", queue_status)
                
                # Overall health
                table.add_row("Network Health", metrics.network_health.value.title(), "")
                table.add_row("Congestion Score", f"{metrics.congestion_score:.3f}", "0=none, 1=max")
                table.add_row("Fee Multiplier", f"{metrics.fee_multiplier:.2f}x", "Base fee scaling")
                
                console.print(table)
                
                # Rate impact
                impact_table = Table(title="💰 Rate Impact")
                impact_table.add_column("Adjustment", style="cyan")
                impact_table.add_column("Value", style="green")
                impact_table.add_column("Reason", style="dim")
                
                congestion_adj = adjustments['congestion_adjustment']
                health_bonus = adjustments.get('network_health_bonus', 0)
                
                if congestion_adj > 0:
                    impact_table.add_row("Congestion Penalty", f"+{congestion_adj*100:.2f}%", "Network congestion")
                if health_bonus > 0:
                    impact_table.add_row("Health Bonus", f"-{health_bonus*100:.2f}%", "Excellent network health")
                    
                net_impact = congestion_adj - health_bonus
                impact_table.add_row("Net Impact", f"{net_impact*100:+.2f}%", "Total rate adjustment")
                
                console.print(impact_table)
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            
    asyncio.run(check_status())

@app.command()
def monitor(
    duration: int = typer.Option(60, "--duration", "-d", help="Monitor duration in seconds"),
    interval: int = typer.Option(5, "--interval", "-i", help="Update interval in seconds"),
    algod_url: str = typer.Option("https://mainnet-api.algonode.cloud", "--algod-url", help="Algorand node URL")
):
    """Monitor network activity in real-time"""
    
    async def run_monitor():
        algod_client = algod.AlgodClient("", algod_url)
        engine = NetworkActivityEngine(algod_client)
        
        def create_table():
            table = Table(title=f"📊 Live Network Monitor ({datetime.now().strftime('%H:%M:%S')})")
            table.add_column("Metric", style="cyan")
            table.add_column("Current", style="green")
            table.add_column("Trend", style="yellow")
            table.add_column("Impact", style="red")
            return table
            
        history = []
        
        with Live(create_table(), refresh_per_second=1) as live:
            for _ in range(duration // interval):
                try:
                    metrics = await engine.analyze_network_activity()
                    adjustments = await engine.get_rate_adjustments()
                    
                    # Store history
                    history.append({
                        'timestamp': datetime.now(),
                        'tps': float(metrics.tps_current),
                        'congestion': float(metrics.congestion_score),
                        'health': metrics.network_health.value
                    })
                    
                    # Create updated table
                    table = create_table()
                    
                    # Calculate trends
                    tps_trend = "→" if len(history) < 2 else ("↑" if history[-1]['tps'] > history[-2]['tps'] else "↓")
                    congestion_trend = "→" if len(history) < 2 else ("↑" if history[-1]['congestion'] > history[-2]['congestion'] else "↓")
                    
                    # Add rows
                    table.add_row("TPS", f"{metrics.tps_current:.0f}", tps_trend, "")
                    table.add_row("Block Time", f"{metrics.block_time:.1f}s", "", "")
                    table.add_row("Pending Txns", f"{metrics.pending_transactions:,}", "", "")
                    table.add_row("Health", metrics.network_health.value.title(), "", "")
                    table.add_row("Congestion", f"{metrics.congestion_score:.3f}", congestion_trend, f"{adjustments['congestion_adjustment']*100:+.2f}%")
                    
                    live.update(table)
                    
                    await asyncio.sleep(interval)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    console.print(f"[red]Monitor error: {e}[/red]")
                    await asyncio.sleep(interval)
                    
        # Show summary
        if history:
            console.print(f"\n[bold]Monitoring Summary ({len(history)} samples):[/bold]")
            tps_values = [h['tps'] for h in history]
            congestion_values = [h['congestion'] for h in history]
            
            console.print(f"TPS Range: {min(tps_values):.0f} - {max(tps_values):.0f} (avg: {sum(tps_values)/len(tps_values):.0f})")
            console.print(f"Congestion Range: {min(congestion_values):.3f} - {max(congestion_values):.3f}")
            
    asyncio.run(run_monitor())

if __name__ == "__main__":
    app()