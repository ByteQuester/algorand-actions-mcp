"""
Contagion Detector - Advanced cross-protocol contagion and spillover effects analysis

This module provides sophisticated detection and analysis of contagion effects across
DeFi protocols in the Algorand ecosystem, modeling how risks spread between interconnected systems.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path
import networkx as nx
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContagionType(Enum):
    """Types of contagion mechanisms"""
    LIQUIDITY = "liquidity"          # Liquidity-based contagion
    CORRELATION = "correlation"      # Correlation-based spillover
    DIRECT = "direct"               # Direct protocol dependencies
    CONFIDENCE = "confidence"        # Confidence/sentiment contagion
    FUNDING = "funding"             # Funding/credit contagion
    OPERATIONAL = "operational"      # Operational dependencies

class ContagionSeverity(Enum):
    """Severity levels of contagion events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    SYSTEMIC = "systemic"

class ProtocolStatus(Enum):
    """Status of protocols during contagion analysis"""
    HEALTHY = "healthy"
    STRESSED = "stressed"
    DISTRESSED = "distressed"
    FAILED = "failed"
    RECOVERED = "recovered"

@dataclass
class ProtocolNode:
    """Node representing a protocol in the contagion network"""
    protocol_id: str
    protocol_type: str  # lending, dex, stablecoin, bridge, etc.
    tvl: float
    status: ProtocolStatus
    health_score: float  # 0-1, 1 = healthiest
    interconnectedness: float  # 0-1, measure of connections
    systemic_importance: float  # 0-1, importance to ecosystem
    risk_factors: Dict[str, float]

@dataclass
class ContagionEdge:
    """Edge representing contagion pathway between protocols"""
    source_protocol: str
    target_protocol: str
    contagion_type: ContagionType
    strength: float  # 0-1, strength of contagion pathway
    transmission_delay: float  # hours
    bidirectional: bool
    historical_events: List[Dict[str, Any]]

@dataclass
class ContagionEvent:
    """Specific contagion event detection"""
    event_id: str
    timestamp: datetime
    source_protocol: str
    affected_protocols: List[str]
    contagion_type: ContagionType
    severity: ContagionSeverity
    trigger_factors: List[str]
    transmission_path: List[str]
    impact_metrics: Dict[str, float]
    recovery_time_estimate: float

@dataclass
class ContagionSimulation:
    """Result of contagion simulation"""
    simulation_id: str
    initial_shock: Dict[str, float]  # Protocol -> shock magnitude
    propagation_timeline: List[Dict[str, Any]]
    final_impacts: Dict[str, float]  # Protocol -> final impact
    total_system_impact: float
    affected_protocols: List[str]
    cascade_depth: int
    recovery_scenarios: Dict[str, Dict[str, Any]]

