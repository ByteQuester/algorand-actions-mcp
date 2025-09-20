"""
DeFi Systemic Risk Analysis
Models cross-protocol contagion and cascade effects across the Algorand DeFi ecosystem
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
import networkx as nx
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemicRiskNode:
    """Individual protocol node in systemic risk network"""
    protocol_name: str
    category: str
    tvl_usd: float
    systemic_importance: float
    interconnectedness: float
    failure_probability: float
    cascade_vulnerability: float
    recovery_time_days: float

@dataclass
class ContagionPath:
    """Contagion propagation path between protocols"""
    source_protocol: str
    target_protocol: str
    contagion_strength: float
    propagation_delay_hours: float
    attenuation_factor: float
    transmission_mechanism: str

@dataclass
class CascadeScenario:
    """Cascade failure scenario analysis"""
    trigger_protocol: str
    affected_protocols: List[str]
    total_tvl_impact: float
    cascade_probability: float
    propagation_time_hours: float
    recovery_time_days: float
    economic_impact_usd: float
    user_impact_count: int

@dataclass
class SystemicRiskAssessment:
    """Complete systemic risk assessment"""
    network_nodes: List[SystemicRiskNode]
    contagion_paths: List[ContagionPath]
    cascade_scenarios: List[CascadeScenario]
    network_stability_score: float
    systemic_risk_score: float
    interconnectedness_index: float
    concentration_vulnerability: float
    liquidity_risk_propagation: float
    overall_ecosystem_health: float
    risk_level: str
    early_warning_indicators: List[str]
    mitigation_recommendations: List[str]
    timestamp: datetime

class SystemicRiskAnalyzer:
    """Analyzes systemic risk and cascade effects in DeFi protocols"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the systemic risk analyzer"""
        self.config = self._load_config(config_path)
        self.risk_network = None

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    async def analyze_systemic_risk(self, protocol_data: Dict[str, Dict]) -> SystemicRiskAssessment:
        """Analyze comprehensive systemic risk across DeFi protocols"""
        logger.info("Analyzing DeFi systemic risk and cascade effects...")

        if not protocol_data:
            raise ValueError("No protocol data provided for systemic risk analysis")

        # Build risk network
        network_nodes = await self._build_risk_network_nodes(protocol_data)
        self.risk_network = await self._build_contagion_network(network_nodes)

        # Analyze contagion paths
        contagion_paths = await self._analyze_contagion_paths(network_nodes)

        # Model cascade scenarios
        cascade_scenarios = await self._model_cascade_scenarios(network_nodes, contagion_paths)

        # Calculate network stability metrics
        network_stability_score = await self._calculate_network_stability(network_nodes, contagion_paths)
        interconnectedness_index = self._calculate_interconnectedness_index(contagion_paths)
        concentration_vulnerability = self._calculate_concentration_vulnerability(network_nodes)

        # Calculate systemic risk scores
        systemic_risk_score = self._calculate_systemic_risk_score(
            network_stability_score, interconnectedness_index, concentration_vulnerability
        )

        # Analyze liquidity risk propagation
        liquidity_risk_propagation = await self._analyze_liquidity_risk_propagation(network_nodes, contagion_paths)

        # Calculate overall ecosystem health
        overall_ecosystem_health = self._calculate_ecosystem_health(
            network_stability_score, systemic_risk_score, liquidity_risk_propagation
        )

        # Determine risk level
        risk_level = self._determine_systemic_risk_level(systemic_risk_score, overall_ecosystem_health)

        # Generate early warning indicators
        early_warning_indicators = await self._generate_early_warning_indicators(network_nodes, cascade_scenarios)

        # Generate mitigation recommendations
        mitigation_recommendations = self._generate_mitigation_recommendations(
            network_nodes, cascade_scenarios, systemic_risk_score
        )

        return SystemicRiskAssessment(
            network_nodes=network_nodes,
            contagion_paths=contagion_paths,
            cascade_scenarios=cascade_scenarios,
            network_stability_score=network_stability_score,
            systemic_risk_score=systemic_risk_score,
            interconnectedness_index=interconnectedness_index,
            concentration_vulnerability=concentration_vulnerability,
            liquidity_risk_propagation=liquidity_risk_propagation,
            overall_ecosystem_health=overall_ecosystem_health,
            risk_level=risk_level,
            early_warning_indicators=early_warning_indicators,
            mitigation_recommendations=mitigation_recommendations,
            timestamp=datetime.now()
        )

    async def _build_risk_network_nodes(self, protocol_data: Dict[str, Dict]) -> List[SystemicRiskNode]:
        """Build network nodes representing each protocol's systemic risk profile"""
        nodes = []
        total_tvl = sum(data.get('tvl_usd', 0) for data in protocol_data.values())

        for protocol_name, data in protocol_data.items():
            protocol_config = self.config['algorand_protocols'].get(protocol_name, {})

            # Calculate systemic importance (based on TVL, users, interconnections)
            tvl_usd = data.get('tvl_usd', 0)
            systemic_importance = self._calculate_systemic_importance(protocol_name, data, total_tvl)

            # Calculate interconnectedness
            interconnectedness = self._calculate_protocol_interconnectedness(protocol_name, protocol_data)

            # Estimate failure probability
            failure_probability = self._estimate_failure_probability(protocol_config, data)

            # Calculate cascade vulnerability
            cascade_vulnerability = self._calculate_cascade_vulnerability(
                protocol_name, systemic_importance, interconnectedness
            )

            # Estimate recovery time
            recovery_time_days = self._estimate_recovery_time(protocol_config, data)

            node = SystemicRiskNode(
                protocol_name=protocol_name,
                category=protocol_config.get('category', 'unknown'),
                tvl_usd=tvl_usd,
                systemic_importance=systemic_importance,
                interconnectedness=interconnectedness,
                failure_probability=failure_probability,
                cascade_vulnerability=cascade_vulnerability,
                recovery_time_days=recovery_time_days
            )

            nodes.append(node)

        return nodes

    def _calculate_systemic_importance(self, protocol_name: str, data: Dict, total_tvl: float) -> float:
        """Calculate systemic importance score for a protocol"""
        tvl_usd = data.get('tvl_usd', 0)
        active_users = data.get('active_users', 0)

        # TVL-based importance (0-0.6)
        tvl_importance = min((tvl_usd / total_tvl) * 2, 0.6) if total_tvl > 0 else 0

        # User-based importance (0-0.2)
        max_users = 5000  # Assumed max users for normalization
        user_importance = min(active_users / max_users, 1.0) * 0.2

        # Protocol type importance (0-0.2)
        protocol_config = self.config['algorand_protocols'].get(protocol_name, {})
        category = protocol_config.get('category', 'unknown')
        category_importance = {
            'lending': 0.2,    # Lending protocols are critical
            'dex': 0.15,       # DEXs are important
            'staking': 0.1,    # Staking protocols less critical
            'bridge': 0.15,    # Bridges are important
            'unknown': 0.05
        }.get(category, 0.05)

        return min(tvl_importance + user_importance + category_importance, 1.0)

    def _calculate_protocol_interconnectedness(self, protocol_name: str, protocol_data: Dict[str, Dict]) -> float:
        """Calculate how interconnected a protocol is with others"""
        correlations = self.config.get('protocol_correlations', {})
        protocol_config = self.config['algorand_protocols'].get(protocol_name, {})

        interconnectedness_score = 0.0
        connection_count = 0

        # Check correlations with other protocols
        for other_protocol in protocol_data.keys():
            if other_protocol == protocol_name:
                continue

            # Get correlation
            corr_key = f"{protocol_name}_{other_protocol}"
            reverse_key = f"{other_protocol}_{protocol_name}"
            correlation = correlations.get(corr_key, correlations.get(reverse_key, 0.0))

            if correlation > 0.3:  # Significant correlation threshold
                interconnectedness_score += correlation
                connection_count += 1

        # Check category-based interconnectedness
        category = protocol_config.get('category', 'unknown')
        category_corr_key = f"{category}_protocols_correlation"
        category_correlation = correlations.get(category_corr_key, 0.0)

        # Normalize interconnectedness
        if connection_count > 0:
            avg_interconnectedness = interconnectedness_score / connection_count
        else:
            avg_interconnectedness = 0.0

        # Combine direct correlations and category correlations
        total_interconnectedness = (avg_interconnectedness * 0.7) + (category_correlation * 0.3)

        return min(total_interconnectedness, 1.0)

    def _estimate_failure_probability(self, protocol_config: Dict, data: Dict) -> float:
        """Estimate the probability of protocol failure"""
        base_failure_rate = 0.05  # 5% base annual failure rate

        # Adjust for risk tier
        risk_tier = protocol_config.get('risk_tier', 'tier_3')
        tier_multipliers = {
            'tier_1': 0.5,   # 50% of base rate
            'tier_2': 1.0,   # Base rate
            'tier_3': 2.0    # 200% of base rate
        }
        tier_multiplier = tier_multipliers.get(risk_tier, 2.0)

        # Adjust for audit status
        audit_status = protocol_config.get('audit_status', 'none')
        audit_multipliers = {
            'audited': 0.7,      # 30% reduction
            'partial': 1.2,      # 20% increase
            'outdated': 1.5,     # 50% increase
            'none': 2.0          # 100% increase
        }
        audit_multiplier = audit_multipliers.get(audit_status, 2.0)

        # Adjust for governance concentration
        governance_concentration = protocol_config.get('governance_concentration', 0.5)
        governance_multiplier = 1.0 + governance_concentration  # Higher concentration = higher risk

        # Adjust for TVL stability (mock metric)
        tvl_usd = data.get('tvl_usd', 0)
        tvl_stability_multiplier = 1.0
        if tvl_usd < 1000000:  # $1M threshold
            tvl_stability_multiplier = 1.5  # Small protocols are riskier

        failure_probability = base_failure_rate * tier_multiplier * audit_multiplier * governance_multiplier * tvl_stability_multiplier

        return min(failure_probability, 0.5)  # Cap at 50% annual failure rate

    def _calculate_cascade_vulnerability(self, protocol_name: str, systemic_importance: float, interconnectedness: float) -> float:
        """Calculate how vulnerable a protocol is to cascade effects from other failures"""
        # Base vulnerability from interconnectedness
        base_vulnerability = interconnectedness

        # Adjust for systemic importance (more important = more vulnerable to contagion)
        importance_multiplier = 1.0 + (systemic_importance * 0.5)

        # Adjust for protocol category
        protocol_config = self.config['algorand_protocols'].get(protocol_name, {})
        category = protocol_config.get('category', 'unknown')

        category_vulnerability = {
            'lending': 1.3,    # Lending protocols highly vulnerable to contagion
            'dex': 1.0,        # DEXs moderately vulnerable
            'staking': 0.8,    # Staking protocols less vulnerable
            'bridge': 1.2,     # Bridges moderately vulnerable
            'unknown': 1.0
        }.get(category, 1.0)

        cascade_vulnerability = base_vulnerability * importance_multiplier * category_vulnerability

        return min(cascade_vulnerability, 1.0)

    def _estimate_recovery_time(self, protocol_config: Dict, data: Dict) -> float:
        """Estimate recovery time in days for a protocol after failure"""
        base_recovery_days = 30  # 30 days base recovery time

        # Adjust for risk tier
        risk_tier = protocol_config.get('risk_tier', 'tier_3')
        tier_multipliers = {
            'tier_1': 0.5,   # Faster recovery for established protocols
            'tier_2': 1.0,   # Base recovery time
            'tier_3': 2.0    # Slower recovery for smaller protocols
        }
        tier_multiplier = tier_multipliers.get(risk_tier, 2.0)

        # Adjust for governance concentration
        governance_concentration = protocol_config.get('governance_concentration', 0.5)
        governance_multiplier = 1.0 + governance_concentration  # Higher concentration = slower recovery

        # Adjust for TVL size
        tvl_usd = data.get('tvl_usd', 0)
        if tvl_usd > 50000000:  # $50M+ protocols recover faster
            size_multiplier = 0.7
        elif tvl_usd > 10000000:  # $10M+ protocols
            size_multiplier = 1.0
        else:  # Smaller protocols recover slower
            size_multiplier = 1.5

        recovery_days = base_recovery_days * tier_multiplier * governance_multiplier * size_multiplier

        return min(recovery_days, 365)  # Cap at 1 year

    async def _build_contagion_network(self, nodes: List[SystemicRiskNode]) -> nx.DiGraph:
        """Build directed graph representing contagion relationships"""
        G = nx.DiGraph()

        # Add nodes
        for node in nodes:
            G.add_node(node.protocol_name, **{
                'systemic_importance': node.systemic_importance,
                'interconnectedness': node.interconnectedness,
                'failure_probability': node.failure_probability,
                'cascade_vulnerability': node.cascade_vulnerability,
                'tvl_usd': node.tvl_usd
            })

        # Add edges based on contagion relationships
        correlations = self.config.get('protocol_correlations', {})

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                # Get correlation between protocols
                corr_key = f"{node1.protocol_name}_{node2.protocol_name}"
                reverse_key = f"{node2.protocol_name}_{node1.protocol_name}"
                correlation = correlations.get(corr_key, correlations.get(reverse_key, 0.0))

                if correlation > 0.3:  # Significant correlation threshold
                    # Bidirectional contagion with weights based on systemic importance and correlation
                    weight1to2 = correlation * node1.systemic_importance
                    weight2to1 = correlation * node2.systemic_importance

                    G.add_edge(node1.protocol_name, node2.protocol_name, weight=weight1to2, correlation=correlation)
                    G.add_edge(node2.protocol_name, node1.protocol_name, weight=weight2to1, correlation=correlation)

        return G

    async def _analyze_contagion_paths(self, nodes: List[SystemicRiskNode]) -> List[ContagionPath]:
        """Analyze potential contagion paths between protocols"""
        contagion_paths = []
        correlations = self.config.get('protocol_correlations', {})

        for i, source_node in enumerate(nodes):
            for target_node in nodes[i+1:]:
                # Get correlation
                corr_key = f"{source_node.protocol_name}_{target_node.protocol_name}"
                reverse_key = f"{target_node.protocol_name}_{source_node.protocol_name}"
                correlation = correlations.get(corr_key, correlations.get(reverse_key, 0.0))

                if correlation > 0.3:  # Significant correlation threshold
                    # Calculate contagion strength
                    contagion_strength = self._calculate_contagion_strength(source_node, target_node, correlation)

                    # Estimate propagation delay
                    propagation_delay = self._estimate_propagation_delay(source_node, target_node)

                    # Calculate attenuation factor
                    attenuation_factor = self._calculate_attenuation_factor(source_node, target_node)

                    # Determine transmission mechanism
                    transmission_mechanism = self._determine_transmission_mechanism(source_node, target_node)

                    # Create bidirectional paths
                    path1 = ContagionPath(
                        source_protocol=source_node.protocol_name,
                        target_protocol=target_node.protocol_name,
                        contagion_strength=contagion_strength,
                        propagation_delay_hours=propagation_delay,
                        attenuation_factor=attenuation_factor,
                        transmission_mechanism=transmission_mechanism
                    )

                    path2 = ContagionPath(
                        source_protocol=target_node.protocol_name,
                        target_protocol=source_node.protocol_name,
                        contagion_strength=contagion_strength * 0.8,  # Slightly asymmetric
                        propagation_delay_hours=propagation_delay,
                        attenuation_factor=attenuation_factor,
                        transmission_mechanism=transmission_mechanism
                    )

                    contagion_paths.extend([path1, path2])

        return contagion_paths

    def _calculate_contagion_strength(self, source_node: SystemicRiskNode, target_node: SystemicRiskNode, correlation: float) -> float:
        """Calculate the strength of contagion between two protocols"""
        # Base strength from correlation
        base_strength = correlation

        # Adjust for source systemic importance (larger failures spread more)
        source_multiplier = 1.0 + source_node.systemic_importance

        # Adjust for target vulnerability
        target_multiplier = 1.0 + target_node.cascade_vulnerability

        # Category-based adjustment
        source_config = self.config['algorand_protocols'].get(source_node.protocol_name, {})
        target_config = self.config['algorand_protocols'].get(target_node.protocol_name, {})

        source_category = source_config.get('category', 'unknown')
        target_category = target_config.get('category', 'unknown')

        # Same category = stronger contagion
        category_multiplier = 1.3 if source_category == target_category else 1.0

        contagion_strength = base_strength * source_multiplier * target_multiplier * category_multiplier * 0.3

        return min(contagion_strength, 1.0)

    def _estimate_propagation_delay(self, source_node: SystemicRiskNode, target_node: SystemicRiskNode) -> float:
        """Estimate delay in hours for contagion to propagate"""
        base_delay = 6.0  # 6 hours base delay

        # Faster propagation for same category
        source_config = self.config['algorand_protocols'].get(source_node.protocol_name, {})
        target_config = self.config['algorand_protocols'].get(target_node.protocol_name, {})

        source_category = source_config.get('category', 'unknown')
        target_category = target_config.get('category', 'unknown')

        if source_category == target_category:
            category_multiplier = 0.5  # 50% faster
        else:
            category_multiplier = 1.0

        # Adjust for interconnectedness
        interconnectedness_multiplier = 2.0 - max(source_node.interconnectedness, target_node.interconnectedness)

        propagation_delay = base_delay * category_multiplier * interconnectedness_multiplier

        return max(propagation_delay, 1.0)  # Minimum 1 hour delay

    def _calculate_attenuation_factor(self, source_node: SystemicRiskNode, target_node: SystemicRiskNode) -> float:
        """Calculate how much the contagion effect attenuates during transmission"""
        base_attenuation = 0.7  # 30% attenuation by default

        # Less attenuation for same category protocols
        source_config = self.config['algorand_protocols'].get(source_node.protocol_name, {})
        target_config = self.config['algorand_protocols'].get(target_node.protocol_name, {})

        source_category = source_config.get('category', 'unknown')
        target_category = target_config.get('category', 'unknown')

        if source_category == target_category:
            category_factor = 0.9  # Less attenuation
        else:
            category_factor = 0.6  # More attenuation

        # Adjust for target resilience (higher tier = more resilient)
        target_tier = target_config.get('risk_tier', 'tier_3')
        tier_resilience = {
            'tier_1': 0.5,   # High resilience
            'tier_2': 0.7,   # Medium resilience
            'tier_3': 0.9    # Low resilience
        }.get(target_tier, 0.9)

        attenuation_factor = base_attenuation * category_factor * tier_resilience

        return max(attenuation_factor, 0.1)  # Minimum 10% transmission

    def _determine_transmission_mechanism(self, source_node: SystemicRiskNode, target_node: SystemicRiskNode) -> str:
        """Determine the primary mechanism of contagion transmission"""
        source_config = self.config['algorand_protocols'].get(source_node.protocol_name, {})
        target_config = self.config['algorand_protocols'].get(target_node.protocol_name, {})

        source_category = source_config.get('category', 'unknown')
        target_category = target_config.get('category', 'unknown')

        if source_category == target_category:
            if source_category == 'lending':
                return 'credit_contagion'
            elif source_category == 'dex':
                return 'liquidity_contagion'
            elif source_category == 'staking':
                return 'validator_contagion'
            else:
                return 'category_correlation'
        else:
            return 'market_sentiment'

    async def _model_cascade_scenarios(self, nodes: List[SystemicRiskNode],
                                     contagion_paths: List[ContagionPath]) -> List[CascadeScenario]:
        """Model various cascade failure scenarios"""
        scenarios = []

        # Scenario 1: Failure of each major protocol
        major_protocols = [node for node in nodes if node.systemic_importance > 0.2]

        for trigger_node in major_protocols:
            scenario = await self._simulate_cascade_from_trigger(trigger_node, nodes, contagion_paths)
            scenarios.append(scenario)

        # Scenario 2: Simultaneous failure of top 2 protocols
        if len(major_protocols) >= 2:
            top_2_protocols = sorted(major_protocols, key=lambda x: x.systemic_importance, reverse=True)[:2]
            scenario = await self._simulate_multi_protocol_cascade(top_2_protocols, nodes, contagion_paths)
            scenarios.append(scenario)

        # Scenario 3: Category-wide failure (e.g., all lending protocols)
        categories = set(node.category for node in nodes)
        for category in categories:
            category_nodes = [node for node in nodes if node.category == category]
            if len(category_nodes) > 1:
                scenario = await self._simulate_category_cascade(category, category_nodes, nodes, contagion_paths)
                scenarios.append(scenario)

        return scenarios

    async def _simulate_cascade_from_trigger(self, trigger_node: SystemicRiskNode,
                                           all_nodes: List[SystemicRiskNode],
                                           contagion_paths: List[ContagionPath]) -> CascadeScenario:
        """Simulate cascade effects from a single protocol failure"""
        affected_protocols = [trigger_node.protocol_name]
        total_tvl_impact = trigger_node.tvl_usd
        propagation_time = 0.0

        # Find direct contagion paths from trigger
        outgoing_paths = [path for path in contagion_paths if path.source_protocol == trigger_node.protocol_name]

        # Simulate propagation
        for path in outgoing_paths:
            if path.contagion_strength > 0.3:  # Threshold for significant contagion
                target_node = next((node for node in all_nodes if node.protocol_name == path.target_protocol), None)
                if target_node and target_node.protocol_name not in affected_protocols:
                    # Calculate probability of contagion
                    contagion_probability = path.contagion_strength * (1 - path.attenuation_factor)

                    if contagion_probability > 0.2:  # 20% threshold
                        affected_protocols.append(target_node.protocol_name)
                        total_tvl_impact += target_node.tvl_usd * path.attenuation_factor
                        propagation_time = max(propagation_time, path.propagation_delay_hours)

        # Calculate cascade probability
        cascade_probability = min(trigger_node.failure_probability * 2, 0.8)  # Up to 80%

        # Estimate recovery time
        recovery_time_days = max(trigger_node.recovery_time_days,
                               max([next((node.recovery_time_days for node in all_nodes
                                        if node.protocol_name == protocol), 0)
                                   for protocol in affected_protocols]))

        # Estimate economic impact and user impact
        economic_impact = total_tvl_impact * 0.3  # Assume 30% of TVL as direct economic impact
        user_impact = sum(next((node.tvl_usd for node in all_nodes if node.protocol_name == protocol), 0)
                         for protocol in affected_protocols) / 1000  # Rough estimate: $1k per user

        return CascadeScenario(
            trigger_protocol=trigger_node.protocol_name,
            affected_protocols=affected_protocols,
            total_tvl_impact=total_tvl_impact,
            cascade_probability=cascade_probability,
            propagation_time_hours=propagation_time,
            recovery_time_days=recovery_time_days,
            economic_impact_usd=economic_impact,
            user_impact_count=int(user_impact)
        )

    async def _simulate_multi_protocol_cascade(self, trigger_nodes: List[SystemicRiskNode],
                                             all_nodes: List[SystemicRiskNode],
                                             contagion_paths: List[ContagionPath]) -> CascadeScenario:
        """Simulate cascade from multiple simultaneous failures"""
        affected_protocols = [node.protocol_name for node in trigger_nodes]
        total_tvl_impact = sum(node.tvl_usd for node in trigger_nodes)
        max_propagation_time = 0.0

        # Find all outgoing paths from trigger protocols
        for trigger_node in trigger_nodes:
            outgoing_paths = [path for path in contagion_paths if path.source_protocol == trigger_node.protocol_name]

            for path in outgoing_paths:
                if path.contagion_strength > 0.2:  # Lower threshold for multi-failure
                    target_node = next((node for node in all_nodes if node.protocol_name == path.target_protocol), None)
                    if target_node and target_node.protocol_name not in affected_protocols:
                        # Enhanced contagion probability due to multiple failures
                        enhanced_probability = path.contagion_strength * (1 - path.attenuation_factor) * 1.5

                        if enhanced_probability > 0.15:  # 15% threshold
                            affected_protocols.append(target_node.protocol_name)
                            total_tvl_impact += target_node.tvl_usd * (1 - path.attenuation_factor)
                            max_propagation_time = max(max_propagation_time, path.propagation_delay_hours)

        # Higher cascade probability for multi-failure
        cascade_probability = min(sum(node.failure_probability for node in trigger_nodes) * 1.5, 0.9)

        recovery_time_days = max(node.recovery_time_days for node in trigger_nodes) * 1.5

        economic_impact = total_tvl_impact * 0.4  # Higher impact for systemic event
        user_impact = total_tvl_impact / 800  # More conservative estimate for crisis

        return CascadeScenario(
            trigger_protocol=f"Multi-failure: {', '.join([node.protocol_name for node in trigger_nodes])}",
            affected_protocols=affected_protocols,
            total_tvl_impact=total_tvl_impact,
            cascade_probability=cascade_probability,
            propagation_time_hours=max_propagation_time,
            recovery_time_days=recovery_time_days,
            economic_impact_usd=economic_impact,
            user_impact_count=int(user_impact)
        )

    async def _simulate_category_cascade(self, category: str, category_nodes: List[SystemicRiskNode],
                                       all_nodes: List[SystemicRiskNode],
                                       contagion_paths: List[ContagionPath]) -> CascadeScenario:
        """Simulate cascade from category-wide failure"""
        affected_protocols = [node.protocol_name for node in category_nodes]
        total_tvl_impact = sum(node.tvl_usd for node in category_nodes)

        # Category failures have high internal correlation
        cascade_probability = 0.7  # 70% probability for category-wide failure

        # Find cross-category contagion
        max_propagation_time = 0.0
        for category_node in category_nodes:
            outgoing_paths = [path for path in contagion_paths
                            if path.source_protocol == category_node.protocol_name]

            for path in outgoing_paths:
                target_node = next((node for node in all_nodes if node.protocol_name == path.target_protocol), None)
                if (target_node and target_node.category != category and
                    target_node.protocol_name not in affected_protocols):

                    # Cross-category contagion probability
                    cross_category_probability = path.contagion_strength * 0.6  # Reduced for cross-category

                    if cross_category_probability > 0.25:
                        affected_protocols.append(target_node.protocol_name)
                        total_tvl_impact += target_node.tvl_usd * 0.7  # 70% impact
                        max_propagation_time = max(max_propagation_time, path.propagation_delay_hours)

        recovery_time_days = max(node.recovery_time_days for node in category_nodes) * 2  # Category failure takes longer

        economic_impact = total_tvl_impact * 0.5  # High impact for category failure
        user_impact = total_tvl_impact / 500  # High user impact

        return CascadeScenario(
            trigger_protocol=f"Category failure: {category}",
            affected_protocols=affected_protocols,
            total_tvl_impact=total_tvl_impact,
            cascade_probability=cascade_probability,
            propagation_time_hours=max_propagation_time,
            recovery_time_days=recovery_time_days,
            economic_impact_usd=economic_impact,
            user_impact_count=int(user_impact)
        )

    async def _calculate_network_stability(self, nodes: List[SystemicRiskNode],
                                         contagion_paths: List[ContagionPath]) -> float:
        """Calculate overall network stability score"""
        if not nodes or not self.risk_network:
            return 0.0

        # Calculate network density
        num_nodes = len(nodes)
        num_edges = len(contagion_paths)
        max_edges = num_nodes * (num_nodes - 1)
        network_density = num_edges / max_edges if max_edges > 0 else 0

        # Calculate average systemic importance
        avg_systemic_importance = np.mean([node.systemic_importance for node in nodes])

        # Calculate failure probability distribution
        failure_probabilities = [node.failure_probability for node in nodes]
        failure_variance = np.var(failure_probabilities)

        # Stability decreases with density, high importance, and high failure variance
        density_factor = 1.0 - min(network_density * 2, 0.8)  # High density = lower stability
        importance_factor = 1.0 - min(avg_systemic_importance * 1.5, 0.7)  # High importance = lower stability
        variance_factor = 1.0 - min(failure_variance * 10, 0.5)  # High variance = lower stability

        network_stability = (density_factor + importance_factor + variance_factor) / 3

        return max(network_stability, 0.1)  # Minimum 10% stability

    def _calculate_interconnectedness_index(self, contagion_paths: List[ContagionPath]) -> float:
        """Calculate network interconnectedness index"""
        if not contagion_paths:
            return 0.0

        # Calculate average contagion strength
        avg_contagion_strength = np.mean([path.contagion_strength for path in contagion_paths])

        # Calculate network clustering
        path_count = len(contagion_paths)
        protocol_set = set()
        for path in contagion_paths:
            protocol_set.add(path.source_protocol)
            protocol_set.add(path.target_protocol)

        protocol_count = len(protocol_set)
        clustering_coefficient = path_count / (protocol_count ** 2) if protocol_count > 0 else 0

        # Combine metrics
        interconnectedness_index = (avg_contagion_strength * 0.6) + (clustering_coefficient * 0.4)

        return min(interconnectedness_index, 1.0)

    def _calculate_concentration_vulnerability(self, nodes: List[SystemicRiskNode]) -> float:
        """Calculate vulnerability from protocol concentration"""
        if not nodes:
            return 0.0

        # Calculate Herfindahl index for systemic importance
        importance_values = [node.systemic_importance for node in nodes]
        total_importance = sum(importance_values)

        if total_importance == 0:
            return 0.0

        hhi = sum((importance / total_importance) ** 2 for importance in importance_values)

        # Higher HHI = higher concentration = higher vulnerability
        concentration_vulnerability = min(hhi * 2, 1.0)

        return concentration_vulnerability

    def _calculate_systemic_risk_score(self, network_stability: float, interconnectedness: float,
                                     concentration_vulnerability: float) -> float:
        """Calculate overall systemic risk score"""
        # Systemic risk increases with interconnectedness and concentration, decreases with stability
        stability_factor = 1.0 - network_stability
        interconnectedness_factor = interconnectedness
        concentration_factor = concentration_vulnerability

        systemic_risk = (stability_factor * 0.4) + (interconnectedness_factor * 0.35) + (concentration_factor * 0.25)

        return min(systemic_risk, 1.0)

    async def _analyze_liquidity_risk_propagation(self, nodes: List[SystemicRiskNode],
                                                contagion_paths: List[ContagionPath]) -> float:
        """Analyze how liquidity risk propagates through the network"""
        # Mock liquidity risk analysis - in production, this would use real liquidity data
        total_liquidity_risk = 0.0

        for node in nodes:
            # Estimate liquidity risk based on TVL and category
            if node.category == 'lending':
                liquidity_risk = 0.3  # Lending protocols have inherent liquidity risk
            elif node.category == 'dex':
                liquidity_risk = 0.2  # DEXs have moderate liquidity risk
            else:
                liquidity_risk = 0.1  # Other protocols have lower liquidity risk

            # Weight by systemic importance
            weighted_risk = liquidity_risk * node.systemic_importance
            total_liquidity_risk += weighted_risk

        # Normalize and adjust for network effects
        avg_liquidity_risk = total_liquidity_risk / len(nodes) if nodes else 0
        network_amplification = 1.0 + (self._calculate_interconnectedness_index(contagion_paths) * 0.5)

        propagation_risk = avg_liquidity_risk * network_amplification

        return min(propagation_risk, 1.0)

    def _calculate_ecosystem_health(self, network_stability: float, systemic_risk: float,
                                  liquidity_risk_propagation: float) -> float:
        """Calculate overall ecosystem health score"""
        # Health increases with stability, decreases with systemic and liquidity risks
        health_score = (
            network_stability * 0.4 -
            systemic_risk * 0.35 -
            liquidity_risk_propagation * 0.25
        )

        return max(health_score, 0.0)  # Minimum 0% health

    def _determine_systemic_risk_level(self, systemic_risk_score: float, ecosystem_health: float) -> str:
        """Determine overall systemic risk level"""
        combined_score = (systemic_risk_score * 0.7) + ((1.0 - ecosystem_health) * 0.3)

        if combined_score >= 0.8:
            return "CRITICAL"
        elif combined_score >= 0.6:
            return "HIGH"
        elif combined_score >= 0.4:
            return "MODERATE"
        elif combined_score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"

    async def _generate_early_warning_indicators(self, nodes: List[SystemicRiskNode],
                                               scenarios: List[CascadeScenario]) -> List[str]:
        """Generate early warning indicators for systemic risk"""
        indicators = []

        # High failure probability protocols
        high_risk_protocols = [node for node in nodes if node.failure_probability > 0.2]
        if high_risk_protocols:
            protocol_names = [node.protocol_name for node in high_risk_protocols]
            indicators.append(f"High failure probability protocols detected: {', '.join(protocol_names)}")

        # High systemic importance concentration
        top_3_importance = sorted(nodes, key=lambda x: x.systemic_importance, reverse=True)[:3]
        total_top_3_importance = sum(node.systemic_importance for node in top_3_importance)
        if total_top_3_importance > 0.7:
            indicators.append(f"High systemic importance concentration: top 3 protocols represent {total_top_3_importance:.1%}")

        # High cascade probability scenarios
        high_cascade_scenarios = [s for s in scenarios if s.cascade_probability > 0.6]
        if high_cascade_scenarios:
            indicators.append(f"High cascade risk scenarios: {len(high_cascade_scenarios)} scenarios with >60% probability")

        # Cross-category vulnerabilities
        categories = set(node.category for node in nodes)
        if len(categories) < 3:
            indicators.append(f"Limited category diversification: only {len(categories)} categories represented")

        return indicators

    def _generate_mitigation_recommendations(self, nodes: List[SystemicRiskNode],
                                           scenarios: List[CascadeScenario],
                                           systemic_risk_score: float) -> List[str]:
        """Generate systemic risk mitigation recommendations"""
        recommendations = []

        if systemic_risk_score > 0.6:
            recommendations.append("URGENT: Implement circuit breakers to halt contagion during crisis events")
            recommendations.append("URGENT: Establish emergency liquidity facilities for critical protocols")

        # Protocol-specific recommendations
        high_importance_protocols = [node for node in nodes if node.systemic_importance > 0.3]
        for node in high_importance_protocols:
            if node.failure_probability > 0.15:
                recommendations.append(f"Monitor {node.protocol_name} closely - high systemic importance with elevated failure risk")

        # Network structure recommendations
        if self._calculate_interconnectedness_index([]) > 0.7:  # This would use actual paths
            recommendations.append("Reduce protocol interconnectedness through diversified integration patterns")

        # Category concentration recommendations
        category_counts = {}
        for node in nodes:
            category_counts[node.category] = category_counts.get(node.category, 0) + 1

        dominant_category = max(category_counts.items(), key=lambda x: x[1])
        if dominant_category[1] > len(nodes) * 0.6:
            recommendations.append(f"Reduce {dominant_category[0]} protocol concentration in ecosystem")

        # Cascade-specific recommendations
        worst_cascade = max(scenarios, key=lambda x: x.cascade_probability) if scenarios else None
        if worst_cascade and worst_cascade.cascade_probability > 0.7:
            recommendations.append(f"Implement specific safeguards for {worst_cascade.trigger_protocol} failure scenario")

        return recommendations[:5]  # Limit to top 5 recommendations

