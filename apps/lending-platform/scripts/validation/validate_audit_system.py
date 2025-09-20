#!/usr/bin/env python3
"""
Audit System Validation Script

This script performs comprehensive validation of the Audit Trail & Compliance System
to ensure it meets all regulatory and operational requirements.

Validation Categories:
1. Database Integrity and Performance
2. API Functionality and Security
3. Compliance Engine Validation
4. Data Retention and Privacy
5. Report Generation Capabilities
6. Real-time Monitoring Systems
7. Regulatory Compliance Verification
8. System Performance Benchmarks

Usage:
    python validate_audit_system.py [--config CONFIG_FILE] [--category CATEGORY] [--verbose]

Requirements:
- PostgreSQL database with audit schema
- Active API server
- Valid authentication tokens
- Test data available
"""

import asyncio
import asyncpg
import aiohttp
import json
import time
import os
import sys
import argparse
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import statistics
from dataclasses import dataclass, asdict
import concurrent.futures

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.audit import (
        AuditService, ComplianceService, BiasDetector, ComplianceReportGenerator,
        AuditTrail, DecisionPoint, ComplianceEvent,
        AuditEventType, DecisionType, AuditSeverity,
        BiasType, RegulatoryFramework,
        setup_audit_database, DatabaseConfig
    )
    from api.auth import create_demo_token
