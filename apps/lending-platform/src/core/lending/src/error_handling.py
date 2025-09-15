"""
Error handling for Lending Platform Core
Centralized error management and recovery strategies
"""

from enum import Enum
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    VALIDATION_ERROR = "validation_error"
    LIQUIDITY_SHORTAGE = "liquidity_shortage"
    NEGOTIATION_FAILED = "negotiation_failed"
    EXECUTION_FAILED = "execution_failed"
    BLOCKCHAIN_ERROR = "blockchain_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RATE_LIMIT_ERROR = "rate_limit_error"


class LendingError(Exception):
    """Base exception for lending platform errors"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.recovery_suggestions = recovery_suggestions or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "recovery_suggestions": self.recovery_suggestions
        }


class ValidationError(LendingError):
    """Raised when input validation fails"""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = {"field": field} if field else {}
        super().__init__(
            message,
            ErrorCategory.VALIDATION_ERROR,
            ErrorSeverity.MEDIUM,
            details=details,
            **kwargs
        )


class LiquidityError(LendingError):
    """Raised when liquidity is insufficient"""

    def __init__(self, message: str, required_amount: Optional[int] = None, available_amount: Optional[int] = None, **kwargs):
        details = {
            "required_amount": required_amount,
            "available_amount": available_amount
        }
        super().__init__(
            message,
            ErrorCategory.LIQUIDITY_SHORTAGE,
            ErrorSeverity.HIGH,
            details={k: v for k, v in details.items() if v is not None},
            **kwargs
        )


class NegotiationError(LendingError):
    """Raised when term negotiation fails"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            ErrorCategory.NEGOTIATION_FAILED,
            ErrorSeverity.MEDIUM,
            **kwargs
        )


class ExecutionError(LendingError):
    """Raised when transaction execution fails"""

    def __init__(self, message: str, transaction_id: Optional[str] = None, **kwargs):
        details = {"transaction_id": transaction_id} if transaction_id else {}
        super().__init__(
            message,
            ErrorCategory.EXECUTION_FAILED,
            ErrorSeverity.HIGH,
            details=details,
            **kwargs
        )


class BlockchainError(LendingError):
    """Raised when blockchain operations fail"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            ErrorCategory.BLOCKCHAIN_ERROR,
            ErrorSeverity.HIGH,
            **kwargs
        )


class SystemError(LendingError):
    """Raised for general system errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            ErrorCategory.SYSTEM_ERROR,
            ErrorSeverity.CRITICAL,
            **kwargs
        )


class ErrorHandler:
    """Central error handler for the lending platform"""

    def __init__(self):
        self.error_counts = {}
        self.recovery_strategies = {
            ErrorCategory.VALIDATION_ERROR: self._handle_validation_error,
            ErrorCategory.LIQUIDITY_SHORTAGE: self._handle_liquidity_error,
            ErrorCategory.NEGOTIATION_FAILED: self._handle_negotiation_error,
            ErrorCategory.EXECUTION_FAILED: self._handle_execution_error,
            ErrorCategory.BLOCKCHAIN_ERROR: self._handle_blockchain_error,
            ErrorCategory.SYSTEM_ERROR: self._handle_system_error,
        }

    def handle_error(self, error: LendingError) -> Dict[str, Any]:
        """Handle an error and return recovery information"""

        # Track error frequency
        error_key = f"{error.category.value}:{error.message}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Log error
        logger.error(
            f"Lending error occurred: {error.message}",
            extra={
                "category": error.category.value,
                "severity": error.severity.value,
                "details": error.details,
                "count": self.error_counts[error_key]
            }
        )

        # Get recovery strategy
        recovery_handler = self.recovery_strategies.get(error.category)
        if recovery_handler:
            recovery_info = recovery_handler(error)
        else:
            recovery_info = self._default_recovery_strategy(error)

        return {
            **error.to_dict(),
            "recovery_info": recovery_info,
            "error_count": self.error_counts[error_key]
        }

    def _handle_validation_error(self, error: ValidationError) -> Dict[str, Any]:
        """Handle validation errors"""
        return {
            "retry_recommended": True,
            "retry_delay": 0,
            "suggestions": [
                "Verify all required fields are provided",
                "Check data format and constraints",
                "Review API documentation for valid values"
            ]
        }

    def _handle_liquidity_error(self, error: LiquidityError) -> Dict[str, Any]:
        """Handle liquidity shortage errors"""
        return {
            "retry_recommended": True,
            "retry_delay": 300,  # 5 minutes
            "suggestions": [
                "Try a smaller loan amount",
                "Increase offered interest rate",
                "Use different collateral type",
                "Wait for more liquidity to become available"
            ]
        }

    def _handle_negotiation_error(self, error: NegotiationError) -> Dict[str, Any]:
        """Handle negotiation failures"""
        return {
            "retry_recommended": True,
            "retry_delay": 60,  # 1 minute
            "suggestions": [
                "Adjust maximum interest rate",
                "Offer more collateral",
                "Reduce loan duration",
                "Try different terms"
            ]
        }

    def _handle_execution_error(self, error: ExecutionError) -> Dict[str, Any]:
        """Handle execution failures"""
        return {
            "retry_recommended": True,
            "retry_delay": 30,  # 30 seconds
            "suggestions": [
                "Check account balance for fees",
                "Verify network connectivity",
                "Ensure wallet is accessible",
                "Contact support if persists"
            ]
        }

    def _handle_blockchain_error(self, error: BlockchainError) -> Dict[str, Any]:
        """Handle blockchain errors"""
        return {
            "retry_recommended": True,
            "retry_delay": 120,  # 2 minutes
            "suggestions": [
                "Wait for network congestion to clear",
                "Check blockchain network status",
                "Verify transaction parameters",
                "Try with higher gas fees"
            ]
        }

    def _handle_system_error(self, error: SystemError) -> Dict[str, Any]:
        """Handle system errors"""
        return {
            "retry_recommended": False,
            "retry_delay": 0,
            "suggestions": [
                "Contact system administrator",
                "Check system status page",
                "Report the error with details"
            ]
        }

    def _default_recovery_strategy(self, error: LendingError) -> Dict[str, Any]:
        """Default recovery strategy for unknown error types"""
        return {
            "retry_recommended": False,
            "retry_delay": 0,
            "suggestions": [
                "Contact support for assistance",
                "Provide error details when reporting"
            ]
        }

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        total_errors = sum(self.error_counts.values())

        category_counts = {}
        for error_key, count in self.error_counts.items():
            category = error_key.split(':')[0]
            category_counts[category] = category_counts.get(category, 0) + count

        return {
            "total_errors": total_errors,
            "category_breakdown": category_counts,
            "most_frequent_errors": sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


# Global error handler instance
error_handler = ErrorHandler()