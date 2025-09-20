"""
Main Blockchain Behavior Risk Analyzer

Orchestrates all blockchain behavior analysis components to provide
comprehensive risk assessment based on on-chain activity patterns.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

from .models import (
    BehaviorRiskProfile, BehaviorRiskScore, RiskLevel,
    TransactionPattern, WalletCluster, MEVRiskIndicator,
    FlashLoanRisk, BridgeActivityRisk, SybilDetectionResult
)
from .transaction_analyzer import TransactionAnomalyDetector
from .wallet_clustering import WalletClusteringEngine
from .mev_detector import MEVExploitationDetector

logger = logging.getLogger(__name__)


class BlockchainBehaviorAnalyzer:
    """
    Main analyzer for blockchain behavior risk assessment
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

        # Initialize component analyzers
        self.transaction_analyzer = TransactionAnomalyDetector(self.config.get('transaction_analyzer', {}))
        self.wallet_clustering = WalletClusteringEngine(self.config.get('wallet_clustering', {}))
        self.mev_detector = MEVExploitationDetector(self.config.get('mev_detector', {}))

        # Risk scoring weights
        self.risk_weights = self.config.get('risk_weights', {
            'transaction_anomaly': 0.20,
            'wallet_clustering': 0.15,
            'mev_exploitation': 0.25,
            'flash_loan_risk': 0.15,
            'bridge_activity': 0.10,
            'sybil_attack': 0.15
        })

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for behavior analysis"""
        return {
            'analysis_window_days': 30,
            'min_transaction_count': 10,
            'risk_thresholds': {
                'low': 25,
                'medium': 50,
                'high': 75
            },
            'enable_advanced_detection': True,
            'data_sources': ['indexer', 'node', 'analytics_api']
        }

    async def analyze_address_behavior(
        self,
        address: str,
        historical_days: int = 30,
        include_related_addresses: bool = True
    ) -> BehaviorRiskProfile:
        """
        Perform comprehensive blockchain behavior risk analysis

        Args:
            address: Algorand address to analyze
            historical_days: Days of history to analyze
            include_related_addresses: Whether to include related address analysis

        Returns:
            Complete behavior risk profile
        """
        try:
            logger.info(f"Starting behavior analysis for address: {address}")

            # Get base account information
            account_info = await self._get_account_info(address)

            # Run parallel analysis components
            analysis_tasks = [
                self._analyze_transaction_patterns(address, historical_days),
                self._analyze_wallet_clustering(address, include_related_addresses),
                self._detect_mev_exploitation(address, historical_days),
                self._analyze_flash_loan_activity(address, historical_days),
                self._analyze_bridge_activity(address, historical_days),
                self._detect_sybil_behavior(address, include_related_addresses)
            ]

            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            # Parse results
            transaction_patterns = results[0] if not isinstance(results[0], Exception) else []
            wallet_clusters = results[1] if not isinstance(results[1], Exception) else []
            mev_indicators = results[2] if not isinstance(results[2], Exception) else []
            flash_loan_activities = results[3] if not isinstance(results[3], Exception) else []
            bridge_activities = results[4] if not isinstance(results[4], Exception) else []
            sybil_detection = results[5] if not isinstance(results[5], Exception) else None

            # Calculate risk score
            risk_score = self._calculate_behavior_risk_score(
                transaction_patterns, wallet_clusters, mev_indicators,
                flash_loan_activities, bridge_activities, sybil_detection
            )

            # Create comprehensive profile
            profile = BehaviorRiskProfile(
                address=address,
                assessment_timestamp=datetime.utcnow(),
                transaction_patterns=transaction_patterns,
                wallet_clusters=wallet_clusters,
                mev_indicators=mev_indicators,
                flash_loan_activities=flash_loan_activities,
                bridge_activities=bridge_activities,
                sybil_detection=sybil_detection,
                risk_score=risk_score,
                account_age_days=account_info.get('age_days', 0),
                total_transaction_count=account_info.get('transaction_count', 0),
                total_volume_algo=account_info.get('total_volume', 0.0),
                unique_counterparties=account_info.get('unique_counterparties', 0),
                app_interactions=account_info.get('app_interactions', []),
                data_sources=self.config['data_sources'],
                analysis_version="1.0.0",
                limitations=self._get_analysis_limitations()
            )

            logger.info(f"Behavior analysis completed. Risk level: {risk_score.risk_level.value}")
            return profile

        except Exception as e:
            logger.error(f"Error in behavior analysis for {address}: {e}")
            raise

    async def _analyze_transaction_patterns(
        self,
        address: str,
        days: int
    ) -> List[TransactionPattern]:
        """Analyze transaction patterns for anomaly detection"""
        try:
            return await self.transaction_analyzer.detect_anomalies(address, days)
        except Exception as e:
            logger.error(f"Transaction pattern analysis failed: {e}")
            return []

    async def _analyze_wallet_clustering(
        self,
        address: str,
        include_related: bool
    ) -> List[WalletCluster]:
        """Analyze wallet clustering and relationships"""
        try:
            return await self.wallet_clustering.analyze_clusters(address, include_related)
        except Exception as e:
            logger.error(f"Wallet clustering analysis failed: {e}")
            return []

    async def _detect_mev_exploitation(
        self,
        address: str,
        days: int
    ) -> List[MEVRiskIndicator]:
        """Detect MEV exploitation patterns"""
        try:
            return await self.mev_detector.detect_mev_activity(address, days)
        except Exception as e:
            logger.error(f"MEV detection failed: {e}")
            return []

    async def _analyze_flash_loan_activity(
        self,
        address: str,
        days: int
    ) -> List[FlashLoanRisk]:
        """Analyze flash loan usage patterns"""
        try:
            # Flash loan analysis logic
            flash_loans = await self._get_flash_loan_transactions(address, days)
            return [self._assess_flash_loan_risk(loan) for loan in flash_loans]
        except Exception as e:
            logger.error(f"Flash loan analysis failed: {e}")
            return []

    async def _analyze_bridge_activity(
        self,
        address: str,
        days: int
    ) -> List[BridgeActivityRisk]:
        """Analyze cross-chain bridge activity"""
        try:
            # Bridge activity analysis logic
            bridge_txns = await self._get_bridge_transactions(address, days)
            return [self._assess_bridge_risk(txn) for txn in bridge_txns]
        except Exception as e:
            logger.error(f"Bridge activity analysis failed: {e}")
            return []

    async def _detect_sybil_behavior(
        self,
        address: str,
        include_related: bool
    ) -> Optional[SybilDetectionResult]:
        """Detect potential sybil attack patterns"""
        try:
            # Sybil detection logic would go here
            # This is a placeholder for the complex sybil detection algorithm
            return None
        except Exception as e:
            logger.error(f"Sybil detection failed: {e}")
            return None

    def _calculate_behavior_risk_score(
        self,
        transaction_patterns: List[TransactionPattern],
        wallet_clusters: List[WalletCluster],
        mev_indicators: List[MEVRiskIndicator],
        flash_loan_activities: List[FlashLoanRisk],
        bridge_activities: List[BridgeActivityRisk],
        sybil_detection: Optional[SybilDetectionResult]
    ) -> BehaviorRiskScore:
        """Calculate comprehensive behavior risk score"""

        # Calculate component scores (0-100)
        transaction_score = self._score_transaction_anomalies(transaction_patterns)
        clustering_score = self._score_wallet_clustering(wallet_clusters)
        mev_score = self._score_mev_risk(mev_indicators)
        flash_loan_score = self._score_flash_loan_risk(flash_loan_activities)
        bridge_score = self._score_bridge_risk(bridge_activities)
        sybil_score = self._score_sybil_risk(sybil_detection)

        # Calculate weighted overall score
        overall_score = (
            transaction_score * self.risk_weights['transaction_anomaly'] +
            clustering_score * self.risk_weights['wallet_clustering'] +
            mev_score * self.risk_weights['mev_exploitation'] +
            flash_loan_score * self.risk_weights['flash_loan_risk'] +
            bridge_score * self.risk_weights['bridge_activity'] +
            sybil_score * self.risk_weights['sybil_attack']
        )

        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)

        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(overall_score)

        # Generate risk factors and recommendations
        risk_factors = self._identify_risk_factors(
            transaction_score, clustering_score, mev_score,
            flash_loan_score, bridge_score, sybil_score
        )

        mitigation_recommendations = self._generate_mitigation_recommendations(risk_factors)
        monitoring_priorities = self._generate_monitoring_priorities(risk_factors)

        return BehaviorRiskScore(
            transaction_anomaly_score=transaction_score,
            wallet_clustering_risk=clustering_score,
            mev_exploitation_risk=mev_score,
            flash_loan_risk=flash_loan_score,
            bridge_activity_risk=bridge_score,
            sybil_attack_risk=sybil_score,
            overall_score=overall_score,
            risk_level=risk_level,
            confidence_interval=confidence_interval,
            risk_factors=risk_factors,
            mitigation_recommendations=mitigation_recommendations,
            monitoring_priorities=monitoring_priorities
        )

    def _score_transaction_anomalies(self, patterns: List[TransactionPattern]) -> float:
        """Score transaction anomaly risk"""
        if not patterns:
            return 10.0  # Low risk baseline

        # Calculate risk based on pattern severity and frequency
        high_risk_patterns = [p for p in patterns if 'high_frequency' in p.risk_indicators or 'unusual_timing' in p.risk_indicators]
        avg_confidence = np.mean([p.confidence_score for p in patterns]) if patterns else 0.5

        base_score = min(len(high_risk_patterns) * 15, 70)
        confidence_adjustment = base_score * avg_confidence

        return min(confidence_adjustment, 100.0)

    def _score_wallet_clustering(self, clusters: List[WalletCluster]) -> float:
        """Score wallet clustering risk"""
        if not clusters:
            return 5.0

        sybil_clusters = [c for c in clusters if c.cluster_type == "sybil"]
        high_correlation_clusters = [c for c in clusters if c.transaction_timing_correlation > 0.8]

        risk_score = len(sybil_clusters) * 30 + len(high_correlation_clusters) * 15
        return min(risk_score, 100.0)

    def _score_mev_risk(self, indicators: List[MEVRiskIndicator]) -> float:
        """Score MEV exploitation risk"""
        if not indicators:
            return 5.0

        critical_mev = [i for i in indicators if i.impact_severity == RiskLevel.CRITICAL]
        high_mev = [i for i in indicators if i.impact_severity == RiskLevel.HIGH]

        risk_score = len(critical_mev) * 40 + len(high_mev) * 25
        return min(risk_score, 100.0)

    def _score_flash_loan_risk(self, activities: List[FlashLoanRisk]) -> float:
        """Score flash loan activity risk"""
        if not activities:
            return 0.0

        failed_loans = [a for a in activities if not a.repayment_success]
        high_complexity = [a for a in activities if a.complexity_score > 0.8]

        risk_score = len(failed_loans) * 50 + len(high_complexity) * 20
        return min(risk_score, 100.0)

    def _score_bridge_risk(self, activities: List[BridgeActivityRisk]) -> float:
        """Score bridge activity risk"""
        if not activities:
            return 0.0

        high_risk_bridges = [a for a in activities if a.current_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        risk_score = len(high_risk_bridges) * 30
        return min(risk_score, 100.0)

    def _score_sybil_risk(self, detection: Optional[SybilDetectionResult]) -> float:
        """Score sybil attack risk"""
        if not detection:
            return 0.0

        return detection.confidence_level * 100

    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from numerical score"""
        thresholds = self.config['risk_thresholds']

        if score <= thresholds['low']:
            return RiskLevel.LOW
        elif score <= thresholds['medium']:
            return RiskLevel.MEDIUM
        elif score <= thresholds['high']:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _calculate_confidence_interval(self, score: float) -> tuple:
        """Calculate confidence interval for risk score"""
        # Simple confidence interval calculation
        # In production, this would be more sophisticated
        margin = score * 0.1  # 10% margin
        return (max(0, score - margin), min(100, score + margin))

    def _identify_risk_factors(self, *scores) -> List[str]:
        """Identify primary risk factors"""
        factors = []
        score_names = [
            'transaction_anomaly', 'wallet_clustering', 'mev_exploitation',
            'flash_loan_risk', 'bridge_activity', 'sybil_attack'
        ]

        for score, name in zip(scores, score_names):
            if score > 50:
                factors.append(f"High {name.replace('_', ' ')} risk detected")

        return factors

    def _generate_mitigation_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        if any('transaction' in factor for factor in risk_factors):
            recommendations.append("Implement transaction pattern monitoring")

        if any('mev' in factor for factor in risk_factors):
            recommendations.append("Monitor for MEV exploitation patterns")

        if any('sybil' in factor for factor in risk_factors):
            recommendations.append("Verify identity and implement KYC measures")

        return recommendations

    def _generate_monitoring_priorities(self, risk_factors: List[str]) -> List[str]:
        """Generate monitoring priorities"""
        priorities = []

        if risk_factors:
            priorities.append("Continuous transaction monitoring")
            priorities.append("Real-time risk score updates")
            priorities.append("Cross-reference with other risk engines")

        return priorities

    def _get_analysis_limitations(self) -> List[str]:
        """Get current analysis limitations"""
        return [
            "Analysis based on on-chain data only",
            "Limited historical depth may affect accuracy",
            "Cross-chain activity detection is experimental",
            "Sybil detection requires network-wide analysis"
        ]

    async def _get_account_info(self, address: str) -> Dict[str, Any]:
        """Get basic account information"""
        # Placeholder - would connect to Algorand indexer/node
        return {
            'age_days': 365,
            'transaction_count': 1250,
            'total_volume': 50000.0,
            'unique_counterparties': 45,
            'app_interactions': [123, 456, 789]
        }

    async def _get_flash_loan_transactions(self, address: str, days: int) -> List[Dict]:
        """Get flash loan transactions"""
        # Placeholder for flash loan detection
        return []

    async def _get_bridge_transactions(self, address: str, days: int) -> List[Dict]:
        """Get bridge transactions"""
        # Placeholder for bridge transaction detection
        return []

    def _assess_flash_loan_risk(self, loan: Dict) -> FlashLoanRisk:
        """Assess individual flash loan risk"""
        # Placeholder implementation
        from .models import FlashLoanRisk
        return FlashLoanRisk(
            loan_amount=loan.get('amount', 0),
            loan_asset_id=loan.get('asset_id', 0),
            borrower_address=loan.get('borrower', ''),
            repayment_success=loan.get('success', True),
            arbitrage_profit=loan.get('profit', 0),
            protocols_involved=loan.get('protocols', []),
            execution_time_ms=loan.get('execution_time', 1000),
            complexity_score=loan.get('complexity', 0.5),
            risk_level=RiskLevel.LOW
        )

    def _assess_bridge_risk(self, txn: Dict) -> BridgeActivityRisk:
        """Assess individual bridge transaction risk"""
        # Placeholder implementation
        from .models import BridgeActivityRisk
        return BridgeActivityRisk(
            bridge_protocol=txn.get('protocol', ''),
            source_chain=txn.get('source', 'algorand'),
            destination_chain=txn.get('destination', 'ethereum'),
            transfer_amount=txn.get('amount', 0),
            transfer_asset=txn.get('asset', 'ALGO'),
            bridge_liquidity_depth=txn.get('liquidity', 1000000),
            slippage_tolerance=txn.get('slippage', 0.01),
            time_to_finality_minutes=txn.get('finality_time', 10),
            validator_set_size=txn.get('validators', 21),
            historical_exploit_count=txn.get('exploits', 0),
            current_risk_level=RiskLevel.LOW
        )