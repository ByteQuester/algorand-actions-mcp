"""
Test suite for On-chain Reputation Scoring Engine
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from core.wallet_analyzer import WalletAnalyzer, WalletScore
from core.governance_scorer import GovernanceScorer, GovernanceScore
from core.reputation_engine import ReputationEngine, ReputationReport


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'reputation_scoring': {
            'wallet_weights': {
                'transaction_consistency': 0.25,
                'balance_stability': 0.20,
                'asset_diversity': 0.15,
                'defi_engagement': 0.25,
                'network_longevity': 0.15
            },
            'governance_weights': {
                'participation_rate': 0.30,
                'voting_consistency': 0.25,
                'algo_staking': 0.25,
                'proposal_engagement': 0.20
            }
        },
        'algorand_config': {
            'indexer': {'url': 'https://mainnet-idx.algonode.cloud'},
            'node': {'url': 'https://mainnet-api.algonode.cloud'},
            'governance': {'periods_to_analyze': 4}
        },
        'reputation_tiers': {
            'excellent': {'min_score': 0.85, 'rate_adjustment': -0.5},
            'good': {'min_score': 0.70, 'rate_adjustment': -0.25},
            'average': {'min_score': 0.50, 'rate_adjustment': 0.0},
            'poor': {'min_score': 0.30, 'rate_adjustment': 0.25},
            'very_poor': {'min_score': 0.0, 'rate_adjustment': 0.5}
        }
    }


@pytest.fixture
def wallet_analyzer(mock_config):
    """Create wallet analyzer with mock config"""
    return WalletAnalyzer(mock_config)


@pytest.fixture
def governance_scorer(mock_config):
    """Create governance scorer with mock config"""
    return GovernanceScorer(mock_config)


@pytest.fixture
def reputation_engine(mock_config):
    """Create reputation engine with mock config"""
    return ReputationEngine(config_dict=mock_config)


class TestWalletAnalyzer:
    """Test wallet analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_wallet_valid_address(self, wallet_analyzer):
        """Test wallet analysis with valid address"""
        test_address = "ALGORAND_ADDRESS_PLACEHOLDER_58_CHARS_LONG_FOR_TESTING"

        with patch.object(wallet_analyzer, 'indexer_client') as mock_indexer, \
             patch.object(wallet_analyzer, 'algod_client') as mock_algod:

            # Mock indexer responses
            mock_indexer.search_transactions.return_value = {
                'transactions': [
                    {
                        'id': 'test_tx_1',
                        'tx-type': 'pay',
                        'round-time': int(datetime.utcnow().timestamp()),
                        'payment-transaction': {'amount': 1000000}
                    }
                ]
            }

            # Mock algod responses
            mock_algod.account_info.return_value = {
                'amount': 10000000,  # 10 ALGO
                'assets': [
                    {'asset-id': 31566704, 'amount': 1000000}  # USDC
                ]
            }

            result = await wallet_analyzer.analyze_wallet(test_address)

            assert isinstance(result, WalletScore)
            assert result.address == test_address
            assert 0 <= result.overall_score <= 1
            assert result.analysis_timestamp is not None

    @pytest.mark.asyncio
    async def test_analyze_wallet_invalid_address(self, wallet_analyzer):
        """Test wallet analysis with invalid address"""
        invalid_address = "INVALID_ADDRESS"

        with pytest.raises(ValueError):
            await wallet_analyzer.analyze_wallet(invalid_address)

    def test_calculate_transaction_score(self, wallet_analyzer):
        """Test transaction score calculation"""
        from core.wallet_analyzer import TransactionPattern

        # Test with good transaction pattern
        good_pattern = TransactionPattern(
            total_transactions=100,
            avg_transactions_per_day=3.0,
            consistency_score=0.8,
            large_transaction_ratio=0.1,
            transaction_types={'pay': 80, 'appl': 20}
        )

        score = wallet_analyzer._calculate_transaction_score(good_pattern)
        assert 0 <= score <= 1
        assert score > 0.5  # Should be good score

    def test_calculate_balance_score(self, wallet_analyzer):
        """Test balance score calculation"""
        from core.wallet_analyzer import BalanceAnalysis

        # Test with stable balance
        stable_balance = BalanceAnalysis(
            current_balance=1000.0,
            avg_balance=950.0,
            balance_volatility=0.1,
            stability_score=0.9,
            min_balance=800.0,
            max_balance=1200.0
        )

        score = wallet_analyzer._calculate_balance_score(stable_balance)
        assert 0 <= score <= 1
        assert score > 0.5  # Should be good score


