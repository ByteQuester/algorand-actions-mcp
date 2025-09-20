"""
Compliance Validator

Comprehensive validation engine for regulatory compliance checking of interest rates,
fees, disclosures, and other lending parameters against applicable legal frameworks.
"""

import asyncio
import logging
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .config import RegulatoryComplianceConfig
from .constants import RegulatoryComplianceConstants, ComplianceLevel, LoanType
from .jurisdictions import JurisdictionManager, ComplianceRule


class ValidationSeverity(Enum):
    """Validation result severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    issue_id: str
    severity: ValidationSeverity
    issue_type: str
    jurisdiction: str
    rule_reference: str
    description: str
    current_value: Optional[float] = None
    limit_value: Optional[float] = None
    remediation_suggestion: str = ""
    legal_reference: str = ""


@dataclass
class LoanParameters:
    """Loan parameters for validation"""
    loan_amount: float
    interest_rate: float  # Annual rate
    loan_term_months: int
    loan_type: LoanType
    fees: Dict[str, float]
    borrower_income: Optional[float] = None
    borrower_credit_score: Optional[int] = None
    collateral_value: Optional[float] = None
    purpose: str = "personal"


@dataclass
class ValidationResult:
    """Comprehensive validation result"""
    is_compliant: bool
    overall_score: float  # 0-100 compliance score
    issues: List[ValidationIssue]
    calculations: Dict[str, Any]
    recommendations: List[str]
    required_disclosures: List[str]
    licensing_requirements: List[str]
    jurisdiction_results: Dict[str, Dict[str, Any]]
    validation_timestamp: datetime


class ComplianceValidator:
    """
    Comprehensive compliance validator for lending regulations
    """

    def __init__(self, config: RegulatoryComplianceConfig):
        """Initialize the compliance validator"""
        self.config = config
        self.constants = RegulatoryComplianceConstants()
        self.jurisdiction_manager = JurisdictionManager(config)
        self.logger = logging.getLogger(__name__)

        # Validation state
        self._validation_cache = {}
        self._last_cache_clear = datetime.now()

    async def validate_loan_compliance(
        self,
        loan_params: LoanParameters,
        jurisdictions: List[str],
        borrower_info: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Perform comprehensive compliance validation for a loan

        Args:
            loan_params: Loan parameters to validate
            jurisdictions: Applicable jurisdictions
            borrower_info: Optional borrower information

        Returns:
            ValidationResult: Comprehensive validation result
        """
        validation_start = datetime.now()
        self.logger.info(f"Starting compliance validation for loan amount ${loan_params.loan_amount:,.2f}")

        # Initialize result structure
        result = ValidationResult(
            is_compliant=True,
            overall_score=100.0,
            issues=[],
            calculations={},
            recommendations=[],
            required_disclosures=[],
            licensing_requirements=[],
            jurisdiction_results={},
            validation_timestamp=validation_start
        )

        try:
            # 1. Calculate APR and related metrics
            result.calculations = await self._calculate_loan_metrics(loan_params)

            # 2. Validate against each jurisdiction
            for jurisdiction in jurisdictions:
                jurisdiction_result = await self._validate_jurisdiction(
                    loan_params, jurisdiction, result.calculations, borrower_info
                )
                result.jurisdiction_results[jurisdiction] = jurisdiction_result

                # Aggregate issues
                result.issues.extend(jurisdiction_result.get('issues', []))

            # 3. Perform cross-jurisdiction analysis
            cross_jurisdiction_issues = await self._validate_cross_jurisdiction(
                loan_params, jurisdictions, result.calculations
            )
            result.issues.extend(cross_jurisdiction_issues)

            # 4. Check for predatory lending indicators
            predatory_issues = await self._check_predatory_lending(
                loan_params, result.calculations, borrower_info
            )
            result.issues.extend(predatory_issues)

            # 5. Validate fee structure
            fee_issues = await self._validate_fee_structure(
                loan_params, jurisdictions
            )
            result.issues.extend(fee_issues)

            # 6. Check disclosure requirements
            result.required_disclosures = await self._get_required_disclosures(
                loan_params, jurisdictions
            )

            # 7. Check licensing requirements
            result.licensing_requirements = await self._get_licensing_requirements(
                jurisdictions, loan_params.loan_type
            )

            # 8. Generate compliance score and recommendations
            result.overall_score = self._calculate_compliance_score(result.issues)
            result.is_compliant = result.overall_score >= 70  # 70% minimum compliance
            result.recommendations = await self._generate_recommendations(
                loan_params, result.issues, result.calculations
            )

            validation_duration = (datetime.now() - validation_start).total_seconds()
            self.logger.info(
                f"Validation completed in {validation_duration:.2f}s. "
                f"Score: {result.overall_score:.1f}, Compliant: {result.is_compliant}"
            )

        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            result.is_compliant = False
            result.overall_score = 0.0
            result.issues.append(ValidationIssue(
                issue_id="VALIDATION_ERROR",
                severity=ValidationSeverity.CRITICAL,
                issue_type="system_error",
                jurisdiction="SYSTEM",
                rule_reference="INTERNAL",
                description=f"Validation system error: {str(e)}",
                remediation_suggestion="Contact system administrator"
            ))

        return result

    async def validate_interest_rate_only(
        self,
        interest_rate: float,
        loan_amount: float,
        loan_type: LoanType,
        jurisdictions: List[str]
    ) -> ValidationResult:
        """
        Quick validation of interest rate only

        Args:
            interest_rate: Annual interest rate
            loan_amount: Loan amount
            loan_type: Type of loan
            jurisdictions: Applicable jurisdictions

        Returns:
            ValidationResult: Validation result focused on rate compliance
        """
        # Create minimal loan parameters
        loan_params = LoanParameters(
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            loan_term_months=12,  # Default term
            loan_type=loan_type,
            fees={}
        )

        # Perform focused validation
        return await self.validate_loan_compliance(loan_params, jurisdictions)

    async def calculate_maximum_compliant_rate(
        self,
        loan_amount: float,
        loan_type: LoanType,
        jurisdictions: List[str],
        fees: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate the maximum compliant interest rate

        Args:
            loan_amount: Loan amount
            loan_type: Type of loan
            jurisdictions: Applicable jurisdictions
            fees: Optional fees to account for

        Returns:
            Dict containing maximum rate and applicable limits
        """
        if fees is None:
            fees = {}

        max_rates = {}
        applicable_limits = {}

        for jurisdiction in jurisdictions:
            limits = self.jurisdiction_manager.get_applicable_rate_limits(
                [jurisdiction], loan_type, loan_amount
            )

            if limits.get('maximum_apr') is not None:
                # Account for fees in maximum rate calculation
                total_fees = sum(fees.values())
                fee_rate_impact = total_fees / loan_amount if loan_amount > 0 else 0
                max_interest_rate = limits['maximum_apr'] - fee_rate_impact

                max_rates[jurisdiction] = max(0, max_interest_rate)
                applicable_limits[jurisdiction] = limits

        # Return the most restrictive limit
        if max_rates:
            min_jurisdiction = min(max_rates.keys(), key=lambda k: max_rates[k])
            return {
                'maximum_rate': max_rates[min_jurisdiction],
                'governing_jurisdiction': min_jurisdiction,
                'all_jurisdiction_limits': max_rates,
                'applicable_limits': applicable_limits
            }
        else:
            return {
                'maximum_rate': None,
                'governing_jurisdiction': None,
                'all_jurisdiction_limits': {},
                'applicable_limits': {}
            }

    async def _calculate_loan_metrics(self, loan_params: LoanParameters) -> Dict[str, Any]:
        """Calculate various loan metrics and APR"""
        # Basic calculations
        total_fees = sum(loan_params.fees.values())
        principal = loan_params.loan_amount

        # Calculate monthly payment
        monthly_rate = loan_params.interest_rate / 12
        num_payments = loan_params.loan_term_months

        if monthly_rate > 0:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                             ((1 + monthly_rate) ** num_payments - 1)
        else:
            monthly_payment = principal / num_payments

        # Calculate total cost
        total_payments = monthly_payment * num_payments
        total_interest = total_payments - principal
        total_cost = total_payments + total_fees

        # Calculate APR (including fees)
        # Simplified APR calculation - in practice would use more sophisticated method
        if principal > 0:
            effective_rate = (total_cost - principal) / principal
            apr = effective_rate * (12 / loan_params.loan_term_months)
        else:
            apr = 0.0

        # Calculate debt-to-income ratio if borrower income provided
        dti_ratio = None
        if loan_params.borrower_income and loan_params.borrower_income > 0:
            annual_payments = monthly_payment * 12
            dti_ratio = annual_payments / loan_params.borrower_income

        return {
            'principal': principal,
            'total_fees': total_fees,
            'monthly_payment': monthly_payment,
            'total_interest': total_interest,
            'total_cost': total_cost,
            'apr': apr,
            'effective_rate': effective_rate,
            'dti_ratio': dti_ratio,
            'fee_to_principal_ratio': total_fees / principal if principal > 0 else 0,
            'calculation_method': 'actuarial'
        }

    async def _validate_jurisdiction(
        self,
        loan_params: LoanParameters,
        jurisdiction: str,
        calculations: Dict[str, Any],
        borrower_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate loan against a specific jurisdiction"""
        issues = []

        # Get jurisdiction profile
        profile = self.jurisdiction_manager.get_jurisdiction_profile(jurisdiction)
        if not profile:
            return {
                'issues': [ValidationIssue(
                    issue_id=f"UNKNOWN_JURISDICTION_{jurisdiction}",
                    severity=ValidationSeverity.ERROR,
                    issue_type="jurisdiction_error",
                    jurisdiction=jurisdiction,
                    rule_reference="UNKNOWN",
                    description=f"Unknown jurisdiction: {jurisdiction}",
                    remediation_suggestion="Verify jurisdiction code"
                )]
            }

        # Check rate limits
        rate_limits = self.jurisdiction_manager.get_applicable_rate_limits(
            [jurisdiction], loan_params.loan_type, loan_params.loan_amount
        )

        apr = calculations['apr']

        # Maximum APR check
        if rate_limits.get('maximum_apr') is not None:
            if apr > rate_limits['maximum_apr']:
                issues.append(ValidationIssue(
                    issue_id=f"USURY_VIOLATION_{jurisdiction}",
                    severity=ValidationSeverity.CRITICAL,
                    issue_type="usury_violation",
                    jurisdiction=jurisdiction,
                    rule_reference="USURY_LAW",
                    description=f"APR {apr:.2%} exceeds maximum allowed {rate_limits['maximum_apr']:.2%}",
                    current_value=apr,
                    limit_value=rate_limits['maximum_apr'],
                    remediation_suggestion="Reduce interest rate or fees to comply with usury laws"
                ))

        # Criminal usury check
        if rate_limits.get('criminal_usury_threshold') is not None:
            if apr > rate_limits['criminal_usury_threshold']:
                issues.append(ValidationIssue(
                    issue_id=f"CRIMINAL_USURY_{jurisdiction}",
                    severity=ValidationSeverity.CRITICAL,
                    issue_type="criminal_usury",
                    jurisdiction=jurisdiction,
                    rule_reference="CRIMINAL_CODE",
                    description=f"APR {apr:.2%} exceeds criminal usury threshold {rate_limits['criminal_usury_threshold']:.2%}",
                    current_value=apr,
                    limit_value=rate_limits['criminal_usury_threshold'],
                    remediation_suggestion="Immediately reduce rate below criminal threshold",
                    legal_reference="Violation may result in criminal penalties"
                ))

        # Warning threshold check
        if rate_limits.get('warning_threshold') is not None:
            if apr > rate_limits['warning_threshold']:
                issues.append(ValidationIssue(
                    issue_id=f"HIGH_RATE_WARNING_{jurisdiction}",
                    severity=ValidationSeverity.WARNING,
                    issue_type="high_rate",
                    jurisdiction=jurisdiction,
                    rule_reference="POLICY",
                    description=f"APR {apr:.2%} is above recommended threshold {rate_limits['warning_threshold']:.2%}",
                    current_value=apr,
                    limit_value=rate_limits['warning_threshold'],
                    remediation_suggestion="Consider reducing rate for better compliance"
                ))

        return {
            'issues': issues,
            'applicable_limits': rate_limits,
            'jurisdiction_profile': profile.jurisdiction_config.jurisdiction_name
        }

    async def _validate_cross_jurisdiction(
        self,
        loan_params: LoanParameters,
        jurisdictions: List[str],
        calculations: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate cross-jurisdiction compliance"""
        issues = []

        # Check for conflicting requirements
        if len(jurisdictions) > 1:
            all_limits = {}
            for jurisdiction in jurisdictions:
                limits = self.jurisdiction_manager.get_applicable_rate_limits(
                    [jurisdiction], loan_params.loan_type, loan_params.loan_amount
                )
                all_limits[jurisdiction] = limits

            # Find conflicts
            max_rates = {j: limits.get('maximum_apr') for j, limits in all_limits.items()
                        if limits.get('maximum_apr') is not None}

            if len(set(max_rates.values())) > 1:  # Different rate limits
                min_rate = min(max_rates.values())
                governing_jurisdiction = [j for j, rate in max_rates.items() if rate == min_rate][0]

                issues.append(ValidationIssue(
                    issue_id="CROSS_JURISDICTION_CONFLICT",
                    severity=ValidationSeverity.INFO,
                    issue_type="cross_jurisdiction",
                    jurisdiction="MULTIPLE",
                    rule_reference="CONFLICT_RESOLUTION",
                    description=f"Multiple jurisdictions apply. Most restrictive: {governing_jurisdiction} ({min_rate:.2%})",
                    limit_value=min_rate,
                    remediation_suggestion=f"Apply {governing_jurisdiction} limits for compliance"
                ))

        return issues

    async def _check_predatory_lending(
        self,
        loan_params: LoanParameters,
        calculations: Dict[str, Any],
        borrower_info: Optional[Dict[str, Any]]
    ) -> List[ValidationIssue]:
        """Check for predatory lending indicators"""
        issues = []

        # Check DTI ratio
        if calculations.get('dti_ratio') is not None:
            dti_threshold = self.constants.CONSUMER_PROTECTION['predatory_lending_checks']['debt_to_income_ratio_max']
            if calculations['dti_ratio'] > dti_threshold:
                issues.append(ValidationIssue(
                    issue_id="EXCESSIVE_DTI",
                    severity=ValidationSeverity.WARNING,
                    issue_type="predatory_lending",
                    jurisdiction="FEDERAL",
                    rule_reference="ABILITY_TO_REPAY",
                    description=f"Debt-to-income ratio {calculations['dti_ratio']:.1%} exceeds safe threshold {dti_threshold:.1%}",
                    current_value=calculations['dti_ratio'],
                    limit_value=dti_threshold,
                    remediation_suggestion="Verify borrower's ability to repay"
                ))

        # Check fee-to-principal ratio
        fee_ratio = calculations.get('fee_to_principal_ratio', 0)
        fee_threshold = self.constants.CONSUMER_PROTECTION['predatory_lending_checks']['points_and_fees_cap']
        if fee_ratio > fee_threshold:
            issues.append(ValidationIssue(
                issue_id="EXCESSIVE_FEES",
                severity=ValidationSeverity.WARNING,
                issue_type="predatory_lending",
                jurisdiction="FEDERAL",
                rule_reference="POINTS_AND_FEES",
                description=f"Fees {fee_ratio:.1%} of principal exceed threshold {fee_threshold:.1%}",
                current_value=fee_ratio,
                limit_value=fee_threshold,
                remediation_suggestion="Reduce fees to comply with points and fees cap"
            ))

        return issues

    async def _validate_fee_structure(
        self,
        loan_params: LoanParameters,
        jurisdictions: List[str]
    ) -> List[ValidationIssue]:
        """Validate fee structure against applicable limits"""
        issues = []

        for jurisdiction in jurisdictions:
            # Get maximum allowable fees
            max_fees = self.constants.calculate_maximum_fees(
                loan_params.loan_amount, jurisdiction
            )

            # Check each fee type
            for fee_type, fee_amount in loan_params.fees.items():
                if fee_type in max_fees:
                    if fee_amount > max_fees[fee_type]:
                        issues.append(ValidationIssue(
                            issue_id=f"EXCESSIVE_FEE_{fee_type.upper()}_{jurisdiction}",
                            severity=ValidationSeverity.ERROR,
                            issue_type="fee_violation",
                            jurisdiction=jurisdiction,
                            rule_reference="FEE_LIMITS",
                            description=f"{fee_type} ${fee_amount:.2f} exceeds maximum ${max_fees[fee_type]:.2f}",
                            current_value=fee_amount,
                            limit_value=max_fees[fee_type],
                            remediation_suggestion=f"Reduce {fee_type} to comply with {jurisdiction} limits"
                        ))

        return issues

    async def _get_required_disclosures(
        self,
        loan_params: LoanParameters,
        jurisdictions: List[str]
    ) -> List[str]:
        """Get all required disclosures"""
        return self.jurisdiction_manager.get_required_disclosures(
            jurisdictions, loan_params.loan_type, loan_params.loan_amount
        )

    async def _get_licensing_requirements(
        self,
        jurisdictions: List[str],
        loan_type: LoanType
    ) -> List[str]:
        """Get licensing requirements"""
        business_type = "crypto_lending" if loan_type in [LoanType.SECURED] else "lending"
        licensing_reqs = self.jurisdiction_manager.check_licensing_requirements(
            jurisdictions, business_type
        )

        # Flatten requirements
        all_requirements = set()
        for jurisdiction_reqs in licensing_reqs.values():
            all_requirements.update(jurisdiction_reqs)

        return list(all_requirements)

    def _calculate_compliance_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate overall compliance score"""
        if not issues:
            return 100.0

        # Weight issues by severity
        severity_weights = {
            ValidationSeverity.INFO: 0,
            ValidationSeverity.WARNING: 5,
            ValidationSeverity.ERROR: 15,
            ValidationSeverity.CRITICAL: 30
        }

        total_deduction = sum(severity_weights.get(issue.severity, 0) for issue in issues)
        score = max(0, 100 - total_deduction)

        return score

    async def _generate_recommendations(
        self,
        loan_params: LoanParameters,
        issues: List[ValidationIssue],
        calculations: Dict[str, Any]
    ) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []

        # Group issues by type
        issue_types = {}
        for issue in issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = []
            issue_types[issue.issue_type].append(issue)

        # Generate type-specific recommendations
        if 'usury_violation' in issue_types:
            max_violation = max(issue_types['usury_violation'],
                              key=lambda x: x.current_value - x.limit_value)
            rate_reduction = max_violation.current_value - max_violation.limit_value
            recommendations.append(
                f"Reduce APR by at least {rate_reduction:.2%} to comply with {max_violation.jurisdiction} usury laws"
            )

        if 'fee_violation' in issue_types:
            recommendations.append("Review and reduce excessive fees to meet regulatory limits")

        if 'predatory_lending' in issue_types:
            recommendations.append("Review loan terms for predatory lending indicators and consumer protection compliance")

        if 'high_rate' in issue_types:
            recommendations.append("Consider reducing interest rate to improve compliance score and reduce regulatory risk")

        # Add general recommendations
        if len(issues) > 5:
            recommendations.append("Consider comprehensive review of loan terms and regulatory compliance procedures")

        return recommendations