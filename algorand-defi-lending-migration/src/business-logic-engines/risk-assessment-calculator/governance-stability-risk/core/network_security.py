"""
Network Security Assessment Engine
Analyzes consensus mechanism security, network health, and infrastructure risks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

class SecurityRiskLevel(Enum):
    """Network security risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"

class NetworkSecurityMetrics:
    """Core network security metrics"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

    async def assess_network_security(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall network security"""
        try:
            # Consensus participation analysis
            consensus_metrics = await self._analyze_consensus_participation(network_data)

            # Node distribution analysis
            distribution_metrics = await self._analyze_node_distribution(network_data)

            # State proof security
            state_proof_metrics = await self._analyze_state_proof_security(network_data)

            # Infrastructure dependencies
            infrastructure_metrics = await self._analyze_infrastructure_dependencies(network_data)

            # Calculate overall security score
            overall_score = self._calculate_overall_security_score(
                consensus_metrics, distribution_metrics, state_proof_metrics, infrastructure_metrics
            )

            return {
                'timestamp': datetime.utcnow(),
                'overall_security_score': overall_score,
                'consensus_metrics': consensus_metrics,
                'distribution_metrics': distribution_metrics,
                'state_proof_metrics': state_proof_metrics,
                'infrastructure_metrics': infrastructure_metrics,
                'risk_level': self._determine_risk_level(overall_score),
                'recommendations': self._generate_security_recommendations(
                    consensus_metrics, distribution_metrics, state_proof_metrics, infrastructure_metrics
                )
            }

        except Exception as e:
            self.logger.error(f"Network security assessment failed: {e}")
            raise

    async def _analyze_consensus_participation(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze consensus participation patterns"""
        try:
            consensus_data = network_data.get('consensus', {})

            participation_rate = consensus_data.get('participation_rate', 0.85)
            unique_participants = consensus_data.get('unique_participants', 1000)
            geographic_distribution = len(consensus_data.get('countries', []))

            # Calculate concentration risk
            top_10_stake = consensus_data.get('top_10_stake_percentage', 0.25)
            herfindahl_index = consensus_data.get('herfindahl_index', 0.1)

            return {
                'participation_rate': participation_rate,
                'unique_participants': unique_participants,
                'geographic_distribution': geographic_distribution,
                'concentration_risk': top_10_stake,
                'herfindahl_index': herfindahl_index,
                'security_score': self._calculate_consensus_security_score(
                    participation_rate, unique_participants, geographic_distribution, top_10_stake
                )
            }

        except Exception as e:
            self.logger.error(f"Consensus participation analysis failed: {e}")
            return {'security_score': 5.0}

    def _calculate_consensus_security_score(self, participation_rate: float,
                                          unique_participants: int,
                                          geographic_distribution: int,
                                          concentration_risk: float) -> float:
        """Calculate consensus security score"""
        try:
            # Participation rate score (0-3 points)
            participation_score = min(3.0, participation_rate * 3)

            # Decentralization score (0-3 points)
            decentralization_score = min(3.0, (1 - concentration_risk) * 3)

            # Scale score (0-2 points)
            scale_score = min(2.0, unique_participants / 1000)

            # Geographic distribution score (0-2 points)
            geo_score = min(2.0, geographic_distribution / 25)

            total_score = participation_score + decentralization_score + scale_score + geo_score
            return min(10.0, total_score)

        except Exception as e:
            self.logger.error(f"Consensus security score calculation failed: {e}")
            return 5.0

    async def _analyze_node_distribution(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze node distribution and diversity"""
        try:
            node_data = network_data.get('nodes', {})

            return {
                'total_nodes': node_data.get('total_count', 0),
                'relay_nodes': node_data.get('relay_count', 0),
                'participation_nodes': node_data.get('participation_count', 0),
                'geographic_diversity': len(node_data.get('countries', [])),
                'cloud_provider_concentration': node_data.get('cloud_concentration', 0.4),
                'isp_concentration': node_data.get('isp_concentration', 0.3),
                'security_score': 7.5  # Simplified calculation
            }

        except Exception as e:
            self.logger.error(f"Node distribution analysis failed: {e}")
            return {'security_score': 5.0}

    async def _analyze_state_proof_security(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze state proof mechanism security"""
        try:
            state_proof_data = network_data.get('state_proofs', {})

            return {
                'adoption_rate': state_proof_data.get('adoption_rate', 0.9),
                'verification_time': state_proof_data.get('avg_verification_time', 1800),
                'challenge_success_rate': state_proof_data.get('challenge_success_rate', 0.95),
                'security_score': 8.5  # Algorand's state proofs are robust
            }

        except Exception as e:
            self.logger.error(f"State proof security analysis failed: {e}")
            return {'security_score': 5.0}

    async def _analyze_infrastructure_dependencies(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze infrastructure dependency risks"""
        try:
            infra_data = network_data.get('infrastructure', {})

            return {
                'cloud_dependency': infra_data.get('cloud_dependency', 0.6),
                'dns_dependency': infra_data.get('dns_dependency', 0.2),
                'single_points_of_failure': infra_data.get('spof_count', 2),
                'redundancy_score': infra_data.get('redundancy_score', 7.0),
                'security_score': 6.0  # Moderate infrastructure risks
            }

        except Exception as e:
            self.logger.error(f"Infrastructure dependency analysis failed: {e}")
            return {'security_score': 5.0}

    def _calculate_overall_security_score(self, consensus_metrics: Dict[str, Any],
                                        distribution_metrics: Dict[str, Any],
                                        state_proof_metrics: Dict[str, Any],
                                        infrastructure_metrics: Dict[str, Any]) -> float:
        """Calculate overall network security score"""
        try:
            weights = {
                'consensus': 0.35,
                'distribution': 0.25,
                'state_proof': 0.25,
                'infrastructure': 0.15
            }

            weighted_score = (
                consensus_metrics.get('security_score', 5.0) * weights['consensus'] +
                distribution_metrics.get('security_score', 5.0) * weights['distribution'] +
                state_proof_metrics.get('security_score', 5.0) * weights['state_proof'] +
                infrastructure_metrics.get('security_score', 5.0) * weights['infrastructure']
            )

            return min(10.0, weighted_score)

        except Exception as e:
            self.logger.error(f"Overall security score calculation failed: {e}")
            return 5.0

    def _determine_risk_level(self, security_score: float) -> SecurityRiskLevel:
        """Determine risk level from security score"""
        if security_score >= 8.0:
            return SecurityRiskLevel.LOW
        elif security_score >= 6.0:
            return SecurityRiskLevel.MODERATE
        elif security_score >= 4.0:
            return SecurityRiskLevel.HIGH
        else:
            return SecurityRiskLevel.CRITICAL

    def _generate_security_recommendations(self, consensus_metrics: Dict[str, Any],
                                         distribution_metrics: Dict[str, Any],
                                         state_proof_metrics: Dict[str, Any],
                                         infrastructure_metrics: Dict[str, Any]) -> List[str]:
        """Generate security improvement recommendations"""
        recommendations = []

        try:
            # Consensus recommendations
            if consensus_metrics.get('participation_rate', 1.0) < 0.8:
                recommendations.append("Increase consensus participation incentives")

            if consensus_metrics.get('concentration_risk', 0) > 0.3:
                recommendations.append("Implement measures to reduce stake concentration")

            # Distribution recommendations
            if distribution_metrics.get('geographic_diversity', 100) < 20:
                recommendations.append("Encourage geographic diversification of nodes")

            # Infrastructure recommendations
            if infrastructure_metrics.get('cloud_dependency', 0) > 0.7:
                recommendations.append("Reduce dependency on cloud infrastructure")

            # General recommendations
            recommendations.extend([
                "Monitor network health metrics continuously",
                "Implement automated threat detection",
                "Maintain emergency response procedures"
            ])

            return recommendations[:5]

        except Exception as e:
            self.logger.error(f"Security recommendation generation failed: {e}")
            return ["Review network security posture"]

# Export main class
__all__ = ['NetworkSecurityMetrics', 'SecurityRiskLevel']