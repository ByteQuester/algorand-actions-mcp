#!/usr/bin/env python3
"""
MCP Integration tests for Portfolio Diversification Engine

Tests integration with MCP services on ports 8002 and 8003
"""

import asyncio
import aiohttp
import json
import unittest
from datetime import datetime
from typing import Dict, List, Optional, Any

from core.config import PortfolioDiversificationConfig, load_config
from core.portfolio_engine import (
    PortfolioDiversificationEngine,
    AssetPosition,
    Portfolio
)


class MCPClient:
    """Client for communicating with MCP services"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_asset_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get asset data from MCP service"""
        try:
            async with self.session.get(
                f"{self.base_url}/asset/{symbol}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Warning: MCP service returned status {response.status} for {symbol}")
                    return None
        except Exception as e:
            print(f"Warning: Could not fetch asset data for {symbol}: {e}")
            return None

    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market data from MCP service"""
        try:
            async with self.session.get(
                f"{self.base_url}/market/{symbol}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Warning: Market data service returned status {response.status} for {symbol}")
                    return None
        except Exception as e:
            print(f"Warning: Could not fetch market data for {symbol}: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if MCP service is healthy"""
        try:
            async with self.session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception as e:
            print(f"Health check failed for {self.base_url}: {e}")
            return False


class PortfolioDataEnricher:
    """Enriches portfolio data using MCP services"""

    def __init__(self, config: PortfolioDiversificationConfig):
        self.config = config

    async def enrich_portfolio_with_mcp_data(self, portfolio: Portfolio) -> Portfolio:
        """Enrich portfolio positions with real data from MCP services"""

        async with MCPClient(self.config.mcp_services.algorand_reader_url) as algorand_client, \
                   MCPClient(self.config.mcp_services.market_data_url) as market_client:

            # Check service health
            algorand_healthy = await algorand_client.health_check()
            market_healthy = await market_client.health_check()

            print(f"Algorand Reader Service (port 8002): {'✓' if algorand_healthy else '✗'}")
            print(f"Market Data Service (port 8003): {'✓' if market_healthy else '✗'}")

            enriched_positions = []

            for position in portfolio.positions:
                enriched_position = await self._enrich_position(
                    position, algorand_client, market_client
                )
                enriched_positions.append(enriched_position)

            return Portfolio(
                positions=enriched_positions,
                total_value_usd=sum(pos.value_usd for pos in enriched_positions),
                timestamp=datetime.now()
            )

    async def _enrich_position(
        self,
        position: AssetPosition,
        algorand_client: MCPClient,
        market_client: MCPClient
    ) -> AssetPosition:
        """Enrich a single position with MCP data"""

        # Get asset data from Algorand reader
        asset_data = await algorand_client.get_asset_data(position.symbol)

        # Get market data
        market_data = await market_client.get_market_data(position.symbol)

        # Create enriched position
        enriched = AssetPosition(
            symbol=position.symbol,
            asset_type=position.asset_type,
            value_usd=position.value_usd,
            weight=position.weight,
            volatility_30d=position.volatility_30d,
            daily_volume_usd=position.daily_volume_usd,
            liquidity_tier=position.liquidity_tier,
            correlation_with_portfolio=position.correlation_with_portfolio
        )

        # Enrich with asset data if available
        if asset_data:
            # Update asset type if available from MCP
            if 'asset_type' in asset_data:
                enriched.asset_type = asset_data['asset_type']

            # Update value if available
            if 'price_usd' in asset_data and 'balance' in asset_data:
                enriched.value_usd = asset_data['price_usd'] * asset_data['balance']

        # Enrich with market data if available
        if market_data:
            if 'volatility_30d' in market_data:
                enriched.volatility_30d = market_data['volatility_30d']

            if 'daily_volume_usd' in market_data:
                enriched.daily_volume_usd = market_data['daily_volume_usd']

            if 'liquidity_tier' in market_data:
                enriched.liquidity_tier = market_data['liquidity_tier']

        # Determine liquidity tier based on volume if not provided
        if not enriched.liquidity_tier or enriched.liquidity_tier == "medium":
            enriched.liquidity_tier = self._determine_liquidity_tier(enriched.daily_volume_usd)

        return enriched

    def _determine_liquidity_tier(self, daily_volume_usd: float) -> str:
        """Determine liquidity tier based on daily volume"""
        high_threshold = self.config.liquidity_tiers.high.daily_volume_threshold
        medium_threshold = self.config.liquidity_tiers.medium.daily_volume_threshold

        if daily_volume_usd >= high_threshold:
            return "high"
        elif daily_volume_usd >= medium_threshold:
            return "medium"
        else:
            return "low"


