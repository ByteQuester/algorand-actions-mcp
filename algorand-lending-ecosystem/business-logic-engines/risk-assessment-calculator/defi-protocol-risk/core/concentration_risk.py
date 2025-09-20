"""
DeFi Concentration Risk Analysis
Analyzes protocol concentration and diversification risks in DeFi portfolios
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConcentrationMetrics:
    """Concentration risk metrics"""
    herfindahl_index: float          # HHI concentration measure
    effective_protocols: float       # Effective number of protocols
    max_exposure_percentage: float   # Largest single exposure
    top_3_concentration: float       # Top 3 protocols concentration
    gini_coefficient: float          # Inequality measure
    shannon_diversity: float         # Information diversity
    risk_score: float               # Overall concentration risk score

@dataclass
class DiversificationAnalysis:
    """Portfolio diversification analysis"""
    protocol_count: int
    category_count: int
    tier_distribution: Dict[str, float]
    category_distribution: Dict[str, float]
    geographic_distribution: Dict[str, float]
    correlation_risk: float
    diversification_score: float
    recommendations: List[str]

@dataclass
class ConcentrationRiskAssessment:
    """Complete concentration risk assessment"""
    concentration_metrics: ConcentrationMetrics
    diversification_analysis: DiversificationAnalysis
    stress_test_results: Dict[str, float]
    liquidity_concentration: Dict[str, float]
    governance_concentration: Dict[str, float]
    overall_risk_score: float
    risk_level: str
    action_required: bool
    timestamp: datetime

class ConcentrationRiskAnalyzer:
    """Analyzes concentration and diversification risks in DeFi portfolios"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the concentration risk analyzer"""
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    async def analyze_concentration_risk(self, positions: Dict[str, float]) -> ConcentrationRiskAssessment:
        """Analyze comprehensive concentration risk"""
        logger.info("Analyzing DeFi concentration risk...")

        if not positions:
            raise ValueError("No positions provided for concentration analysis")

        # Calculate concentration metrics
        concentration_metrics = self._calculate_concentration_metrics(positions)

        # Analyze diversification
        diversification_analysis = await self._analyze_diversification(positions)

        # Run stress tests
        stress_test_results = await self._run_concentration_stress_tests(positions)

        # Analyze liquidity concentration
        liquidity_concentration = await self._analyze_liquidity_concentration(positions)

        # Analyze governance concentration
        governance_concentration = await self._analyze_governance_concentration(positions)

        # Calculate overall risk score
        overall_risk_score = self._calculate_overall_concentration_risk(
            concentration_metrics,
            diversification_analysis,
            stress_test_results
        )

        # Determine risk level and action required
        risk_level, action_required = self._determine_risk_level_and_action(overall_risk_score)

        return ConcentrationRiskAssessment(
            concentration_metrics=concentration_metrics,
            diversification_analysis=diversification_analysis,
            stress_test_results=stress_test_results,
            liquidity_concentration=liquidity_concentration,
            governance_concentration=governance_concentration,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            action_required=action_required,
            timestamp=datetime.now()
        )

    def _calculate_concentration_metrics(self, positions: Dict[str, float]) -> ConcentrationMetrics:
        """Calculate various concentration metrics"""
        total_value = sum(positions.values())
        if total_value == 0:
            raise ValueError("Total portfolio value is zero")

        # Calculate proportions
        proportions = np.array([value / total_value for value in positions.values()])
        proportions = proportions[proportions > 0]  # Remove zero positions

        # Herfindahl-Hirschman Index
        hhi = np.sum(proportions ** 2)

        # Effective number of protocols (1/HHI)
        effective_protocols = 1 / hhi if hhi > 0 else 0

        # Maximum exposure percentage
        max_exposure = np.max(proportions) * 100

        # Top 3 concentration
        sorted_proportions = np.sort(proportions)[::-1]
        top_3_concentration = np.sum(sorted_proportions[:3]) * 100

        # Gini coefficient (inequality measure)
        gini_coefficient = self._calculate_gini_coefficient(proportions)

        # Shannon diversity index
        shannon_diversity = -np.sum(proportions * np.log2(proportions + 1e-10))

        # Overall concentration risk score
        risk_score = self._calculate_concentration_risk_score(
            hhi, max_exposure, top_3_concentration, gini_coefficient
        )

        return ConcentrationMetrics(
            herfindahl_index=hhi,
            effective_protocols=effective_protocols,
            max_exposure_percentage=max_exposure,
            top_3_concentration=top_3_concentration,
            gini_coefficient=gini_coefficient,
            shannon_diversity=shannon_diversity,
            risk_score=risk_score
        )

    def _calculate_gini_coefficient(self, proportions: np.ndarray) -> float:
        """Calculate Gini coefficient for inequality measurement"""
        if len(proportions) == 0:
            return 0.0

        # Sort proportions
        sorted_proportions = np.sort(proportions)
        n = len(sorted_proportions)

        # Calculate Gini coefficient
        index = np.arange(1, n + 1)
        gini = (2 * np.sum(index * sorted_proportions)) / (n * np.sum(sorted_proportions)) - (n + 1) / n

        return max(0.0, gini)

    def _calculate_concentration_risk_score(self, hhi: float, max_exposure: float,
                                          top_3_concentration: float, gini: float) -> float:
        """Calculate overall concentration risk score"""
        # Normalize each metric to 0-1 scale
        hhi_score = min(hhi * 4, 1.0)  # HHI of 0.25 = max score
        max_exposure_score = min(max_exposure / 40, 1.0)  # 40% = max score
        top_3_score = min(top_3_concentration / 80, 1.0)  # 80% = max score
        gini_score = gini  # Already 0-1

        # Weighted combination
        weights = self.config.get('concentration_risk_weights', {
            'hhi_weight': 0.3,
            'max_exposure_weight': 0.3,
            'top_3_weight': 0.25,
            'gini_weight': 0.15
        })

        risk_score = (
            hhi_score * weights.get('hhi_weight', 0.3) +
            max_exposure_score * weights.get('max_exposure_weight', 0.3) +
            top_3_score * weights.get('top_3_weight', 0.25) +
            gini_score * weights.get('gini_weight', 0.15)
        )

        return min(risk_score, 1.0)

    async def _analyze_diversification(self, positions: Dict[str, float]) -> DiversificationAnalysis:
        """Analyze portfolio diversification across multiple dimensions"""
        protocols = self.config.get('algorand_protocols', {})
        total_value = sum(positions.values())

        # Protocol and category counts
        protocol_count = len([p for p, v in positions.items() if v > 0])
        categories = set()
        category_distribution = {}
        tier_distribution = {}

        for protocol, value in positions.items():
            if value <= 0:
                continue

            protocol_config = protocols.get(protocol, {})
            category = protocol_config.get('category', 'unknown')
            tier = protocol_config.get('risk_tier', 'tier_3')

            categories.add(category)

            # Update distributions
            weight = value / total_value
            category_distribution[category] = category_distribution.get(category, 0) + weight
            tier_distribution[tier] = tier_distribution.get(tier, 0) + weight

        category_count = len(categories)

        # Geographic distribution (simplified - based on protocol origins)
        geographic_distribution = await self._calculate_geographic_distribution(positions)

        # Correlation risk analysis
        correlation_risk = await self._calculate_correlation_risk(positions)

        # Calculate diversification score
        diversification_score = self._calculate_diversification_score(
            protocol_count, category_count, category_distribution, tier_distribution
        )

        # Generate diversification recommendations
        recommendations = self._generate_diversification_recommendations(
            protocol_count, category_count, category_distribution, tier_distribution, correlation_risk
        )

        return DiversificationAnalysis(
            protocol_count=protocol_count,
            category_count=category_count,
            tier_distribution=dict(tier_distribution),
            category_distribution=dict(category_distribution),
            geographic_distribution=geographic_distribution,
            correlation_risk=correlation_risk,
            diversification_score=diversification_score,
            recommendations=recommendations
        )

    async def _calculate_geographic_distribution(self, positions: Dict[str, float]) -> Dict[str, float]:
        """Calculate geographic distribution of protocol origins"""
        # Simplified geographic mapping
        protocol_geography = {
            'algofi': 'North America',
            'folks_finance': 'Europe',
            'tinyman': 'North America',
            'pact': 'North America',
            'humble_defi': 'Asia',
            'algomint': 'North America',
            'yieldly': 'North America'
        }

        total_value = sum(positions.values())
        geographic_distribution = {}

        for protocol, value in positions.items():
            if value <= 0:
                continue

            geography = protocol_geography.get(protocol, 'Unknown')
            weight = value / total_value
            geographic_distribution[geography] = geographic_distribution.get(geography, 0) + weight

        return geographic_distribution

    async def _calculate_correlation_risk(self, positions: Dict[str, float]) -> float:
        """Calculate correlation risk between protocol positions"""
        correlations = self.config.get('protocol_correlations', {})
        total_value = sum(positions.values())

        if len(positions) < 2:
            return 0.0

        weighted_correlation_sum = 0.0
        total_weight = 0.0

        protocols = list(positions.keys())
        for i, protocol1 in enumerate(protocols):
            for protocol2 in protocols[i+1:]:
                value1 = positions[protocol1]
                value2 = positions[protocol2]

                if value1 <= 0 or value2 <= 0:
                    continue

                # Get correlation coefficient
                corr_key = f"{protocol1}_{protocol2}"
                reverse_key = f"{protocol2}_{protocol1}"
                correlation = correlations.get(corr_key, correlations.get(reverse_key, 0.5))

                # Weight by position sizes
                weight1 = value1 / total_value
                weight2 = value2 / total_value
                pair_weight = weight1 * weight2

                weighted_correlation_sum += correlation * pair_weight
                total_weight += pair_weight

        return weighted_correlation_sum / total_weight if total_weight > 0 else 0.0

    def _calculate_diversification_score(self, protocol_count: int, category_count: int,
                                       category_distribution: Dict[str, float],
                                       tier_distribution: Dict[str, float]) -> float:
        """Calculate overall diversification score"""
        # Protocol count score (0-1)
        protocol_score = min(protocol_count / 5, 1.0)  # 5+ protocols = perfect

        # Category count score (0-1)
        category_score = min(category_count / 3, 1.0)  # 3+ categories = perfect

        # Category balance score (using Shannon entropy)
        category_entropy = 0.0
        for weight in category_distribution.values():
            if weight > 0:
                category_entropy -= weight * np.log2(weight)

        max_category_entropy = np.log2(min(3, len(category_distribution)))
        category_balance_score = category_entropy / max_category_entropy if max_category_entropy > 0 else 0

        # Tier distribution score (prefer tier 1 protocols)
        tier_1_weight = tier_distribution.get('tier_1', 0)
        tier_2_weight = tier_distribution.get('tier_2', 0)
        tier_3_weight = tier_distribution.get('tier_3', 0)

        tier_quality_score = (tier_1_weight * 1.0) + (tier_2_weight * 0.7) + (tier_3_weight * 0.3)

        # Combine scores
        diversification_score = (
            protocol_score * 0.3 +
            category_score * 0.25 +
            category_balance_score * 0.25 +
            tier_quality_score * 0.2
        )

        return min(diversification_score, 1.0)

    def _generate_diversification_recommendations(self, protocol_count: int, category_count: int,
                                                category_distribution: Dict[str, float],
                                                tier_distribution: Dict[str, float],
                                                correlation_risk: float) -> List[str]:
        """Generate diversification improvement recommendations"""
        recommendations = []

        # Protocol count recommendations
        if protocol_count < 3:
            recommendations.append(
                f"Increase protocol diversification: Consider adding {3 - protocol_count} more protocols"
            )

        # Category diversification recommendations
        if category_count < 3:
            missing_categories = []
            existing_categories = set(category_distribution.keys())
            all_categories = {'lending', 'dex', 'staking', 'bridge'}
            missing = all_categories - existing_categories

            for category in missing:
                if len(recommendations) < 5:  # Limit recommendations
                    recommendations.append(f"Consider adding {category} protocol exposure")

        # Category concentration recommendations
        for category, weight in category_distribution.items():
            if weight > 0.6:  # 60% threshold
                recommendations.append(
                    f"Reduce {category} protocol concentration below 60% (currently {weight*100:.1f}%)"
                )

        # Tier distribution recommendations
        tier_3_weight = tier_distribution.get('tier_3', 0)
        if tier_3_weight > 0.2:  # 20% threshold
            recommendations.append(
                f"Reduce Tier 3 protocol exposure below 20% (currently {tier_3_weight*100:.1f}%)"
            )

        tier_1_weight = tier_distribution.get('tier_1', 0)
        if tier_1_weight < 0.6:  # 60% minimum
            recommendations.append(
                f"Increase Tier 1 protocol exposure above 60% (currently {tier_1_weight*100:.1f}%)"
            )

        # Correlation risk recommendations
        if correlation_risk > 0.7:
            recommendations.append(
                f"High correlation risk detected ({correlation_risk:.2f}): Consider protocols with lower correlation"
            )

        return recommendations[:5]  # Limit to top 5 recommendations

    async def _run_concentration_stress_tests(self, positions: Dict[str, float]) -> Dict[str, float]:
        """Run stress tests on concentration risk"""
        stress_tests = {}

        # Test 1: Largest protocol failure
        largest_protocol = max(positions.items(), key=lambda x: x[1])
        largest_impact = largest_protocol[1] / sum(positions.values())
        stress_tests['largest_protocol_failure'] = largest_impact

        # Test 2: Category failure (e.g., all lending protocols fail)
        protocols = self.config.get('algorand_protocols', {})
        category_impacts = {}

        for protocol, value in positions.items():
            if value <= 0:
                continue

            category = protocols.get(protocol, {}).get('category', 'unknown')
            category_impacts[category] = category_impacts.get(category, 0) + value

        total_value = sum(positions.values())
        max_category_impact = max(category_impacts.values()) / total_value if category_impacts else 0
        stress_tests['category_failure'] = max_category_impact

        # Test 3: Tier 3 protocol failure
        tier_3_impact = 0
        for protocol, value in positions.items():
            if value <= 0:
                continue

            tier = protocols.get(protocol, {}).get('risk_tier', 'tier_3')
            if tier == 'tier_3':
                tier_3_impact += value

        stress_tests['tier_3_failure'] = tier_3_impact / total_value if total_value > 0 else 0

        # Test 4: Top 2 protocols failure
        sorted_positions = sorted(positions.items(), key=lambda x: x[1], reverse=True)
        top_2_impact = (sorted_positions[0][1] + (sorted_positions[1][1] if len(sorted_positions) > 1 else 0))
        stress_tests['top_2_failure'] = top_2_impact / total_value if total_value > 0 else 0

        return stress_tests

    async def _analyze_liquidity_concentration(self, positions: Dict[str, float]) -> Dict[str, float]:
        """Analyze concentration in low-liquidity protocols"""
        protocols = self.config.get('algorand_protocols', {})
        total_value = sum(positions.values())

        liquidity_tiers = {'high': 0, 'medium': 0, 'low': 0}

        for protocol, value in positions.items():
            if value <= 0:
                continue

            # Get protocol liquidity tier (simplified)
            protocol_config = protocols.get(protocol, {})
            tvl_weight = protocol_config.get('tvl_weight', 0.01)

            # Classify liquidity based on TVL weight
            if tvl_weight >= 0.2:
                tier = 'high'
            elif tvl_weight >= 0.05:
                tier = 'medium'
            else:
                tier = 'low'

            liquidity_tiers[tier] += value

        # Convert to percentages
        return {tier: amount / total_value for tier, amount in liquidity_tiers.items()}

    async def _analyze_governance_concentration(self, positions: Dict[str, float]) -> Dict[str, float]:
        """Analyze concentration risk from governance token concentration"""
        protocols = self.config.get('algorand_protocols', {})
        total_value = sum(positions.values())

        governance_risk_levels = {'low': 0, 'medium': 0, 'high': 0}

        for protocol, value in positions.items():
            if value <= 0:
                continue

            protocol_config = protocols.get(protocol, {})
            governance_concentration = protocol_config.get('governance_concentration', 0.5)

            # Classify governance risk
            if governance_concentration <= 0.3:
                risk_level = 'low'
            elif governance_concentration <= 0.6:
                risk_level = 'medium'
            else:
                risk_level = 'high'

            governance_risk_levels[risk_level] += value

        # Convert to percentages
        return {level: amount / total_value for level, amount in governance_risk_levels.items()}

    def _calculate_overall_concentration_risk(self, concentration_metrics: ConcentrationMetrics,
                                            diversification_analysis: DiversificationAnalysis,
                                            stress_test_results: Dict[str, float]) -> float:
        """Calculate overall concentration risk score"""
        # Base concentration risk
        base_risk = concentration_metrics.risk_score

        # Diversification adjustment
        diversification_adjustment = 1.0 - (diversification_analysis.diversification_score * 0.3)

        # Stress test adjustment
        max_stress_impact = max(stress_test_results.values()) if stress_test_results else 0
        stress_adjustment = 1.0 + (max_stress_impact * 0.5)

        # Correlation risk adjustment
        correlation_adjustment = 1.0 + (diversification_analysis.correlation_risk * 0.2)

        # Combine adjustments
        overall_risk = base_risk * diversification_adjustment * stress_adjustment * correlation_adjustment

        return min(overall_risk, 1.0)

    def _determine_risk_level_and_action(self, risk_score: float) -> Tuple[str, bool]:
        """Determine risk level and whether action is required"""
        if risk_score >= 0.8:
            return "CRITICAL", True
        elif risk_score >= 0.6:
            return "HIGH", True
        elif risk_score >= 0.4:
            return "MODERATE", False
        elif risk_score >= 0.2:
            return "LOW", False
        else:
            return "MINIMAL", False

    async def get_rebalancing_suggestions(self, positions: Dict[str, float],
                                        target_concentrations: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Generate portfolio rebalancing suggestions to reduce concentration risk"""
        current_analysis = await self.analyze_concentration_risk(positions)

        if not target_concentrations:
            # Use default targets from config
            target_concentrations = {
                'single_protocol_max': 0.3,  # 30% max in single protocol
                'category_max': 0.5,         # 50% max in single category
                'tier_1_min': 0.6,           # 60% min in tier 1 protocols
                'tier_3_max': 0.15           # 15% max in tier 3 protocols
            }

        total_value = sum(positions.values())
        protocols = self.config.get('algorand_protocols', {})

        rebalancing_actions = []

        # Check individual protocol concentrations
        for protocol, value in positions.items():
            percentage = value / total_value
            if percentage > target_concentrations.get('single_protocol_max', 0.3):
                target_value = total_value * target_concentrations['single_protocol_max']
                reduction = value - target_value

                rebalancing_actions.append({
                    'action': 'reduce',
                    'protocol': protocol,
                    'current_value': value,
                    'target_value': target_value,
                    'reduction_amount': reduction,
                    'reason': f"Reduce concentration below {target_concentrations['single_protocol_max']*100:.0f}%"
                })

        # Check category concentrations
        category_values = {}
        for protocol, value in positions.items():
            if value <= 0:
                continue

            category = protocols.get(protocol, {}).get('category', 'unknown')
            category_values[category] = category_values.get(category, 0) + value

        for category, total_category_value in category_values.items():
            percentage = total_category_value / total_value
            if percentage > target_concentrations.get('category_max', 0.5):
                rebalancing_actions.append({
                    'action': 'diversify_category',
                    'category': category,
                    'current_percentage': percentage,
                    'target_percentage': target_concentrations['category_max'],
                    'reason': f"Reduce {category} concentration below {target_concentrations['category_max']*100:.0f}%"
                })

        return {
            'current_analysis': current_analysis,
            'rebalancing_actions': rebalancing_actions,
            'target_concentrations': target_concentrations,
            'estimated_risk_reduction': self._estimate_risk_reduction(rebalancing_actions, current_analysis)
        }

    def _estimate_risk_reduction(self, rebalancing_actions: List[Dict], current_analysis: ConcentrationRiskAssessment) -> float:
        """Estimate risk reduction from rebalancing actions"""
        if not rebalancing_actions:
            return 0.0

        # Simple estimation: assume 20% risk reduction for major rebalancing
        major_rebalancing = any(
            action.get('reduction_amount', 0) > 10000 or  # $10k+ reduction
            action.get('current_percentage', 0) - action.get('target_percentage', 0) > 0.1  # 10%+ reduction
            for action in rebalancing_actions
        )

        if major_rebalancing:
            return min(current_analysis.overall_risk_score * 0.3, 0.3)  # Up to 30% risk reduction
        else:
            return min(current_analysis.overall_risk_score * 0.1, 0.1)  # Up to 10% risk reduction

# Example usage
async def main():
    """Example usage of the concentration risk analyzer"""
    analyzer = ConcentrationRiskAnalyzer()

    # Example positions with high concentration
    positions = {
        'algofi': 70000,        # $70k in Algofi (70% concentration)
        'tinyman': 20000,       # $20k in Tinyman
        'pact': 10000          # $10k in Pact
    }

    # Analyze concentration risk
    risk_assessment = await analyzer.analyze_concentration_risk(positions)

    print(f"\n=== Concentration Risk Analysis ===")
    print(f"Overall Risk Score: {risk_assessment.overall_risk_score:.2f}")
    print(f"Risk Level: {risk_assessment.risk_level}")
    print(f"Action Required: {risk_assessment.action_required}")

    print(f"\n=== Concentration Metrics ===")
    metrics = risk_assessment.concentration_metrics
    print(f"Herfindahl Index: {metrics.herfindahl_index:.3f}")
    print(f"Effective Protocols: {metrics.effective_protocols:.1f}")
    print(f"Max Exposure: {metrics.max_exposure_percentage:.1f}%")
    print(f"Top 3 Concentration: {metrics.top_3_concentration:.1f}%")
    print(f"Gini Coefficient: {metrics.gini_coefficient:.3f}")

    print(f"\n=== Diversification Analysis ===")
    div = risk_assessment.diversification_analysis
    print(f"Protocol Count: {div.protocol_count}")
    print(f"Category Count: {div.category_count}")
    print(f"Diversification Score: {div.diversification_score:.2f}")
    print(f"Correlation Risk: {div.correlation_risk:.2f}")

    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(div.recommendations, 1):
        print(f"{i}. {rec}")

    # Get rebalancing suggestions
    rebalancing = await analyzer.get_rebalancing_suggestions(positions)
    print(f"\n=== Rebalancing Suggestions ===")
    for action in rebalancing['rebalancing_actions']:
        if action['action'] == 'reduce':
            print(f"Reduce {action['protocol']}: ${action['reduction_amount']:,.0f} "
                  f"(${action['current_value']:,.0f} → ${action['target_value']:,.0f})")
        else:
            print(f"{action['action']}: {action['reason']}")

if __name__ == "__main__":
    asyncio.run(main())