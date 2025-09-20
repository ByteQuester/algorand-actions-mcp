"""
Constants for Regulatory Compliance Engine

Defines regulatory constants, limits, and compliance parameters for
interest rate determination across different jurisdictions.
"""

from enum import Enum
from typing import Dict, Any, List
from pathlib import Path
import json


class ComplianceLevel(Enum):
    """Compliance check severity levels"""
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


class LoanType(Enum):
    """Types of loans for regulatory classification"""
    PERSONAL = "personal"
    BUSINESS = "business"
    SECURED = "secured"
    UNSECURED = "unsecured"
    PAYDAY = "payday"
    INSTALLMENT = "installment"
    REVOLVING = "revolving"


class JurisdictionType(Enum):
    """Types of jurisdictions"""
    FEDERAL = "federal"
    STATE = "state"
    MUNICIPAL = "municipal"
    INTERNATIONAL = "international"


class RegulatoryFramework(Enum):
    """Regulatory frameworks"""
    TILA = "truth_in_lending_act"  # US Truth in Lending Act
    GDPR = "general_data_protection_regulation"  # EU GDPR
    PCI_DSS = "payment_card_industry"  # Payment Card Industry
    SOX = "sarbanes_oxley"  # Sarbanes-Oxley Act
    CCPA = "california_consumer_privacy_act"  # California Consumer Privacy Act
    MLD = "mortgage_lending_directive"  # EU Mortgage Lending Directive
    CRA = "community_reinvestment_act"  # US Community Reinvestment Act


