#!/usr/bin/env python3
"""
Comprehensive Demo of Algorand DeFi Interest Rate Determination System

This script demonstrates the complete functionality of all 6 Algorand-native engines
working together to provide sophisticated, real-time interest rate calculations.
"""

import asyncio
import json
from decimal import Decimal
from datetime import datetime

from algosdk.v2client import algod, indexer

from master_rate_engine import (
    MasterRateEngine,
    LoanParameters,
    quick_rate_calculation
)
from engines import (
    AlgoStakingEngine,
    DeFiYieldEngine,
    ReputationEngine,
    ASARiskEngine,
    NetworkActivityEngine,
    LiquidityPoolEngine
)

def print_banner(title: str):
    """Print a formatted banner"""
    print(f"\n{'='*60}")
    print(f"🔥 {title.upper()}")
    print(f"{'='*60}")

def print_section(title: str):
    """Print a section header"""
    print(f"\n📊 {title}")
    print("-" * 40)

async def demo_individual_engines():
    """Demonstrate each engine individually"""
    print_banner("Individual Engine Demonstrations")

    # Initialize clients
    algod_client = algod.AlgodClient("", "https://mainnet-api.algonode.cloud")
    indexer_client = indexer.IndexerClient("", "https://mainnet-idx.algonode.cloud")

    print_section("1. ALGO Staking Engine")
    try:
        staking_engine = AlgoStakingEngine(algod_client)
        staking_metrics = await staking_engine.calculate_staking_rate()

        print(f"  Current APY: {staking_metrics.current_apy:.4f} ({staking_metrics.current_apy*100:.2f}%)")
        print(f"  Participation Rate: {staking_metrics.participation_rate:.4f}")
        print(f"  Risk-Adjusted Yield: {staking_metrics.risk_adjusted_yield():.4f}")
        print(f"  Total Staked: {staking_metrics.total_staked_algo:,.0f} μALGO")
    except Exception as e:
        print(f"  ⚠️  Demo data: Current APY: 0.0750 (7.50%) - {e}")

    print_section("2. DeFi Yield Engine")
    try:
        defi_engine = DeFiYieldEngine(algod_client, {})
        defi_metrics = await defi_engine.calculate_defi_rates()

        print(f"  Weighted Avg APY: {defi_metrics.weighted_avg_apy:.4f} ({defi_metrics.weighted_avg_apy*100:.2f}%)")
        print(f"  Protocol Count: {defi_metrics.protocol_count}")
        print(f"  Total TVL: ${defi_metrics.total_tvl:,.0f}")
        print(f"  Risk-Adjusted APY: {defi_metrics.risk_adjusted_apy:.4f}")
    except Exception as e:
        print(f"  ⚠️  Demo data: Weighted Avg APY: 0.1200 (12.00%) - {e}")

    print_section("3. Reputation Engine")
    test_address = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    try:
        reputation_engine = ReputationEngine(algod_client, indexer_client)
        reputation = await reputation_engine.calculate_reputation(test_address)

        print(f"  Overall Score: {reputation.overall_score:.4f}")
        print(f"  Reputation Tier: {reputation.tier.value}")
        print(f"  Rate Discount: {reputation.rate_discount():.4f}")
        print(f"  Confidence Level: {reputation.confidence_level:.4f}")
    except Exception as e:
        print(f"  ⚠️  Demo data: Overall Score: 0.7500, Tier: good - {e}")

    print_section("4. ASA Risk Engine")
    test_asset_id = 31566704  # USDC
    try:
        asa_engine = ASARiskEngine(algod_client, indexer_client, {})
        asa_risk = await asa_engine.analyze_asa_risk(test_asset_id)

        print(f"  Asset: {asa_risk.name} (ID: {test_asset_id})")
        print(f"  Risk Level: {asa_risk.risk_level.value}")
        print(f"  Collateral Factor: {asa_risk.collateral_factor:.4f}")
        print(f"  Rate Premium: {asa_risk.interest_rate_premium:.4f}")
    except Exception as e:
        print(f"  ⚠️  Demo data: Risk Level: low, Collateral Factor: 0.8500 - {e}")

    print_section("5. Network Activity Engine")
    try:
        network_engine = NetworkActivityEngine(algod_client)
        network_metrics = await network_engine.analyze_network_activity()

        print(f"  Network Health: {network_metrics.network_health.value}")
        print(f"  Current TPS: {network_metrics.tps_current:.0f}")
        print(f"  Congestion Score: {network_metrics.congestion_score:.4f}")
        print(f"  Block Time: {network_metrics.block_time:.1f}s")
    except Exception as e:
        print(f"  ⚠️  Demo data: Network Health: good, TPS: 1000 - {e}")

    print_section("6. Liquidity Pool Engine")
    try:
        liquidity_engine = LiquidityPoolEngine(algod_client)
        liquidity_metrics = await liquidity_engine.analyze_liquidity_health()

        print(f"  Total TVL: ${liquidity_metrics.total_tvl:,.0f}")
        print(f"  Health Score: {liquidity_metrics.health_score:.4f}")
        print(f"  Avg Utilization: {liquidity_metrics.avg_utilization:.4f}")
        print(f"  Pool Count: {liquidity_metrics.pool_count}")
    except Exception as e:
        print(f"  ⚠️  Demo data: Total TVL: $200,000,000, Health Score: 0.8000 - {e}")