class ContagionDetector:
    """
    Advanced contagion detection and analysis system for the Algorand DeFi ecosystem.
    Models interconnections between protocols and simulates contagion propagation.
    """

    def __init__(self, config_path: str = None):
        """Initialize the contagion detector"""
        self.config = self._load_config(config_path)
        self.contagion_config = self.config['contagion']

        # Network components
        self.protocol_network = nx.DiGraph()
        self.protocol_nodes: Dict[str, ProtocolNode] = {}
        self.contagion_edges: Dict[Tuple[str, str], ContagionEdge] = {}

        # Historical data
        self.contagion_events: List[ContagionEvent] = []
        self.simulation_results: List[ContagionSimulation] = []

        # Detection parameters
        self.detection_params = self.contagion_config['detection']
        self.propagation_params = self.contagion_config['propagation']
        self.network_params = self.contagion_config['network']

        # Initialize network
        self._initialize_protocol_network()
        self._initialize_contagion_pathways()

        logger.info("Contagion Detector initialized")

    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _initialize_protocol_network(self):
        """Initialize the network of DeFi protocols"""
        protocols = {
            'algofi': ProtocolNode(
                protocol_id='algofi',
                protocol_type='lending',
                tvl=50_000_000,
                status=ProtocolStatus.HEALTHY,
                health_score=0.85,
                interconnectedness=0.8,
                systemic_importance=0.9,
                risk_factors={'liquidity_risk': 0.3, 'credit_risk': 0.4, 'smart_contract_risk': 0.2}
            ),
            'folks_finance': ProtocolNode(
                protocol_id='folks_finance',
                protocol_type='lending',
                tvl=30_000_000,
                status=ProtocolStatus.HEALTHY,
                health_score=0.8,
                interconnectedness=0.7,
                systemic_importance=0.7,
                risk_factors={'liquidity_risk': 0.25, 'credit_risk': 0.35, 'smart_contract_risk': 0.25}
            ),
            'tinyman': ProtocolNode(
                protocol_id='tinyman',
                protocol_type='dex',
                tvl=25_000_000,
                status=ProtocolStatus.HEALTHY,
                health_score=0.9,
                interconnectedness=0.95,
                systemic_importance=0.85,
                risk_factors={'liquidity_risk': 0.4, 'impermanent_loss_risk': 0.3, 'smart_contract_risk': 0.1}
            ),
            'pact': ProtocolNode(
                protocol_id='pact',
                protocol_type='dex',
                tvl=15_000_000,
                status=ProtocolStatus.HEALTHY,
                health_score=0.85,
                interconnectedness=0.8,
                systemic_importance=0.6,
                risk_factors={'liquidity_risk': 0.35, 'impermanent_loss_risk': 0.35, 'smart_contract_risk': 0.15}
            ),
            'gard': ProtocolNode(
                protocol_id='gard',
                protocol_type='stablecoin',
                tvl=10_000_000,
                status=ProtocolStatus.HEALTHY,
                health_score=0.75,
                interconnectedness=0.6,
                systemic_importance=0.8,
                risk_factors={'peg_risk': 0.4, 'collateral_risk': 0.3, 'governance_risk': 0.2}
            ),
            'algodex': ProtocolNode(
                protocol_id='algodex',
                protocol_type='dex',
                tvl=8_000_000,
                status=ProtocolStatus.HEALTHY,
                health_score=0.8,
                interconnectedness=0.5,
                systemic_importance=0.4,
                risk_factors={'liquidity_risk': 0.4, 'orderbook_risk': 0.25, 'smart_contract_risk': 0.2}
            )
        }

        # Add nodes to network
        for protocol_id, node in protocols.items():
            self.protocol_nodes[protocol_id] = node
            self.protocol_network.add_node(
                protocol_id,
                **node.__dict__
            )

    def _initialize_contagion_pathways(self):
        """Initialize contagion pathways between protocols"""

        # Define contagion relationships
        contagion_relationships = [
            # Lending protocols interconnection (shared users, liquidations)
            ('algofi', 'folks_finance', ContagionType.LIQUIDITY, 0.6, 2.0),
            ('folks_finance', 'algofi', ContagionType.LIQUIDITY, 0.5, 2.5),

            # Lending to DEX (liquidation execution)
            ('algofi', 'tinyman', ContagionType.LIQUIDITY, 0.8, 0.5),
            ('algofi', 'pact', ContagionType.LIQUIDITY, 0.6, 1.0),
            ('folks_finance', 'tinyman', ContagionType.LIQUIDITY, 0.7, 0.5),
            ('folks_finance', 'pact', ContagionType.LIQUIDITY, 0.5, 1.0),

            # DEX interconnections (arbitrage, shared liquidity)
            ('tinyman', 'pact', ContagionType.CORRELATION, 0.9, 0.25),
            ('pact', 'tinyman', ContagionType.CORRELATION, 0.85, 0.3),
            ('tinyman', 'algodex', ContagionType.CORRELATION, 0.6, 1.0),
            ('pact', 'algodex', ContagionType.CORRELATION, 0.5, 1.5),

            # Stablecoin dependencies
            ('gard', 'algofi', ContagionType.DIRECT, 0.7, 1.0),  # Collateral backing
            ('gard', 'tinyman', ContagionType.LIQUIDITY, 0.8, 0.5),  # Primary trading venue
            ('gard', 'pact', ContagionType.LIQUIDITY, 0.6, 1.0),

            # Confidence/sentiment contagion (affects all)
            ('algofi', 'gard', ContagionType.CONFIDENCE, 0.5, 4.0),
            ('tinyman', 'algofi', ContagionType.CONFIDENCE, 0.4, 6.0),
            ('tinyman', 'folks_finance', ContagionType.CONFIDENCE, 0.3, 8.0),
        ]

        # Create contagion edges
        for source, target, contagion_type, strength, delay in contagion_relationships:
            edge = ContagionEdge(
                source_protocol=source,
                target_protocol=target,
                contagion_type=contagion_type,
                strength=strength,
                transmission_delay=delay,
                bidirectional=False,
                historical_events=[]
            )

            self.contagion_edges[(source, target)] = edge

            # Add edge to network graph
            self.protocol_network.add_edge(
                source, target,
                contagion_type=contagion_type.value,
                strength=strength,
                delay=delay
            )

    async def detect_contagion_risk(
        self,
        trigger_events: List[Dict[str, Any]],
        time_horizon_hours: int = 48
    ) -> List[ContagionEvent]:
        """
        Detect potential contagion events from trigger events

        Args:
            trigger_events: List of initial trigger events
            time_horizon_hours: Time horizon for contagion detection

        Returns:
            List of detected contagion events
        """
        logger.info(f"Detecting contagion risk from {len(trigger_events)} trigger events")

        detected_events = []

        for trigger in trigger_events:
            source_protocol = trigger['protocol']
            shock_magnitude = trigger.get('magnitude', 0.1)
            trigger_type = trigger.get('type', 'unknown')

            # Analyze contagion pathways from source
            contagion_paths = self._analyze_contagion_pathways(
                source_protocol, shock_magnitude
            )

            if contagion_paths:
                # Create contagion event
                event = ContagionEvent(
                    event_id=f"contagion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source_protocol}",
                    timestamp=datetime.now(),
                    source_protocol=source_protocol,
                    affected_protocols=[path['target'] for path in contagion_paths],
                    contagion_type=self._determine_primary_contagion_type(contagion_paths),
                    severity=self._assess_contagion_severity(contagion_paths, shock_magnitude),
                    trigger_factors=[trigger_type],
                    transmission_path=self._construct_transmission_path(contagion_paths),
                    impact_metrics=self._calculate_impact_metrics(contagion_paths),
                    recovery_time_estimate=self._estimate_recovery_time(contagion_paths)
                )

                detected_events.append(event)
                self.contagion_events.append(event)

        return detected_events

    def _analyze_contagion_pathways(
        self,
        source_protocol: str,
        shock_magnitude: float
    ) -> List[Dict[str, Any]]:
        """Analyze potential contagion pathways from source protocol"""

        pathways = []

        # Get direct connections
        for (source, target), edge in self.contagion_edges.items():
            if source == source_protocol:
                # Calculate transmission probability
                transmission_prob = self._calculate_transmission_probability(
                    edge, shock_magnitude
                )

                if transmission_prob > self.detection_params['correlation_spike_threshold']:
                    # Calculate expected impact
                    expected_impact = self._calculate_expected_impact(
                        edge, shock_magnitude, transmission_prob
                    )

                    pathway = {
                        'source': source,
                        'target': target,
                        'contagion_type': edge.contagion_type,
                        'transmission_probability': transmission_prob,
                        'expected_impact': expected_impact,
                        'transmission_delay': edge.transmission_delay,
                        'pathway_strength': edge.strength
                    }

                    pathways.append(pathway)

        # Sort by transmission probability
        pathways.sort(key=lambda x: x['transmission_probability'], reverse=True)

        return pathways

    def _calculate_transmission_probability(
        self,
        edge: ContagionEdge,
        shock_magnitude: float
    ) -> float:
        """Calculate probability of contagion transmission"""

        # Base probability from edge strength
        base_prob = edge.strength

        # Shock magnitude factor
        shock_factor = min(shock_magnitude * 2, 1.0)  # Cap at 100%

        # Source and target health factors
        source_node = self.protocol_nodes[edge.source_protocol]
        target_node = self.protocol_nodes[edge.target_protocol]

        source_health_factor = 2.0 - source_node.health_score  # Lower health = higher transmission
        target_vulnerability = 2.0 - target_node.health_score   # Lower health = higher susceptibility

        # Contagion type multipliers
        type_multipliers = {
            ContagionType.DIRECT: 1.5,       # Direct connections stronger
            ContagionType.LIQUIDITY: 1.2,    # Liquidity contagion significant
            ContagionType.CORRELATION: 1.0,  # Base level
            ContagionType.CONFIDENCE: 0.8,   # Confidence contagion slower
            ContagionType.FUNDING: 1.3,      # Funding contagion strong
            ContagionType.OPERATIONAL: 1.1   # Operational dependencies
        }

        type_multiplier = type_multipliers.get(edge.contagion_type, 1.0)

        # Network effects (highly connected nodes spread contagion more)
        network_effect = (source_node.interconnectedness + target_node.interconnectedness) / 2

        # Calculate final probability
        transmission_prob = (
            base_prob *
            shock_factor *
            source_health_factor *
            target_vulnerability *
            type_multiplier *
            network_effect
        )

        return min(transmission_prob, 0.95)  # Cap at 95%

    def _calculate_expected_impact(
        self,
        edge: ContagionEdge,
        shock_magnitude: float,
        transmission_prob: float
    ) -> float:
        """Calculate expected impact on target protocol"""

        # Base impact proportional to shock and transmission probability
        base_impact = shock_magnitude * transmission_prob * edge.strength

        # Target protocol vulnerability
        target_node = self.protocol_nodes[edge.target_protocol]
        vulnerability_factor = 2.0 - target_node.health_score

        # Contagion type impact factors
        impact_factors = {
            ContagionType.DIRECT: 0.8,       # Direct impact high
            ContagionType.LIQUIDITY: 0.6,    # Liquidity impact moderate
            ContagionType.CORRELATION: 0.4,  # Correlation impact lower
            ContagionType.CONFIDENCE: 0.3,   # Confidence impact gradual
            ContagionType.FUNDING: 0.7,      # Funding impact significant
            ContagionType.OPERATIONAL: 0.5   # Operational impact moderate
        }

        impact_factor = impact_factors.get(edge.contagion_type, 0.5)

        # Protocol size factor (larger protocols more resilient)
        size_factor = 1.0 / (1.0 + target_node.tvl / 100_000_000)  # Normalize by $100M

        expected_impact = base_impact * vulnerability_factor * impact_factor * (1 + size_factor)

        return min(expected_impact, 0.9)  # Cap at 90% impact

    def _determine_primary_contagion_type(self, pathways: List[Dict[str, Any]]) -> ContagionType:
        """Determine the primary contagion type from pathways"""
        if not pathways:
            return ContagionType.CORRELATION

        # Weight by transmission probability
        type_weights = defaultdict(float)

        for pathway in pathways:
            contagion_type = pathway['contagion_type']
            weight = pathway['transmission_probability']
            type_weights[contagion_type] += weight

        # Return type with highest weight
        return max(type_weights.items(), key=lambda x: x[1])[0]

    def _assess_contagion_severity(
        self,
        pathways: List[Dict[str, Any]],
        shock_magnitude: float
    ) -> ContagionSeverity:
        """Assess overall severity of contagion event"""

        if not pathways:
            return ContagionSeverity.LOW

        # Calculate severity metrics
        num_affected = len(pathways)
        max_impact = max(pathway['expected_impact'] for pathway in pathways)
        avg_transmission_prob = np.mean([pathway['transmission_probability'] for pathway in pathways])

        # Calculate total system impact
        total_tvl = sum(node.tvl for node in self.protocol_nodes.values())
        affected_tvl = sum(
            self.protocol_nodes[pathway['target']].tvl for pathway in pathways
        )
        system_impact_ratio = affected_tvl / total_tvl

        # Severity classification
        severity_score = (
            (num_affected / len(self.protocol_nodes)) * 0.3 +  # Breadth of impact
            max_impact * 0.3 +                                 # Maximum single impact
            avg_transmission_prob * 0.2 +                      # Transmission strength
            system_impact_ratio * 0.2                          # System-wide impact
        )

        if severity_score < 0.2:
            return ContagionSeverity.LOW
        elif severity_score < 0.4:
            return ContagionSeverity.MEDIUM
        elif severity_score < 0.6:
            return ContagionSeverity.HIGH
        elif severity_score < 0.8:
            return ContagionSeverity.CRITICAL
        else:
            return ContagionSeverity.SYSTEMIC

    def _construct_transmission_path(self, pathways: List[Dict[str, Any]]) -> List[str]:
        """Construct the primary transmission path"""
        if not pathways:
            return []

        # Sort by transmission delay to get sequence
        sorted_pathways = sorted(pathways, key=lambda x: x['transmission_delay'])

        # Build path
        path = [sorted_pathways[0]['source']]

        for pathway in sorted_pathways:
            if pathway['target'] not in path:
                path.append(pathway['target'])

        return path

    def _calculate_impact_metrics(self, pathways: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate comprehensive impact metrics"""
        if not pathways:
            return {}

        impacts = [pathway['expected_impact'] for pathway in pathways]
        probs = [pathway['transmission_probability'] for pathway in pathways]

        return {
            'max_single_impact': max(impacts),
            'total_expected_impact': sum(impacts),
            'avg_transmission_probability': np.mean(probs),
            'num_protocols_affected': len(pathways),
            'cascade_amplification': sum(impacts) / pathways[0]['expected_impact'] if pathways else 1.0
        }

    def _estimate_recovery_time(self, pathways: List[Dict[str, Any]]) -> float:
        """Estimate recovery time from contagion event"""
        if not pathways:
            return 0.0

        # Base recovery time from longest transmission delay
        max_delay = max(pathway['transmission_delay'] for pathway in pathways)
        base_recovery = max_delay * 3  # Usually 3x the transmission time

        # Adjust for severity
        max_impact = max(pathway['expected_impact'] for pathway in pathways)
        severity_multiplier = 1 + max_impact

        # Adjust for number of affected protocols
        complexity_multiplier = 1 + (len(pathways) - 1) * 0.2

        recovery_time = base_recovery * severity_multiplier * complexity_multiplier

        return min(recovery_time, 168)  # Cap at 1 week

    async def simulate_contagion_propagation(
        self,
        initial_shock: Dict[str, float],
        simulation_steps: int = 48,
        intervention_scenarios: List[Dict[str, Any]] = None
    ) -> ContagionSimulation:
        """
        Simulate contagion propagation through the network

        Args:
            initial_shock: Protocol -> shock magnitude
            simulation_steps: Number of time steps (hours)
            intervention_scenarios: Possible intervention scenarios

        Returns:
            Comprehensive contagion simulation results
        """
        logger.info(f"Simulating contagion propagation over {simulation_steps} steps")

        simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize protocol states
        protocol_states = {}
        for protocol_id, node in self.protocol_nodes.items():
            protocol_states[protocol_id] = {
                'health_score': node.health_score,
                'status': node.status,
                'cumulative_impact': initial_shock.get(protocol_id, 0.0),
                'last_shock_step': 0 if protocol_id in initial_shock else -1
            }

        propagation_timeline = []
        step = 0

        # Propagation simulation
        while step < simulation_steps:
            step_events = []
            new_shocks = {}

            # Check for contagion propagation in this step
            for (source, target), edge in self.contagion_edges.items():
                source_state = protocol_states[source]
                target_state = protocol_states[target]

                # Check if source has recent shock and enough time has passed
                if (source_state['last_shock_step'] >= 0 and
                    step - source_state['last_shock_step'] >= edge.transmission_delay):

                    # Calculate transmission
                    source_impact = source_state['cumulative_impact']

                    if source_impact > 0.01:  # Minimum threshold
                        transmission_prob = self._calculate_transmission_probability(
                            edge, source_impact
                        )

                        # Stochastic transmission
                        if np.random.random() < transmission_prob:
                            transmitted_impact = self._calculate_expected_impact(
                                edge, source_impact, transmission_prob
                            )

                            # Apply dampening
                            dampening = self.propagation_params['decay_rate'] ** (step / 24)
                            final_impact = transmitted_impact * dampening

                            if target not in new_shocks:
                                new_shocks[target] = 0
                            new_shocks[target] += final_impact

                            step_events.append({
                                'step': step,
                                'source': source,
                                'target': target,
                                'transmitted_impact': final_impact,
                                'transmission_probability': transmission_prob,
                                'contagion_type': edge.contagion_type.value
                            })

            # Apply new shocks
            for protocol, shock in new_shocks.items():
                protocol_states[protocol]['cumulative_impact'] += shock
                protocol_states[protocol]['last_shock_step'] = step

                # Update protocol status based on cumulative impact
                cumulative_impact = protocol_states[protocol]['cumulative_impact']

                if cumulative_impact > 0.8:
                    protocol_states[protocol]['status'] = ProtocolStatus.FAILED
                elif cumulative_impact > 0.5:
                    protocol_states[protocol]['status'] = ProtocolStatus.DISTRESSED
                elif cumulative_impact > 0.2:
                    protocol_states[protocol]['status'] = ProtocolStatus.STRESSED
                else:
                    protocol_states[protocol]['status'] = ProtocolStatus.HEALTHY

                # Update health score
                protocol_states[protocol]['health_score'] = max(
                    0.1, 1.0 - cumulative_impact
                )

            # Record step
            if step_events:
                propagation_timeline.append({
                    'step': step,
                    'events': step_events,
                    'protocol_states': {k: v.copy() for k, v in protocol_states.items()}
                })

            step += 1

            # Check for intervention scenarios
            if intervention_scenarios:
                for intervention in intervention_scenarios:
                    if intervention.get('trigger_step') == step:
                        self._apply_intervention(protocol_states, intervention)

        # Calculate final results
        final_impacts = {
            protocol: state['cumulative_impact']
            for protocol, state in protocol_states.items()
        }

        affected_protocols = [
            protocol for protocol, impact in final_impacts.items()
            if impact > 0.01
        ]

        total_system_impact = sum(final_impacts.values()) / len(self.protocol_nodes)

        cascade_depth = len(propagation_timeline)

        # Generate recovery scenarios
        recovery_scenarios = self._generate_recovery_scenarios(protocol_states)

        simulation = ContagionSimulation(
            simulation_id=simulation_id,
            initial_shock=initial_shock,
            propagation_timeline=propagation_timeline,
            final_impacts=final_impacts,
            total_system_impact=total_system_impact,
            affected_protocols=affected_protocols,
            cascade_depth=cascade_depth,
            recovery_scenarios=recovery_scenarios
        )

        self.simulation_results.append(simulation)

        return simulation

    def _apply_intervention(
        self,
        protocol_states: Dict[str, Dict[str, Any]],
        intervention: Dict[str, Any]
    ):
        """Apply intervention scenario to simulation"""
        intervention_type = intervention.get('type', 'liquidity_injection')
        target_protocols = intervention.get('targets', [])
        effectiveness = intervention.get('effectiveness', 0.5)

        for protocol in target_protocols:
            if protocol in protocol_states:
                if intervention_type == 'liquidity_injection':
                    # Reduce cumulative impact
                    reduction = protocol_states[protocol]['cumulative_impact'] * effectiveness
                    protocol_states[protocol]['cumulative_impact'] -= reduction
                    protocol_states[protocol]['health_score'] = min(1.0,
                        protocol_states[protocol]['health_score'] + reduction)

                elif intervention_type == 'circuit_breaker':
                    # Temporarily halt contagion transmission
                    protocol_states[protocol]['last_shock_step'] = -999  # Prevent transmission

                elif intervention_type == 'bailout':
                    # Restore protocol to healthy state
                    protocol_states[protocol]['cumulative_impact'] = 0.0
                    protocol_states[protocol]['health_score'] = 1.0
                    protocol_states[protocol]['status'] = ProtocolStatus.HEALTHY

    def _generate_recovery_scenarios(
        self,
        final_states: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Generate recovery scenarios based on final states"""

        scenarios = {}

        # Natural recovery scenario
        natural_recovery_time = 0
        for protocol, state in final_states.items():
            impact = state['cumulative_impact']
            # Recovery time proportional to impact
            recovery_time = impact * 72  # Up to 72 hours for full impact
            natural_recovery_time = max(natural_recovery_time, recovery_time)

        scenarios['natural_recovery'] = {
            'recovery_time_hours': natural_recovery_time,
            'intervention_cost': 0,
            'success_probability': 0.8,
            'residual_impact': 0.1  # 10% residual impact
        }

        # Intervention scenarios
        total_impact = sum(state['cumulative_impact'] for state in final_states.values())

        scenarios['liquidity_support'] = {
            'recovery_time_hours': natural_recovery_time * 0.6,
            'intervention_cost': total_impact * 10_000_000,  # $10M per unit impact
            'success_probability': 0.9,
            'residual_impact': 0.05
        }

        scenarios['coordinated_response'] = {
            'recovery_time_hours': natural_recovery_time * 0.4,
            'intervention_cost': total_impact * 20_000_000,  # $20M per unit impact
            'success_probability': 0.95,
            'residual_impact': 0.02
        }

        return scenarios

    async def analyze_network_vulnerabilities(self) -> Dict[str, Any]:
        """Analyze systemic vulnerabilities in the protocol network"""
        logger.info("Analyzing network vulnerabilities")

        # Calculate network metrics
        network_metrics = self._calculate_network_metrics()

        # Identify critical nodes
        critical_nodes = self._identify_critical_nodes()

        # Analyze contagion pathways
        pathway_analysis = self._analyze_pathway_vulnerabilities()

        # Stress test network
        stress_test_results = await self._stress_test_network()

        # Calculate systemic risk indicators
        systemic_indicators = self._calculate_systemic_risk_indicators()

        return {
            'network_metrics': network_metrics,
            'critical_nodes': critical_nodes,
            'pathway_vulnerabilities': pathway_analysis,
            'stress_test_results': stress_test_results,
            'systemic_risk_indicators': systemic_indicators,
            'vulnerability_assessment': self._assess_overall_vulnerability(
                network_metrics, critical_nodes, pathway_analysis
            )
        }

    def _calculate_network_metrics(self) -> Dict[str, float]:
        """Calculate network topology metrics"""
        G = self.protocol_network

        return {
            'network_density': nx.density(G),
            'avg_clustering': nx.average_clustering(G.to_undirected()),
            'connectivity': nx.node_connectivity(G.to_undirected()),
            'avg_path_length': nx.average_shortest_path_length(G.to_undirected())
                if nx.is_connected(G.to_undirected()) else float('inf'),
            'centralization': self._calculate_centralization(),
            'robustness_index': self._calculate_robustness_index()
        }

    def _calculate_centralization(self) -> float:
        """Calculate network centralization"""
        G = self.protocol_network

        # Use betweenness centrality
        centrality = nx.betweenness_centrality(G)
        max_centrality = max(centrality.values())

        # Calculate centralization index
        n = len(G.nodes())
        if n <= 2:
            return 0.0

        centralization = sum(max_centrality - c for c in centrality.values())
        max_possible = (n - 1) * (n - 2)

        return centralization / max_possible if max_possible > 0 else 0.0

    def _calculate_robustness_index(self) -> float:
        """Calculate network robustness to node failures"""
        G = self.protocol_network.to_undirected()
        n = len(G.nodes())

        if n <= 1:
            return 1.0

        # Calculate robustness as fraction of nodes that can be removed
        # while maintaining connectivity
        robustness = 0

        for k in range(1, n):
            # Check if removing k random nodes still leaves network connected
            connected_fraction = 0
            trials = 10  # Monte Carlo sampling

            for _ in range(trials):
                nodes_to_remove = np.random.choice(list(G.nodes()), k, replace=False)
                G_temp = G.copy()
                G_temp.remove_nodes_from(nodes_to_remove)

                if len(G_temp.nodes()) > 0 and nx.is_connected(G_temp):
                    connected_fraction += 1

            if connected_fraction / trials < 0.5:  # 50% threshold
                break

            robustness = k / n

        return robustness

    def _identify_critical_nodes(self) -> Dict[str, Dict[str, float]]:
        """Identify critical nodes in the network"""
        G = self.protocol_network

        critical_nodes = {}

        for node_id in G.nodes():
            node = self.protocol_nodes[node_id]

            # Calculate various centrality measures
            betweenness = nx.betweenness_centrality(G)[node_id]
            closeness = nx.closeness_centrality(G)[node_id]
            degree = G.degree(node_id) / (len(G.nodes()) - 1)  # Normalized

            # Economic importance
            economic_importance = node.tvl / sum(n.tvl for n in self.protocol_nodes.values())

            # Systemic importance score
            systemic_score = (
                betweenness * 0.3 +
                closeness * 0.2 +
                degree * 0.2 +
                economic_importance * 0.2 +
                node.systemic_importance * 0.1
            )

            critical_nodes[node_id] = {
                'systemic_score': systemic_score,
                'betweenness_centrality': betweenness,
                'closeness_centrality': closeness,
                'degree_centrality': degree,
                'economic_importance': economic_importance,
                'interconnectedness': node.interconnectedness,
                'tvl': node.tvl
            }

        return critical_nodes

    def _analyze_pathway_vulnerabilities(self) -> Dict[str, Any]:
        """Analyze vulnerabilities in contagion pathways"""
        pathway_analysis = {
            'high_risk_pathways': [],
            'pathway_redundancy': {},
            'bottleneck_analysis': {},
            'cascade_potential': {}
        }

        # Analyze high-risk pathways
        for (source, target), edge in self.contagion_edges.items():
            risk_score = edge.strength * (2.0 - self.protocol_nodes[target].health_score)

            if risk_score > 0.7:  # High risk threshold
                pathway_analysis['high_risk_pathways'].append({
                    'source': source,
                    'target': target,
                    'risk_score': risk_score,
                    'contagion_type': edge.contagion_type.value,
                    'strength': edge.strength
                })

        # Analyze pathway redundancy
        for node_id in self.protocol_nodes.keys():
            incoming_paths = [edge for (s, t), edge in self.contagion_edges.items() if t == node_id]
            outgoing_paths = [edge for (s, t), edge in self.contagion_edges.items() if s == node_id]

            pathway_analysis['pathway_redundancy'][node_id] = {
                'incoming_redundancy': len(incoming_paths),
                'outgoing_redundancy': len(outgoing_paths),
                'total_redundancy': len(incoming_paths) + len(outgoing_paths)
            }

        # Identify bottlenecks
        for node_id in self.protocol_nodes.keys():
            # Calculate how much contagion flow goes through this node
            betweenness = nx.betweenness_centrality(self.protocol_network)[node_id]

            pathway_analysis['bottleneck_analysis'][node_id] = {
                'betweenness_centrality': betweenness,
                'is_bottleneck': betweenness > 0.3,  # Threshold for bottleneck
                'failure_impact': self._calculate_node_failure_impact(node_id)
            }

        return pathway_analysis

    def _calculate_node_failure_impact(self, node_id: str) -> float:
        """Calculate impact of node failure on network connectivity"""
        G = self.protocol_network.copy()

        # Calculate original connectivity
        original_connectivity = nx.node_connectivity(G.to_undirected())

        # Remove node and calculate new connectivity
        G.remove_node(node_id)

        if len(G.nodes()) > 1:
            new_connectivity = nx.node_connectivity(G.to_undirected())
        else:
            new_connectivity = 0

        # Impact is the relative decrease in connectivity
        if original_connectivity > 0:
            impact = (original_connectivity - new_connectivity) / original_connectivity
        else:
            impact = 0

        return impact

    async def _stress_test_network(self) -> Dict[str, Any]:
        """Stress test the network under various failure scenarios"""
        stress_scenarios = [
            {'name': 'single_critical_failure', 'failed_nodes': 1},
            {'name': 'double_failure', 'failed_nodes': 2},
            {'name': 'lending_protocol_failure', 'protocol_type': 'lending'},
            {'name': 'dex_failure', 'protocol_type': 'dex'},
            {'name': 'cascade_failure', 'cascade': True}
        ]

        stress_results = {}

        for scenario in stress_scenarios:
            scenario_name = scenario['name']

            if 'failed_nodes' in scenario:
                # Random node failure
                n_failures = scenario['failed_nodes']
                failure_impact = await self._simulate_random_failures(n_failures)

            elif 'protocol_type' in scenario:
                # Protocol type failure
                protocol_type = scenario['protocol_type']
                failure_impact = await self._simulate_protocol_type_failure(protocol_type)

            elif scenario.get('cascade'):
                # Cascade failure simulation
                failure_impact = await self._simulate_cascade_failure()

            else:
                failure_impact = {'error': 'Unknown scenario type'}

            stress_results[scenario_name] = failure_impact

        return stress_results

    async def _simulate_random_failures(self, n_failures: int) -> Dict[str, Any]:
        """Simulate random node failures"""
        # Select nodes to fail (weighted by systemic importance)
        nodes = list(self.protocol_nodes.keys())
        weights = [self.protocol_nodes[node].systemic_importance for node in nodes]

        if n_failures >= len(nodes):
            failed_nodes = nodes
        else:
            failed_nodes = np.random.choice(
                nodes, n_failures, replace=False, p=np.array(weights)/sum(weights)
            ).tolist()

        # Simulate contagion from failures
        initial_shock = {node: 0.8 for node in failed_nodes}  # 80% shock to failed nodes

        simulation = await self.simulate_contagion_propagation(initial_shock)

        return {
            'failed_nodes': failed_nodes,
            'total_impact': simulation.total_system_impact,
            'affected_protocols': simulation.affected_protocols,
            'cascade_depth': simulation.cascade_depth,
            'recovery_time': min(simulation.recovery_scenarios['natural_recovery']['recovery_time_hours'], 168)
        }

    async def _simulate_protocol_type_failure(self, protocol_type: str) -> Dict[str, Any]:
        """Simulate failure of all protocols of a specific type"""
        failed_nodes = [
            node_id for node_id, node in self.protocol_nodes.items()
            if node.protocol_type == protocol_type
        ]

        if not failed_nodes:
            return {'error': f'No protocols of type {protocol_type} found'}

        initial_shock = {node: 0.9 for node in failed_nodes}  # 90% shock

        simulation = await self.simulate_contagion_propagation(initial_shock)

        return {
            'failed_protocol_type': protocol_type,
            'failed_nodes': failed_nodes,
            'total_impact': simulation.total_system_impact,
            'affected_protocols': simulation.affected_protocols,
            'cascade_depth': simulation.cascade_depth,
            'systemic_disruption': len(simulation.affected_protocols) / len(self.protocol_nodes)
        }

    async def _simulate_cascade_failure(self) -> Dict[str, Any]:
        """Simulate a cascading failure scenario"""
        # Start with the most systemically important protocol
        critical_nodes = self._identify_critical_nodes()
        start_node = max(critical_nodes.items(), key=lambda x: x[1]['systemic_score'])[0]

        # Apply progressive shocks
        initial_shock = {start_node: 0.6}  # Initial 60% shock

        simulation = await self.simulate_contagion_propagation(
            initial_shock, simulation_steps=72  # 3 days
        )

        return {
            'cascade_origin': start_node,
            'total_impact': simulation.total_system_impact,
            'affected_protocols': simulation.affected_protocols,
            'cascade_depth': simulation.cascade_depth,
            'max_single_impact': max(simulation.final_impacts.values()),
            'cascade_efficiency': simulation.total_system_impact / 0.6  # Amplification factor
        }

    def _calculate_systemic_risk_indicators(self) -> Dict[str, float]:
        """Calculate systemic risk indicators for the network"""
        # Network concentration (Herfindahl-Hirschman Index)
        total_tvl = sum(node.tvl for node in self.protocol_nodes.values())
        hhi = sum((node.tvl / total_tvl) ** 2 for node in self.protocol_nodes.values())

        # Interconnectedness measure
        avg_interconnectedness = np.mean([node.interconnectedness for node in self.protocol_nodes.values()])

        # Health fragility (inverse of average health)
        avg_health = np.mean([node.health_score for node in self.protocol_nodes.values()])
        health_fragility = 1.0 - avg_health

        # Contagion potential
        total_edge_strength = sum(edge.strength for edge in self.contagion_edges.values())
        avg_edge_strength = total_edge_strength / len(self.contagion_edges) if self.contagion_edges else 0

        # Systemic importance concentration
        systemic_importance_values = [node.systemic_importance for node in self.protocol_nodes.values()]
        systemic_concentration = np.std(systemic_importance_values) / np.mean(systemic_importance_values)

        return {
            'network_concentration_hhi': hhi,
            'avg_interconnectedness': avg_interconnectedness,
            'health_fragility': health_fragility,
            'contagion_potential': avg_edge_strength,
            'systemic_concentration': systemic_concentration,
            'overall_systemic_risk': (hhi + avg_interconnectedness + health_fragility +
                                    avg_edge_strength + systemic_concentration) / 5
        }

    def _assess_overall_vulnerability(
        self,
        network_metrics: Dict[str, float],
        critical_nodes: Dict[str, Dict[str, float]],
        pathway_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall network vulnerability"""

        # Calculate vulnerability scores
        structural_vulnerability = (
            network_metrics['centralization'] * 0.4 +
            (1 - network_metrics['robustness_index']) * 0.3 +
            network_metrics['network_density'] * 0.3
        )

        # Critical node vulnerability
        max_systemic_score = max(node['systemic_score'] for node in critical_nodes.values())
        critical_vulnerability = max_systemic_score

        # Pathway vulnerability
        high_risk_count = len(pathway_analysis['high_risk_pathways'])
        total_pathways = len(self.contagion_edges)
        pathway_vulnerability = high_risk_count / total_pathways if total_pathways > 0 else 0

        # Overall vulnerability
        overall_vulnerability = (
            structural_vulnerability * 0.4 +
            critical_vulnerability * 0.3 +
            pathway_vulnerability * 0.3
        )

        # Risk level classification
        if overall_vulnerability < 0.3:
            risk_level = "LOW"
        elif overall_vulnerability < 0.5:
            risk_level = "MEDIUM"
        elif overall_vulnerability < 0.7:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return {
            'structural_vulnerability': structural_vulnerability,
            'critical_node_vulnerability': critical_vulnerability,
            'pathway_vulnerability': pathway_vulnerability,
            'overall_vulnerability': overall_vulnerability,
            'risk_level': risk_level,
            'key_risks': self._identify_key_risks(
                network_metrics, critical_nodes, pathway_analysis
            )
        }

    def _identify_key_risks(
        self,
        network_metrics: Dict[str, float],
        critical_nodes: Dict[str, Dict[str, float]],
        pathway_analysis: Dict[str, Any]
    ) -> List[str]:
        """Identify key risks in the network"""
        risks = []

        # Structural risks
        if network_metrics['centralization'] > 0.7:
            risks.append("High network centralization - failure of central nodes could be catastrophic")

        if network_metrics['robustness_index'] < 0.3:
            risks.append("Low network robustness - vulnerable to node failures")

        # Critical node risks
        max_systemic_node = max(critical_nodes.items(), key=lambda x: x[1]['systemic_score'])
        if max_systemic_node[1]['systemic_score'] > 0.8:
            risks.append(f"Critical dependency on {max_systemic_node[0]} - single point of failure")

        # High-risk pathways
        if len(pathway_analysis['high_risk_pathways']) > len(self.contagion_edges) * 0.3:
            risks.append("High number of risky contagion pathways")

        # Bottleneck risks
        bottlenecks = [
            node for node, analysis in pathway_analysis['bottleneck_analysis'].items()
            if analysis['is_bottleneck']
        ]
        if len(bottlenecks) > 0:
            risks.append(f"Network bottlenecks detected: {', '.join(bottlenecks)}")

        return risks

    def get_contagion_statistics(self) -> Dict[str, Any]:
        """Get comprehensive contagion detection statistics"""
        if not self.contagion_events:
            return {'error': 'No contagion events detected'}

        events = self.contagion_events
        simulations = self.simulation_results

        return {
            'detection_summary': {
                'total_events_detected': len(events),
                'total_simulations_run': len(simulations),
                'avg_affected_protocols': np.mean([len(event.affected_protocols) for event in events]),
                'severity_distribution': {
                    severity.value: sum(1 for event in events if event.severity == severity)
                    for severity in ContagionSeverity
                }
            },
            'contagion_patterns': {
                'most_common_source': self._find_most_common_source(),
                'most_vulnerable_target': self._find_most_vulnerable_target(),
                'primary_contagion_types': self._analyze_contagion_types(),
                'average_recovery_time': np.mean([event.recovery_time_estimate for event in events])
            },
            'simulation_analysis': {
                'avg_system_impact': np.mean([sim.total_system_impact for sim in simulations]),
                'max_cascade_depth': max([sim.cascade_depth for sim in simulations]) if simulations else 0,
                'most_affected_protocol': self._find_most_affected_protocol_in_simulations()
            },
            'network_health': {
                'avg_protocol_health': np.mean([node.health_score for node in self.protocol_nodes.values()]),
                'protocols_at_risk': sum(1 for node in self.protocol_nodes.values() if node.health_score < 0.7),
                'network_resilience_score': self._calculate_network_resilience()
            }
        }

    def _find_most_common_source(self) -> str:
        """Find most common contagion source protocol"""
        if not self.contagion_events:
            return "None"

        source_counts = defaultdict(int)
        for event in self.contagion_events:
            source_counts[event.source_protocol] += 1

        return max(source_counts.items(), key=lambda x: x[1])[0] if source_counts else "None"

    def _find_most_vulnerable_target(self) -> str:
        """Find most vulnerable target protocol"""
        if not self.contagion_events:
            return "None"

        target_counts = defaultdict(int)
        for event in self.contagion_events:
            for target in event.affected_protocols:
                target_counts[target] += 1

        return max(target_counts.items(), key=lambda x: x[1])[0] if target_counts else "None"

    def _analyze_contagion_types(self) -> Dict[str, int]:
        """Analyze distribution of contagion types"""
        type_counts = defaultdict(int)
        for event in self.contagion_events:
            type_counts[event.contagion_type.value] += 1

        return dict(type_counts)

    def _find_most_affected_protocol_in_simulations(self) -> str:
        """Find protocol most affected across simulations"""
        if not self.simulation_results:
            return "None"

        protocol_impacts = defaultdict(list)
        for sim in self.simulation_results:
            for protocol, impact in sim.final_impacts.items():
                protocol_impacts[protocol].append(impact)

        # Calculate average impact per protocol
        avg_impacts = {
            protocol: np.mean(impacts)
            for protocol, impacts in protocol_impacts.items()
        }

        return max(avg_impacts.items(), key=lambda x: x[1])[0] if avg_impacts else "None"

    def _calculate_network_resilience(self) -> float:
        """Calculate overall network resilience score"""
        # Combine multiple resilience factors
        avg_health = np.mean([node.health_score for node in self.protocol_nodes.values()])
        diversity = 1.0 - self._calculate_protocol_concentration()
        connectivity = min(1.0, nx.node_connectivity(self.protocol_network.to_undirected()) / 2)

        resilience = (avg_health * 0.4 + diversity * 0.3 + connectivity * 0.3)
        return resilience

    def _calculate_protocol_concentration(self) -> float:
        """Calculate protocol concentration (Herfindahl-Hirschman Index)"""
        total_tvl = sum(node.tvl for node in self.protocol_nodes.values())
        if total_tvl == 0:
            return 0

        return sum((node.tvl / total_tvl) ** 2 for node in self.protocol_nodes.values())


# Example usage and testing
async def main():
    """Example usage of the contagion detector"""
    detector = ContagionDetector()

    # Detect contagion from a trigger event
    trigger_events = [
        {'protocol': 'algofi', 'magnitude': 0.3, 'type': 'liquidity_crisis'}
    ]

    contagion_events = await detector.detect_contagion_risk(trigger_events)

    print("Contagion Detection Results:")
    for event in contagion_events:
        print(f"Event: {event.event_id}")
        print(f"Source: {event.source_protocol}")
        print(f"Affected: {event.affected_protocols}")
        print(f"Severity: {event.severity.value}")
        print(f"Recovery Time: {event.recovery_time_estimate:.1f} hours")

    # Run contagion simulation
    initial_shock = {'algofi': 0.4, 'tinyman': 0.2}
    simulation = await detector.simulate_contagion_propagation(initial_shock)

    print(f"\nContagion Simulation:")
    print(f"Total System Impact: {simulation.total_system_impact:.3f}")
    print(f"Affected Protocols: {len(simulation.affected_protocols)}")
    print(f"Cascade Depth: {simulation.cascade_depth}")

    # Analyze network vulnerabilities
    vulnerability_analysis = await detector.analyze_network_vulnerabilities()

    print(f"\nNetwork Vulnerability Analysis:")
    print(f"Overall Vulnerability: {vulnerability_analysis['vulnerability_assessment']['overall_vulnerability']:.3f}")
    print(f"Risk Level: {vulnerability_analysis['vulnerability_assessment']['risk_level']}")

    # Get statistics
    stats = detector.get_contagion_statistics()
    if 'error' not in stats:
        print(f"\nContagion Statistics:")
        print(f"Events Detected: {stats['detection_summary']['total_events_detected']}")
        print(f"Average Recovery Time: {stats['contagion_patterns']['average_recovery_time']:.1f} hours")
        print(f"Network Resilience: {stats['network_health']['network_resilience_score']:.3f}")

if __name__ == "__main__":
    asyncio.run(main())