"""
Production Configuration Management for Lending Platform
Handles environment-based configuration with proper defaults and validation
"""

import os
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class MCPServiceConfig:
    """Configuration for MCP services"""
    endpoint: str
    health_path: str = "/health"
    timeout: int = 30000
    max_retries: int = 3

@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    name: str
    model: str = "gemini-2.0-flash-exp"
    timeout: int = 60000
    max_retries: int = 3

@dataclass
class LendingConfig:
    """Lending business logic configuration"""
    default_interest_rate: float = 7.5
    max_loan_amount: int = 100000000000  # 100k ALGO in microAlgos
    min_collateral_ratio: float = 1.3
    supported_collateral: list = field(default_factory=lambda: ["ALGO", "USDC"])
    max_loan_duration_days: int = 365
    min_loan_duration_days: int = 1

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "structured"
    console: bool = True
    file: bool = False
    file_path: str = "./logs/lending-platform.log"
    max_file_size: str = "10MB"
    max_files: int = 5
    include_debug_info: bool = False

@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: str = "sqlite"
    url: Optional[str] = None
    path: str = "./data/lending.db"
    pool_size: int = 20
    max_overflow: int = 30

@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_secret: Optional[str] = None
    token_expiry: int = 3600
    rate_limiting: bool = True
    cors_enabled: bool = True
    cors_origin: str = "*"

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    health_check_interval: int = 30
    metrics_enabled: bool = True
    performance_tracking: bool = True
    debug_mode: bool = False

