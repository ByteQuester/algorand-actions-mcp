"""
Common Validation Utilities for Blockchain Collateral Analysis

Input validation and data integrity checks used across all analysis engines.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_positive_number(value: float, name: str = "value") -> None:
    """
    Validate that a number is positive.

    Args:
        value: Number to validate
        name: Name of the value for error messages

    Raises:
        ValidationError: If value is not positive
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")

    if value <= 0:
        raise ValidationError(f"{name} must be positive, got {value}")


def validate_percentage(value: float, name: str = "percentage") -> None:
    """
    Validate that a value is a valid percentage (0.0 to 1.0).

    Args:
        value: Percentage to validate
        name: Name of the value for error messages

    Raises:
        ValidationError: If value is not a valid percentage
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")

    if not 0.0 <= value <= 1.0:
        raise ValidationError(f"{name} must be between 0.0 and 1.0, got {value}")


def validate_ratio(value: float, min_ratio: float = 1.0, max_ratio: float = 10.0, name: str = "ratio") -> None:
    """
    Validate that a value is within acceptable ratio bounds.

    Args:
        value: Ratio to validate
        min_ratio: Minimum acceptable ratio
        max_ratio: Maximum acceptable ratio
        name: Name of the value for error messages

    Raises:
        ValidationError: If value is not within bounds
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")

    if not min_ratio <= value <= max_ratio:
        raise ValidationError(f"{name} must be between {min_ratio} and {max_ratio}, got {value}")


def validate_portfolio_weights(weights: List[float], tolerance: float = 0.01) -> None:
    """
    Validate that portfolio weights sum to approximately 1.0.

    Args:
        weights: List of portfolio weights
        tolerance: Tolerance for sum deviation from 1.0

    Raises:
        ValidationError: If weights don't sum to approximately 1.0
    """
    if not weights:
        raise ValidationError("Portfolio weights cannot be empty")

    for i, weight in enumerate(weights):
        if not isinstance(weight, (int, float)):
            raise ValidationError(f"Weight {i} must be a number, got {type(weight).__name__}")

        if weight < 0:
            raise ValidationError(f"Weight {i} must be non-negative, got {weight}")

    total_weight = sum(weights)
    if abs(total_weight - 1.0) > tolerance:
        raise ValidationError(f"Portfolio weights must sum to 1.0 ± {tolerance}, got {total_weight}")


def validate_market_conditions(market_conditions: str) -> None:
    """
    Validate market conditions string.

    Args:
        market_conditions: Market conditions to validate

    Raises:
        ValidationError: If market conditions are not valid
    """
    valid_conditions = {"bull", "normal", "bear", "crisis"}

    if not isinstance(market_conditions, str):
        raise ValidationError(f"Market conditions must be a string, got {type(market_conditions).__name__}")

    if market_conditions.lower() not in valid_conditions:
        raise ValidationError(f"Market conditions must be one of {valid_conditions}, got '{market_conditions}'")


def validate_asset_symbol(symbol: str) -> None:
    """
    Validate asset symbol format.

    Args:
        symbol: Asset symbol to validate

    Raises:
        ValidationError: If symbol format is invalid
    """
    if not isinstance(symbol, str):
        raise ValidationError(f"Asset symbol must be a string, got {type(symbol).__name__}")

    if not symbol:
        raise ValidationError("Asset symbol cannot be empty")

    # Basic format validation: 2-10 alphanumeric characters
    if not re.match(r'^[A-Z0-9]{2,10}$', symbol.upper()):
        raise ValidationError(f"Asset symbol must be 2-10 alphanumeric characters, got '{symbol}'")


def validate_timestamp(timestamp: datetime, max_age_hours: Optional[float] = None) -> None:
    """
    Validate timestamp and optionally check if it's not too old.

    Args:
        timestamp: Timestamp to validate
        max_age_hours: Maximum age in hours (None to skip age check)

    Raises:
        ValidationError: If timestamp is invalid or too old
    """
    if not isinstance(timestamp, datetime):
        raise ValidationError(f"Timestamp must be a datetime object, got {type(timestamp).__name__}")

    now = datetime.now(timestamp.tzinfo)

    # Check if timestamp is in the future
    if timestamp > now:
        raise ValidationError(f"Timestamp cannot be in the future: {timestamp} > {now}")

    # Check age if specified
    if max_age_hours is not None:
        age = now - timestamp
        max_age = timedelta(hours=max_age_hours)

        if age > max_age:
            raise ValidationError(f"Timestamp is too old: {age} > {max_age}")


