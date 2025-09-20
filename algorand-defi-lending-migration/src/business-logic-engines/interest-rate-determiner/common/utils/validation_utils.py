"""
Validation utilities for interest rate calculation inputs and outputs.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from enum import Enum

from ..models.rate_models import RateRequest, RateResponse, RiskLevel, LoanPurpose


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    field: str
    message: str
    severity: ValidationSeverity
    code: str
    suggested_fix: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation process"""
    is_valid: bool
    issues: List[ValidationIssue]
    warnings_count: int = 0
    errors_count: int = 0

    def __post_init__(self):
        """Calculate counts after initialization"""
        self.warnings_count = len([i for i in self.issues if i.severity == ValidationSeverity.WARNING])
        self.errors_count = len([i for i in self.issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]])
        self.is_valid = self.errors_count == 0

    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue"""
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.WARNING:
            self.warnings_count += 1
        elif issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.errors_count += 1
        self.is_valid = self.errors_count == 0

    def get_error_messages(self) -> List[str]:
        """Get all error messages"""
        return [issue.message for issue in self.issues if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]

    def get_warning_messages(self) -> List[str]:
        """Get all warning messages"""
        return [issue.message for issue in self.issues if issue.severity == ValidationSeverity.WARNING]


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, validation_result: Optional[ValidationResult] = None):
        super().__init__(message)
        self.validation_result = validation_result


def validate_wallet_address(address: str) -> ValidationResult:
    """
    Validate Algorand wallet address.

    Args:
        address: Wallet address to validate

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult(is_valid=True, issues=[])

    if not address:
        result.add_issue(ValidationIssue(
            field="wallet_address",
            message="Wallet address cannot be empty",
            severity=ValidationSeverity.ERROR,
            code="WALLET_ADDR_EMPTY"
        ))
        return result

    # Algorand addresses are 58 characters long and base32 encoded
    if len(address) != 58:
        result.add_issue(ValidationIssue(
            field="wallet_address",
            message=f"Algorand address must be 58 characters long, got {len(address)}",
            severity=ValidationSeverity.ERROR,
            code="WALLET_ADDR_LENGTH",
            suggested_fix="Ensure the address is a valid Algorand address"
        ))

    # Check if it contains only valid base32 characters
    base32_pattern = re.compile(r'^[A-Z2-7]+$')
    if not base32_pattern.match(address):
        result.add_issue(ValidationIssue(
            field="wallet_address",
            message="Algorand address contains invalid characters",
            severity=ValidationSeverity.ERROR,
            code="WALLET_ADDR_INVALID_CHARS",
            suggested_fix="Address should only contain uppercase letters A-Z and digits 2-7"
        ))

    return result


