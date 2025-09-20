"""
Conditions Generator for Holistic Loan Decisions

Generates specific loan conditions, monitoring requirements, and safeguards
based on holistic risk assessment and borrower profile analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from .decision_orchestrator import BorrowerProfile, LoanApplication


class ConditionType(Enum):
    """Types of loan conditions"""
    COLLATERAL = "collateral"
    MONITORING = "monitoring"
    BEHAVIORAL = "behavioral"
    FINANCIAL = "financial"
    GOVERNANCE = "governance"
    TECHNICAL = "technical"


class ConditionSeverity(Enum):
    """Severity levels for conditions"""
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class LoanCondition:
    """Individual loan condition with metadata"""

    def __init__(
        self,
        condition_type: ConditionType,
        severity: ConditionSeverity,
        description: str,
        rationale: str,
        monitoring_frequency: str = "monthly",
        auto_enforceable: bool = False,
        violation_consequences: List[str] = None
    ):
        self.condition_type = condition_type
        self.severity = severity
        self.description = description
        self.rationale = rationale
        self.monitoring_frequency = monitoring_frequency
        self.auto_enforceable = auto_enforceable
        self.violation_consequences = violation_consequences or []
        self.created_at = datetime.now()


class ConditionsGenerator:
    """
    Generates comprehensive loan conditions based on holistic risk assessment.

    Creates specific, actionable conditions that address identified risks
    while supporting borrower success in the Algorand ecosystem.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.loan_conditions = config.get('loan_conditions', {})
        self.monitoring_config = config.get('monitoring', {})
        self.logger = logging.getLogger("conditions_generator")

    async def generate_conditions(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[str]:
        """
        Generate comprehensive loan conditions based on holistic analysis.

        Returns list of condition descriptions for the loan agreement.
        """

        self.logger.info(f"Generating conditions for application {application.application_id}")

        # Generate condition objects
        conditions = await self._generate_condition_objects(
            holistic_scores, application, profile
        )

        # Convert to string descriptions for loan agreement
        condition_descriptions = []
        for condition in conditions:
            description = self._format_condition_description(condition)
            condition_descriptions.append(description)

        self.logger.info(f"Generated {len(condition_descriptions)} conditions")
        return condition_descriptions

    async def _generate_condition_objects(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[LoanCondition]:
        """Generate detailed condition objects"""

        conditions = []

        # 1. Collateral conditions
        collateral_conditions = self._generate_collateral_conditions(
            holistic_scores, application, profile
        )
        conditions.extend(collateral_conditions)

        # 2. Monitoring conditions
        monitoring_conditions = self._generate_monitoring_conditions(
            holistic_scores, application, profile
        )
        conditions.extend(monitoring_conditions)

        # 3. Behavioral conditions
        behavioral_conditions = self._generate_behavioral_conditions(
            holistic_scores, application, profile
        )
        conditions.extend(behavioral_conditions)

        # 4. Financial conditions
        financial_conditions = self._generate_financial_conditions(
            holistic_scores, application, profile
        )
        conditions.extend(financial_conditions)

        # 5. Governance conditions
        governance_conditions = self._generate_governance_conditions(
            holistic_scores, application, profile
        )
        conditions.extend(governance_conditions)

        # 6. Technical conditions
        technical_conditions = self._generate_technical_conditions(
            holistic_scores, application, profile
        )
        conditions.extend(technical_conditions)

        return conditions

    def _generate_collateral_conditions(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[LoanCondition]:
        """Generate collateral-related conditions"""

        conditions = []
        collateral_score = holistic_scores['engine_scores']['collateral_intelligence']['score']

        # Mandatory collateral maintenance
        conditions.append(LoanCondition(
            condition_type=ConditionType.COLLATERAL,
            severity=ConditionSeverity.MANDATORY,
            description="Maintain minimum collateral ratio of 150% throughout loan term",
            rationale="Ensures loan security and protects against market volatility",
            monitoring_frequency="real-time",
            auto_enforceable=True,
            violation_consequences=["Margin call", "Accelerated repayment", "Liquidation"]
        ))

        # Collateral quality conditions based on score
        if collateral_score < 0.6:
            conditions.append(LoanCondition(
                condition_type=ConditionType.COLLATERAL,
                severity=ConditionSeverity.MANDATORY,
                description="Provide additional collateral worth 25% of loan value within 30 days",
                rationale="Low collateral quality score requires additional security",
                monitoring_frequency="weekly",
                auto_enforceable=False,
                violation_consequences=["Loan recall", "Interest rate increase"]
            ))

        # Diversification requirements
        collateral_data = profile.collateral_data
        if collateral_data.get('diversification_score', 0) < 0.5:
            conditions.append(LoanCondition(
                condition_type=ConditionType.COLLATERAL,
                severity=ConditionSeverity.RECOMMENDED,
                description="Diversify collateral portfolio across at least 3 different asset types",
                rationale="Reduces concentration risk and improves portfolio stability",
                monitoring_frequency="monthly"
            ))

        # Liquid asset requirements
        if collateral_data.get('liquidity_score', 0) < 0.7:
            conditions.append(LoanCondition(
                condition_type=ConditionType.COLLATERAL,
                severity=ConditionSeverity.MANDATORY,
                description="Maintain at least 20% of collateral in highly liquid assets (ALGO, USDC)",
                rationale="Ensures ability to meet margin calls and reduces liquidation risk",
                monitoring_frequency="daily",
                auto_enforceable=True
            ))

        return conditions

    def _generate_monitoring_conditions(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[LoanCondition]:
        """Generate monitoring-related conditions"""

        conditions = []
        overall_score = holistic_scores['overall_score']
        confidence_level = holistic_scores['confidence_level']

        # Base monitoring frequency based on risk
        if overall_score < 0.5:
            monitoring_freq = "daily"
        elif overall_score < 0.7:
            monitoring_freq = "weekly"
        else:
            monitoring_freq = "monthly"

        conditions.append(LoanCondition(
            condition_type=ConditionType.MONITORING,
            severity=ConditionSeverity.MANDATORY,
            description=f"Submit {monitoring_freq} portfolio and activity reports",
            rationale="Enables proactive risk management and early intervention",
            monitoring_frequency=monitoring_freq,
            auto_enforceable=False
        ))

        # Enhanced monitoring for low confidence
        if confidence_level < 0.8:
            conditions.append(LoanCondition(
                condition_type=ConditionType.MONITORING,
                severity=ConditionSeverity.MANDATORY,
                description="Provide additional documentation on DeFi positions and strategies",
                rationale="Limited historical data requires enhanced ongoing monitoring",
                monitoring_frequency="weekly"
            ))

        # Real-time monitoring triggers
        conditions.append(LoanCondition(
            condition_type=ConditionType.MONITORING,
            severity=ConditionSeverity.MANDATORY,
            description="Enable real-time monitoring of all collateral wallets and DeFi positions",
            rationale="Allows for immediate response to market changes and risk events",
            monitoring_frequency="real-time",
            auto_enforceable=True,
            violation_consequences=["Immediate review", "Margin call"]
        ))

        return conditions

    def _generate_behavioral_conditions(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[LoanCondition]:
        """Generate behavioral conditions based on DeFi history"""

        conditions = []
        defi_score = holistic_scores['engine_scores']['defi_behavior']['score']
        defi_data = profile.defi_data

        # Risk management requirements for poor DeFi behavior
        if defi_score < 0.5:
            conditions.append(LoanCondition(
                condition_type=ConditionType.BEHAVIORAL,
                severity=ConditionSeverity.MANDATORY,
                description="Limit leverage usage to maximum 2x across all DeFi positions",
                rationale="Poor DeFi risk management history requires leverage restrictions",
                monitoring_frequency="daily",
                auto_enforceable=True,
                violation_consequences=["Position closure", "Interest penalty"]
            ))

        # Yield farming restrictions
        if defi_data.get('risk_management_score', 0) < 0.6:
            conditions.append(LoanCondition(
                condition_type=ConditionType.BEHAVIORAL,
                severity=ConditionSeverity.MANDATORY,
                description="Restrict high-risk yield farming strategies (>50% APY protocols)",
                rationale="History of poor risk management requires conservative strategies",
                monitoring_frequency="weekly"
            ))

        # Protocol diversification
        protocols_used = defi_data.get('protocols_used', 0)
        if protocols_used < 3:
            conditions.append(LoanCondition(
                condition_type=ConditionType.BEHAVIORAL,
                severity=ConditionSeverity.RECOMMENDED,
                description="Diversify DeFi activities across at least 3 established protocols",
                rationale="Protocol diversification reduces smart contract and platform risks",
                monitoring_frequency="monthly"
            ))

        # Education requirements for new users
        defi_experience = defi_data.get('defi_experience_months', 0)
        if defi_experience < 6:
            conditions.append(LoanCondition(
                condition_type=ConditionType.BEHAVIORAL,
                severity=ConditionSeverity.RECOMMENDED,
                description="Complete DeFi risk management course within 60 days",
                rationale="New DeFi users benefit from additional education",
                monitoring_frequency="one-time"
            ))

        return conditions

    def _generate_financial_conditions(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[LoanCondition]:
        """Generate financial conditions and requirements"""

        conditions = []
        overall_score = holistic_scores['overall_score']

        # Interest rate adjustments based on performance
        conditions.append(LoanCondition(
            condition_type=ConditionType.FINANCIAL,
            severity=ConditionSeverity.MANDATORY,
            description="Interest rate subject to quarterly review based on risk profile changes",
            rationale="Aligns pricing with current risk assessment",
            monitoring_frequency="quarterly"
        ))

        # Prepayment incentives for good performance
        if overall_score >= 0.8:
            conditions.append(LoanCondition(
                condition_type=ConditionType.FINANCIAL,
                severity=ConditionSeverity.OPTIONAL,
                description="Early repayment discount of 0.5% available after 6 months",
                rationale="Reward excellent borrower performance",
                monitoring_frequency="semi-annual"
            ))

        # Conservative terms for lower scores
        if overall_score < 0.6:
            conditions.append(LoanCondition(
                condition_type=ConditionType.FINANCIAL,
                severity=ConditionSeverity.MANDATORY,
                description="Monthly principal payments required (no interest-only periods)",
                rationale="Lower risk profile requires accelerated principal reduction",
                monitoring_frequency="monthly",
                auto_enforceable=True
            ))

        # Fee structures
        conditions.append(LoanCondition(
            condition_type=ConditionType.FINANCIAL,
            severity=ConditionSeverity.MANDATORY,
            description="Late payment fee of 2% applied to overdue amounts after 5-day grace period",
            rationale="Incentivizes timely payments and covers administrative costs",
            monitoring_frequency="daily",
            auto_enforceable=True
        ))

        return conditions

    def _generate_governance_conditions(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[LoanCondition]:
        """Generate governance-related conditions"""

        conditions = []
        governance_score = holistic_scores['engine_scores']['governance_reputation']['score']
        governance_data = profile.governance_data

        # Governance participation incentives
        if governance_score >= 0.7:
            conditions.append(LoanCondition(
                condition_type=ConditionType.GOVERNANCE,
                severity=ConditionSeverity.OPTIONAL,
                description="Interest rate discount of 0.25% for continued governance participation",
                rationale="Rewards community engagement and platform alignment",
                monitoring_frequency="quarterly"
            ))

        # Governance requirements for low participation
        if governance_score < 0.3:
            conditions.append(LoanCondition(
                condition_type=ConditionType.GOVERNANCE,
                severity=ConditionSeverity.RECOMMENDED,
                description="Participate in at least 50% of governance votes during loan term",
                rationale="Encourages ecosystem engagement and community responsibility",
                monitoring_frequency="quarterly"
            ))

        # Community standing requirements
        if not governance_data.get('governance_participation', False):
            conditions.append(LoanCondition(
                condition_type=ConditionType.GOVERNANCE,
                severity=ConditionSeverity.RECOMMENDED,
                description="Join Algorand governance program within 90 days",
                rationale="Aligns borrower interests with ecosystem health",
                monitoring_frequency="quarterly"
            ))

        return conditions

    def _generate_technical_conditions(
        self,
        holistic_scores: Dict[str, Any],
        application: LoanApplication,
        profile: BorrowerProfile
    ) -> List[LoanCondition]:
        """Generate technical and operational conditions"""

        conditions = []
        ecosystem_score = holistic_scores['engine_scores']['ecosystem_analysis']['score']

        # Wallet security requirements
        conditions.append(LoanCondition(
            condition_type=ConditionType.TECHNICAL,
            severity=ConditionSeverity.MANDATORY,
            description="Maintain collateral in hardware wallet or multi-signature setup",
            rationale="Reduces custody risk and ensures secure asset management",
            monitoring_frequency="monthly"
        ))

        # Smart contract interaction monitoring
        if ecosystem_score < 0.6:
            conditions.append(LoanCondition(
                condition_type=ConditionType.TECHNICAL,
                severity=ConditionSeverity.MANDATORY,
                description="Pre-approval required for interactions with new smart contracts",
                rationale="Limited ecosystem experience requires additional oversight",
                monitoring_frequency="real-time",
                auto_enforceable=True
            ))

        # API access and monitoring
        conditions.append(LoanCondition(
            condition_type=ConditionType.TECHNICAL,
            severity=ConditionSeverity.MANDATORY,
            description="Provide read-only API access to all wallets and DeFi positions",
            rationale="Enables continuous monitoring and risk assessment",
            monitoring_frequency="continuous",
            auto_enforceable=True,
            violation_consequences=["Monitoring failure", "Compliance breach"]
        ))

        # Insurance requirements for large loans
        if application.loan_amount > 100000:
            conditions.append(LoanCondition(
                condition_type=ConditionType.TECHNICAL,
                severity=ConditionSeverity.MANDATORY,
                description="Maintain smart contract insurance coverage of at least 50% of loan value",
                rationale="Large loans require additional protection against technical risks",
                monitoring_frequency="monthly"
            ))

        return conditions

    def _format_condition_description(self, condition: LoanCondition) -> str:
        """Format condition for loan agreement"""

        severity_prefix = {
            ConditionSeverity.MANDATORY: "REQUIRED:",
            ConditionSeverity.RECOMMENDED: "RECOMMENDED:",
            ConditionSeverity.OPTIONAL: "OPTIONAL:"
        }

        prefix = severity_prefix.get(condition.severity, "")

        description = f"{prefix} {condition.description}"

        # Add monitoring information
        if condition.monitoring_frequency and condition.monitoring_frequency != "one-time":
            description += f" (Monitored: {condition.monitoring_frequency})"

        # Add enforcement information
        if condition.auto_enforceable:
            description += " [Auto-enforced]"

        return description

    def get_conditions_summary(self, conditions: List[str]) -> Dict[str, Any]:
        """Generate summary of conditions for borrower review"""

        # Count conditions by type
        mandatory_count = len([c for c in conditions if c.startswith("REQUIRED:")])
        recommended_count = len([c for c in conditions if c.startswith("RECOMMENDED:")])
        optional_count = len([c for c in conditions if c.startswith("OPTIONAL:")])

        return {
            'total_conditions': len(conditions),
            'mandatory_conditions': mandatory_count,
            'recommended_conditions': recommended_count,
            'optional_conditions': optional_count,
            'summary': {
                'collateral_focused': any('collateral' in c.lower() for c in conditions),
                'monitoring_intensive': any('daily' in c.lower() or 'real-time' in c.lower() for c in conditions),
                'governance_incentives': any('governance' in c.lower() and 'discount' in c.lower() for c in conditions),
                'behavioral_restrictions': any('limit' in c.lower() or 'restrict' in c.lower() for c in conditions)
            }
        }