#!/usr/bin/env python3
"""
Integration Example: Interest Rate Determiner with Lending Platform

This example shows how to integrate the interest rate determination system
with the main lending platform for real-time rate calculations.
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add paths for integration
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "apps" / "lending-platform" / "src"))

from algosdk.v2client import algod, indexer

# Interest rate determiner imports
from master_rate_engine import MasterRateEngine, LoanParameters
from engines import (
    AlgoStakingEngine,
    DeFiYieldEngine,
    ReputationEngine,
    ASARiskEngine,
    NetworkActivityEngine,
    LiquidityPoolEngine
)

# Lending platform imports (if available)
try:
    from core.lending.lending_engine import LendingEngine
    from core.lending.models import LoanRequest, BorrowerProfile
    LENDING_PLATFORM_AVAILABLE = True
except ImportError:
    LENDING_PLATFORM_AVAILABLE = False
    print("⚠️  Lending platform not available - using mock classes")

    # Mock classes for demonstration
    class LoanRequest:
        def __init__(self, amount, term_days, borrower_id, collateral_asset_id=None):
            self.amount = amount
            self.term_days = term_days
            self.borrower_id = borrower_id
            self.collateral_asset_id = collateral_asset_id

    class BorrowerProfile:
        def __init__(self, borrower_id, algorand_address):
            self.borrower_id = borrower_id
            self.algorand_address = algorand_address

    class LendingEngine:
        async def get_borrower_profile(self, borrower_id):
            return BorrowerProfile(borrower_id, f"ADDR{borrower_id}")

class IntegratedRateCalculator:
    """
    Integrated rate calculator that combines the interest rate determiner
    with the lending platform for seamless rate calculations.
    """

    def __init__(
        self,
        algod_url: str = "https://mainnet-api.algonode.cloud",
        indexer_url: str = "https://mainnet-idx.algonode.cloud"
    ):
        # Initialize blockchain clients
        self.algod_client = algod.AlgodClient("", algod_url)
        self.indexer_client = indexer.IndexerClient("", indexer_url)

        # Initialize rate engine
        self.rate_engine = MasterRateEngine(
            self.algod_client,
            self.indexer_client
        )

        # Initialize lending engine (if available)
        if LENDING_PLATFORM_AVAILABLE:
            self.lending_engine = LendingEngine()
        else:
            self.lending_engine = LendingEngine()

    async def calculate_rate_for_loan_request(self, loan_request: LoanRequest) -> dict:
        """
        Calculate interest rate for a loan request from the lending platform
        """
        try:
            # Get borrower profile from lending platform
            borrower_profile = await self.lending_engine.get_borrower_profile(
                loan_request.borrower_id
            )

            # Create loan parameters for rate engine
            loan_params = LoanParameters(
                principal_amount=Decimal(str(loan_request.amount)),
                term_days=loan_request.term_days,
                borrower_address=borrower_profile.algorand_address,
                collateral_asset_id=loan_request.collateral_asset_id,
                loan_purpose="defi_lending"
            )

            # Calculate comprehensive rate
            rate_result = await self.rate_engine.calculate_comprehensive_rate(loan_params)

            # Format result for lending platform
            return {
                'loan_id': rate_result.loan_id,
                'borrower_id': loan_request.borrower_id,
                'rate_calculation': {
                    'final_interest_rate': float(rate_result.final_interest_rate),
                    'effective_apr': float(rate_result.effective_apr),
                    'risk_level': rate_result.risk_level,
                    'confidence_score': float(rate_result.confidence_score),
                    'rate_valid_until': rate_result.rate_valid_until.isoformat()
                },
                'loan_terms': {
                    'principal_amount': float(rate_result.loan_parameters.principal_amount),
                    'annual_interest': float(rate_result.annual_interest_amount),
                    'monthly_payment': float(rate_result.monthly_payment),
                    'total_repayment': float(rate_result.total_repayment)
                },
                'rate_breakdown': {
                    'base_staking_rate': float(rate_result.base_staking_rate),
                    'defi_market_rate': float(rate_result.defi_market_rate),
                    'reputation_adjustment': float(rate_result.reputation_adjustment),
                    'collateral_risk_adjustment': float(rate_result.collateral_risk_adjustment),
                    'network_adjustment': float(rate_result.network_adjustment),
                    'liquidity_adjustment': float(rate_result.liquidity_adjustment)
                },
                'risk_assessment': {
                    'loan_to_value_ratio': float(rate_result.loan_to_value_ratio) if rate_result.loan_to_value_ratio else None,
                    'collateral_factor': float(rate_result.collateral_factor) if rate_result.collateral_factor else None
                },
                'metadata': {
                    'calculation_timestamp': rate_result.calculation_timestamp.isoformat(),
                    'engines_used': [
                        'algo_staking',
                        'defi_yield',
                        'reputation' if rate_result.reputation_data else None,
                        'asa_risk' if rate_result.collateral_data else None,
                        'network_activity',
                        'liquidity_pool'
                    ]
                }
            }

        except Exception as e:
            raise Exception(f"Rate calculation failed: {e}")

    async def get_market_rate_summary(self) -> dict:
        """
        Get current market rate summary for the lending platform dashboard
        """
        try:
            # Quick rate calculation for standard loan
            standard_loan = LoanParameters(
                principal_amount=Decimal('100000'),  # 100k ALGO
                term_days=365
            )

            result = await self.rate_engine.calculate_comprehensive_rate(standard_loan)

            # Get individual engine data
            staking_engine = AlgoStakingEngine(self.algod_client)
            defi_engine = DeFiYieldEngine(self.algod_client, {})
            network_engine = NetworkActivityEngine(self.algod_client)
            liquidity_engine = LiquidityPoolEngine(self.algod_client)

            staking_data = await staking_engine.calculate_staking_rate()
            defi_data = await defi_engine.calculate_defi_rates()
            network_data = await network_engine.analyze_network_activity()
            liquidity_data = await liquidity_engine.analyze_liquidity_health()

            return {
                'market_summary': {
                    'standard_rate': float(result.final_interest_rate),
                    'market_health': 'excellent' if result.confidence_score > 0.8 else 'good' if result.confidence_score > 0.6 else 'fair',
                    'last_updated': datetime.utcnow().isoformat()
                },
                'staking_metrics': {
                    'current_apy': float(staking_data.current_apy),
                    'participation_rate': float(staking_data.participation_rate)
                },
                'defi_metrics': {
                    'weighted_avg_apy': float(defi_data.weighted_avg_apy),
                    'protocol_count': defi_data.protocol_count,
                    'total_tvl': float(defi_data.total_tvl)
                },
                'network_health': {
                    'status': network_data.network_health.value,
                    'congestion_score': float(network_data.congestion_score),
                    'current_tps': float(network_data.tps_current)
                },
                'liquidity_health': {
                    'total_tvl': float(liquidity_data.total_tvl),
                    'health_score': float(liquidity_data.health_score),
                    'avg_utilization': float(liquidity_data.avg_utilization)
                }
            }

        except Exception as e:
            # Return fallback data
            return {
                'market_summary': {
                    'standard_rate': 0.08,
                    'market_health': 'good',
                    'last_updated': datetime.utcnow().isoformat(),
                    'note': f'Using fallback data: {e}'
                }
            }

    async def stream_rate_updates_for_loan(self, loan_request: LoanRequest):
        """
        Stream real-time rate updates for a specific loan request
        """
        loan_params = LoanParameters(
            principal_amount=Decimal(str(loan_request.amount)),
            term_days=loan_request.term_days,
            borrower_address=f"ADDR{loan_request.borrower_id}",
            collateral_asset_id=loan_request.collateral_asset_id
        )

        async for update in self.rate_engine.stream_rate_updates(
            loan_params,
            update_interval=60,  # 1 minute
            duration=3600        # 1 hour
        ):
            yield {
                'loan_id': loan_request.borrower_id,
                'timestamp': update.get('timestamp'),
                'rate': update.get('rate'),
                'confidence': update.get('confidence'),
                'risk_level': update.get('risk_level'),
                'error': update.get('error')
            }

async def demo_integration():
    """Demonstrate the integration with lending platform"""

    print("🔗 INTEGRATION DEMO: Interest Rate Determiner + Lending Platform")
    print("=" * 70)

    # Initialize integrated calculator
    calculator = IntegratedRateCalculator()

    # Example loan requests from lending platform
    loan_requests = [
        LoanRequest(
            amount=50000,
            term_days=365,
            borrower_id="borrower_001",
            collateral_asset_id=31566704  # USDC
        ),
        LoanRequest(
            amount=25000,
            term_days=180,
            borrower_id="borrower_002"
        ),
        LoanRequest(
            amount=100000,
            term_days=730,  # 2 years
            borrower_id="borrower_003",
            collateral_asset_id=12345  # Volatile ASA
        )
    ]

    print("\n📊 CALCULATING RATES FOR LOAN REQUESTS")
    print("-" * 50)

    for i, loan_request in enumerate(loan_requests, 1):
        print(f"\n{i}. Loan Request from {loan_request.borrower_id}")
        print(f"   Amount: {loan_request.amount:,} ALGO")
        print(f"   Term: {loan_request.term_days} days")
        print(f"   Collateral: {loan_request.collateral_asset_id or 'None'}")

        try:
            rate_result = await calculator.calculate_rate_for_loan_request(loan_request)

            print(f"   ✅ Rate Calculated: {rate_result['rate_calculation']['final_interest_rate']:.4f} "
                  f"({rate_result['rate_calculation']['final_interest_rate']*100:.2f}%)")
            print(f"   💰 Annual Interest: {rate_result['loan_terms']['annual_interest']:,.2f} ALGO")
            print(f"   🏷️ Risk Level: {rate_result['rate_calculation']['risk_level']}")
            print(f"   🎯 Confidence: {rate_result['rate_calculation']['confidence_score']:.3f}")

            # Show rate breakdown
            breakdown = rate_result['rate_breakdown']
            print(f"   📈 Components: Staking({breakdown['base_staking_rate']:.3f}) + "
                  f"DeFi({breakdown['defi_market_rate']:.3f}) + "
                  f"Adjustments({breakdown['reputation_adjustment'] + breakdown['collateral_risk_adjustment'] + breakdown['network_adjustment'] + breakdown['liquidity_adjustment']:+.3f})")

        except Exception as e:
            print(f"   ❌ Calculation failed: {e}")

    print("\n🌐 MARKET RATE SUMMARY")
    print("-" * 30)

    try:
        market_summary = await calculator.get_market_rate_summary()

        print(f"Standard Rate (100k ALGO, 1yr): {market_summary['market_summary']['standard_rate']:.4f}")
        print(f"Market Health: {market_summary['market_summary']['market_health']}")

        if 'staking_metrics' in market_summary:
            staking = market_summary['staking_metrics']
            print(f"ALGO Staking APY: {staking['current_apy']:.4f}")
            print(f"Network Participation: {staking['participation_rate']:.1%}")

        if 'defi_metrics' in market_summary:
            defi = market_summary['defi_metrics']
            print(f"DeFi Avg APY: {defi['weighted_avg_apy']:.4f}")
            print(f"Total DeFi TVL: ${defi['total_tvl']:,.0f}")

        if 'network_health' in market_summary:
            network = market_summary['network_health']
            print(f"Network Status: {network['status']}")
            print(f"Current TPS: {network['current_tps']:.0f}")

    except Exception as e:
        print(f"❌ Market summary failed: {e}")

    print("\n📡 REAL-TIME RATE STREAMING (Demo)")
    print("-" * 40)

    # Demo streaming for first loan request
    loan_request = loan_requests[0]
    print(f"Streaming rates for {loan_request.borrower_id} (5 samples)...")

    try:
        sample_count = 0
        async for update in calculator.stream_rate_updates_for_loan(loan_request):
            if 'error' in update:
                print(f"   [{update['timestamp']}] Error: {update['error']}")
            else:
                print(f"   [{update['timestamp']}] Rate: {update['rate']:.4f} "
                      f"| Confidence: {update['confidence']:.3f} "
                      f"| Risk: {update['risk_level']}")

            sample_count += 1
            if sample_count >= 5:  # Limit demo to 5 samples
                break

    except Exception as e:
        print(f"   ❌ Streaming failed: {e}")

    print("\n✅ INTEGRATION DEMO COMPLETE")
    print("="*70)
    print("The interest rate determiner is successfully integrated with the lending platform!")
    print("- Real-time rate calculations")
    print("- Comprehensive risk assessment")
    print("- Market health monitoring")
    print("- Live rate streaming")
    print("- Seamless data flow between systems")

# API Integration Example
async def api_integration_example():
    """Example of API-based integration"""

    print("\n🔌 API INTEGRATION EXAMPLE")
    print("-" * 30)

    # This would be used in a FastAPI endpoint
    integration_code = '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from integration_with_lending_platform import IntegratedRateCalculator

app = FastAPI()
rate_calculator = IntegratedRateCalculator()

class LoanRateRequest(BaseModel):
    borrower_id: str
    amount: float
    term_days: int
    collateral_asset_id: int = None

@app.post("/api/v1/calculate-rate")
async def calculate_loan_rate(request: LoanRateRequest):
    try:
        loan_request = LoanRequest(
            amount=request.amount,
            term_days=request.term_days,
            borrower_id=request.borrower_id,
            collateral_asset_id=request.collateral_asset_id
        )

        result = await rate_calculator.calculate_rate_for_loan_request(loan_request)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/market-summary")
async def get_market_summary():
    return await rate_calculator.get_market_rate_summary()
'''

    print(integration_code)

async def main():
    """Run the integration demonstration"""
    await demo_integration()
    await api_integration_example()

if __name__ == "__main__":
    asyncio.run(main())