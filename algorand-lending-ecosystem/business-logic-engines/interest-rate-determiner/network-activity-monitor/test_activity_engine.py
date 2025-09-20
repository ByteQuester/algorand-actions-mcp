"""
Test suite for Network Activity Monitor Engine
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from core.network_health import NetworkHealthMonitor, NetworkHealthReport
from core.dapp_activity import DAppActivityMonitor, DAppActivityReport
from core.ecosystem_monitor import EcosystemMonitor, EcosystemReport
from core.activity_engine import NetworkActivityEngine, NetworkActivityReport


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'network_monitoring': {
            'health_weights': {
                'transaction_throughput': 0.30,
                'consensus_health': 0.25,
                'node_participation': 0.20,
                'mempool_status': 0.25
            },
            'dapp_weights': {
                'smart_contract_activity': 0.35,
                'defi_protocol_usage': 0.30,
                'nft_marketplace_activity': 0.15,
                'governance_activity': 0.20
            }
        },
        'network_thresholds': {
            'tps_levels': {
                'excellent': 1000,
                'good': 500,
                'average': 100,
                'poor': 50,
                'critical': 10
            },
            'block_time': {
                'target': 4.5,
                'excellent_variance': 0.5,
                'good_variance': 1.0,
                'poor_variance': 2.0
            },
            'participation_levels': {
                'excellent': 0.95,
                'good': 0.90,
                'average': 0.85,
                'poor': 0.80,
                'critical': 0.75
            }
        },
        'dapp_monitoring': {
            'defi_protocols': {
                'tinyman': {
                    'app_ids': [552635992],
                    'metrics': ['swaps', 'liquidity']
                }
            },
            'nft_platforms': {
                'algogems': {
                    'app_ids': [403380490],
                    'metrics': ['sales', 'listings']
                }
            },
            'activity_levels': {
                'high_activity': 10000,
                'moderate_activity': 1000,
                'low_activity': 100,
                'minimal_activity': 10
            }
        },
        'utilization_categories': {
            'very_high': {
                'min_tps': 800,
                'description': 'Network operating at high capacity',
                'rate_impact': -0.1
            },
            'high': {
                'min_tps': 400,
                'description': 'Strong network activity',
                'rate_impact': -0.05
            },
            'moderate': {
                'min_tps': 100,
                'description': 'Normal network activity',
                'rate_impact': 0.0
            },
            'low': {
                'min_tps': 50,
                'description': 'Below average activity',
                'rate_impact': 0.05
            },
            'very_low': {
                'min_tps': 0,
                'description': 'Minimal network activity',
                'rate_impact': 0.1
            }
        },
        'algorand_config': {
            'node': {'url': 'https://mainnet-api.algonode.cloud'},
            'indexer': {'url': 'https://mainnet-idx.algonode.cloud'}
        }
    }


@pytest.fixture
def network_monitor(mock_config):
    """Create network health monitor with mock config"""
    return NetworkHealthMonitor(mock_config)


@pytest.fixture
def dapp_monitor(mock_config):
    """Create DApp activity monitor with mock config"""
    return DAppActivityMonitor(mock_config)


@pytest.fixture
def ecosystem_monitor(mock_config):
    """Create ecosystem monitor with mock config"""
    return EcosystemMonitor(mock_config)


@pytest.fixture
def activity_engine(mock_config):
    """Create activity engine with mock config"""
    return NetworkActivityEngine(config_dict=mock_config)


class TestNetworkHealthMonitor:
    """Test network health monitoring functionality"""

    @pytest.mark.asyncio
    async def test_get_network_health_report(self, network_monitor):
        """Test network health report generation"""
        with patch.object(network_monitor, 'algod_client') as mock_algod:
            # Mock node status
            mock_algod.status.return_value = {
                'last-round': 100000,
                'last-round-time': int(datetime.utcnow().timestamp())
            }

            # Mock block info
            mock_algod.block_info.return_value = {
                'block': {
                    'txns': [{'tx-type': 'pay'} for _ in range(500)]
                }
            }

            # Mock suggested params
            mock_algod.suggested_params.return_value = Mock(fee=1000, min_fee=1000)

            result = await network_monitor.get_network_health_report()

            assert isinstance(result, NetworkHealthReport)
            assert result.timestamp is not None
            assert 0 <= result.overall_health_score <= 1
            assert result.health_status in ['excellent', 'good', 'average', 'poor', 'critical']

    @pytest.mark.asyncio
    async def test_calculate_current_tps(self, network_monitor):
        """Test TPS calculation"""
        with patch.object(network_monitor, 'algod_client') as mock_algod:
            # Mock status and block info for TPS calculation
            mock_algod.status.return_value = {'last-round': 10000}
            mock_algod.block_info.side_effect = lambda round_num: {
                'block': {
                    'txns': [{'tx-type': 'pay'} for _ in range(100)],  # 100 txns per block
                    'ts': int(datetime.utcnow().timestamp()) - (10000 - round_num) * 4.5
                }
            }

            tps = await network_monitor._calculate_current_tps()

            assert tps >= 0
            # With 100 txns per block and 4.5s block time, expect ~22 TPS
            assert 15 <= tps <= 30

    def test_calculate_throughput_score(self, network_monitor):
        """Test throughput score calculation"""
        from core.network_health import NetworkMetrics

        # High TPS metrics
        high_tps_metrics = NetworkMetrics(
            timestamp=datetime.utcnow(),
            current_round=100000,
            last_round_time=datetime.utcnow(),
            transactions_per_second=1200.0,  # Excellent level
            transactions_in_round=500,
            block_time=4.5,
            block_time_variance=0.3,
            rounds_per_minute=13.3,
            participation_rate=0.95,
            online_stake=7000000000000000,
            total_stake=10000000000000000,
            mempool_size=500,
            pending_transactions=500,
            suggested_fee=1000,
            min_fee=1000
        )

        score = network_monitor._calculate_throughput_score(high_tps_metrics)
        assert score == 1.0  # Should get maximum score

        # Low TPS metrics
        low_tps_metrics = NetworkMetrics(
            timestamp=datetime.utcnow(),
            current_round=100000,
            last_round_time=datetime.utcnow(),
            transactions_per_second=30.0,  # Poor level
            transactions_in_round=500,
            block_time=4.5,
            block_time_variance=0.3,
            rounds_per_minute=13.3,
            participation_rate=0.95,
            online_stake=7000000000000000,
            total_stake=10000000000000000,
            mempool_size=500,
            pending_transactions=500,
            suggested_fee=1000,
            min_fee=1000
        )

        score = network_monitor._calculate_throughput_score(low_tps_metrics)
        assert score == 0.2  # Should get low score


class TestDAppActivityMonitor:
    """Test DApp activity monitoring functionality"""

    @pytest.mark.asyncio
    async def test_get_dapp_activity_report(self, dapp_monitor):
        """Test DApp activity report generation"""
        with patch.object(dapp_monitor, 'indexer_client') as mock_indexer:
            # Mock application transactions
            mock_indexer.search_transactions.return_value = {
                'transactions': [
                    {
                        'id': f'tx_{i}',
                        'tx-type': 'appl',
                        'sender': f'sender_{i % 100}',  # 100 unique senders
                        'application-transaction': {
                            'application-id': 552635992
                        },
                        'round-time': int(datetime.utcnow().timestamp())
                    } for i in range(1000)  # 1000 app calls
                ]
            }

            result = await dapp_monitor.get_dapp_activity_report()

            assert isinstance(result, DAppActivityReport)
            assert result.timestamp is not None
            assert 0 <= result.overall_activity_score <= 1
            assert result.ecosystem_status in ['very_active', 'active', 'moderate', 'low', 'minimal']

    @pytest.mark.asyncio
    async def test_analyze_protocol_activity(self, dapp_monitor):
        """Test protocol activity analysis"""
        protocol_name = "tinyman"
        app_ids = [552635992]
        metrics = ['swaps', 'liquidity']

        with patch.object(dapp_monitor, 'indexer_client') as mock_indexer:
            # Mock protocol transactions
            mock_indexer.search_transactions.return_value = {
                'transactions': [
                    {
                        'id': f'tx_{i}',
                        'sender': f'user_{i}',
                        'payment-transaction': {'amount': 1000000}
                    } for i in range(500)
                ]
            }

            result = await dapp_monitor._analyze_protocol_activity(protocol_name, app_ids, metrics)

            assert result.protocol_name == protocol_name
            assert result.app_ids == app_ids
            assert result.total_transactions >= 0
            assert result.unique_users >= 0

    def test_calculate_defi_activity_score(self, dapp_monitor):
        """Test DeFi activity score calculation"""
        from core.dapp_activity import DeFiMetrics

        # High activity DeFi metrics
        high_activity = DeFiMetrics(
            dex_volume_24h=2000000.0,  # $2M volume
            dex_trades_count=5000,
            swap_protocols=[],
            lending_volume_24h=1000000.0,
            borrows_count=100,
            supplies_count=150,
            lending_protocols=[],
            total_liquidity_pools=200,
            total_tvl_usd=300000000.0,  # $300M TVL
            liquidity_growth=0.15,
            farming_protocols=10,
            staking_volume=50000000.0,
            average_apr=0.12
        )

        score = dapp_monitor._calculate_defi_activity_score(high_activity)
        assert 0 <= score <= 1
        assert score > 0.8  # Should get high score


class TestEcosystemMonitor:
    """Test ecosystem monitoring functionality"""

    @pytest.mark.asyncio
    async def test_generate_ecosystem_report(self, ecosystem_monitor):
        """Test ecosystem report generation"""
        # Most methods return default values, so this tests the integration
        result = await ecosystem_monitor.generate_ecosystem_report()

        assert isinstance(result, EcosystemReport)
        assert result.timestamp is not None
        assert 0 <= result.overall_ecosystem_score <= 1
        assert result.ecosystem_status in ['thriving', 'healthy', 'growing', 'developing', 'emerging']

    def test_calculate_growth_score(self, ecosystem_monitor):
        """Test growth score calculation"""
        from core.ecosystem_monitor import EcosystemGrowth

        # Strong growth metrics
        strong_growth = EcosystemGrowth(
            total_addresses=30000000,
            active_addresses_30d=3000000,
            new_addresses_30d=600000,
            address_growth_rate=0.25,  # 25% growth
            total_assets=600000,
            new_assets_30d=15000,
            asset_growth_rate=0.20,  # 20% growth
            verified_assets=6000,
            total_applications=20000,
            new_applications_30d=2500,
            application_growth_rate=0.30,  # 30% growth
            active_applications=8000,
            total_transactions=3000000000,
            transactions_30d=150000000,
            transaction_growth_rate=0.35  # 35% growth
        )

        score = ecosystem_monitor._calculate_growth_score(strong_growth)
        assert 0 <= score <= 1
        assert score > 0.8  # Should get high score


class TestActivityEngine:
    """Test activity engine integration"""

    @pytest.mark.asyncio
    async def test_analyze_network_activity_integration(self, activity_engine):
        """Test full network activity analysis integration"""
        # Mock the component monitors
        mock_network_report = self._create_mock_network_report()
        mock_dapp_report = self._create_mock_dapp_report()
        mock_ecosystem_report = self._create_mock_ecosystem_report()

        with patch.object(activity_engine.network_monitor, 'get_network_health_report',
                         return_value=mock_network_report), \
             patch.object(activity_engine.dapp_monitor, 'get_dapp_activity_report',
                         return_value=mock_dapp_report), \
             patch.object(activity_engine.ecosystem_monitor, 'generate_ecosystem_report',
                         return_value=mock_ecosystem_report):

            result = await activity_engine.analyze_network_activity()

            assert isinstance(result, NetworkActivityReport)
            assert result.timestamp is not None
            assert 0 <= result.overall_activity_score <= 1
            assert result.utilization_category in activity_engine.utilization_categories
            assert isinstance(result.recommended_rate_adjustment, (int, float))
            assert 0 <= result.adjustment_confidence <= 1

    @pytest.mark.asyncio
    async def test_get_real_time_activity_score(self, activity_engine):
        """Test real-time activity score"""
        with patch.object(activity_engine, '_get_quick_tps', return_value=250.0), \
             patch.object(activity_engine, '_get_quick_mempool_utilization', return_value=0.3):

            result = await activity_engine.get_real_time_activity_score()

            assert 'activity_score' in result
            assert 'network_tps' in result
            assert 'mempool_utilization' in result
            assert 'rate_adjustment' in result
            assert 0 <= result['activity_score'] <= 1

    def test_calculate_combined_activity_score(self, activity_engine):
        """Test combined activity score calculation"""
        mock_network_report = self._create_mock_network_report()
        mock_dapp_report = self._create_mock_dapp_report()
        mock_ecosystem_report = self._create_mock_ecosystem_report()

        combined_score = activity_engine._calculate_combined_activity_score(
            mock_network_report, mock_dapp_report, mock_ecosystem_report
        )

        assert 0 <= combined_score <= 1

    def test_determine_rate_adjustment(self, activity_engine):
        """Test rate adjustment determination"""
        mock_network_report = self._create_mock_network_report()
        mock_dapp_report = self._create_mock_dapp_report()

        category, adjustment = activity_engine._determine_rate_adjustment(
            0.7, mock_network_report, mock_dapp_report
        )

        assert category in activity_engine.utilization_categories
        assert isinstance(adjustment, (int, float))

    def test_calculate_adjustment_confidence(self, activity_engine):
        """Test adjustment confidence calculation"""
        mock_network_report = self._create_mock_network_report()
        mock_dapp_report = self._create_mock_dapp_report()
        mock_ecosystem_report = self._create_mock_ecosystem_report()

        confidence = activity_engine._calculate_adjustment_confidence(
            mock_network_report, mock_dapp_report, mock_ecosystem_report
        )

        assert 0 <= confidence <= 1

    @pytest.mark.asyncio
    async def test_get_activity_summary(self, activity_engine):
        """Test activity summary generation"""
        # Mock the full analysis
        mock_report = NetworkActivityReport(
            timestamp=datetime.utcnow(),
            components=None,
            network_performance_score=0.8,
            ecosystem_vitality_score=0.7,
            overall_activity_score=0.75,
            utilization_category="high",
            recommended_rate_adjustment=-0.05,
            adjustment_confidence=0.85,
            key_metrics={
                'network_tps': 300.0,
                'defi_volume_24h': 5000000.0
            },
            activity_trends=["Strong growth"],
            performance_indicators=["High throughput"],
            risk_warnings=[],
            recommendations=["Maintain current policies"],
            projected_activity={'24h': 0.77, '7d': 0.8, '30d': 0.85},
            capacity_outlook="moderate_growth_expected"
        )

        with patch.object(activity_engine, 'analyze_network_activity', return_value=mock_report):
            summary = await activity_engine.get_activity_summary()

            assert 'overall_activity_score' in summary
            assert 'utilization_category' in summary
            assert 'recommended_rate_adjustment' in summary
            assert 'capacity_outlook' in summary

    def test_export_activity_report(self, activity_engine):
        """Test activity report export"""
        mock_report = NetworkActivityReport(
            timestamp=datetime.utcnow(),
            components=None,
            network_performance_score=0.8,
            ecosystem_vitality_score=0.7,
            overall_activity_score=0.75,
            utilization_category="high",
            recommended_rate_adjustment=-0.05,
            adjustment_confidence=0.85,
            key_metrics={'network_tps': 300.0},
            activity_trends=["Growth"],
            performance_indicators=["High activity"],
            risk_warnings=[],
            recommendations=["Continue monitoring"],
            projected_activity={'24h': 0.77},
            capacity_outlook="stable"
        )

        # Test JSON export
        json_export = activity_engine.export_activity_report(mock_report, 'json')
        assert '"overall_activity_score": 0.75' in json_export
        assert '"utilization_category": "high"' in json_export

        # Test YAML export
        yaml_export = activity_engine.export_activity_report(mock_report, 'yaml')
        assert 'activity_score: 0.75' in yaml_export
        assert 'utilization_category: high' in yaml_export

    # Helper methods to create mock reports
    def _create_mock_network_report(self):
        """Create mock network health report"""
        from core.network_health import (
            NetworkHealthReport, NetworkMetrics, ConsensusHealth, TransactionPoolStatus
        )

        mock_metrics = NetworkMetrics(
            timestamp=datetime.utcnow(),
            current_round=100000,
            last_round_time=datetime.utcnow(),
            transactions_per_second=250.0,
            transactions_in_round=500,
            block_time=4.5,
            block_time_variance=0.5,
            rounds_per_minute=13.3,
            participation_rate=0.92,
            online_stake=7000000000000000,
            total_stake=10000000000000000,
            mempool_size=1500,
            pending_transactions=1500,
            suggested_fee=1000,
            min_fee=1000
        )

        mock_consensus = ConsensusHealth(
            participation_rate=0.92,
            participation_trend="stable",
            consensus_score=0.85,
            online_validators=120,
            total_validators=150,
            validator_distribution={},
            block_production_consistency=0.9,
            missed_blocks=0,
            fork_events=0,
            agreement_time=0.5,
            finality_confidence=0.95
        )

        mock_mempool = TransactionPoolStatus(
            current_size=1500,
            max_size=50000,
            utilization_rate=0.03,
            payment_txns=600,
            app_call_txns=500,
            asset_txns=300,
            key_reg_txns=100,
            average_wait_time=15.0,
            processing_rate=250.0,
            rejected_transactions=0,
            fee_distribution={'min_fee': 1000},
            congestion_factor=0.15
        )

        return NetworkHealthReport(
            timestamp=datetime.utcnow(),
            network_metrics=mock_metrics,
            consensus_health=mock_consensus,
            mempool_status=mock_mempool,
            throughput_score=0.8,
            consensus_score=0.85,
            stability_score=0.9,
            overall_health_score=0.85,
            health_status="good",
            alerts=[],
            recommendations=[],
            performance_trend="stable",
            capacity_utilization=0.5
        )

    def _create_mock_dapp_report(self):
        """Create mock DApp activity report"""
        from core.dapp_activity import (
            DAppActivityReport, SmartContractMetrics, DeFiMetrics,
            NFTActivity, GovernanceActivity
        )

        mock_sc = SmartContractMetrics(
            total_app_calls=25000,
            daily_app_calls=25000,
            unique_apps_used=800,
            top_apps_by_calls=[],
            top_apps_by_users=[],
            new_applications=75,
            app_call_growth=0.15,
            user_adoption_rate=0.12
        )

        mock_defi = DeFiMetrics(
            dex_volume_24h=3000000.0,
            dex_trades_count=2500,
            swap_protocols=[],
            lending_volume_24h=1500000.0,
            borrows_count=200,
            supplies_count=300,
            lending_protocols=[],
            total_liquidity_pools=400,
            total_tvl_usd=200000000.0,
            liquidity_growth=0.08,
            farming_protocols=8,
            staking_volume=30000000.0,
            average_apr=0.10
        )

        mock_nft = NFTActivity(
            total_marketplaces=4,
            daily_sales_count=80,
            daily_sales_volume=25000.0,
            new_collections=8,
            new_nfts_minted=400,
            creator_count=80,
            floor_price_changes={},
            volume_by_marketplace={}
        )

        mock_gov = GovernanceActivity(
            total_participants=80000,
            participation_rate=0.08,
            algo_committed=2000000000.0,
            active_proposals=3,
            votes_cast=50000,
            voting_participation=0.62,
            delegated_stake=400000000.0,
            delegation_rate=0.2
        )

        return DAppActivityReport(
            timestamp=datetime.utcnow(),
            smart_contract_metrics=mock_sc,
            defi_metrics=mock_defi,
            nft_activity=mock_nft,
            governance_activity=mock_gov,
            defi_activity_score=0.7,
            nft_activity_score=0.5,
            governance_activity_score=0.6,
            overall_activity_score=0.65,
            ecosystem_status="active",
            activity_trend="growth",
            growth_indicators=["Strong DeFi growth"],
            recommendations=[]
        )

    def _create_mock_ecosystem_report(self):
        """Create mock ecosystem report"""
        from core.ecosystem_monitor import (
            EcosystemReport, EcosystemGrowth, AdoptionMetrics,
            EcosystemHealth, LongTermTrends
        )

        mock_growth = EcosystemGrowth(
            total_addresses=25000000,
            active_addresses_30d=2500000,
            new_addresses_30d=500000,
            address_growth_rate=0.15,
            total_assets=500000,
            new_assets_30d=12000,
            asset_growth_rate=0.10,
            verified_assets=5000,
            total_applications=15000,
            new_applications_30d=1800,
            application_growth_rate=0.18,
            active_applications=6000,
            total_transactions=2500000000,
            transactions_30d=120000000,
            transaction_growth_rate=0.22
        )

        mock_adoption = AdoptionMetrics(
            developer_count=6000,
            github_activity={'commits': 1800, 'pull_requests': 250},
            new_projects=60,
            documentation_usage=15000,
            enterprise_integrations=80,
            institutional_accounts=180,
            corporate_partnerships=30,
            geographic_distribution={'north_america': 0.35, 'europe': 0.3, 'asia': 0.25, 'other': 0.1},
            global_reach_score=0.75,
            educational_programs=18,
            certification_completions=600,
            community_events=30
        )

        mock_health = EcosystemHealth(
            uptime_percentage=0.9995,
            consensus_health=0.94,
            decentralization_score=0.82,
            market_cap=2800000000.0,
            trading_volume=120000000.0,
            price_stability=0.72,
            code_commits=600,
            active_repositories=120,
            protocol_upgrades=2,
            social_media_engagement={'twitter_followers': 280000},
            forum_activity=1200,
            support_ticket_resolution=0.88
        )

        mock_trends = LongTermTrends(
            growth_1m={'addresses': 0.12, 'transactions': 0.18},
            growth_3m={'addresses': 0.38, 'transactions': 0.55},
            growth_6m={'addresses': 0.85, 'transactions': 1.25},
            growth_1y={'addresses': 1.8, 'transactions': 3.2},
            seasonal_patterns={'q1': 0.23, 'q2': 0.26, 'q3': 0.29, 'q4': 0.22},
            weekly_patterns={},
            daily_patterns={},
            new_use_cases=["DeFi expansion", "Enterprise adoption"],
            protocol_improvements=["Performance optimization"],
            ecosystem_milestones=["Major milestone achieved"]
        )

        return EcosystemReport(
            timestamp=datetime.utcnow(),
            ecosystem_growth=mock_growth,
            adoption_metrics=mock_adoption,
            ecosystem_health=mock_health,
            long_term_trends=mock_trends,
            growth_score=0.75,
            adoption_score=0.68,
            health_score=0.82,
            innovation_score=0.55,
            overall_ecosystem_score=0.7,
            ecosystem_status="healthy",
            key_insights=["Strong growth trajectory"],
            risk_factors=[],
            opportunities=["Enterprise expansion"],
            recommendations=[]
        )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])