class TestGovernanceScorer:
    """Test governance scoring functionality"""

    @pytest.mark.asyncio
    async def test_score_governance_participation(self, governance_scorer):
        """Test governance participation scoring"""
        test_address = "ALGORAND_ADDRESS_PLACEHOLDER_58_CHARS_LONG_FOR_TESTING"

        with patch.object(governance_scorer, 'indexer_client') as mock_indexer, \
             patch.object(governance_scorer, 'algod_client') as mock_algod:

            # Mock governance data
            mock_indexer.search_transactions.return_value = {
                'transactions': [
                    {
                        'id': 'gov_tx_1',
                        'tx-type': 'appl',
                        'application-transaction': {
                            'application-id': 552635992,
                            'application-args': ['register']
                        }
                    }
                ]
            }

            mock_algod.account_info.return_value = {
                'amount': 50000000000  # 50k ALGO
            }

            result = await governance_scorer.score_governance_participation(test_address)

            assert isinstance(result, GovernanceScore)
            assert result.address == test_address
            assert 0 <= result.overall_score <= 1

    def test_calculate_participation_score(self, governance_scorer):
        """Test participation score calculation"""
        from core.governance_scorer import GovernanceHistory

        # Test with good participation
        good_history = GovernanceHistory(
            total_periods=4,
            participated_periods=3,
            participation_rate=0.75,
            avg_algo_committed=10000.0,
            total_votes_cast=6,
            avg_voting_consistency=0.8,
            recent_activity=True
        )

        score = governance_scorer._calculate_participation_score(good_history)
        assert 0 <= score <= 1
        assert score > 0.5  # Should be good score