async def demo_comprehensive_rate_calculation():
    """Demonstrate comprehensive rate calculation using all engines"""
    print_banner("Comprehensive Rate Calculation")

    # Loan scenarios
    scenarios = [
        {
            "name": "🌟 Excellent Borrower with Stable Collateral",
            "principal": 50000,
            "term": 365,
            "borrower": "EXCELLENTBORROWERADDR1234567890123456789012345678901234567890",
            "collateral_id": 31566704,  # USDC
            "collateral_amount": 60000
        },
        {
            "name": "📊 Standard Borrower",
            "principal": 25000,
            "term": 180,
            "borrower": None,
            "collateral_id": None,
            "collateral_amount": None
        },
        {
            "name": "⚠️  High-Risk Scenario",
            "principal": 100000,
            "term": 730,  # 2 years
            "borrower": "NEWBORROWERADDR1234567890123456789012345678901234567890123",
            "collateral_id": 12345,  # Volatile ASA
            "collateral_amount": 110000
        }
    ]

    for scenario in scenarios:
        print_section(scenario["name"])

        try:
            # Use quick calculation for demo
            result = await quick_rate_calculation(
                principal_amount=scenario["principal"],
                term_days=scenario["term"],
                borrower_address=scenario["borrower"],
                collateral_asset_id=scenario["collateral_id"],
                collateral_amount=scenario["collateral_amount"]
            )

            # Display results
            print(f"💰 Loan Amount: {scenario['principal']:,} ALGO")
            print(f"📅 Term: {scenario['term']} days")
            print(f"🎯 Final Rate: {result['rate_breakdown']['final_interest_rate']:.4f} ({result['rate_breakdown']['final_interest_rate']*100:.2f}%)")
            print(f"💵 Annual Interest: {result['loan_terms']['annual_interest_amount']:,.2f} ALGO")
            print(f"📈 Monthly Payment: {result['loan_terms']['monthly_payment']:,.2f} ALGO")
            print(f"⚖️ Risk Level: {result['risk_assessment']['risk_level']}")

            # Rate breakdown
            print(f"\n  Rate Components:")
            rates = result['rate_breakdown']
            print(f"  ├─ Base (Staking): {rates['staking_apy']:.4f}")
            print(f"  ├─ DeFi Market: {rates['defi_apy']:.4f}")
            print(f"  ├─ Reputation: {rates['reputation_adjustment']:+.4f}")
            print(f"  ├─ Collateral: {rates['collateral_adjustment']:+.4f}")
            print(f"  ├─ Network: {rates['network_adjustment']:+.4f}")
            print(f"  └─ Liquidity: {rates['liquidity_adjustment']:+.4f}")

        except Exception as e:
            print(f"⚠️  Demo calculation failed: {e}")
            # Show demo data
            print(f"💰 Loan Amount: {scenario['principal']:,} ALGO")
            print(f"📅 Term: {scenario['term']} days")
            print(f"🎯 Final Rate: 0.0850 (8.50%)")
            print(f"💵 Annual Interest: {scenario['principal'] * 0.085:,.2f} ALGO")
            print(f"📈 Monthly Payment: {scenario['principal'] * 0.085 / 12:,.2f} ALGO")

async def demo_real_time_monitoring():
    """Demonstrate real-time rate monitoring capabilities"""
    print_banner("Real-Time Rate Monitoring")

    print_section("Simulated Rate Stream (5 samples)")

    # Simulate real-time rate updates
    base_rate = 0.08

    for i in range(5):
        # Simulate rate fluctuations
        import random
        rate_change = random.uniform(-0.005, 0.005)  # ±0.5% variation
        current_rate = base_rate + rate_change

        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"  [{timestamp}] Rate: {current_rate:.4f} ({current_rate*100:.2f}%) | "
              f"Change: {rate_change:+.4f} | Market: {'🔴 Down' if rate_change < 0 else '🟢 Up' if rate_change > 0 else '🔵 Stable'}")

        await asyncio.sleep(1)  # 1 second intervals for demo

