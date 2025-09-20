"""
Cascade Risk Modeling

Models cascade effects and contagion risks in DeFi protocols
and blockchain ecosystems for systemic risk assessment.
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import json
from collections import defaultdict, deque


class CascadeType(Enum):
    """Types of cascade effects"""
    LIQUIDITY_CRISIS = "liquidity_crisis"
    LIQUIDATION_CASCADE = "liquidation_cascade"
    ORACLE_FAILURE = "oracle_failure"
    BRIDGE_FAILURE = "bridge_failure"
    GOVERNANCE_ATTACK = "governance_attack"
    SMART_CONTRACT_EXPLOIT = "smart_contract_exploit"
    MARKET_PANIC = "market_panic"


class NodeType(Enum):
    """Types of nodes in the risk network"""
    PROTOCOL = "protocol"
    ASSET = "asset"
    WALLET = "wallet"
    ORACLE = "oracle"
    BRIDGE = "bridge"
    EXCHANGE = "exchange"


@dataclass
class RiskNode:
    """Node in the cascade risk network"""
    node_id: str
    node_type: NodeType
    name: str
    tvl: float
    risk_score: float
    critical_threshold: float
    recovery_time: timedelta
    dependencies: List[str]
    dependents: List[str]
    stress_multiplier: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CascadeEdge:
    """Edge representing risk transmission between nodes"""
    source_node: str
    target_node: str
    transmission_probability: float
    impact_multiplier: float
    transmission_delay: timedelta
    edge_type: str
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CascadeEvent:
    """Cascade event in the simulation"""
    event_id: str
    timestamp: datetime
    affected_node: str
    event_type: CascadeType
    severity: float
    caused_by: Optional[str]
    impact_magnitude: float
    recovery_estimate: timedelta


@dataclass
class CascadeSimulationResult:
    """Result of cascade simulation"""
    initial_shock: Dict[str, float]
    cascade_events: List[CascadeEvent]
    final_state: Dict[str, float]
    total_impact: float
    affected_nodes: Set[str]
    cascade_depth: int
    simulation_duration: timedelta
    peak_impact_time: datetime
    recovery_scenarios: Dict[str, timedelta]


class CascadeRiskModeler:
    """Advanced cascade risk modeling system"""

    def __init__(self):
        self.risk_network = {}
        self.transmission_edges = {}
        self.cascade_parameters = {
            'max_simulation_time': timedelta(days=30),
            'time_step': timedelta(hours=1),
            'convergence_threshold': 0.001,
            'max_iterations': 1000
        }
        self.historical_cascades = []

    async def build_risk_network(
        self,
        protocols: List[Dict[str, Any]],
        assets: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> None:
        """
        Build the risk network from protocol and asset data

        Args:
            protocols: List of protocol data
            assets: List of asset data
            relationships: List of relationships/dependencies
        """
        # Add protocol nodes
        for protocol in protocols:
            node = RiskNode(
                node_id=protocol['id'],
                node_type=NodeType.PROTOCOL,
                name=protocol['name'],
                tvl=protocol.get('tvl', 0),
                risk_score=protocol.get('risk_score', 0.5),
                critical_threshold=protocol.get('critical_threshold', 0.8),
                recovery_time=timedelta(days=protocol.get('recovery_days', 7)),
                dependencies=[],
                dependents=[],
                stress_multiplier=protocol.get('stress_multiplier', 1.0),
                metadata=protocol.get('metadata', {})
            )
            self.risk_network[node.node_id] = node

        # Add asset nodes
        for asset in assets:
            node = RiskNode(
                node_id=asset['id'],
                node_type=NodeType.ASSET,
                name=asset['name'],
                tvl=asset.get('market_cap', 0),
                risk_score=asset.get('risk_score', 0.3),
                critical_threshold=asset.get('critical_threshold', 0.7),
                recovery_time=timedelta(days=asset.get('recovery_days', 3)),
                dependencies=[],
                dependents=[],
                stress_multiplier=asset.get('volatility_multiplier', 1.2),
                metadata=asset.get('metadata', {})
            )
            self.risk_network[node.node_id] = node

        # Build edges from relationships
        await self._build_transmission_edges(relationships)

    async def _build_transmission_edges(
        self,
        relationships: List[Dict[str, Any]]
    ) -> None:
        """Build transmission edges from relationship data"""
        for relationship in relationships:
            source = relationship['source']
            target = relationship['target']

            if source in self.risk_network and target in self.risk_network:
                edge = CascadeEdge(
                    source_node=source,
                    target_node=target,
                    transmission_probability=relationship.get('transmission_probability', 0.5),
                    impact_multiplier=relationship.get('impact_multiplier', 0.8),
                    transmission_delay=timedelta(
                        hours=relationship.get('delay_hours', 1)
                    ),
                    edge_type=relationship.get('type', 'dependency'),
                    conditions=relationship.get('conditions', {})
                )

                edge_key = f"{source}_{target}"
                self.transmission_edges[edge_key] = edge

                # Update node dependencies
                self.risk_network[source].dependents.append(target)
                self.risk_network[target].dependencies.append(source)

    async def simulate_cascade_scenario(
        self,
        initial_shock: Dict[str, float],
        scenario_type: CascadeType,
        market_conditions: Dict[str, Any] = None
    ) -> CascadeSimulationResult:
        """
        Simulate cascade scenario

        Args:
            initial_shock: Initial shock values for nodes
            scenario_type: Type of cascade scenario
            market_conditions: Market condition parameters

        Returns:
            Cascade simulation result
        """
        # Initialize simulation state
        current_state = {node_id: node.risk_score for node_id, node in self.risk_network.items()}

        # Apply initial shock
        for node_id, shock_value in initial_shock.items():
            if node_id in current_state:
                current_state[node_id] = min(current_state[node_id] + shock_value, 1.0)

        # Track cascade events
        cascade_events = []
        event_queue = deque()
        simulation_time = datetime.utcnow()
        end_time = simulation_time + self.cascade_parameters['max_simulation_time']

        # Initialize event queue with initial shocks
        for node_id, shock_value in initial_shock.items():
            if shock_value > 0:
                event = CascadeEvent(
                    event_id=f"initial_{node_id}",
                    timestamp=simulation_time,
                    affected_node=node_id,
                    event_type=scenario_type,
                    severity=shock_value,
                    caused_by=None,
                    impact_magnitude=shock_value,
                    recovery_estimate=self.risk_network[node_id].recovery_time
                )
                cascade_events.append(event)
                event_queue.append(event)

        peak_impact = max(current_state.values())
        peak_impact_time = simulation_time
        affected_nodes = set(initial_shock.keys())

        # Run cascade simulation
        iteration = 0
        while event_queue and simulation_time < end_time and iteration < self.cascade_parameters['max_iterations']:
            current_event = event_queue.popleft()

            # Process cascade effects from this event
            new_events = await self._process_cascade_event(
                current_event, current_state, simulation_time, scenario_type, market_conditions
            )

            for new_event in new_events:
                cascade_events.append(new_event)
                event_queue.append(new_event)
                affected_nodes.add(new_event.affected_node)

                # Update peak impact tracking
                if current_state[new_event.affected_node] > peak_impact:
                    peak_impact = current_state[new_event.affected_node]
                    peak_impact_time = new_event.timestamp

            # Advance simulation time
            simulation_time += self.cascade_parameters['time_step']
            iteration += 1

        # Calculate final metrics
        total_impact = await self._calculate_total_impact(current_state, initial_shock)
        cascade_depth = await self._calculate_cascade_depth(cascade_events)
        recovery_scenarios = await self._estimate_recovery_scenarios(
            current_state, cascade_events
        )

        return CascadeSimulationResult(
            initial_shock=initial_shock,
            cascade_events=cascade_events,
            final_state=current_state,
            total_impact=total_impact,
            affected_nodes=affected_nodes,
            cascade_depth=cascade_depth,
            simulation_duration=simulation_time - datetime.utcnow(),
            peak_impact_time=peak_impact_time,
            recovery_scenarios=recovery_scenarios
        )

    async def _process_cascade_event(
        self,
        event: CascadeEvent,
        current_state: Dict[str, float],
        simulation_time: datetime,
        scenario_type: CascadeType,
        market_conditions: Dict[str, Any] = None
    ) -> List[CascadeEvent]:
        """Process a single cascade event and generate new events"""
        new_events = []
        source_node = self.risk_network[event.affected_node]

        # Find all outgoing transmission edges from this node
        outgoing_edges = [
            edge for edge in self.transmission_edges.values()
            if edge.source_node == event.affected_node
        ]

        for edge in outgoing_edges:
            target_node_id = edge.target_node
            target_node = self.risk_network[target_node_id]

            # Check if transmission occurs
            if await self._should_transmit(edge, event, current_state, market_conditions):
                # Calculate transmission impact
                transmission_impact = await self._calculate_transmission_impact(
                    edge, event, target_node, scenario_type, market_conditions
                )

                if transmission_impact > 0:
                    # Update target node state
                    old_state = current_state[target_node_id]
                    new_state = min(old_state + transmission_impact, 1.0)
                    current_state[target_node_id] = new_state

                    # Create new cascade event
                    new_event = CascadeEvent(
                        event_id=f"cascade_{target_node_id}_{len(new_events)}",
                        timestamp=simulation_time + edge.transmission_delay,
                        affected_node=target_node_id,
                        event_type=scenario_type,
                        severity=new_state,
                        caused_by=event.event_id,
                        impact_magnitude=transmission_impact,
                        recovery_estimate=target_node.recovery_time
                    )
                    new_events.append(new_event)

        return new_events

    async def _should_transmit(
        self,
        edge: CascadeEdge,
        source_event: CascadeEvent,
        current_state: Dict[str, float],
        market_conditions: Dict[str, Any] = None
    ) -> bool:
        """Determine if cascade should transmit along edge"""
        # Base transmission probability
        base_probability = edge.transmission_probability

        # Adjust for source event severity
        severity_multiplier = 1.0 + source_event.severity
        adjusted_probability = base_probability * severity_multiplier

        # Adjust for market conditions
        if market_conditions:
            stress_level = market_conditions.get('stress_level', 1.0)
            adjusted_probability *= stress_level

        # Check edge conditions
        if edge.conditions:
            min_severity = edge.conditions.get('min_severity', 0.0)
            if source_event.severity < min_severity:
                return False

            required_node_state = edge.conditions.get('required_node_state', 0.0)
            if current_state.get(edge.target_node, 0) < required_node_state:
                return False

        # Generate random transmission event
        return np.random.random() < min(adjusted_probability, 1.0)

    async def _calculate_transmission_impact(
        self,
        edge: CascadeEdge,
        source_event: CascadeEvent,
        target_node: RiskNode,
        scenario_type: CascadeType,
        market_conditions: Dict[str, Any] = None
    ) -> float:
        """Calculate the impact of transmission to target node"""
        base_impact = source_event.impact_magnitude * edge.impact_multiplier

        # Apply target node stress multiplier
        adjusted_impact = base_impact * target_node.stress_multiplier

        # Scenario-specific adjustments
        if scenario_type == CascadeType.LIQUIDITY_CRISIS:
            if target_node.node_type == NodeType.PROTOCOL:
                adjusted_impact *= 1.5  # Protocols more vulnerable to liquidity
        elif scenario_type == CascadeType.ORACLE_FAILURE:
            if 'oracle_dependent' in target_node.metadata:
                adjusted_impact *= 2.0  # Oracle-dependent protocols more vulnerable

        # Market condition adjustments
        if market_conditions:
            volatility = market_conditions.get('volatility', 1.0)
            adjusted_impact *= volatility

        return min(adjusted_impact, 1.0)

    async def _calculate_total_impact(
        self,
        final_state: Dict[str, float],
        initial_shock: Dict[str, float]
    ) -> float:
        """Calculate total impact of cascade"""
        total_impact = 0.0
        total_value = 0.0

        for node_id, final_risk in final_state.items():
            initial_risk = initial_shock.get(node_id, self.risk_network[node_id].risk_score)
            impact = final_risk - initial_risk

            node_value = self.risk_network[node_id].tvl
            total_impact += impact * node_value
            total_value += node_value

        return total_impact / max(total_value, 1.0)

    async def _calculate_cascade_depth(self, cascade_events: List[CascadeEvent]) -> int:
        """Calculate the depth of the cascade (longest chain of causation)"""
        if not cascade_events:
            return 0

        # Build causation graph
        causation_graph = defaultdict(list)
        for event in cascade_events:
            if event.caused_by:
                causation_graph[event.caused_by].append(event.event_id)

        # Find maximum depth using DFS
        max_depth = 0

        def dfs(event_id: str, current_depth: int) -> int:
            depth = current_depth
            for child_event in causation_graph[event_id]:
                child_depth = dfs(child_event, current_depth + 1)
                depth = max(depth, child_depth)
            return depth

        # Start DFS from initial events (no caused_by)
        initial_events = [event.event_id for event in cascade_events if not event.caused_by]
        for initial_event in initial_events:
            depth = dfs(initial_event, 1)
            max_depth = max(max_depth, depth)

        return max_depth

    async def _estimate_recovery_scenarios(
        self,
        final_state: Dict[str, float],
        cascade_events: List[CascadeEvent]
    ) -> Dict[str, timedelta]:
        """Estimate recovery scenarios"""
        scenarios = {}

        # Optimistic scenario (no additional shocks)
        optimistic_recovery = timedelta(0)
        for node_id, risk_level in final_state.items():
            if risk_level > self.risk_network[node_id].critical_threshold:
                node_recovery = self.risk_network[node_id].recovery_time
                optimistic_recovery = max(optimistic_recovery, node_recovery)

        scenarios['optimistic'] = optimistic_recovery

        # Realistic scenario (with some ongoing stress)
        realistic_recovery = optimistic_recovery * 1.5
        scenarios['realistic'] = realistic_recovery

        # Pessimistic scenario (with additional shocks)
        pessimistic_recovery = optimistic_recovery * 2.5
        scenarios['pessimistic'] = pessimistic_recovery

        return scenarios

    async def analyze_systemic_vulnerabilities(
        self
    ) -> Dict[str, Any]:
        """Analyze systemic vulnerabilities in the network"""
        vulnerabilities = {}

        # Central node analysis
        centrality_scores = await self._calculate_node_centrality()
        vulnerabilities['central_nodes'] = [
            {'node_id': node_id, 'centrality': score}
            for node_id, score in sorted(centrality_scores.items(),
                                       key=lambda x: x[1], reverse=True)[:5]
        ]

        # Critical path analysis
        critical_paths = await self._find_critical_paths()
        vulnerabilities['critical_paths'] = critical_paths

        # Concentration risks
        concentration_risks = await self._analyze_concentration_risks()
        vulnerabilities['concentration_risks'] = concentration_risks

        # Interconnectedness metrics
        interconnectedness = await self._calculate_interconnectedness_metrics()
        vulnerabilities['interconnectedness'] = interconnectedness

        return vulnerabilities

    async def _calculate_node_centrality(self) -> Dict[str, float]:
        """Calculate centrality scores for nodes"""
        centrality_scores = {}

        for node_id, node in self.risk_network.items():
            # Simple degree centrality (in + out connections)
            in_degree = len(node.dependencies)
            out_degree = len(node.dependents)
            total_degree = in_degree + out_degree

            # Weight by TVL
            tvl_weight = node.tvl / max(sum(n.tvl for n in self.risk_network.values()), 1)

            centrality_scores[node_id] = total_degree * (1 + tvl_weight)

        return centrality_scores

    async def _find_critical_paths(self) -> List[List[str]]:
        """Find critical paths through the network"""
        critical_paths = []

        # Use DFS to find long dependency chains
        def dfs_paths(node_id: str, path: List[str], visited: Set[str]) -> None:
            if node_id in visited:
                return

            visited.add(node_id)
            path.append(node_id)

            node = self.risk_network[node_id]
            if not node.dependents:
                # End of path
                if len(path) >= 3:  # Only consider paths of length 3+
                    critical_paths.append(path.copy())
            else:
                for dependent in node.dependents:
                    dfs_paths(dependent, path, visited.copy())

            path.pop()

        # Start DFS from nodes with no dependencies
        start_nodes = [
            node_id for node_id, node in self.risk_network.items()
            if not node.dependencies
        ]

        for start_node in start_nodes:
            dfs_paths(start_node, [], set())

        # Sort by path length and return top paths
        critical_paths.sort(key=len, reverse=True)
        return critical_paths[:10]

    async def _analyze_concentration_risks(self) -> Dict[str, Any]:
        """Analyze concentration risks in the network"""
        # TVL concentration
        total_tvl = sum(node.tvl for node in self.risk_network.values())
        tvl_by_type = defaultdict(float)

        for node in self.risk_network.values():
            tvl_by_type[node.node_type.value] += node.tvl

        tvl_concentration = {
            node_type: tvl / max(total_tvl, 1)
            for node_type, tvl in tvl_by_type.items()
        }

        # Risk concentration
        high_risk_nodes = [
            node for node in self.risk_network.values()
            if node.risk_score > 0.7
        ]

        risk_concentration = {
            'high_risk_node_count': len(high_risk_nodes),
            'high_risk_tvl_ratio': sum(node.tvl for node in high_risk_nodes) / max(total_tvl, 1)
        }

        return {
            'tvl_concentration': tvl_concentration,
            'risk_concentration': risk_concentration
        }

    async def _calculate_interconnectedness_metrics(self) -> Dict[str, float]:
        """Calculate interconnectedness metrics"""
        total_nodes = len(self.risk_network)
        total_edges = len(self.transmission_edges)

        # Network density
        max_possible_edges = total_nodes * (total_nodes - 1)
        density = total_edges / max(max_possible_edges, 1)

        # Average degree
        total_degree = sum(
            len(node.dependencies) + len(node.dependents)
            for node in self.risk_network.values()
        )
        avg_degree = total_degree / max(total_nodes, 1)

        # Clustering coefficient (simplified)
        clustering = await self._calculate_clustering_coefficient()

        return {
            'network_density': density,
            'average_degree': avg_degree,
            'clustering_coefficient': clustering
        }

    async def _calculate_clustering_coefficient(self) -> float:
        """Calculate network clustering coefficient"""
        # Simplified clustering calculation
        total_clustering = 0.0
        node_count = 0

        for node_id, node in self.risk_network.items():
            neighbors = set(node.dependencies + node.dependents)

            if len(neighbors) < 2:
                continue

            # Count edges between neighbors
            neighbor_edges = 0
            for neighbor1 in neighbors:
                for neighbor2 in neighbors:
                    if neighbor1 != neighbor2:
                        edge_key = f"{neighbor1}_{neighbor2}"
                        if edge_key in self.transmission_edges:
                            neighbor_edges += 1

            # Calculate local clustering coefficient
            max_neighbor_edges = len(neighbors) * (len(neighbors) - 1)
            local_clustering = neighbor_edges / max(max_neighbor_edges, 1)

            total_clustering += local_clustering
            node_count += 1

        return total_clustering / max(node_count, 1)

    async def stress_test_scenarios(
        self,
        scenarios: List[Dict[str, Any]]
    ) -> Dict[str, CascadeSimulationResult]:
        """Run multiple stress test scenarios"""
        results = {}

        for i, scenario in enumerate(scenarios):
            scenario_name = scenario.get('name', f'scenario_{i}')
            initial_shock = scenario['initial_shock']
            cascade_type = CascadeType(scenario.get('cascade_type', 'liquidity_crisis'))
            market_conditions = scenario.get('market_conditions', {})

            result = await self.simulate_cascade_scenario(
                initial_shock, cascade_type, market_conditions
            )
            results[scenario_name] = result

        return results

    def export_network_graph(self) -> Dict[str, Any]:
        """Export network graph for visualization"""
        nodes = []
        edges = []

        # Export nodes
        for node_id, node in self.risk_network.items():
            nodes.append({
                'id': node_id,
                'name': node.name,
                'type': node.node_type.value,
                'tvl': node.tvl,
                'risk_score': node.risk_score,
                'critical_threshold': node.critical_threshold
            })

        # Export edges
        for edge_key, edge in self.transmission_edges.items():
            edges.append({
                'source': edge.source_node,
                'target': edge.target_node,
                'transmission_probability': edge.transmission_probability,
                'impact_multiplier': edge.impact_multiplier,
                'edge_type': edge.edge_type
            })

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'export_timestamp': datetime.utcnow().isoformat()
            }
        }