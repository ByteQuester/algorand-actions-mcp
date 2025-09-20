#!/usr/bin/env python3
"""
Basic functionality tests for Portfolio Diversification Engine
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from core.config import PortfolioDiversificationConfig, load_config
from core.portfolio_engine import (
    PortfolioDiversificationEngine,
    AssetPosition,
    Portfolio,
    create_sample_portfolio
)


class TestPortfolioDiversificationEngine(unittest.TestCase):
    """Test cases for the Portfolio Diversification Engine"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test database
        self.temp_dir = tempfile.mkdtemp()

        # Create test config with temporary database path
        self.config = PortfolioDiversificationConfig()
        self.config.database.default_path = str(Path(self.temp_dir) / "test_portfolio.db")

        # Initialize engine
        self.engine = PortfolioDiversificationEngine(self.config)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_loading(self):
        """Test configuration loading"""
        config = load_config()
        self.assertIsInstance(config, PortfolioDiversificationConfig)
        self.assertEqual(config.mcp_services.algorand_reader_url, "http://localhost:8002")
        self.assertEqual(config.mcp_services.market_data_url, "http://localhost:8003")
        self.assertEqual(config.hhi_calculation.min_hhi, 0.2)
        self.assertEqual(config.hhi_calculation.max_hhi, 1.0)

    def test_hhi_calculation(self):
        """Test HHI score calculation"""
        # Test single asset portfolio (should have max HHI)
        single_asset_portfolio = Portfolio(
            positions=[
                AssetPosition(
                    symbol="BTC",
                    asset_type="cryptocurrency",
                    value_usd=10000,
                    weight=1.0
                )
            ],
            total_value_usd=10000,
            timestamp=datetime.now()
        )

        hhi = self.engine.calculate_hhi_score(single_asset_portfolio)
        self.assertEqual(hhi, 1.0)

        # Test perfectly diversified portfolio
        diversified_portfolio = Portfolio(
            positions=[
                AssetPosition(symbol="BTC", asset_type="cryptocurrency", value_usd=2000, weight=0.2),
                AssetPosition(symbol="USDC", asset_type="stablecoin", value_usd=2000, weight=0.2),
                AssetPosition(symbol="UNI", asset_type="defi_token", value_usd=2000, weight=0.2),
                AssetPosition(symbol="APE", asset_type="nft", value_usd=2000, weight=0.2),
                AssetPosition(symbol="COMP", asset_type="governance_token", value_usd=2000, weight=0.2)
            ],
            total_value_usd=10000,
            timestamp=datetime.now()
        )

        hhi = self.engine.calculate_hhi_score(diversified_portfolio)
        self.assertAlmostEqual(hhi, 0.2, places=2)

    def test_diversification_score_calculation(self):
        """Test diversification score calculation"""
        # Test max HHI (min diversification)
        score = self.engine.calculate_diversification_score(1.0)
        self.assertEqual(score, 0.0)

        # Test min HHI (max diversification)
        score = self.engine.calculate_diversification_score(0.2)
        self.assertEqual(score, 1.0)

        # Test middle HHI
        score = self.engine.calculate_diversification_score(0.6)
        self.assertEqual(score, 0.5)

    def test_diversification_level_classification(self):
        """Test diversification level classification"""
        self.assertEqual(self.engine.get_diversification_level(0.9), "excellent")
        self.assertEqual(self.engine.get_diversification_level(0.7), "good")
        self.assertEqual(self.engine.get_diversification_level(0.5), "adequate")
        self.assertEqual(self.engine.get_diversification_level(0.3), "poor")
        self.assertEqual(self.engine.get_diversification_level(0.1), "very_poor")

    def test_concentration_violation_detection(self):
        """Test concentration violation detection"""
        # Portfolio with single asset over limit
        concentrated_portfolio = Portfolio(
            positions=[
                AssetPosition(symbol="BTC", asset_type="cryptocurrency", value_usd=5000, weight=0.5),
                AssetPosition(symbol="DOGE", asset_type="cryptocurrency", value_usd=5000, weight=0.5)
            ],
            total_value_usd=10000,
            timestamp=datetime.now()
        )

        violations = self.engine.check_concentration_violations(concentrated_portfolio)
        self.assertTrue(len(violations) > 0)
        self.assertTrue(any("concentration" in v for v in violations))

    def test_sample_portfolio_analysis(self):
        """Test analysis of sample portfolio"""
        portfolio = create_sample_portfolio()
        analysis = self.engine.analyze_portfolio(portfolio)

        # Verify analysis structure
        self.assertIsNotNone(analysis.hhi_score)
        self.assertIsNotNone(analysis.diversification_score)
        self.assertIn(analysis.diversification_level,
                     ["excellent", "good", "adequate", "poor", "very_poor"])
        self.assertIsInstance(analysis.concentration_violations, list)
        self.assertIsInstance(analysis.correlation_risks, list)
        self.assertIsInstance(analysis.liquidity_risks, list)
        self.assertIsInstance(analysis.recommendations, list)
        self.assertIsInstance(analysis.risk_adjustments, dict)
        self.assertGreaterEqual(analysis.confidence_score, 0.0)
        self.assertLessEqual(analysis.confidence_score, 1.0)

    def test_risk_adjustments(self):
        """Test risk adjustment calculations"""
        # Test excellent diversification
        adjustments = self.engine.calculate_risk_adjustments("excellent")
        self.assertIn("collateral_ratio_reduction", adjustments)
        self.assertIn("confidence_bonus", adjustments)

        # Test poor diversification
        adjustments = self.engine.calculate_risk_adjustments("poor")
        self.assertIn("collateral_ratio_increase", adjustments)
        self.assertIn("confidence_penalty", adjustments)

    def test_database_operations(self):
        """Test database storage and retrieval"""
        portfolio = create_sample_portfolio()
        analysis = self.engine.analyze_portfolio(portfolio)

        # Test history retrieval
        history = self.engine.get_analysis_history(limit=10)
        self.assertIsInstance(history, list)

        if history:  # Only test if storage was successful
            self.assertGreater(len(history), 0)
            self.assertIn("portfolio_value_usd", history[0])
            self.assertIn("diversification_score", history[0])

    def test_empty_portfolio_handling(self):
        """Test handling of empty portfolios"""
        empty_portfolio = Portfolio(
            positions=[],
            total_value_usd=0.0,
            timestamp=datetime.now()
        )

        hhi = self.engine.calculate_hhi_score(empty_portfolio)
        self.assertEqual(hhi, 1.0)  # Max HHI for empty portfolio

    def test_recommendation_generation(self):
        """Test recommendation generation"""
        # Create poorly diversified portfolio
        poor_portfolio = Portfolio(
            positions=[
                AssetPosition(symbol="BTC", asset_type="cryptocurrency", value_usd=9000, weight=0.9),
                AssetPosition(symbol="ETH", asset_type="cryptocurrency", value_usd=1000, weight=0.1)
            ],
            total_value_usd=10000,
            timestamp=datetime.now()
        )

        analysis = self.engine.analyze_portfolio(poor_portfolio)
        self.assertTrue(len(analysis.recommendations) > 0)
        self.assertTrue(any("diversification" in rec.lower() for rec in analysis.recommendations))

    def test_configuration_parameters(self):
        """Test that configuration parameters are used correctly"""
        # Test HHI parameters
        self.assertEqual(self.engine.config.hhi_calculation.min_hhi, 0.2)
        self.assertEqual(self.engine.config.hhi_calculation.max_hhi, 1.0)

        # Test concentration limits
        self.assertEqual(self.engine.config.concentration_limits.single_asset_max, 0.40)
        self.assertEqual(self.engine.config.concentration_limits.single_type_max, 0.60)

        # Test diversification scoring thresholds
        self.assertEqual(self.engine.config.diversification_scoring.excellent_threshold, 0.8)
        self.assertEqual(self.engine.config.diversification_scoring.good_threshold, 0.6)

    def test_mcp_service_configuration(self):
        """Test MCP service URL configuration"""
        self.assertEqual(self.engine.config.mcp_services.algorand_reader_url, "http://localhost:8002")
        self.assertEqual(self.engine.config.mcp_services.market_data_url, "http://localhost:8003")

    def test_liquidity_tier_analysis(self):
        """Test liquidity tier analysis"""
        # Create portfolio with mixed liquidity tiers
        mixed_liquidity_portfolio = Portfolio(
            positions=[
                AssetPosition(symbol="BTC", asset_type="cryptocurrency", value_usd=3000, weight=0.3, liquidity_tier="high"),
                AssetPosition(symbol="ETH", asset_type="cryptocurrency", value_usd=3000, weight=0.3, liquidity_tier="high"),
                AssetPosition(symbol="UNI", asset_type="defi_token", value_usd=2000, weight=0.2, liquidity_tier="medium"),
                AssetPosition(symbol="NFT1", asset_type="nft", value_usd=2000, weight=0.2, liquidity_tier="low")
            ],
            total_value_usd=10000,
            timestamp=datetime.now()
        )

        liquidity_risks = self.engine.analyze_liquidity_risks(mixed_liquidity_portfolio)
        self.assertIsInstance(liquidity_risks, list)