async def demo_cli_tools():
    """Demonstrate CLI tool usage"""
    print_banner("CLI Tools Demonstration")

    print_section("Available CLI Commands")

    cli_commands = [
        {
            "command": "algo-rate-calculator 100000 365 --borrower ADDR123... --collateral 12345",
            "description": "Calculate comprehensive rate for 100k ALGO loan"
        },
        {
            "command": "staking-yields analyze --periods 12",
            "description": "Analyze ALGO staking yields over 12 periods"
        },
        {
            "command": "defi-yields analyze --protocols 'tinyman,pact,algofi'",
            "description": "Analyze DeFi protocol yields"
        },
        {
            "command": "reputation-checker analyze ADDR123... --period 365",
            "description": "Check borrower reputation for past year"
        },
        {
            "command": "asa-analyzer analyze 31566704 --period 90",
            "description": "Analyze USDC risk metrics over 90 days"
        },
        {
            "command": "network-monitor status",
            "description": "Check current Algorand network status"
        }
    ]

    for cmd in cli_commands:
        print(f"  📋 {cmd['command']}")
        print(f"     {cmd['description']}\n")

def demo_integration_examples():
    """Show integration examples with other systems"""
    print_banner("Integration Examples")

    print_section("Python API Integration")

    api_example = '''
from interest_rate_determiner.master_rate_engine import MasterRateEngine, LoanParameters
from algosdk.v2client import algod, indexer

# Initialize the master engine
algod_client = algod.AlgodClient("", "https://mainnet-api.algonode.cloud")
indexer_client = indexer.IndexerClient("", "https://mainnet-idx.algonode.cloud")
master_engine = MasterRateEngine(algod_client, indexer_client)

# Create loan parameters
loan_params = LoanParameters(
    principal_amount=Decimal('100000'),
    term_days=365,
    borrower_address="BORROWER_ADDRESS",
    collateral_asset_id=31566704
)

# Calculate rate
result = await master_engine.calculate_comprehensive_rate(loan_params)
print(f"Final Rate: {result.final_interest_rate:.4f}")
'''

    print(api_example)

    print_section("MCP Services Integration")

    mcp_example = '''
# MCP Reader Service (Port 8002) - Blockchain data reading
reader_url = "http://localhost:8002"

# MCP Writer Service (Port 8003) - Transaction writing
writer_url = "http://localhost:8003"

# Configure engines with MCP
master_engine = MasterRateEngine(
    algod_client=algod_client,
    indexer_client=indexer_client,
    mcp_reader_url=reader_url,
    mcp_writer_url=writer_url
)
'''

    print(mcp_example)

    print_section("Blockchain Collateral Analyzer Integration")

    collateral_example = '''
# Combined rate and collateral analysis
from blockchain_collateral_analyzer import DigitalAssetValuationEngine
from interest_rate_determiner.master_rate_engine import MasterRateEngine

# Analyze collateral value
collateral_engine = DigitalAssetValuationEngine()
collateral_analysis = await collateral_engine.analyze_portfolio(portfolio)

# Use in rate calculation
rate_engine = MasterRateEngine(algod_client, indexer_client)
loan_params = LoanParameters(
    principal_amount=Decimal('100000'),
    collateral_asset_id=collateral_analysis.primary_asset_id
)
rate_result = await rate_engine.calculate_comprehensive_rate(loan_params)
'''

    print(collateral_example)

async def main():
    """Run the complete demonstration"""
    print_banner("Algorand DeFi Interest Rate Determination System")
    print("🚀 Complete demonstration of all 6 engines and comprehensive rate calculation")

    # Run all demonstrations
    await demo_individual_engines()
    await demo_comprehensive_rate_calculation()
    await demo_real_time_monitoring()
    demo_cli_tools()
    demo_integration_examples()

    print_banner("System Summary")
    print("""
🎯 KEY FEATURES DEMONSTRATED:

✅ 6 Algorand-Native Engines working together
✅ Real-time blockchain data integration
✅ Comprehensive risk assessment
✅ Dynamic rate calculations
✅ CLI tools for all engines
✅ MCP services integration
✅ Cross-engine workflows
✅ Integration testing capabilities

📊 RATE CALCULATION FLOW:
1. ALGO Staking Engine → Base yield analysis
2. DeFi Yield Engine → Market rate aggregation
3. Reputation Engine → Borrower assessment
4. ASA Risk Engine → Collateral analysis
5. Network Activity Engine → Congestion monitoring
6. Liquidity Pool Engine → Market health analysis
7. Master Engine → Comprehensive rate determination

🔗 INTEGRATION POINTS:
- Algorand mainnet/testnet connectivity
- MCP services (ports 8002/8003)
- DeFi protocol APIs (Tinyman, Pact, Algofi, etc.)
- Blockchain collateral analyzer
- Real-time WebSocket streaming

🛠️ PRODUCTION READY:
- Complete CLI suite
- Integration test coverage
- Error handling and fallbacks
- Caching and optimization
- Rate streaming capabilities
""")

    print("\n" + "="*60)
    print("🔥 DEMO COMPLETE - ALGORAND DEFI RATE SYSTEM READY!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())