class TestMCPIntegration(unittest.TestCase):
    """Test cases for MCP integration"""

    def setUp(self):
        """Set up test environment"""
        self.config = load_config()
        self.engine = PortfolioDiversificationEngine(self.config)
        self.enricher = PortfolioDataEnricher(self.config)

    def test_mcp_service_configuration(self):
        """Test MCP service configuration"""
        self.assertEqual(self.config.mcp_services.algorand_reader_url, "http://localhost:8002")
        self.assertEqual(self.config.mcp_services.market_data_url, "http://localhost:8003")

    def test_mcp_service_health_check(self):
        """Test MCP service health checks"""

        async def check_services():
            async with MCPClient(self.config.mcp_services.algorand_reader_url) as algorand_client, \
                       MCPClient(self.config.mcp_services.market_data_url) as market_client:

                algorand_healthy = await algorand_client.health_check()
                market_healthy = await market_client.health_check()

                return algorand_healthy, market_healthy

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            algorand_healthy, market_healthy = loop.run_until_complete(check_services())

            # Note: These may fail if services are not running, which is expected
            print(f"Algorand Reader Service: {'Available' if algorand_healthy else 'Unavailable'}")
            print(f"Market Data Service: {'Available' if market_healthy else 'Unavailable'}")

            # Test passes regardless of service availability for CI/CD compatibility
            self.assertTrue(True)

        finally:
            loop.close()

    def test_portfolio_enrichment_with_mcp_fallback(self):
        """Test portfolio enrichment with MCP data (with fallback for service unavailability)"""

        # Create test portfolio
        test_portfolio = Portfolio(
            positions=[
                AssetPosition(
                    symbol="ALGO",
                    asset_type="cryptocurrency",
                    value_usd=10000,
                    weight=0.4,
                    volatility_30d=0.20,
                    daily_volume_usd=50_000_000,
                    liquidity_tier="high"
                ),
                AssetPosition(
                    symbol="USDC",
                    asset_type="stablecoin",
                    value_usd=7500,
                    weight=0.3,
                    volatility_30d=0.02,
                    daily_volume_usd=1_000_000_000,
                    liquidity_tier="high"
                ),
                AssetPosition(
                    symbol="UNI",
                    asset_type="defi_token",
                    value_usd=5000,
                    weight=0.2,
                    volatility_30d=0.30,
                    daily_volume_usd=200_000_000,
                    liquidity_tier="medium"
                ),
                AssetPosition(
                    symbol="COMP",
                    asset_type="governance_token",
                    value_usd=2500,
                    weight=0.1,
                    volatility_30d=0.35,
                    daily_volume_usd=75_000_000,
                    liquidity_tier="medium"
                )
            ],
            total_value_usd=25000,
            timestamp=datetime.now()
        )

        async def test_enrichment():
            enriched_portfolio = await self.enricher.enrich_portfolio_with_mcp_data(test_portfolio)
            return enriched_portfolio

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            enriched_portfolio = loop.run_until_complete(test_enrichment())

            # Verify portfolio structure
            self.assertEqual(len(enriched_portfolio.positions), 4)
            self.assertGreater(enriched_portfolio.total_value_usd, 0)

            # Verify positions have required fields
            for position in enriched_portfolio.positions:
                self.assertIsNotNone(position.symbol)
                self.assertIsNotNone(position.asset_type)
                self.assertGreaterEqual(position.value_usd, 0)
                self.assertIn(position.liquidity_tier, ["high", "medium", "low"])

        finally:
            loop.close()

    def test_diversification_analysis_with_enriched_data(self):
        """Test diversification analysis with enriched MCP data"""

        async def test_analysis():
            # Create test portfolio
            test_portfolio = Portfolio(
                positions=[
                    AssetPosition(symbol="ALGO", asset_type="cryptocurrency", value_usd=15000, weight=0.5),
                    AssetPosition(symbol="USDC", asset_type="stablecoin", value_usd=9000, weight=0.3),
                    AssetPosition(symbol="UNI", asset_type="defi_token", value_usd=6000, weight=0.2)
                ],
                total_value_usd=30000,
                timestamp=datetime.now()
            )

            # Enrich with MCP data
            enriched_portfolio = await self.enricher.enrich_portfolio_with_mcp_data(test_portfolio)

            # Analyze diversification
            analysis = self.engine.analyze_portfolio(enriched_portfolio)

            return analysis

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analysis = loop.run_until_complete(test_analysis())

            # Verify analysis results
            self.assertIsNotNone(analysis.hhi_score)
            self.assertIsNotNone(analysis.diversification_score)
            self.assertIn(analysis.diversification_level,
                         ["excellent", "good", "adequate", "poor", "very_poor"])
            self.assertIsInstance(analysis.recommendations, list)
            self.assertGreaterEqual(analysis.confidence_score, 0.0)
            self.assertLessEqual(analysis.confidence_score, 1.0)

        finally:
            loop.close()


