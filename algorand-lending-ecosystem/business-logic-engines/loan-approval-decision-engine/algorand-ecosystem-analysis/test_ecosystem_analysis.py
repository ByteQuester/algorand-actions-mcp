"""
Comprehensive Ecosystem Analysis Tests

Test suite for the Algorand ecosystem analysis engine covering all
components and integration scenarios.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from core.ecosystem_engine import EcosystemAnalysisEngine, EcosystemAnalysisResult
from core.wallet_footprint import WalletFootprintAnalyzer, WalletMetrics
from core.dapp_engagement import DAppEngagementAnalyzer, ProtocolEngagement
from core.nft_portfolio import NFTPortfolioAnalyzer, NFTHolding


class TestEcosystemAnalysisEngine:
    """Test the main ecosystem analysis engine"""

    @pytest.fixture
    def engine(self):
        """Create test engine instance"""
        return EcosystemAnalysisEngine()

    @pytest.fixture
    def test_wallet_address(self):
        """Test wallet address"""
        return "TESTWALLETADDRESS123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self, engine, test_wallet_address):
        """Test comprehensive ecosystem analysis"""
        result = await engine.analyze_complete_ecosystem(
            test_wallet_address,
            analysis_depth="comprehensive",
            requested_loan_amount=50000.0
        )

        assert isinstance(result, EcosystemAnalysisResult)
        assert result.borrower_profile.wallet_address == test_wallet_address
        assert result.confidence_score > 0
        assert result.analysis_metadata['analysis_depth'] == "comprehensive"

    @pytest.mark.asyncio
    async def test_basic_analysis(self, engine, test_wallet_address):
        """Test basic ecosystem analysis"""
        result = await engine.analyze_complete_ecosystem(
            test_wallet_address,
            analysis_depth="basic"
        )

        assert isinstance(result, EcosystemAnalysisResult)
        assert 'wallet_fundamentals' in result.analysis_metadata['components_analyzed']

    @pytest.mark.asyncio
    async def test_standard_analysis(self, engine, test_wallet_address):
        """Test standard ecosystem analysis"""
        result = await engine.analyze_complete_ecosystem(
            test_wallet_address,
            analysis_depth="standard"
        )

        assert isinstance(result, EcosystemAnalysisResult)
        components = result.analysis_metadata['components_analyzed']
        assert 'wallet_fundamentals' in components
        assert 'governance_analysis' in components

    @pytest.mark.asyncio
    async def test_invalid_analysis_depth(self, engine, test_wallet_address):
        """Test invalid analysis depth raises error"""
        with pytest.raises(ValueError, match="Invalid analysis depth"):
            await engine.analyze_complete_ecosystem(
                test_wallet_address,
                analysis_depth="invalid_depth"
            )

    @pytest.mark.asyncio
    async def test_analysis_summary(self, engine, test_wallet_address):
        """Test analysis summary generation"""
        summary = await engine.get_analysis_summary(test_wallet_address)

        assert 'wallet_address' in summary
        assert 'ecosystem_maturity' in summary
        assert 'risk_level' in summary
        assert 'analysis_confidence' in summary

    def test_ecosystem_maturity_calculation(self, engine):
        """Test ecosystem maturity calculation"""
        # Create mock result with known values
        mock_result = MagicMock()
        mock_result.borrower_profile.wallet_age_days = 800  # > 730 (30 points)
        mock_result.borrower_profile.total_transaction_count = 600  # > 500 (25 points)
        mock_result.borrower_profile.governance_participation = True  # 25 points
        mock_result.ecosystem_footprint.defi_protocols_used = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6']  # > 5 (20 points)

        maturity = engine._calculate_ecosystem_maturity(mock_result)
        assert maturity == "highly_mature"  # 100 points total

    def test_config_loading(self):
        """Test configuration loading"""
        engine = EcosystemAnalysisEngine()
        assert 'analysis' in engine.config
        assert 'scoring_weights' in engine.config


class TestWalletFootprintAnalyzer:
    """Test wallet footprint analysis"""

    @pytest.fixture
    def analyzer(self):
        """Create test analyzer instance"""
        config = {
            'wallet_footprint': {
                'age_scoring': {
                    'excellent_threshold_days': 730,
                    'good_threshold_days': 365,
                    'fair_threshold_days': 180,
                    'poor_threshold_days': 90
                },
                'volume_scoring': {
                    'excellent_threshold': 100000,
                    'good_threshold': 10000,
                    'fair_threshold': 1000,
                    'poor_threshold': 100
                }
            }
        }
        return WalletFootprintAnalyzer(config)

    @pytest.fixture
    def test_wallet_address(self):
        return "TESTWALLETADDRESS123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @pytest.mark.asyncio
    async def test_wallet_fundamentals_analysis(self, analyzer, test_wallet_address):
        """Test wallet fundamentals analysis"""
        result = await analyzer.analyze_wallet_fundamentals(test_wallet_address)

        assert 'wallet_metrics' in result
        assert 'asset_distribution' in result
        assert 'activity_patterns' in result
        assert 'scores' in result
        assert result['wallet_age_days'] > 0
        assert result['total_transactions'] >= 0

    @pytest.mark.asyncio
    async def test_transaction_patterns_analysis(self, analyzer, test_wallet_address):
        """Test transaction patterns analysis"""
        result = await analyzer.analyze_transaction_patterns(test_wallet_address)

        assert 'temporal_patterns' in result
        assert 'volume_patterns' in result
        assert 'counterparty_patterns' in result
        assert 'fee_patterns' in result
        assert 'pattern_scores' in result

    @pytest.mark.asyncio
    async def test_asset_portfolio_analysis(self, analyzer, test_wallet_address):
        """Test asset portfolio analysis"""
        result = await analyzer.analyze_asset_portfolio(test_wallet_address)

        assert 'composition' in result
        assert 'diversification' in result
        assert 'risk_analysis' in result
        assert 'portfolio_scores' in result

    @pytest.mark.asyncio
    async def test_empty_transaction_history(self, analyzer, test_wallet_address):
        """Test handling of empty transaction history"""
        with patch.object(analyzer, '_fetch_transaction_history', return_value=[]):
            result = await analyzer.analyze_transaction_patterns(test_wallet_address)

            assert result['total_transactions'] == 0
            assert 'temporal_patterns' in result

    def test_wallet_metrics_calculation(self, analyzer):
        """Test wallet metrics calculation"""
        creation_date = datetime.utcnow() - timedelta(days=365)
        creation_data = {'creation_date': creation_date}

        tx_history = [
            {'amount': 100, 'receiver': 'addr1'},
            {'amount': 200, 'receiver': 'addr2'},
            {'amount': 150, 'receiver': 'addr1'}
        ]

        asset_holdings = [{'asset_id': 0}, {'asset_id': 1}]
        nft_holdings = [{'asset_id': 123}]

        metrics = analyzer._calculate_wallet_metrics(
            creation_data, tx_history, asset_holdings, nft_holdings
        )

        assert isinstance(metrics, WalletMetrics)
        assert metrics.age_days == 365
        assert metrics.total_transactions == 3
        assert metrics.total_volume_algo == 450
        assert metrics.unique_counterparties == 2
        assert metrics.asset_count == 2
        assert metrics.nft_count == 1

    def test_score_calculation(self, analyzer):
        """Test wallet score calculation"""
        # Mock metrics
        wallet_metrics = WalletMetrics(
            creation_date=datetime.utcnow() - timedelta(days=800),
            age_days=800,
            total_transactions=500,
            total_volume_algo=50000,
            unique_counterparties=50,
            asset_count=10,
            nft_count=5,
            average_transaction_size=100,
            transaction_frequency=0.625
        )

        asset_distribution = MagicMock()
        asset_distribution.diversity_score = 0.8

        activity_patterns = MagicMock()
        activity_patterns.consistency_score = 0.9

        scores = analyzer._calculate_wallet_scores(
            wallet_metrics, asset_distribution, activity_patterns
        )

        assert 'age_score' in scores
        assert 'volume_score' in scores
        assert 'overall_score' in scores
        assert scores['age_score'] == 95  # Excellent age
        assert scores['volume_score'] == 80  # Good volume


class TestDAppEngagementAnalyzer:
    """Test DApp engagement analysis"""

    @pytest.fixture
    def analyzer(self):
        """Create test analyzer instance"""
        config = {
            'dapp_engagement': {
                'protocol_categories': {
                    'defi': {
                        'weight': 0.4,
                        'protocols': ['tinyman', 'algofi', 'folks_finance']
                    }
                },
                'sophistication_thresholds': {
                    'beginner': {'max_protocols': 2, 'max_interactions': 10},
                    'advanced': {'max_protocols': 10, 'max_interactions': 200}
                }
            }
        }
        return DAppEngagementAnalyzer(config)

    @pytest.fixture
    def test_wallet_address(self):
        return "TESTWALLETADDRESS123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @pytest.mark.asyncio
    async def test_defi_engagement_analysis(self, analyzer, test_wallet_address):
        """Test DeFi engagement analysis"""
        result = await analyzer.analyze_defi_engagement(test_wallet_address)

        assert 'protocol_engagement' in result
        assert 'detected_strategies' in result
        assert 'sophistication_metrics' in result
        assert 'engagement_scores' in result
        assert isinstance(result['protocols_used'], list)

    @pytest.mark.asyncio
    async def test_protocol_sophistication_analysis(self, analyzer, test_wallet_address):
        """Test protocol sophistication analysis"""
        result = await analyzer.analyze_protocol_sophistication(
            test_wallet_address,
            protocol_filter=['tinyman', 'algofi']
        )

        assert 'protocol_analysis' in result
        assert 'overall_sophistication' in result
        assert 'protocol_diversity' in result

    def test_protocol_engagement_creation(self, analyzer):
        """Test protocol engagement object creation"""
        activities = [
            {
                'timestamp': datetime.utcnow(),
                'protocol': 'tinyman',
                'amount': 1000,
                'function': 'swap'
            }
        ]

        engagement = asyncio.run(
            analyzer._analyze_single_protocol_engagement('tinyman', activities)
        )

        assert isinstance(engagement, ProtocolEngagement)
        assert engagement.protocol_name == 'tinyman'
        assert engagement.interaction_count == 1
        assert engagement.total_volume == 1000

    @pytest.mark.asyncio
    async def test_arbitrage_strategy_detection(self, analyzer):
        """Test arbitrage strategy detection"""
        dex_txs = [
            {
                'timestamp': datetime.utcnow(),
                'protocol': 'tinyman',
                'type': 'swap'
            },
            {
                'timestamp': datetime.utcnow() + timedelta(seconds=60),
                'protocol': 'pact',
                'type': 'swap'
            }
        ]

        strategy = await analyzer._detect_arbitrage_strategy(dex_txs)
        # With only 2 transactions, shouldn't detect arbitrage
        assert strategy is None

    @pytest.mark.asyncio
    async def test_yield_farming_strategy_detection(self, analyzer):
        """Test yield farming strategy detection"""
        yield_farming = [
            {'protocol': 'tinyman', 'action': 'add_liquidity'},
            {'protocol': 'algofi', 'action': 'stake'},
            {'protocol': 'folks_finance', 'action': 'supply'}
        ]
        staking_activities = [
            {'type': 'governance_stake', 'amount': 1000}
        ]

        strategy = await analyzer._detect_yield_farming_strategy(
            yield_farming, staking_activities
        )

        assert strategy is not None
        assert strategy.strategy_type == "yield_farming"
        assert strategy.sophistication_indicator is True

    def test_sophistication_metrics_calculation(self, analyzer):
        """Test sophistication metrics calculation"""
        protocol_engagement = [
            MagicMock(protocol_name='tinyman', interaction_count=10, total_volume=5000),
            MagicMock(protocol_name='algofi', interaction_count=5, total_volume=10000),
        ]

        detected_strategies = [
            MagicMock(sophistication_indicator=True),
            MagicMock(sophistication_indicator=False)
        ]

        metrics = analyzer._calculate_sophistication_metrics(
            protocol_engagement, detected_strategies
        )

        assert 'protocol_diversity_score' in metrics
        assert 'strategy_sophistication' in metrics
        assert 'overall_sophistication' in metrics
        assert metrics['strategy_sophistication'] == 0.5  # 1 sophisticated out of 2


class TestNFTPortfolioAnalyzer:
    """Test NFT portfolio analysis"""

    @pytest.fixture
    def analyzer(self):
        """Create test analyzer instance"""
        config = {
            'nft_portfolio': {
                'collection_tiers': {
                    'blue_chip': {'weight': 3.0, 'min_floor_price': 100},
                    'established': {'weight': 2.0, 'min_floor_price': 10}
                }
            }
        }
        return NFTPortfolioAnalyzer(config)

    @pytest.fixture
    def test_wallet_address(self):
        return "TESTWALLETADDRESS123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @pytest.fixture
    def sample_nft_holdings(self):
        """Sample NFT holdings for testing"""
        return [
            NFTHolding(
                asset_id=123,
                collection_name='Algorand Pandas',
                token_name='Panda #123',
                rarity_rank=100,
                floor_price=45.0,
                current_value=50.0,
                acquisition_date=datetime.utcnow() - timedelta(days=60),
                acquisition_method='purchase',
                hold_duration_days=60
            ),
            NFTHolding(
                asset_id=456,
                collection_name='AlgoGems',
                token_name='Gem #456',
                rarity_rank=500,
                floor_price=12.0,
                current_value=15.0,
                acquisition_date=datetime.utcnow() - timedelta(days=30),
                acquisition_method='mint',
                hold_duration_days=30
            )
        ]

    @pytest.mark.asyncio
    async def test_nft_portfolio_analysis(self, analyzer, test_wallet_address):
        """Test NFT portfolio analysis"""
        result = await analyzer.analyze_nft_portfolio(test_wallet_address)

        assert 'portfolio_composition' in result
        assert 'collection_strategies' in result
        assert 'value_analysis' in result
        assert 'nft_scores' in result
        assert result['nft_count'] >= 0

    @pytest.mark.asyncio
    async def test_collection_behavior_analysis(self, analyzer, test_wallet_address):
        """Test collection-specific behavior analysis"""
        result = await analyzer.analyze_collection_behavior(
            test_wallet_address,
            'Algorand Pandas'
        )

        assert 'collection_name' in result
        assert 'analysis' in result
        assert 'engagement_level' in result

    def test_portfolio_composition_analysis(self, analyzer, sample_nft_holdings):
        """Test portfolio composition analysis"""
        composition = analyzer._analyze_portfolio_composition(sample_nft_holdings)

        assert composition['total_value'] == 65.0  # 50 + 15
        assert composition['collection_count'] == 2
        assert composition['total_tokens'] == 2
        assert 'diversification_score' in composition

    def test_tier_distribution_analysis(self, analyzer, sample_nft_holdings):
        """Test tier distribution analysis"""
        tier_dist = analyzer._analyze_tier_distribution(sample_nft_holdings)

        # Should have both blue_chip and established based on mock tier assignment
        assert isinstance(tier_dist, dict)
        assert sum(tier_dist.values()) <= 1.0  # Percentages should sum to ≤ 1

    def test_collection_tier_determination(self, analyzer):
        """Test collection tier determination"""
        assert analyzer._determine_collection_tier('Algorand Pandas') == 'blue_chip'
        assert analyzer._determine_collection_tier('Unknown Collection') == 'emerging'

    def test_holding_strategy_determination(self, analyzer, sample_nft_holdings):
        """Test holding strategy determination"""
        trading_history = [
            {'collection': 'Algorand Pandas', 'action': 'sell'},
            {'collection': 'AlgoGems', 'action': 'buy'}
        ]

        strategy = analyzer._determine_holding_strategy(
            sample_nft_holdings, trading_history
        )

        # Based on average hold time of 45 days (30-60), should be medium_term_holder
        assert strategy in ['long_term_collector', 'medium_term_holder', 'active_trader', 'short_term_speculator']

    def test_creator_sophistication_calculation(self, analyzer):
        """Test creator sophistication calculation"""
        from core.nft_portfolio import CreatorActivity

        creator_activity = CreatorActivity(
            collections_created=2,
            tokens_minted=50,
            total_sales_volume=5000,
            creator_royalties_earned=250,
            community_engagement_score=0.8,
            artistic_reputation_score=0.7
        )

        sophistication = analyzer._calculate_creator_sophistication(creator_activity)

        assert 0 <= sophistication <= 1.0
        assert sophistication > 0.5  # Should be high given the good metrics

    def test_empty_portfolio_handling(self, analyzer):
        """Test handling of empty NFT portfolio"""
        composition = analyzer._analyze_portfolio_composition([])

        assert composition['total_value'] == 0
        assert composition['collection_count'] == 0
        assert composition['diversification_score'] == 0


class TestIntegrationScenarios:
    """Test integration scenarios across components"""

    @pytest.fixture
    def engine(self):
        return EcosystemAnalysisEngine()

    @pytest.mark.asyncio
    async def test_new_wallet_analysis(self, engine):
        """Test analysis of a very new wallet"""
        new_wallet = "NEWWALLETADDRESS123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        # Mock very basic data for new wallet
        with patch.object(engine.wallet_analyzer, '_fetch_wallet_creation_data') as mock_creation:
            mock_creation.return_value = {
                'creation_date': datetime.utcnow() - timedelta(days=5),
                'first_transaction_date': datetime.utcnow() - timedelta(days=4),
                'is_multisig': False,
                'account_type': 'standard'
            }

            result = await engine.analyze_complete_ecosystem(
                new_wallet,
                analysis_depth="basic"
            )

            assert result.borrower_profile.wallet_age_days == 5
            assert result.confidence_score < 0.8  # Should have lower confidence for new wallets

    @pytest.mark.asyncio
    async def test_sophisticated_user_analysis(self, engine):
        """Test analysis of a sophisticated DeFi user"""
        sophisticated_wallet = "SOPHISTICATEDWALLET123456789ABCDEFGHIJKLMNOP"

        result = await engine.analyze_complete_ecosystem(
            sophisticated_wallet,
            analysis_depth="comprehensive",
            requested_loan_amount=100000.0
        )

        # Should detect high sophistication
        assert result.borrower_profile.governance_participation is True
        assert len(result.ecosystem_footprint.defi_protocols_used) > 0
        assert result.confidence_score > 0.5

    @pytest.mark.asyncio
    async def test_risk_detection_integration(self, engine):
        """Test integration of risk detection across components"""
        risky_wallet = "RISKYWALLET123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        result = await engine.analyze_complete_ecosystem(
            risky_wallet,
            analysis_depth="comprehensive"
        )

        # Should have risk indicators
        assert result.risk_profile.overall_risk_level is not None
        assert result.risk_profile.overall_risk_score >= 0

    def test_config_validation(self, engine):
        """Test configuration validation"""
        assert engine.config is not None
        assert 'analysis' in engine.config
        assert 'scoring_weights' in engine.config

        # Validate scoring weights sum to reasonable total
        weights = engine.config['scoring_weights']
        total_weight = sum(weights.values())
        assert 0.9 <= total_weight <= 1.1  # Allow for small rounding errors


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def engine(self):
        return EcosystemAnalysisEngine()

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, engine):
        """Test handling of network timeouts"""
        with patch.object(engine.wallet_analyzer, '_fetch_transaction_history') as mock_fetch:
            mock_fetch.side_effect = asyncio.TimeoutError("Network timeout")

            # Should handle timeout gracefully
            with pytest.raises(asyncio.TimeoutError):
                await engine.analyze_complete_ecosystem("TESTWALLET", "basic")

    @pytest.mark.asyncio
    async def test_invalid_wallet_address(self, engine):
        """Test handling of invalid wallet addresses"""
        invalid_addresses = [
            "",
            "TOOSHORT",
            "TOOLONGWALLETADDRESSTOOLONGWALLETADDRESSTOOLONGWALLETADDRESSS",
            "INVALID@CHARACTERS#",
            None
        ]

        for invalid_addr in invalid_addresses:
            if invalid_addr is not None:
                # Should either handle gracefully or raise appropriate error
                try:
                    await engine.analyze_complete_ecosystem(invalid_addr, "basic")
                except (ValueError, TypeError):
                    pass  # Expected for invalid addresses

    @pytest.mark.asyncio
    async def test_partial_data_analysis(self, engine):
        """Test analysis with partial data availability"""
        with patch.object(engine.wallet_analyzer, '_fetch_asset_holdings') as mock_assets:
            mock_assets.return_value = []  # No asset data

            result = await engine.analyze_complete_ecosystem("TESTWALLET", "standard")

            # Should still complete analysis with available data
            assert result is not None
            assert result.confidence_score < 0.8  # Lower confidence with missing data

    def test_configuration_edge_cases(self):
        """Test configuration edge cases"""
        # Test with minimal config
        minimal_config = {
            'analysis': {
                'depth_levels': {
                    'basic': 'wallet_fundamentals'
                }
            },
            'scoring_weights': {
                'wallet_age': 1.0
            }
        }

        with patch('builtins.open', side_effect=FileNotFoundError):
            engine = EcosystemAnalysisEngine()
            # Should fall back to default config
            assert engine.config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])