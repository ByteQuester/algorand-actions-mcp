"""
Health Checks and Monitoring Endpoints

Provides comprehensive health monitoring for the Algorand lending platform,
including service health checks, system metrics, database connectivity,
external service dependencies, and performance monitoring.

Features:
- Service health monitoring with detailed status reporting
- Database and external service connectivity checks
- System resource monitoring (CPU, memory, disk)
- Performance metrics and response time tracking
- Dependency health checking
- Alerting and notification capabilities
- Prometheus-compatible metrics export
- Health check scheduling and automation
"""

import asyncio
import json
import logging
import psutil
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import os
import platform

import httpx
import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import asyncpg

logger = logging.getLogger(__name__)

# Prometheus metrics for health monitoring
HEALTH_CHECK_COUNT = Counter('health_checks_total', 'Total health checks', ['service', 'status'])
HEALTH_CHECK_DURATION = Histogram('health_check_duration_seconds', 'Health check duration', ['service'])
SERVICE_AVAILABILITY = Gauge('service_availability', 'Service availability', ['service'])
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_percent', 'System memory usage percentage')
SYSTEM_DISK_USAGE = Gauge('system_disk_usage_percent', 'System disk usage percentage')

# Enums and Models

class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ComponentType(str, Enum):
    """Types of system components"""
    SERVICE = "service"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    BLOCKCHAIN = "blockchain"

@dataclass
class HealthCheckResult:
    """Individual health check result"""
    component: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SystemMetrics(BaseModel):
    """System resource metrics"""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    disk_io: Dict[str, int]
    load_average: List[float]
    uptime_seconds: float
    timestamp: str

class ServiceHealth(BaseModel):
    """Individual service health information"""
    service_name: str
    status: HealthStatus
    version: Optional[str] = None
    response_time_ms: float
    last_check: str
    uptime_seconds: Optional[float] = None
    error_rate: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)

class OverallHealth(BaseModel):
    """Overall system health summary"""
    status: HealthStatus
    version: str
    timestamp: str
    uptime_seconds: float
    services: List[ServiceHealth]
    system_metrics: SystemMetrics
    dependencies: List[HealthCheckResult]
    summary: Dict[str, Any]

class HealthCheckConfig(BaseModel):
    """Health check configuration"""
    enabled: bool = True
    interval_seconds: int = 30
    timeout_seconds: int = 10
    retries: int = 3
    alert_thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "cpu_usage": 80.0,
        "memory_usage": 85.0,
        "disk_usage": 90.0,
        "response_time": 5000.0
    })

# Health Check Implementations

class DatabaseHealthChecker:
    """Database connectivity and health checker"""

    def __init__(self):
        self.connection_pool: Optional[asyncpg.Pool] = None

    async def check_postgresql(self, connection_string: str) -> HealthCheckResult:
        """Check PostgreSQL database health"""
        start_time = time.time()
        try:
            # Test connection
            conn = await asyncpg.connect(connection_string)

            # Run simple query
            result = await conn.fetchval("SELECT 1")

            # Check database stats
            stats = await conn.fetchrow("""
                SELECT
                    count(*) as total_connections,
                    sum(case when state = 'active' then 1 else 0 end) as active_connections
                FROM pg_stat_activity
            """)

            await conn.close()

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="postgresql",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat(),
                details={
                    "query_result": result,
                    "total_connections": stats["total_connections"],
                    "active_connections": stats["active_connections"]
                }
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="postgresql",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.UNHEALTHY,
                message="Database connection failed",
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat(),
                error=str(e)
            )

class CacheHealthChecker:
    """Cache service health checker"""

    async def check_redis(self, redis_url: str = "redis://localhost:6379") -> HealthCheckResult:
        """Check Redis cache health"""
        start_time = time.time()
        try:
            redis_client = redis.from_url(redis_url)

            # Test basic operations
            await redis_client.ping()
            await redis_client.set("health_check", "test", ex=10)
            result = await redis_client.get("health_check")
            await redis_client.delete("health_check")

            # Get Redis info
            info = await redis_client.info()

            await redis_client.close()

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="redis",
                component_type=ComponentType.CACHE,
                status=HealthStatus.HEALTHY,
                message="Redis cache operational",
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat(),
                details={
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory": info.get("used_memory_human"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses")
                }
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="redis",
                component_type=ComponentType.CACHE,
                status=HealthStatus.UNHEALTHY,
                message="Redis cache unavailable",
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat(),
                error=str(e)
            )

