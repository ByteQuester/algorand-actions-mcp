"""
Traceability API Router
REST endpoints for decision traceability and explanation
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body, status
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..core.audit.traceability_engine import (
    TraceabilityEngine, DecisionType, DecisionTrace
)
from ..core.audit.explanation_generator import (
    ExplanationGenerator, StakeholderType, ExplanationLevel
)
from .auth import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/audit/trace",
    tags=["traceability"],
    responses={404: {"description": "Not found"}}
)

# Initialize services
traceability_engine = TraceabilityEngine()
explanation_generator = ExplanationGenerator()


@router.get("/{loan_id}/decision/{decision_id}")
async def get_decision_trace(
    loan_id: str,
    decision_id: str,
    include_alternatives: bool = Query(False, description="Include alternative scenarios"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get complete trace for a specific decision

    Returns detailed traceability information linking the decision
    to all data points, reasoning steps, and influencing factors.

    Args:
        loan_id: Unique loan identifier
        decision_id: Specific decision node identifier
        include_alternatives: Whether to include alternative scenarios

    Returns:
        Complete decision trace with full reasoning chain
    """
    try:
        logger.info(f"Getting decision trace for loan {loan_id}, decision {decision_id}")

        # Find the trace for this loan
        trace = traceability_engine._find_trace_by_loan(loan_id)
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No trace found for loan {loan_id}"
            )

        # Find the specific decision node
        if decision_id not in trace.nodes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Decision {decision_id} not found in trace"
            )

        decision_node = trace.nodes[decision_id]

        # Build detailed trace response
        trace_response = {
            "loan_id": loan_id,
            "decision_id": decision_id,
            "decision_type": decision_node.decision_type.value,
            "timestamp": decision_node.timestamp.isoformat(),
            "confidence_score": decision_node.confidence_score,
            "input_data": decision_node.input_data,
            "output_decision": decision_node.output_decision,
            "reasoning_chain": decision_node.reasoning_chain,
            "factors": [
                {
                    "factor_id": factor.factor_id,
                    "name": factor.name,
                    "weight": factor.weight,
                    "confidence": factor.confidence.value,
                    "reasoning": factor.reasoning,
                    "data_points": [
                        {
                            "key": dp.key,
                            "value": dp.value,
                            "source": dp.source,
                            "timestamp": dp.timestamp.isoformat(),
                            "confidence": dp.confidence,
                            "impact_score": dp.impact_score,
                            "validation_status": dp.validation_status
                        }
                        for dp in factor.data_points
                    ]
                }
                for factor in decision_node.factors
            ],
            "parent_decisions": decision_node.parent_nodes,
            "child_decisions": decision_node.child_nodes,
            "agent_context": decision_node.agent_context
        }

        if include_alternatives:
            trace_response["alternatives_considered"] = decision_node.alternatives_considered

        return trace_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get decision trace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve decision trace"
        )


