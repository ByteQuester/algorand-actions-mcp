"""
Configurable Logging System for Lending Platform
Replaces hardcoded print statements with structured logging
"""

import os
import sys
import json
import logging
import logging.handlers
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging output"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

class LendingPlatformLogger:
    """Central logging configuration for the lending platform"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self._setup_logging()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default logging configuration"""
        return {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": os.getenv("LOG_FORMAT", "structured"),
            "console": os.getenv("LOG_CONSOLE", "true").lower() == "true",
            "file": os.getenv("LOG_FILE", "false").lower() == "true",
            "file_path": os.getenv("LOG_FILE_PATH", "./logs/lending-platform.log"),
            "max_file_size": os.getenv("LOG_MAX_FILE_SIZE", "10MB"),
            "max_files": int(os.getenv("LOG_MAX_FILES", "5")),
            "include_debug_info": os.getenv("LOG_DEBUG_INFO", "false").lower() == "true"
        }

    def _setup_logging(self):
        """Configure logging based on settings"""
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config["level"].upper()))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Setup console handler
        if self.config["console"]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.config["level"].upper()))

            if self.config["format"] == "structured":
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                )

            root_logger.addHandler(console_handler)

        # Setup file handler
        if self.config["file"]:
            log_file = Path(self.config["file_path"])
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Parse max file size
            max_bytes = self._parse_size(self.config["max_file_size"])

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=self.config["max_files"]
            )
            file_handler.setLevel(getattr(logging, self.config["level"].upper()))
            file_handler.setFormatter(StructuredFormatter())

            root_logger.addHandler(file_handler)

    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with the given name"""
        return logging.getLogger(name)

# Global logger instance
_logger_instance = None

def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance - convenience function"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LendingPlatformLogger()
    return _logger_instance.get_logger(name)

def init_logging(config: Optional[Dict[str, Any]] = None):
    """Initialize logging system with optional config"""
    global _logger_instance
    _logger_instance = LendingPlatformLogger(config)

# Business-specific logging helpers
class BusinessLogger:
    """Business logic specific logging helpers"""

    def __init__(self, logger_name: str = "lending.business"):
        self.logger = get_logger(logger_name)

    def log_loan_request(self, borrower: str, amount: int, **kwargs):
        """Log loan request with structured data"""
        extra_fields = {
            "event_type": "loan_request",
            "borrower": borrower,
            "amount_micro_algos": amount,
            **kwargs
        }
        self.logger.info("Loan request received", extra={'extra_fields': extra_fields})

    def log_negotiation_result(self, loan_id: str, result: str, **kwargs):
        """Log negotiation result"""
        extra_fields = {
            "event_type": "negotiation_result",
            "loan_id": loan_id,
            "result": result,
            **kwargs
        }
        self.logger.info("Negotiation completed", extra={'extra_fields': extra_fields})

    def log_transaction_execution(self, loan_id: str, tx_id: str, status: str, **kwargs):
        """Log transaction execution"""
        extra_fields = {
            "event_type": "transaction_execution",
            "loan_id": loan_id,
            "transaction_id": tx_id,
            "status": status,
            **kwargs
        }
        self.logger.info("Transaction executed", extra={'extra_fields': extra_fields})

    def log_error(self, error_type: str, message: str, **kwargs):
        """Log business errors with context"""
        extra_fields = {
            "event_type": "business_error",
            "error_type": error_type,
            **kwargs
        }
        self.logger.error(message, extra={'extra_fields': extra_fields})

# Performance logging
class PerformanceLogger:
    """Performance monitoring and logging"""

    def __init__(self, logger_name: str = "lending.performance"):
        self.logger = get_logger(logger_name)

    def log_agent_performance(self, agent_name: str, operation: str, duration_ms: float, **kwargs):
        """Log agent performance metrics"""
        extra_fields = {
            "event_type": "agent_performance",
            "agent_name": agent_name,
            "operation": operation,
            "duration_ms": duration_ms,
            **kwargs
        }
        self.logger.info("Agent operation completed", extra={'extra_fields': extra_fields})

    def log_mcp_call(self, service: str, endpoint: str, duration_ms: float, status: str, **kwargs):
        """Log MCP service call performance"""
        extra_fields = {
            "event_type": "mcp_call",
            "service": service,
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "status": status,
            **kwargs
        }
        self.logger.info("MCP service call", extra={'extra_fields': extra_fields})

# Migration helper for replacing print statements
def debug_print(*args, **kwargs):
    """Replacement for print() statements in debug code"""
    logger = get_logger("lending.debug")
    message = " ".join(str(arg) for arg in args)
    logger.debug(message)

def info_print(*args, **kwargs):
    """Replacement for informational print() statements"""
    logger = get_logger("lending.info")
    message = " ".join(str(arg) for arg in args)
    logger.info(message)

def error_print(*args, **kwargs):
    """Replacement for error print() statements"""
    logger = get_logger("lending.error")
    message = " ".join(str(arg) for arg in args)
    logger.error(message)