class BlockchainHealthChecker:
    """Algorand blockchain connectivity checker"""

    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None

    async def check_algorand_node(self, node_url: str = "https://testnet-api.algonode.cloud") -> HealthCheckResult:
        """Check Algorand node connectivity"""
        start_time = time.time()
        try:
            if not self.http_client:
                self.http_client = httpx.AsyncClient(timeout=10.0)

            # Get node status
            response = await self.http_client.get(f"{node_url}/v2/status")
            response.raise_for_status()

            status_data = response.json()

            # Get node health
            health_response = await self.http_client.get(f"{node_url}/health")

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="algorand_node",
                component_type=ComponentType.BLOCKCHAIN,
                status=HealthStatus.HEALTHY if health_response.status_code == 200 else HealthStatus.DEGRADED,
                message="Algorand node accessible",
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat(),
                details={
                    "last_round": status_data.get("last-round"),
                    "last_consensus_version": status_data.get("last-consensus-version"),
                    "next_version": status_data.get("next-version"),
                    "next_version_round": status_data.get("next-version-round"),
                    "next_version_supported": status_data.get("next-version-supported"),
                    "time_since_last_round": status_data.get("time-since-last-round"),
                    "catchup_time": status_data.get("catchup-time")
                }
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="algorand_node",
                component_type=ComponentType.BLOCKCHAIN,
                status=HealthStatus.UNHEALTHY,
                message="Algorand node unreachable",
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat(),
                error=str(e)
            )

class ExternalServiceHealthChecker:
    """External service dependency checker"""

    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None

    async def check_external_service(self, name: str, url: str, expected_status: int = 200) -> HealthCheckResult:
        """Check external service health"""
        start_time = time.time()
        try:
            if not self.http_client:
                self.http_client = httpx.AsyncClient(timeout=10.0)

            response = await self.http_client.get(url)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == expected_status:
                status = HealthStatus.HEALTHY
                message = f"External service {name} is healthy"
            else:
                status = HealthStatus.DEGRADED
                message = f"External service {name} returned unexpected status: {response.status_code}"

            return HealthCheckResult(
                component=name,
                component_type=ComponentType.EXTERNAL_API,
                status=status,
                message=message,
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat(),
                details={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "response_size": len(response.content)
                }
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component=name,
                component_type=ComponentType.EXTERNAL_API,
                status=HealthStatus.UNHEALTHY,
                message=f"External service {name} is unreachable",
                response_time_ms=response_time,
                timestamp=datetime.utcnow().isoformat(),
                error=str(e)
            )