class TestReputationEngine:
    """Test reputation engine integration"""

    @pytest.mark.asyncio
    async def test_analyze_reputation_integration(self, reputation_engine):
        """Test full reputation analysis integration"""
        test_address = "ALGORAND_ADDRESS_PLACEHOLDER_58_CHARS_LONG_FOR_TESTING"

        # Mock the component analyzers
        mock_wallet_score = WalletScore(
            address=test_address,
            transaction_score=0.8,
            balance_score=0.7,
            asset_score=0.6,
            defi_score=0.5,
            longevity_score=0.9,
            overall_score=0.7,
            analysis_timestamp=datetime.utcnow()
        )

        from core.governance_scorer import GovernanceHistory
        mock_governance_score = GovernanceScore(
            address=test_address,
            participation_score=0.8,
            voting_consistency_score=0.7,
            staking_commitment_score=0.6,
            engagement_score=0.75,
            overall_score=0.73,
            governance_history=GovernanceHistory(
                total_periods=4,
                participated_periods=3,
                participation_rate=0.75,
                avg_algo_committed=5000.0,
                total_votes_cast=6,
                avg_voting_consistency=0.8,
                recent_activity=True
            ),
            analysis_timestamp=datetime.utcnow()
        )

        with patch.object(reputation_engine.wallet_analyzer, 'analyze_wallet',
                         return_value=mock_wallet_score), \
             patch.object(reputation_engine.governance_scorer, 'score_governance_participation',
                         return_value=mock_governance_score):

            result = await reputation_engine.analyze_reputation(test_address)

            assert isinstance(result, ReputationReport)
            assert result.address == test_address
            assert 0 <= result.overall_reputation_score <= 1
            assert result.risk_tier in reputation_engine.reputation_tiers
            assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_analyze_portfolio_reputation(self, reputation_engine):
        """Test portfolio reputation analysis"""
        test_addresses = [
            "ADDRESS_1_PLACEHOLDER_58_CHARS_LONG_FOR_TESTING_WALLET",
            "ADDRESS_2_PLACEHOLDER_58_CHARS_LONG_FOR_TESTING_WALLET"
        ]

        # Mock individual reports
        mock_report = ReputationReport(
            address="test",
            overall_reputation_score=0.7,
            risk_tier="good",
            rate_adjustment=-0.25,
            components=None,
            recommendations=["Test recommendation"],
            analysis_timestamp=datetime.utcnow(),
            next_review_date=datetime.utcnow() + timedelta(days=60)
        )

        with patch.object(reputation_engine, 'analyze_reputation',
                         return_value=mock_report):

            result = await reputation_engine.analyze_portfolio_reputation(test_addresses)

            assert len(result.individual_scores) == len(test_addresses)
            assert 0 <= result.portfolio_average <= 1
            assert isinstance(result.risk_distribution, dict)

    def test_calculate_combined_score(self, reputation_engine):
        """Test combined score calculation"""
        mock_wallet_score = WalletScore(
            address="test",
            transaction_score=0.8,
            balance_score=0.7,
            asset_score=0.6,
            defi_score=0.5,
            longevity_score=0.9,
            overall_score=0.7,
            analysis_timestamp=datetime.utcnow()
        )

        from core.governance_scorer import GovernanceHistory
        mock_governance_score = GovernanceScore(
            address="test",
            participation_score=0.8,
            voting_consistency_score=0.7,
            staking_commitment_score=0.6,
            engagement_score=0.75,
            overall_score=0.73,
            governance_history=GovernanceHistory(
                total_periods=4, participated_periods=3, participation_rate=0.75,
                avg_algo_committed=5000.0, total_votes_cast=6,
                avg_voting_consistency=0.8, recent_activity=True
            ),
            analysis_timestamp=datetime.utcnow()
        )

        combined_score = reputation_engine._calculate_combined_score(
            mock_wallet_score, mock_governance_score
        )

        assert 0 <= combined_score <= 1
        # Should be weighted average of wallet (0.7) and governance (0.73) scores
        expected = 0.7 * 0.6 + 0.73 * 0.4
        assert abs(combined_score - expected) < 0.01

    def test_determine_risk_tier(self, reputation_engine):
        """Test risk tier determination"""
        # Test excellent tier
        tier, adjustment = reputation_engine._determine_risk_tier(0.9)
        assert tier == "excellent"
        assert adjustment == -0.5

        # Test poor tier
        tier, adjustment = reputation_engine._determine_risk_tier(0.4)
        assert tier == "poor"
        assert adjustment == 0.25

    def test_export_reputation_report(self, reputation_engine):
        """Test report export functionality"""
        from core.governance_scorer import GovernanceHistory

        mock_wallet_score = WalletScore(
            address="test", transaction_score=0.8, balance_score=0.7,
            asset_score=0.6, defi_score=0.5, longevity_score=0.9,
            overall_score=0.7, analysis_timestamp=datetime.utcnow()
        )

        mock_governance_score = GovernanceScore(
            address="test", participation_score=0.8, voting_consistency_score=0.7,
            staking_commitment_score=0.6, engagement_score=0.75, overall_score=0.73,
            governance_history=GovernanceHistory(
                total_periods=4, participated_periods=3, participation_rate=0.75,
                avg_algo_committed=5000.0, total_votes_cast=6,
                avg_voting_consistency=0.8, recent_activity=True
            ),
            analysis_timestamp=datetime.utcnow()
        )

        from core.reputation_engine import ReputationComponents
        components = ReputationComponents(
            wallet_score=mock_wallet_score,
            governance_score=mock_governance_score,
            combined_score=0.7,
            risk_tier="good",
            rate_adjustment=-0.25
        )

        mock_report = ReputationReport(
            address="test",
            overall_reputation_score=0.7,
            risk_tier="good",
            rate_adjustment=-0.25,
            components=components,
            recommendations=["Test"],
            analysis_timestamp=datetime.utcnow(),
            next_review_date=datetime.utcnow() + timedelta(days=60)
        )

        # Test JSON export
        json_export = reputation_engine.export_reputation_report(mock_report, 'json')
        assert '"address": "test"' in json_export
        assert '"overall_score": 0.7' in json_export

        # Test YAML export
        yaml_export = reputation_engine.export_reputation_report(mock_report, 'yaml')
        assert 'address: test' in yaml_export


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])