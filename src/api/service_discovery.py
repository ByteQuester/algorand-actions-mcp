"""
Service Discovery Mechanism for Algorand Lending Platform

Provides dynamic service discovery and registry capabilities for both vendor mode
(direct imports) and hosted service mode (HTTP calls). Supports service health
monitoring, load balancing, and automatic failover.

Features:
- Service registration and discovery
- Vendor vs hosted mode detection
- Health monitoring and status tracking
- Load balancing with multiple strategies
- Service configuration management
- Automatic service failover
- Service metadata and versioning
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import os

import httpx
import aiofiles
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# Enums and Models

class ServiceMode(str, Enum):
    """Service deployment modes"""
    VENDOR = "vendor"      # Direct import/vendoring
    HOSTED = "hosted"      # HTTP service calls
    HYBRID = "hybrid"      # Mix of vendor and hosted

class ServiceStatus(str, Enum):
    """Service status states"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"

class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    RANDOM = "random"
    FAILOVER = "failover"

@dataclass
class ServiceEndpoint:
    """Individual service endpoint information"""
    url: str
    weight: int = 100
    max_connections: int = 100
    current_connections: int = 0
    avg_response_time: float = 0.0
    last_health_check: Optional[float] = None
    health_check_failures: int = 0
    status: ServiceStatus = ServiceStatus.UNKNOWN

