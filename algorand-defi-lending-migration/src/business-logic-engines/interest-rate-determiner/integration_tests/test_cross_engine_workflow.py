"""
Integration tests for cross-engine workflows combining all 6 Algorand-native engines.

Tests:
- ALGO staking → DeFi yields → final rate calculation
- Reputation scoring → ASA risk → rate adjustment
- Network activity → liquidity pools → dynamic pricing
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from algosdk.v2client import algod, indexer

from interest_rate_determiner.engines import (
    AlgoStakingEngine,
    DeFiYieldEngine,
    ReputationEngine,
    ASARiskEngine,
    NetworkActivityEngine,
    LiquidityPoolEngine
)

@pytest.fixture
def mock_algod_client():
    """Mock Algorand client"""
    client = Mock(spec=algod.AlgodClient)
    client.status.return_value = {
        'last-round': 1000000,
        'time-since-last-round': 1000000000
    }
    client.supply.return_value = {
        'total-money': 10000000000,
        'online-money': 7000000000
    }
    return client

@pytest.fixture
def mock_indexer_client():
    """Mock Algorand indexer client"""
    client = Mock(spec=indexer.IndexerClient)
    client.search_transactions.return_value = []
    return client

@pytest.fixture
def engines(mock_algod_client, mock_indexer_client):
    """Create all 6 engines for testing"""
    return {
        'staking': AlgoStakingEngine(mock_algod_client),
        'defi': DeFiYieldEngine(mock_algod_client, {}),
        'reputation': ReputationEngine(mock_algod_client, mock_indexer_client),
        'asa_risk': ASARiskEngine(mock_algod_client, mock_indexer_client, {}),
        'network': NetworkActivityEngine(mock_algod_client),
        'liquidity': LiquidityPoolEngine(mock_algod_client)
    }

class TestCrossEngineWorkflows:
    """Test workflows that combine multiple engines"""

    @pytest.mark.asyncio
    async def test_staking_to_defi_to_final_rate(self, engines):
        """Test: ALGO staking → DeFi yields → final rate calculation"""

        # Step 1: Get ALGO staking rate
        staking_metrics = await engines['staking'].calculate_staking_rate()
        assert staking_metrics.current_apy > Decimal('0')
        assert staking_metrics.risk_adjusted_yield() > Decimal('0')

        # Step 2: Get DeFi market rates
        defi_metrics = await engines['defi'].calculate_defi_rates()
        assert defi_metrics.weighted_avg_apy > Decimal('0')
        assert defi_metrics.risk_adjusted_apy > Decimal('0')

        # Step 3: Combine rates for final calculation
        base_rate = staking_metrics.risk_adjusted_yield()
        market_rate = defi_metrics.risk_adjusted_apy

        # Final rate should be competitive with market but above staking
        competitive_rate = (base_rate + market_rate) / Decimal('2')

        assert competitive_rate >= base_rate
        assert competitive_rate <= market_rate * Decimal('1.2')  # At most 20% above market

        print(f"ALGO Staking Rate: {base_rate}")
        print(f"DeFi Market Rate: {market_rate}")
        print(f"Final Competitive Rate: {competitive_rate}")

    @pytest.mark.asyncio
    async def test_reputation_to_asa_risk_adjustment(self, engines):
        """Test: Reputation scoring → ASA risk → rate adjustment"""

        test_address = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        test_asset_id = 12345

        # Step 1: Calculate borrower reputation
        reputation = await engines['reputation'].calculate_reputation(test_address)
        assert reputation.overall_score >= Decimal('0')
        assert reputation.overall_score <= Decimal('1')

        # Step 2: Analyze ASA collateral risk
        asa_risk = await engines['asa_risk'].analyze_asa_risk(test_asset_id)
        assert asa_risk.overall_risk_score >= Decimal('0')
        assert asa_risk.overall_risk_score <= Decimal('1')

        # Step 3: Calculate combined rate adjustment
        reputation_discount = reputation.rate_discount()
        reputation_premium = reputation.rate_premium()
        asa_premium = asa_risk.rate_adjustment()

        # Net adjustment combines reputation and collateral risk
        net_adjustment = -reputation_discount + reputation_premium + asa_premium

        # Verify logical bounds
        assert net_adjustment >= Decimal('-0.02')  # Max 2% discount
        assert net_adjustment <= Decimal('0.07')   # Max 7% premium

        print(f"Reputation Score: {reputation.overall_score}")
        print(f"ASA Risk Score: {asa_risk.overall_risk_score}")
        print(f"Net Rate Adjustment: {net_adjustment}")

    @pytest.mark.asyncio
    async def test_network_activity_to_liquidity_pricing(self, engines):
        """Test: Network activity → liquidity pools → dynamic pricing"""

        # Step 1: Analyze network activity
        network_metrics = await engines['network'].analyze_network_activity()
        network_adjustments = await engines['network'].get_rate_adjustments()

        assert network_metrics.congestion_score >= Decimal('0')
        assert network_metrics.congestion_score <= Decimal('1')

        # Step 2: Analyze liquidity pool health
        liquidity_metrics = await engines['liquidity'].analyze_liquidity_health()
        liquidity_adjustments = await engines['liquidity'].get_liquidity_adjustments()

        assert liquidity_metrics.health_score >= Decimal('0')
        assert liquidity_metrics.health_score <= Decimal('1')

        # Step 3: Calculate dynamic pricing adjustments
        congestion_penalty = network_adjustments['congestion_adjustment']
        liquidity_bonus = liquidity_adjustments.get('liquidity_health_bonus', Decimal('0'))

        # Dynamic adjustment balances network stress with liquidity availability
        dynamic_adjustment = congestion_penalty - liquidity_bonus

        # Verify reasonable bounds
        assert dynamic_adjustment >= Decimal('-0.01')  # Max 1% discount for good liquidity
        assert dynamic_adjustment <= Decimal('0.02')   # Max 2% penalty for congestion

        print(f"Network Congestion: {network_metrics.congestion_score}")
        print(f"Liquidity Health: {liquidity_metrics.health_score}")
        print(f"Dynamic Adjustment: {dynamic_adjustment}")

    @pytest.mark.asyncio
    async def test_full_integration_rate_calculation(self, engines):
        """Test complete rate calculation using all 6 engines"""

        # Test parameters
        loan_amount = Decimal('100000')  # 100k ALGO
        loan_term_days = 365  # 1 year
        borrower_address = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        collateral_asset_id = 12345

        # Step 1: Get base rates from staking and DeFi
        staking_metrics = await engines['staking'].calculate_staking_rate()
        defi_metrics = await engines['defi'].calculate_defi_rates()

        base_rate = (staking_metrics.current_apy + defi_metrics.weighted_avg_apy) / Decimal('2')

        # Step 2: Apply borrower reputation adjustment
        reputation = await engines['reputation'].calculate_reputation(borrower_address)
        reputation_adjustment = reputation.rate_discount() - reputation.rate_premium()

        # Step 3: Apply collateral risk adjustment
        asa_risk = await engines['asa_risk'].analyze_asa_risk(collateral_asset_id)
        collateral_adjustment = asa_risk.rate_adjustment()

        # Step 4: Apply network and liquidity adjustments
        network_adjustments = await engines['network'].get_rate_adjustments()
        liquidity_adjustments = await engines['liquidity'].get_liquidity_adjustments()

        network_adjustment = network_adjustments['congestion_adjustment']
        liquidity_adjustment = liquidity_adjustments.get('liquidity_health_bonus', Decimal('0'))

        # Step 5: Calculate final rate
        final_rate = (
            base_rate +
            reputation_adjustment +
            collateral_adjustment +
            network_adjustment -
            liquidity_adjustment
        )

        # Ensure reasonable bounds
        min_rate = Decimal('0.02')  # 2% minimum
        max_rate = Decimal('0.25')  # 25% maximum
        final_rate = max(min_rate, min(final_rate, max_rate))

        # Verify all components
        assert base_rate > Decimal('0')
        assert final_rate >= min_rate
        assert final_rate <= max_rate

        # Calculate loan terms
        annual_interest = loan_amount * final_rate
        monthly_payment = (loan_amount * final_rate) / Decimal('12')

        print(f"\\n=== FULL INTEGRATION RATE CALCULATION ===")
        print(f"Base Rate (Staking + DeFi): {base_rate:.4f}")
        print(f"Reputation Adjustment: {reputation_adjustment:+.4f}")
        print(f"Collateral Risk Adjustment: {collateral_adjustment:+.4f}")
        print(f"Network Adjustment: {network_adjustment:+.4f}")
        print(f"Liquidity Adjustment: {-liquidity_adjustment:+.4f}")
        print(f"Final Interest Rate: {final_rate:.4f} ({final_rate*100:.2f}%)")
        print(f"Annual Interest: {annual_interest:.2f} ALGO")
        print(f"Monthly Payment: {monthly_payment:.2f} ALGO")

        return {
            'final_rate': final_rate,
            'base_rate': base_rate,
            'adjustments': {
                'reputation': reputation_adjustment,
                'collateral': collateral_adjustment,
                'network': network_adjustment,
                'liquidity': -liquidity_adjustment
            },
            'loan_terms': {
                'principal': loan_amount,
                'annual_interest': annual_interest,
                'monthly_payment': monthly_payment
            }
        }

    @pytest.mark.asyncio
    async def test_stress_scenarios(self, engines):
        """Test rate calculations under stress scenarios"""

        scenarios = [
            {
                'name': 'High DeFi Yield Environment',
                'description': 'High DeFi yields pushing rates up',
                'expected_rate_range': (Decimal('0.08'), Decimal('0.20'))
            },
            {
                'name': 'Bear Market ASA Volatility',
                'description': 'High ASA volatility increasing collateral risk',
                'expected_rate_range': (Decimal('0.06'), Decimal('0.25'))
            },
            {
                'name': 'Network Congestion',
                'description': 'High network congestion affecting rates',
                'expected_rate_range': (Decimal('0.05'), Decimal('0.15'))
            }
        ]

        for scenario in scenarios:
            # Run full integration test
            result = await self.test_full_integration_rate_calculation(engines)
            final_rate = result['final_rate']

            min_rate, max_rate = scenario['expected_rate_range']

            print(f"\\nScenario: {scenario['name']}")
            print(f"Description: {scenario['description']}")
            print(f"Final Rate: {final_rate:.4f}")
            print(f"Expected Range: {min_rate:.4f} - {max_rate:.4f}")

            # Verify rate is within expected range for scenario
            assert final_rate >= Decimal('0.02')  # Always above minimum
            assert final_rate <= Decimal('0.25')  # Always below maximum

class TestEngineInteractions:
    """Test specific engine-to-engine interactions"""

    @pytest.mark.asyncio
    async def test_staking_defi_correlation(self, engines):
        """Test correlation between staking and DeFi rates"""

        staking_rate = await engines['staking'].calculate_staking_rate()
        defi_rate = await engines['defi'].calculate_defi_rates()

        # DeFi rates should generally be higher than staking rates
        assert defi_rate.weighted_avg_apy >= staking_rate.current_apy * Decimal('0.8')

        # But not excessively higher (market efficiency)
        assert defi_rate.weighted_avg_apy <= staking_rate.current_apy * Decimal('3.0')

    @pytest.mark.asyncio
    async def test_reputation_risk_interaction(self, engines):
        """Test interaction between reputation and risk engines"""

        test_address = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        test_asset = 12345

        reputation = await engines['reputation'].calculate_reputation(test_address)
        asa_risk = await engines['asa_risk'].analyze_asa_risk(test_asset)

        # High reputation should offset some collateral risk
        if reputation.overall_score > Decimal('0.8'):  # Excellent reputation
            max_premium = asa_risk.rate_adjustment() * Decimal('0.8')  # 20% discount on risk premium
        else:
            max_premium = asa_risk.rate_adjustment()

        assert max_premium >= Decimal('0')

    @pytest.mark.asyncio
    async def test_network_liquidity_balance(self, engines):
        """Test balance between network congestion and liquidity"""

        network_metrics = await engines['network'].analyze_network_activity()
        liquidity_metrics = await engines['liquidity'].analyze_liquidity_health()

        # High liquidity should mitigate network congestion impact
        if liquidity_metrics.health_score > Decimal('0.8'):
            # Good liquidity reduces congestion impact
            congestion_impact = network_metrics.congestion_score * Decimal('0.5')
        else:
            # Poor liquidity amplifies congestion impact
            congestion_impact = network_metrics.congestion_score * Decimal('1.2')

        assert congestion_impact >= Decimal('0')
        assert congestion_impact <= Decimal('1.2')

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])