def validate_asset_id(asset_id: int) -> ValidationResult:
    """
    Validate Algorand asset ID.

    Args:
        asset_id: Asset ID to validate

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult(is_valid=True, issues=[])

    if asset_id < 0:
        result.add_issue(ValidationIssue(
            field="asset_id",
            message="Asset ID cannot be negative",
            severity=ValidationSeverity.ERROR,
            code="ASSET_ID_NEGATIVE"
        ))

    # Asset ID 0 is reserved for ALGO
    if asset_id == 0:
        result.add_issue(ValidationIssue(
            field="asset_id",
            message="Asset ID 0 is reserved for ALGO",
            severity=ValidationSeverity.INFO,
            code="ASSET_ID_ALGO"
        ))

    # Check for reasonable upper bound (Algorand uses sequential IDs)
    if asset_id > 1_000_000_000:  # 1 billion
        result.add_issue(ValidationIssue(
            field="asset_id",
            message=f"Asset ID {asset_id} seems unusually high",
            severity=ValidationSeverity.WARNING,
            code="ASSET_ID_HIGH",
            suggested_fix="Verify this is a valid asset ID"
        ))

    return result


def validate_decimal_amount(
    amount: Decimal,
    field_name: str,
    min_value: Optional[Decimal] = None,
    max_value: Optional[Decimal] = None,
    allow_zero: bool = False
) -> ValidationResult:
    """
    Validate decimal amount with optional bounds.

    Args:
        amount: Amount to validate
        field_name: Name of the field being validated
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        allow_zero: Whether zero is allowed

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult(is_valid=True, issues=[])

    if not isinstance(amount, Decimal):
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} must be a Decimal type",
            severity=ValidationSeverity.ERROR,
            code="AMOUNT_INVALID_TYPE"
        ))
        return result

    if amount < 0:
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} cannot be negative",
            severity=ValidationSeverity.ERROR,
            code="AMOUNT_NEGATIVE"
        ))

    if not allow_zero and amount == 0:
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} cannot be zero",
            severity=ValidationSeverity.ERROR,
            code="AMOUNT_ZERO"
        ))

    if min_value is not None and amount < min_value:
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} must be at least {min_value}",
            severity=ValidationSeverity.ERROR,
            code="AMOUNT_TOO_LOW",
            suggested_fix=f"Increase {field_name} to at least {min_value}"
        ))

    if max_value is not None and amount > max_value:
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} cannot exceed {max_value}",
            severity=ValidationSeverity.ERROR,
            code="AMOUNT_TOO_HIGH",
            suggested_fix=f"Reduce {field_name} to {max_value} or less"
        ))

    return result


def validate_date_range(
    start_date: datetime,
    end_date: datetime,
    field_name: str = "date_range"
) -> ValidationResult:
    """
    Validate date range.

    Args:
        start_date: Start date
        end_date: End date
        field_name: Name of the field being validated

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult(is_valid=True, issues=[])

    if start_date >= end_date:
        result.add_issue(ValidationIssue(
            field=field_name,
            message="Start date must be before end date",
            severity=ValidationSeverity.ERROR,
            code="DATE_RANGE_INVALID"
        ))

    # Check for unreasonable date ranges
    now = datetime.now(timezone.utc)
    if start_date > now:
        result.add_issue(ValidationIssue(
            field=field_name,
            message="Start date cannot be in the future",
            severity=ValidationSeverity.WARNING,
            code="DATE_FUTURE_START"
        ))

    # Check for very old dates
    if (now - start_date).days > 365 * 10:  # 10 years
        result.add_issue(ValidationIssue(
            field=field_name,
            message="Start date is more than 10 years ago",
            severity=ValidationSeverity.WARNING,
            code="DATE_VERY_OLD",
            suggested_fix="Consider using more recent data"
        ))

    return result


def validate_confidence_score(score: float, field_name: str = "confidence_score") -> ValidationResult:
    """
    Validate confidence score.

    Args:
        score: Confidence score to validate (should be 0-1)
        field_name: Name of the field being validated

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult(is_valid=True, issues=[])

    if not isinstance(score, (int, float)):
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} must be a number",
            severity=ValidationSeverity.ERROR,
            code="CONFIDENCE_INVALID_TYPE"
        ))
        return result

    if score < 0 or score > 1:
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} must be between 0 and 1, got {score}",
            severity=ValidationSeverity.ERROR,
            code="CONFIDENCE_OUT_OF_RANGE",
            suggested_fix="Confidence score should be between 0.0 and 1.0"
        ))

    if score < 0.1:
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} is very low ({score})",
            severity=ValidationSeverity.WARNING,
            code="CONFIDENCE_VERY_LOW",
            suggested_fix="Consider improving data quality or model parameters"
        ))

    return result


