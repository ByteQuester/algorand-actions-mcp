"""
Regulatory Compliance Engine

Ensures interest rate calculations comply with financial regulations including
usury laws, consumer protection regulations, and emerging DeFi compliance requirements.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Jurisdiction(Enum):
    """Supported jurisdictions"""
    US_FEDERAL = "us_federal"
    US_STATE = "us_state"
    EU = "eu"
    UK = "uk"
    SINGAPORE = "singapore"
    SWITZERLAND = "switzerland"
    GLOBAL = "global"


@dataclass
class RegulatoryLimits:
    """Regulatory limits for interest rates"""
    jurisdiction: Jurisdiction
    max_annual_rate: Optional[Decimal] = None
    max_monthly_rate: Optional[Decimal] = None
    max_total_cost: Optional[Decimal] = None
    cooling_off_period_hours: Optional[int] = None
    disclosure_requirements: List[str] = None
    consumer_protection_limits: Optional[Dict[str, Any]] = None


@dataclass
class ComplianceCheck:
    """Result of compliance verification"""
    is_compliant: bool
    jurisdiction: Jurisdiction
    applied_rate: Decimal
    max_allowed_rate: Decimal
    violations: List[str]
    warnings: List[str]
    required_disclosures: List[str]
    compliance_score: float
    check_timestamp: datetime


class RegulatoryComplianceEngine:
    """Engine for regulatory compliance verification"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._load_regulatory_limits()

    def _load_regulatory_limits(self):
        """Load regulatory limits for different jurisdictions"""
        self.regulatory_limits = {
            Jurisdiction.US_FEDERAL: RegulatoryLimits(
                jurisdiction=Jurisdiction.US_FEDERAL,
                max_annual_rate=Decimal('0.36'),  # 36% APR federal limit
                disclosure_requirements=[
                    "Annual Percentage Rate (APR)",
                    "Total cost of loan",
                    "Payment schedule",
                    "Late payment fees"
                ]
            ),
            Jurisdiction.EU: RegulatoryLimits(
                jurisdiction=Jurisdiction.EU,
                max_annual_rate=Decimal('0.25'),  # Conservative EU limit
                cooling_off_period_hours=14 * 24,  # 14 days
                disclosure_requirements=[
                    "Annual Percentage Rate of Charge (APRC)",
                    "Total amount of credit",
                    "Right of withdrawal"
                ]
            )
        }

    async def verify_compliance(self, proposed_rate: Decimal, loan_amount: Decimal,
                              duration_days: int, jurisdiction: Jurisdiction,
                              borrower_type: str = "individual") -> ComplianceCheck:
        """Verify regulatory compliance for proposed interest rate"""
        try:
            logger.info(f"Verifying compliance for {jurisdiction.value}")

            limits = self.regulatory_limits.get(jurisdiction)
            if not limits:
                # Use global defaults for unsupported jurisdictions
                limits = self._get_default_limits()

            violations = []
            warnings = []
            applied_rate = proposed_rate

            # Check maximum rate limits
            if limits.max_annual_rate and proposed_rate > limits.max_annual_rate:
                violations.append(f"Rate {proposed_rate:.2%} exceeds maximum {limits.max_annual_rate:.2%}")
                applied_rate = limits.max_annual_rate

            # Additional compliance checks would go here

            is_compliant = len(violations) == 0
            compliance_score = self._calculate_compliance_score(violations, warnings)

            return ComplianceCheck(
                is_compliant=is_compliant,
                jurisdiction=jurisdiction,
                applied_rate=applied_rate,
                max_allowed_rate=limits.max_annual_rate or Decimal('1.0'),
                violations=violations,
                warnings=warnings,
                required_disclosures=limits.disclosure_requirements or [],
                compliance_score=compliance_score,
                check_timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error in compliance verification: {e}")
            raise

    def _get_default_limits(self) -> RegulatoryLimits:
        """Get default regulatory limits"""
        return RegulatoryLimits(
            jurisdiction=Jurisdiction.GLOBAL,
            max_annual_rate=Decimal('0.50'),  # 50% conservative global limit
            disclosure_requirements=["Interest rate", "Total cost", "Payment terms"]
        )

    def _calculate_compliance_score(self, violations: List[str], warnings: List[str]) -> float:
        """Calculate compliance score"""
        if violations:
            return 0.0
        elif warnings:
            return 0.8
        else:
            return 1.0