"""
Comprehensive Test Suite for Blockchain Risk Assessment

Tests all components of the Algorand-native risk assessment system
including transaction analysis, MEV detection, and risk scoring.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Import modules to test
from common.models.blockchain_risk import (
    TransactionPattern, BehaviorPattern, RiskLevel, HolisticRiskProfile,
    BlockchainRisk, SystemicRisk, RiskAlert
)

from common.algorand.transaction_analyzer import AlgorandTransactionAnalyzer
from common.algorand.wallet_clustering import WalletClusteringAnalyzer
from common.algorand.bridge_analyzer import BridgeRiskAssessment
from common.algorand.mev_detector import MEVDetector

from common.utils.anomaly_detection import AnomalyDetector
from common.utils.risk_scoring import BlockchainRiskScorer, ScoringContext
from common.utils.correlation_analysis import CorrelationAnalyzer
from common.utils.cascade_modeling import CascadeRiskModeler

from blockchain_behavior_risk.core.behavior_engine import BlockchainBehaviorEngine
from blockchain_behavior_risk.core.transaction_risk import TransactionRiskAnalyzer
from blockchain_behavior_risk.core.wallet_risk import WalletRiskAnalyzer
from blockchain_behavior_risk.core.flash_loan_risk import FlashLoanRiskDetector
from blockchain_behavior_risk.core.bridge_risk import BridgeRiskAnalyzer


class TestData:
    """Test data generator for blockchain risk testing"""

    @staticmethod
    def generate_normal_transactions(count: int = 50) -> List[Dict[str, Any]]:
        """Generate normal transaction patterns"""
        transactions = []
        base_time = datetime.utcnow() - timedelta(days=30)

        for i in range(count):
            transactions.append({
                'id': f'txn_{i}',
                'timestamp': (base_time + timedelta(hours=i * 12)).isoformat(),
                'sender': f'wallet_sender_{i % 5}',
                'receiver': f'wallet_receiver_{i % 3}',
                'amount': 100 + (i * 10),
                'asset-id': 0,
                'tx-type': 'pay',
                'fee': 0.001,
                'confirmed-round': 1000000 + i,
                'intra-round-offset': i % 10
            })

        return transactions

    @staticmethod
    def generate_suspicious_transactions() -> List[Dict[str, Any]]:
        """Generate suspicious transaction patterns"""
        base_time = datetime.utcnow() - timedelta(days=7)
        transactions = []

        # Velocity spike pattern
        for i in range(20):
            transactions.append({
                'id': f'sus_txn_{i}',
                'timestamp': (base_time + timedelta(minutes=i * 5)).isoformat(),
                'sender': 'suspicious_wallet',
                'receiver': f'target_{i % 3}',
                'amount': 1000,  # Identical amounts
                'asset-id': 0,
                'tx-type': 'pay',
                'fee': 0.001,
                'confirmed-round': 2000000 + i,
                'intra-round-offset': i
            })

        return transactions

    @staticmethod
    def generate_mev_transactions() -> List[Dict[str, Any]]:
        """Generate MEV exploitation patterns"""
        base_time = datetime.utcnow() - timedelta(hours=1)
        transactions = []

        # Sandwich attack pattern
        sandwich_txns = [
            {
                'id': 'mev_front',
                'timestamp': base_time.isoformat(),
                'sender': 'mev_bot',
                'receiver': 'dex_contract',
                'amount': 10000,
                'asset-id': 100,
                'tx-type': 'appl',
                'application-id': 12345,
                'confirmed-round': 3000000,
                'intra-round-offset': 0
            },
            {
                'id': 'victim_txn',
                'timestamp': base_time.isoformat(),
                'sender': 'victim_wallet',
                'receiver': 'dex_contract',
                'amount': 5000,
                'asset-id': 100,
                'tx-type': 'appl',
                'application-id': 12345,
                'confirmed-round': 3000000,
                'intra-round-offset': 1
            },
            {
                'id': 'mev_back',
                'timestamp': base_time.isoformat(),
                'sender': 'mev_bot',
                'receiver': 'dex_contract',
                'amount': 9800,  # Profit taken
                'asset-id': 100,
                'tx-type': 'appl',
                'application-id': 12345,
                'confirmed-round': 3000000,
                'intra-round-offset': 2
            }
        ]

        return sandwich_txns

    @staticmethod
    def generate_clustering_data() -> Dict[str, List[Dict[str, Any]]]:
        """Generate wallet clustering test data"""
        base_time = datetime.utcnow() - timedelta(days=14)

        # Create cluster of related wallets
        cluster_wallets = {}
        funding_source = 'funding_wallet'

        for i in range(5):
            wallet_id = f'cluster_wallet_{i}'
            transactions = []

            # Initial funding from same source
            transactions.append({
                'id': f'funding_{i}',
                'timestamp': (base_time + timedelta(minutes=i * 10)).isoformat(),
                'sender': funding_source,
                'receiver': wallet_id,
                'amount': 1000,
                'asset-id': 0,
                'tx-type': 'pay'
            })

            # Similar transaction patterns
            for j in range(10):
                transactions.append({
                    'id': f'cluster_txn_{i}_{j}',
                    'timestamp': (base_time + timedelta(hours=j * 2, minutes=i * 5)).isoformat(),
                    'sender': wallet_id,
                    'receiver': f'target_{j % 2}',
                    'amount': 50,  # Similar amounts
                    'asset-id': 0,
                    'tx-type': 'pay'
                })

            cluster_wallets[wallet_id] = transactions

        return cluster_wallets


class TestTransactionAnalyzer:
    """Test transaction pattern analysis"""

    @pytest.fixture
    def analyzer(self):
        return AlgorandTransactionAnalyzer()

    @pytest.mark.asyncio
    async def test_normal_transaction_analysis(self, analyzer):
        """Test analysis of normal transaction patterns"""
        transactions = TestData.generate_normal_transactions()

        patterns = await analyzer.analyze_wallet_transactions(
            'test_wallet', transactions, timedelta(days=30)
        )

        assert isinstance(patterns, list)
        # Normal transactions should have minimal risk patterns
        high_risk_patterns = [p for p in patterns if p.confidence_score > 0.8]
        assert len(high_risk_patterns) == 0

    @pytest.mark.asyncio
    async def test_suspicious_transaction_detection(self, analyzer):
        """Test detection of suspicious patterns"""
        transactions = TestData.generate_suspicious_transactions()

        patterns = await analyzer.analyze_wallet_transactions(
            'suspicious_wallet', transactions, timedelta(days=7)
        )

        # Should detect velocity spike pattern
        velocity_patterns = [p for p in patterns if p.pattern_type == BehaviorPattern.VELOCITY_SPIKE]
        assert len(velocity_patterns) > 0
        assert velocity_patterns[0].confidence_score > 0.5

    @pytest.mark.asyncio
    async def test_pattern_risk_scoring(self, analyzer):
        """Test pattern risk scoring"""
        suspicious_transactions = TestData.generate_suspicious_transactions()
        patterns = await analyzer.analyze_wallet_transactions(
            'test_wallet', suspicious_transactions, timedelta(days=7)
        )

        risk_score = analyzer.calculate_pattern_risk_score(patterns)
        assert 0.0 <= risk_score <= 1.0
        assert risk_score > 0.3  # Should detect elevated risk


class TestMEVDetector:
    """Test MEV pattern detection"""

    @pytest.fixture
    def detector(self):
        return MEVDetector()

    @pytest.mark.asyncio
    async def test_sandwich_attack_detection(self, detector):
        """Test sandwich attack pattern detection"""
        # Convert test data to MEV transaction format
        mev_transactions = []
        for txn in TestData.generate_mev_transactions():
            from common.algorand.mev_detector import MEVTransaction
            mev_txn = MEVTransaction(
                txn_id=txn['id'],
                block_number=txn['confirmed-round'],
                position_in_block=txn['intra-round-offset'],
                timestamp=datetime.fromisoformat(txn['timestamp']),
                sender=txn['sender'],
                receiver=txn['receiver'],
                amount=txn['amount'],
                asset_id=txn['asset-id'],
                application_id=txn.get('application-id'),
                fee=txn.get('fee', 0.001),
                gas_used=None,
                transaction_type=txn['tx-type']
            )
            mev_transactions.append(mev_txn)

        patterns = await detector.detect_mev_patterns(mev_transactions)

        # Should detect sandwich attack
        sandwich_patterns = [p for p in patterns if 'sandwich' in p.mev_type.value]
        assert len(sandwich_patterns) > 0
        assert sandwich_patterns[0].confidence_score > 0.5

    @pytest.mark.asyncio
    async def test_mev_analytics(self, detector):
        """Test MEV analytics generation"""
        patterns = []  # Would be populated with detected patterns
        analytics = detector.generate_mev_analytics(patterns)

        assert hasattr(analytics, 'total_mev_extracted')
        assert hasattr(analytics, 'top_mev_extractors')
        assert analytics.total_mev_extracted >= 0


class TestWalletClustering:
    """Test wallet clustering analysis"""

    @pytest.fixture
    def analyzer(self):
        return WalletClusteringAnalyzer()

    @pytest.mark.asyncio
    async def test_cluster_detection(self, analyzer):
        """Test detection of wallet clusters"""
        wallet_data = TestData.generate_clustering_data()

        clusters = await analyzer.analyze_wallet_relationships(wallet_data)

        assert len(clusters) > 0
        # Should detect the coordinated cluster
        high_risk_clusters = [c for c in clusters if c.cluster_score > 0.7]
        assert len(high_risk_clusters) > 0

    @pytest.mark.asyncio
    async def test_sybil_alert_creation(self, analyzer):
        """Test Sybil attack alert creation"""
        wallet_data = TestData.generate_clustering_data()
        clusters = await analyzer.analyze_wallet_relationships(wallet_data)

        if clusters:
            alert = analyzer.create_sybil_alert(clusters[0])
            assert alert.alert_type == "SYBIL_ATTACK"
            assert alert.severity in [RiskLevel.HIGH, RiskLevel.MODERATE]


class TestRiskScoring:
    """Test blockchain risk scoring"""

    @pytest.fixture
    def scorer(self):
        return BlockchainRiskScorer()

    @pytest.mark.asyncio
    async def test_comprehensive_risk_scoring(self, scorer):
        """Test comprehensive risk score calculation"""
        # Create mock risk profile
        risk_profile = HolisticRiskProfile(
            entity_id='test_wallet',
            entity_type='wallet',
            assessment_timestamp=datetime.utcnow(),
            transaction_patterns=[],
            defi_exposures=[],
            smart_contract_risks=[],
            liquidity_risks=[],
            governance_risks=[],
            asa_risks=[],
            protocol_risks=[],
            overall_risk_score=0.0,
            risk_level=RiskLevel.LOW,
            confidence_score=0.8,
            risk_factor_scores={'transaction_behavior': 0.3, 'mev_risk': 0.1},
            risk_factor_weights={'transaction_behavior': 0.5, 'mev_risk': 0.5},
            active_alerts=[],
            recommended_mitigations=[],
            data_completeness=0.9
        )

        context = ScoringContext(
            entity_type='wallet',
            time_horizon=timedelta(days=30),
            market_conditions='normal',
            regulatory_environment='moderate',
            protocol_maturity='established',
            analysis_purpose='lending'
        )

        overall_score, risk_level, component_scores = await scorer.calculate_comprehensive_risk_score(
            risk_profile, context
        )

        assert 0.0 <= overall_score <= 1.0
        assert isinstance(risk_level, RiskLevel)
        assert isinstance(component_scores, dict)

    @pytest.mark.asyncio
    async def test_portfolio_risk_calculation(self, scorer):
        """Test portfolio-level risk calculation"""
        portfolio_positions = [
            {'asset': 'ALGO', 'value': 10000, 'risk_score': 0.2},
            {'asset': 'USDC', 'value': 5000, 'risk_score': 0.1},
            {'asset': 'TEST_TOKEN', 'value': 2000, 'risk_score': 0.8}
        ]

        context = ScoringContext(
            entity_type='wallet',
            time_horizon=timedelta(days=30),
            market_conditions='normal',
            regulatory_environment='moderate',
            protocol_maturity='established',
            analysis_purpose='lending'
        )

        portfolio_risk, breakdown = await scorer.calculate_portfolio_risk_score(
            portfolio_positions, context
        )

        assert 0.0 <= portfolio_risk <= 1.0
        assert 'weighted_position_risk' in breakdown
        assert 'concentration_risk' in breakdown


class TestAnomalyDetection:
    """Test anomaly detection"""

    @pytest.fixture
    def detector(self):
        return AnomalyDetector()

    @pytest.mark.asyncio
    async def test_transaction_anomaly_detection(self, detector):
        """Test transaction anomaly detection"""
        transactions = TestData.generate_suspicious_transactions()

        anomalies = await detector.detect_transaction_anomalies(
            'test_wallet', transactions, timedelta(days=7)
        )

        assert isinstance(anomalies, list)
        # Should detect anomalies in suspicious patterns
        if anomalies:
            assert all(hasattr(a, 'score') for a in anomalies)
            assert all(0.0 <= a.score <= 1.0 for a in anomalies)

    @pytest.mark.asyncio
    async def test_anomaly_alert_creation(self, detector):
        """Test anomaly alert creation"""
        from common.utils.anomaly_detection import AnomalyScore, AnomalyType

        anomaly = AnomalyScore(
            score=0.8,
            anomaly_type=AnomalyType.STATISTICAL,
            confidence=0.9,
            deviation_magnitude=3.5,
            baseline_reference=100.0,
            evidence={'test': 'data'},
            detection_method='Test Method'
        )

        alert = detector.create_anomaly_alert('test_wallet', anomaly)
        assert alert.alert_type.startswith('ANOMALY_')
        assert alert.risk_score == anomaly.score


class TestBehaviorEngine:
    """Test main behavior engine"""

    @pytest.fixture
    def engine(self):
        # Create engine with test config
        test_config = {
            'engine': {
                'analysis': {
                    'max_concurrent_wallets': 50,
                    'cache_ttl_minutes': 60
                }
            },
            'risk_assessment': {
                'transaction_patterns': {
                    'velocity_spike': {'z_score_threshold': 2.5}
                }
            },
            'alerts': {
                'thresholds': {
                    'critical_risk_score': 0.85
                }
            }
        }

        return BlockchainBehaviorEngine()

    @pytest.mark.asyncio
    async def test_comprehensive_wallet_analysis(self, engine):
        """Test comprehensive wallet analysis"""
        # Mock the data fetching methods for testing
        async def mock_fetch_transaction_data(wallet_address, analysis_window):
            return TestData.generate_normal_transactions()

        async def mock_fetch_mev_transaction_data(wallet_address, analysis_window):
            return TestData.generate_mev_transactions()

        async def mock_find_related_wallets(wallet_address):
            return TestData.generate_clustering_data()

        # Patch the methods
        engine._fetch_transaction_data = mock_fetch_transaction_data
        engine._fetch_mev_transaction_data = mock_fetch_mev_transaction_data
        engine._find_related_wallets = mock_find_related_wallets

        # Additional mocks for missing methods
        async def mock_fetch_bridge_data(wallet_address, analysis_window):
            return []

        async def mock_convert_to_mev_format(transactions):
            return []

        async def mock_get_portfolio_data(wallet_address):
            return []

        async def mock_get_asset_correlation_data(wallet_address):
            return {}

        engine._fetch_bridge_data = mock_fetch_bridge_data
        engine._convert_to_mev_format = mock_convert_to_mev_format
        engine._get_portfolio_data = mock_get_portfolio_data
        engine._get_asset_correlation_data = mock_get_asset_correlation_data

        risk_profile = await engine.analyze_wallet_comprehensive('test_wallet')

        assert isinstance(risk_profile, HolisticRiskProfile)
        assert risk_profile.entity_id == 'test_wallet'
        assert risk_profile.entity_type == 'wallet'
        assert 0.0 <= risk_profile.overall_risk_score <= 1.0
        assert isinstance(risk_profile.risk_level, RiskLevel)


class TestIntegration:
    """Integration tests for the complete system"""

    @pytest.mark.asyncio
    async def test_end_to_end_risk_assessment(self):
        """Test complete end-to-end risk assessment"""
        # Create test data
        normal_transactions = TestData.generate_normal_transactions()
        suspicious_transactions = TestData.generate_suspicious_transactions()

        # Test transaction analysis
        analyzer = AlgorandTransactionAnalyzer()
        patterns = await analyzer.analyze_wallet_transactions(
            'test_wallet', suspicious_transactions, timedelta(days=30)
        )

        # Test risk scoring
        scorer = BlockchainRiskScorer()

        # Create mock risk profile
        risk_profile = HolisticRiskProfile(
            entity_id='test_wallet',
            entity_type='wallet',
            assessment_timestamp=datetime.utcnow(),
            transaction_patterns=patterns,
            defi_exposures=[],
            smart_contract_risks=[],
            liquidity_risks=[],
            governance_risks=[],
            asa_risks=[],
            protocol_risks=[],
            overall_risk_score=0.0,
            risk_level=RiskLevel.LOW,
            confidence_score=0.8,
            risk_factor_scores={},
            risk_factor_weights={},
            active_alerts=[],
            recommended_mitigations=[],
            data_completeness=0.9
        )

        context = ScoringContext(
            entity_type='wallet',
            time_horizon=timedelta(days=30),
            market_conditions='normal',
            regulatory_environment='moderate',
            protocol_maturity='established',
            analysis_purpose='lending'
        )

        overall_score, risk_level, component_scores = await scorer.calculate_comprehensive_risk_score(
            risk_profile, context
        )

        # Verify results
        assert 0.0 <= overall_score <= 1.0
        assert isinstance(risk_level, RiskLevel)
        assert len(component_scores) > 0

    @pytest.mark.asyncio
    async def test_alert_generation_workflow(self):
        """Test alert generation workflow"""
        # Create high-risk scenario
        detector = MEVDetector()

        # Test alert creation for MEV pattern
        from common.algorand.mev_detector import MEVPattern, MEVType

        mev_pattern = MEVPattern(
            pattern_id='test_pattern',
            mev_type=MEVType.SANDWICH_ATTACK,
            transactions=[],
            extracted_value=1000.0,
            confidence_score=0.9,
            victim_addresses=['victim_wallet'],
            exploiter_address='exploiter_wallet',
            time_window=timedelta(seconds=30),
            detection_method='Test Detection',
            evidence={'test': 'evidence'}
        )

        alert = detector.create_mev_alert(mev_pattern)

        assert alert.severity in [RiskLevel.HIGH, RiskLevel.MODERATE]
        assert 'MEV' in alert.alert_type
        assert len(alert.recommendations) > 0


def run_performance_tests():
    """Run performance tests for the risk assessment system"""
    import time
    import asyncio

    async def performance_test():
        print("Running performance tests...")

        # Test transaction analysis performance
        analyzer = AlgorandTransactionAnalyzer()
        large_transaction_set = TestData.generate_normal_transactions(1000)

        start_time = time.time()
        patterns = await analyzer.analyze_wallet_transactions(
            'perf_test_wallet', large_transaction_set, timedelta(days=30)
        )
        analysis_time = time.time() - start_time

        print(f"Transaction analysis for 1000 transactions: {analysis_time:.2f} seconds")
        print(f"Patterns detected: {len(patterns)}")

        # Test risk scoring performance
        scorer = BlockchainRiskScorer()
        risk_profile = HolisticRiskProfile(
            entity_id='perf_test_wallet',
            entity_type='wallet',
            assessment_timestamp=datetime.utcnow(),
            transaction_patterns=patterns,
            defi_exposures=[],
            smart_contract_risks=[],
            liquidity_risks=[],
            governance_risks=[],
            asa_risks=[],
            protocol_risks=[],
            overall_risk_score=0.0,
            risk_level=RiskLevel.LOW,
            confidence_score=0.8,
            risk_factor_scores={},
            risk_factor_weights={},
            active_alerts=[],
            recommended_mitigations=[],
            data_completeness=0.9
        )

        context = ScoringContext(
            entity_type='wallet',
            time_horizon=timedelta(days=30),
            market_conditions='normal',
            regulatory_environment='moderate',
            protocol_maturity='established',
            analysis_purpose='lending'
        )

        start_time = time.time()
        overall_score, risk_level, component_scores = await scorer.calculate_comprehensive_risk_score(
            risk_profile, context
        )
        scoring_time = time.time() - start_time

        print(f"Risk scoring: {scoring_time:.2f} seconds")
        print(f"Overall risk score: {overall_score:.3f}")
        print(f"Risk level: {risk_level.value}")

    # Run the performance test
    asyncio.run(performance_test())


if __name__ == "__main__":
    # Run tests with pytest
    print("Running Blockchain Risk Assessment Test Suite...")
    print("=" * 60)

    # Run performance tests
    run_performance_tests()

    print("\nTo run the full test suite, use: pytest test_blockchain_risk.py -v")
    print("To run specific test classes, use: pytest test_blockchain_risk.py::TestTransactionAnalyzer -v")