def validate_risk_level(risk_level: str) -> ValidationResult:
    """
    Validate risk level string.

    Args:
        risk_level: Risk level to validate

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult(is_valid=True, issues=[])

    valid_levels = [level.value for level in RiskLevel]

    if risk_level not in valid_levels:
        result.add_issue(ValidationIssue(
            field="risk_level",
            message=f"Invalid risk level '{risk_level}'. Must be one of: {valid_levels}",
            severity=ValidationSeverity.ERROR,
            code="RISK_LEVEL_INVALID",
            suggested_fix=f"Use one of: {', '.join(valid_levels)}"
        ))

    return result


def validate_rate_request(request: RateRequest) -> ValidationResult:
    """
    Comprehensive validation of rate request.

    Args:
        request: RateRequest to validate

    Returns:
        ValidationResult with all validation issues
    """
    result = ValidationResult(is_valid=True, issues=[])

    # Validate loan amount
    loan_validation = validate_decimal_amount(
        request.loan_amount,
        "loan_amount",
        min_value=Decimal('100'),  # Minimum $100 loan
        max_value=Decimal('100000000')  # Maximum $100M loan
    )
    result.issues.extend(loan_validation.issues)

    # Validate duration
    if request.duration_days <= 0:
        result.add_issue(ValidationIssue(
            field="duration_days",
            message="Loan duration must be positive",
            severity=ValidationSeverity.ERROR,
            code="DURATION_INVALID"
        ))

    if request.duration_days > 365 * 30:  # 30 years max
        result.add_issue(ValidationIssue(
            field="duration_days",
            message="Loan duration cannot exceed 30 years",
            severity=ValidationSeverity.ERROR,
            code="DURATION_TOO_LONG"
        ))

    if request.duration_days < 30:  # Less than 1 month
        result.add_issue(ValidationIssue(
            field="duration_days",
            message="Loan duration less than 30 days is unusual",
            severity=ValidationSeverity.WARNING,
            code="DURATION_VERY_SHORT"
        ))

    # Validate wallet address
    wallet_validation = validate_wallet_address(request.borrower_wallet_address)
    result.issues.extend(wallet_validation.issues)

    # Validate loan purpose
    if request.purpose not in [purpose.value for purpose in LoanPurpose]:
        result.add_issue(ValidationIssue(
            field="purpose",
            message=f"Invalid loan purpose: {request.purpose}",
            severity=ValidationSeverity.ERROR,
            code="PURPOSE_INVALID"
        ))

    # Validate collateral information
    if request.collateral_asset_ids and request.collateral_values:
        for asset_id in request.collateral_asset_ids:
            asset_validation = validate_asset_id(asset_id)
            result.issues.extend(asset_validation.issues)

            if asset_id in request.collateral_values:
                collateral_validation = validate_decimal_amount(
                    request.collateral_values[asset_id],
                    f"collateral_value_{asset_id}",
                    min_value=Decimal('0'),
                    allow_zero=True
                )
                result.issues.extend(collateral_validation.issues)

    # Validate credit score if provided
    if request.borrower_credit_score is not None:
        if not (300 <= request.borrower_credit_score <= 850):
            result.add_issue(ValidationIssue(
                field="borrower_credit_score",
                message=f"Credit score must be between 300-850, got {request.borrower_credit_score}",
                severity=ValidationSeverity.WARNING,
                code="CREDIT_SCORE_RANGE"
            ))

    # Validate debt-to-income ratio if provided
    if request.debt_to_income_ratio is not None:
        if request.debt_to_income_ratio < 0 or request.debt_to_income_ratio > 10:
            result.add_issue(ValidationIssue(
                field="debt_to_income_ratio",
                message=f"Debt-to-income ratio seems unrealistic: {request.debt_to_income_ratio}",
                severity=ValidationSeverity.WARNING,
                code="DTI_UNREALISTIC"
            ))

    # Validate risk score if provided
    if request.risk_score is not None:
        if not (0 <= request.risk_score <= 100):
            result.add_issue(ValidationIssue(
                field="risk_score",
                message=f"Risk score must be between 0-100, got {request.risk_score}",
                severity=ValidationSeverity.ERROR,
                code="RISK_SCORE_RANGE"
            ))

    # Calculate final validation state
    result.warnings_count = len([i for i in result.issues if i.severity == ValidationSeverity.WARNING])
    result.errors_count = len([i for i in result.issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]])
    result.is_valid = result.errors_count == 0

    return result


def validate_rate_response(response: RateResponse) -> ValidationResult:
    """
    Validate rate response for correctness and reasonableness.

    Args:
        response: RateResponse to validate

    Returns:
        ValidationResult with all validation issues
    """
    result = ValidationResult(is_valid=True, issues=[])

    # Validate interest rates
    rate_validation = validate_decimal_amount(
        response.annual_interest_rate,
        "annual_interest_rate",
        min_value=Decimal('0'),
        max_value=Decimal('1.0')  # 100% max
    )
    result.issues.extend(rate_validation.issues)

    # Check for reasonable interest rates
    if response.annual_interest_rate > Decimal('0.5'):  # 50%
        result.add_issue(ValidationIssue(
            field="annual_interest_rate",
            message=f"Interest rate seems very high: {response.annual_interest_rate:.2%}",
            severity=ValidationSeverity.WARNING,
            code="RATE_VERY_HIGH"
        ))

    if response.annual_interest_rate < Decimal('0.001'):  # 0.1%
        result.add_issue(ValidationIssue(
            field="annual_interest_rate",
            message=f"Interest rate seems very low: {response.annual_interest_rate:.2%}",
            severity=ValidationSeverity.WARNING,
            code="RATE_VERY_LOW"
        ))

    # Validate payment amounts
    payment_validation = validate_decimal_amount(
        response.monthly_payment,
        "monthly_payment",
        min_value=Decimal('0')
    )
    result.issues.extend(payment_validation.issues)

    # Validate confidence score
    confidence_validation = validate_confidence_score(response.overall_confidence_score)
    result.issues.extend(confidence_validation.issues)

    # Validate risk level
    risk_validation = validate_risk_level(response.calculated_risk_level.value)
    result.issues.extend(risk_validation.issues)

    # Check rate component consistency
    total_adjustments = (
        response.risk_premium +
        response.duration_adjustment +
        response.algorand_premium_discount +
        response.defi_market_adjustment -
        response.collateral_discount
    )

    calculated_rate = response.base_rate + total_adjustments
    if abs(calculated_rate - response.annual_interest_rate) > Decimal('0.001'):
        result.add_issue(ValidationIssue(
            field="rate_components",
            message="Rate components don't sum to final rate",
            severity=ValidationSeverity.ERROR,
            code="RATE_COMPONENT_MISMATCH"
        ))

    # Validate explanation presence
    if not response.explanation or len(response.explanation) < 10:
        result.add_issue(ValidationIssue(
            field="explanation",
            message="Rate explanation is missing or too short",
            severity=ValidationSeverity.WARNING,
            code="EXPLANATION_INSUFFICIENT"
        ))

    # Calculate final validation state
    result.warnings_count = len([i for i in result.issues if i.severity == ValidationSeverity.WARNING])
    result.errors_count = len([i for i in result.issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]])
    result.is_valid = result.errors_count == 0

    return result


def validate_percentage(
    value: float,
    field_name: str,
    min_value: float = 0.0,
    max_value: float = 100.0
) -> ValidationResult:
    """
    Validate percentage value.

    Args:
        value: Percentage value to validate
        field_name: Name of the field
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult(is_valid=True, issues=[])

    if not isinstance(value, (int, float)):
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} must be a number",
            severity=ValidationSeverity.ERROR,
            code="PERCENTAGE_INVALID_TYPE"
        ))
        return result

    if value < min_value or value > max_value:
        result.add_issue(ValidationIssue(
            field=field_name,
            message=f"{field_name} must be between {min_value}% and {max_value}%, got {value}%",
            severity=ValidationSeverity.ERROR,
            code="PERCENTAGE_OUT_OF_RANGE"
        ))

    return result


def sanitize_string_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent injection attacks.

    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return ""

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';\\]', '', input_str)

    # Limit length
    sanitized = sanitized[:max_length]

    # Strip whitespace
    sanitized = sanitized.strip()

    return sanitized