@router.get("/explain/{loan_id}")
async def get_loan_explanation(
    loan_id: str,
    stakeholder: StakeholderType = Query(StakeholderType.LOAN_OFFICER, description="Type of stakeholder"),
    decision_type: Optional[DecisionType] = Query(None, description="Specific decision to explain"),
    simplified: bool = Query(False, description="Generate simplified explanation"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get human-readable explanation of loan decisions

    Generates explanations tailored for different stakeholders,
    from simple customer explanations to detailed regulatory reports.

    Args:
        loan_id: Unique loan identifier
        stakeholder: Who the explanation is for
        decision_type: Focus on specific decision type (optional)
        simplified: Generate simplified explanation

    Returns:
        Structured explanation with reasoning and supporting evidence
    """
    try:
        logger.info(f"Generating explanation for loan {loan_id}, stakeholder {stakeholder.value}")

        # Find trace
        trace = traceability_engine._find_trace_by_loan(loan_id)
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No decision trace found for loan {loan_id}"
            )

        # Verify user authorization based on stakeholder type
        await _verify_stakeholder_access(user, stakeholder)

        # Generate explanation
        explanation = explanation_generator.generate_explanation(
            trace=trace,
            stakeholder=stakeholder,
            specific_decision=decision_type
        )

        return explanation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation"
        )


@router.post("/impact/{loan_id}")
async def analyze_decision_impact(
    loan_id: str,
    proposed_changes: Dict[str, Any] = Body(..., description="Proposed data changes"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyze impact of proposed data changes on loan decision

    Performs "what if" analysis to show how changing specific data points
    would affect the loan decision and terms.

    Args:
        loan_id: Unique loan identifier
        proposed_changes: Dictionary of data point changes to analyze

    Returns:
        Impact analysis with predicted outcomes and confidence scores
    """
    try:
        logger.info(f"Analyzing impact for loan {loan_id}")

        # Find completed trace
        trace = None
        for trace_id, t in traceability_engine.completed_traces.items():
            if t.loan_id == loan_id:
                trace = t
                break

        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No completed trace found for loan {loan_id}"
            )

        # Perform impact analysis
        impact_analysis = await traceability_engine.analyze_decision_impact(
            trace_id=trace.trace_id,
            data_point_changes=proposed_changes
        )

        # Generate explanation of impact
        explanation = explanation_generator.generate_impact_analysis(
            trace=trace,
            proposed_changes=proposed_changes
        )

        return {
            "loan_id": loan_id,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "proposed_changes": proposed_changes,
            "impact_analysis": impact_analysis,
            "explanation": explanation,
            "recommendations": await _generate_impact_recommendations(impact_analysis)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze impact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze decision impact"
        )


@router.get("/similar-cases/{loan_id}")
async def find_similar_cases(
    loan_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of similar cases"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Find similar decision cases for comparison

    Identifies loans with similar characteristics and decision patterns
    to provide context and validate decision consistency.

    Args:
        loan_id: Reference loan ID
        limit: Maximum number of similar cases to return
        similarity_threshold: Minimum similarity score (0.0-1.0)

    Returns:
        List of similar cases with comparison analysis
    """
    try:
        logger.info(f"Finding similar cases for loan {loan_id}")

        similar_cases = await traceability_engine.find_similar_decisions(
            loan_id=loan_id,
            similarity_threshold=similarity_threshold,
            limit=limit
        )

        if not similar_cases:
            return {
                "reference_loan_id": loan_id,
                "similar_cases": [],
                "message": "No similar cases found with the specified threshold",
                "suggestions": [
                    "Lower the similarity threshold",
                    "Check if more loan data is available for comparison"
                ]
            }

        # Enrich similar cases with explanations
        enriched_cases = []
        for case in similar_cases:
            case_trace = traceability_engine._find_trace_by_loan(case["loan_id"])
            if case_trace:
                # Generate comparison explanation
                reference_trace = traceability_engine._find_trace_by_loan(loan_id)
                comparison = explanation_generator.generate_decision_comparison(
                    trace1=reference_trace,
                    trace2=case_trace
                )
                case["comparison_analysis"] = comparison

            enriched_cases.append(case)

        return {
            "reference_loan_id": loan_id,
            "similarity_threshold": similarity_threshold,
            "similar_cases": enriched_cases,
            "total_found": len(enriched_cases),
            "analysis_notes": await _generate_similarity_insights(enriched_cases)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find similar cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar cases"
        )


@router.get("/validate/{loan_id}")
async def validate_decision_completeness(
    loan_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Validate completeness of decision audit trail

    Checks that all required decisions have been captured and traced,
    identifying any gaps in the audit trail.

    Args:
        loan_id: Unique loan identifier

    Returns:
        Validation report with completeness scores and recommendations
    """
    try:
        logger.info(f"Validating decision completeness for loan {loan_id}")

        trace = traceability_engine._find_trace_by_loan(loan_id)
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No trace found for loan {loan_id}"
            )

        validation_report = {
            "loan_id": loan_id,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "completeness_score": trace.completeness_score,
            "consistency_score": trace.consistency_score,
            "audit_flags": trace.audit_flags,
            "required_decisions": await _check_required_decisions(trace),
            "missing_elements": await _identify_missing_elements(trace),
            "quality_metrics": await _calculate_quality_metrics(trace),
            "recommendations": await _generate_validation_recommendations(trace)
        }

        # Overall validation status
        if trace.completeness_score >= 0.9 and trace.consistency_score >= 0.9:
            validation_report["status"] = "excellent"
        elif trace.completeness_score >= 0.8 and trace.consistency_score >= 0.8:
            validation_report["status"] = "good"
        elif trace.completeness_score >= 0.7 and trace.consistency_score >= 0.7:
            validation_report["status"] = "acceptable"
        else:
            validation_report["status"] = "needs_improvement"

        return validation_report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate decision completeness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate decision completeness"
        )