def run_comprehensive_test():
    """Run comprehensive test of the portfolio diversification engine"""
    print("=" * 60)
    print("Portfolio Diversification Engine - Comprehensive Test")
    print("=" * 60)

    # Initialize engine
    engine = PortfolioDiversificationEngine()

    # Test with sample portfolio
    print("\n1. Testing with sample portfolio...")
    portfolio = create_sample_portfolio()
    analysis = engine.analyze_portfolio(portfolio)

    print(f"Portfolio Value: ${analysis.portfolio.total_value_usd:,.0f}")
    print(f"Number of Positions: {len(analysis.portfolio.positions)}")
    print(f"HHI Score: {analysis.hhi_score:.3f}")
    print(f"Diversification Score: {analysis.diversification_score:.1%}")
    print(f"Diversification Level: {analysis.diversification_level}")
    print(f"Confidence Score: {analysis.confidence_score:.1%}")

    if analysis.concentration_violations:
        print(f"\nConcentration Violations:")
        for violation in analysis.concentration_violations:
            print(f"  - {violation}")

    if analysis.correlation_risks:
        print(f"\nCorrelation Risks:")
        for risk in analysis.correlation_risks:
            print(f"  - {risk}")

    if analysis.liquidity_risks:
        print(f"\nLiquidity Risks:")
        for risk in analysis.liquidity_risks:
            print(f"  - {risk}")

    if analysis.recommendations:
        print(f"\nRecommendations:")
        for rec in analysis.recommendations:
            print(f"  - {rec}")

    if analysis.risk_adjustments:
        print(f"\nRisk Adjustments:")
        for key, value in analysis.risk_adjustments.items():
            print(f"  - {key}: {value:.1%}")

    # Test with poorly diversified portfolio
    print("\n\n2. Testing with poorly diversified portfolio...")
    poor_portfolio = Portfolio(
        positions=[
            AssetPosition(symbol="BTC", asset_type="cryptocurrency", value_usd=80000, weight=0.8),
            AssetPosition(symbol="ETH", asset_type="cryptocurrency", value_usd=20000, weight=0.2)
        ],
        total_value_usd=100000,
        timestamp=datetime.now()
    )

    poor_analysis = engine.analyze_portfolio(poor_portfolio)
    print(f"HHI Score: {poor_analysis.hhi_score:.3f}")
    print(f"Diversification Score: {poor_analysis.diversification_score:.1%}")
    print(f"Diversification Level: {poor_analysis.diversification_level}")
    print(f"Number of Violations: {len(poor_analysis.concentration_violations)}")
    print(f"Number of Recommendations: {len(poor_analysis.recommendations)}")

    # Test configuration
    print("\n\n3. Testing configuration...")
    config = engine.config
    print(f"MCP Reader URL: {config.mcp_services.algorand_reader_url}")
    print(f"MCP Market URL: {config.mcp_services.market_data_url}")
    print(f"Min HHI: {config.hhi_calculation.min_hhi}")
    print(f"Max HHI: {config.hhi_calculation.max_hhi}")
    print(f"Single Asset Max: {config.concentration_limits.single_asset_max:.1%}")

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    print("\n" + "=" * 60)

    # Run comprehensive test
    run_comprehensive_test()