"""
Production Logging Configuration - Agent 2
Structured logging with security, performance, and audit trails
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

import structlog
from pythonjsonlogger import jsonlogger

class ProductionLogger:
    """Enhanced production logging system"""

    @staticmethod
    def configure_production_logging():
        """Configure structured logging for production"""

        # Create log directory
        log_dir = Path("/var/log/lending-api")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                ProductionLogger.add_security_context,
                ProductionLogger.add_performance_metrics,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configure standard library logging
        logging.basicConfig(
            level=logging.INFO,
            handlers=[
                # Console handler for development
                logging.StreamHandler(sys.stdout),
                # File handler for production
                logging.FileHandler("/var/log/lending-api/app.log"),
                # Separate file for security events
                logging.FileHandler("/var/log/lending-api/security.log"),
                # Audit trail for all transactions
                logging.FileHandler("/var/log/lending-api/audit.log")
            ]
        )

        return structlog.get_logger()

    @staticmethod
    def add_security_context(logger, method_name, event_dict):
        """Add security-related context to logs"""

        # Sanitize sensitive data
        if 'password' in event_dict:
            event_dict['password'] = '[REDACTED]'
        if 'secret' in event_dict:
            event_dict['secret'] = '[REDACTED]'
        if 'private_key' in event_dict:
            event_dict['private_key'] = '[REDACTED]'

        # Add security flags
        if any(term in str(event_dict) for term in ['login', 'auth', 'token', 'jwt']):
            event_dict['security_event'] = True

        # Truncate long addresses for privacy
        for key in ['account', 'address', 'wallet']:
            if key in event_dict and isinstance(event_dict[key], str):
                if len(event_dict[key]) > 20:
                    event_dict[key] = event_dict[key][:10] + "..." + event_dict[key][-6:]

        return event_dict

    @staticmethod
    def add_performance_metrics(logger, method_name, event_dict):
        """Add performance-related metrics to logs"""

        # Add timestamp for performance tracking
        event_dict['timestamp'] = datetime.utcnow().isoformat()

        # Add component identifier
        event_dict['component'] = 'lending-api'

        # Add environment
        event_dict['environment'] = os.getenv('ENVIRONMENT', 'production')

        return event_dict

class AuditLogger:
    """Specialized audit logging for financial transactions"""

    def __init__(self):
        self.logger = structlog.get_logger("audit")

    def log_loan_request(self, loan_id: str, user_id: str, amount: int, **kwargs):
        """Audit log for loan requests"""
        self.logger.info(
            "LOAN_REQUEST",
            audit_type="financial",
            loan_id=loan_id,
            user_id=user_id,
            amount_micro_algos=amount,
            amount_algos=amount / 1_000_000,
            **kwargs
        )

    def log_loan_approval(self, loan_id: str, approver: str, **kwargs):
        """Audit log for loan approvals"""
        self.logger.info(
            "LOAN_APPROVAL",
            audit_type="financial",
            loan_id=loan_id,
            approver=approver,
            **kwargs
        )

    def log_transaction_created(self, loan_id: str, transaction_id: str, **kwargs):
        """Audit log for blockchain transactions"""
        self.logger.info(
            "TRANSACTION_CREATED",
            audit_type="blockchain",
            loan_id=loan_id,
            transaction_id=transaction_id,
            **kwargs
        )

    def log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Audit log for security events"""
        self.logger.warning(
            "SECURITY_EVENT",
            audit_type="security",
            event_type=event_type,
            user_id=user_id,
            **details
        )

class PerformanceLogger:
    """Performance and monitoring logger"""

    def __init__(self):
        self.logger = structlog.get_logger("performance")

    def log_api_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """Log API request performance"""
        self.logger.info(
            "API_REQUEST",
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time * 1000,
            status_code=status_code,
            performance_category="api"
        )

    def log_database_query(self, query_type: str, duration: float, success: bool):
        """Log database query performance"""
        self.logger.info(
            "DATABASE_QUERY",
            query_type=query_type,
            duration_ms=duration * 1000,
            success=success,
            performance_category="database"
        )

    def log_blockchain_operation(self, operation: str, duration: float, success: bool):
        """Log blockchain operation performance"""
        self.logger.info(
            "BLOCKCHAIN_OPERATION",
            operation=operation,
            duration_ms=duration * 1000,
            success=success,
            performance_category="blockchain"
        )

class SecurityLogger:
    """Security-focused logging"""

    def __init__(self):
        self.logger = structlog.get_logger("security")

    def log_authentication_attempt(self, user_id: str, success: bool, ip_address: str):
        """Log authentication attempts"""
        self.logger.info(
            "AUTH_ATTEMPT",
            user_id=user_id,
            success=success,
            client_ip=ip_address,
            security_event=True
        )

    def log_rate_limit_exceeded(self, client_ip: str, endpoint: str, limit: str):
        """Log rate limit violations"""
        self.logger.warning(
            "RATE_LIMIT_EXCEEDED",
            client_ip=client_ip,
            endpoint=endpoint,
            limit=limit,
            security_event=True,
            alert_level="medium"
        )

    def log_suspicious_activity(self, user_id: str, activity: str, details: Dict[str, Any]):
        """Log suspicious activities"""
        self.logger.warning(
            "SUSPICIOUS_ACTIVITY",
            user_id=user_id,
            activity=activity,
            security_event=True,
            alert_level="high",
            **details
        )

# Production log analysis queries (for monitoring)
LOG_ANALYSIS_QUERIES = {
    "error_rate": """
        SELECT
            DATE_TRUNC('minute', timestamp) as minute,
            COUNT(*) as total_requests,
            COUNT(CASE WHEN level = 'ERROR' THEN 1 END) as errors,
            COUNT(CASE WHEN level = 'ERROR' THEN 1 END) * 100.0 / COUNT(*) as error_rate
        FROM logs
        WHERE timestamp > NOW() - INTERVAL '1 hour'
        GROUP BY minute
        ORDER BY minute DESC;
    """,

    "performance_metrics": """
        SELECT
            endpoint,
            AVG(response_time_ms) as avg_response_time,
            MAX(response_time_ms) as max_response_time,
            COUNT(*) as request_count
        FROM logs
        WHERE event = 'API_REQUEST'
        AND timestamp > NOW() - INTERVAL '1 hour'
        GROUP BY endpoint
        ORDER BY avg_response_time DESC;
    """,

    "security_events": """
        SELECT
            event,
            COUNT(*) as count,
            MAX(timestamp) as last_occurrence
        FROM logs
        WHERE security_event = true
        AND timestamp > NOW() - INTERVAL '24 hours'
        GROUP BY event
        ORDER BY count DESC;
    """
}

# Initialize loggers for production
def get_production_loggers():
    """Get all production loggers"""
    return {
        'main': ProductionLogger.configure_production_logging(),
        'audit': AuditLogger(),
        'performance': PerformanceLogger(),
        'security': SecurityLogger()
    }