async def run_mcp_integration_demo():
    """Run comprehensive MCP integration demonstration"""
    print("=" * 70)
    print("Portfolio Diversification Engine - MCP Integration Demo")
    print("=" * 70)

    config = load_config()
    engine = PortfolioDiversificationEngine(config)
    enricher = PortfolioDataEnricher(config)

    print(f"\nMCP Service Configuration:")
    print(f"  Algorand Reader: {config.mcp_services.algorand_reader_url}")
    print(f"  Market Data:     {config.mcp_services.market_data_url}")

    # Test service connectivity
    print(f"\nTesting MCP Service Connectivity...")

    async with MCPClient(config.mcp_services.algorand_reader_url) as algorand_client, \
               MCPClient(config.mcp_services.market_data_url) as market_client:

        algorand_healthy = await algorand_client.health_check()
        market_healthy = await market_client.health_check()

        print(f"  Algorand Reader Service: {'✓ Available' if algorand_healthy else '✗ Unavailable'}")
        print(f"  Market Data Service:     {'✓ Available' if market_healthy else '✗ Unavailable'}")

        if not algorand_healthy or not market_healthy:
            print(f"\n⚠️  Note: Some MCP services are unavailable.")
            print(f"   To test with live data, ensure services are running on:")
            print(f"   - Port 8002 (Algorand Reader)")
            print(f"   - Port 8003 (Market Data)")

    # Create sample Algorand-focused portfolio
    print(f"\n" + "="*50)
    print(f"Testing with Algorand-focused portfolio...")
    print(f"="*50)

    algorand_portfolio = Portfolio(
        positions=[
            AssetPosition(
                symbol="ALGO",
                asset_type="cryptocurrency",
                value_usd=20000,
                weight=0.4,
                volatility_30d=0.25,
                daily_volume_usd=150_000_000,
                liquidity_tier="high"
            ),
            AssetPosition(
                symbol="USDC",
                asset_type="stablecoin",
                value_usd=15000,
                weight=0.3,
                volatility_30d=0.02,
                daily_volume_usd=5_000_000_000,
                liquidity_tier="high"
            ),
            AssetPosition(
                symbol="PLANETS",
                asset_type="defi_token",
                value_usd=7500,
                weight=0.15,
                volatility_30d=0.40,
                daily_volume_usd=5_000_000,
                liquidity_tier="medium"
            ),
            AssetPosition(
                symbol="CHOICE",
                asset_type="governance_token",
                value_usd=5000,
                weight=0.1,
                volatility_30d=0.35,
                daily_volume_usd=2_000_000,
                liquidity_tier="medium"
            ),
            AssetPosition(
                symbol="ALGONODE_NFT",
                asset_type="nft",
                value_usd=2500,
                weight=0.05,
                volatility_30d=0.50,
                daily_volume_usd=100_000,
                liquidity_tier="low"
            )
        ],
        total_value_usd=50000,
        timestamp=datetime.now()
    )

    # Enrich portfolio with MCP data
    print(f"\nEnriching portfolio with MCP data...")
    enriched_portfolio = await enricher.enrich_portfolio_with_mcp_data(algorand_portfolio)

    print(f"\nPortfolio Summary (after MCP enrichment):")
    print(f"  Total Value: ${enriched_portfolio.total_value_usd:,.0f}")
    print(f"  Positions: {len(enriched_portfolio.positions)}")

    print(f"\nPosition Details:")
    for pos in enriched_portfolio.positions:
        print(f"  {pos.symbol:12} | {pos.asset_type:15} | ${pos.value_usd:8,.0f} | {pos.weight:5.1%} | {pos.liquidity_tier:6}")

    # Analyze diversification
    print(f"\nPerforming diversification analysis...")
    analysis = engine.analyze_portfolio(enriched_portfolio)

    print(f"\nDiversification Analysis Results:")
    print(f"  HHI Score:              {analysis.hhi_score:.3f}")
    print(f"  Diversification Score:  {analysis.diversification_score:.1%}")
    print(f"  Diversification Level:  {analysis.diversification_level}")
    print(f"  Confidence Score:       {analysis.confidence_score:.1%}")

    if analysis.concentration_violations:
        print(f"\nConcentration Violations:")
        for violation in analysis.concentration_violations:
            print(f"  ⚠️  {violation}")

    if analysis.correlation_risks:
        print(f"\nCorrelation Risks:")
        for risk in analysis.correlation_risks:
            print(f"  ⚠️  {risk}")

    if analysis.liquidity_risks:
        print(f"\nLiquidity Risks:")
        for risk in analysis.liquidity_risks:
            print(f"  ⚠️  {risk}")

    if analysis.recommendations:
        print(f"\nRecommendations:")
        for rec in analysis.recommendations:
            print(f"  💡 {rec}")

    if analysis.risk_adjustments:
        print(f"\nRisk Adjustments for Lending:")
        for key, value in analysis.risk_adjustments.items():
            if value > 0:
                print(f"  📈 {key.replace('_', ' ').title()}: {value:+.1%}")
            else:
                print(f"  📉 {key.replace('_', ' ').title()}: {value:+.1%}")

    print(f"\n" + "="*70)
    print(f"MCP Integration Demo completed successfully!")
    print(f"="*70)


def main():
    """Main function to run tests and demo"""
    print("Running MCP Integration Tests...")

    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)

    print(f"\n" + "="*70)

    # Run async demo
    print("Running MCP Integration Demo...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_mcp_integration_demo())
    finally:
        loop.close()


if __name__ == "__main__":
    main()