class ConfigurationManager:
    """Manages configuration loading and environment-specific overrides"""

    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv("NODE_ENV", "development")
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.base_dir / "config"

        # Load configuration
        self._config = self._load_configuration()

        # Initialize typed configurations
        self.lending = LendingConfig(**self._config.get("lending", {}))
        self.logging = LoggingConfig(**self._config.get("logging", {}))
        self.monitoring = MonitoringConfig(**self._config.get("monitoring", {}))
        self.database = DatabaseConfig(**self._config.get("database", {}))
        self.security = SecurityConfig(**self._config.get("security", {}))

        # Initialize service configurations
        self.mcp_services = {
            name: MCPServiceConfig(**config)
            for name, config in self._config.get("mcp_services", {}).items()
        }

        # Initialize agent configurations, filtering out global settings
        agent_configs = self._config.get("agents", {})
        self.agents = {}

        # Global agent settings
        global_settings = {
            "model": agent_configs.get("model", "gemini-2.0-flash-exp"),
            "timeout": agent_configs.get("timeout", 60000),
            "max_retries": agent_configs.get("max_retries", 3)
        }

        # Individual agent configurations
        for name, config in agent_configs.items():
            if isinstance(config, dict) and "name" in config:
                # Merge global settings with agent-specific settings
                merged_config = {**global_settings, **config}
                self.agents[name] = AgentConfig(**merged_config)

    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from files and environment"""
        config = {}

        # Load default configuration
        default_config_file = self.config_dir / "default.json"
        if default_config_file.exists():
            with open(default_config_file, 'r') as f:
                config = json.load(f)

        # Load environment-specific configuration
        env_config_file = self.config_dir / self.environment / f"{self.environment}.json"
        if env_config_file.exists():
            with open(env_config_file, 'r') as f:
                env_config = json.load(f)
                config = self._deep_merge(config, env_config)

        # Apply environment variable overrides
        config = self._apply_env_overrides(config)

        return config

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        # Environment variable mappings
        env_mappings = {
            # Google API
            "GOOGLE_API_KEY": ("google", "api_key"),
            "GOOGLE_GENAI_USE_VERTEXAI": ("google", "use_vertexai"),
            "GOOGLE_MODEL_NAME": ("agents", "model"),

            # MCP Services
            "ALGORAND_READER_ENDPOINT": ("mcp_services", "algorand_reader", "endpoint"),
            "ALGORAND_WRITER_ENDPOINT": ("mcp_services", "algorand_writer", "endpoint"),
            "LENDING_TOOLBOX_ENDPOINT": ("mcp_services", "lending_toolbox", "endpoint"),

            # Database
            "DATABASE_TYPE": ("database", "type"),
            "DATABASE_URL": ("database", "url"),

            # Security
            "JWT_SECRET": ("security", "jwt_secret"),
            "JWT_EXPIRY": ("security", "token_expiry"),

            # Logging
            "LOG_LEVEL": ("logging", "level"),
            "LOG_FORMAT": ("logging", "format"),
            "LOG_FILE": ("logging", "file"),
            "LOG_FILE_PATH": ("logging", "file_path"),

            # Server
            "PORT": ("server", "port"),
            "HOST": ("server", "host"),

            # ADK Web
            "ADK_WEB_BASE_URL": ("adk_web", "base_url"),
            "ADK_WEB_PORT": ("adk_web", "port"),
        }

        for env_var, path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Navigate to the correct nested dictionary
                current = config
                for key in path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                # Set the value, converting types as needed
                final_key = path[-1]
                current[final_key] = self._convert_env_value(value)

        return config

    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass

        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass

        # String (default)
        return value

    def get_mcp_service_config(self, service_name: str) -> Optional[MCPServiceConfig]:
        """Get MCP service configuration by name"""
        return self.mcp_services.get(service_name)

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get agent configuration by name"""
        return self.agents.get(agent_name)

    def validate_configuration(self) -> list:
        """Validate configuration and return list of issues"""
        issues = []

        # Check required environment variables for production
        if self.environment == "production":
            required_vars = [
                "GOOGLE_API_KEY",
                "JWT_SECRET",
                "DATABASE_URL"
            ]

            for var in required_vars:
                if not os.getenv(var):
                    issues.append(f"Missing required environment variable: {var}")

        # Validate JWT secret length
        if self.security.jwt_secret and len(self.security.jwt_secret) < 32:
            issues.append("JWT secret should be at least 32 characters long")

        # Validate MCP service endpoints
        for service_name, service_config in self.mcp_services.items():
            if not service_config.endpoint:
                issues.append(f"Missing endpoint for MCP service: {service_name}")

        # Validate lending configuration
        if self.lending.min_collateral_ratio < 1.0:
            issues.append("Minimum collateral ratio should be at least 1.0")

        if self.lending.max_loan_amount <= 0:
            issues.append("Maximum loan amount should be positive")

        return issues

    def get_runtime_config(self) -> Dict[str, Any]:
        """Get runtime configuration for application startup"""
        return {
            "environment": self.environment,
            "lending": self.lending,
            "logging": self.logging,
            "monitoring": self.monitoring,
            "database": self.database,
            "security": self.security,
            "mcp_services": {name: config for name, config in self.mcp_services.items()},
            "agents": {name: config for name, config in self.agents.items()}
        }

# Global configuration instance
_config_instance = None

def get_config(environment: str = None) -> ConfigurationManager:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None or (environment and _config_instance.environment != environment):
        _config_instance = ConfigurationManager(environment)
    return _config_instance

def init_config(environment: str = None) -> ConfigurationManager:
    """Initialize configuration system"""
    return get_config(environment)

# Convenience functions for common configurations
def get_mcp_endpoint(service_name: str) -> Optional[str]:
    """Get MCP service endpoint"""
    config = get_config()
    service_config = config.get_mcp_service_config(service_name)
    return service_config.endpoint if service_config else None

def get_agent_model(agent_name: str) -> str:
    """Get agent model name"""
    config = get_config()
    agent_config = config.get_agent_config(agent_name)
    return agent_config.model if agent_config else "gemini-2.0-flash-exp"

def is_production() -> bool:
    """Check if running in production environment"""
    return get_config().environment == "production"

def is_development() -> bool:
    """Check if running in development environment"""
    return get_config().environment == "development"