# Example usage
async def main():
    """Example usage of the systemic risk analyzer"""
    analyzer = SystemicRiskAnalyzer()

    # Example protocol data
    protocol_data = {
        'algofi': {
            'tvl_usd': 45000000,
            'active_users': 2500,
            'total_borrowed': 25000000
        },
        'folks_finance': {
            'tvl_usd': 32000000,
            'active_users': 1800,
            'total_borrowed': 18000000
        },
        'tinyman': {
            'tvl_usd': 25000000,
            'active_users': 3000,
            'total_volume_24h': 2000000
        },
        'pact': {
            'tvl_usd': 12000000,
            'active_users': 1200,
            'total_volume_24h': 800000
        }
    }

    # Analyze systemic risk
    systemic_assessment = await analyzer.analyze_systemic_risk(protocol_data)

    print(f"\n=== Systemic Risk Analysis ===")
    print(f"Systemic Risk Score: {systemic_assessment.systemic_risk_score:.2f}")
    print(f"Risk Level: {systemic_assessment.risk_level}")
    print(f"Network Stability: {systemic_assessment.network_stability_score:.2f}")
    print(f"Interconnectedness Index: {systemic_assessment.interconnectedness_index:.2f}")
    print(f"Ecosystem Health: {systemic_assessment.overall_ecosystem_health:.2f}")

    print(f"\n=== Network Nodes ===")
    for node in systemic_assessment.network_nodes:
        print(f"{node.protocol_name}:")
        print(f"  Systemic Importance: {node.systemic_importance:.2f}")
        print(f"  Failure Probability: {node.failure_probability:.2f}")
        print(f"  Cascade Vulnerability: {node.cascade_vulnerability:.2f}")

    print(f"\n=== Cascade Scenarios ===")
    for scenario in systemic_assessment.cascade_scenarios:
        print(f"Trigger: {scenario.trigger_protocol}")
        print(f"  Affected Protocols: {len(scenario.affected_protocols)}")
        print(f"  Cascade Probability: {scenario.cascade_probability:.2f}")
        print(f"  TVL Impact: ${scenario.total_tvl_impact:,.0f}")
        print(f"  Economic Impact: ${scenario.economic_impact_usd:,.0f}")

    print(f"\n=== Early Warning Indicators ===")
    for indicator in systemic_assessment.early_warning_indicators:
        print(f"⚠️  {indicator}")

    print(f"\n=== Mitigation Recommendations ===")
    for i, rec in enumerate(systemic_assessment.mitigation_recommendations, 1):
        print(f"{i}. {rec}")

if __name__ == "__main__":
    asyncio.run(main())