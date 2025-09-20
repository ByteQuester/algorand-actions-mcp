"""
Configuration management for Regulatory Compliance Engine
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class JurisdictionConfig:
    """Configuration for jurisdiction-specific compliance"""
    jurisdiction_code: str
    jurisdiction_name: str
    jurisdiction_type: str  # federal, state, municipal, international
    primary_language: str = "en"
    currency: str = "USD"

    # Regulatory frameworks applicable
    applicable_frameworks: List[str] = None

    # Usury law limits
    maximum_apr: Optional[float] = None
    criminal_usury_threshold: Optional[float] = None
    small_loan_cap: Optional[float] = None

    # Required licenses
    required_licenses: List[str] = None

    # Disclosure requirements
    mandatory_disclosures: List[str] = None
    disclosure_language_requirements: List[str] = None

    # Consumer protection rules
    cooling_off_period_days: int = 0
    right_to_cancel_period_days: int = 0
    max_late_fee_amount: Optional[float] = None
    max_late_fee_percentage: Optional[float] = None

    def __post_init__(self):
        if self.applicable_frameworks is None:
            self.applicable_frameworks = []
        if self.required_licenses is None:
            self.required_licenses = []
        if self.mandatory_disclosures is None:
            self.mandatory_disclosures = []
        if self.disclosure_language_requirements is None:
            self.disclosure_language_requirements = ["en"]


@dataclass
class ComplianceMonitoringConfig:
    """Configuration for compliance monitoring"""
    enable_real_time_monitoring: bool = True
    monitoring_interval_seconds: int = 300  # 5 minutes

    # Alert thresholds
    rate_violation_threshold: float = 0.01  # 1% above legal limit
    fee_violation_threshold: float = 0.05   # 5% above legal limit

    # Audit settings
    enable_compliance_logging: bool = True
    log_retention_days: int = 2555  # 7 years

    # Reporting settings
    generate_compliance_reports: bool = True
    report_frequency_days: int = 30

    # Integration settings
    external_compliance_api_enabled: bool = False
    external_api_endpoint: Optional[str] = None
    external_api_timeout_seconds: int = 30


@dataclass
class ValidationConfig:
    """Configuration for rate validation"""
    # Validation modes
    strict_validation: bool = True
    fail_on_violation: bool = True
    warn_on_borderline: bool = True

    # Validation checks to perform
    check_usury_laws: bool = True
    check_consumer_protection: bool = True
    check_anti_predatory: bool = True
    check_disclosure_requirements: bool = True
    check_fee_limits: bool = True

    # APR calculation settings
    apr_calculation_method: str = "actuarial"  # actuarial, simple, compound
    include_fees_in_apr: bool = True
    fee_inclusion_list: List[str] = None
    fee_exclusion_list: List[str] = None

    # Rounding settings
    apr_rounding_decimals: int = 3
    fee_rounding_decimals: int = 2

    # Tolerance settings
    calculation_tolerance: float = 0.0001  # 0.01%

    def __post_init__(self):
        if self.fee_inclusion_list is None:
            self.fee_inclusion_list = [
                "origination_fee",
                "processing_fee",
                "application_fee",
                "credit_check_fee",
                "documentation_fee"
            ]
        if self.fee_exclusion_list is None:
            self.fee_exclusion_list = [
                "late_payment_fee",
                "returned_payment_fee",
                "insurance_premium",
                "taxes",
                "recording_fees"
            ]


@dataclass
class AuditConfig:
    """Configuration for compliance auditing"""
    enable_audit_trail: bool = True
    audit_all_transactions: bool = True
    audit_sensitive_operations: bool = True

    # Audit data retention
    audit_retention_years: int = 7
    compress_old_audits: bool = True

    # Audit reporting
    generate_audit_reports: bool = True
    audit_report_frequency_days: int = 90
    include_statistical_analysis: bool = True

    # External audit support
    enable_external_audit_export: bool = True
    audit_export_format: str = "json"  # json, csv, xml

    # Performance settings
    async_audit_logging: bool = True
    audit_batch_size: int = 1000
    audit_queue_max_size: int = 10000


@dataclass
class IntegrationConfig:
    """Configuration for external integrations"""
    # Regulatory API integrations
    cfpb_api_enabled: bool = False
    cfpb_api_key: Optional[str] = None

    finra_api_enabled: bool = False
    finra_api_key: Optional[str] = None

    # International regulatory APIs
    fca_api_enabled: bool = False  # UK Financial Conduct Authority
    fca_api_key: Optional[str] = None

    bafin_api_enabled: bool = False  # German BaFin
    bafin_api_key: Optional[str] = None

    # Legal database integrations
    westlaw_enabled: bool = False
    westlaw_api_key: Optional[str] = None

    lexisnexis_enabled: bool = False
    lexisnexis_api_key: Optional[str] = None

    # Rate limit settings
    api_rate_limit_per_minute: int = 60
    api_timeout_seconds: int = 30
    api_retry_attempts: int = 3

    # Cache settings
    regulatory_data_cache_hours: int = 24
    legal_update_check_hours: int = 6


@dataclass
class RegulatoryComplianceConfig:
    """Main configuration class for regulatory compliance engine"""
    # Sub-configurations
    monitoring: ComplianceMonitoringConfig
    validation: ValidationConfig
    audit: AuditConfig
    integration: IntegrationConfig

    # Active jurisdictions
    primary_jurisdiction: str = "US"
    secondary_jurisdictions: List[str] = None
    jurisdiction_configs: Dict[str, JurisdictionConfig] = None

    # Engine settings
    engine_name: str = "regulatory_compliance_engine"
    version: str = "1.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"

    # Performance settings
    max_concurrent_validations: int = 50
    validation_timeout_seconds: int = 30
    cache_size_mb: int = 128

    # Feature flags
    enable_predictive_compliance: bool = True
    enable_regulatory_change_alerts: bool = True
    enable_cross_jurisdiction_analysis: bool = True

    # Compliance scoring
    enable_compliance_scoring: bool = True
    compliance_score_weights: Dict[str, float] = None

    def __post_init__(self):
        if self.secondary_jurisdictions is None:
            self.secondary_jurisdictions = []
        if self.jurisdiction_configs is None:
            self.jurisdiction_configs = {}
        if self.compliance_score_weights is None:
            self.compliance_score_weights = {
                "usury_compliance": 0.3,
                "consumer_protection": 0.25,
                "disclosure_compliance": 0.2,
                "fee_compliance": 0.15,
                "licensing_compliance": 0.1
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegulatoryComplianceConfig':
        """Create config from dictionary"""

        # Handle jurisdiction configs
        jurisdiction_configs = {}
        if 'jurisdiction_configs' in data:
            for jurisdiction, config_data in data['jurisdiction_configs'].items():
                jurisdiction_configs[jurisdiction] = JurisdictionConfig(**config_data)

        return cls(
            monitoring=ComplianceMonitoringConfig(**data.get('monitoring', {})),
            validation=ValidationConfig(**data.get('validation', {})),
            audit=AuditConfig(**data.get('audit', {})),
            integration=IntegrationConfig(**data.get('integration', {})),
            jurisdiction_configs=jurisdiction_configs,
            **{k: v for k, v in data.items() if k not in [
                'monitoring', 'validation', 'audit', 'integration', 'jurisdiction_configs'
            ]}
        )

    def add_jurisdiction(self, jurisdiction_config: JurisdictionConfig) -> None:
        """Add a jurisdiction configuration"""
        self.jurisdiction_configs[jurisdiction_config.jurisdiction_code] = jurisdiction_config

    def get_jurisdiction_config(self, jurisdiction_code: str) -> Optional[JurisdictionConfig]:
        """Get configuration for a specific jurisdiction"""
        return self.jurisdiction_configs.get(jurisdiction_code)

    def get_applicable_jurisdictions(self) -> List[str]:
        """Get list of all applicable jurisdictions"""
        jurisdictions = [self.primary_jurisdiction]
        jurisdictions.extend(self.secondary_jurisdictions)
        return list(set(jurisdictions))  # Remove duplicates


def load_config(config_path: Optional[Path] = None) -> RegulatoryComplianceConfig:
    """
    Load configuration from file or return default configuration

    Args:
        config_path: Path to configuration file

    Returns:
        RegulatoryComplianceConfig: Loaded or default configuration
    """
    if config_path and config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return RegulatoryComplianceConfig.from_dict(config_data)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            print("Using default configuration")

    # Return default configuration with common jurisdictions
    config = RegulatoryComplianceConfig(
        monitoring=ComplianceMonitoringConfig(),
        validation=ValidationConfig(),
        audit=AuditConfig(),
        integration=IntegrationConfig()
    )

    # Add default US jurisdiction
    us_config = JurisdictionConfig(
        jurisdiction_code="US",
        jurisdiction_name="United States",
        jurisdiction_type="federal",
        maximum_apr=0.36,  # Federal MLA limit
        criminal_usury_threshold=0.45,
        applicable_frameworks=["TILA", "FCRA", "ECOA"],
        required_licenses=["money_transmitter", "lending_license"],
        mandatory_disclosures=[
            "annual_percentage_rate",
            "total_cost_of_credit",
            "payment_schedule",
            "right_to_cancel"
        ],
        cooling_off_period_days=14,
        right_to_cancel_period_days=3
    )
    config.add_jurisdiction(us_config)

    return config


def save_config(config: RegulatoryComplianceConfig, config_path: Path) -> None:
    """
    Save configuration to file

    Args:
        config: Configuration to save
        config_path: Path where to save configuration
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config.to_dict(), f, indent=2, default=str)


def create_default_config_file(config_path: Path) -> None:
    """
    Create a default configuration file

    Args:
        config_path: Path where to create the configuration file
    """
    default_config = load_config()
    save_config(default_config, config_path)


def load_jurisdiction_database(database_path: Path) -> Dict[str, JurisdictionConfig]:
    """
    Load jurisdiction database from file

    Args:
        database_path: Path to jurisdiction database file

    Returns:
        Dict mapping jurisdiction codes to configurations
    """
    if not database_path.exists():
        return {}

    try:
        with open(database_path, 'r') as f:
            data = json.load(f)

        jurisdictions = {}
        for jurisdiction_code, config_data in data.items():
            jurisdictions[jurisdiction_code] = JurisdictionConfig(**config_data)

        return jurisdictions

    except Exception as e:
        print(f"Warning: Failed to load jurisdiction database from {database_path}: {e}")
        return {}