class ServiceInfo(BaseModel):
    """Service information model"""
    name: str = Field(..., description="Service name")
    mode: ServiceMode = Field(..., description="Service deployment mode")
    version: str = Field("1.0.0", description="Service version")
    description: Optional[str] = Field(None, description="Service description")

    # Vendor mode fields
    import_path: Optional[str] = Field(None, description="Import path for vendor mode")
    class_name: Optional[str] = Field(None, description="Class name for vendor mode")

    # Hosted mode fields
    base_url: Optional[str] = Field(None, description="Base URL for hosted mode")
    endpoints: List[ServiceEndpoint] = Field(default_factory=list)
    auth_token: Optional[str] = Field(None, description="Authentication token")

    # Health and monitoring
    health_check_url: Optional[str] = Field(None, description="Health check endpoint")
    health_check_interval: int = Field(30, description="Health check interval in seconds")
    timeout: int = Field(30, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")

    # Load balancing
    load_balancing_strategy: LoadBalancingStrategy = Field(
        LoadBalancingStrategy.ROUND_ROBIN,
        description="Load balancing strategy"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @validator('endpoints')
    def validate_endpoints(cls, v, values):
        """Validate endpoints for hosted mode"""
        mode = values.get('mode')
        if mode == ServiceMode.HOSTED and not v:
            raise ValueError("Hosted mode requires at least one endpoint")
        return v

    @validator('import_path')
    def validate_import_path(cls, v, values):
        """Validate import path for vendor mode"""
        mode = values.get('mode')
        if mode == ServiceMode.VENDOR and not v:
            raise ValueError("Vendor mode requires import_path")
        return v

class ServiceRegistry(BaseModel):
    """Service registry configuration"""
    services: Dict[str, ServiceInfo] = Field(default_factory=dict)
    default_mode: ServiceMode = Field(ServiceMode.VENDOR)
    registry_file: str = Field("services.json")
    auto_discovery: bool = Field(True)
    health_monitoring: bool = Field(True)

# Service Discovery Implementation

class ServiceDiscovery:
    """Service discovery and registry manager"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/services.json"
        self.registry = ServiceRegistry()
        self.service_status: Dict[str, ServiceStatus] = {}
        self.endpoint_status: Dict[str, Dict[str, Any]] = {}
        self.load_balancer_state: Dict[str, Dict[str, Any]] = {}
        self.http_client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self._monitoring_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize service discovery"""
        try:
            # Initialize HTTP client
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )

            # Load service configuration
            await self._load_registry()

            # Initialize default services if not configured
            if not self.registry.services:
                await self._initialize_default_services()

            # Start health monitoring if enabled
            if self.registry.health_monitoring:
                self._monitoring_task = asyncio.create_task(self._health_monitoring_loop())

            # Perform initial health checks
            await self._perform_initial_health_checks()

            logger.info(f"Service discovery initialized with {len(self.registry.services)} services")

        except Exception as e:
            logger.error(f"Failed to initialize service discovery: {e}")
            raise

    async def shutdown(self):
        """Shutdown service discovery"""
        try:
            # Cancel monitoring task
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass

            # Close HTTP client
            if self.http_client:
                await self.http_client.aclose()

            # Save registry
            await self._save_registry()

            logger.info("Service discovery shutdown completed")

        except Exception as e:
            logger.error(f"Error during service discovery shutdown: {e}")

    async def _load_registry(self):
        """Load service registry from file"""
        try:
            if os.path.exists(self.config_path):
                async with aiofiles.open(self.config_path, 'r') as f:
                    data = await f.read()
                    registry_data = json.loads(data)
                    self.registry = ServiceRegistry(**registry_data)
                    logger.info(f"Loaded service registry from {self.config_path}")
            else:
                logger.info(f"No registry file found at {self.config_path}, using defaults")
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")

    async def _save_registry(self):
        """Save service registry to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            # Save registry
            async with aiofiles.open(self.config_path, 'w') as f:
                data = self.registry.json(indent=2)
                await f.write(data)

            logger.info(f"Saved service registry to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    async def _initialize_default_services(self):
        """Initialize default lending services"""
        default_services = {
            "collateral_analyzer": ServiceInfo(
                name="collateral_analyzer",
                mode=ServiceMode.VENDOR,
                description="Collateral analysis and valuation service",
                import_path="algorand_lending_bl.engines.collateral",
                class_name="CollateralAnalyzer",
                tags=["lending", "collateral", "analysis"],
                metadata={"engine_type": "collateral", "priority": "high"}
            ),
            "rate_calculator": ServiceInfo(
                name="rate_calculator",
                mode=ServiceMode.VENDOR,
                description="Interest rate calculation service",
                import_path="algorand_lending_bl.engines.rates",
                class_name="RateCalculator",
                tags=["lending", "rates", "calculation"],
                metadata={"engine_type": "rates", "priority": "high"}
            ),
            "loan_evaluator": ServiceInfo(
                name="loan_evaluator",
                mode=ServiceMode.VENDOR,
                description="Loan evaluation and approval service",
                import_path="algorand_lending_bl.engines.evaluation",
                class_name="LoanEvaluator",
                tags=["lending", "evaluation", "approval"],
                metadata={"engine_type": "evaluation", "priority": "critical"}
            ),
            "risk_assessor": ServiceInfo(
                name="risk_assessor",
                mode=ServiceMode.VENDOR,
                description="Risk assessment and analysis service",
                import_path="algorand_lending_bl.engines.risk",
                class_name="RiskAssessor",
                tags=["lending", "risk", "assessment"],
                metadata={"engine_type": "risk", "priority": "high"}
            )
        }

        # Check if services should be in hosted mode based on environment
        if os.getenv("LENDING_MODE") == "hosted":
            for service_name, service_info in default_services.items():
                service_info.mode = ServiceMode.HOSTED
                service_info.base_url = os.getenv(f"{service_name.upper()}_URL", f"http://localhost:800{hash(service_name) % 10}")
                service_info.health_check_url = f"{service_info.base_url}/health"
                service_info.endpoints = [
                    ServiceEndpoint(url=service_info.base_url)
                ]

        # Add services to registry
        for service_name, service_info in default_services.items():
            await self.register_service(service_info)

        logger.info(f"Initialized {len(default_services)} default services")

    async def register_service(self, service_info: ServiceInfo) -> bool:
        """Register a new service"""
        try:
            async with self._lock:
                self.registry.services[service_info.name] = service_info
                self.service_status[service_info.name] = ServiceStatus.UNKNOWN

                # Initialize load balancer state
                if service_info.mode == ServiceMode.HOSTED:
                    self.load_balancer_state[service_info.name] = {
                        "current_endpoint": 0,
                        "endpoint_weights": [ep.weight for ep in service_info.endpoints],
                        "total_requests": 0
                    }

            # Perform initial health check
            if service_info.mode == ServiceMode.HOSTED:
                await self._check_service_health(service_info.name)

            logger.info(f"Registered service: {service_info.name} ({service_info.mode})")
            return True

        except Exception as e:
            logger.error(f"Failed to register service {service_info.name}: {e}")
            return False

    async def unregister_service(self, service_name: str) -> bool:
        """Unregister a service"""
        try:
            async with self._lock:
                if service_name in self.registry.services:
                    del self.registry.services[service_name]
                if service_name in self.service_status:
                    del self.service_status[service_name]
                if service_name in self.load_balancer_state:
                    del self.load_balancer_state[service_name]

            logger.info(f"Unregistered service: {service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister service {service_name}: {e}")
            return False

    async def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Get service information"""
        return self.registry.services.get(service_name)

    async def get_service_endpoint(self, service_name: str) -> Optional[str]:
        """Get the best available endpoint for a service using load balancing"""
        service_info = await self.get_service(service_name)
        if not service_info:
            return None

        if service_info.mode == ServiceMode.VENDOR:
            return None  # No endpoint needed for vendor mode

        if not service_info.endpoints:
            return service_info.base_url

        # Select endpoint based on load balancing strategy
        endpoint = await self._select_endpoint(service_name, service_info)
        return endpoint.url if endpoint else None

    async def _select_endpoint(self, service_name: str, service_info: ServiceInfo) -> Optional[ServiceEndpoint]:
        """Select best endpoint using configured load balancing strategy"""
        if not service_info.endpoints:
            return None

        healthy_endpoints = [
            ep for ep in service_info.endpoints
            if ep.status == ServiceStatus.HEALTHY
        ]

        if not healthy_endpoints:
            # Fallback to any available endpoint
            healthy_endpoints = service_info.endpoints

        strategy = service_info.load_balancing_strategy

        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return await self._round_robin_selection(service_name, healthy_endpoints)
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(healthy_endpoints, key=lambda ep: ep.current_connections)
        elif strategy == LoadBalancingStrategy.RESPONSE_TIME:
            return min(healthy_endpoints, key=lambda ep: ep.avg_response_time)
        elif strategy == LoadBalancingStrategy.RANDOM:
            import random
            return random.choice(healthy_endpoints)
        elif strategy == LoadBalancingStrategy.FAILOVER:
            return healthy_endpoints[0]
        else:
            return healthy_endpoints[0]

    async def _round_robin_selection(self, service_name: str, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Round-robin endpoint selection"""
        if service_name not in self.load_balancer_state:
            self.load_balancer_state[service_name] = {"current_endpoint": 0}

        current = self.load_balancer_state[service_name]["current_endpoint"]
        endpoint = endpoints[current % len(endpoints)]

        # Update counter
        self.load_balancer_state[service_name]["current_endpoint"] = (current + 1) % len(endpoints)

        return endpoint

    async def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all registered services with their status"""
        services = {}
        for name, service_info in self.registry.services.items():
            services[name] = {
                "name": name,
                "mode": service_info.mode,
                "status": self.service_status.get(name, ServiceStatus.UNKNOWN),
                "version": service_info.version,
                "description": service_info.description,
                "tags": service_info.tags,
                "endpoints": len(service_info.endpoints) if service_info.endpoints else 0,
                "load_balancing": service_info.load_balancing_strategy,
                "last_updated": service_info.last_updated
            }
        return services

    async def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get current status of a service"""
        return self.service_status.get(service_name, ServiceStatus.UNKNOWN)

    async def _perform_initial_health_checks(self):
        """Perform initial health checks for all services"""
        for service_name in self.registry.services:
            await self._check_service_health(service_name)

    async def _check_service_health(self, service_name: str):
        """Check health of a specific service"""
        service_info = self.registry.services.get(service_name)
        if not service_info:
            return

        if service_info.mode == ServiceMode.VENDOR:
            # For vendor mode, check if import is possible
            try:
                # Try to import the module
                import importlib
                module = importlib.import_module(service_info.import_path)
                if hasattr(module, service_info.class_name):
                    self.service_status[service_name] = ServiceStatus.HEALTHY
                else:
                    self.service_status[service_name] = ServiceStatus.UNHEALTHY
            except Exception as e:
                logger.warning(f"Vendor service {service_name} import failed: {e}")
                self.service_status[service_name] = ServiceStatus.UNHEALTHY

        elif service_info.mode == ServiceMode.HOSTED:
            # For hosted mode, check HTTP endpoints
            await self._check_hosted_service_health(service_info)

    async def _check_hosted_service_health(self, service_info: ServiceInfo):
        """Check health of hosted service endpoints"""
        if not service_info.endpoints:
            self.service_status[service_info.name] = ServiceStatus.UNHEALTHY
            return

        healthy_count = 0
        total_count = len(service_info.endpoints)

        for endpoint in service_info.endpoints:
            try:
                start_time = time.time()

                # Use health check URL if available, otherwise use base URL
                check_url = service_info.health_check_url or f"{endpoint.url}/health"

                response = await self.http_client.get(
                    check_url,
                    timeout=service_info.timeout
                )

                response_time = time.time() - start_time

                if response.status_code == 200:
                    endpoint.status = ServiceStatus.HEALTHY
                    endpoint.avg_response_time = (
                        (endpoint.avg_response_time * 0.7) + (response_time * 0.3)
                    )
                    endpoint.health_check_failures = 0
                    healthy_count += 1
                else:
                    endpoint.status = ServiceStatus.UNHEALTHY
                    endpoint.health_check_failures += 1

                endpoint.last_health_check = time.time()

            except Exception as e:
                logger.warning(f"Health check failed for {endpoint.url}: {e}")
                endpoint.status = ServiceStatus.UNHEALTHY
                endpoint.health_check_failures += 1
                endpoint.last_health_check = time.time()

        # Update overall service status
        if healthy_count == 0:
            self.service_status[service_info.name] = ServiceStatus.UNHEALTHY
        elif healthy_count < total_count:
            self.service_status[service_info.name] = ServiceStatus.DEGRADED
        else:
            self.service_status[service_info.name] = ServiceStatus.HEALTHY

    async def _health_monitoring_loop(self):
        """Background task for continuous health monitoring"""
        while True:
            try:
                for service_name in list(self.registry.services.keys()):
                    await self._check_service_health(service_name)

                # Wait for next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                logger.info("Health monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(30)

    async def update_service_config(self, service_name: str, updates: Dict[str, Any]) -> bool:
        """Update service configuration"""
        try:
            async with self._lock:
                if service_name not in self.registry.services:
                    return False

                service_info = self.registry.services[service_name]

                # Update fields
                for key, value in updates.items():
                    if hasattr(service_info, key):
                        setattr(service_info, key, value)

                # Update timestamp
                service_info.last_updated = datetime.utcnow().isoformat()

            # Save registry
            await self._save_registry()

            logger.info(f"Updated configuration for service: {service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update service config for {service_name}: {e}")
            return False

    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get service discovery metrics"""
        total_services = len(self.registry.services)
        healthy_services = sum(
            1 for status in self.service_status.values()
            if status == ServiceStatus.HEALTHY
        )

        vendor_services = sum(
            1 for service in self.registry.services.values()
            if service.mode == ServiceMode.VENDOR
        )

        hosted_services = sum(
            1 for service in self.registry.services.values()
            if service.mode == ServiceMode.HOSTED
        )

        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "vendor_services": vendor_services,
            "hosted_services": hosted_services,
            "service_status": dict(self.service_status),
            "timestamp": datetime.utcnow().isoformat()
        }