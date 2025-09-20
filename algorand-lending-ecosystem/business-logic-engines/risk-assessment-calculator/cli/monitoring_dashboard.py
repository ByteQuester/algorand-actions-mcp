#!/usr/bin/env python3
"""
Risk Monitoring Dashboard CLI
"""

import typer
from rich.console import Console

app = typer.Typer(name="risk-monitoring-dashboard", help="Risk Monitoring Dashboard CLI")
console = Console()

@app.command()
def start(port: int = typer.Option(8080, "--port", "-p", help="Dashboard port")):
    """Start risk monitoring dashboard."""
    console.print(f"[yellow]Starting dashboard on port {port}...[/yellow]")

def main():
    app()

if __name__ == "__main__":
    main()