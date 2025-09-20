"""
Foundation Dependency Analysis
Analyzes Algorand Foundation dependencies and centralization risks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

class DependencyRiskLevel(Enum):
    """Foundation dependency risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"

class FoundationDependencyAnalyzer:
    """Analyzes Algorand Foundation dependency risks"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

    async def analyze_foundation_dependencies(self, foundation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze foundation dependency risks"""
        try:
            # Funding dependency analysis
            funding_metrics = await self._analyze_funding_dependency(foundation_data)

            # Governance control analysis
            governance_metrics = await self._analyze_governance_control(foundation_data)

            # Development dependency analysis
            development_metrics = await self._analyze_development_dependency(foundation_data)

            # Strategic dependency analysis
            strategic_metrics = await self._analyze_strategic_dependencies(foundation_data)

            # Calculate overall dependency risk
            overall_risk = self._calculate_overall_dependency_risk(
                funding_metrics, governance_metrics, development_metrics, strategic_metrics
            )

            return {
                'timestamp': datetime.utcnow(),
                'overall_dependency_risk': overall_risk,
                'funding_metrics': funding_metrics,
                'governance_metrics': governance_metrics,
                'development_metrics': development_metrics,
                'strategic_metrics': strategic_metrics,
                'risk_level': self._determine_risk_level(overall_risk),
                'recommendations': self._generate_dependency_recommendations(
                    funding_metrics, governance_metrics, development_metrics, strategic_metrics
                )
            }

        except Exception as e:
            self.logger.error(f"Foundation dependency analysis failed: {e}")
            raise

    async def _analyze_funding_dependency(self, foundation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze funding dependency risks"""
        try:
            funding_data = foundation_data.get('funding', {})

            runway_months = funding_data.get('runway_months', 36)
            diversification = funding_data.get('revenue_diversification', 0.3)
            sustainability = funding_data.get('sustainability_score', 0.6)

            return {
                'runway_months': runway_months,
                'revenue_diversification': diversification,
                'sustainability_score': sustainability,
                'dependency_risk': self._calculate_funding_risk(runway_months, diversification, sustainability)
            }

        except Exception as e:
            self.logger.error(f"Funding dependency analysis failed: {e}")
            return {'dependency_risk': 5.0}

    def _calculate_funding_risk(self, runway_months: int, diversification: float, sustainability: float) -> float:
        """Calculate funding dependency risk score"""
        try:
            # Runway risk (higher risk if less runway)
            runway_risk = max(0, 10 - runway_months / 3)

            # Diversification risk (higher risk if less diversified)
            diversification_risk = (1 - diversification) * 5

            # Sustainability risk
            sustainability_risk = (1 - sustainability) * 5

            total_risk = (runway_risk + diversification_risk + sustainability_risk) / 3
            return min(10.0, total_risk)

        except Exception as e:
            self.logger.error(f"Funding risk calculation failed: {e}")
            return 5.0

    async def _analyze_governance_control(self, foundation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze governance control dependency"""
        try:
            governance_data = foundation_data.get('governance', {})

            foundation_voting_power = governance_data.get('foundation_voting_power', 0.15)
            foundation_influence = governance_data.get('foundation_influence_score', 0.4)
            community_autonomy = governance_data.get('community_autonomy_score', 0.7)

            return {
                'foundation_voting_power': foundation_voting_power,
                'foundation_influence': foundation_influence,
                'community_autonomy': community_autonomy,
                'dependency_risk': self._calculate_governance_risk(
                    foundation_voting_power, foundation_influence, community_autonomy
                )
            }

        except Exception as e:
            self.logger.error(f"Governance control analysis failed: {e}")
            return {'dependency_risk': 5.0}

    def _calculate_governance_risk(self, voting_power: float, influence: float, autonomy: float) -> float:
        """Calculate governance dependency risk"""
        try:
            # Higher risk if foundation has too much control
            voting_risk = voting_power * 20  # Scale to 0-10
            influence_risk = influence * 10
            autonomy_risk = (1 - autonomy) * 10

            total_risk = (voting_risk + influence_risk + autonomy_risk) / 3
            return min(10.0, total_risk)

        except Exception as e:
            self.logger.error(f"Governance risk calculation failed: {e}")
            return 5.0

    async def _analyze_development_dependency(self, foundation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze development dependency risks"""
        try:
            dev_data = foundation_data.get('development', {})

            core_developers = dev_data.get('foundation_core_developers', 15)
            total_developers = dev_data.get('total_ecosystem_developers', 200)
            foundation_commits = dev_data.get('foundation_commit_percentage', 0.6)

            return {
                'foundation_core_developers': core_developers,
                'total_ecosystem_developers': total_developers,
                'foundation_commit_percentage': foundation_commits,
                'dependency_risk': self._calculate_development_risk(
                    core_developers, total_developers, foundation_commits
                )
            }

        except Exception as e:
            self.logger.error(f"Development dependency analysis failed: {e}")
            return {'dependency_risk': 5.0}

    def _calculate_development_risk(self, core_devs: int, total_devs: int, commit_pct: float) -> float:
        """Calculate development dependency risk"""
        try:
            # Bus factor risk
            bus_factor_risk = max(0, 10 - core_devs / 2)

            # Foundation dominance risk
            dominance_risk = commit_pct * 10

            # Ecosystem diversity risk
            diversity_ratio = core_devs / max(total_devs, 1)
            diversity_risk = diversity_ratio * 15

            total_risk = (bus_factor_risk + dominance_risk + diversity_risk) / 3
            return min(10.0, total_risk)

        except Exception as e:
            self.logger.error(f"Development risk calculation failed: {e}")
            return 5.0

    async def _analyze_strategic_dependencies(self, foundation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze strategic partnership dependencies"""
        try:
            strategic_data = foundation_data.get('strategic', {})

            partnership_concentration = strategic_data.get('partnership_concentration', 0.3)
            vendor_dependencies = strategic_data.get('critical_vendor_count', 5)
            relationship_stability = strategic_data.get('relationship_stability_score', 0.8)

            return {
                'partnership_concentration': partnership_concentration,
                'critical_vendor_count': vendor_dependencies,
                'relationship_stability': relationship_stability,
                'dependency_risk': self._calculate_strategic_risk(
                    partnership_concentration, vendor_dependencies, relationship_stability
                )
            }

        except Exception as e:
            self.logger.error(f"Strategic dependency analysis failed: {e}")
            return {'dependency_risk': 5.0}

    def _calculate_strategic_risk(self, concentration: float, vendors: int, stability: float) -> float:
        """Calculate strategic dependency risk"""
        try:
            # Concentration risk
            concentration_risk = concentration * 8

            # Vendor dependency risk
            vendor_risk = max(0, vendors - 3) * 1.5

            # Stability risk
            stability_risk = (1 - stability) * 6

            total_risk = (concentration_risk + vendor_risk + stability_risk) / 3
            return min(10.0, total_risk)

        except Exception as e:
            self.logger.error(f"Strategic risk calculation failed: {e}")
            return 5.0

    def _calculate_overall_dependency_risk(self, funding_metrics: Dict[str, Any],
                                         governance_metrics: Dict[str, Any],
                                         development_metrics: Dict[str, Any],
                                         strategic_metrics: Dict[str, Any]) -> float:
        """Calculate overall foundation dependency risk"""
        try:
            weights = {
                'funding': 0.30,
                'governance': 0.25,
                'development': 0.25,
                'strategic': 0.20
            }

            weighted_risk = (
                funding_metrics.get('dependency_risk', 5.0) * weights['funding'] +
                governance_metrics.get('dependency_risk', 5.0) * weights['governance'] +
                development_metrics.get('dependency_risk', 5.0) * weights['development'] +
                strategic_metrics.get('dependency_risk', 5.0) * weights['strategic']
            )

            return min(10.0, weighted_risk)

        except Exception as e:
            self.logger.error(f"Overall dependency risk calculation failed: {e}")
            return 5.0

    def _determine_risk_level(self, dependency_risk: float) -> DependencyRiskLevel:
        """Determine dependency risk level"""
        if dependency_risk >= 8.0:
            return DependencyRiskLevel.CRITICAL
        elif dependency_risk >= 6.0:
            return DependencyRiskLevel.HIGH
        elif dependency_risk >= 4.0:
            return DependencyRiskLevel.MODERATE
        else:
            return DependencyRiskLevel.LOW

    def _generate_dependency_recommendations(self, funding_metrics: Dict[str, Any],
                                           governance_metrics: Dict[str, Any],
                                           development_metrics: Dict[str, Any],
                                           strategic_metrics: Dict[str, Any]) -> List[str]:
        """Generate dependency risk mitigation recommendations"""
        recommendations = []

        try:
            # Funding recommendations
            if funding_metrics.get('dependency_risk', 5.0) > 6.0:
                recommendations.append("Diversify funding sources and revenue streams")

            # Governance recommendations
            if governance_metrics.get('dependency_risk', 5.0) > 6.0:
                recommendations.append("Increase community governance participation")

            # Development recommendations
            if development_metrics.get('dependency_risk', 5.0) > 6.0:
                recommendations.append("Expand developer ecosystem beyond foundation")

            # Strategic recommendations
            if strategic_metrics.get('dependency_risk', 5.0) > 6.0:
                recommendations.append("Reduce strategic partnership concentration")

            # General recommendations
            recommendations.extend([
                "Monitor foundation dependency metrics regularly",
                "Develop ecosystem independence roadmap",
                "Strengthen community-driven initiatives"
            ])

            return recommendations[:5]

        except Exception as e:
            self.logger.error(f"Dependency recommendation generation failed: {e}")
            return ["Review foundation dependency risks"]

# Export main class
__all__ = ['FoundationDependencyAnalyzer', 'DependencyRiskLevel']