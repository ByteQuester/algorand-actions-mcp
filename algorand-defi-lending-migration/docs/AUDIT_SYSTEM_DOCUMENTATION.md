# Audit Trail & Compliance System Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [API Reference](#api-reference)
5. [Usage Guides](#usage-guides)
6. [Performance Characteristics](#performance-characteristics)
7. [Error Handling](#error-handling)
8. [Security and Access Control](#security-and-access-control)
9. [Deployment Guide](#deployment-guide)
10. [Troubleshooting](#troubleshooting)

## System Overview

The Audit Trail & Compliance System is a production-ready, high-performance audit solution designed specifically for regulated financial services. It provides comprehensive tracking, analysis, and reporting capabilities for all lending decisions and transactions on the Algorand blockchain.

### Key Features

- **Complete Decision Traceability**: 100% audit trail coverage for all lending decisions
- **Real-time Event Capture**: Sub-second event processing and storage
- **Regulatory Compliance**: Built-in support for ECOA, Fair Lending Act, CRA, TILA, and other frameworks
- **Bias Detection**: Automated statistical analysis for fair lending compliance
- **High Performance**: Sub-second query responses for up to 10M+ audit records
- **Immutable Audit Trails**: Cryptographically verifiable audit chains
- **Advanced Analytics**: Statistical bias detection and compliance reporting

### Business Value

- **Regulatory Compliance**: Ensure full compliance with financial regulations
- **Risk Management**: Early detection of bias and compliance issues
- **Operational Transparency**: Complete visibility into all lending decisions
- **Audit Readiness**: Always-ready audit trails for regulatory examinations
- **Performance Optimization**: Identify bottlenecks and improvement opportunities

## Architecture

### System Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Lending       │    │   Audit Trail   │    │   Compliance    │
│   Platform      │───▶│   Capture       │───▶│   Analysis      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Real-time     │    │   Audit         │    │   Report        │
│   Streaming     │◀───│   Database      │───▶│   Generation    │
│                 │    │   (PostgreSQL)  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Event         │    │   API           │    │   Dashboard     │
│   Processing    │    │   Gateway       │    │   & Analytics   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Event Capture**: All lending platform activities generate audit events
2. **Real-time Processing**: Events are processed and stored in <100ms
3. **Compliance Analysis**: Automated bias detection and compliance checks
4. **Report Generation**: On-demand and scheduled compliance reports
5. **API Access**: RESTful API for programmatic access to audit data

### Technology Stack

- **Database**: PostgreSQL 14+ with JSONB and full-text search
- **Backend**: Python 3.11+ with AsyncIO
- **API Framework**: FastAPI with async support
- **Analytics**: NumPy, SciPy, Pandas for statistical analysis
- **Deployment**: Docker containers with Kubernetes support

## Core Components

### 1. Audit Service (`AuditService`)

The primary service for audit data retrieval and analysis.

**Key Capabilities:**
- Session timeline reconstruction
- Decision reasoning chain analysis
- Tool usage analytics
- Full-text search across audit data
- High-performance concurrent queries

**Example Usage:**
```python
from src.core.audit import AuditService

# Initialize service
audit_service = AuditService(database_url)
await audit_service.initialize()

# Get complete audit trail for a loan
timeline = await audit_service.get_session_timeline("LOAN_001")

# Get all decisions with reasoning
decisions = await audit_service.get_decision_breakdown("LOAN_001")

# Analyze tool performance
tools = await audit_service.get_tool_usage_analysis("LOAN_001")
```

### 2. Compliance Service (`ComplianceService`)

Advanced compliance analysis and bias detection service.

**Key Capabilities:**
- Regulatory framework compliance checking
- Statistical bias detection (ECOA, Fair Lending)
- Interest rate justification analysis
- Decision consistency validation
- Automated violation detection

**Example Usage:**
```python
from src.core.audit import ComplianceService, RegulatoryFramework

compliance_service = ComplianceService(database_url)
await compliance_service.initialize()

# Generate compliance metrics
metrics = await compliance_service.generate_compliance_metrics(
    start_date=start_date,
    end_date=end_date,
    frameworks=[RegulatoryFramework.ECOA, RegulatoryFramework.FAIR_LENDING_ACT]
)

# Detect bias in lending decisions
loan_data = [...]  # Your loan data
bias_results = await compliance_service.detect_bias(loan_data)

# Justify interest rate assignment
justification = await compliance_service.justify_interest_rate(
    loan_id="LOAN_001",
    borrower_profile=profile,
    assigned_rate=5.25
)
```

### 3. Report Generator (`ComplianceReportGenerator`)

Generates comprehensive compliance and regulatory reports.

**Key Capabilities:**
- Executive summary generation
- Detailed bias analysis reports
- Regulatory compliance status
- Performance metrics analysis
- Custom report configurations

**Example Usage:**
```python
from src.core.audit import ComplianceReportGenerator, ReportConfiguration

report_generator = ComplianceReportGenerator(database_url)
await report_generator.initialize()

# Configure report
config = ReportConfiguration(
    report_type="comprehensive_compliance",
    date_range=(start_date, end_date),
    regulatory_frameworks=[RegulatoryFramework.ECOA],
    include_bias_analysis=True,
    include_decision_breakdown=True
)

# Generate report (completes in <30 seconds)
report = await report_generator.generate_comprehensive_report(config)
```

### 4. Event Streaming Service (`EventStreamingService`)

Real-time event processing and streaming capabilities.

**Key Capabilities:**
- Real-time event ingestion
- Event filtering and routing
- Stream processing
- Event validation
- Error handling and retry logic

### 5. Bias Detector (`BiasDetector`)

Specialized service for detecting bias in lending decisions.

**Key Capabilities:**
- Approval rate bias detection
- Interest rate bias analysis
- Loan amount disparities
- Geographic bias detection
- Statistical significance testing

## API Reference

### Base URL
```
http://localhost:8003/api/v1/audit
```

### Authentication
All API endpoints require bearer token authentication:
```
Authorization: Bearer <your_token>
```

### Core Endpoints

#### 1. Get Session Timeline
Retrieve complete session timeline for a loan.

```http
GET /session/{loan_id}
```

**Parameters:**
- `loan_id` (string, required): The loan ID to retrieve timeline for

**Response:**
```json
{
  "loan_id": "LOAN_001",
  "total_events": 15,
  "total_sessions": 2,
  "timeline_start": "2024-01-01T10:00:00Z",
  "timeline_end": "2024-01-01T10:30:00Z",
  "sessions": [...],
  "events": [...]
}
```

#### 2. Get Decision Breakdown
Retrieve decision breakdown with reasoning chains.

```http
GET /decisions/{loan_id}
```

**Response:**
```json
{
  "loan_id": "LOAN_001",
  "total_decisions": 3,
  "decision_types": ["credit_approval", "interest_rate_setting"],
  "average_risk_score": 45.2,
  "average_confidence": 0.87,
  "decision_chain": [...],
  "decisions": [...]
}
```

#### 3. Get Tool Usage Analysis
Retrieve tool usage and performance analysis.

```http
GET /tools/{loan_id}
```

**Response:**
```json
{
  "loan_id": "LOAN_001",
  "total_tool_executions": 8,
  "unique_tools_used": 5,
  "total_errors": 0,
  "total_warnings": 1,
  "success_rate": 1.0,
  "average_processing_time_ms": 250.5,
  "tool_performance": [...],
  "tool_executions": [...]
}
```

#### 4. Search Audit Events
Search audit events using full-text search.

```http
GET /search?query={query}&loan_id={loan_id}&limit={limit}
```

**Parameters:**
- `query` (string, required): Search query string
- `loan_id` (string, optional): Filter by loan ID
- `start_date` (datetime, optional): Filter by start date
- `end_date` (datetime, optional): Filter by end date
- `limit` (integer, optional): Maximum results (default: 100)

**Response:**
```json
{
  "query": "credit approval",
  "total_results": 25,
  "filters": {...},
  "events": [...]
}
```

#### 5. Get Raw Events
Retrieve raw audit events for detailed analysis.

```http
GET /events/{session_id}?limit={limit}&offset={offset}
```

**Response:**
```json
{
  "session_id": "session_123",
  "total_events": 50,
  "returned_events": 10,
  "limit": 10,
  "offset": 0,
  "has_more": true,
  "events": [...]
}
```

#### 6. Get Visual Timeline Data
Retrieve timeline data optimized for visualization.

```http
GET /timeline/{loan_id}
```

**Response:**
```json
{
  "loan_id": "LOAN_001",
  "timeline_buckets": 15,
  "event_types": ["application", "decision", "funding"],
  "severity_distribution": {"info": 12, "warning": 2, "error": 1},
  "milestones": [...],
  "timeline_data": [...],
  "visualization_ready": true
}
```

#### 7. Health Check
Check service health and status.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database_connected": true,
  "connection_pool_size": 10,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Error Responses

All endpoints return standardized error responses:

```json
{
  "error": "AuditNotFoundError",
  "message": "No audit data found for loan LOAN_001",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

**Common Error Codes:**
- `400`: Invalid request parameters
- `401`: Unauthorized (invalid or missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Audit data not found
- `500`: Internal server error

## Usage Guides

### For Compliance Officers

#### Daily Compliance Monitoring

1. **Monitor Real-time Metrics**
   ```python
   # Get today's compliance metrics
   today = datetime.now(timezone.utc)
   yesterday = today - timedelta(days=1)

   metrics = await compliance_service.generate_compliance_metrics(
       start_date=yesterday,
       end_date=today
   )

   if metrics.compliance_score < 0.9:
       # Alert: Compliance score below threshold
       alert_compliance_team(metrics)
   ```

2. **Weekly Bias Analysis**
   ```python
   # Weekly bias detection report
   loan_data = await get_recent_loans(days=7)
   bias_results = await compliance_service.detect_bias(loan_data)

   high_severity_bias = [b for b in bias_results
                        if b.detected and b.severity_score > 0.7]

   if high_severity_bias:
       generate_bias_alert_report(high_severity_bias)
   ```

#### Regulatory Examination Preparation

1. **Generate Comprehensive Reports**
   ```python
   # Quarterly compliance report
   config = ReportConfiguration(
       report_type="regulatory_examination",
       date_range=(quarter_start, quarter_end),
       regulatory_frameworks=[
           RegulatoryFramework.ECOA,
           RegulatoryFramework.FAIR_LENDING_ACT,
           RegulatoryFramework.CRA
       ],
       include_bias_analysis=True,
       include_decision_breakdown=True,
       include_performance_metrics=True
   )

   report = await report_generator.generate_comprehensive_report(config)
   save_report_for_examination(report)
   ```

### For Auditors

#### Loan Decision Investigation

1. **Complete Audit Trail Analysis**
   ```python
   # Investigate specific loan decision
   loan_id = "LOAN_UNDER_REVIEW"

   # Get complete timeline
   timeline = await audit_service.get_session_timeline(loan_id)

   # Get decision breakdown
   decisions = await audit_service.get_decision_breakdown(loan_id)

   # Analyze tool usage
   tools = await audit_service.get_tool_usage_analysis(loan_id)

   # Generate investigation report
   investigation_report = {
       "loan_id": loan_id,
       "timeline": timeline,
       "decisions": decisions,
       "tools": tools,
       "findings": analyze_for_irregularities(timeline, decisions, tools)
   }
   ```

2. **Pattern Analysis Across Multiple Loans**
   ```python
   # Search for patterns across multiple loans
   search_results = await audit_service.search_audit_events(
       query="high_risk_approval",
       start_date=month_start,
       end_date=month_end,
       limit=500
   )

   # Analyze patterns
   patterns = analyze_decision_patterns(search_results["events"])
   ```

### For Developers

#### Custom Analytics Implementation

1. **Custom Bias Detection Algorithm**
   ```python
   class CustomBiasDetector:
       def __init__(self, audit_service: AuditService):
           self.audit_service = audit_service

       async def detect_geographic_bias(self, loan_data: List[Dict]) -> BiasAnalysisResult:
           # Implement custom geographic bias detection
           zip_code_groups = group_by_zip_code(loan_data)
           statistical_test_result = perform_anova_test(zip_code_groups)

           return BiasAnalysisResult(
               bias_type=BiasType.GEOGRAPHIC_BIAS,
               detected=statistical_test_result.p_value < 0.05,
               severity_score=calculate_severity(statistical_test_result),
               p_value=statistical_test_result.p_value,
               # ... other fields
           )
   ```

2. **Performance Monitoring Dashboard**
   ```python
   async def get_system_performance_metrics():
       # Database performance
       db_metrics = await get_database_metrics()

       # API performance
       api_metrics = await get_api_performance()

       # Audit processing performance
       processing_metrics = await get_processing_performance()

       return {
           "database": db_metrics,
           "api": api_metrics,
           "processing": processing_metrics,
           "overall_health": calculate_overall_health()
       }
   ```

### For Risk Management Teams

#### Risk Monitoring and Alerting

1. **Automated Risk Alerts**
   ```python
   class RiskMonitor:
       async def monitor_lending_risks(self):
           # Check for unusual approval patterns
           recent_loans = await get_recent_loans(hours=24)

           # Detect anomalies
           anomalies = await detect_approval_anomalies(recent_loans)

           # High-risk pattern detection
           high_risk_patterns = await detect_high_risk_patterns(recent_loans)

           if anomalies or high_risk_patterns:
               await send_risk_alert(anomalies, high_risk_patterns)
   ```

## Performance Characteristics

### Database Performance

- **Query Response Time**: <1 second for 95% of queries
- **Concurrent Users**: Support for 100+ concurrent users
- **Data Volume**: Optimized for 10M+ audit records
- **Storage Efficiency**: JSONB compression reduces storage by 40%

### API Performance

- **Throughput**: 1000+ requests/second
- **Response Time**:
  - Simple queries: <100ms
  - Complex analytics: <5 seconds
  - Report generation: <30 seconds
- **Availability**: 99.9% uptime SLA

### Scalability Metrics

| Component | Current Limit | Scaling Strategy |
|-----------|--------------|------------------|
| Database | 10M records | Horizontal partitioning |
| API | 1K RPS | Load balancing |
| Processing | 10K events/sec | Async processing |
| Storage | 100GB | Auto-scaling storage |

### Performance Optimization Tips

1. **Query Optimization**
   ```sql
   -- Use proper indexes
   CREATE INDEX CONCURRENTLY idx_audit_trails_loan_id
   ON audit_trails USING BTREE ((event_data->>'loan_id'));

   -- Use materialized views for complex analytics
   CREATE MATERIALIZED VIEW compliance_metrics_daily AS
   SELECT date_trunc('day', timestamp) as date,
          COUNT(*) as total_events,
          AVG(CAST(event_data->>'processing_time_ms' AS FLOAT)) as avg_processing_time
   FROM audit_trails
   GROUP BY date_trunc('day', timestamp);
   ```

2. **Application-Level Caching**
   ```python
   import redis

   cache = redis.Redis(host='localhost', port=6379, db=0)

   async def get_cached_compliance_metrics(date_key: str):
       cached = cache.get(f"compliance_metrics:{date_key}")
       if cached:
           return json.loads(cached)

       # Calculate metrics
       metrics = await calculate_compliance_metrics(date_key)

       # Cache for 1 hour
       cache.setex(f"compliance_metrics:{date_key}", 3600, json.dumps(metrics))
       return metrics
   ```

## Error Handling

### Error Types and Handling

#### 1. Database Errors
```python
from src.api.audit_exceptions import AuditDatabaseError

try:
    timeline = await audit_service.get_session_timeline(loan_id)
except AuditDatabaseError as e:
    logger.error(f"Database error: {e}")
    # Implement retry logic
    await retry_with_backoff(audit_service.get_session_timeline, loan_id)
```

#### 2. Validation Errors
```python
from src.api.audit_exceptions import AuditValidationError

try:
    if not loan_id or len(loan_id) < 3:
        raise AuditValidationError("Invalid loan ID format")
except AuditValidationError as e:
    return {"error": "validation_error", "message": str(e)}
```

#### 3. Access Control Errors
```python
from src.api.audit_exceptions import AuditAccessError

try:
    check_audit_access(user, loan_id)
except AuditAccessError as e:
    raise HTTPException(status_code=403, detail=str(e))
```

### Error Recovery Strategies

1. **Connection Pooling with Retry**
   ```python
   async def execute_with_retry(query_func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await query_func()
           except ConnectionError:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(2 ** attempt)  # Exponential backoff
   ```

2. **Circuit Breaker Pattern**
   ```python
   class CircuitBreaker:
       def __init__(self, failure_threshold=5, timeout=60):
           self.failure_threshold = failure_threshold
           self.timeout = timeout
           self.failure_count = 0
           self.last_failure_time = None

       async def call(self, func, *args, **kwargs):
           if self._is_circuit_open():
               raise CircuitBreakerOpenError()

           try:
               result = await func(*args, **kwargs)
               self._on_success()
               return result
           except Exception as e:
               self._on_failure()
               raise
   ```

### Monitoring and Alerting

```python
class AuditMetrics:
    def __init__(self):
        self.operation_counts = defaultdict(int)
        self.operation_times = defaultdict(list)
        self.error_counts = defaultdict(int)

    def record_operation(self, operation: str, duration: float, success: bool):
        self.operation_counts[operation] += 1
        self.operation_times[operation].append(duration)

        if not success:
            self.error_counts[operation] += 1

        # Alert on high error rates
        if self.get_error_rate(operation) > 0.1:
            send_alert(f"High error rate for {operation}")
```

## Security and Access Control

### Authentication and Authorization

#### Role-Based Access Control (RBAC)

```python
# User roles and permissions
ROLE_PERMISSIONS = {
    "admin": ["read", "write", "delete", "manage_users"],
    "auditor": ["read", "search", "export"],
    "compliance_officer": ["read", "search", "generate_reports"],
    "developer": ["read", "debug", "metrics"],
    "analyst": ["read", "search"]
}

def check_permission(user_roles: List[str], required_permission: str) -> bool:
    user_permissions = set()
    for role in user_roles:
        user_permissions.update(ROLE_PERMISSIONS.get(role, []))
    return required_permission in user_permissions
```

#### JWT Token Validation
```python
import jwt
from datetime import datetime, timezone

def validate_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        # Check expiration
        if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
            raise TokenExpiredError()

        return payload

    except jwt.InvalidTokenError:
        raise InvalidTokenError()
```

### Data Privacy and Protection

#### PII Redaction
```python
class PIIRedactor:
    def __init__(self):
        self.pii_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "phone": r"\b\d{3}-\d{3}-\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        }

    def redact_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        redacted_data = data.copy()

        for field, value in data.items():
            if isinstance(value, str):
                for pii_type, pattern in self.pii_patterns.items():
                    value = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", value)
                redacted_data[field] = value

        return redacted_data
```

#### Audit Trail Integrity
```python
import hashlib
import json

class AuditIntegrityValidator:
    def generate_hash(self, audit_record: Dict[str, Any]) -> str:
        # Create deterministic hash of audit record
        normalized_record = json.dumps(audit_record, sort_keys=True)
        return hashlib.sha256(normalized_record.encode()).hexdigest()

    def verify_integrity(self, audit_record: Dict[str, Any], expected_hash: str) -> bool:
        calculated_hash = self.generate_hash(audit_record)
        return calculated_hash == expected_hash
```

### Compliance and Audit Logging

```python
async def log_audit_access(user_id: str, action: str, resource: str, result: str):
    access_log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "result": result,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }

    # Store in separate audit access log
    await store_audit_access_log(access_log)
```

## Deployment Guide

### Prerequisites

- PostgreSQL 14+
- Python 3.11+
- Redis (optional, for caching)
- Docker and Docker Compose (recommended)

### Environment Configuration

Create `.env` file:
```env
# Database Configuration
AUDIT_DATABASE_URL=postgresql://username:password@localhost:5432/audit_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=audit_db
DB_USER=audit_user
DB_PASSWORD=secure_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8003
SECRET_KEY=your-secret-key-here

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

### Docker Deployment

1. **Docker Compose Setup**
   ```yaml
   version: '3.8'
   services:
     audit-db:
       image: postgres:14
       environment:
         POSTGRES_DB: audit_db
         POSTGRES_USER: audit_user
         POSTGRES_PASSWORD: secure_password
       volumes:
         - audit_db_data:/var/lib/postgresql/data
       ports:
         - "5432:5432"

     audit-api:
       build: .
       environment:
         AUDIT_DATABASE_URL: postgresql://audit_user:secure_password@audit-db:5432/audit_db
       ports:
         - "8003:8003"
       depends_on:
         - audit-db
         - redis

     redis:
       image: redis:7
       ports:
         - "6379:6379"

   volumes:
     audit_db_data:
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Kubernetes Deployment

1. **Database StatefulSet**
   ```yaml
   apiVersion: apps/v1
   kind: StatefulSet
   metadata:
     name: audit-postgres
   spec:
     serviceName: audit-postgres
     replicas: 1
     selector:
       matchLabels:
         app: audit-postgres
     template:
       metadata:
         labels:
           app: audit-postgres
       spec:
         containers:
         - name: postgres
           image: postgres:14
           env:
           - name: POSTGRES_DB
             value: audit_db
           - name: POSTGRES_USER
             valueFrom:
               secretKeyRef:
                 name: audit-db-secret
                 key: username
           - name: POSTGRES_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: audit-db-secret
                 key: password
           volumeMounts:
           - name: postgres-storage
             mountPath: /var/lib/postgresql/data
     volumeClaimTemplates:
     - metadata:
         name: postgres-storage
       spec:
         accessModes: ["ReadWriteOnce"]
         resources:
           requests:
             storage: 100Gi
   ```

2. **API Deployment**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: audit-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: audit-api
     template:
       metadata:
         labels:
           app: audit-api
       spec:
         containers:
         - name: audit-api
           image: audit-api:latest
           ports:
           - containerPort: 8003
           env:
           - name: AUDIT_DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: audit-db-secret
                 key: database-url
   ```

### Database Setup

1. **Initialize Database**
   ```python
   from src.core.audit.database import setup_audit_database, DatabaseConfig

   config = DatabaseConfig(
       host="localhost",
       port=5432,
       database="audit_db",
       username="audit_user",
       password="secure_password"
   )

   await setup_audit_database(config)
   ```

2. **Create Indexes**
   ```sql
   -- Essential indexes for performance
   CREATE INDEX CONCURRENTLY idx_audit_trails_loan_id
   ON audit_trails USING BTREE ((event_data->>'loan_id'));

   CREATE INDEX CONCURRENTLY idx_audit_trails_timestamp
   ON audit_trails USING BTREE (timestamp);

   CREATE INDEX CONCURRENTLY idx_audit_trails_session_id
   ON audit_trails USING BTREE (session_id);

   CREATE INDEX CONCURRENTLY idx_decision_points_loan_id
   ON decision_points USING BTREE (loan_id);

   -- Full-text search index
   CREATE INDEX CONCURRENTLY idx_audit_trails_search
   ON audit_trails USING GIN (search_vector);
   ```

### Production Configuration

1. **Performance Tuning**
   ```python
   # Database connection pool
   AUDIT_DB_POOL_MIN_SIZE = 10
   AUDIT_DB_POOL_MAX_SIZE = 50
   AUDIT_DB_POOL_COMMAND_TIMEOUT = 30

   # API server
   API_WORKERS = 4
   API_TIMEOUT = 60

   # Caching
   CACHE_TTL = 3600  # 1 hour
   CACHE_MAX_ENTRIES = 10000
   ```

2. **Monitoring Setup**
   ```python
   # Prometheus metrics
   import prometheus_client

   REQUEST_COUNT = prometheus_client.Counter(
       'audit_api_requests_total',
       'Total requests',
       ['method', 'endpoint']
   )

   REQUEST_DURATION = prometheus_client.Histogram(
       'audit_api_request_duration_seconds',
       'Request duration'
   )
   ```

### Load Testing

```python
import asyncio
import aiohttp
import time

async def load_test():
    """Simple load test for the audit API"""

    async with aiohttp.ClientSession() as session:
        # Test concurrent requests
        tasks = []
        for i in range(100):
            task = session.get(
                f"http://localhost:8003/api/v1/audit/session/TEST_LOAN_{i%10}",
                headers={"Authorization": "Bearer test_token"}
            )
            tasks.append(task)

        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        success_count = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
        total_time = end_time - start_time

        print(f"Load test results:")
        print(f"Total requests: {len(tasks)}")
        print(f"Successful: {success_count}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests/second: {len(tasks)/total_time:.2f}")

# Run load test
asyncio.run(load_test())
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues

**Problem**: `asyncpg.exceptions.ConnectionDoesNotExistError`

**Solution**:
```python
# Check connection pool status
if not audit_service.connection_pool:
    await audit_service.initialize()

# Verify database connectivity
async with audit_service.connection_pool.acquire() as conn:
    result = await conn.fetchval("SELECT 1")
    print(f"Database connection test: {result}")
```

#### 2. Slow Query Performance

**Problem**: Queries taking >5 seconds

**Solutions**:
```sql
-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'audit_trails' AND n_distinct > 100;

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_audit_trails_event_type
ON audit_trails(event_type);

-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM audit_trails
WHERE event_data->>'loan_id' = 'LOAN_001';
```

#### 3. High Memory Usage

**Problem**: API consuming >2GB RAM

**Solutions**:
```python
# Implement pagination
async def get_events_paginated(loan_id: str, page_size: int = 100):
    total_events = await get_total_event_count(loan_id)

    for offset in range(0, total_events, page_size):
        events = await get_events_batch(loan_id, offset, page_size)
        yield events

# Use streaming responses
from fastapi.responses import StreamingResponse

@router.get("/export/{loan_id}")
async def export_audit_data(loan_id: str):
    def generate_csv():
        # Stream CSV data instead of loading all in memory
        yield "timestamp,event_type,severity\n"

        for batch in get_events_paginated(loan_id):
            for event in batch:
                yield f"{event.timestamp},{event.event_type},{event.severity}\n"

    return StreamingResponse(generate_csv(), media_type="text/csv")
```

#### 4. API Rate Limiting Issues

**Problem**: Too many requests causing 429 errors

**Solution**:
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Add rate limiting
@router.get("/session/{loan_id}")
@RateLimiter(times=100, seconds=60)  # 100 requests per minute
async def get_session_timeline(loan_id: str):
    # ... endpoint logic
    pass
```

#### 5. Compliance Report Generation Timeout

**Problem**: Reports taking >30 seconds to generate

**Solutions**:
```python
# Implement async report generation with caching
async def generate_report_async(config: ReportConfiguration):
    # Check cache first
    cache_key = generate_cache_key(config)
    cached_report = await get_cached_report(cache_key)

    if cached_report:
        return cached_report

    # Generate report asynchronously
    report_task = asyncio.create_task(generate_compliance_report(config))

    try:
        report = await asyncio.wait_for(report_task, timeout=25.0)

        # Cache the result
        await cache_report(cache_key, report, ttl=3600)
        return report

    except asyncio.TimeoutError:
        raise ReportGenerationTimeoutError("Report generation exceeded 30 second limit")
```

### Diagnostic Commands

#### Database Health Check
```sql
-- Check database size and performance
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_stat_get_tuples_returned(c.oid) as tuples_read,
    pg_stat_get_tuples_fetched(c.oid) as tuples_fetched
FROM pg_tables pt
JOIN pg_class c ON c.relname = pt.tablename
WHERE schemaname = 'public';

-- Check index usage
SELECT
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public';
```

#### API Performance Check
```python
async def diagnose_api_performance():
    """Diagnose API performance issues"""

    # Check connection pool status
    pool_info = {
        "size": audit_service.connection_pool.get_size(),
        "min_size": audit_service.connection_pool.get_min_size(),
        "max_size": audit_service.connection_pool.get_max_size(),
        "idle_connections": audit_service.connection_pool.get_idle_size()
    }

    # Test query performance
    start_time = time.time()
    test_result = await audit_service.get_session_timeline("TEST_LOAN_001")
    query_time = time.time() - start_time

    print(f"Connection pool: {pool_info}")
    print(f"Test query time: {query_time:.3f}s")

    if query_time > 1.0:
        print("WARNING: Query performance degraded")

    return {
        "pool_info": pool_info,
        "query_performance": query_time,
        "status": "healthy" if query_time < 1.0 else "degraded"
    }
```

### Support and Maintenance

#### Regular Maintenance Tasks

```python
# Daily maintenance script
async def daily_maintenance():
    """Perform daily maintenance tasks"""

    # 1. Update table statistics
    await update_table_statistics()

    # 2. Clean up old sessions
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
    await cleanup_old_sessions(cutoff_date)

    # 3. Refresh materialized views
    await refresh_materialized_views()

    # 4. Check disk space
    disk_usage = await check_disk_usage()
    if disk_usage > 0.8:
        send_alert("High disk usage detected")

    # 5. Generate health report
    health_report = await generate_health_report()
    save_health_report(health_report)

# Weekly maintenance script
async def weekly_maintenance():
    """Perform weekly maintenance tasks"""

    # 1. Reindex tables
    await reindex_audit_tables()

    # 2. Backup audit data
    await backup_audit_data()

    # 3. Performance analysis
    performance_report = await analyze_performance_trends()
    save_performance_report(performance_report)
```

For additional support, please refer to:
- System logs: `/var/log/audit-system/`
- Monitoring dashboard: `http://localhost:3000/audit-dashboard`
- Support email: audit-support@company.com
- Documentation updates: Check the repository for the latest version

---

*Last updated: 2024-01-01*
*Version: 1.0.0*