class SystemResourceChecker:
    """System resource monitoring"""

    def get_system_metrics(self) -> SystemMetrics:
        """Get current system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100

            # Network I/O
            network_io = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            }

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_stats = {
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes
            }

            # Load average (Unix only)
            try:
                load_avg = list(os.getloadavg())
            except (OSError, AttributeError):
                load_avg = [0.0, 0.0, 0.0]  # Windows fallback

            # System uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time

            # Update Prometheus metrics
            SYSTEM_CPU_USAGE.set(cpu_percent)
            SYSTEM_MEMORY_USAGE.set(memory_percent)
            SYSTEM_DISK_USAGE.set(disk_percent)

            return SystemMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory_percent,
                disk_usage_percent=disk_percent,
                network_io=network_stats,
                disk_io=disk_stats,
                load_average=load_avg,
                uptime_seconds=uptime,
                timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            # Return default metrics on error
            return SystemMetrics(
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                disk_usage_percent=0.0,
                network_io={},
                disk_io={},
                load_average=[0.0, 0.0, 0.0],
                uptime_seconds=0.0,
                timestamp=datetime.utcnow().isoformat()
            )

# Main Health Checker Class

class HealthChecker:
    """Main health checking coordinator"""

    def __init__(self, config: Optional[HealthCheckConfig] = None):
        self.config = config or HealthCheckConfig()
        self.start_time = time.time()

        # Component checkers
        self.db_checker = DatabaseHealthChecker()
        self.cache_checker = CacheHealthChecker()
        self.blockchain_checker = BlockchainHealthChecker()
        self.external_checker = ExternalServiceHealthChecker()
        self.system_checker = SystemResourceChecker()

        # Health check registry
        self.health_checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}
        self._monitoring_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize health checker"""
        try:
            # Register default health checks
            await self._register_default_checks()

            # Start monitoring if enabled
            if self.config.enabled:
                self._monitoring_task = asyncio.create_task(self._monitoring_loop())

            logger.info("Health checker initialized")

        except Exception as e:
            logger.error(f"Failed to initialize health checker: {e}")
            raise

    async def shutdown(self):
        """Shutdown health checker"""
        try:
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass

            # Close HTTP clients
            if hasattr(self.blockchain_checker, 'http_client') and self.blockchain_checker.http_client:
                await self.blockchain_checker.http_client.aclose()

            if hasattr(self.external_checker, 'http_client') and self.external_checker.http_client:
                await self.external_checker.http_client.aclose()

            logger.info("Health checker shutdown completed")

        except Exception as e:
            logger.error(f"Error during health checker shutdown: {e}")

    async def _register_default_checks(self):
        """Register default health checks"""
        # Database checks
        if os.getenv("DATABASE_URL"):
            self.health_checks["postgresql"] = lambda: self.db_checker.check_postgresql(
                os.getenv("DATABASE_URL")
            )

        # Cache checks
        if os.getenv("REDIS_URL") or os.getenv("REDIS_HOST"):
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.health_checks["redis"] = lambda: self.cache_checker.check_redis(redis_url)

        # Blockchain checks
        algorand_url = os.getenv("ALGORAND_NODE_URL", "https://testnet-api.algonode.cloud")
        self.health_checks["algorand"] = lambda: self.blockchain_checker.check_algorand_node(algorand_url)

        # External service checks
        external_services = {
            "market_data": os.getenv("MARKET_DATA_API_URL"),
            "price_oracle": os.getenv("PRICE_ORACLE_URL"),
            "notification_service": os.getenv("NOTIFICATION_SERVICE_URL")
        }

        for name, url in external_services.items():
            if url:
                self.health_checks[name] = lambda u=url, n=name: self.external_checker.check_external_service(n, u)

    async def check_all_services(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks"""
        results = {}

        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                result = await check_func()

                # Update metrics
                duration = time.time() - start_time
                HEALTH_CHECK_DURATION.labels(service=name).observe(duration)
                HEALTH_CHECK_COUNT.labels(service=name, status=result.status.value).inc()
                SERVICE_AVAILABILITY.labels(service=name).set(
                    1.0 if result.status == HealthStatus.HEALTHY else 0.0
                )

                results[name] = result
                self.last_results[name] = result

            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                result = HealthCheckResult(
                    component=name,
                    component_type=ComponentType.SERVICE,
                    status=HealthStatus.UNKNOWN,
                    message=f"Health check failed: {str(e)}",
                    response_time_ms=0.0,
                    timestamp=datetime.utcnow().isoformat(),
                    error=str(e)
                )
                results[name] = result
                HEALTH_CHECK_COUNT.labels(service=name, status="error").inc()

        return results

    async def get_overall_health(self) -> OverallHealth:
        """Get comprehensive health status"""
        # Run all health checks
        dependency_results = await self.check_all_services()

        # Get system metrics
        system_metrics = self.system_checker.get_system_metrics()

        # Calculate overall status
        overall_status = self._calculate_overall_status(dependency_results, system_metrics)

        # Build service health list
        services = []
        for name, result in dependency_results.items():
            services.append(ServiceHealth(
                service_name=name,
                status=result.status,
                response_time_ms=result.response_time_ms,
                last_check=result.timestamp,
                details=result.details or {}
            ))

        # Create summary
        summary = {
            "total_checks": len(dependency_results),
            "healthy_checks": sum(1 for r in dependency_results.values() if r.status == HealthStatus.HEALTHY),
            "critical_issues": sum(1 for r in dependency_results.values() if r.status == HealthStatus.CRITICAL),
            "platform_info": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "architecture": platform.architecture()[0]
            }
        }

        return OverallHealth(
            status=overall_status,
            version="1.0.0",  # Should come from app config
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=time.time() - self.start_time,
            services=services,
            system_metrics=system_metrics,
            dependencies=list(dependency_results.values()),
            summary=summary
        )

    def _calculate_overall_status(self, dependency_results: Dict[str, HealthCheckResult], system_metrics: SystemMetrics) -> HealthStatus:
        """Calculate overall system health status"""
        # Check for critical issues
        critical_count = sum(1 for r in dependency_results.values() if r.status == HealthStatus.CRITICAL)
        if critical_count > 0:
            return HealthStatus.CRITICAL

        # Check for unhealthy services
        unhealthy_count = sum(1 for r in dependency_results.values() if r.status == HealthStatus.UNHEALTHY)
        total_count = len(dependency_results)

        if total_count > 0 and unhealthy_count / total_count > 0.5:
            return HealthStatus.UNHEALTHY

        # Check system resource thresholds
        thresholds = self.config.alert_thresholds
        if (system_metrics.cpu_usage_percent > thresholds.get("cpu_usage", 80) or
            system_metrics.memory_usage_percent > thresholds.get("memory_usage", 85) or
            system_metrics.disk_usage_percent > thresholds.get("disk_usage", 90)):
            return HealthStatus.DEGRADED

        # Check for degraded services
        degraded_count = sum(1 for r in dependency_results.values() if r.status == HealthStatus.DEGRADED)
        if degraded_count > 0:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.config.interval_seconds)

            except asyncio.CancelledError:
                logger.info("Health monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.config.interval_seconds)

# FastAPI Router

router = APIRouter(prefix="/health", tags=["Health"])

# Global health checker instance
health_checker = HealthChecker()

@router.get("/", response_model=OverallHealth, summary="Overall system health")
async def get_health():
    """Get comprehensive system health status"""
    try:
        return await health_checker.get_overall_health()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check service unavailable")

@router.get("/quick", summary="Quick health check")
async def quick_health():
    """Quick health check for load balancers"""
    try:
        # Simple check - if we can respond, we're alive
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": time.time() - health_checker.start_time
        }
    except Exception:
        raise HTTPException(status_code=503, detail="Service unavailable")

@router.get("/services", summary="Service health status")
async def get_services_health():
    """Get health status of all monitored services"""
    try:
        results = await health_checker.check_all_services()
        return {
            "services": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Service health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service health check failed")

@router.get("/system", response_model=SystemMetrics, summary="System resource metrics")
async def get_system_metrics():
    """Get current system resource metrics"""
    try:
        return health_checker.system_checker.get_system_metrics()
    except Exception as e:
        logger.error(f"System metrics failed: {e}")
        raise HTTPException(status_code=500, detail="System metrics unavailable")

@router.get("/metrics", summary="Prometheus metrics")
async def get_prometheus_metrics():
    """Get Prometheus-compatible metrics"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/readiness", summary="Readiness probe")
async def readiness_probe():
    """Kubernetes readiness probe endpoint"""
    try:
        # Check critical dependencies
        results = await health_checker.check_all_services()

        # Consider service ready if no critical failures
        critical_failures = [
            r for r in results.values()
            if r.status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]
            and r.component_type in [ComponentType.DATABASE, ComponentType.SERVICE]
        ]

        if critical_failures:
            raise HTTPException(status_code=503, detail="Service not ready")

        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        raise HTTPException(status_code=503, detail="Readiness check failed")

@router.get("/liveness", summary="Liveness probe")
async def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    try:
        # Simple liveness check - if we can respond, we're alive
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": time.time() - health_checker.start_time
        }
    except Exception as e:
        logger.error(f"Liveness probe failed: {e}")
        raise HTTPException(status_code=503, detail="Service not responding")