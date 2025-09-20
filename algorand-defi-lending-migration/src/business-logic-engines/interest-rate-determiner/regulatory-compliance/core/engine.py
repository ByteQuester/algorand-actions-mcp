"""
Regulatory Compliance Engine

Main engine interface for regulatory compliance in interest rate determination.
Provides comprehensive compliance checking, monitoring, and reporting capabilities
for lending platforms operating across multiple jurisdictions.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from .config import RegulatoryComplianceConfig, load_config
from .constants import RegulatoryComplianceConstants, LoanType
from .validator import ComplianceValidator, ValidationResult, LoanParameters
from .monitor import ComplianceMonitor, ComplianceAlert
from .jurisdictions import JurisdictionManager


class RegulatoryComplianceEngine:
    """
    Main engine for regulatory compliance in interest rate determination

    Provides comprehensive compliance validation, real-time monitoring,
    and regulatory reporting for lending platforms operating across
    multiple jurisdictions with varying regulatory requirements.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the regulatory compliance engine"""
        self.config = load_config(config_path)
        self.constants = RegulatoryComplianceConstants(config_path)
        self.validator = ComplianceValidator(self.config)
        self.monitor = ComplianceMonitor(self.config)
        self.jurisdiction_manager = JurisdictionManager(self.config)

        self.logger = logging.getLogger(__name__)
        self._initialized = False
        self._audit_trail = []

    async def initialize(self) -> None:
        """Initialize the engine and its components"""
        if self._initialized:
            return

        self.logger.info("Initializing Regulatory Compliance Engine")

        # Initialize monitoring if enabled
        if self.config.monitoring.enable_real_time_monitoring:
            await self.monitor.start_monitoring()

        # Register alert callbacks
        self.monitor.add_alert_callback(self._handle_compliance_alert)

        self._initialized = True
        self.logger.info("Regulatory Compliance Engine initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown the engine and cleanup resources"""
        self.logger.info("Shutting down Regulatory Compliance Engine")

        # Stop monitoring
        await self.monitor.stop_monitoring()

        self._initialized = False

    async def validate_interest_rate(
        self,
        interest_rate: float,
        loan_amount: float,
        loan_term_months: int,
        loan_type: LoanType,
        jurisdictions: List[str],
        fees: Optional[Dict[str, float]] = None,
        borrower_info: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate interest rate for regulatory compliance

        Args:
            interest_rate: Annual interest rate (as decimal, e.g., 0.15 for 15%)
            loan_amount: Loan amount in USD
            loan_term_months: Loan term in months
            loan_type: Type of loan
            jurisdictions: Applicable jurisdictions
            fees: Optional fees to include in APR calculation
            borrower_info: Optional borrower information

        Returns:
            ValidationResult: Comprehensive compliance validation result
        """
        if not self._initialized:
            await self.initialize()

        if fees is None:
            fees = {}

        # Create loan parameters
        loan_params = LoanParameters(
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            loan_term_months=loan_term_months,
            loan_type=loan_type,
            fees=fees,
            borrower_income=borrower_info.get('annual_income') if borrower_info else None,
            borrower_credit_score=borrower_info.get('credit_score') if borrower_info else None
        )

        # Perform validation
        result = await self.validator.validate_loan_compliance(
            loan_params, jurisdictions, borrower_info
        )

        # Log audit trail
        self._log_audit_event('rate_validation', {
            'loan_params': {
                'amount': loan_amount,
                'rate': interest_rate,
                'term': loan_term_months,
                'type': loan_type.value
            },
            'jurisdictions': jurisdictions,
            'result': {
                'is_compliant': result.is_compliant,
                'score': result.overall_score,
                'issues_count': len(result.issues)
            }
        })

        self.logger.info(
            f"Validated interest rate {interest_rate:.2%} for ${loan_amount:,.2f} loan. "
            f"Compliant: {result.is_compliant}, Score: {result.overall_score:.1f}"
        )

        return result

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
            Dict containing maximum rate and compliance information
        """
        if not self._initialized:
            await self.initialize()

        result = await self.validator.calculate_maximum_compliant_rate(
            loan_amount, loan_type, jurisdictions, fees
        )

        self.logger.info(
            f"Maximum compliant rate for ${loan_amount:,.2f} {loan_type.value} loan: "
            f"{result.get('maximum_rate', 'N/A'):.2%} "
            f"(governed by {result.get('governing_jurisdiction', 'N/A')})"
        )

        return result

    async def get_jurisdiction_requirements(
        self,
        jurisdictions: List[str],
        loan_type: LoanType,
        loan_amount: float
    ) -> Dict[str, Any]:
        """
        Get comprehensive regulatory requirements for jurisdictions

        Args:
            jurisdictions: List of jurisdiction codes
            loan_type: Type of loan
            loan_amount: Loan amount

        Returns:
            Dict containing all regulatory requirements
        """
        requirements = {
            'rate_limits': {},
            'required_disclosures': [],
            'licensing_requirements': {},
            'consumer_protection': {},
            'fee_limits': {},
            'jurisdiction_profiles': {}
        }

        # Get rate limits
        for jurisdiction in jurisdictions:
            rate_limits = self.jurisdiction_manager.get_applicable_rate_limits(
                [jurisdiction], loan_type, loan_amount
            )
            requirements['rate_limits'][jurisdiction] = rate_limits

            # Get jurisdiction profile
            profile = self.jurisdiction_manager.get_jurisdiction_profile(jurisdiction)
            if profile:
                requirements['jurisdiction_profiles'][jurisdiction] = {
                    'name': profile.jurisdiction_config.jurisdiction_name,
                    'type': profile.jurisdiction_config.jurisdiction_type,
                    'currency': profile.jurisdiction_config.currency,
                    'frameworks': profile.jurisdiction_config.applicable_frameworks
                }

        # Get disclosure requirements
        requirements['required_disclosures'] = self.jurisdiction_manager.get_required_disclosures(
            jurisdictions, loan_type, loan_amount
        )

        # Get licensing requirements
        requirements['licensing_requirements'] = self.jurisdiction_manager.check_licensing_requirements(
            jurisdictions
        )

        # Get consumer protection requirements
        requirements['consumer_protection'] = self.jurisdiction_manager.get_consumer_protection_requirements(
            jurisdictions, loan_type
        )

        # Get fee limits
        for jurisdiction in jurisdictions:
            fee_limits = self.constants.calculate_maximum_fees(loan_amount, jurisdiction)
            requirements['fee_limits'][jurisdiction] = fee_limits

        return requirements

    async def add_loan_to_monitoring(
        self,
        loan_id: str,
        loan_amount: float,
        interest_rate: float,
        loan_term_months: int,
        loan_type: LoanType,
        jurisdictions: List[str],
        fees: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Add a loan to regulatory compliance monitoring

        Args:
            loan_id: Unique loan identifier
            loan_amount: Loan amount
            interest_rate: Annual interest rate
            loan_term_months: Loan term in months
            loan_type: Type of loan
            jurisdictions: Applicable jurisdictions
            fees: Optional fees
        """
        if not self._initialized:
            await self.initialize()

        if fees is None:
            fees = {}

        loan_params = LoanParameters(
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            loan_term_months=loan_term_months,
            loan_type=loan_type,
            fees=fees
        )

        self.monitor.add_loan_to_monitoring(loan_id, loan_params, jurisdictions)

        self.logger.info(f"Added loan {loan_id} to compliance monitoring")

    async def remove_loan_from_monitoring(self, loan_id: str) -> None:
        """Remove a loan from compliance monitoring"""
        self.monitor.remove_loan_from_monitoring(loan_id)
        self.logger.info(f"Removed loan {loan_id} from compliance monitoring")

    async def check_loan_compliance(self, loan_id: str) -> ValidationResult:
        """Perform immediate compliance check for a monitored loan"""
        return await self.monitor.perform_compliance_check(loan_id)

    async def generate_compliance_report(
        self,
        report_type: str = "comprehensive",
        jurisdiction: Optional[str] = None,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Generate compliance report

        Args:
            report_type: Type of report (comprehensive, summary, audit)
            jurisdiction: Specific jurisdiction to focus on
            include_recommendations: Whether to include recommendations

        Returns:
            Dict containing compliance report data
        """
        if not self._initialized:
            await self.initialize()

        if report_type == "comprehensive":
            report = await self.monitor.generate_compliance_report(
                include_resolved_alerts=True,
                jurisdiction=jurisdiction
            )
        elif report_type == "summary":
            report = await self.monitor.generate_compliance_report(
                include_resolved_alerts=False,
                jurisdiction=jurisdiction
            )
        elif report_type == "audit":
            report = await self._generate_audit_report(jurisdiction)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        if include_recommendations:
            report['regulatory_recommendations'] = await self._generate_regulatory_recommendations()

        # Add engine metadata
        report['engine_info'] = {
            'engine_name': self.config.engine_name,
            'version': self.config.version,
            'report_type': report_type,
            'generated_by': 'RegulatoryComplianceEngine'
        }

        self.logger.info(f"Generated {report_type} compliance report")
        return report

    async def get_regulatory_updates(self) -> List[Dict[str, Any]]:
        """Get recent regulatory updates and changes"""
        updates = await self.monitor.check_regulatory_updates()

        return [
            {
                'update_id': update.update_id,
                'jurisdiction': update.jurisdiction,
                'regulation_type': update.regulation_type,
                'effective_date': update.effective_date.isoformat(),
                'description': update.description,
                'impact_assessment': update.impact_assessment,
                'action_required': update.action_required
            }
            for update in updates
        ]

    async def validate_fee_structure(
        self,
        fees: Dict[str, float],
        loan_amount: float,
        jurisdictions: List[str]
    ) -> Dict[str, Any]:
        """
        Validate fee structure against regulatory limits

        Args:
            fees: Fee structure to validate
            loan_amount: Loan amount
            jurisdictions: Applicable jurisdictions

        Returns:
            Dict containing validation results
        """
        validation_result = {
            'is_compliant': True,
            'violations': [],
            'warnings': [],
            'jurisdiction_limits': {}
        }

        for jurisdiction in jurisdictions:
            max_fees = self.constants.calculate_maximum_fees(loan_amount, jurisdiction)
            jurisdiction_violations = []

            for fee_type, fee_amount in fees.items():
                if fee_type in max_fees and fee_amount > max_fees[fee_type]:
                    violation = {
                        'fee_type': fee_type,
                        'current_amount': fee_amount,
                        'maximum_allowed': max_fees[fee_type],
                        'excess_amount': fee_amount - max_fees[fee_type]
                    }
                    jurisdiction_violations.append(violation)
                    validation_result['is_compliant'] = False

            if jurisdiction_violations:
                validation_result['violations'].append({
                    'jurisdiction': jurisdiction,
                    'violations': jurisdiction_violations
                })

            validation_result['jurisdiction_limits'][jurisdiction] = max_fees

        return validation_result

    async def check_predatory_lending_indicators(
        self,
        loan_amount: float,
        interest_rate: float,
        fees: Dict[str, float],
        borrower_income: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Check for predatory lending indicators

        Args:
            loan_amount: Loan amount
            interest_rate: Annual interest rate
            fees: Fee structure
            borrower_income: Optional borrower income

        Returns:
            Dict containing predatory lending analysis
        """
        total_fees = sum(fees.values())

        indicators = self.constants.is_predatory_lending_indicator(
            apr=interest_rate + (total_fees / loan_amount),
            loan_amount=loan_amount,
            borrower_income=borrower_income or 0,
            fees_total=total_fees
        )

        result = {
            'has_predatory_indicators': len(indicators) > 0,
            'indicators': indicators,
            'risk_level': 'high' if len(indicators) >= 3 else 'medium' if len(indicators) > 0 else 'low',
            'recommendations': []
        }

        # Generate recommendations based on indicators
        if 'excessive_interest_rate' in indicators:
            result['recommendations'].append("Reduce interest rate to below 36% APR threshold")

        if 'excessive_fees' in indicators:
            result['recommendations'].append("Reduce fees to reasonable levels")

        if 'excessive_debt_to_income' in indicators:
            result['recommendations'].append("Verify borrower's ability to repay")

        return result

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status and statistics"""
        return self.monitor.get_monitoring_statistics()

    async def _generate_audit_report(self, jurisdiction: Optional[str] = None) -> Dict[str, Any]:
        """Generate audit-specific compliance report"""
        base_report = await self.monitor.generate_compliance_report(
            include_resolved_alerts=True,
            jurisdiction=jurisdiction
        )

        # Add audit-specific information
        audit_report = {
            **base_report,
            'audit_metadata': {
                'audit_date': datetime.now().isoformat(),
                'audit_scope': jurisdiction if jurisdiction else 'all_jurisdictions',
                'audit_type': 'regulatory_compliance',
                'auditor': 'RegulatoryComplianceEngine'
            },
            'audit_trail': self._audit_trail[-100:],  # Last 100 events
            'compliance_controls': self._assess_compliance_controls(),
            'risk_assessment': await self._assess_regulatory_risks()
        }

        return audit_report

    def _assess_compliance_controls(self) -> Dict[str, Any]:
        """Assess the effectiveness of compliance controls"""
        return {
            'monitoring_enabled': self.config.monitoring.enable_real_time_monitoring,
            'audit_trail_enabled': self.config.audit.enable_audit_trail,
            'validation_strictness': 'strict' if self.config.validation.strict_validation else 'lenient',
            'jurisdictions_covered': len(self.config.get_applicable_jurisdictions()),
            'automated_alerts': len(self.monitor._alert_callbacks) > 0,
            'regulatory_update_monitoring': self.config.monitoring.enable_real_time_monitoring
        }

    async def _assess_regulatory_risks(self) -> Dict[str, Any]:
        """Assess current regulatory risks"""
        risks = {
            'high_risk_loans': 0,
            'jurisdiction_risks': {},
            'upcoming_regulatory_changes': 0,
            'compliance_gaps': []
        }

        # Analyze monitored loans for risks
        for loan in self.monitor._monitored_loans.values():
            if loan.compliance_score < 70:
                risks['high_risk_loans'] += 1

        # Check for jurisdiction-specific risks
        for jurisdiction in self.config.get_applicable_jurisdictions():
            jurisdiction_loans = [
                loan for loan in self.monitor._monitored_loans.values()
                if jurisdiction in loan.applicable_jurisdictions
            ]

            if jurisdiction_loans:
                avg_score = sum(loan.compliance_score for loan in jurisdiction_loans) / len(jurisdiction_loans)
                risks['jurisdiction_risks'][jurisdiction] = {
                    'average_compliance_score': avg_score,
                    'loan_count': len(jurisdiction_loans),
                    'risk_level': 'high' if avg_score < 70 else 'medium' if avg_score < 85 else 'low'
                }

        return risks

    async def _generate_regulatory_recommendations(self) -> List[str]:
        """Generate regulatory recommendations"""
        recommendations = []

        # Check monitoring statistics
        stats = self.monitor.get_monitoring_statistics()

        if stats.get('violations_detected', 0) > 0:
            recommendations.append("Review and address detected compliance violations")

        if stats.get('loans_monitored', 0) == 0:
            recommendations.append("Enable loan monitoring for proactive compliance management")

        # Check configuration
        if not self.config.monitoring.enable_real_time_monitoring:
            recommendations.append("Enable real-time compliance monitoring for better risk management")

        if not self.config.audit.enable_audit_trail:
            recommendations.append("Enable audit trail for regulatory reporting and compliance tracking")

        if len(self.config.get_applicable_jurisdictions()) < 2:
            recommendations.append("Consider multi-jurisdictional compliance for business expansion")

        return recommendations

    def _handle_compliance_alert(self, alert: ComplianceAlert) -> None:
        """Handle compliance alerts from monitoring system"""
        self.logger.warning(
            f"Compliance alert: {alert.event_type.value} - {alert.description} "
            f"(Jurisdiction: {alert.jurisdiction}, Severity: {alert.severity.value})"
        )

        # Log to audit trail
        self._log_audit_event('compliance_alert', {
            'alert_id': alert.alert_id,
            'event_type': alert.event_type.value,
            'severity': alert.severity.value,
            'jurisdiction': alert.jurisdiction,
            'description': alert.description
        })

    def _log_audit_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log event to audit trail"""
        if not self.config.audit.enable_audit_trail:
            return

        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details,
            'engine': 'RegulatoryComplianceEngine'
        }

        self._audit_trail.append(audit_entry)

        # Keep only recent entries to manage memory
        if len(self._audit_trail) > 10000:
            self._audit_trail = self._audit_trail[-5000:]