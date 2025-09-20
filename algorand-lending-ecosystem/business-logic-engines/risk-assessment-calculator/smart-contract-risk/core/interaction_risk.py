"""
Smart Contract Interaction Risk Analysis
Analyzes contract interaction patterns and associated security risks
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml
import networkx as nx
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContractInteraction:
    """Single contract interaction"""
    source_contract: str
    target_contract: str
    interaction_type: str
    frequency: int
    gas_usage: int
    success_rate: float
    risk_score: float
    last_interaction: datetime

@dataclass
class InteractionPattern:
    """Contract interaction pattern analysis"""
    pattern_type: str
    pattern_description: str
    contracts_involved: List[str]
    interaction_frequency: float
    risk_level: str
    vulnerability_indicators: List[str]
    mitigation_recommendations: List[str]

@dataclass
class CallGraph:
    """Contract call graph analysis"""
    nodes: List[str]
    edges: List[ContractInteraction]
    max_call_depth: int
    circular_dependencies: List[List[str]]
    critical_paths: List[List[str]]
    complexity_score: float

@dataclass
class InteractionRiskAssessment:
    """Complete interaction risk assessment"""
    contract_interactions: List[ContractInteraction]
    interaction_patterns: List[InteractionPattern]
    call_graph: CallGraph
    cross_protocol_risks: Dict[str, float]
    atomicity_risks: Dict[str, float]
    timing_attack_risks: Dict[str, float]
    front_running_risks: Dict[str, float]
    overall_interaction_risk: float
    risk_level: str
    critical_interactions: List[str]
    recommendations: List[str]
    monitoring_alerts: List[str]
    timestamp: datetime

class InteractionRiskAnalyzer:
    """Analyzes smart contract interaction patterns and risks"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the interaction risk analyzer"""
        self.config = self._load_config(config_path)
        self.interaction_cache = {}

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    async def analyze_interaction_risks(self, contracts_data: Dict[str, Dict[str, Any]],
                                      interaction_history: Optional[List[Dict]] = None) -> InteractionRiskAssessment:
        """Analyze comprehensive interaction risks"""
        logger.info("Analyzing smart contract interaction risks...")

        # Build interaction graph
        contract_interactions = await self._build_interaction_graph(contracts_data, interaction_history)

        # Analyze interaction patterns
        interaction_patterns = await self._analyze_interaction_patterns(contract_interactions, contracts_data)

        # Build call graph
        call_graph = await self._build_call_graph(contract_interactions, contracts_data)

        # Analyze specific risk types
        cross_protocol_risks = await self._analyze_cross_protocol_risks(contract_interactions, contracts_data)
        atomicity_risks = await self._analyze_atomicity_risks(contract_interactions, contracts_data)
        timing_attack_risks = await self._analyze_timing_attack_risks(contract_interactions, contracts_data)
        front_running_risks = await self._analyze_front_running_risks(contract_interactions, contracts_data)

        # Calculate overall interaction risk
        overall_risk = self._calculate_overall_interaction_risk(
            interaction_patterns, call_graph, cross_protocol_risks,
            atomicity_risks, timing_attack_risks, front_running_risks
        )

        # Determine risk level
        risk_level = self._determine_interaction_risk_level(overall_risk)

        # Identify critical interactions
        critical_interactions = self._identify_critical_interactions(contract_interactions, interaction_patterns)

        # Generate recommendations
        recommendations = self._generate_interaction_recommendations(
            interaction_patterns, call_graph, critical_interactions, overall_risk
        )

        # Generate monitoring alerts
        monitoring_alerts = self._generate_monitoring_alerts(
            contract_interactions, interaction_patterns, critical_interactions
        )

        return InteractionRiskAssessment(
            contract_interactions=contract_interactions,
            interaction_patterns=interaction_patterns,
            call_graph=call_graph,
            cross_protocol_risks=cross_protocol_risks,
            atomicity_risks=atomicity_risks,
            timing_attack_risks=timing_attack_risks,
            front_running_risks=front_running_risks,
            overall_interaction_risk=overall_risk,
            risk_level=risk_level,
            critical_interactions=critical_interactions,
            recommendations=recommendations,
            monitoring_alerts=monitoring_alerts,
            timestamp=datetime.now()
        )

    async def _build_interaction_graph(self, contracts_data: Dict[str, Dict[str, Any]],
                                     interaction_history: Optional[List[Dict]] = None) -> List[ContractInteraction]:
        """Build contract interaction graph from data"""
        interactions = []

        # Use provided interaction history if available
        if interaction_history:
            for interaction_data in interaction_history:
                interaction = ContractInteraction(
                    source_contract=interaction_data.get('source'),
                    target_contract=interaction_data.get('target'),
                    interaction_type=interaction_data.get('type', 'direct_call'),
                    frequency=interaction_data.get('frequency', 1),
                    gas_usage=interaction_data.get('gas_usage', 50000),
                    success_rate=interaction_data.get('success_rate', 1.0),
                    risk_score=0.0,  # Will be calculated
                    last_interaction=datetime.fromisoformat(
                        interaction_data.get('last_interaction', datetime.now().isoformat())
                    )
                )
                interactions.append(interaction)

        # Generate interactions based on contract patterns and dependencies
        interactions.extend(await self._infer_interactions_from_contracts(contracts_data))

        # Calculate risk scores for all interactions
        for interaction in interactions:
            interaction.risk_score = self._calculate_interaction_risk_score(
                interaction, contracts_data
            )

        return interactions

    async def _infer_interactions_from_contracts(self, contracts_data: Dict[str, Dict[str, Any]]) -> List[ContractInteraction]:
        """Infer likely interactions from contract patterns"""
        interactions = []

        for source_id, source_data in contracts_data.items():
            source_category = self._determine_contract_category(source_data)
            source_functions = source_data.get('functions', [])

            for target_id, target_data in contracts_data.items():
                if source_id == target_id:
                    continue

                target_category = self._determine_contract_category(target_data)

                # Infer interactions based on categories and functions
                interaction_type = self._infer_interaction_type(
                    source_category, target_category, source_functions
                )

                if interaction_type:
                    # Estimate interaction frequency based on categories
                    frequency = self._estimate_interaction_frequency(source_category, target_category)

                    interaction = ContractInteraction(
                        source_contract=source_id,
                        target_contract=target_id,
                        interaction_type=interaction_type,
                        frequency=frequency,
                        gas_usage=self._estimate_gas_usage(interaction_type),
                        success_rate=0.98,  # Assume high success rate
                        risk_score=0.0,  # Will be calculated later
                        last_interaction=datetime.now() - timedelta(hours=1)
                    )
                    interactions.append(interaction)

        return interactions

    def _determine_contract_category(self, contract_data: Dict[str, Any]) -> str:
        """Determine contract category (same logic as contract_analyzer)"""
        functions = contract_data.get('functions', [])

        if any(func in functions for func in ['deposit', 'withdraw', 'borrow', 'repay', 'liquidate']):
            return 'core_protocol'
        elif any(func in functions for func in ['propose', 'vote', 'execute', 'delegate']):
            return 'governance'
        elif any(func in functions for func in ['transfer', 'mint', 'burn', 'approve']):
            return 'token_contracts'
        elif any(func in functions for func in ['update_price', 'get_price', 'validate_data']):
            return 'oracle_integration'
        elif any(func in functions for func in ['lock', 'unlock', 'validate_proof']):
            return 'bridge_contracts'
        elif any(func in functions for func in ['swap', 'add_liquidity', 'remove_liquidity']):
            return 'liquidity_pools'

        return 'core_protocol'

    def _infer_interaction_type(self, source_category: str, target_category: str,
                              source_functions: List[str]) -> Optional[str]:
        """Infer interaction type between contract categories"""
        # Core protocol interactions
        if source_category == 'core_protocol':
            if target_category == 'oracle_integration':
                return 'price_query'
            elif target_category == 'token_contracts':
                return 'token_transfer'
            elif target_category == 'governance':
                return 'parameter_query'

        # DEX interactions
        elif source_category == 'liquidity_pools':
            if target_category == 'oracle_integration':
                return 'price_query'
            elif target_category == 'token_contracts':
                return 'token_swap'

        # Governance interactions
        elif source_category == 'governance':
            if target_category == 'core_protocol':
                return 'parameter_update'
            elif target_category == 'token_contracts':
                return 'governance_action'

        # Bridge interactions
        elif source_category == 'bridge_contracts':
            if target_category == 'token_contracts':
                return 'bridge_transfer'
            elif target_category == 'oracle_integration':
                return 'validation_query'

        # Check for delegated calls in functions
        if 'delegated_call' in source_functions:
            return 'delegated_call'
        elif 'external_call' in source_functions:
            return 'external_call'

        return None

    def _estimate_interaction_frequency(self, source_category: str, target_category: str) -> int:
        """Estimate interaction frequency based on categories"""
        frequency_matrix = {
            ('core_protocol', 'oracle_integration'): 100,    # High frequency price queries
            ('core_protocol', 'token_contracts'): 50,        # Medium frequency transfers
            ('liquidity_pools', 'oracle_integration'): 200,  # Very high frequency
            ('liquidity_pools', 'token_contracts'): 150,     # High frequency swaps
            ('governance', 'core_protocol'): 5,              # Low frequency governance
            ('bridge_contracts', 'token_contracts'): 20,     # Medium-low frequency
        }

        return frequency_matrix.get((source_category, target_category), 10)

    def _estimate_gas_usage(self, interaction_type: str) -> int:
        """Estimate gas usage for interaction type"""
        gas_estimates = {
            'direct_call': 21000,
            'external_call': 35000,
            'delegated_call': 25000,
            'price_query': 15000,
            'token_transfer': 45000,
            'token_swap': 85000,
            'parameter_update': 55000,
            'governance_action': 75000,
            'bridge_transfer': 120000,
            'validation_query': 25000
        }

        return gas_estimates.get(interaction_type, 50000)

    def _calculate_interaction_risk_score(self, interaction: ContractInteraction,
                                        contracts_data: Dict[str, Dict[str, Any]]) -> float:
        """Calculate risk score for a single interaction"""
        base_risk = 0.3  # Base risk for any interaction

        # Interaction type risk multipliers
        type_risks = self.config.get('interaction_patterns', {})
        type_risk = type_risks.get(interaction.interaction_type, {}).get('risk_multiplier', 1.0)

        # Frequency risk (higher frequency = higher risk)
        frequency_risk = min(interaction.frequency / 1000, 0.5)  # Cap at 0.5

        # Success rate risk (lower success rate = higher risk)
        success_risk = (1.0 - interaction.success_rate) * 0.3

        # Gas usage risk (higher gas = higher complexity = higher risk)
        gas_risk = min(interaction.gas_usage / 200000, 0.3)  # Cap at 0.3

        # Contract category risk
        source_data = contracts_data.get(interaction.source_contract, {})
        target_data = contracts_data.get(interaction.target_contract, {})

        source_category = self._determine_contract_category(source_data)
        target_category = self._determine_contract_category(target_data)

        category_risk = self._calculate_category_interaction_risk(source_category, target_category)

        # Combine risks
        total_risk = (base_risk * type_risk) + frequency_risk + success_risk + gas_risk + category_risk

        return min(total_risk, 1.0)

    def _calculate_category_interaction_risk(self, source_category: str, target_category: str) -> float:
        """Calculate risk based on interacting contract categories"""
        # High-risk category combinations
        high_risk_combinations = [
            ('bridge_contracts', 'token_contracts'),
            ('governance', 'core_protocol'),
            ('core_protocol', 'oracle_integration')
        ]

        # Medium-risk combinations
        medium_risk_combinations = [
            ('liquidity_pools', 'token_contracts'),
            ('core_protocol', 'token_contracts')
        ]

        if (source_category, target_category) in high_risk_combinations:
            return 0.3
        elif (source_category, target_category) in medium_risk_combinations:
            return 0.2
        else:
            return 0.1

    async def _analyze_interaction_patterns(self, interactions: List[ContractInteraction],
                                          contracts_data: Dict[str, Dict[str, Any]]) -> List[InteractionPattern]:
        """Analyze interaction patterns for risk assessment"""
        patterns = []

        # Group interactions by type
        type_groups = {}
        for interaction in interactions:
            if interaction.interaction_type not in type_groups:
                type_groups[interaction.interaction_type] = []
            type_groups[interaction.interaction_type].append(interaction)

        # Analyze each interaction type pattern
        for interaction_type, type_interactions in type_groups.items():
            pattern = await self._analyze_single_pattern(interaction_type, type_interactions, contracts_data)
            patterns.append(pattern)

        # Detect complex patterns
        complex_patterns = await self._detect_complex_patterns(interactions, contracts_data)
        patterns.extend(complex_patterns)

        return patterns

    async def _analyze_single_pattern(self, interaction_type: str,
                                    interactions: List[ContractInteraction],
                                    contracts_data: Dict[str, Dict[str, Any]]) -> InteractionPattern:
        """Analyze a single interaction pattern"""
        contracts_involved = list(set(
            [inter.source_contract for inter in interactions] +
            [inter.target_contract for inter in interactions]
        ))

        avg_frequency = sum(inter.frequency for inter in interactions) / len(interactions)
        avg_risk = sum(inter.risk_score for inter in interactions) / len(interactions)

        # Determine risk level
        if avg_risk >= 0.7:
            risk_level = "HIGH"
        elif avg_risk >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Identify vulnerability indicators
        vulnerability_indicators = self._identify_pattern_vulnerabilities(interaction_type, interactions)

        # Generate mitigation recommendations
        mitigation_recommendations = self._generate_pattern_mitigations(interaction_type, vulnerability_indicators)

        return InteractionPattern(
            pattern_type=interaction_type,
            pattern_description=self._get_pattern_description(interaction_type),
            contracts_involved=contracts_involved,
            interaction_frequency=avg_frequency,
            risk_level=risk_level,
            vulnerability_indicators=vulnerability_indicators,
            mitigation_recommendations=mitigation_recommendations
        )

    def _get_pattern_description(self, interaction_type: str) -> str:
        """Get description for interaction pattern type"""
        descriptions = {
            'direct_call': 'Direct function calls between contracts',
            'external_call': 'External calls to other contracts',
            'delegated_call': 'Delegated calls with shared storage context',
            'price_query': 'Price oracle queries for market data',
            'token_transfer': 'Token transfer operations',
            'token_swap': 'Token swap transactions',
            'parameter_update': 'Protocol parameter updates',
            'governance_action': 'Governance-related actions',
            'bridge_transfer': 'Cross-chain bridge transfers',
            'validation_query': 'Data validation queries'
        }

        return descriptions.get(interaction_type, f'Pattern type: {interaction_type}')

    def _identify_pattern_vulnerabilities(self, interaction_type: str,
                                        interactions: List[ContractInteraction]) -> List[str]:
        """Identify vulnerability indicators for interaction pattern"""
        vulnerabilities = []

        # Type-specific vulnerabilities
        if interaction_type == 'delegated_call':
            vulnerabilities.append('Storage collision risk')
            vulnerabilities.append('Implementation contract vulnerabilities')

        elif interaction_type == 'external_call':
            vulnerabilities.append('Reentrancy attack risk')
            vulnerabilities.append('Gas griefing potential')

        elif interaction_type == 'price_query':
            vulnerabilities.append('Oracle manipulation risk')
            vulnerabilities.append('Price staleness issues')

        elif interaction_type == 'bridge_transfer':
            vulnerabilities.append('Cross-chain validation risk')
            vulnerabilities.append('Asset locking vulnerabilities')

        # Frequency-based vulnerabilities
        high_frequency_interactions = [inter for inter in interactions if inter.frequency > 100]
        if high_frequency_interactions:
            vulnerabilities.append('High frequency attack vectors')

        # Success rate vulnerabilities
        low_success_interactions = [inter for inter in interactions if inter.success_rate < 0.95]
        if low_success_interactions:
            vulnerabilities.append('Transaction failure exploitation')

        return vulnerabilities

    def _generate_pattern_mitigations(self, interaction_type: str,
                                    vulnerabilities: List[str]) -> List[str]:
        """Generate mitigation recommendations for pattern vulnerabilities"""
        mitigations = []

        if 'Storage collision risk' in vulnerabilities:
            mitigations.append('Implement storage layout validation')

        if 'Reentrancy attack risk' in vulnerabilities:
            mitigations.append('Use reentrancy guards on all external calls')

        if 'Oracle manipulation risk' in vulnerabilities:
            mitigations.append('Implement multiple oracle sources and price deviation checks')

        if 'Cross-chain validation risk' in vulnerabilities:
            mitigations.append('Require multiple validator confirmations')

        if 'High frequency attack vectors' in vulnerabilities:
            mitigations.append('Implement rate limiting and gas price thresholds')

        if 'Gas griefing potential' in vulnerabilities:
            mitigations.append('Set gas limits and implement proper error handling')

        # General mitigations
        mitigations.append('Regular security audits of interaction patterns')
        mitigations.append('Implement comprehensive event logging')

        return mitigations

    async def _detect_complex_patterns(self, interactions: List[ContractInteraction],
                                     contracts_data: Dict[str, Dict[str, Any]]) -> List[InteractionPattern]:
        """Detect complex interaction patterns"""
        complex_patterns = []

        # Detect circular dependencies
        circular_patterns = self._detect_circular_patterns(interactions)
        complex_patterns.extend(circular_patterns)

        # Detect flash loan patterns
        flash_loan_patterns = self._detect_flash_loan_patterns(interactions)
        complex_patterns.extend(flash_loan_patterns)

        # Detect arbitrage patterns
        arbitrage_patterns = self._detect_arbitrage_patterns(interactions)
        complex_patterns.extend(arbitrage_patterns)

        return complex_patterns

    def _detect_circular_patterns(self, interactions: List[ContractInteraction]) -> List[InteractionPattern]:
        """Detect circular dependency patterns"""
        patterns = []

        # Build directed graph
        graph = {}
        for interaction in interactions:
            if interaction.source_contract not in graph:
                graph[interaction.source_contract] = []
            graph[interaction.source_contract].append(interaction.target_contract)

        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [neighbor])

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [node])

        # Create pattern for each cycle
        for cycle in cycles:
            if len(cycle) > 2:  # Only consider meaningful cycles
                pattern = InteractionPattern(
                    pattern_type='circular_dependency',
                    pattern_description=f'Circular dependency involving {len(cycle)} contracts',
                    contracts_involved=cycle,
                    interaction_frequency=50,  # Estimated
                    risk_level='HIGH',
                    vulnerability_indicators=['Dependency loop risk', 'Recursive call vulnerability'],
                    mitigation_recommendations=[
                        'Break circular dependencies where possible',
                        'Implement call depth limits',
                        'Add circuit breakers for recursive patterns'
                    ]
                )
                patterns.append(pattern)

        return patterns

    def _detect_flash_loan_patterns(self, interactions: List[ContractInteraction]) -> List[InteractionPattern]:
        """Detect flash loan interaction patterns"""
        patterns = []

        # Look for high-frequency, high-value interactions that could be flash loans
        flash_loan_candidates = []

        for interaction in interactions:
            # Flash loans typically have high frequency and involve lending protocols
            if (interaction.frequency > 50 and
                interaction.gas_usage > 100000 and
                interaction.interaction_type in ['external_call', 'token_transfer']):
                flash_loan_candidates.append(interaction)

        if flash_loan_candidates:
            contracts_involved = list(set(
                [inter.source_contract for inter in flash_loan_candidates] +
                [inter.target_contract for inter in flash_loan_candidates]
            ))

            pattern = InteractionPattern(
                pattern_type='flash_loan_pattern',
                pattern_description='High-frequency lending/borrowing pattern indicative of flash loans',
                contracts_involved=contracts_involved,
                interaction_frequency=sum(inter.frequency for inter in flash_loan_candidates),
                risk_level='HIGH',
                vulnerability_indicators=[
                    'Flash loan attack vectors',
                    'Price manipulation opportunities',
                    'Liquidity drainage risk'
                ],
                mitigation_recommendations=[
                    'Implement flash loan detection and rate limiting',
                    'Use time-weighted average prices',
                    'Require minimum holding periods for certain actions'
                ]
            )
            patterns.append(pattern)

        return patterns

    def _detect_arbitrage_patterns(self, interactions: List[ContractInteraction]) -> List[InteractionPattern]:
        """Detect arbitrage interaction patterns"""
        patterns = []

        # Look for rapid swap patterns across multiple DEXs
        swap_interactions = [inter for inter in interactions if inter.interaction_type == 'token_swap']

        if len(swap_interactions) >= 3:  # Minimum for triangular arbitrage
            pattern = InteractionPattern(
                pattern_type='arbitrage_pattern',
                pattern_description='Multi-DEX swap pattern indicative of arbitrage activity',
                contracts_involved=list(set(
                    [inter.source_contract for inter in swap_interactions] +
                    [inter.target_contract for inter in swap_interactions]
                )),
                interaction_frequency=sum(inter.frequency for inter in swap_interactions),
                risk_level='MEDIUM',
                vulnerability_indicators=[
                    'MEV extraction opportunities',
                    'Front-running vulnerabilities',
                    'Slippage manipulation'
                ],
                mitigation_recommendations=[
                    'Implement commit-reveal schemes',
                    'Use fair ordering mechanisms',
                    'Add slippage protection'
                ]
            )
            patterns.append(pattern)

        return patterns

    async def _build_call_graph(self, interactions: List[ContractInteraction],
                              contracts_data: Dict[str, Dict[str, Any]]) -> CallGraph:
        """Build contract call graph for analysis"""
        # Create nodes and edges
        nodes = list(set(
            [inter.source_contract for inter in interactions] +
            [inter.target_contract for inter in interactions]
        ))

        edges = interactions

        # Calculate maximum call depth
        max_depth = self._calculate_max_call_depth(interactions)

        # Find circular dependencies
        circular_deps = self._find_circular_dependencies(interactions)

        # Identify critical paths
        critical_paths = self._identify_critical_paths(interactions, contracts_data)

        # Calculate complexity score
        complexity_score = self._calculate_graph_complexity(nodes, edges, max_depth, circular_deps)

        return CallGraph(
            nodes=nodes,
            edges=edges,
            max_call_depth=max_depth,
            circular_dependencies=circular_deps,
            critical_paths=critical_paths,
            complexity_score=complexity_score
        )

    def _calculate_max_call_depth(self, interactions: List[ContractInteraction]) -> int:
        """Calculate maximum call depth in interaction graph"""
        # Build adjacency list
        graph = {}
        for interaction in interactions:
            if interaction.source_contract not in graph:
                graph[interaction.source_contract] = []
            graph[interaction.source_contract].append(interaction.target_contract)

        max_depth = 0

        def dfs_depth(node, depth, visited):
            nonlocal max_depth
            if node in visited:
                return depth

            visited.add(node)
            max_depth = max(max_depth, depth)

            for neighbor in graph.get(node, []):
                dfs_depth(neighbor, depth + 1, visited.copy())

        for node in graph:
            dfs_depth(node, 1, set())

        return max_depth

    def _find_circular_dependencies(self, interactions: List[ContractInteraction]) -> List[List[str]]:
        """Find circular dependencies in interaction graph"""
        # Use networkx for cycle detection
        G = nx.DiGraph()

        for interaction in interactions:
            G.add_edge(interaction.source_contract, interaction.target_contract)

        try:
            cycles = list(nx.simple_cycles(G))
            return cycles
        except Exception:
            return []

    def _identify_critical_paths(self, interactions: List[ContractInteraction],
                               contracts_data: Dict[str, Dict[str, Any]]) -> List[List[str]]:
        """Identify critical paths in interaction graph"""
        critical_paths = []

        # Identify high-risk contract categories
        high_risk_categories = ['bridge_contracts', 'oracle_integration', 'governance']

        # Find paths involving high-risk contracts
        high_risk_contracts = []
        for contract_id, contract_data in contracts_data.items():
            category = self._determine_contract_category(contract_data)
            if category in high_risk_categories:
                high_risk_contracts.append(contract_id)

        # Build graph for path finding
        graph = {}
        for interaction in interactions:
            if interaction.source_contract not in graph:
                graph[interaction.source_contract] = []
            graph[interaction.source_contract].append(interaction.target_contract)

        # Find paths between high-risk contracts
        for source in high_risk_contracts:
            for target in high_risk_contracts:
                if source != target:
                    path = self._find_shortest_path(graph, source, target)
                    if path and len(path) <= 4:  # Only consider short critical paths
                        critical_paths.append(path)

        return critical_paths[:10]  # Limit to top 10 critical paths

    def _find_shortest_path(self, graph: Dict[str, List[str]], start: str, end: str) -> Optional[List[str]]:
        """Find shortest path between two nodes"""
        if start == end:
            return [start]

        visited = set()
        queue = [(start, [start])]

        while queue:
            node, path = queue.pop(0)
            if node in visited:
                continue

            visited.add(node)

            for neighbor in graph.get(node, []):
                if neighbor == end:
                    return path + [neighbor]
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return None

    def _calculate_graph_complexity(self, nodes: List[str], edges: List[ContractInteraction],
                                  max_depth: int, circular_deps: List[List[str]]) -> float:
        """Calculate overall graph complexity score"""
        # Node complexity (0-0.3)
        node_score = min(len(nodes) / 20, 0.3)  # 20+ nodes = max node complexity

        # Edge complexity (0-0.3)
        edge_score = min(len(edges) / 50, 0.3)  # 50+ edges = max edge complexity

        # Depth complexity (0-0.2)
        depth_score = min(max_depth / 10, 0.2)  # Depth 10+ = max depth complexity

        # Circular dependency complexity (0-0.2)
        circular_score = min(len(circular_deps) / 5, 0.2)  # 5+ cycles = max circular complexity

        total_complexity = node_score + edge_score + depth_score + circular_score

        return min(total_complexity, 1.0)

    async def _analyze_cross_protocol_risks(self, interactions: List[ContractInteraction],
                                          contracts_data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Analyze cross-protocol interaction risks"""
        risks = {}

        # Group interactions by protocol pairs
        protocol_pairs = {}
        for interaction in interactions:
            source_protocol = self._get_contract_protocol(interaction.source_contract, contracts_data)
            target_protocol = self._get_contract_protocol(interaction.target_contract, contracts_data)

            if source_protocol != target_protocol:
                pair_key = f"{source_protocol}_{target_protocol}"
                if pair_key not in protocol_pairs:
                    protocol_pairs[pair_key] = []
                protocol_pairs[pair_key].append(interaction)

        # Calculate risk for each protocol pair
        for pair_key, pair_interactions in protocol_pairs.items():
            avg_risk = sum(inter.risk_score for inter in pair_interactions) / len(pair_interactions)
            frequency_risk = sum(inter.frequency for inter in pair_interactions) / 1000  # Normalize
            risks[pair_key] = min(avg_risk + frequency_risk, 1.0)

        return risks

    def _get_contract_protocol(self, contract_id: str, contracts_data: Dict[str, Dict[str, Any]]) -> str:
        """Get protocol name for a contract"""
        # Extract protocol from contract name or use contract ID
        if 'algofi' in contract_id.lower():
            return 'algofi'
        elif 'folks' in contract_id.lower():
            return 'folks_finance'
        elif 'tinyman' in contract_id.lower():
            return 'tinyman'
        elif 'pact' in contract_id.lower():
            return 'pact'
        else:
            return contract_id.split('_')[0] if '_' in contract_id else contract_id

    async def _analyze_atomicity_risks(self, interactions: List[ContractInteraction],
                                     contracts_data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Analyze atomicity and transaction ordering risks"""
        risks = {}

        # Group interactions that might be part of atomic transactions
        atomic_groups = self._identify_atomic_groups(interactions)

        for group_id, group_interactions in atomic_groups.items():
            # Calculate atomicity risk based on group complexity and failure probability
            group_complexity = len(group_interactions)
            avg_success_rate = sum(inter.success_rate for inter in group_interactions) / len(group_interactions)

            # Risk increases with complexity and decreases with success rate
            complexity_risk = min(group_complexity / 10, 0.7)  # Cap at 0.7
            failure_risk = (1.0 - avg_success_rate) * 0.5

            risks[group_id] = min(complexity_risk + failure_risk, 1.0)

        return risks

    def _identify_atomic_groups(self, interactions: List[ContractInteraction]) -> Dict[str, List[ContractInteraction]]:
        """Identify groups of interactions that should be atomic"""
        groups = {}

        # Group by interaction patterns that suggest atomicity
        for interaction in interactions:
            # Flash loan patterns
            if interaction.interaction_type in ['token_transfer', 'token_swap']:
                group_key = f"atomic_swap_{interaction.source_contract}"
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(interaction)

            # Liquidation patterns
            elif interaction.interaction_type in ['external_call'] and interaction.frequency > 20:
                group_key = f"liquidation_{interaction.target_contract}"
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(interaction)

        return groups

    async def _analyze_timing_attack_risks(self, interactions: List[ContractInteraction],
                                         contracts_data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Analyze timing attack and MEV risks"""
        risks = {}

        # Identify time-sensitive interactions
        for interaction in interactions:
            source_category = self._determine_contract_category(
                contracts_data.get(interaction.source_contract, {})
            )
            target_category = self._determine_contract_category(
                contracts_data.get(interaction.target_contract, {})
            )

            risk_key = f"{interaction.source_contract}_{interaction.target_contract}"

            # Oracle price queries are vulnerable to timing attacks
            if interaction.interaction_type == 'price_query':
                risks[risk_key] = 0.6

            # DEX interactions vulnerable to sandwich attacks
            elif interaction.interaction_type == 'token_swap':
                risks[risk_key] = 0.7

            # Liquidation calls vulnerable to front-running
            elif source_category == 'core_protocol' and interaction.frequency > 10:
                risks[risk_key] = 0.5

            # High-frequency interactions more vulnerable
            elif interaction.frequency > 100:
                risks[risk_key] = 0.4

        return risks

    async def _analyze_front_running_risks(self, interactions: List[ContractInteraction],
                                         contracts_data: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Analyze front-running and MEV extraction risks"""
        risks = {}

        for interaction in interactions:
            risk_key = f"{interaction.source_contract}_{interaction.target_contract}"

            # High-value interactions are attractive for front-running
            if interaction.gas_usage > 100000:  # High gas = high value
                base_risk = 0.6
            elif interaction.gas_usage > 50000:
                base_risk = 0.4
            else:
                base_risk = 0.2

            # Frequency multiplier (more frequent = more opportunities)
            frequency_multiplier = min(1 + (interaction.frequency / 1000), 2.0)

            # Success rate consideration (failed txs are less attractive)
            success_multiplier = interaction.success_rate

            risks[risk_key] = min(base_risk * frequency_multiplier * success_multiplier, 1.0)

        return risks

    def _calculate_overall_interaction_risk(self, patterns: List[InteractionPattern],
                                          call_graph: CallGraph,
                                          cross_protocol_risks: Dict[str, float],
                                          atomicity_risks: Dict[str, float],
                                          timing_attack_risks: Dict[str, float],
                                          front_running_risks: Dict[str, float]) -> float:
        """Calculate overall interaction risk score"""
        # Pattern risk component
        if patterns:
            high_risk_patterns = [p for p in patterns if p.risk_level == 'HIGH']
            pattern_risk = min(len(high_risk_patterns) / len(patterns), 1.0)
        else:
            pattern_risk = 0.0

        # Graph complexity risk
        complexity_risk = call_graph.complexity_score

        # Cross-protocol risk
        cross_protocol_risk = max(cross_protocol_risks.values()) if cross_protocol_risks else 0.0

        # Specific attack risks
        atomicity_risk = max(atomicity_risks.values()) if atomicity_risks else 0.0
        timing_risk = max(timing_attack_risks.values()) if timing_attack_risks else 0.0
        front_running_risk = max(front_running_risks.values()) if front_running_risks else 0.0

        # Weighted combination
        weights = {
            'patterns': 0.25,
            'complexity': 0.2,
            'cross_protocol': 0.15,
            'atomicity': 0.15,
            'timing': 0.15,
            'front_running': 0.1
        }

        overall_risk = (
            pattern_risk * weights['patterns'] +
            complexity_risk * weights['complexity'] +
            cross_protocol_risk * weights['cross_protocol'] +
            atomicity_risk * weights['atomicity'] +
            timing_risk * weights['timing'] +
            front_running_risk * weights['front_running']
        )

        return min(overall_risk, 1.0)

    def _determine_interaction_risk_level(self, risk_score: float) -> str:
        """Determine interaction risk level"""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MODERATE"
        elif risk_score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"

    def _identify_critical_interactions(self, interactions: List[ContractInteraction],
                                      patterns: List[InteractionPattern]) -> List[str]:
        """Identify critical interactions requiring monitoring"""
        critical = []

        # High-risk interactions
        for interaction in interactions:
            if interaction.risk_score >= 0.7:
                critical.append(f"{interaction.source_contract} -> {interaction.target_contract}")

        # High-risk patterns
        for pattern in patterns:
            if pattern.risk_level == 'HIGH':
                for contract in pattern.contracts_involved:
                    if contract not in critical:
                        critical.append(contract)

        return critical[:10]  # Limit to top 10

    def _generate_interaction_recommendations(self, patterns: List[InteractionPattern],
                                            call_graph: CallGraph,
                                            critical_interactions: List[str],
                                            overall_risk: float) -> List[str]:
        """Generate interaction risk mitigation recommendations"""
        recommendations = []

        # High-level recommendations based on overall risk
        if overall_risk >= 0.7:
            recommendations.append("URGENT: Implement comprehensive interaction monitoring and circuit breakers")

        # Pattern-specific recommendations
        high_risk_patterns = [p for p in patterns if p.risk_level == 'HIGH']
        for pattern in high_risk_patterns[:3]:  # Top 3 high-risk patterns
            recommendations.extend(pattern.mitigation_recommendations[:2])  # Top 2 mitigations

        # Graph complexity recommendations
        if call_graph.complexity_score >= 0.7:
            recommendations.append("Simplify contract interaction patterns to reduce complexity")

        if call_graph.circular_dependencies:
            recommendations.append("Break circular dependencies to prevent recursive vulnerabilities")

        if call_graph.max_call_depth >= 5:
            recommendations.append("Implement call depth limits to prevent deep recursion attacks")

        # Critical interaction recommendations
        if critical_interactions:
            recommendations.append(f"Monitor critical interactions: {', '.join(critical_interactions[:3])}")

        return recommendations[:6]  # Limit to top 6 recommendations

    def _generate_monitoring_alerts(self, interactions: List[ContractInteraction],
                                  patterns: List[InteractionPattern],
                                  critical_interactions: List[str]) -> List[str]:
        """Generate monitoring alert configurations"""
        alerts = []

        # High-frequency interaction alerts
        high_freq_interactions = [inter for inter in interactions if inter.frequency > 100]
        if high_freq_interactions:
            alerts.append("Monitor high-frequency interactions for abuse patterns")

        # Low success rate alerts
        low_success_interactions = [inter for inter in interactions if inter.success_rate < 0.9]
        if low_success_interactions:
            alerts.append("Alert on low success rate interactions indicating potential attacks")

        # Pattern-specific alerts
        for pattern in patterns:
            if pattern.risk_level == 'HIGH':
                alerts.append(f"Monitor {pattern.pattern_type} patterns for anomalous behavior")

        # Critical interaction alerts
        for critical in critical_interactions[:3]:
            alerts.append(f"Real-time monitoring for: {critical}")

        return alerts

# Example usage
async def main():
    """Example usage of the interaction risk analyzer"""
    analyzer = InteractionRiskAnalyzer()

    # Example contracts data
    contracts_data = {
        'algofi_pool': {
            'name': 'AlgoFi Lending Pool',
            'functions': ['deposit', 'withdraw', 'borrow', 'repay', 'external_call'],
            'features': ['access_control', 'reentrancy_protection']
        },
        'tinyman_dex': {
            'name': 'Tinyman DEX',
            'functions': ['swap', 'add_liquidity', 'remove_liquidity', 'external_call'],
            'features': ['slippage_protection', 'access_control']
        },
        'oracle_contract': {
            'name': 'Price Oracle',
            'functions': ['update_price', 'get_price', 'validate_data'],
            'features': ['access_control', 'staleness_check']
        }
    }

    # Example interaction history
    interaction_history = [
        {
            'source': 'algofi_pool',
            'target': 'oracle_contract',
            'type': 'price_query',
            'frequency': 150,
            'gas_usage': 25000,
            'success_rate': 0.98,
            'last_interaction': '2024-01-15T10:30:00'
        },
        {
            'source': 'tinyman_dex',
            'target': 'oracle_contract',
            'type': 'price_query',
            'frequency': 200,
            'gas_usage': 20000,
            'success_rate': 0.99,
            'last_interaction': '2024-01-15T10:25:00'
        }
    ]

    # Analyze interaction risks
    risk_assessment = await analyzer.analyze_interaction_risks(contracts_data, interaction_history)

    print(f"\n=== Smart Contract Interaction Risk Analysis ===")
    print(f"Overall Interaction Risk: {risk_assessment.overall_interaction_risk:.2f}")
    print(f"Risk Level: {risk_assessment.risk_level}")

    print(f"\n=== Contract Interactions ===")
    for interaction in risk_assessment.contract_interactions:
        print(f"{interaction.source_contract} -> {interaction.target_contract}")
        print(f"  Type: {interaction.interaction_type}")
        print(f"  Frequency: {interaction.frequency}")
        print(f"  Risk Score: {interaction.risk_score:.2f}")

    print(f"\n=== Interaction Patterns ===")
    for pattern in risk_assessment.interaction_patterns:
        print(f"Pattern: {pattern.pattern_type} ({pattern.risk_level})")
        print(f"  Description: {pattern.pattern_description}")
        print(f"  Contracts: {len(pattern.contracts_involved)}")
        print(f"  Vulnerabilities: {', '.join(pattern.vulnerability_indicators[:2])}")

    print(f"\n=== Call Graph Analysis ===")
    graph = risk_assessment.call_graph
    print(f"Nodes: {len(graph.nodes)}")
    print(f"Edges: {len(graph.edges)}")
    print(f"Max Call Depth: {graph.max_call_depth}")
    print(f"Circular Dependencies: {len(graph.circular_dependencies)}")
    print(f"Complexity Score: {graph.complexity_score:.2f}")

    print(f"\n=== Critical Interactions ===")
    for critical in risk_assessment.critical_interactions:
        print(f"• {critical}")

    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(risk_assessment.recommendations, 1):
        print(f"{i}. {rec}")

    print(f"\n=== Monitoring Alerts ===")
    for alert in risk_assessment.monitoring_alerts:
        print(f"⚠️  {alert}")

if __name__ == "__main__":
    asyncio.run(main())