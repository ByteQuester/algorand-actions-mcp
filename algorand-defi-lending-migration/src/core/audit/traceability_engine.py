"""
Decision Traceability Engine
Complete decision traceability and explanation system for lending decisions
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import hashlib
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class DecisionType(Enum):
    """Types of decisions that can be traced"""
    LOAN_APPROVAL = "loan_approval"
    INTEREST_RATE = "interest_rate"
    COLLATERAL_REQUIREMENT = "collateral_requirement"
    LOAN_TERMS = "loan_terms"
    RISK_ASSESSMENT = "risk_assessment"
    LIQUIDATION = "liquidation"
    COLLATERAL_RELEASE = "collateral_release"

class ConfidenceLevel(Enum):
    """Confidence levels for decision factors"""
    CRITICAL = "critical"      # 90-100% impact
    HIGH = "high"             # 70-89% impact
    MEDIUM = "medium"         # 40-69% impact
    LOW = "low"              # 10-39% impact
    MINIMAL = "minimal"       # 0-9% impact

@dataclass
class DataPoint:
    """Individual data point used in a decision"""
    key: str
    value: Any
    source: str                    # Where the data came from
    timestamp: datetime
    confidence: float              # 0.0-1.0 confidence in data accuracy
    impact_score: float           # 0.0-1.0 impact on decision
    validation_status: str        # 'validated', 'unverified', 'flagged'
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionFactor:
    """Factor that influenced a decision"""
    factor_id: str
    name: str
    weight: float                 # 0.0-1.0 weight in final decision
    confidence: ConfidenceLevel
    data_points: List[DataPoint]
    reasoning: str
    alternative_impact: Dict[str, float] = field(default_factory=dict)

@dataclass
class DecisionNode:
    """Node in the decision tree"""
    node_id: str
    decision_type: DecisionType
    timestamp: datetime
    input_data: Dict[str, Any]
    output_decision: Dict[str, Any]
    factors: List[DecisionFactor]
    reasoning_chain: List[str]
    confidence_score: float
    alternatives_considered: List[Dict[str, Any]] = field(default_factory=list)
    parent_nodes: List[str] = field(default_factory=list)
    child_nodes: List[str] = field(default_factory=list)
    agent_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionTrace:
    """Complete trace of a decision process"""
    trace_id: str
    loan_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    nodes: Dict[str, DecisionNode]
    root_decisions: List[str]
    final_outcome: Dict[str, Any]
    completeness_score: float    # 0.0-1.0 how complete the trace is
    consistency_score: float     # 0.0-1.0 internal consistency
    audit_flags: List[str] = field(default_factory=list)

class TraceabilityEngine:
    """
    Main engine for decision traceability and explanation
    Tracks every decision made in the lending process
    """

    def __init__(self):
        """Initialize the traceability engine"""
        self.active_traces: Dict[str, DecisionTrace] = {}
        self.completed_traces: Dict[str, DecisionTrace] = {}
        self.decision_patterns: Dict[str, List[str]] = defaultdict(list)
        self.validation_rules: List[Any] = []

    async def start_decision_trace(
        self,
        loan_id: str,
        session_id: str,
        initial_context: Dict[str, Any]
    ) -> str:
        """
        Start tracing decisions for a loan application

        Args:
            loan_id: Unique loan identifier
            session_id: ADK session identifier
            initial_context: Initial context data

        Returns:
            trace_id: Unique trace identifier
        """
        trace_id = f"trace_{loan_id}_{uuid.uuid4().hex[:8]}"

        trace = DecisionTrace(
            trace_id=trace_id,
            loan_id=loan_id,
            session_id=session_id,
            start_time=datetime.utcnow(),
            end_time=None,
            nodes={},
            root_decisions=[],
            final_outcome={},
            completeness_score=0.0,
            consistency_score=0.0
        )

        # Add initial context as root data
        if initial_context:
            await self._capture_initial_context(trace, initial_context)

        self.active_traces[trace_id] = trace
        logger.info(f"Started decision trace {trace_id} for loan {loan_id}")

        return trace_id

    async def record_decision(
        self,
        trace_id: str,
        decision_type: DecisionType,
        input_data: Dict[str, Any],
        output_decision: Dict[str, Any],
        reasoning_chain: List[str],
        factors: List[DecisionFactor],
        agent_context: Dict[str, Any] = None
    ) -> str:
        """
        Record a decision in the trace

        Args:
            trace_id: Trace identifier
            decision_type: Type of decision being made
            input_data: Input data used for decision
            output_decision: The decision that was made
            reasoning_chain: Step-by-step reasoning
            factors: Factors that influenced the decision
            agent_context: Context about the agent making the decision

        Returns:
            node_id: Identifier for the decision node
        """
        if trace_id not in self.active_traces:
            raise ValueError(f"No active trace found for {trace_id}")

        trace = self.active_traces[trace_id]
        node_id = f"node_{len(trace.nodes)}_{uuid.uuid4().hex[:6]}"

        # Calculate confidence score from factors
        confidence_score = self._calculate_confidence_score(factors)

        # Create decision node
        node = DecisionNode(
            node_id=node_id,
            decision_type=decision_type,
            timestamp=datetime.utcnow(),
            input_data=input_data.copy(),
            output_decision=output_decision.copy(),
            factors=factors,
            reasoning_chain=reasoning_chain.copy(),
            confidence_score=confidence_score,
            agent_context=agent_context or {}
        )

        # Add alternatives if available in reasoning
        node.alternatives_considered = self._extract_alternatives(reasoning_chain, output_decision)

        # Store the node
        trace.nodes[node_id] = node

        # Update decision patterns
        pattern_key = f"{decision_type.value}_{len(factors)}"
        self.decision_patterns[pattern_key].append(node_id)

        logger.info(f"Recorded decision {node_id} of type {decision_type.value} in trace {trace_id}")

        return node_id

    async def link_decisions(
        self,
        trace_id: str,
        parent_node_id: str,
        child_node_id: str
    ):
        """
        Link parent and child decisions to build decision tree

        Args:
            trace_id: Trace identifier
            parent_node_id: Parent decision node
            child_node_id: Child decision node
        """
        if trace_id not in self.active_traces:
            raise ValueError(f"No active trace found for {trace_id}")

        trace = self.active_traces[trace_id]

        if parent_node_id in trace.nodes and child_node_id in trace.nodes:
            trace.nodes[parent_node_id].child_nodes.append(child_node_id)
            trace.nodes[child_node_id].parent_nodes.append(parent_node_id)

            logger.debug(f"Linked decisions {parent_node_id} -> {child_node_id} in trace {trace_id}")

    async def complete_trace(
        self,
        trace_id: str,
        final_outcome: Dict[str, Any]
    ) -> DecisionTrace:
        """
        Complete a decision trace and perform validation

        Args:
            trace_id: Trace identifier
            final_outcome: Final outcome of the lending decision

        Returns:
            Completed trace with validation scores
        """
        if trace_id not in self.active_traces:
            raise ValueError(f"No active trace found for {trace_id}")

        trace = self.active_traces[trace_id]
        trace.end_time = datetime.utcnow()
        trace.final_outcome = final_outcome.copy()

        # Identify root decisions (nodes with no parents)
        trace.root_decisions = [
            node_id for node_id, node in trace.nodes.items()
            if not node.parent_nodes
        ]

        # Calculate completeness and consistency scores
        trace.completeness_score = await self._calculate_completeness(trace)
        trace.consistency_score = await self._calculate_consistency(trace)

        # Run validation checks
        trace.audit_flags = await self._validate_trace(trace)

        # Move to completed traces
        self.completed_traces[trace_id] = trace
        del self.active_traces[trace_id]

        logger.info(
            f"Completed trace {trace_id} - "
            f"Completeness: {trace.completeness_score:.2f}, "
            f"Consistency: {trace.consistency_score:.2f}, "
            f"Flags: {len(trace.audit_flags)}"
        )

        return trace

    async def get_decision_explanation(
        self,
        loan_id: str,
        decision_type: Optional[DecisionType] = None,
        simplified: bool = False
    ) -> Dict[str, Any]:
        """
        Generate explanation for a loan's decisions

        Args:
            loan_id: Loan identifier
            decision_type: Specific decision type to explain (optional)
            simplified: Whether to generate simplified explanation

        Returns:
            Explanation dictionary
        """
        # Find trace for loan
        trace = self._find_trace_by_loan(loan_id)
        if not trace:
            return {
                "error": f"No decision trace found for loan {loan_id}",
                "explanation": "Unable to provide explanation - decision trace not available"
            }

        # Filter nodes by decision type if specified
        relevant_nodes = []
        if decision_type:
            relevant_nodes = [
                node for node in trace.nodes.values()
                if node.decision_type == decision_type
            ]
        else:
            relevant_nodes = list(trace.nodes.values())

        if not relevant_nodes:
            return {
                "error": f"No decisions of type {decision_type} found for loan {loan_id}",
                "explanation": "No matching decisions found"
            }

        # Generate explanation
        explanation = await self._generate_explanation(
            trace, relevant_nodes, simplified
        )

        return explanation

    async def find_similar_decisions(
        self,
        loan_id: str,
        similarity_threshold: float = 0.8,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar decision cases for comparison

        Args:
            loan_id: Reference loan ID
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of similar cases to return

        Returns:
            List of similar decision cases
        """
        reference_trace = self._find_trace_by_loan(loan_id)
        if not reference_trace:
            return []

        similar_cases = []

        for trace_id, trace in self.completed_traces.items():
            if trace.loan_id == loan_id:
                continue

            similarity_score = await self._calculate_similarity(reference_trace, trace)

            if similarity_score >= similarity_threshold:
                similar_cases.append({
                    "loan_id": trace.loan_id,
                    "trace_id": trace_id,
                    "similarity_score": similarity_score,
                    "outcome": trace.final_outcome,
                    "key_differences": await self._identify_differences(reference_trace, trace),
                    "completion_time": trace.end_time.isoformat() if trace.end_time else None
                })

        # Sort by similarity score (descending) and limit results
        similar_cases.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_cases[:limit]

    async def analyze_decision_impact(
        self,
        trace_id: str,
        data_point_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze how changing specific data points would impact decisions

        Args:
            trace_id: Trace to analyze
            data_point_changes: Proposed changes to data points

        Returns:
            Impact analysis results
        """
        if trace_id not in self.completed_traces:
            raise ValueError(f"No completed trace found for {trace_id}")

        trace = self.completed_traces[trace_id]
        impact_analysis = {
            "original_outcome": trace.final_outcome,
            "proposed_changes": data_point_changes,
            "impact_by_decision": {},
            "overall_impact": "low",
            "confidence": 0.0
        }

        # Analyze impact on each decision node
        for node_id, node in trace.nodes.items():
            node_impact = await self._analyze_node_impact(node, data_point_changes)
            impact_analysis["impact_by_decision"][node_id] = node_impact

        # Calculate overall impact
        impact_analysis["overall_impact"], impact_analysis["confidence"] = \
            await self._calculate_overall_impact(impact_analysis["impact_by_decision"])

        return impact_analysis

    # Private helper methods

    async def _capture_initial_context(self, trace: DecisionTrace, context: Dict[str, Any]):
        """Capture initial context as root data points"""
        # This would create initial data points from context
        pass

    def _calculate_confidence_score(self, factors: List[DecisionFactor]) -> float:
        """Calculate overall confidence score from factors"""
        if not factors:
            return 0.0

        total_weight = sum(factor.weight for factor in factors)
        if total_weight == 0:
            return 0.0

        weighted_confidence = sum(
            factor.weight * self._confidence_level_to_float(factor.confidence)
            for factor in factors
        )

        return weighted_confidence / total_weight

    def _confidence_level_to_float(self, level: ConfidenceLevel) -> float:
        """Convert confidence level to numeric value"""
        mapping = {
            ConfidenceLevel.CRITICAL: 0.95,
            ConfidenceLevel.HIGH: 0.80,
            ConfidenceLevel.MEDIUM: 0.55,
            ConfidenceLevel.LOW: 0.25,
            ConfidenceLevel.MINIMAL: 0.05
        }
        return mapping.get(level, 0.5)

    def _extract_alternatives(
        self,
        reasoning_chain: List[str],
        final_decision: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract alternative options from reasoning chain"""
        alternatives = []
        # This would parse reasoning chain to extract alternatives considered
        # For now, return empty list
        return alternatives

    async def _calculate_completeness(self, trace: DecisionTrace) -> float:
        """Calculate how complete the decision trace is"""
        if not trace.nodes:
            return 0.0

        # Check for required decision types
        required_decisions = {
            DecisionType.RISK_ASSESSMENT,
            DecisionType.LOAN_APPROVAL,
            DecisionType.INTEREST_RATE
        }

        present_decisions = {node.decision_type for node in trace.nodes.values()}
        completeness = len(present_decisions & required_decisions) / len(required_decisions)

        # Check for reasoning completeness
        reasoning_completeness = sum(
            1 if node.reasoning_chain else 0
            for node in trace.nodes.values()
        ) / len(trace.nodes)

        return (completeness + reasoning_completeness) / 2

    async def _calculate_consistency(self, trace: DecisionTrace) -> float:
        """Calculate internal consistency of decisions"""
        if len(trace.nodes) < 2:
            return 1.0

        # Check for contradictory decisions
        consistency_score = 1.0
        # This would implement actual consistency checking logic
        return consistency_score

    async def _validate_trace(self, trace: DecisionTrace) -> List[str]:
        """Validate trace and return audit flags"""
        flags = []

        # Check completeness
        if trace.completeness_score < 0.8:
            flags.append("incomplete_trace")

        # Check consistency
        if trace.consistency_score < 0.8:
            flags.append("inconsistent_decisions")

        # Check for missing data
        for node in trace.nodes.values():
            if not node.factors:
                flags.append(f"missing_factors_{node.node_id}")

        return flags

    def _find_trace_by_loan(self, loan_id: str) -> Optional[DecisionTrace]:
        """Find trace by loan ID"""
        # Check active traces first
        for trace in self.active_traces.values():
            if trace.loan_id == loan_id:
                return trace

        # Check completed traces
        for trace in self.completed_traces.values():
            if trace.loan_id == loan_id:
                return trace

        return None

    async def _generate_explanation(
        self,
        trace: DecisionTrace,
        nodes: List[DecisionNode],
        simplified: bool
    ) -> Dict[str, Any]:
        """Generate human-readable explanation"""
        explanation = {
            "loan_id": trace.loan_id,
            "summary": "",
            "key_decisions": [],
            "data_sources": [],
            "confidence_assessment": "",
            "alternative_scenarios": []
        }

        # Generate summary
        if simplified:
            explanation["summary"] = await self._generate_simple_summary(nodes)
        else:
            explanation["summary"] = await self._generate_detailed_summary(nodes)

        # Extract key decisions
        for node in sorted(nodes, key=lambda x: x.timestamp):
            decision_info = {
                "type": node.decision_type.value,
                "outcome": node.output_decision,
                "reasoning": node.reasoning_chain,
                "confidence": node.confidence_score,
                "key_factors": [
                    {
                        "name": factor.name,
                        "impact": factor.weight,
                        "reasoning": factor.reasoning
                    }
                    for factor in node.factors
                ]
            }
            explanation["key_decisions"].append(decision_info)

        return explanation

    async def _generate_simple_summary(self, nodes: List[DecisionNode]) -> str:
        """Generate simplified summary for non-technical users"""
        # This would generate a simple, plain-English summary
        return "Loan decision based on creditworthiness assessment and risk analysis."

    async def _generate_detailed_summary(self, nodes: List[DecisionNode]) -> str:
        """Generate detailed technical summary"""
        # This would generate a detailed technical summary
        return "Comprehensive analysis of loan application with detailed factor analysis."

    async def _calculate_similarity(
        self,
        trace1: DecisionTrace,
        trace2: DecisionTrace
    ) -> float:
        """Calculate similarity between two traces"""
        # This would implement similarity calculation logic
        # For now, return a placeholder
        return 0.7

    async def _identify_differences(
        self,
        trace1: DecisionTrace,
        trace2: DecisionTrace
    ) -> List[str]:
        """Identify key differences between traces"""
        # This would identify specific differences
        return ["interest_rate_methodology", "collateral_requirements"]

    async def _analyze_node_impact(
        self,
        node: DecisionNode,
        data_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze impact of data changes on a specific node"""
        return {
            "impact_level": "medium",
            "affected_factors": ["credit_score", "income"],
            "estimated_change": 0.15
        }

    async def _calculate_overall_impact(
        self,
        node_impacts: Dict[str, Any]
    ) -> Tuple[str, float]:
        """Calculate overall impact from individual node impacts"""
        # This would aggregate individual impacts
        return "medium", 0.65

    def get_trace_statistics(self) -> Dict[str, Any]:
        """Get statistics about traces"""
        return {
            "active_traces": len(self.active_traces),
            "completed_traces": len(self.completed_traces),
            "total_decisions": sum(
                len(trace.nodes) for trace in self.completed_traces.values()
            ),
            "average_completeness": sum(
                trace.completeness_score for trace in self.completed_traces.values()
            ) / max(len(self.completed_traces), 1),
            "patterns_identified": len(self.decision_patterns)
        }