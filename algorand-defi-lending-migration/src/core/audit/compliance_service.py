"""
Compliance Service for Regulatory Reporting and Analysis

This service provides comprehensive regulatory compliance functionality including:
- Fair lending bias detection (ECOA, Fair Lending Act)
- Interest rate justification with market comparison
- Decision consistency validation across demographics
- Automated bias detection algorithms
- Regulatory metrics calculation and monitoring

Designed to generate actionable insights and maintain regulatory compliance.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass, field
import asyncpg
import json
import statistics
import numpy as np
from scipy import stats
import pandas as pd

from .models import (
    AuditTrail, DecisionPoint, ComplianceEvent, AuditSession,
    AuditEventType, DecisionType, AuditSeverity, ComplianceClassification
)

logger = logging.getLogger(__name__)


class BiasType(Enum):
    """Types of bias that can be detected in lending decisions"""
    DEMOGRAPHIC_BIAS = "demographic_bias"
    GEOGRAPHIC_BIAS = "geographic_bias"
    INCOME_BIAS = "income_bias"
    CREDIT_SCORE_BIAS = "credit_score_bias"
    COLLATERAL_BIAS = "collateral_bias"
    INTEREST_RATE_BIAS = "interest_rate_bias"
    APPROVAL_RATE_BIAS = "approval_rate_bias"
    LOAN_AMOUNT_BIAS = "loan_amount_bias"


class RegulatoryFramework(Enum):
    """Supported regulatory frameworks"""
    ECOA = "ecoa"  # Equal Credit Opportunity Act
    FAIR_LENDING_ACT = "fair_lending_act"
    CRA = "cra"  # Community Reinvestment Act
    SAFE_ACT = "safe_act"  # Secure and Fair Enforcement Act
    TILA = "tila"  # Truth in Lending Act
    RESPA = "respa"  # Real Estate Settlement Procedures Act
    FCRA = "fcra"  # Fair Credit Reporting Act
    HMDA = "hmda"  # Home Mortgage Disclosure Act


@dataclass
class BiasAnalysisResult:
    """Results of bias analysis for a specific metric"""
    bias_type: BiasType
    detected: bool
    severity_score: float  # 0.0 to 1.0
    p_value: float
    confidence_interval: Tuple[float, float]
    affected_groups: List[str]
    statistical_test: str
    sample_sizes: Dict[str, int]
    effect_size: float
    recommendations: List[str]
    regulatory_impact: str
    evidence: Dict[str, Any]


@dataclass
class ComplianceMetrics:
    """Key compliance metrics for regulatory reporting"""
    total_loans: int
    approval_rate: float
    average_interest_rate: float
    demographic_breakdown: Dict[str, Dict[str, Any]]
    geographic_distribution: Dict[str, Dict[str, Any]]
    risk_score_distribution: Dict[str, int]
    bias_flags: List[BiasAnalysisResult]
    regulatory_violations: List[str]
    compliance_score: float  # 0.0 to 1.0
    generated_at: datetime
    period_start: datetime
    period_end: datetime


@dataclass
class InterestRateJustification:
    """Justification analysis for interest rates"""
    loan_id: str
    borrower_profile: Dict[str, Any]
    assigned_rate: float
    market_benchmark: float
    risk_premium: float
    justified: bool
    justification_factors: List[str]
    comparable_loans: List[Dict[str, Any]]
    regulatory_compliance: bool
    explanation: str


class ComplianceService:
    """
    Advanced compliance service for regulatory reporting and bias detection

    Provides comprehensive analysis of lending decisions for regulatory compliance,
    including automated bias detection, interest rate justification, and report generation.
    """

    def __init__(self, database_url: str, market_data_source: Optional[str] = None):
        self.database_url = database_url
        self.market_data_source = market_data_source
        self.connection_pool: Optional[asyncpg.Pool] = None

        # Statistical thresholds for bias detection
        self.bias_thresholds = {
            "p_value": 0.05,  # Statistical significance threshold
            "effect_size": 0.2,  # Minimum effect size to consider meaningful
            "sample_size": 30,  # Minimum sample size for statistical tests
            "severity_high": 0.8,  # High severity threshold
            "severity_medium": 0.5  # Medium severity threshold
        }

        # Protected classes for fair lending analysis
        self.protected_classes = [
            "race", "ethnicity", "gender", "age", "religion",
            "national_origin", "marital_status", "disability_status"
        ]

    async def initialize(self):
        """Initialize the compliance service"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Compliance service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize compliance service: {e}")
            raise

    async def close(self):
        """Clean up resources"""
        if self.connection_pool:
            await self.connection_pool.close()

    async def generate_compliance_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        frameworks: Optional[List[RegulatoryFramework]] = None
    ) -> ComplianceMetrics:
        """Generate comprehensive compliance metrics for a time period"""

        if frameworks is None:
            frameworks = [RegulatoryFramework.ECOA, RegulatoryFramework.FAIR_LENDING_ACT]

        async with self.connection_pool.acquire() as conn:
            # Get loan data for the period
            loan_data = await self._get_loan_data(conn, start_date, end_date)

            # Calculate basic metrics
            total_loans = len(loan_data)
            approved_loans = [loan for loan in loan_data if loan.get('approved', False)]
            approval_rate = len(approved_loans) / total_loans if total_loans > 0 else 0.0

            # Calculate average interest rate
            rates = [loan.get('interest_rate', 0.0) for loan in approved_loans if loan.get('interest_rate')]
            avg_interest_rate = statistics.mean(rates) if rates else 0.0

            # Demographic breakdown
            demographic_breakdown = await self._analyze_demographics(loan_data)

            # Geographic distribution
            geographic_distribution = await self._analyze_geography(loan_data)

            # Risk score distribution
            risk_distribution = await self._analyze_risk_distribution(loan_data)

            # Bias analysis
            bias_results = await self._perform_bias_analysis(loan_data)

            # Check for regulatory violations
            violations = await self._check_regulatory_violations(
                loan_data, bias_results, frameworks
            )

            # Calculate overall compliance score
            compliance_score = await self._calculate_compliance_score(
                bias_results, violations, demographic_breakdown
            )

            return ComplianceMetrics(
                total_loans=total_loans,
                approval_rate=approval_rate,
                average_interest_rate=avg_interest_rate,
                demographic_breakdown=demographic_breakdown,
                geographic_distribution=geographic_distribution,
                risk_score_distribution=risk_distribution,
                bias_flags=bias_results,
                regulatory_violations=violations,
                compliance_score=compliance_score,
                generated_at=datetime.now(timezone.utc),
                period_start=start_date,
                period_end=end_date
            )

    async def detect_bias(
        self,
        loan_data: List[Dict[str, Any]],
        bias_types: Optional[List[BiasType]] = None
    ) -> List[BiasAnalysisResult]:
        """Perform comprehensive bias detection analysis"""

        if bias_types is None:
            bias_types = list(BiasType)

        bias_results = []

        for bias_type in bias_types:
            try:
                result = await self._analyze_specific_bias(loan_data, bias_type)
                if result:
                    bias_results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {bias_type}: {e}")
                continue

        return bias_results

    async def justify_interest_rate(
        self,
        loan_id: str,
        borrower_profile: Dict[str, Any],
        assigned_rate: float
    ) -> InterestRateJustification:
        """Analyze and justify interest rate assignment"""

        async with self.connection_pool.acquire() as conn:
            # Get market benchmark data
            market_benchmark = await self._get_market_benchmark(
                conn, borrower_profile
            )

            # Find comparable loans
            comparable_loans = await self._find_comparable_loans(
                conn, borrower_profile, limit=10
            )

            # Calculate risk premium
            risk_premium = assigned_rate - market_benchmark

            # Analyze justification factors
            factors = await self._analyze_rate_factors(
                borrower_profile, comparable_loans, risk_premium
            )

            # Determine if rate is justified
            justified = await self._is_rate_justified(
                assigned_rate, market_benchmark, risk_premium, factors
            )

            # Check regulatory compliance
            regulatory_compliant = await self._check_rate_compliance(
                assigned_rate, borrower_profile, comparable_loans
            )

            # Generate explanation
            explanation = await self._generate_rate_explanation(
                factors, justified, regulatory_compliant
            )

            return InterestRateJustification(
                loan_id=loan_id,
                borrower_profile=borrower_profile,
                assigned_rate=assigned_rate,
                market_benchmark=market_benchmark,
                risk_premium=risk_premium,
                justified=justified,
                justification_factors=factors,
                comparable_loans=comparable_loans,
                regulatory_compliance=regulatory_compliant,
                explanation=explanation
            )

    async def validate_decision_consistency(
        self,
        start_date: datetime,
        end_date: datetime,
        decision_type: DecisionType
    ) -> Dict[str, Any]:
        """Validate consistency of lending decisions across demographics"""

        async with self.connection_pool.acquire() as conn:
            # Get decision data
            decisions = await self._get_decision_data(
                conn, start_date, end_date, decision_type
            )

            # Group by demographics
            demographic_groups = await self._group_by_demographics(decisions)

            # Calculate consistency metrics
            consistency_metrics = {}

            for group_name, group_decisions in demographic_groups.items():
                metrics = await self._calculate_group_metrics(group_decisions)
                consistency_metrics[group_name] = metrics

            # Perform statistical consistency tests
            consistency_tests = await self._perform_consistency_tests(
                demographic_groups
            )

            # Generate recommendations
            recommendations = await self._generate_consistency_recommendations(
                consistency_tests, consistency_metrics
            )

            return {
                "decision_type": decision_type.value,
                "period": {"start": start_date, "end": end_date},
                "total_decisions": len(decisions),
                "demographic_groups": len(demographic_groups),
                "group_metrics": consistency_metrics,
                "consistency_tests": consistency_tests,
                "recommendations": recommendations,
                "overall_consistency_score": await self._calculate_overall_consistency(
                    consistency_tests
                )
            }

    async def _get_loan_data(
        self,
        conn: asyncpg.Connection,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Retrieve loan data for analysis"""
        query = """
        SELECT
            dt.loan_id,
            dt.borrower_address,
            dt.decision_outcome,
            dt.input_data,
            dt.decision_rationale,
            dt.confidence_score,
            dt.risk_score,
            dt.decision_timestamp
        FROM decision_points dt
        WHERE dt.decision_timestamp >= $1
        AND dt.decision_timestamp <= $2
        AND dt.decision_type = 'credit_approval'
        ORDER BY dt.decision_timestamp DESC
        """

        rows = await conn.fetch(query, start_date, end_date)

        loan_data = []
        for row in rows:
            input_data = json.loads(row['input_data']) if row['input_data'] else {}

            loan_record = {
                'loan_id': row['loan_id'],
                'borrower_address': row['borrower_address'],
                'approved': row['decision_outcome'].lower() == 'approved',
                'rationale': row['decision_rationale'],
                'confidence_score': row['confidence_score'],
                'risk_score': row['risk_score'],
                'decision_timestamp': row['decision_timestamp'],
                **input_data  # Include all input data fields
            }

            loan_data.append(loan_record)

        return loan_data

    async def _perform_bias_analysis(
        self,
        loan_data: List[Dict[str, Any]]
    ) -> List[BiasAnalysisResult]:
        """Perform comprehensive bias analysis"""

        bias_results = []

        # Approval rate bias analysis
        approval_bias = await self._analyze_approval_rate_bias(loan_data)
        if approval_bias:
            bias_results.append(approval_bias)

        # Interest rate bias analysis
        rate_bias = await self._analyze_interest_rate_bias(loan_data)
        if rate_bias:
            bias_results.append(rate_bias)

        # Loan amount bias analysis
        amount_bias = await self._analyze_loan_amount_bias(loan_data)
        if amount_bias:
            bias_results.append(amount_bias)

        return bias_results

    async def _analyze_approval_rate_bias(
        self,
        loan_data: List[Dict[str, Any]]
    ) -> Optional[BiasAnalysisResult]:
        """Analyze bias in approval rates across protected classes"""

        if len(loan_data) < self.bias_thresholds["sample_size"]:
            return None

        # Group by protected characteristics
        groups = {}

        for loan in loan_data:
            # Example: Analyze by credit score ranges as proxy for protected class analysis
            # In real implementation, would use actual demographic data
            credit_score = loan.get('credit_score', 600)

            if credit_score >= 750:
                group_key = 'high_credit'
            elif credit_score >= 650:
                group_key = 'medium_credit'
            else:
                group_key = 'low_credit'

            if group_key not in groups:
                groups[group_key] = {'approved': 0, 'total': 0}

            groups[group_key]['total'] += 1
            if loan.get('approved', False):
                groups[group_key]['approved'] += 1

        # Calculate approval rates
        approval_rates = {}
        sample_sizes = {}

        for group, stats in groups.items():
            if stats['total'] >= self.bias_thresholds["sample_size"]:
                approval_rates[group] = stats['approved'] / stats['total']
                sample_sizes[group] = stats['total']

        if len(approval_rates) < 2:
            return None

        # Perform statistical test (Chi-square test)
        contingency_table = []
        group_names = list(approval_rates.keys())

        for group in group_names:
            approved = groups[group]['approved']
            rejected = groups[group]['total'] - approved
            contingency_table.append([approved, rejected])

        try:
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

            # Calculate effect size (Cramer's V)
            n = sum(sum(row) for row in contingency_table)
            effect_size = np.sqrt(chi2 / (n * (min(len(contingency_table), 2) - 1)))

            # Determine severity
            severity = 0.0
            if p_value < self.bias_thresholds["p_value"]:
                severity = min(1.0, effect_size * 2)  # Scale effect size to severity

            detected = (
                p_value < self.bias_thresholds["p_value"] and
                effect_size > self.bias_thresholds["effect_size"]
            )

            # Generate recommendations
            recommendations = []
            if detected:
                recommendations.extend([
                    "Review approval criteria for potential disparate impact",
                    "Conduct manual review of rejected applications from affected groups",
                    "Implement additional controls for approval consistency",
                    "Consider alternative credit assessment methods"
                ])

            # Determine regulatory impact
            regulatory_impact = "HIGH" if severity > 0.7 else "MEDIUM" if severity > 0.4 else "LOW"

            return BiasAnalysisResult(
                bias_type=BiasType.APPROVAL_RATE_BIAS,
                detected=detected,
                severity_score=severity,
                p_value=p_value,
                confidence_interval=(max(0, effect_size - 0.1), min(1, effect_size + 0.1)),
                affected_groups=group_names if detected else [],
                statistical_test="Chi-square test of independence",
                sample_sizes=sample_sizes,
                effect_size=effect_size,
                recommendations=recommendations,
                regulatory_impact=regulatory_impact,
                evidence={
                    "approval_rates": approval_rates,
                    "chi2_statistic": chi2,
                    "degrees_of_freedom": dof,
                    "contingency_table": contingency_table
                }
            )

        except Exception as e:
            logger.error(f"Error in approval rate bias analysis: {e}")
            return None

    async def _analyze_specific_bias(
        self,
        loan_data: List[Dict[str, Any]],
        bias_type: BiasType
    ) -> Optional[BiasAnalysisResult]:
        """Analyze a specific type of bias"""

        if bias_type == BiasType.APPROVAL_RATE_BIAS:
            return await self._analyze_approval_rate_bias(loan_data)
        elif bias_type == BiasType.INTEREST_RATE_BIAS:
            return await self._analyze_interest_rate_bias(loan_data)
        elif bias_type == BiasType.LOAN_AMOUNT_BIAS:
            return await self._analyze_loan_amount_bias(loan_data)
        else:
            # Placeholder for other bias types
            return None

    async def _analyze_interest_rate_bias(
        self,
        loan_data: List[Dict[str, Any]]
    ) -> Optional[BiasAnalysisResult]:
        """Analyze bias in interest rate assignment"""

        approved_loans = [loan for loan in loan_data if loan.get('approved', False)]

        if len(approved_loans) < self.bias_thresholds["sample_size"]:
            return None

        # Group by risk score ranges
        groups = {'low_risk': [], 'medium_risk': [], 'high_risk': []}

        for loan in approved_loans:
            risk_score = loan.get('risk_score', 50.0)
            interest_rate = loan.get('interest_rate')

            if interest_rate is None:
                continue

            if risk_score <= 30:
                groups['low_risk'].append(interest_rate)
            elif risk_score <= 70:
                groups['medium_risk'].append(interest_rate)
            else:
                groups['high_risk'].append(interest_rate)

        # Filter groups with sufficient sample size
        valid_groups = {k: v for k, v in groups.items()
                       if len(v) >= self.bias_thresholds["sample_size"]}

        if len(valid_groups) < 2:
            return None

        # Perform ANOVA test
        group_values = list(valid_groups.values())

        try:
            f_stat, p_value = stats.f_oneway(*group_values)

            # Calculate effect size (eta squared)
            ss_between = sum(len(group) * (np.mean(group) - np.mean([item for sublist in group_values for item in sublist]))**2 for group in group_values)
            ss_total = sum((rate - np.mean([item for sublist in group_values for item in sublist]))**2 for sublist in group_values for rate in sublist)
            effect_size = ss_between / ss_total if ss_total > 0 else 0

            severity = min(1.0, effect_size * 3) if p_value < self.bias_thresholds["p_value"] else 0.0

            detected = (
                p_value < self.bias_thresholds["p_value"] and
                effect_size > self.bias_thresholds["effect_size"]
            )

            recommendations = []
            if detected:
                recommendations.extend([
                    "Review interest rate calculation methodology",
                    "Ensure consistent risk-based pricing across all groups",
                    "Implement rate validation controls",
                    "Conduct periodic rate benchmarking analysis"
                ])

            return BiasAnalysisResult(
                bias_type=BiasType.INTEREST_RATE_BIAS,
                detected=detected,
                severity_score=severity,
                p_value=p_value,
                confidence_interval=(max(0, effect_size - 0.05), min(1, effect_size + 0.05)),
                affected_groups=list(valid_groups.keys()) if detected else [],
                statistical_test="One-way ANOVA",
                sample_sizes={k: len(v) for k, v in valid_groups.items()},
                effect_size=effect_size,
                recommendations=recommendations,
                regulatory_impact="HIGH" if severity > 0.7 else "MEDIUM" if severity > 0.4 else "LOW",
                evidence={
                    "group_means": {k: np.mean(v) for k, v in valid_groups.items()},
                    "f_statistic": f_stat,
                    "group_statistics": {k: {"mean": np.mean(v), "std": np.std(v), "count": len(v)}
                                       for k, v in valid_groups.items()}
                }
            )

        except Exception as e:
            logger.error(f"Error in interest rate bias analysis: {e}")
            return None

    async def _analyze_loan_amount_bias(
        self,
        loan_data: List[Dict[str, Any]]
    ) -> Optional[BiasAnalysisResult]:
        """Analyze bias in loan amount decisions"""

        approved_loans = [loan for loan in loan_data if loan.get('approved', False)
                         and loan.get('loan_amount') is not None]

        if len(approved_loans) < self.bias_thresholds["sample_size"]:
            return None

        # Similar analysis structure as interest rate bias
        # Implementation would follow similar pattern
        return None

    async def _analyze_demographics(
        self,
        loan_data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze demographic breakdown of loan applications"""

        demographics = {
            'total_applications': len(loan_data),
            'approval_rate_by_group': {},
            'average_rates_by_group': {},
            'risk_distribution_by_group': {}
        }

        # For demonstration - in real implementation would use actual demographic data
        return demographics

    async def _analyze_geography(
        self,
        loan_data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze geographic distribution of loans"""
        return {}

    async def _analyze_risk_distribution(
        self,
        loan_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Analyze risk score distribution"""

        risk_buckets = {'low': 0, 'medium': 0, 'high': 0}

        for loan in loan_data:
            risk_score = loan.get('risk_score', 50.0)

            if risk_score <= 30:
                risk_buckets['low'] += 1
            elif risk_score <= 70:
                risk_buckets['medium'] += 1
            else:
                risk_buckets['high'] += 1

        return risk_buckets

    async def _check_regulatory_violations(
        self,
        loan_data: List[Dict[str, Any]],
        bias_results: List[BiasAnalysisResult],
        frameworks: List[RegulatoryFramework]
    ) -> List[str]:
        """Check for potential regulatory violations"""

        violations = []

        # Check for high-severity bias issues
        for bias_result in bias_results:
            if bias_result.detected and bias_result.severity_score > 0.7:
                violations.append(
                    f"Potential {bias_result.bias_type.value} violation detected "
                    f"(severity: {bias_result.severity_score:.2f})"
                )

        # Framework-specific checks
        for framework in frameworks:
            if framework == RegulatoryFramework.ECOA:
                ecoa_violations = await self._check_ecoa_compliance(loan_data, bias_results)
                violations.extend(ecoa_violations)

            elif framework == RegulatoryFramework.FAIR_LENDING_ACT:
                fla_violations = await self._check_fair_lending_compliance(loan_data, bias_results)
                violations.extend(fla_violations)

        return violations

    async def _check_ecoa_compliance(
        self,
        loan_data: List[Dict[str, Any]],
        bias_results: List[BiasAnalysisResult]
    ) -> List[str]:
        """Check ECOA (Equal Credit Opportunity Act) compliance"""

        violations = []

        # Check for disparate impact in approval rates
        approval_bias = next(
            (result for result in bias_results
             if result.bias_type == BiasType.APPROVAL_RATE_BIAS and result.detected),
            None
        )

        if approval_bias and approval_bias.severity_score > 0.5:
            violations.append(
                "ECOA violation: Potential disparate impact in credit approval rates"
            )

        return violations

    async def _check_fair_lending_compliance(
        self,
        loan_data: List[Dict[str, Any]],
        bias_results: List[BiasAnalysisResult]
    ) -> List[str]:
        """Check Fair Lending Act compliance"""

        violations = []

        # Check for pricing disparities
        rate_bias = next(
            (result for result in bias_results
             if result.bias_type == BiasType.INTEREST_RATE_BIAS and result.detected),
            None
        )

        if rate_bias and rate_bias.severity_score > 0.5:
            violations.append(
                "Fair Lending violation: Potential disparate treatment in interest rate pricing"
            )

        return violations

    async def _calculate_compliance_score(
        self,
        bias_results: List[BiasAnalysisResult],
        violations: List[str],
        demographic_breakdown: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate overall compliance score (0.0 to 1.0)"""

        base_score = 1.0

        # Deduct points for detected bias
        for bias_result in bias_results:
            if bias_result.detected:
                deduction = bias_result.severity_score * 0.3
                base_score -= deduction

        # Deduct points for violations
        violation_deduction = len(violations) * 0.1
        base_score -= violation_deduction

        return max(0.0, base_score)

    # Additional helper methods would be implemented here...
    # Including market benchmarking, comparable loan analysis, etc.

    async def _get_market_benchmark(
        self,
        conn: asyncpg.Connection,
        borrower_profile: Dict[str, Any]
    ) -> float:
        """Get market benchmark interest rate"""
        # Placeholder implementation
        return 5.0  # Would connect to actual market data source

    async def _find_comparable_loans(
        self,
        conn: asyncpg.Connection,
        borrower_profile: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find comparable loans for rate justification"""
        # Placeholder implementation
        return []

    async def _analyze_rate_factors(
        self,
        borrower_profile: Dict[str, Any],
        comparable_loans: List[Dict[str, Any]],
        risk_premium: float
    ) -> List[str]:
        """Analyze factors affecting interest rate"""
        factors = []

        if risk_premium > 2.0:
            factors.append("High risk premium due to credit score")
        if borrower_profile.get('debt_to_income', 0) > 0.4:
            factors.append("Elevated debt-to-income ratio")

        return factors

    async def _is_rate_justified(
        self,
        assigned_rate: float,
        market_benchmark: float,
        risk_premium: float,
        factors: List[str]
    ) -> bool:
        """Determine if interest rate is justified"""
        # Simple justification logic
        return risk_premium <= 3.0 and len(factors) >= 1

    async def _check_rate_compliance(
        self,
        assigned_rate: float,
        borrower_profile: Dict[str, Any],
        comparable_loans: List[Dict[str, Any]]
    ) -> bool:
        """Check if rate complies with regulations"""
        # Placeholder compliance check
        return assigned_rate <= 25.0  # Basic usury check

    async def _generate_rate_explanation(
        self,
        factors: List[str],
        justified: bool,
        regulatory_compliant: bool
    ) -> str:
        """Generate human-readable explanation for rate assignment"""

        explanation = "Interest rate determination: "

        if justified and regulatory_compliant:
            explanation += "Rate is justified based on risk factors: " + "; ".join(factors)
        elif not justified:
            explanation += "Rate may not be adequately justified by risk factors"
        elif not regulatory_compliant:
            explanation += "Rate may not comply with regulatory requirements"

        return explanation

    async def _get_decision_data(
        self,
        conn: asyncpg.Connection,
        start_date: datetime,
        end_date: datetime,
        decision_type: DecisionType
    ) -> List[Dict[str, Any]]:
        """Get decision data for consistency analysis"""
        # Implementation would query decision_points table
        return []

    async def _group_by_demographics(
        self,
        decisions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group decisions by demographic characteristics"""
        return {}

    async def _calculate_group_metrics(
        self,
        group_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate metrics for a demographic group"""
        return {}

    async def _perform_consistency_tests(
        self,
        demographic_groups: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Perform statistical tests for decision consistency"""
        return {}

    async def _generate_consistency_recommendations(
        self,
        consistency_tests: Dict[str, Any],
        consistency_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving decision consistency"""
        return []

    async def _calculate_overall_consistency(
        self,
        consistency_tests: Dict[str, Any]
    ) -> float:
        """Calculate overall consistency score"""
        return 0.85  # Placeholder