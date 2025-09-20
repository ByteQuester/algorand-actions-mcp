"""
Jurisdiction Manager

Manages jurisdiction-specific regulatory requirements, limits, and compliance rules
for interest rate determination across different legal frameworks.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass

from .config import JurisdictionConfig, RegulatoryComplianceConfig
from .constants import RegulatoryComplianceConstants, LoanType, RegulatoryFramework


@dataclass
class ComplianceRule:
    """Represents a specific compliance rule"""
    rule_id: str
    rule_name: str
    jurisdiction: str
    framework: str
    rule_type: str  # usury, disclosure, fee_limit, etc.
    description: str
    threshold_value: Optional[float] = None
    threshold_type: str = "max"  # max, min, exact
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    exceptions: List[str] = None
    penalties: Dict[str, Any] = None

    def __post_init__(self):
        if self.exceptions is None:
            self.exceptions = []
        if self.penalties is None:
            self.penalties = {}


@dataclass
class JurisdictionProfile:
    """Complete regulatory profile for a jurisdiction"""
    jurisdiction_config: JurisdictionConfig
    compliance_rules: List[ComplianceRule]
    rate_limits: Dict[str, float]
    fee_limits: Dict[str, float]
    disclosure_requirements: List[str]
    licensing_requirements: List[str]
    last_updated: datetime


class JurisdictionManager:
    """
    Manages regulatory compliance across multiple jurisdictions
    """

    def __init__(self, config: RegulatoryComplianceConfig):
        """Initialize the jurisdiction manager"""
        self.config = config
        self.constants = RegulatoryComplianceConstants()
        self.logger = logging.getLogger(__name__)

        # Jurisdiction data
        self._jurisdiction_profiles: Dict[str, JurisdictionProfile] = {}
        self._compliance_rules: Dict[str, List[ComplianceRule]] = {}
        self._regulatory_updates: List[Dict[str, Any]] = []

        # Load built-in jurisdictions
        self._load_built_in_jurisdictions()

    def add_jurisdiction(self, jurisdiction_config: JurisdictionConfig) -> None:
        """Add a jurisdiction to the manager"""
        # Create jurisdiction profile
        profile = JurisdictionProfile(
            jurisdiction_config=jurisdiction_config,
            compliance_rules=self._load_jurisdiction_rules(jurisdiction_config.jurisdiction_code),
            rate_limits=self._get_jurisdiction_rate_limits(jurisdiction_config.jurisdiction_code),
            fee_limits=self._get_jurisdiction_fee_limits(jurisdiction_config.jurisdiction_code),
            disclosure_requirements=jurisdiction_config.mandatory_disclosures,
            licensing_requirements=jurisdiction_config.required_licenses,
            last_updated=datetime.now()
        )

        self._jurisdiction_profiles[jurisdiction_config.jurisdiction_code] = profile
        self.logger.info(f"Added jurisdiction: {jurisdiction_config.jurisdiction_name} ({jurisdiction_config.jurisdiction_code})")

    def get_jurisdiction_profile(self, jurisdiction_code: str) -> Optional[JurisdictionProfile]:
        """Get complete profile for a jurisdiction"""
        return self._jurisdiction_profiles.get(jurisdiction_code)

    def get_applicable_rate_limits(
        self,
        jurisdiction_codes: List[str],
        loan_type: LoanType,
        loan_amount: float
    ) -> Dict[str, Any]:
        """
        Get applicable rate limits across multiple jurisdictions

        Args:
            jurisdiction_codes: List of applicable jurisdictions
            loan_type: Type of loan
            loan_amount: Loan amount

        Returns:
            Dict containing the most restrictive limits
        """
        limits = {
            'maximum_apr': float('inf'),
            'criminal_usury_threshold': float('inf'),
            'warning_threshold': float('inf'),
            'governing_jurisdiction': None,
            'applicable_rules': []
        }

        for jurisdiction_code in jurisdiction_codes:
            profile = self._jurisdiction_profiles.get(jurisdiction_code)
            if not profile:
                self.logger.warning(f"No profile found for jurisdiction: {jurisdiction_code}")
                continue

            # Get jurisdiction-specific limits
            jurisdiction_limits = self._get_jurisdiction_rate_limits(jurisdiction_code)

            # Check for loan-type specific limits
            loan_type_limits = self._get_loan_type_limits(jurisdiction_code, loan_type, loan_amount)
            jurisdiction_limits.update(loan_type_limits)

            # Apply most restrictive limits
            for limit_type, value in jurisdiction_limits.items():
                if value is not None and value < limits.get(limit_type, float('inf')):
                    limits[limit_type] = value
                    limits['governing_jurisdiction'] = jurisdiction_code

            # Collect applicable rules
            rules = self._get_applicable_rules(jurisdiction_code, loan_type, loan_amount)
            limits['applicable_rules'].extend(rules)

        # Clean up infinite values
        for key, value in limits.items():
            if value == float('inf'):
                limits[key] = None

        return limits

    def validate_interest_rate(
        self,
        interest_rate: float,
        jurisdiction_codes: List[str],
        loan_type: LoanType,
        loan_amount: float,
        fees: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Validate interest rate against all applicable jurisdictions

        Args:
            interest_rate: Proposed interest rate (APR)
            jurisdiction_codes: Applicable jurisdictions
            loan_type: Type of loan
            loan_amount: Loan amount
            fees: Optional fees to include in APR calculation

        Returns:
            Validation result with compliance status
        """
        if fees is None:
            fees = {}

        # Calculate total APR including fees
        total_apr = self._calculate_total_apr(interest_rate, fees, loan_amount)

        validation_result = {
            'is_compliant': True,
            'violations': [],
            'warnings': [],
            'governing_limits': {},
            'calculated_apr': total_apr,
            'jurisdiction_results': {}
        }

        # Check each jurisdiction
        for jurisdiction_code in jurisdiction_codes:
            jurisdiction_result = self._validate_jurisdiction_compliance(
                total_apr, jurisdiction_code, loan_type, loan_amount, fees
            )

            validation_result['jurisdiction_results'][jurisdiction_code] = jurisdiction_result

            # Aggregate violations and warnings
            if not jurisdiction_result['is_compliant']:
                validation_result['is_compliant'] = False
                validation_result['violations'].extend(jurisdiction_result['violations'])

            validation_result['warnings'].extend(jurisdiction_result['warnings'])

        return validation_result

    def get_required_disclosures(
        self,
        jurisdiction_codes: List[str],
        loan_type: LoanType,
        loan_amount: float
    ) -> List[str]:
        """Get all required disclosures across jurisdictions"""
        all_disclosures = set()

        for jurisdiction_code in jurisdiction_codes:
            profile = self._jurisdiction_profiles.get(jurisdiction_code)
            if profile:
                # Add base disclosures
                all_disclosures.update(profile.disclosure_requirements)

                # Add loan-type specific disclosures
                specific_disclosures = self._get_loan_type_disclosures(
                    jurisdiction_code, loan_type, loan_amount
                )
                all_disclosures.update(specific_disclosures)

        return list(all_disclosures)

    def check_licensing_requirements(
        self,
        jurisdiction_codes: List[str],
        business_type: str = "lending"
    ) -> Dict[str, List[str]]:
        """Check licensing requirements across jurisdictions"""
        licensing_requirements = {}

        for jurisdiction_code in jurisdiction_codes:
            profile = self._jurisdiction_profiles.get(jurisdiction_code)
            if profile:
                requirements = profile.licensing_requirements.copy()

                # Add business-type specific requirements
                if business_type == "crypto_lending":
                    requirements.extend([
                        "virtual_currency_license",
                        "money_transmitter_license"
                    ])

                licensing_requirements[jurisdiction_code] = list(set(requirements))

        return licensing_requirements

    def get_consumer_protection_requirements(
        self,
        jurisdiction_codes: List[str],
        loan_type: LoanType
    ) -> Dict[str, Any]:
        """Get consumer protection requirements"""
        protection_requirements = {
            'cooling_off_period_days': 0,
            'right_to_cancel_days': 0,
            'adverse_action_notice_required': False,
            'credit_counseling_required': False,
            'ability_to_repay_verification': False,
            'debt_to_income_limits': {},
            'prohibited_practices': []
        }

        for jurisdiction_code in jurisdiction_codes:
            profile = self._jurisdiction_profiles.get(jurisdiction_code)
            if profile:
                config = profile.jurisdiction_config

                # Take maximum protection periods
                protection_requirements['cooling_off_period_days'] = max(
                    protection_requirements['cooling_off_period_days'],
                    config.cooling_off_period_days
                )
                protection_requirements['right_to_cancel_days'] = max(
                    protection_requirements['right_to_cancel_days'],
                    config.right_to_cancel_period_days
                )

                # Check for additional requirements
                rules = self._get_applicable_rules(jurisdiction_code, loan_type, 0)
                for rule in rules:
                    if rule.rule_type == "consumer_protection":
                        if "adverse_action" in rule.rule_name.lower():
                            protection_requirements['adverse_action_notice_required'] = True
                        elif "credit_counseling" in rule.rule_name.lower():
                            protection_requirements['credit_counseling_required'] = True
                        elif "ability_to_repay" in rule.rule_name.lower():
                            protection_requirements['ability_to_repay_verification'] = True

        return protection_requirements

    def _load_built_in_jurisdictions(self) -> None:
        """Load built-in jurisdiction configurations"""
        # Load from config first
        for jurisdiction_code, jurisdiction_config in self.config.jurisdiction_configs.items():
            self.add_jurisdiction(jurisdiction_config)

        # Add additional built-in jurisdictions if not already present
        self._add_default_us_jurisdictions()
        self._add_default_eu_jurisdictions()

    def _add_default_us_jurisdictions(self) -> None:
        """Add default US jurisdictions"""
        # US Federal
        if "US" not in self._jurisdiction_profiles:
            us_federal = JurisdictionConfig(
                jurisdiction_code="US",
                jurisdiction_name="United States Federal",
                jurisdiction_type="federal",
                maximum_apr=0.36,  # MLA limit
                criminal_usury_threshold=0.45,
                applicable_frameworks=["TILA", "FCRA", "ECOA", "HMDA"],
                required_licenses=["money_transmitter"],
                mandatory_disclosures=[
                    "annual_percentage_rate",
                    "finance_charge",
                    "amount_financed",
                    "total_of_payments",
                    "payment_schedule"
                ],
                right_to_cancel_period_days=3
            )
            self.add_jurisdiction(us_federal)

        # New York
        if "NY" not in self._jurisdiction_profiles:
            ny_state = JurisdictionConfig(
                jurisdiction_code="NY",
                jurisdiction_name="New York",
                jurisdiction_type="state",
                maximum_apr=0.16,  # 16% general usury cap
                criminal_usury_threshold=0.25,  # 25% criminal usury
                small_loan_cap=0.30,  # 30% for loans under $25,000
                required_licenses=["ny_lending_license"],
                mandatory_disclosures=[
                    "total_cost_disclosure",
                    "payment_schedule",
                    "late_fee_disclosure"
                ]
            )
            self.add_jurisdiction(ny_state)

        # California
        if "CA" not in self._jurisdiction_profiles:
            ca_state = JurisdictionConfig(
                jurisdiction_code="CA",
                jurisdiction_name="California",
                jurisdiction_type="state",
                maximum_apr=0.10,  # 10% for loans under $2,500
                applicable_frameworks=["CCPA"],
                required_licenses=["ca_finance_lender_license"],
                mandatory_disclosures=[
                    "ccpa_privacy_notice",
                    "right_to_opt_out"
                ],
                cooling_off_period_days=7
            )
            self.add_jurisdiction(ca_state)

    def _add_default_eu_jurisdictions(self) -> None:
        """Add default EU jurisdictions"""
        if "EU" not in self._jurisdiction_profiles:
            eu_general = JurisdictionConfig(
                jurisdiction_code="EU",
                jurisdiction_name="European Union",
                jurisdiction_type="international",
                currency="EUR",
                maximum_apr=0.15,  # General consumer credit limit
                applicable_frameworks=["GDPR", "MLD", "CCD"],
                mandatory_disclosures=[
                    "secci_form",  # Standard European Consumer Credit Information
                    "right_of_withdrawal",
                    "early_repayment_rights"
                ],
                cooling_off_period_days=14,
                right_to_cancel_period_days=14
            )
            self.add_jurisdiction(eu_general)

    def _load_jurisdiction_rules(self, jurisdiction_code: str) -> List[ComplianceRule]:
        """Load compliance rules for a jurisdiction"""
        rules = []

        # Load rules based on jurisdiction
        if jurisdiction_code == "US":
            rules.extend(self._get_us_federal_rules())
        elif jurisdiction_code == "NY":
            rules.extend(self._get_ny_state_rules())
        elif jurisdiction_code == "CA":
            rules.extend(self._get_ca_state_rules())
        elif jurisdiction_code == "EU":
            rules.extend(self._get_eu_rules())

        return rules

    def _get_us_federal_rules(self) -> List[ComplianceRule]:
        """Get US federal compliance rules"""
        return [
            ComplianceRule(
                rule_id="US_MLA_001",
                rule_name="Military Lending Act APR Cap",
                jurisdiction="US",
                framework="MLA",
                rule_type="usury",
                description="36% APR cap for covered borrowers",
                threshold_value=0.36,
                threshold_type="max"
            ),
            ComplianceRule(
                rule_id="US_TILA_001",
                rule_name="Truth in Lending Act Disclosure",
                jurisdiction="US",
                framework="TILA",
                rule_type="disclosure",
                description="APR disclosure required within 0.125% accuracy"
            ),
            ComplianceRule(
                rule_id="US_ECOA_001",
                rule_name="Equal Credit Opportunity Act",
                jurisdiction="US",
                framework="ECOA",
                rule_type="fair_lending",
                description="Prohibition on discriminatory lending practices"
            )
        ]

    def _get_ny_state_rules(self) -> List[ComplianceRule]:
        """Get New York state compliance rules"""
        return [
            ComplianceRule(
                rule_id="NY_USURY_001",
                rule_name="New York General Usury Law",
                jurisdiction="NY",
                framework="NY_BANKING_LAW",
                rule_type="usury",
                description="16% maximum interest rate",
                threshold_value=0.16,
                threshold_type="max"
            ),
            ComplianceRule(
                rule_id="NY_CRIMINAL_001",
                rule_name="New York Criminal Usury",
                jurisdiction="NY",
                framework="NY_PENAL_LAW",
                rule_type="criminal_usury",
                description="25% criminal usury threshold",
                threshold_value=0.25,
                threshold_type="max"
            )
        ]

    def _get_ca_state_rules(self) -> List[ComplianceRule]:
        """Get California state compliance rules"""
        return [
            ComplianceRule(
                rule_id="CA_USURY_001",
                rule_name="California Constitutional Usury",
                jurisdiction="CA",
                framework="CA_CONSTITUTION",
                rule_type="usury",
                description="10% maximum for loans under $2,500",
                threshold_value=0.10,
                threshold_type="max"
            ),
            ComplianceRule(
                rule_id="CA_CCPA_001",
                rule_name="California Consumer Privacy Act",
                jurisdiction="CA",
                framework="CCPA",
                rule_type="privacy",
                description="Consumer privacy rights and disclosures"
            )
        ]

    def _get_eu_rules(self) -> List[ComplianceRule]:
        """Get EU compliance rules"""
        return [
            ComplianceRule(
                rule_id="EU_CCD_001",
                rule_name="Consumer Credit Directive",
                jurisdiction="EU",
                framework="CCD",
                rule_type="consumer_protection",
                description="14-day withdrawal period for credit agreements"
            ),
            ComplianceRule(
                rule_id="EU_GDPR_001",
                rule_name="General Data Protection Regulation",
                jurisdiction="EU",
                framework="GDPR",
                rule_type="data_protection",
                description="Data protection and privacy requirements"
            )
        ]

    def _get_jurisdiction_rate_limits(self, jurisdiction_code: str) -> Dict[str, float]:
        """Get rate limits for a jurisdiction"""
        return self.constants.get_jurisdiction_limits(jurisdiction_code, LoanType.PERSONAL)

    def _get_jurisdiction_fee_limits(self, jurisdiction_code: str) -> Dict[str, float]:
        """Get fee limits for a jurisdiction"""
        return self.constants.calculate_maximum_fees(10000, jurisdiction_code)  # Use $10k as baseline

    def _get_loan_type_limits(
        self,
        jurisdiction_code: str,
        loan_type: LoanType,
        loan_amount: float
    ) -> Dict[str, float]:
        """Get loan-type specific limits"""
        limits = {}

        # Payday loan specific limits
        if loan_type == LoanType.PAYDAY:
            if jurisdiction_code == "US":
                limits['maximum_apr'] = 0.36  # Federal payday loan cap

        # Small dollar loan limits
        if loan_amount < 2500:  # Small dollar threshold
            if jurisdiction_code == "CA":
                limits['maximum_apr'] = 0.10  # California small loan limit

        return limits

    def _get_applicable_rules(
        self,
        jurisdiction_code: str,
        loan_type: LoanType,
        loan_amount: float
    ) -> List[ComplianceRule]:
        """Get applicable compliance rules"""
        all_rules = self._compliance_rules.get(jurisdiction_code, [])
        applicable_rules = []

        for rule in all_rules:
            # Check if rule applies to this loan type and amount
            if self._rule_applies(rule, loan_type, loan_amount):
                applicable_rules.append(rule)

        return applicable_rules

    def _rule_applies(self, rule: ComplianceRule, loan_type: LoanType, loan_amount: float) -> bool:
        """Check if a rule applies to a specific loan"""
        # Check effective date
        if rule.effective_date and rule.effective_date > datetime.now():
            return False

        # Check expiration date
        if rule.expiration_date and rule.expiration_date < datetime.now():
            return False

        # Check exceptions
        if loan_type.value in rule.exceptions:
            return False

        # Rule applies by default
        return True

    def _get_loan_type_disclosures(
        self,
        jurisdiction_code: str,
        loan_type: LoanType,
        loan_amount: float
    ) -> List[str]:
        """Get loan-type specific disclosure requirements"""
        disclosures = []

        if loan_type == LoanType.SECURED:
            disclosures.extend([
                "collateral_description",
                "security_interest_disclosure",
                "default_consequences"
            ])

        if loan_type == LoanType.PAYDAY:
            disclosures.extend([
                "rollover_consequences",
                "alternative_sources_notice"
            ])

        return disclosures

    def _calculate_total_apr(
        self,
        interest_rate: float,
        fees: Dict[str, float],
        loan_amount: float
    ) -> float:
        """Calculate total APR including fees"""
        total_fees = sum(fees.values())
        return interest_rate + (total_fees / loan_amount)

    def _validate_jurisdiction_compliance(
        self,
        apr: float,
        jurisdiction_code: str,
        loan_type: LoanType,
        loan_amount: float,
        fees: Dict[str, float]
    ) -> Dict[str, Any]:
        """Validate compliance for a specific jurisdiction"""
        result = {
            'is_compliant': True,
            'violations': [],
            'warnings': [],
            'applicable_limits': {}
        }

        # Get jurisdiction limits
        limits = self._get_jurisdiction_rate_limits(jurisdiction_code)
        loan_type_limits = self._get_loan_type_limits(jurisdiction_code, loan_type, loan_amount)
        limits.update(loan_type_limits)

        # Check maximum APR
        if 'maximum_apr' in limits and limits['maximum_apr'] is not None:
            if apr > limits['maximum_apr']:
                result['is_compliant'] = False
                result['violations'].append({
                    'type': 'usury_violation',
                    'description': f"APR {apr:.2%} exceeds maximum {limits['maximum_apr']:.2%}",
                    'severity': 'high'
                })

        # Check criminal usury threshold
        if 'criminal_usury' in limits and limits['criminal_usury'] is not None:
            if apr > limits['criminal_usury']:
                result['violations'].append({
                    'type': 'criminal_usury',
                    'description': f"APR {apr:.2%} exceeds criminal usury threshold {limits['criminal_usury']:.2%}",
                    'severity': 'critical'
                })

        # Check warning threshold
        if 'warning_threshold' in limits and limits['warning_threshold'] is not None:
            if apr > limits['warning_threshold']:
                result['warnings'].append({
                    'type': 'high_rate_warning',
                    'description': f"APR {apr:.2%} is above recommended threshold {limits['warning_threshold']:.2%}"
                })

        result['applicable_limits'] = limits
        return result