class RegulatoryComplianceConstants:
    """
    Configurable constants for regulatory compliance
    """

    def __init__(self, config_path: Path = None):
        """Initialize with optional config file override"""
        self.config_path = config_path
        self._load_constants()

    def _load_constants(self):
        """Load constants from config file or use defaults"""
        if self.config_path and self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                constants = config.get('compliance_constants', {})
        else:
            constants = {}

        # US Federal Usury Laws (by jurisdiction)
        self.US_FEDERAL_LIMITS = constants.get('us_federal_limits', {
            'maximum_apr': 0.36,  # 36% APR for service members (MLA)
            'payday_loan_cap': 0.36,  # Federal payday loan cap
            'small_dollar_loan_cap': 0.28,  # 28% for small dollar loans
            'credit_card_penalty_apr': 0.2999  # Credit card penalty APR limit
        })

        # US State Usury Laws (examples - would need complete database)
        self.US_STATE_LIMITS = constants.get('us_state_limits', {
            'NY': {'max_apr': 0.16, 'criminal_usury': 0.25},  # New York
            'CA': {'max_apr': 0.10, 'above_2500': 0.12},      # California
            'TX': {'max_apr': 0.10, 'above_2500': 0.18},      # Texas
            'FL': {'max_apr': 0.18, 'criminal_usury': 0.45},  # Florida
            'DE': {'max_apr': 0.05, 'above_100k': None},      # Delaware (no limit for large loans)
            'SD': {'max_apr': None}  # South Dakota (no usury laws)
        })

        # EU Interest Rate Regulations
        self.EU_REGULATIONS = constants.get('eu_regulations', {
            'mortgage_lending_directive': {
                'max_apr_consumer': 0.15,  # 15% for consumer credit
                'max_fees_ratio': 0.03,    # 3% of loan amount
                'cooling_off_period': 14   # 14 days
            },
            'consumer_credit_directive': {
                'min_loan_amount': 200,    # €200 minimum
                'max_loan_amount': 75000,  # €75,000 maximum
                'max_total_cost': 1.0      # 100% of principal
            }
        })

        # APR Calculation Standards
        self.APR_CALCULATION = constants.get('apr_calculation', {
            'compounding_frequency': 'daily',  # daily, monthly, annual
            'fee_inclusion': [
                'origination_fee',
                'processing_fee',
                'application_fee',
                'credit_check_fee'
            ],
            'excluded_fees': [
                'late_payment_fee',
                'returned_payment_fee',
                'insurance_premium'
            ],
            'rounding_precision': 3  # 3 decimal places
        })

        # Consumer Protection Requirements
        self.CONSUMER_PROTECTION = constants.get('consumer_protection', {
            'truth_in_lending': {
                'apr_disclosure_required': True,
                'total_cost_disclosure': True,
                'payment_schedule_required': True,
                'right_to_cancel_period': 3  # 3 business days
            },
            'fair_lending': {
                'prohibited_discrimination': [
                    'race', 'color', 'religion', 'national_origin',
                    'sex', 'marital_status', 'age', 'disability'
                ],
                'disparate_impact_monitoring': True,
                'adverse_action_notice_required': True
            },
            'predatory_lending_checks': {
                'debt_to_income_ratio_max': 0.43,  # 43% DTI ratio
                'points_and_fees_cap': 0.03,       # 3% of loan amount
                'balloon_payment_restrictions': True,
                'prepayment_penalty_limits': True
            }
        })

        # Anti-Money Laundering (AML) Requirements
        self.AML_REQUIREMENTS = constants.get('aml_requirements', {
            'customer_due_diligence': {
                'identity_verification_required': True,
                'beneficial_ownership_threshold': 0.25,  # 25% ownership
                'enhanced_due_diligence_threshold': 10000  # $10,000
            },
            'suspicious_activity_reporting': {
                'transaction_monitoring_required': True,
                'sar_filing_threshold': 5000,  # $5,000
                'cash_transaction_reporting': 10000  # $10,000
            },
            'record_keeping': {
                'transaction_record_retention': 5,  # 5 years
                'customer_record_retention': 5,     # 5 years
                'compliance_record_retention': 7    # 7 years
            }
        })

        # Know Your Customer (KYC) Requirements
        self.KYC_REQUIREMENTS = constants.get('kyc_requirements', {
            'identity_verification': {
                'government_id_required': True,
                'address_verification_required': True,
                'phone_verification_required': True,
                'email_verification_required': True
            },
            'risk_assessment': {
                'politically_exposed_person_check': True,
                'sanctions_list_screening': True,
                'adverse_media_screening': True,
                'risk_scoring_required': True
            },
            'ongoing_monitoring': {
                'transaction_monitoring': True,
                'periodic_review_frequency': 12,  # 12 months
                'high_risk_review_frequency': 6   # 6 months
            }
        })

        # Data Protection and Privacy
        self.DATA_PROTECTION = constants.get('data_protection', {
            'gdpr_compliance': {
                'consent_required': True,
                'data_minimization': True,
                'right_to_erasure': True,
                'data_portability': True,
                'privacy_by_design': True
            },
            'ccpa_compliance': {
                'disclosure_requirements': True,
                'opt_out_rights': True,
                'deletion_rights': True,
                'non_discrimination': True
            },
            'data_retention': {
                'loan_application_data': 25,   # 25 months
                'loan_servicing_data': 84,     # 84 months (7 years)
                'marketing_data': 36,          # 36 months
                'compliance_data': 84          # 84 months (7 years)
            }
        })

        # Cryptocurrency-Specific Regulations
        self.CRYPTO_REGULATIONS = constants.get('crypto_regulations', {
            'licensing_requirements': {
                'money_transmitter_license': True,
                'virtual_currency_license': True,
                'lending_license_required': True
            },
            'reporting_requirements': {
                'large_transaction_reporting': 10000,  # $10,000
                'suspicious_activity_monitoring': True,
                'tax_reporting_required': True
            },
            'custody_requirements': {
                'segregated_custody_required': True,
                'insurance_required': True,
                'audit_requirements': True
            }
        })

        # Algorithmic Trading and AI Regulations
        self.ALGORITHMIC_REGULATIONS = constants.get('algorithmic_regulations', {
            'model_governance': {
                'model_validation_required': True,
                'bias_testing_required': True,
                'explainability_required': True,
                'regular_model_review': True
            },
            'fair_lending_ai': {
                'disparate_impact_testing': True,
                'protected_class_monitoring': True,
                'adverse_action_explanations': True
            }
        })

        # Audit and Reporting Requirements
        self.AUDIT_REQUIREMENTS = constants.get('audit_requirements', {
            'external_audit_frequency': 12,  # 12 months
            'internal_audit_frequency': 6,   # 6 months
            'regulatory_reporting_frequency': 3,  # 3 months
            'compliance_testing_frequency': 1     # 1 month
        })

        # Stress Testing Requirements
        self.STRESS_TESTING = constants.get('stress_testing', {
            'frequency': 12,  # 12 months
            'scenarios': [
                'baseline',
                'adverse',
                'severely_adverse'
            ],
            'capital_adequacy_ratio_min': 0.08,  # 8% minimum
            'leverage_ratio_min': 0.04           # 4% minimum
        })

        # Cross-Border Lending Regulations
        self.CROSS_BORDER = constants.get('cross_border', {
            'licensing_reciprocity': False,
            'local_licensing_required': True,
            'currency_restrictions': True,
            'withholding_tax_compliance': True
        })

    def get_jurisdiction_limits(self, jurisdiction: str, loan_type: LoanType) -> Dict[str, Any]:
        """Get rate limits for a specific jurisdiction and loan type"""
        jurisdiction = jurisdiction.upper()

        # Check US state limits
        if jurisdiction in self.US_STATE_LIMITS:
            return self.US_STATE_LIMITS[jurisdiction]

        # Check US federal limits
        if jurisdiction in ['US', 'USA', 'FEDERAL']:
            return self.US_FEDERAL_LIMITS

        # Check EU regulations
        if jurisdiction in ['EU', 'EUR', 'EUROPE']:
            return self.EU_REGULATIONS

        # Default to conservative limits
        return {
            'max_apr': 0.15,  # 15% default maximum
            'criminal_usury': 0.25,
            'warning_threshold': 0.12
        }

    def get_compliance_thresholds(self, framework: RegulatoryFramework) -> Dict[str, Any]:
        """Get compliance thresholds for a regulatory framework"""
        framework_map = {
            RegulatoryFramework.TILA: self.CONSUMER_PROTECTION['truth_in_lending'],
            RegulatoryFramework.GDPR: self.DATA_PROTECTION['gdpr_compliance'],
            RegulatoryFramework.CCPA: self.DATA_PROTECTION['ccpa_compliance']
        }

        return framework_map.get(framework, {})

    def get_disclosure_requirements(self, jurisdiction: str, loan_type: LoanType) -> List[str]:
        """Get required disclosures for jurisdiction and loan type"""
        base_disclosures = [
            'annual_percentage_rate',
            'total_cost_of_credit',
            'payment_schedule',
            'late_payment_fees',
            'prepayment_terms'
        ]

        # Add jurisdiction-specific requirements
        if jurisdiction.upper() in ['US', 'USA']:
            base_disclosures.extend([
                'right_to_cancel',
                'credit_score_impact',
                'complaint_procedures'
            ])

        if jurisdiction.upper() in ['EU', 'EUR']:
            base_disclosures.extend([
                'cooling_off_period',
                'right_of_withdrawal',
                'early_repayment_rights'
            ])

        # Add loan type specific requirements
        if loan_type == LoanType.SECURED:
            base_disclosures.extend([
                'collateral_description',
                'foreclosure_procedures',
                'insurance_requirements'
            ])

        return base_disclosures

    def calculate_maximum_fees(self, loan_amount: float, jurisdiction: str) -> Dict[str, float]:
        """Calculate maximum allowable fees for a loan"""
        limits = self.get_jurisdiction_limits(jurisdiction, LoanType.PERSONAL)

        max_fees = {
            'origination_fee': loan_amount * 0.05,  # 5% default
            'processing_fee': min(500, loan_amount * 0.02),  # Lesser of $500 or 2%
            'late_fee': min(50, loan_amount * 0.05),  # Lesser of $50 or 5%
            'returned_payment_fee': 25
        }

        # Apply jurisdiction-specific limits
        if 'max_fees_ratio' in limits:
            total_fees_limit = loan_amount * limits['max_fees_ratio']
            current_total = sum(max_fees.values())

            if current_total > total_fees_limit:
                # Scale down proportionally
                scale_factor = total_fees_limit / current_total
                for fee_type in max_fees:
                    max_fees[fee_type] *= scale_factor

        return max_fees

    def is_predatory_lending_indicator(
        self,
        apr: float,
        loan_amount: float,
        borrower_income: float,
        fees_total: float
    ) -> List[str]:
        """Check for predatory lending indicators"""
        indicators = []

        # High APR check
        if apr > 0.36:  # 36% threshold
            indicators.append('excessive_interest_rate')

        # High fees relative to loan amount
        if fees_total / loan_amount > 0.05:  # 5% threshold
            indicators.append('excessive_fees')

        # Debt-to-income ratio check
        if borrower_income > 0:
            monthly_payment = loan_amount * (apr / 12) / (1 - (1 + apr / 12) ** -12)
            dti_ratio = (monthly_payment * 12) / borrower_income

            if dti_ratio > self.CONSUMER_PROTECTION['predatory_lending_checks']['debt_to_income_ratio_max']:
                indicators.append('excessive_debt_to_income')

        # Points and fees check
        if fees_total / loan_amount > self.CONSUMER_PROTECTION['predatory_lending_checks']['points_and_fees_cap']:
            indicators.append('excessive_points_and_fees')

        return indicators