def validate_liquidity_tier(tier: str) -> None:
    """
    Validate liquidity tier.

    Args:
        tier: Liquidity tier to validate

    Raises:
        ValidationError: If tier is invalid
    """
    valid_tiers = {"high", "medium", "low"}

    if not isinstance(tier, str):
        raise ValidationError(f"Liquidity tier must be a string, got {type(tier).__name__}")

    if tier.lower() not in valid_tiers:
        raise ValidationError(f"Liquidity tier must be one of {valid_tiers}, got '{tier}'")


def validate_urgency_level(urgency: str) -> None:
    """
    Validate urgency level.

    Args:
        urgency: Urgency level to validate

    Raises:
        ValidationError: If urgency level is invalid
    """
    valid_levels = {"low", "medium", "high", "critical"}

    if not isinstance(urgency, str):
        raise ValidationError(f"Urgency level must be a string, got {type(urgency).__name__}")

    if urgency.lower() not in valid_levels:
        raise ValidationError(f"Urgency level must be one of {valid_levels}, got '{urgency}'")


def validate_url(url: str, require_https: bool = True) -> None:
    """
    Validate URL format.

    Args:
        url: URL to validate
        require_https: Whether to require HTTPS

    Raises:
        ValidationError: If URL is invalid
    """
    if not isinstance(url, str):
        raise ValidationError(f"URL must be a string, got {type(url).__name__}")

    if not url:
        raise ValidationError("URL cannot be empty")

    # Basic URL pattern
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url):
        raise ValidationError(f"Invalid URL format: '{url}'")

    if require_https and not url.startswith('https://'):
        raise ValidationError(f"URL must use HTTPS: '{url}'")


def validate_port(port: int, min_port: int = 1024, max_port: int = 65535) -> None:
    """
    Validate port number.

    Args:
        port: Port number to validate
        min_port: Minimum valid port number
        max_port: Maximum valid port number

    Raises:
        ValidationError: If port is invalid
    """
    if not isinstance(port, int):
        raise ValidationError(f"Port must be an integer, got {type(port).__name__}")

    if not min_port <= port <= max_port:
        raise ValidationError(f"Port must be between {min_port} and {max_port}, got {port}")


def validate_database_path(path: str) -> None:
    """
    Validate database path.

    Args:
        path: Database path to validate

    Raises:
        ValidationError: If path is invalid
    """
    if not isinstance(path, str):
        raise ValidationError(f"Database path must be a string, got {type(path).__name__}")

    if not path:
        raise ValidationError("Database path cannot be empty")

    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in invalid_chars:
        if char in path:
            raise ValidationError(f"Database path contains invalid character '{char}': '{path}'")


def validate_config_dict(config: Dict[str, Any], required_keys: List[str]) -> None:
    """
    Validate configuration dictionary has required keys.

    Args:
        config: Configuration dictionary to validate
        required_keys: List of required keys

    Raises:
        ValidationError: If required keys are missing
    """
    if not isinstance(config, dict):
        raise ValidationError(f"Config must be a dictionary, got {type(config).__name__}")

    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValidationError(f"Missing required configuration keys: {missing_keys}")


def validate_numeric_range(value: float, min_val: float, max_val: float, name: str = "value") -> None:
    """
    Validate that a numeric value is within a specified range.

    Args:
        value: Value to validate
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value
        name: Name of the value for error messages

    Raises:
        ValidationError: If value is outside the range
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")

    if not min_val <= value <= max_val:
        raise ValidationError(f"{name} must be between {min_val} and {max_val}, got {value}")


def validate_list_not_empty(items: List[Any], name: str = "list") -> None:
    """
    Validate that a list is not empty.

    Args:
        items: List to validate
        name: Name of the list for error messages

    Raises:
        ValidationError: If list is empty
    """
    if not isinstance(items, list):
        raise ValidationError(f"{name} must be a list, got {type(items).__name__}")

    if not items:
        raise ValidationError(f"{name} cannot be empty")