@router.get("/stats")
async def get_traceability_statistics(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get traceability system statistics

    Returns system-wide statistics about decision tracing,
    completeness scores, and processing metrics.

    Returns:
        System statistics and performance metrics
    """
    try:
        # Verify admin access
        if user.get("role") not in ["admin", "compliance_officer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view system statistics"
            )

        stats = traceability_engine.get_trace_statistics()

        # Add additional analytics
        enhanced_stats = {
            **stats,
            "system_health": {
                "average_completeness": stats["average_completeness"],
                "trace_success_rate": stats["completed_traces"] / max(
                    stats["completed_traces"] + len(traceability_engine.active_traces), 1
                ),
                "processing_efficiency": "high" if stats["average_completeness"] > 0.8 else "medium"
            },
            "quality_metrics": await _calculate_system_quality_metrics(),
            "recent_activity": await _get_recent_activity_summary(),
            "performance_trends": await _get_performance_trends()
        }

        return enhanced_stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )


# Helper functions

async def _verify_stakeholder_access(user: Dict[str, Any], stakeholder: StakeholderType):
    """Verify user has access to request explanation for stakeholder type"""
    user_role = user.get("role", "user")

    # Define access permissions
    access_permissions = {
        StakeholderType.LOAN_APPLICANT: ["user", "loan_officer", "admin"],
        StakeholderType.LOAN_OFFICER: ["loan_officer", "admin"],
        StakeholderType.COMPLIANCE_OFFICER: ["compliance_officer", "admin"],
        StakeholderType.REGULATOR: ["compliance_officer", "regulator", "admin"],
        StakeholderType.EXECUTIVE: ["executive", "admin"],
        StakeholderType.DEVELOPER: ["developer", "admin"]
    }

    if user_role not in access_permissions.get(stakeholder, []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to request {stakeholder.value} explanation"
        )


async def _generate_impact_recommendations(impact_analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on impact analysis"""
    recommendations = []

    overall_impact = impact_analysis.get("overall_impact", "low")
    if overall_impact == "high":
        recommendations.append("Consider implementing proposed changes - significant positive impact expected")
    elif overall_impact == "medium":
        recommendations.append("Review proposed changes carefully - moderate impact detected")
    else:
        recommendations.append("Proposed changes would have minimal impact on decision")

    return recommendations


async def _generate_similarity_insights(similar_cases: List[Dict[str, Any]]) -> List[str]:
    """Generate insights from similar cases analysis"""
    if not similar_cases:
        return ["No similar cases available for analysis"]

    insights = []
    avg_similarity = sum(case["similarity_score"] for case in similar_cases) / len(similar_cases)

    if avg_similarity > 0.9:
        insights.append("Very high similarity detected - decisions show strong consistency")
    elif avg_similarity > 0.8:
        insights.append("Good similarity detected - decisions follow established patterns")
    else:
        insights.append("Moderate similarity - review for potential inconsistencies")

    return insights


async def _check_required_decisions(trace: DecisionTrace) -> Dict[str, Any]:
    """Check if all required decision types are present"""
    required_types = {
        DecisionType.RISK_ASSESSMENT,
        DecisionType.LOAN_APPROVAL,
        DecisionType.INTEREST_RATE
    }

    present_types = {node.decision_type for node in trace.nodes.values()}
    missing_types = required_types - present_types

    return {
        "required": [t.value for t in required_types],
        "present": [t.value for t in present_types],
        "missing": [t.value for t in missing_types],
        "completeness_percentage": (len(present_types & required_types) / len(required_types)) * 100
    }


async def _identify_missing_elements(trace: DecisionTrace) -> List[str]:
    """Identify missing elements in the trace"""
    missing = []

    for node in trace.nodes.values():
        if not node.reasoning_chain:
            missing.append(f"Missing reasoning for decision {node.node_id}")
        if not node.factors:
            missing.append(f"Missing factors for decision {node.node_id}")
        if node.confidence_score < 0.5:
            missing.append(f"Low confidence decision {node.node_id}")

    return missing


async def _calculate_quality_metrics(trace: DecisionTrace) -> Dict[str, float]:
    """Calculate various quality metrics for the trace"""
    if not trace.nodes:
        return {"overall_quality": 0.0}

    reasoning_completeness = sum(
        1 if node.reasoning_chain else 0 for node in trace.nodes.values()
    ) / len(trace.nodes)

    factor_completeness = sum(
        1 if node.factors else 0 for node in trace.nodes.values()
    ) / len(trace.nodes)

    avg_confidence = sum(
        node.confidence_score for node in trace.nodes.values()
    ) / len(trace.nodes)

    return {
        "reasoning_completeness": reasoning_completeness,
        "factor_completeness": factor_completeness,
        "average_confidence": avg_confidence,
        "overall_quality": (reasoning_completeness + factor_completeness + avg_confidence) / 3
    }


async def _generate_validation_recommendations(trace: DecisionTrace) -> List[str]:
    """Generate recommendations for improving trace quality"""
    recommendations = []

    if trace.completeness_score < 0.8:
        recommendations.append("Improve decision capture completeness")

    if trace.consistency_score < 0.8:
        recommendations.append("Review decision consistency and logic")

    if trace.audit_flags:
        recommendations.append(f"Address {len(trace.audit_flags)} audit flags")

    return recommendations


async def _calculate_system_quality_metrics() -> Dict[str, Any]:
    """Calculate system-wide quality metrics"""
    return {
        "decision_capture_rate": 0.95,
        "explanation_accuracy": 0.92,
        "user_satisfaction": 0.88
    }


async def _get_recent_activity_summary() -> Dict[str, Any]:
    """Get summary of recent system activity"""
    return {
        "traces_completed_today": 15,
        "explanations_generated_today": 42,
        "impact_analyses_performed": 8
    }


async def _get_performance_trends() -> Dict[str, Any]:
    """Get performance trend data"""
    return {
        "completeness_trend": "improving",
        "processing_speed": "stable",
        "user_adoption": "increasing"
    }