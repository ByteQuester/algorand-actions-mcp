"""
Blockchain Behavior Risk Engine

Main engine for orchestrating blockchain behavior pattern analysis
and risk assessment across multiple components.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
import yaml
from pathlib import Path

from ..common.models.blockchain_risk import (
    HolisticRiskProfile, RiskLevel, RiskAlert, SystemicRisk
)
from ..common.algorand.transaction_analyzer import AlgorandTransactionAnalyzer
from ..common.algorand.wallet_clustering import WalletClusteringAnalyzer
from ..common.algorand.bridge_analyzer import BridgeRiskAssessment
from ..common.algorand.mev_detector import MEVDetector
from ..common.utils.anomaly_detection import AnomalyDetector
from ..common.utils.risk_scoring import BlockchainRiskScorer, ScoringContext
from ..common.utils.correlation_analysis import CorrelationAnalyzer
from ..common.utils.cascade_modeling import CascadeRiskModeler

from .transaction_risk import TransactionRiskAnalyzer
from .wallet_risk import WalletRiskAnalyzer
from .flash_loan_risk import FlashLoanRiskDetector
from .bridge_risk import BridgeRiskAnalyzer


@dataclass
class EngineConfig:
    """Configuration for the behavior engine"""
    max_concurrent_analyses: int
    analysis_timeout_seconds: int
    cache_enabled: bool
    cache_ttl_minutes: int
    enable_real_time_monitoring: bool
    alert_thresholds: Dict[str, float]


class BlockchainBehaviorEngine:
    """
    Main blockchain behavior risk assessment engine

    Orchestrates various risk analyzers and provides comprehensive
    risk assessment for Algorand blockchain entities.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize components
        self.transaction_analyzer = AlgorandTransactionAnalyzer()
        self.wallet_clustering = WalletClusteringAnalyzer()
        self.bridge_analyzer = BridgeRiskAssessment()
        self.mev_detector = MEVDetector()
        self.anomaly_detector = AnomalyDetector()
        self.risk_scorer = BlockchainRiskScorer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.cascade_modeler = CascadeRiskModeler()

        # Initialize specialized analyzers
        self.transaction_risk = TransactionRiskAnalyzer(self.config)
        self.wallet_risk = WalletRiskAnalyzer(self.config)
        self.flash_loan_risk = FlashLoanRiskDetector(self.config)
        self.bridge_risk = BridgeRiskAnalyzer(self.config)

        # Analysis cache
        self.analysis_cache = {}
        self.cache_timestamps = {}

        # Active monitoring
        self.monitoring_tasks = {}
        self.alert_handlers = []

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'engine': {
                'analysis': {
                    'max_concurrent_wallets': 50,
                    'batch_size': 100,
                    'cache_ttl_minutes': 60,
                    'analysis_window_days': 30
                }
            },
            'risk_assessment': {
                'transaction_patterns': {
                    'velocity_spike': {'z_score_threshold': 2.5},
                    'dormant_activation': {'dormant_days_threshold': 30},
                    'wash_trading': {'balance_ratio_threshold': 0.8}
                }
            },
            'alerts': {
                'thresholds': {
                    'critical_risk_score': 0.85,
                    'high_risk_score': 0.70
                }
            }
        }

    async def analyze_wallet_comprehensive(
        self,
        wallet_address: str,
        analysis_window: timedelta = timedelta(days=30),
        include_correlations: bool = True
    ) -> HolisticRiskProfile:
        """
        Perform comprehensive risk analysis for a wallet

        Args:
            wallet_address: Wallet address to analyze
            analysis_window: Time window for analysis
            include_correlations: Whether to include correlation analysis

        Returns:
            Comprehensive risk profile
        """
        try:
            # Check cache first
            cache_key = f"wallet_{wallet_address}_{analysis_window.days}d"
            if self._is_cached_valid(cache_key):
                return self.analysis_cache[cache_key]

            self.logger.info(f"Starting comprehensive analysis for wallet {wallet_address}")

            # Parallel analysis execution
            analysis_tasks = {
                'transactions': self._analyze_transaction_patterns(wallet_address, analysis_window),
                'wallet_clustering': self._analyze_wallet_clustering(wallet_address),
                'anomalies': self._detect_anomalies(wallet_address, analysis_window),
                'mev_exposure': self._analyze_mev_exposure(wallet_address, analysis_window),
                'bridge_activities': self._analyze_bridge_activities(wallet_address, analysis_window)
            }

            # Execute analyses concurrently
            results = await asyncio.gather(
                *analysis_tasks.values(),
                return_exceptions=True
            )

            # Process results
            analysis_results = dict(zip(analysis_tasks.keys(), results))

            # Handle any exceptions
            for key, result in analysis_results.items():
                if isinstance(result, Exception):
                    self.logger.error(f"Analysis {key} failed for {wallet_address}: {result}")
                    analysis_results[key] = None

            # Build holistic risk profile
            risk_profile = await self._build_risk_profile(
                wallet_address, analysis_results, analysis_window
            )

            # Add correlation analysis if requested
            if include_correlations:
                correlation_data = await self._analyze_correlations(wallet_address)
                risk_profile.risk_factor_scores['correlation_risk'] = correlation_data.get('risk_score', 0.0)

            # Calculate overall risk score
            scoring_context = ScoringContext(
                entity_type='wallet',
                time_horizon=analysis_window,
                market_conditions='normal',  # Would be determined dynamically
                regulatory_environment='moderate',
                protocol_maturity='established',
                analysis_purpose='lending'
            )

            overall_score, risk_level, component_scores = await self.risk_scorer.calculate_comprehensive_risk_score(
                risk_profile, scoring_context
            )

            risk_profile.overall_risk_score = overall_score
            risk_profile.risk_level = risk_level
            risk_profile.risk_factor_scores = component_scores

            # Generate alerts if necessary
            alerts = await self._generate_alerts(risk_profile)
            risk_profile.active_alerts = alerts

            # Cache the result
            self._cache_result(cache_key, risk_profile)

            self.logger.info(f"Completed analysis for {wallet_address}: risk level {risk_level.value}")
            return risk_profile

        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed for {wallet_address}: {e}")
            raise

    async def _analyze_transaction_patterns(
        self,
        wallet_address: str,
        analysis_window: timedelta
    ) -> Dict[str, Any]:
        """Analyze transaction patterns for wallet"""
        try:
            # Get transaction data (would integrate with Algorand API)
            transactions = await self._fetch_transaction_data(wallet_address, analysis_window)

            # Analyze patterns using transaction analyzer
            patterns = await self.transaction_analyzer.analyze_wallet_transactions(
                wallet_address, transactions, analysis_window
            )

            # Additional analysis using specialized transaction risk analyzer
            transaction_risk_data = await self.transaction_risk.analyze_transaction_patterns(
                wallet_address, transactions
            )

            return {
                'patterns': patterns,
                'risk_metrics': transaction_risk_data,
                'transaction_count': len(transactions)
            }

        except Exception as e:
            self.logger.error(f"Transaction pattern analysis failed for {wallet_address}: {e}")
            return {'patterns': [], 'risk_metrics': {}, 'transaction_count': 0}

    async def _analyze_wallet_clustering(self, wallet_address: str) -> Dict[str, Any]:
        """Analyze wallet clustering and relationships"""
        try:
            # Get related wallet data
            related_wallets = await self._find_related_wallets(wallet_address)

            if not related_wallets:
                return {'clusters': [], 'relationships': []}

            # Analyze clustering patterns
            clusters = await self.wallet_clustering.analyze_wallet_relationships(
                related_wallets
            )

            # Additional clustering analysis
            clustering_risk = await self.wallet_risk.analyze_clustering_risk(
                wallet_address, related_wallets
            )

            return {
                'clusters': clusters,
                'clustering_risk': clustering_risk,
                'related_wallet_count': len(related_wallets)
            }

        except Exception as e:
            self.logger.error(f"Wallet clustering analysis failed for {wallet_address}: {e}")
            return {'clusters': [], 'relationships': []}

    async def _detect_anomalies(
        self,
        wallet_address: str,
        analysis_window: timedelta
    ) -> Dict[str, Any]:
        """Detect anomalous behavior patterns"""
        try:
            # Get transaction data
            transactions = await self._fetch_transaction_data(wallet_address, analysis_window)

            # Detect anomalies
            anomalies = await self.anomaly_detector.detect_transaction_anomalies(
                wallet_address, transactions, analysis_window
            )

            return {
                'anomalies': anomalies,
                'anomaly_count': len(anomalies),
                'max_anomaly_score': max([a.score for a in anomalies], default=0.0)
            }

        except Exception as e:
            self.logger.error(f"Anomaly detection failed for {wallet_address}: {e}")
            return {'anomalies': [], 'anomaly_count': 0, 'max_anomaly_score': 0.0}

    async def _analyze_mev_exposure(
        self,
        wallet_address: str,
        analysis_window: timedelta
    ) -> Dict[str, Any]:
        """Analyze MEV exposure and exploitation"""
        try:
            # Get transaction data for MEV analysis
            transactions = await self._fetch_mev_transaction_data(wallet_address, analysis_window)

            # Convert to MEV transaction format
            mev_transactions = await self._convert_to_mev_format(transactions)

            # Detect MEV patterns
            mev_patterns = await self.mev_detector.detect_mev_patterns(mev_transactions)

            # Calculate MEV analytics
            mev_analytics = self.mev_detector.generate_mev_analytics(mev_patterns)

            return {
                'mev_patterns': mev_patterns,
                'mev_analytics': mev_analytics,
                'mev_exposure_score': self._calculate_mev_exposure_score(mev_patterns)
            }

        except Exception as e:
            self.logger.error(f"MEV analysis failed for {wallet_address}: {e}")
            return {'mev_patterns': [], 'mev_analytics': None, 'mev_exposure_score': 0.0}

    async def _analyze_bridge_activities(
        self,
        wallet_address: str,
        analysis_window: timedelta
    ) -> Dict[str, Any]:
        """Analyze cross-chain bridge activities"""
        try:
            # Get bridge activity data
            bridge_activities = await self._fetch_bridge_data(wallet_address, analysis_window)

            if not bridge_activities:
                return {'bridge_risk': 0.0, 'activities': []}

            # Analyze bridge behavior
            bridge_analysis = await self.bridge_analyzer.analyze_user_bridge_behavior(
                wallet_address, bridge_activities, analysis_window
            )

            # Additional bridge risk analysis
            bridge_risk_data = await self.bridge_risk.analyze_bridge_risk_patterns(
                wallet_address, bridge_activities
            )

            return {
                'bridge_analysis': bridge_analysis,
                'bridge_risk_data': bridge_risk_data,
                'activity_count': len(bridge_activities)
            }

        except Exception as e:
            self.logger.error(f"Bridge analysis failed for {wallet_address}: {e}")
            return {'bridge_analysis': {}, 'bridge_risk_data': {}, 'activity_count': 0}

    async def _analyze_correlations(self, wallet_address: str) -> Dict[str, Any]:
        """Analyze correlations with other entities"""
        try:
            # Get correlation data
            portfolio_data = await self._get_portfolio_data(wallet_address)
            asset_data = await self._get_asset_correlation_data(wallet_address)

            # Analyze correlations
            correlation_matrices = await self.correlation_analyzer.analyze_asset_correlations(
                asset_data, ['price', 'volume', 'liquidity']
            )

            # Calculate correlation risks
            correlation_risks = await self.correlation_analyzer.calculate_portfolio_correlation_risk(
                portfolio_data, correlation_matrices
            )

            return {
                'correlation_matrices': correlation_matrices,
                'correlation_risks': correlation_risks,
                'risk_score': correlation_risks.get('overall_correlation_risk', 0.0)
            }

        except Exception as e:
            self.logger.error(f"Correlation analysis failed for {wallet_address}: {e}")
            return {'risk_score': 0.0}

    async def _build_risk_profile(
        self,
        wallet_address: str,
        analysis_results: Dict[str, Any],
        analysis_window: timedelta
    ) -> HolisticRiskProfile:
        """Build comprehensive risk profile from analysis results"""

        # Extract data from analysis results
        transaction_patterns = analysis_results.get('transactions', {}).get('patterns', [])
        anomalies = analysis_results.get('anomalies', {}).get('anomalies', [])
        mev_patterns = analysis_results.get('mev_exposure', {}).get('mev_patterns', [])

        # Initialize risk factor scores
        risk_factor_scores = {
            'transaction_behavior': self._calculate_transaction_risk_score(transaction_patterns),
            'anomaly_risk': self._calculate_anomaly_risk_score(anomalies),
            'mev_risk': self._calculate_mev_risk_score(mev_patterns),
            'clustering_risk': self._calculate_clustering_risk_score(analysis_results.get('wallet_clustering', {})),
            'bridge_risk': self._calculate_bridge_risk_score(analysis_results.get('bridge_activities', {}))
        }

        # Risk factor weights (would be configurable)
        risk_factor_weights = {
            'transaction_behavior': 0.25,
            'anomaly_risk': 0.20,
            'mev_risk': 0.20,
            'clustering_risk': 0.20,
            'bridge_risk': 0.15
        }

        # Calculate data completeness
        data_completeness = self._calculate_data_completeness(analysis_results)

        # Build holistic risk profile
        risk_profile = HolisticRiskProfile(
            entity_id=wallet_address,
            entity_type='wallet',
            assessment_timestamp=datetime.utcnow(),
            transaction_patterns=transaction_patterns,
            defi_exposures=[],  # Would be populated from DeFi analysis
            smart_contract_risks=[],  # Would be populated from smart contract analysis
            liquidity_risks=[],  # Would be populated from liquidity analysis
            governance_risks=[],  # Would be populated from governance analysis
            asa_risks=[],  # Would be populated from ASA analysis
            protocol_risks=[],  # Would be populated from protocol analysis
            overall_risk_score=0.0,  # Will be calculated by risk scorer
            risk_level=RiskLevel.LOW,  # Will be determined by risk scorer
            confidence_score=data_completeness,
            risk_factor_scores=risk_factor_scores,
            risk_factor_weights=risk_factor_weights,
            active_alerts=[],  # Will be populated by alert generation
            recommended_mitigations=[],  # Will be populated by mitigation system
            data_completeness=data_completeness
        )

        return risk_profile

    def _calculate_transaction_risk_score(self, patterns: List[Any]) -> float:
        """Calculate transaction behavior risk score"""
        if not patterns:
            return 0.0

        # Use pattern confidence scores
        pattern_scores = [pattern.confidence_score for pattern in patterns]
        return min(sum(pattern_scores) / len(pattern_scores), 1.0)

    def _calculate_anomaly_risk_score(self, anomalies: List[Any]) -> float:
        """Calculate anomaly risk score"""
        if not anomalies:
            return 0.0

        # Use anomaly scores
        anomaly_scores = [anomaly.score for anomaly in anomalies]
        return min(max(anomaly_scores), 1.0)

    def _calculate_mev_risk_score(self, patterns: List[Any]) -> float:
        """Calculate MEV risk score"""
        if not patterns:
            return 0.0

        # MEV patterns indicate risk
        return min(len(patterns) / 10.0, 1.0)  # Normalize to 0-1

    def _calculate_clustering_risk_score(self, clustering_data: Dict[str, Any]) -> float:
        """Calculate clustering risk score"""
        clusters = clustering_data.get('clusters', [])
        if not clusters:
            return 0.0

        # Use cluster scores
        cluster_scores = [cluster.cluster_score for cluster in clusters]
        return max(cluster_scores) if cluster_scores else 0.0

    def _calculate_bridge_risk_score(self, bridge_data: Dict[str, Any]) -> float:
        """Calculate bridge risk score"""
        bridge_analysis = bridge_data.get('bridge_analysis', {})
        return bridge_analysis.get('risk_score', 0.0)

    def _calculate_data_completeness(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate data completeness score"""
        completed_analyses = sum(1 for result in analysis_results.values() if result is not None)
        total_analyses = len(analysis_results)
        return completed_analyses / max(total_analyses, 1)

    async def _generate_alerts(self, risk_profile: HolisticRiskProfile) -> List[RiskAlert]:
        """Generate risk alerts based on profile"""
        alerts = []

        # High risk score alert
        if risk_profile.overall_risk_score > self.config.get('alerts', {}).get('thresholds', {}).get('critical_risk_score', 0.85):
            alert = RiskAlert(
                alert_id=f"high_risk_{risk_profile.entity_id}_{datetime.utcnow().timestamp()}",
                alert_type="HIGH_RISK_SCORE",
                severity=RiskLevel.CRITICAL,
                title="Critical Risk Score Detected",
                description=f"Entity {risk_profile.entity_id} has critical risk score: {risk_profile.overall_risk_score:.2f}",
                affected_addresses=[risk_profile.entity_id],
                affected_protocols=[],
                risk_score=risk_profile.overall_risk_score,
                confidence=risk_profile.confidence_score,
                detection_method="Comprehensive Risk Assessment",
                evidence={'risk_factors': risk_profile.risk_factor_scores},
                recommendations=[
                    "Implement enhanced monitoring",
                    "Consider position limitations",
                    "Review risk mitigation strategies"
                ]
            )
            alerts.append(alert)

        return alerts

    def _is_cached_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        if cache_key not in self.analysis_cache:
            return False

        cache_time = self.cache_timestamps.get(cache_key)
        if not cache_time:
            return False

        ttl_minutes = self.config.get('engine', {}).get('analysis', {}).get('cache_ttl_minutes', 60)
        return (datetime.utcnow() - cache_time) < timedelta(minutes=ttl_minutes)

    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache analysis result"""
        self.analysis_cache[cache_key] = result
        self.cache_timestamps[cache_key] = datetime.utcnow()

    # Placeholder methods for data fetching (would integrate with actual APIs)
    async def _fetch_transaction_data(self, wallet_address: str, analysis_window: timedelta) -> List[Dict[str, Any]]:
        """Fetch transaction data from Algorand"""
        # Placeholder - would integrate with Algorand API
        return []

    async def _fetch_mev_transaction_data(self, wallet_address: str, analysis_window: timedelta) -> List[Dict[str, Any]]:
        """Fetch MEV-relevant transaction data"""
        # Placeholder - would integrate with Algorand API
        return []

    async def _convert_to_mev_format(self, transactions: List[Dict[str, Any]]) -> List[Any]:
        """Convert transaction data to MEV format"""
        # Placeholder conversion
        return []

    async def _fetch_bridge_data(self, wallet_address: str, analysis_window: timedelta) -> List[Any]:
        """Fetch bridge activity data"""
        # Placeholder - would integrate with bridge APIs
        return []

    async def _find_related_wallets(self, wallet_address: str) -> Dict[str, List[Dict[str, Any]]]:
        """Find wallets related to the target wallet"""
        # Placeholder - would analyze transaction patterns to find related wallets
        return {}

    async def _get_portfolio_data(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Get portfolio data for correlation analysis"""
        # Placeholder - would get asset holdings
        return []

    async def _get_asset_correlation_data(self, wallet_address: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get asset data for correlation analysis"""
        # Placeholder - would get historical asset data
        return {}

    def _calculate_mev_exposure_score(self, mev_patterns: List[Any]) -> float:
        """Calculate MEV exposure score"""
        if not mev_patterns:
            return 0.0
        return min(len(mev_patterns) / 5.0, 1.0)