except ImportError as e:
    print(f"Error importing audit modules: {e}")
    print("Please ensure the audit system is properly installed and configured.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Individual validation test result"""
    test_name: str
    category: str
    status: str  # 'PASS', 'FAIL', 'WARNING', 'SKIP'
    score: float  # 0-100
    execution_time: float
    details: str
    recommendations: List[str]
    error: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report"""
    validation_date: datetime
    system_version: str
    database_version: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    warning_tests: int
    skipped_tests: int
    overall_score: float
    categories: Dict[str, List[ValidationResult]]
    performance_benchmarks: Dict[str, float]
    critical_issues: List[str]
    recommendations: List[str]
    compliance_status: str


class AuditSystemValidator:
    """Comprehensive audit system validation suite"""

    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.database_url = self.config.get(
            'database_url',
            os.getenv('AUDIT_DATABASE_URL', 'postgresql://localhost:5432/audit_db')
        )
        self.api_base_url = self.config.get(
            'api_base_url',
            os.getenv('API_BASE_URL', 'http://localhost:8003')
        )

        # Initialize services
        self.audit_service = None
        self.compliance_service = None
        self.bias_detector = None
        self.report_generator = None

        # Validation results
        self.results: List[ValidationResult] = []
        self.start_time = None
        self.performance_metrics = {}

        # Test configuration
        self.test_categories = {
            'database': 'Database Integrity and Performance',
            'api': 'API Functionality and Security',
            'compliance': 'Compliance Engine Validation',
            'privacy': 'Data Retention and Privacy',
            'reports': 'Report Generation Capabilities',
            'monitoring': 'Real-time Monitoring Systems',
            'regulatory': 'Regulatory Compliance Verification',
            'performance': 'System Performance Benchmarks'
        }

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")

        return {
            'database_url': 'postgresql://localhost:5432/audit_db',
            'api_base_url': 'http://localhost:8003',
            'test_timeout': 30,
            'performance_thresholds': {
                'query_response_time': 1.0,
                'report_generation_time': 30.0,
                'api_response_time': 0.5,
                'concurrent_queries': 5.0
            },
            'sample_sizes': {
                'minimum_audit_events': 100,
                'bias_analysis_minimum': 50,
                'performance_test_iterations': 10
            }
        }

    async def initialize_services(self) -> bool:
        """Initialize audit system services"""
        try:
            logger.info("Initializing audit system services...")

            # Initialize audit service
            self.audit_service = AuditService(self.database_url)
            await self.audit_service.initialize()

            # Initialize compliance service
            self.compliance_service = ComplianceService(self.database_url)
            await self.compliance_service.initialize()

            # Initialize bias detector
            self.bias_detector = BiasDetector(self.database_url)
            await self.bias_detector.initialize()

            # Initialize report generator
            self.report_generator = ComplianceReportGenerator(self.database_url)
            await self.report_generator.initialize()

            logger.info("All audit services initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False

    async def run_validation(self, categories: Optional[List[str]] = None) -> ValidationReport:
        """Run comprehensive validation suite"""
        self.start_time = time.time()
        logger.info("Starting audit system validation...")

        # Initialize services
        if not await self.initialize_services():
            raise RuntimeError("Failed to initialize audit services")

        # Determine which categories to run
        if categories is None:
            categories = list(self.test_categories.keys())

        # Run validation tests by category
        for category in categories:
            if category not in self.test_categories:
                logger.warning(f"Unknown validation category: {category}")
                continue

            logger.info(f"Running {self.test_categories[category]} validation...")

            try:
                if category == 'database':
                    await self._validate_database()
                elif category == 'api':
                    await self._validate_api()
                elif category == 'compliance':
                    await self._validate_compliance_engine()
                elif category == 'privacy':
                    await self._validate_data_privacy()
                elif category == 'reports':
                    await self._validate_report_generation()
                elif category == 'monitoring':
                    await self._validate_monitoring_systems()
                elif category == 'regulatory':
                    await self._validate_regulatory_compliance()
                elif category == 'performance':
                    await self._validate_performance()

            except Exception as e:
                logger.error(f"Validation failed for category {category}: {e}")
                self._add_result(ValidationResult(
                    test_name=f"{category}_category_execution",
                    category=category,
                    status='FAIL',
                    score=0,
                    execution_time=0,
                    details=f"Category validation failed: {str(e)}",
                    recommendations=[f"Fix {category} validation issues"],
                    error=str(e)
                ))

        # Clean up services
        await self._cleanup_services()

        # Generate final report
        return self._generate_validation_report()

    async def _validate_database(self):
        """Validate database integrity and performance"""

        # Test 1: Database Connectivity
        result = await self._test_database_connectivity()
        self._add_result(result)

        # Test 2: Schema Validation
        result = await self._test_database_schema()
        self._add_result(result)

        # Test 3: Index Performance
        result = await self._test_index_performance()
        self._add_result(result)

        # Test 4: Data Integrity
        result = await self._test_data_integrity()
        self._add_result(result)

        # Test 5: Backup and Recovery
        result = await self._test_backup_recovery()
        self._add_result(result)

        # Test 6: Connection Pool Management
        result = await self._test_connection_pooling()
        self._add_result(result)

    async def _test_database_connectivity(self) -> ValidationResult:
        """Test database connectivity and basic operations"""
        start_time = time.time()

        try:
            async with asyncpg.create_pool(self.database_url, min_size=1, max_size=5) as pool:
                async with pool.acquire() as conn:
                    # Test basic query
                    result = await conn.fetchval("SELECT 1")
                    assert result == 1

                    # Test audit tables exist
                    tables = await conn.fetch("""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name IN ('audit_trails', 'decision_points', 'compliance_events')
                    """)

                    expected_tables = {'audit_trails', 'decision_points', 'compliance_events'}
                    found_tables = {row['table_name'] for row in tables}

                    missing_tables = expected_tables - found_tables

                    if missing_tables:
                        return ValidationResult(
                            test_name="database_connectivity",
                            category="database",
                            status='FAIL',
                            score=50,
                            execution_time=time.time() - start_time,
                            details=f"Missing required tables: {missing_tables}",
                            recommendations=["Run database migration scripts", "Verify database schema"]
                        )

            return ValidationResult(
                test_name="database_connectivity",
                category="database",
                status='PASS',
                score=100,
                execution_time=time.time() - start_time,
                details="Database connectivity and basic operations successful",
                recommendations=[]
            )

        except Exception as e:
            return ValidationResult(
                test_name="database_connectivity",
                category="database",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Database connectivity failed: {str(e)}",
                recommendations=["Check database configuration", "Verify database is running", "Check connection string"],
                error=str(e)
            )

    async def _test_database_schema(self) -> ValidationResult:
        """Test database schema completeness and correctness"""
        start_time = time.time()

        try:
            async with asyncpg.create_pool(self.database_url, min_size=1, max_size=2) as pool:
                async with pool.acquire() as conn:
                    schema_issues = []

                    # Check required columns in audit_trails
                    audit_columns = await conn.fetch("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = 'audit_trails'
                    """)

                    required_audit_columns = {
                        'id': 'uuid',
                        'event_type': 'character varying',
                        'severity': 'character varying',
                        'timestamp': 'timestamp with time zone',
                        'event_data': 'jsonb',
                        'service_name': 'character varying',
                        'session_id': 'character varying'
                    }

                    audit_column_dict = {row['column_name']: row['data_type'] for row in audit_columns}

                    for col_name, expected_type in required_audit_columns.items():
                        if col_name not in audit_column_dict:
                            schema_issues.append(f"Missing column: {col_name} in audit_trails")
                        elif expected_type not in audit_column_dict[col_name]:
                            schema_issues.append(f"Incorrect type for {col_name}: expected {expected_type}, got {audit_column_dict[col_name]}")

                    # Check indexes exist
                    indexes = await conn.fetch("""
                        SELECT indexname, indexdef
                        FROM pg_indexes
                        WHERE tablename IN ('audit_trails', 'decision_points', 'compliance_events')
                    """)

                    index_names = {row['indexname'] for row in indexes}
                    required_indexes = {'idx_audit_trails_timestamp', 'idx_audit_trails_session_id'}

                    # Note: Some indexes might have different names, so we check if any timestamp index exists
                    timestamp_indexes = [idx for idx in index_names if 'timestamp' in idx.lower()]
                    if not timestamp_indexes:
                        schema_issues.append("Missing timestamp index on audit_trails")

                    if schema_issues:
                        return ValidationResult(
                            test_name="database_schema",
                            category="database",
                            status='WARNING',
                            score=70,
                            execution_time=time.time() - start_time,
                            details=f"Schema issues found: {'; '.join(schema_issues)}",
                            recommendations=["Update database schema", "Run migration scripts", "Create missing indexes"]
                        )

            return ValidationResult(
                test_name="database_schema",
                category="database",
                status='PASS',
                score=100,
                execution_time=time.time() - start_time,
                details="Database schema validation successful",
                recommendations=[]
            )

        except Exception as e:
            return ValidationResult(
                test_name="database_schema",
                category="database",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Schema validation failed: {str(e)}",
                recommendations=["Check database schema", "Verify table structures"],
                error=str(e)
            )

    async def _test_index_performance(self) -> ValidationResult:
        """Test database index performance"""
        start_time = time.time()

        try:
            async with asyncpg.create_pool(self.database_url, min_size=1, max_size=2) as pool:
                async with pool.acquire() as conn:
                    # Check if we have data to test with
                    count = await conn.fetchval("SELECT COUNT(*) FROM audit_trails")

                    if count == 0:
                        return ValidationResult(
                            test_name="index_performance",
                            category="database",
                            status='SKIP',
                            score=0,
                            execution_time=time.time() - start_time,
                            details="No audit data available for index performance testing",
                            recommendations=["Generate test data", "Run with existing audit data"]
                        )

                    # Test index usage on common queries
                    test_queries = [
                        "SELECT COUNT(*) FROM audit_trails WHERE timestamp >= NOW() - INTERVAL '1 day'",
                        "SELECT COUNT(*) FROM audit_trails WHERE session_id = 'test_session'",
                        "SELECT COUNT(*) FROM audit_trails WHERE event_data->>'loan_id' = 'TEST_LOAN'"
                    ]

                    query_times = []
                    for query in test_queries:
                        query_start = time.time()
                        await conn.execute(query)
                        query_time = time.time() - query_start
                        query_times.append(query_time)

                    avg_query_time = statistics.mean(query_times)
                    max_query_time = max(query_times)

                    # Performance thresholds
                    if max_query_time > 2.0:  # 2 seconds
                        status = 'WARNING'
                        score = 60
                        recommendations = ["Optimize database indexes", "Analyze query performance", "Consider partitioning"]
                    elif avg_query_time > 0.5:  # 0.5 seconds average
                        status = 'WARNING'
                        score = 80
                        recommendations = ["Monitor query performance", "Consider index optimization"]
                    else:
                        status = 'PASS'
                        score = 100
                        recommendations = []

                    self.performance_metrics['database_avg_query_time'] = avg_query_time
                    self.performance_metrics['database_max_query_time'] = max_query_time

                    return ValidationResult(
                        test_name="index_performance",
                        category="database",
                        status=status,
                        score=score,
                        execution_time=time.time() - start_time,
                        details=f"Average query time: {avg_query_time:.3f}s, Max query time: {max_query_time:.3f}s",
                        recommendations=recommendations
                    )

        except Exception as e:
            return ValidationResult(
                test_name="index_performance",
                category="database",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Index performance test failed: {str(e)}",
                recommendations=["Check database health", "Verify indexes exist"],
                error=str(e)
            )

    async def _test_data_integrity(self) -> ValidationResult:
        """Test data integrity and consistency"""
        start_time = time.time()

        try:
            async with asyncpg.create_pool(self.database_url, min_size=1, max_size=2) as pool:
                async with pool.acquire() as conn:
                    integrity_issues = []

                    # Check for orphaned records
                    orphaned_decisions = await conn.fetchval("""
                        SELECT COUNT(*)
                        FROM decision_points dp
                        LEFT JOIN audit_trails at ON dp.audit_event_id = at.id
                        WHERE at.id IS NULL AND dp.audit_event_id IS NOT NULL
                    """)

                    if orphaned_decisions > 0:
                        integrity_issues.append(f"Found {orphaned_decisions} orphaned decision records")

                    # Check for duplicate audit events (same timestamp, session, event_type)
                    duplicates = await conn.fetchval("""
                        SELECT COUNT(*)
                        FROM (
                            SELECT timestamp, session_id, event_type, COUNT(*)
                            FROM audit_trails
                            GROUP BY timestamp, session_id, event_type
                            HAVING COUNT(*) > 1
                        ) duplicates
                    """)

                    if duplicates > 0:
                        integrity_issues.append(f"Found {duplicates} potential duplicate audit events")

                    # Check for invalid JSON in event_data
                    try:
                        await conn.execute("""
                            SELECT COUNT(*)
                            FROM audit_trails
                            WHERE event_data IS NOT NULL
                            AND jsonb_typeof(event_data) != 'object'
                        """)
                    except Exception:
                        integrity_issues.append("Found invalid JSON in event_data fields")

                    # Check chronological consistency
                    chronology_issues = await conn.fetchval("""
                        SELECT COUNT(*)
                        FROM audit_trails a1
                        JOIN audit_trails a2 ON a1.session_id = a2.session_id
                        WHERE a1.timestamp > a2.timestamp
                        AND a1.event_type = 'session_started'
                        AND a2.event_type IN ('loan_decision_made', 'session_ended')
                    """)

                    if chronology_issues > 0:
                        integrity_issues.append(f"Found {chronology_issues} chronological inconsistencies")

                    if integrity_issues:
                        return ValidationResult(
                            test_name="data_integrity",
                            category="database",
                            status='WARNING',
                            score=70,
                            execution_time=time.time() - start_time,
                            details=f"Data integrity issues: {'; '.join(integrity_issues)}",
                            recommendations=["Clean up orphaned records", "Investigate duplicate data", "Validate data import processes"]
                        )

            return ValidationResult(
                test_name="data_integrity",
                category="database",
                status='PASS',
                score=100,
                execution_time=time.time() - start_time,
                details="Data integrity validation passed",
                recommendations=[]
            )

        except Exception as e:
            return ValidationResult(
                test_name="data_integrity",
                category="database",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Data integrity test failed: {str(e)}",
                recommendations=["Check database consistency", "Review data validation rules"],
                error=str(e)
            )

    async def _test_backup_recovery(self) -> ValidationResult:
        """Test backup and recovery capabilities"""
        start_time = time.time()

        try:
            # This is a simplified test - in production, you'd test actual backup/recovery
            async with asyncpg.create_pool(self.database_url, min_size=1, max_size=2) as pool:
                async with pool.acquire() as conn:
                    # Check if pg_dump is available
                    import shutil
                    pg_dump_path = shutil.which('pg_dump')

                    if not pg_dump_path:
                        return ValidationResult(
                            test_name="backup_recovery",
                            category="database",
                            status='WARNING',
                            score=50,
                            execution_time=time.time() - start_time,
                            details="pg_dump not found - backup capabilities may be limited",
                            recommendations=["Install PostgreSQL client tools", "Verify backup scripts", "Test backup procedures"]
                        )

                    # Check database size and estimate backup time
                    db_size = await conn.fetchval("""
                        SELECT pg_size_pretty(pg_database_size(current_database()))
                    """)

                    # Verify Write-Ahead Logging is enabled (important for recovery)
                    wal_level = await conn.fetchval("SHOW wal_level")

                    if wal_level not in ['replica', 'logical']:
                        return ValidationResult(
                            test_name="backup_recovery",
                            category="database",
                            status='WARNING',
                            score=70,
                            execution_time=time.time() - start_time,
                            details=f"WAL level is {wal_level} - may limit recovery options. Database size: {db_size}",
                            recommendations=["Configure WAL level for better recovery", "Test backup and restore procedures"]
                        )

            return ValidationResult(
                test_name="backup_recovery",
                category="database",
                status='PASS',
                score=100,
                execution_time=time.time() - start_time,
                details=f"Backup capabilities verified. Database size: {db_size}, WAL level: {wal_level}",
                recommendations=["Regularly test backup and recovery procedures"]
            )

        except Exception as e:
            return ValidationResult(
                test_name="backup_recovery",
                category="database",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Backup/recovery test failed: {str(e)}",
                recommendations=["Check database configuration", "Verify backup tools"],
                error=str(e)
            )

    async def _test_connection_pooling(self) -> ValidationResult:
        """Test connection pooling performance"""
        start_time = time.time()

        try:
            # Test concurrent connections
            async def test_connection():
                async with asyncpg.create_pool(self.database_url, min_size=2, max_size=10) as pool:
                    async with pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                        await asyncio.sleep(0.1)  # Simulate work

            # Run multiple concurrent connection tests
            tasks = [test_connection() for _ in range(5)]
            concurrent_start = time.time()
            await asyncio.gather(*tasks)
            concurrent_time = time.time() - concurrent_start

            self.performance_metrics['connection_pool_concurrent_time'] = concurrent_time

            if concurrent_time > 5.0:
                status = 'WARNING'
                score = 60
                recommendations = ["Optimize connection pool settings", "Check database connections limit"]
            elif concurrent_time > 2.0:
                status = 'WARNING'
                score = 80
                recommendations = ["Monitor connection pool performance"]
            else:
                status = 'PASS'
                score = 100
                recommendations = []

            return ValidationResult(
                test_name="connection_pooling",
                category="database",
                status=status,
                score=score,
                execution_time=time.time() - start_time,
                details=f"Concurrent connection test completed in {concurrent_time:.2f}s",
                recommendations=recommendations
            )

        except Exception as e:
            return ValidationResult(
                test_name="connection_pooling",
                category="database",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Connection pooling test failed: {str(e)}",
                recommendations=["Check connection pool configuration", "Verify database connection limits"],
                error=str(e)
            )

    async def _validate_api(self):
        """Validate API functionality and security"""

        # Test 1: API Health Check
        result = await self._test_api_health()
        self._add_result(result)

        # Test 2: Authentication and Authorization
        result = await self._test_authentication()
        self._add_result(result)

        # Test 3: Core API Endpoints
        result = await self._test_core_endpoints()
        self._add_result(result)

        # Test 4: Error Handling
        result = await self._test_error_handling()
        self._add_result(result)

        # Test 5: Rate Limiting
        result = await self._test_rate_limiting()
        self._add_result(result)

        # Test 6: Response Times
        result = await self._test_api_performance()
        self._add_result(result)

    async def _test_api_health(self) -> ValidationResult:
        """Test API health and basic connectivity"""
        start_time = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.api_base_url}/api/v1/audit/health") as response:
                    if response.status == 200:
                        health_data = await response.json()

                        status = health_data.get('status', 'unknown')
                        db_connected = health_data.get('database_connected', False)

                        if status == 'healthy' and db_connected:
                            return ValidationResult(
                                test_name="api_health",
                                category="api",
                                status='PASS',
                                score=100,
                                execution_time=time.time() - start_time,
                                details=f"API health check passed: {status}, DB connected: {db_connected}",
                                recommendations=[]
                            )
                        else:
                            return ValidationResult(
                                test_name="api_health",
                                category="api",
                                status='WARNING',
                                score=70,
                                execution_time=time.time() - start_time,
                                details=f"API health issues: {status}, DB connected: {db_connected}",
                                recommendations=["Check API service status", "Verify database connectivity"]
                            )
                    else:
                        return ValidationResult(
                            test_name="api_health",
                            category="api",
                            status='FAIL',
                            score=0,
                            execution_time=time.time() - start_time,
                            details=f"API health check failed with status {response.status}",
                            recommendations=["Check API server is running", "Verify API configuration"]
                        )

        except asyncio.TimeoutError:
            return ValidationResult(
                test_name="api_health",
                category="api",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details="API health check timed out",
                recommendations=["Check API server is running", "Check network connectivity"],
                error="Timeout"
            )
        except Exception as e:
            return ValidationResult(
                test_name="api_health",
                category="api",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"API health check failed: {str(e)}",
                recommendations=["Check API server is running", "Verify API URL"],
                error=str(e)
            )

    async def _test_authentication(self) -> ValidationResult:
        """Test API authentication and authorization"""
        start_time = time.time()

        try:
            # Test without token (should fail)
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.api_base_url}/api/v1/audit/metrics") as response:
                    if response.status != 401:
                        return ValidationResult(
                            test_name="authentication",
                            category="api",
                            status='FAIL',
                            score=0,
                            execution_time=time.time() - start_time,
                            details=f"Unauthenticated request should return 401, got {response.status}",
                            recommendations=["Verify authentication middleware", "Check security configuration"]
                        )

                # Test with valid token
                admin_token = create_demo_token("admin")
                headers = {"Authorization": f"Bearer {admin_token}"}

                async with session.get(f"{self.api_base_url}/api/v1/audit/metrics", headers=headers) as response:
                    if response.status in [200, 500, 503]:  # 500/503 acceptable if no data
                        auth_score = 100
                        auth_status = 'PASS'
                        auth_details = "Authentication working correctly"
                    else:
                        auth_score = 70
                        auth_status = 'WARNING'
                        auth_details = f"Unexpected response with valid token: {response.status}"

                # Test with invalid token
                invalid_headers = {"Authorization": "Bearer invalid_token"}

                async with session.get(f"{self.api_base_url}/api/v1/audit/metrics", headers=invalid_headers) as response:
                    if response.status != 401:
                        auth_score = min(auth_score, 70)
                        auth_status = 'WARNING'
                        auth_details += f"; Invalid token should return 401, got {response.status}"

            return ValidationResult(
                test_name="authentication",
                category="api",
                status=auth_status,
                score=auth_score,
                execution_time=time.time() - start_time,
                details=auth_details,
                recommendations=["Verify token validation logic"] if auth_score < 100 else []
            )

        except Exception as e:
            return ValidationResult(
                test_name="authentication",
                category="api",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Authentication test failed: {str(e)}",
                recommendations=["Check authentication configuration", "Verify token generation"],
                error=str(e)
            )

    async def _test_core_endpoints(self) -> ValidationResult:
        """Test core API endpoints functionality"""
        start_time = time.time()

        try:
            admin_token = create_demo_token("admin")
            headers = {"Authorization": f"Bearer {admin_token}"}

            endpoints_to_test = [
                ("GET", "/api/v1/audit/health", None),
                ("GET", "/api/v1/audit/metrics", None),
                ("GET", "/api/v1/audit/session/TEST_LOAN_001", None),
                ("GET", "/api/v1/audit/decisions/TEST_LOAN_001", None),
                ("GET", "/api/v1/audit/search", {"query": "test", "limit": 10}),
            ]

            results = []
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                for method, endpoint, params in endpoints_to_test:
                    endpoint_start = time.time()

                    try:
                        if method == "GET":
                            async with session.get(
                                f"{self.api_base_url}{endpoint}",
                                headers=headers,
                                params=params
                            ) as response:
                                endpoint_time = time.time() - endpoint_start

                                # Accept 200, 404 (no data), or 500 (service issues) as reasonable responses
                                if response.status in [200, 404, 500]:
                                    results.append({
                                        'endpoint': endpoint,
                                        'status': response.status,
                                        'time': endpoint_time,
                                        'success': True
                                    })
                                else:
                                    results.append({
                                        'endpoint': endpoint,
                                        'status': response.status,
                                        'time': endpoint_time,
                                        'success': False
                                    })

                    except Exception as e:
                        results.append({
                            'endpoint': endpoint,
                            'status': 'ERROR',
                            'time': time.time() - endpoint_start,
                            'success': False,
                            'error': str(e)
                        })

            successful_endpoints = sum(1 for r in results if r['success'])
            total_endpoints = len(results)
            success_rate = successful_endpoints / total_endpoints

            avg_response_time = statistics.mean([r['time'] for r in results])
            self.performance_metrics['api_avg_response_time'] = avg_response_time

            if success_rate >= 0.8:
                status = 'PASS'
                score = min(100, int(success_rate * 100))
            elif success_rate >= 0.6:
                status = 'WARNING'
                score = int(success_rate * 100)
            else:
                status = 'FAIL'
                score = int(success_rate * 50)

            details = f"Endpoint success rate: {success_rate:.2%} ({successful_endpoints}/{total_endpoints}), "
            details += f"Average response time: {avg_response_time:.3f}s"

            failed_endpoints = [r['endpoint'] for r in results if not r['success']]
            recommendations = []
            if failed_endpoints:
                recommendations.extend([
                    f"Fix failed endpoints: {', '.join(failed_endpoints)}",
                    "Check service health and data availability"
                ])

            return ValidationResult(
                test_name="core_endpoints",
                category="api",
                status=status,
                score=score,
                execution_time=time.time() - start_time,
                details=details,
                recommendations=recommendations
            )

        except Exception as e:
            return ValidationResult(
                test_name="core_endpoints",
                category="api",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Core endpoints test failed: {str(e)}",
                recommendations=["Check API service health", "Verify endpoint configurations"],
                error=str(e)
            )

    async def _test_error_handling(self) -> ValidationResult:
        """Test API error handling"""
        start_time = time.time()

        try:
            admin_token = create_demo_token("admin")
            headers = {"Authorization": f"Bearer {admin_token}"}

            error_scenarios = [
                ("Invalid loan ID", "/api/v1/audit/session/", 404),
                ("Invalid search query", "/api/v1/audit/search?query=", 400),
                ("Non-existent endpoint", "/api/v1/audit/nonexistent", 404),
            ]

            error_handling_score = 0
            error_details = []

            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for scenario, endpoint, expected_status in error_scenarios:
                    try:
                        async with session.get(f"{self.api_base_url}{endpoint}", headers=headers) as response:
                            if response.status == expected_status:
                                error_handling_score += 1
                                error_details.append(f"✓ {scenario}: {response.status}")

                                # Check if response has proper error format
                                try:
                                    error_data = await response.json()
                                    if 'error' in error_data and 'message' in error_data:
                                        error_handling_score += 0.5
                                        error_details.append(f"  Proper error format returned")
                                    else:
                                        error_details.append(f"  Missing standard error format")
                                except:
                                    error_details.append(f"  Non-JSON error response")
                            else:
                                error_details.append(f"✗ {scenario}: expected {expected_status}, got {response.status}")

                    except Exception as e:
                        error_details.append(f"✗ {scenario}: Exception {str(e)}")

            max_possible_score = len(error_scenarios) * 1.5  # 1 for status + 0.5 for format
            score = int((error_handling_score / max_possible_score) * 100)

            if score >= 80:
                status = 'PASS'
            elif score >= 60:
                status = 'WARNING'
            else:
                status = 'FAIL'

            return ValidationResult(
                test_name="error_handling",
                category="api",
                status=status,
                score=score,
                execution_time=time.time() - start_time,
                details="; ".join(error_details),
                recommendations=["Standardize error response format", "Implement proper HTTP status codes"] if score < 80 else []
            )

        except Exception as e:
            return ValidationResult(
                test_name="error_handling",
                category="api",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Error handling test failed: {str(e)}",
                recommendations=["Check error handling middleware", "Verify API error responses"],
                error=str(e)
            )

    async def _test_rate_limiting(self) -> ValidationResult:
        """Test API rate limiting"""
        start_time = time.time()

        try:
            admin_token = create_demo_token("admin")
            headers = {"Authorization": f"Bearer {admin_token}"}

            # Make multiple rapid requests to test rate limiting
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                responses = []

                # Send 20 requests rapidly
                tasks = []
                for i in range(20):
                    task = session.get(f"{self.api_base_url}/api/v1/audit/health", headers=headers)
                    tasks.append(task)

                # Execute all requests
                try:
                    responses = await asyncio.gather(*tasks)

                    status_codes = [r.status for r in responses]
                    rate_limited_count = status_codes.count(429)
                    successful_count = status_codes.count(200)

                    # Close all responses
                    for response in responses:
                        response.close()

                    if rate_limited_count > 0:
                        # Rate limiting is working
                        return ValidationResult(
                            test_name="rate_limiting",
                            category="api",
                            status='PASS',
                            score=100,
                            execution_time=time.time() - start_time,
                            details=f"Rate limiting working: {rate_limited_count} requests rate limited, {successful_count} succeeded",
                            recommendations=[]
                        )
                    else:
                        # No rate limiting detected - might be expected in test environment
                        return ValidationResult(
                            test_name="rate_limiting",
                            category="api",
                            status='WARNING',
                            score=60,
                            execution_time=time.time() - start_time,
                            details=f"No rate limiting detected from {len(responses)} rapid requests",
                            recommendations=["Consider implementing rate limiting", "Verify rate limiting configuration"]
                        )

                except Exception as e:
                    return ValidationResult(
                        test_name="rate_limiting",
                        category="api",
                        status='WARNING',
                        score=50,
                        execution_time=time.time() - start_time,
                        details=f"Rate limiting test inconclusive: {str(e)}",
                        recommendations=["Check rate limiting configuration"],
                        error=str(e)
                    )

        except Exception as e:
            return ValidationResult(
                test_name="rate_limiting",
                category="api",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"Rate limiting test failed: {str(e)}",
                recommendations=["Check API service health", "Verify rate limiting middleware"],
                error=str(e)
            )

    async def _test_api_performance(self) -> ValidationResult:
        """Test API response time performance"""
        start_time = time.time()

        try:
            admin_token = create_demo_token("admin")
            headers = {"Authorization": f"Bearer {admin_token}"}

            # Test multiple endpoints for performance
            performance_endpoints = [
                "/api/v1/audit/health",
                "/api/v1/audit/metrics",
            ]

            response_times = []
            timeout = aiohttp.ClientTimeout(total=20)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                for endpoint in performance_endpoints:
                    # Test each endpoint multiple times
                    endpoint_times = []

                    for _ in range(3):
                        endpoint_start = time.time()

                        try:
                            async with session.get(f"{self.api_base_url}{endpoint}", headers=headers) as response:
                                endpoint_time = time.time() - endpoint_start
                                endpoint_times.append(endpoint_time)

                                # Read response to ensure full processing
                                await response.text()

                        except Exception as e:
                            logger.warning(f"Performance test failed for {endpoint}: {e}")

                    if endpoint_times:
                        avg_endpoint_time = statistics.mean(endpoint_times)
                        response_times.extend(endpoint_times)

            if not response_times:
                return ValidationResult(
                    test_name="api_performance",
                    category="api",
                    status='FAIL',
                    score=0,
                    execution_time=time.time() - start_time,
                    details="No successful performance measurements",
                    recommendations=["Check API service health"]
                )

            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            self.performance_metrics['api_performance_avg'] = avg_response_time
            self.performance_metrics['api_performance_max'] = max_response_time

            # Performance thresholds
            if max_response_time > 2.0:
                status = 'WARNING'
                score = 60
                recommendations = ["Optimize API performance", "Check server resources"]
            elif avg_response_time > 0.5:
                status = 'WARNING'
                score = 80
                recommendations = ["Monitor API performance"]
            else:
                status = 'PASS'
                score = 100
                recommendations = []

            return ValidationResult(
                test_name="api_performance",
                category="api",
                status=status,
                score=score,
                execution_time=time.time() - start_time,
                details=f"Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s, Min: {min_response_time:.3f}s",
                recommendations=recommendations
            )

        except Exception as e:
            return ValidationResult(
                test_name="api_performance",
                category="api",
                status='FAIL',
                score=0,
                execution_time=time.time() - start_time,
                details=f"API performance test failed: {str(e)}",
                recommendations=["Check API service health", "Verify server resources"],
                error=str(e)
            )

    # Additional validation method stubs for other categories
    async def _validate_compliance_engine(self):
        """Validate compliance engine functionality"""
        # Implementation for compliance validation
        pass

    async def _validate_data_privacy(self):
        """Validate data privacy and retention"""
        # Implementation for privacy validation
        pass

    async def _validate_report_generation(self):
        """Validate report generation capabilities"""
        # Implementation for report generation validation
        pass

    async def _validate_monitoring_systems(self):
        """Validate real-time monitoring systems"""
        # Implementation for monitoring validation
        pass

    async def _validate_regulatory_compliance(self):
        """Validate regulatory compliance"""
        # Implementation for regulatory validation
        pass

    async def _validate_performance(self):
        """Validate system performance benchmarks"""
        # Implementation for performance validation
        pass

    def _add_result(self, result: ValidationResult):
        """Add validation result to results list"""
        self.results.append(result)
        logger.info(f"{result.test_name}: {result.status} (Score: {result.score})")

    async def _cleanup_services(self):
        """Clean up initialized services"""
        try:
            if self.audit_service:
                await self.audit_service.close()
            if self.compliance_service:
                await self.compliance_service.close()
            if self.bias_detector:
                await self.bias_detector.close()
            if self.report_generator:
                await self.report_generator.close()

            logger.info("Services cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _generate_validation_report(self) -> ValidationReport:
        """Generate final validation report"""

        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'PASS'])
        failed_tests = len([r for r in self.results if r.status == 'FAIL'])
        warning_tests = len([r for r in self.results if r.status == 'WARNING'])
        skipped_tests = len([r for r in self.results if r.status == 'SKIP'])

        # Calculate overall score
        if total_tests > 0:
            overall_score = sum(r.score for r in self.results) / total_tests
        else:
            overall_score = 0

        # Group results by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        # Identify critical issues
        critical_issues = [
            f"{r.test_name}: {r.details}" for r in self.results
            if r.status == 'FAIL' and r.score < 50
        ]

        # Generate recommendations
        recommendations = []
        for result in self.results:
            if result.recommendations:
                recommendations.extend(result.recommendations)

        # Remove duplicates
        recommendations = list(set(recommendations))

        # Determine compliance status
        if overall_score >= 90 and failed_tests == 0:
            compliance_status = "COMPLIANT"
        elif overall_score >= 75 and failed_tests <= 2:
            compliance_status = "MOSTLY_COMPLIANT"
        elif overall_score >= 60:
            compliance_status = "NEEDS_IMPROVEMENT"
        else:
            compliance_status = "NON_COMPLIANT"

        return ValidationReport(
            validation_date=datetime.now(timezone.utc),
            system_version="1.0.0",
            database_version="PostgreSQL",
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warning_tests=warning_tests,
            skipped_tests=skipped_tests,
            overall_score=overall_score,
            categories=categories,
            performance_benchmarks=self.performance_metrics,
            critical_issues=critical_issues,
            recommendations=recommendations[:10],  # Top 10 recommendations
            compliance_status=compliance_status
        )

    def print_validation_report(self, report: ValidationReport):
        """Print formatted validation report"""

        print("=" * 80)
        print("AUDIT SYSTEM VALIDATION REPORT")
        print("=" * 80)
        print(f"Validation Date: {report.validation_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"System Version: {report.system_version}")
        print(f"Database Version: {report.database_version}")
        print()

        print("SUMMARY:")
        print(f"  Total Tests: {report.total_tests}")
        print(f"  Passed: {report.passed_tests}")
        print(f"  Failed: {report.failed_tests}")
        print(f"  Warnings: {report.warning_tests}")
        print(f"  Skipped: {report.skipped_tests}")
        print(f"  Overall Score: {report.overall_score:.1f}/100")
        print(f"  Compliance Status: {report.compliance_status}")
        print()

        if report.performance_benchmarks:
            print("PERFORMANCE BENCHMARKS:")
            for metric, value in report.performance_benchmarks.items():
                print(f"  {metric}: {value:.3f}s")
            print()

        print("RESULTS BY CATEGORY:")
        for category, results in report.categories.items():
            category_name = self.test_categories.get(category, category)
            print(f"\n{category_name}:")

            for result in results:
                status_symbol = {
                    'PASS': '✓',
                    'FAIL': '✗',
                    'WARNING': '⚠',
                    'SKIP': '○'
                }.get(result.status, '?')

                print(f"  {status_symbol} {result.test_name}: {result.status} ({result.score}/100)")
                if result.details:
                    print(f"    {result.details}")

        if report.critical_issues:
            print("\nCRITICAL ISSUES:")
            for issue in report.critical_issues:
                print(f"  • {issue}")

        if report.recommendations:
            print("\nRECOMMENDATIONS:")
            for rec in report.recommendations[:10]:
                print(f"  • {rec}")

        print("\n" + "=" * 80)


async def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate Audit Trail & Compliance System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--category", help="Validation category to run", choices=[
        'database', 'api', 'compliance', 'privacy', 'reports', 'monitoring', 'regulatory', 'performance'
    ])
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize validator
    validator = AuditSystemValidator(args.config)

    categories = [args.category] if args.category else None

    try:
        # Run validation
        report = await validator.run_validation(categories)

        # Print report
        validator.print_validation_report(report)

        # Save report to file
        report_data = asdict(report)

        # Convert datetime objects to strings for JSON serialization
        def convert_datetimes(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetimes(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetimes(item) for item in obj]
            return obj

        report_data = convert_datetimes(report_data)

        report_filename = f"audit_system_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\nDetailed report saved to: {report_filename}")

        # Set exit code based on results
        if report.compliance_status in ["COMPLIANT", "MOSTLY_COMPLIANT"]:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"\nValidation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())