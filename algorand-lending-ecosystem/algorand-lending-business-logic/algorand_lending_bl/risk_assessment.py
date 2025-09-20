"""
Consolidated Risk Assessment Engine

Combines all risk assessment functionality into a single, working module.
Includes behavioral analysis, protocol risk monitoring, and holistic risk evaluation.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

import httpx

from .models import (
    RiskAssessment, RiskProfile, RiskScore, RiskLevel,
    AlgorandAddress
)
from .config import RiskAssessmentConfig, DEFAULT_RISK_ASSESSMENT_CONFIG

logger = logging.getLogger(__name__)


class RiskAssessmentEngine:
    """
    Unified risk assessment engine for Algorand lending.

    Provides comprehensive risk analysis including:
    - Blockchain behavior analysis
    - DeFi protocol risk assessment
    - Smart contract interaction analysis
    - Liquidity cascade risk evaluation
    - Cross-engine risk correlation
    """

    def __init__(self, config: Optional[RiskAssessmentConfig] = None):
        """Initialize the risk assessment engine with configuration."""
        self.config = config or DEFAULT_RISK_ASSESSMENT_CONFIG
        self._risk_cache: Dict[str, Tuple[RiskAssessment, datetime]] = {}
        self._profile_cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}

    async def assess_risk(self, address: AlgorandAddress) -> RiskAssessment:
        """
        Perform comprehensive risk assessment for an address.

        Args:
            address: Algorand address to assess

        Returns:
            Complete risk assessment with profile and recommendations
        """
        try:
            logger.info(f"Assessing risk for address {address.address}")

            # Check cache for recent assessment
            cache_key = f"risk_{address.address}"
            cached_assessment = self._get_cached_assessment(cache_key)
            if cached_assessment:
                logger.info(f"Returning cached risk assessment for {address.address}")
                return cached_assessment

            # Build comprehensive risk profile
            risk_profiles = await self._build_risk_profiles(address)

            # Calculate holistic risk metrics
            holistic_risk = await self._calculate_holistic_risk(risk_profiles, address)

            # Generate risk profile summary
            risk_profile = self._create_risk_profile_summary(holistic_risk, address)

            # Create final assessment
            assessment = RiskAssessment(
                address=address,
                risk_profile=risk_profile,
                individual_profiles=risk_profiles,
                assessment_metadata={
                    'assessment_completeness': self._calculate_assessment_completeness(risk_profiles),
                    'data_freshness': self._calculate_data_freshness(risk_profiles),
                    'model_version': '1.0.0',
                    'assessment_timestamp': datetime.utcnow().isoformat()
                }
            )

            # Cache the assessment
            self._cache_assessment(cache_key, assessment)

            logger.info(f"Risk assessment completed for {address.address}: {risk_profile.risk_level.value}")
            return assessment

        except Exception as e:
            logger.error(f"Error assessing risk for {address.address}: {e}")
            return self._create_fallback_assessment(address)

    async def _build_risk_profiles(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Build comprehensive risk profiles from multiple analysis engines."""
        logger.debug(f"Building risk profiles for {address.address}")

        try:
            # Execute risk analyses in parallel
            blockchain_task = self._analyze_blockchain_behavior(address)
            defi_task = self._analyze_defi_protocol_risk(address)
            smart_contract_task = self._analyze_smart_contract_risk(address)
            liquidity_task = self._analyze_liquidity_risk(address)
            governance_task = self._analyze_governance_risk(address)

            # Gather results
            blockchain_profile, defi_profile, smart_contract_profile, liquidity_profile, governance_profile = await asyncio.gather(
                blockchain_task, defi_task, smart_contract_task, liquidity_task, governance_task,
                return_exceptions=True
            )

            # Handle exceptions
            if isinstance(blockchain_profile, Exception):
                logger.warning(f"Blockchain behavior analysis failed: {blockchain_profile}")
                blockchain_profile = self._get_default_blockchain_profile()

            if isinstance(defi_profile, Exception):
                logger.warning(f"DeFi protocol analysis failed: {defi_profile}")
                defi_profile = self._get_default_defi_profile()

            if isinstance(smart_contract_profile, Exception):
                logger.warning(f"Smart contract analysis failed: {smart_contract_profile}")
                smart_contract_profile = self._get_default_smart_contract_profile()

            if isinstance(liquidity_profile, Exception):
                logger.warning(f"Liquidity analysis failed: {liquidity_profile}")
                liquidity_profile = self._get_default_liquidity_profile()

            if isinstance(governance_profile, Exception):
                logger.warning(f"Governance analysis failed: {governance_profile}")
                governance_profile = self._get_default_governance_profile()

            return {
                'blockchain_behavior': blockchain_profile,
                'defi_protocol': defi_profile,
                'smart_contract': smart_contract_profile,
                'liquidity_cascade': liquidity_profile,
                'governance_stability': governance_profile
            }

        except Exception as e:
            logger.error(f"Error building risk profiles: {e}")
            return self._get_minimal_risk_profiles()

    async def _analyze_blockchain_behavior(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Analyze blockchain behavior patterns for risk indicators."""
        try:
            # Get account transaction history
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address.address}/transactions",
                    params={'limit': 1000}  # Analyze recent transactions
                )

                if response.status_code == 200:
                    tx_data = response.json()
                    transactions = tx_data.get('transactions', [])

                    # Analyze transaction patterns
                    pattern_analysis = self._analyze_transaction_patterns(transactions)
                    volume_analysis = self._analyze_volume_patterns(transactions)
                    temporal_analysis = self._analyze_temporal_patterns(transactions)
                    counterparty_analysis = self._analyze_counterparty_patterns(transactions)

                    # Calculate risk scores
                    transaction_pattern_risk = self._calculate_transaction_pattern_risk(pattern_analysis)
                    volume_anomaly_risk = self._calculate_volume_anomaly_risk(volume_analysis)
                    temporal_pattern_risk = self._calculate_temporal_pattern_risk(temporal_analysis)
                    counterparty_risk = self._calculate_counterparty_risk(counterparty_analysis)

                    # Calculate overall blockchain behavior risk
                    risk_components = [
                        transaction_pattern_risk,
                        volume_anomaly_risk,
                        temporal_pattern_risk,
                        counterparty_risk
                    ]
                    overall_risk = sum(risk_components) / len(risk_components)

                    return {
                        'transaction_pattern_risk': transaction_pattern_risk,
                        'volume_anomaly_risk': volume_anomaly_risk,
                        'temporal_pattern_risk': temporal_pattern_risk,
                        'counterparty_risk': counterparty_risk,
                        'overall_risk_score': overall_risk,
                        'risk_level': self._score_to_risk_level(overall_risk),
                        'analysis_data': {
                            'transaction_count': len(transactions),
                            'pattern_analysis': pattern_analysis,
                            'volume_analysis': volume_analysis,
                            'temporal_analysis': temporal_analysis,
                            'counterparty_analysis': counterparty_analysis
                        },
                        'data_quality': Decimal('0.8'),
                        'confidence': Decimal('0.7'),
                        'last_updated': datetime.utcnow()
                    }

        except Exception as e:
            logger.debug(f"Failed to analyze blockchain behavior: {e}")

        return self._get_default_blockchain_profile()

    async def _analyze_defi_protocol_risk(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Analyze DeFi protocol interaction risks."""
        try:
            # Get account information for DeFi protocol analysis
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address.address}"
                )

                if response.status_code == 200:
                    account_data = response.json()

                    # Analyze DeFi protocol exposure
                    apps_opted_in = account_data.get('total-apps-opted-in', 0)
                    assets_count = len(account_data.get('assets', []))

                    # Calculate risk metrics
                    protocol_concentration_risk = self._calculate_protocol_concentration_risk(apps_opted_in)
                    liquidity_risk = self._calculate_defi_liquidity_risk(assets_count)
                    smart_contract_risk = self._calculate_defi_smart_contract_risk(apps_opted_in)

                    # Overall DeFi risk
                    overall_risk = (protocol_concentration_risk + liquidity_risk + smart_contract_risk) / 3

                    return {
                        'protocol_concentration_risk': protocol_concentration_risk,
                        'liquidity_risk': liquidity_risk,
                        'smart_contract_risk': smart_contract_risk,
                        'yield_hunting_risk': Decimal('0.3'),  # Default estimate
                        'leverage_risk': Decimal('0.2'),       # Default estimate
                        'bridge_risk': Decimal('0.1'),         # Default estimate
                        'overall_risk_score': overall_risk,
                        'risk_level': self._score_to_risk_level(overall_risk),
                        'analysis_data': {
                            'apps_opted_in': apps_opted_in,
                            'assets_count': assets_count
                        },
                        'data_quality': Decimal('0.6'),
                        'confidence': Decimal('0.6'),
                        'last_updated': datetime.utcnow()
                    }

        except Exception as e:
            logger.debug(f"Failed to analyze DeFi protocol risk: {e}")

        return self._get_default_defi_profile()

    async def _analyze_smart_contract_risk(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Analyze smart contract interaction risks."""
        try:
            # Get account application interactions
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address.address}"
                )

                if response.status_code == 200:
                    account_data = response.json()

                    apps_opted_in = account_data.get('total-apps-opted-in', 0)
                    apps_created = account_data.get('total-created-apps', 0)

                    # Calculate smart contract risk metrics
                    code_quality_risk = self._calculate_code_quality_risk(apps_created)
                    complexity_risk = self._calculate_contract_complexity_risk(apps_opted_in)
                    audit_status_risk = self._calculate_audit_status_risk(apps_opted_in)

                    # Overall smart contract risk
                    overall_risk = (code_quality_risk + complexity_risk + audit_status_risk) / 3

                    return {
                        'code_quality_risk': code_quality_risk,
                        'audit_status_risk': audit_status_risk,
                        'complexity_risk': complexity_risk,
                        'upgrade_risk': Decimal('0.3'),        # Default estimate
                        'governance_risk': Decimal('0.25'),    # Default estimate
                        'economic_risk': Decimal('0.2'),       # Default estimate
                        'overall_risk_score': overall_risk,
                        'risk_level': self._score_to_risk_level(overall_risk),
                        'analysis_data': {
                            'apps_opted_in': apps_opted_in,
                            'apps_created': apps_created
                        },
                        'data_quality': Decimal('0.5'),
                        'confidence': Decimal('0.5'),
                        'last_updated': datetime.utcnow()
                    }

        except Exception as e:
            logger.debug(f"Failed to analyze smart contract risk: {e}")

        return self._get_default_smart_contract_profile()

    async def _analyze_liquidity_risk(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Analyze liquidity cascade risks."""
        try:
            # Get account asset portfolio
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address.address}"
                )

                if response.status_code == 200:
                    account_data = response.json()

                    balance = Decimal(str(account_data.get('amount', 0))) / Decimal('1000000')
                    assets = account_data.get('assets', [])

                    # Calculate liquidity risk metrics
                    market_depth_risk = self._calculate_market_depth_risk(balance, assets)
                    concentration_risk = self._calculate_liquidity_concentration_risk(assets)
                    correlation_risk = self._calculate_asset_correlation_risk(assets)

                    # Overall liquidity risk
                    overall_risk = (market_depth_risk + concentration_risk + correlation_risk) / 3

                    return {
                        'market_depth_risk': market_depth_risk,
                        'concentration_risk': concentration_risk,
                        'correlation_risk': correlation_risk,
                        'volatility_risk': Decimal('0.4'),             # Default estimate
                        'slippage_risk': Decimal('0.3'),               # Default estimate
                        'liquidation_cascade_risk': Decimal('0.2'),    # Default estimate
                        'overall_risk_score': overall_risk,
                        'risk_level': self._score_to_risk_level(overall_risk),
                        'analysis_data': {
                            'algo_balance': balance,
                            'asset_count': len(assets)
                        },
                        'data_quality': Decimal('0.6'),
                        'confidence': Decimal('0.6'),
                        'last_updated': datetime.utcnow()
                    }

        except Exception as e:
            logger.debug(f"Failed to analyze liquidity risk: {e}")

        return self._get_default_liquidity_profile()

    async def _analyze_governance_risk(self, address: AlgorandAddress) -> Dict[str, Any]:
        """Analyze governance stability risks."""
        try:
            # Get account balance for governance participation analysis
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address.address}"
                )

                if response.status_code == 200:
                    account_data = response.json()

                    balance = Decimal(str(account_data.get('amount', 0))) / Decimal('1000000')

                    # Calculate governance risk metrics
                    centralization_risk = self._calculate_centralization_risk(balance)
                    participation_risk = self._calculate_governance_participation_risk(balance)
                    decision_quality_risk = self._calculate_decision_quality_risk(balance)

                    # Overall governance risk
                    overall_risk = (centralization_risk + participation_risk + decision_quality_risk) / 3

                    return {
                        'centralization_risk': centralization_risk,
                        'participation_risk': participation_risk,
                        'decision_quality_risk': decision_quality_risk,
                        'attack_risk': Decimal('0.15'),        # Default estimate
                        'upgrade_risk': Decimal('0.2'),        # Default estimate
                        'community_risk': Decimal('0.25'),     # Default estimate
                        'overall_risk_score': overall_risk,
                        'risk_level': self._score_to_risk_level(overall_risk),
                        'analysis_data': {
                            'algo_balance': balance,
                            'governance_eligible': balance >= Decimal('1')
                        },
                        'data_quality': Decimal('0.5'),
                        'confidence': Decimal('0.5'),
                        'last_updated': datetime.utcnow()
                    }

        except Exception as e:
            logger.debug(f"Failed to analyze governance risk: {e}")

        return self._get_default_governance_profile()

    async def _calculate_holistic_risk(self, profiles: Dict[str, Any], address: AlgorandAddress) -> Dict[str, Any]:
        """Calculate holistic risk metrics combining all individual assessments."""

        # Extract individual risk scores
        blockchain_risk = profiles['blockchain_behavior'].get('overall_risk_score', Decimal('0.5'))
        defi_risk = profiles['defi_protocol'].get('overall_risk_score', Decimal('0.5'))
        smart_contract_risk = profiles['smart_contract'].get('overall_risk_score', Decimal('0.5'))
        liquidity_risk = profiles['liquidity_cascade'].get('overall_risk_score', Decimal('0.5'))
        governance_risk = profiles['governance_stability'].get('overall_risk_score', Decimal('0.5'))

        # Apply weights to different risk categories
        weights = {
            'blockchain_behavior': Decimal('0.3'),
            'defi_protocol': Decimal('0.25'),
            'smart_contract': Decimal('0.2'),
            'liquidity_cascade': Decimal('0.15'),
            'governance_stability': Decimal('0.1')
        }

        # Calculate weighted overall risk score
        overall_risk_score = (
            blockchain_risk * weights['blockchain_behavior'] +
            defi_risk * weights['defi_protocol'] +
            smart_contract_risk * weights['smart_contract'] +
            liquidity_risk * weights['liquidity_cascade'] +
            governance_risk * weights['governance_stability']
        )

        # Calculate cross-engine correlations
        correlations = self._calculate_cross_engine_correlations(profiles)

        # Identify systemic risk factors
        systemic_factors = self._identify_systemic_risk_factors(profiles)

        # Generate risk alerts
        risk_alerts = self._generate_risk_alerts(profiles, overall_risk_score)

        # Generate recommendations
        recommendations = self._generate_risk_recommendations(profiles, overall_risk_score)

        return {
            'overall_risk_score': overall_risk_score,
            'individual_scores': {
                'blockchain_behavior': blockchain_risk,
                'defi_protocol': defi_risk,
                'smart_contract': smart_contract_risk,
                'liquidity_cascade': liquidity_risk,
                'governance_stability': governance_risk
            },
            'risk_level': self._score_to_risk_level(overall_risk_score),
            'cross_engine_correlations': correlations,
            'systemic_risk_factors': systemic_factors,
            'risk_alerts': risk_alerts,
            'recommendations': recommendations,
            'confidence': self._calculate_overall_confidence(profiles),
            'assessment_timestamp': datetime.utcnow()
        }

    def _create_risk_profile_summary(self, holistic_risk: Dict[str, Any], address: AlgorandAddress) -> RiskProfile:
        """Create simplified risk profile summary for external API."""

        overall_risk_score = holistic_risk['overall_risk_score'] * 100  # Convert to 0-100 scale
        risk_level = holistic_risk['risk_level']
        confidence = holistic_risk['confidence']

        # Extract key risk factors
        key_risk_factors = []
        individual_scores = holistic_risk['individual_scores']

        if individual_scores['blockchain_behavior'] > Decimal('0.7'):
            key_risk_factors.append("High blockchain behavior risk")
        if individual_scores['defi_protocol'] > Decimal('0.7'):
            key_risk_factors.append("Elevated DeFi protocol exposure")
        if individual_scores['smart_contract'] > Decimal('0.7'):
            key_risk_factors.append("Smart contract interaction risks")
        if individual_scores['liquidity_cascade'] > Decimal('0.7'):
            key_risk_factors.append("Liquidity cascade vulnerability")

        if not key_risk_factors:
            key_risk_factors = ["Standard risk factors identified"]

        # Generate recommended actions
        recommended_actions = holistic_risk.get('recommendations', [])
        if not recommended_actions:
            if overall_risk_score > 70:
                recommended_actions = ["Enhanced monitoring recommended", "Consider additional risk mitigation"]
            elif overall_risk_score > 50:
                recommended_actions = ["Regular monitoring advised"]
            else:
                recommended_actions = ["Standard monitoring sufficient"]

        return RiskProfile(
            address=address,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            confidence=confidence,
            key_risk_factors=key_risk_factors,
            recommended_actions=recommended_actions,
            assessment_timestamp=datetime.utcnow()
        )

    # Risk calculation helper methods
    def _analyze_transaction_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction patterns for anomalies."""
        if not transactions:
            return {'pattern_score': 0.5, 'anomaly_count': 0}

        # Simple pattern analysis
        tx_types = {}
        for tx in transactions:
            tx_type = tx.get('tx-type', 'unknown')
            tx_types[tx_type] = tx_types.get(tx_type, 0) + 1

        # Calculate pattern diversity
        total_txs = len(transactions)
        pattern_entropy = len(tx_types) / min(total_txs, 10)  # Normalize to 0-1

        return {
            'pattern_score': pattern_entropy,
            'transaction_types': tx_types,
            'total_transactions': total_txs,
            'anomaly_count': 0  # Simplified
        }

    def _analyze_volume_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction volume patterns."""
        if not transactions:
            return {'volume_score': 0.5, 'total_volume': 0}

        total_volume = 0
        volumes = []

        for tx in transactions:
            # Get payment amount if it's a payment transaction
            if tx.get('tx-type') == 'pay':
                amount = tx.get('payment-transaction', {}).get('amount', 0)
                amount_algo = amount / 1000000  # Convert microalgos
                total_volume += amount_algo
                volumes.append(amount_algo)

        # Calculate volume metrics
        avg_volume = total_volume / len(volumes) if volumes else 0
        volume_score = min(total_volume / 10000, 1.0)  # Normalize to reasonable scale

        return {
            'volume_score': volume_score,
            'total_volume': total_volume,
            'average_volume': avg_volume,
            'transaction_count': len(volumes)
        }

    def _analyze_temporal_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal transaction patterns."""
        if not transactions:
            return {'temporal_score': 0.5}

        # Simple temporal analysis - check for regular patterns
        timestamps = []
        for tx in transactions:
            round_time = tx.get('round-time')
            if round_time:
                timestamps.append(round_time)

        # Calculate temporal regularity (simplified)
        temporal_score = 0.5  # Default neutral score

        return {
            'temporal_score': temporal_score,
            'transaction_timespan_days': len(timestamps) // 24 if timestamps else 0
        }

    def _analyze_counterparty_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze counterparty interaction patterns."""
        if not transactions:
            return {'counterparty_score': 0.5}

        counterparties = set()
        for tx in transactions:
            if tx.get('tx-type') == 'pay':
                receiver = tx.get('payment-transaction', {}).get('receiver')
                if receiver:
                    counterparties.add(receiver)

        # More unique counterparties = lower risk (more distributed)
        diversity_score = min(len(counterparties) / 20, 1.0)  # Normalize

        return {
            'counterparty_score': diversity_score,
            'unique_counterparties': len(counterparties)
        }

    def _calculate_transaction_pattern_risk(self, analysis: Dict[str, Any]) -> Decimal:
        """Calculate risk from transaction patterns."""
        pattern_score = analysis.get('pattern_score', 0.5)
        # Higher pattern diversity = lower risk
        return Decimal(str(1.0 - pattern_score))

    def _calculate_volume_anomaly_risk(self, analysis: Dict[str, Any]) -> Decimal:
        """Calculate risk from volume anomalies."""
        volume_score = analysis.get('volume_score', 0.5)
        # Very high volume could indicate risk
        if volume_score > 0.9:
            return Decimal('0.7')
        else:
            return Decimal(str(volume_score * 0.5))

    def _calculate_temporal_pattern_risk(self, analysis: Dict[str, Any]) -> Decimal:
        """Calculate risk from temporal patterns."""
        temporal_score = analysis.get('temporal_score', 0.5)
        return Decimal(str(1.0 - temporal_score))

    def _calculate_counterparty_risk(self, analysis: Dict[str, Any]) -> Decimal:
        """Calculate risk from counterparty patterns."""
        counterparty_score = analysis.get('counterparty_score', 0.5)
        # Higher diversity = lower risk
        return Decimal(str(1.0 - counterparty_score))

    def _calculate_protocol_concentration_risk(self, apps_opted_in: int) -> Decimal:
        """Calculate DeFi protocol concentration risk."""
        if apps_opted_in == 0:
            return Decimal('0.1')  # Low risk if no DeFi exposure
        elif apps_opted_in <= 2:
            return Decimal('0.3')  # Moderate concentration
        elif apps_opted_in <= 5:
            return Decimal('0.5')  # Higher concentration
        else:
            return Decimal('0.7')  # Very high concentration

    def _calculate_defi_liquidity_risk(self, assets_count: int) -> Decimal:
        """Calculate DeFi liquidity risk."""
        if assets_count <= 2:
            return Decimal('0.2')  # Low complexity
        elif assets_count <= 5:
            return Decimal('0.4')  # Medium complexity
        elif assets_count <= 10:
            return Decimal('0.6')  # High complexity
        else:
            return Decimal('0.8')  # Very high complexity

    def _calculate_defi_smart_contract_risk(self, apps_opted_in: int) -> Decimal:
        """Calculate smart contract risk from DeFi exposure."""
        return min(Decimal(str(apps_opted_in)) * Decimal('0.1'), Decimal('0.8'))

    def _calculate_code_quality_risk(self, apps_created: int) -> Decimal:
        """Calculate code quality risk."""
        if apps_created == 0:
            return Decimal('0.3')  # No development = medium risk
        else:
            return Decimal('0.4')  # Some development = moderate risk

    def _calculate_contract_complexity_risk(self, apps_opted_in: int) -> Decimal:
        """Calculate contract complexity risk."""
        return min(Decimal(str(apps_opted_in)) * Decimal('0.08'), Decimal('0.7'))

    def _calculate_audit_status_risk(self, apps_opted_in: int) -> Decimal:
        """Calculate audit status risk."""
        # Assume most contracts are not formally audited
        return min(Decimal(str(apps_opted_in)) * Decimal('0.1'), Decimal('0.8'))

    def _calculate_market_depth_risk(self, balance: Decimal, assets: List[Dict]) -> Decimal:
        """Calculate market depth risk."""
        total_value = balance  # Simplified - would calculate actual portfolio value
        if total_value < Decimal('100'):
            return Decimal('0.2')  # Low risk for small portfolios
        elif total_value < Decimal('10000'):
            return Decimal('0.4')
        else:
            return Decimal('0.6')  # Higher risk for large portfolios

    def _calculate_liquidity_concentration_risk(self, assets: List[Dict]) -> Decimal:
        """Calculate liquidity concentration risk."""
        if len(assets) <= 1:
            return Decimal('0.3')
        elif len(assets) <= 3:
            return Decimal('0.5')
        else:
            return Decimal('0.7')

    def _calculate_asset_correlation_risk(self, assets: List[Dict]) -> Decimal:
        """Calculate asset correlation risk."""
        # Simplified - assume moderate correlation
        return Decimal('0.4')

    def _calculate_centralization_risk(self, balance: Decimal) -> Decimal:
        """Calculate governance centralization risk."""
        if balance < Decimal('1'):
            return Decimal('0.2')  # Low stake = low centralization risk
        elif balance < Decimal('1000'):
            return Decimal('0.3')
        elif balance < Decimal('100000'):
            return Decimal('0.4')
        else:
            return Decimal('0.6')  # Large stake = higher centralization concern

    def _calculate_governance_participation_risk(self, balance: Decimal) -> Decimal:
        """Calculate governance participation risk."""
        if balance < Decimal('1'):
            return Decimal('0.5')  # Can't participate
        else:
            return Decimal('0.3')  # Can participate = lower risk

    def _calculate_decision_quality_risk(self, balance: Decimal) -> Decimal:
        """Calculate governance decision quality risk."""
        # Simplified assessment
        return Decimal('0.3')

    def _score_to_risk_level(self, score: Decimal) -> RiskLevel:
        """Convert risk score to risk level enum."""
        if score <= Decimal('0.2'):
            return RiskLevel.VERY_LOW
        elif score <= Decimal('0.4'):
            return RiskLevel.LOW
        elif score <= Decimal('0.6'):
            return RiskLevel.MEDIUM
        elif score <= Decimal('0.8'):
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _calculate_cross_engine_correlations(self, profiles: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate correlations between different risk engines."""
        correlations = []

        # Example correlation: DeFi and Smart Contract risks are often correlated
        defi_risk = profiles['defi_protocol'].get('overall_risk_score', Decimal('0.5'))
        sc_risk = profiles['smart_contract'].get('overall_risk_score', Decimal('0.5'))

        correlation_coeff = abs(defi_risk - sc_risk) / max(defi_risk + sc_risk, Decimal('0.1'))

        correlations.append({
            'engine_1': 'defi_protocol',
            'engine_2': 'smart_contract',
            'correlation_coefficient': correlation_coeff,
            'correlation_strength': 'moderate' if correlation_coeff > 0.5 else 'weak'
        })

        return correlations

    def _identify_systemic_risk_factors(self, profiles: Dict[str, Any]) -> List[str]:
        """Identify systemic risk factors across engines."""
        factors = []

        # Check for high risk across multiple engines
        high_risk_engines = []
        for engine, profile in profiles.items():
            if profile.get('overall_risk_score', Decimal('0.5')) > Decimal('0.7'):
                high_risk_engines.append(engine)

        if len(high_risk_engines) >= 2:
            factors.append(f"High risk detected across multiple engines: {', '.join(high_risk_engines)}")

        # Check for specific systemic patterns
        defi_risk = profiles['defi_protocol'].get('overall_risk_score', Decimal('0.5'))
        liquidity_risk = profiles['liquidity_cascade'].get('overall_risk_score', Decimal('0.5'))

        if defi_risk > Decimal('0.6') and liquidity_risk > Decimal('0.6'):
            factors.append("Potential DeFi liquidity cascade vulnerability")

        return factors

    def _generate_risk_alerts(self, profiles: Dict[str, Any], overall_risk: Decimal) -> List[Dict[str, Any]]:
        """Generate risk alerts based on analysis."""
        alerts = []

        # Overall risk alert
        if overall_risk > self.config.critical_alert_threshold:
            alerts.append({
                'severity': 'critical',
                'title': 'Critical Risk Level Detected',
                'description': f'Overall risk score of {overall_risk:.2%} exceeds critical threshold',
                'recommended_actions': ['Immediate review required', 'Consider position limits']
            })
        elif overall_risk > self.config.risk_alert_threshold:
            alerts.append({
                'severity': 'high',
                'title': 'Elevated Risk Level',
                'description': f'Overall risk score of {overall_risk:.2%} requires attention',
                'recommended_actions': ['Enhanced monitoring', 'Review risk parameters']
            })

        # Engine-specific alerts
        for engine, profile in profiles.items():
            engine_risk = profile.get('overall_risk_score', Decimal('0.5'))
            if engine_risk > Decimal('0.8'):
                alerts.append({
                    'severity': 'high',
                    'title': f'High {engine.replace("_", " ").title()} Risk',
                    'description': f'Elevated risk detected in {engine} analysis',
                    'recommended_actions': [f'Review {engine} exposure', 'Consider mitigation strategies']
                })

        return alerts

    def _generate_risk_recommendations(self, profiles: Dict[str, Any], overall_risk: Decimal) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []

        if overall_risk > Decimal('0.7'):
            recommendations.append("Implement enhanced risk monitoring protocols")
            recommendations.append("Consider reducing exposure limits")

        # Engine-specific recommendations
        if profiles['defi_protocol'].get('overall_risk_score', Decimal('0.5')) > Decimal('0.6'):
            recommendations.append("Diversify DeFi protocol exposure")
            recommendations.append("Monitor protocol governance changes")

        if profiles['liquidity_cascade'].get('overall_risk_score', Decimal('0.5')) > Decimal('0.6'):
            recommendations.append("Increase portfolio liquidity buffers")
            recommendations.append("Monitor market depth conditions")

        if profiles['smart_contract'].get('overall_risk_score', Decimal('0.5')) > Decimal('0.6'):
            recommendations.append("Review smart contract audit status")
            recommendations.append("Limit exposure to unaudited contracts")

        if not recommendations:
            recommendations.append("Continue standard risk monitoring procedures")

        return recommendations

    def _calculate_overall_confidence(self, profiles: Dict[str, Any]) -> Decimal:
        """Calculate overall confidence in the risk assessment."""
        confidences = []
        for profile in profiles.values():
            confidences.append(profile.get('confidence', Decimal('0.5')))

        return sum(confidences) / len(confidences) if confidences else Decimal('0.5')

    def _calculate_assessment_completeness(self, profiles: Dict[str, Any]) -> Decimal:
        """Calculate assessment completeness score."""
        data_qualities = []
        for profile in profiles.values():
            data_qualities.append(profile.get('data_quality', Decimal('0.5')))

        return sum(data_qualities) / len(data_qualities) if data_qualities else Decimal('0.5')

    def _calculate_data_freshness(self, profiles: Dict[str, Any]) -> Decimal:
        """Calculate data freshness score."""
        freshness_scores = []
        current_time = datetime.utcnow()

        for profile in profiles.values():
            last_updated = profile.get('last_updated', current_time)
            age_seconds = (current_time - last_updated).total_seconds()

            if age_seconds < 300:       # < 5 minutes
                freshness_scores.append(Decimal('1.0'))
            elif age_seconds < 3600:    # < 1 hour
                freshness_scores.append(Decimal('0.8'))
            elif age_seconds < 86400:   # < 1 day
                freshness_scores.append(Decimal('0.6'))
            else:
                freshness_scores.append(Decimal('0.3'))

        return sum(freshness_scores) / len(freshness_scores) if freshness_scores else Decimal('0.5')

    # Cache management methods
    def _get_cached_assessment(self, cache_key: str) -> Optional[RiskAssessment]:
        """Get cached risk assessment if still valid."""
        if cache_key in self._risk_cache:
            assessment, timestamp = self._risk_cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < self.config.risk_cache_ttl:
                return assessment
        return None

    def _cache_assessment(self, cache_key: str, assessment: RiskAssessment) -> None:
        """Cache risk assessment."""
        self._risk_cache[cache_key] = (assessment, datetime.utcnow())

    # Default profile methods
    def _get_default_blockchain_profile(self) -> Dict[str, Any]:
        """Get default blockchain behavior profile."""
        return {
            'transaction_pattern_risk': Decimal('0.5'),
            'volume_anomaly_risk': Decimal('0.4'),
            'temporal_pattern_risk': Decimal('0.4'),
            'counterparty_risk': Decimal('0.3'),
            'overall_risk_score': Decimal('0.4'),
            'risk_level': RiskLevel.MEDIUM,
            'analysis_data': {},
            'data_quality': Decimal('0.3'),
            'confidence': Decimal('0.3'),
            'last_updated': datetime.utcnow()
        }

    def _get_default_defi_profile(self) -> Dict[str, Any]:
        """Get default DeFi protocol profile."""
        return {
            'protocol_concentration_risk': Decimal('0.3'),
            'liquidity_risk': Decimal('0.3'),
            'smart_contract_risk': Decimal('0.3'),
            'yield_hunting_risk': Decimal('0.3'),
            'leverage_risk': Decimal('0.2'),
            'bridge_risk': Decimal('0.1'),
            'overall_risk_score': Decimal('0.3'),
            'risk_level': RiskLevel.MEDIUM,
            'analysis_data': {},
            'data_quality': Decimal('0.3'),
            'confidence': Decimal('0.3'),
            'last_updated': datetime.utcnow()
        }

    def _get_default_smart_contract_profile(self) -> Dict[str, Any]:
        """Get default smart contract profile."""
        return {
            'code_quality_risk': Decimal('0.4'),
            'audit_status_risk': Decimal('0.5'),
            'complexity_risk': Decimal('0.3'),
            'upgrade_risk': Decimal('0.3'),
            'governance_risk': Decimal('0.3'),
            'economic_risk': Decimal('0.2'),
            'overall_risk_score': Decimal('0.35'),
            'risk_level': RiskLevel.MEDIUM,
            'analysis_data': {},
            'data_quality': Decimal('0.3'),
            'confidence': Decimal('0.3'),
            'last_updated': datetime.utcnow()
        }

    def _get_default_liquidity_profile(self) -> Dict[str, Any]:
        """Get default liquidity profile."""
        return {
            'market_depth_risk': Decimal('0.4'),
            'concentration_risk': Decimal('0.3'),
            'correlation_risk': Decimal('0.4'),
            'volatility_risk': Decimal('0.4'),
            'slippage_risk': Decimal('0.3'),
            'liquidation_cascade_risk': Decimal('0.2'),
            'overall_risk_score': Decimal('0.35'),
            'risk_level': RiskLevel.MEDIUM,
            'analysis_data': {},
            'data_quality': Decimal('0.3'),
            'confidence': Decimal('0.3'),
            'last_updated': datetime.utcnow()
        }

    def _get_default_governance_profile(self) -> Dict[str, Any]:
        """Get default governance profile."""
        return {
            'centralization_risk': Decimal('0.3'),
            'participation_risk': Decimal('0.4'),
            'decision_quality_risk': Decimal('0.3'),
            'attack_risk': Decimal('0.15'),
            'upgrade_risk': Decimal('0.2'),
            'community_risk': Decimal('0.25'),
            'overall_risk_score': Decimal('0.3'),
            'risk_level': RiskLevel.LOW,
            'analysis_data': {},
            'data_quality': Decimal('0.3'),
            'confidence': Decimal('0.3'),
            'last_updated': datetime.utcnow()
        }

    def _get_minimal_risk_profiles(self) -> Dict[str, Any]:
        """Get minimal risk profiles for error cases."""
        return {
            'blockchain_behavior': self._get_default_blockchain_profile(),
            'defi_protocol': self._get_default_defi_profile(),
            'smart_contract': self._get_default_smart_contract_profile(),
            'liquidity_cascade': self._get_default_liquidity_profile(),
            'governance_stability': self._get_default_governance_profile()
        }

    def _create_fallback_assessment(self, address: AlgorandAddress) -> RiskAssessment:
        """Create fallback assessment for error cases."""
        fallback_profile = RiskProfile(
            address=address,
            overall_risk_score=Decimal('50'),  # Medium risk
            risk_level=RiskLevel.MEDIUM,
            confidence=Decimal('0.3'),
            key_risk_factors=["Limited data available for assessment"],
            recommended_actions=["Manual review recommended"],
            assessment_timestamp=datetime.utcnow()
        )

        return RiskAssessment(
            address=address,
            risk_profile=fallback_profile,
            individual_profiles={},
            assessment_metadata={
                'assessment_completeness': Decimal('0.2'),
                'data_freshness': Decimal('0.5'),
                'model_version': '1.0.0',
                'assessment_timestamp': datetime.utcnow().isoformat(),
                'fallback_mode': True
            }
        )

    # Public utility methods
    def get_risk_thresholds(self) -> Dict[str, Decimal]:
        """Get current risk alert thresholds."""
        return {
            'low_risk_threshold': self.config.low_risk_threshold,
            'medium_risk_threshold': self.config.medium_risk_threshold,
            'high_risk_threshold': self.config.high_risk_threshold,
            'alert_threshold': self.config.risk_alert_threshold,
            'critical_threshold': self.config.critical_alert_threshold
        }

    async def validate_risk_data_quality(self) -> Dict[str, bool]:
        """Validate the quality of risk data sources."""
        validation_results = {}

        # Test data source availability
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config.service.algorand_reader_url}/health")
                validation_results['algorand_reader'] = response.status_code == 200
        except Exception:
            validation_results['algorand_reader'] = False

        return validation_results

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._risk_cache.clear()
        self._profile_cache.clear()
        logger.info("Risk assessment engine cache cleared")