# Audit Trail API Implementation

## Overview

The Audit Trail API provides comprehensive audit data retrieval and compliance reporting capabilities for the Algorand Lending Platform. This implementation offers high-performance access to audit trails, decision points, and compliance events with sub-second response times.

## Architecture

### Core Components

1. **AuditService** (`src/core/audit/audit_service.py`)
   - Business logic layer for audit data operations
   - High-performance database queries with connection pooling
   - Real-time session data processing
   - Tool usage analytics and decision reconstruction

2. **AuditRouter** (`src/api/audit_router.py`)
   - REST API endpoints with FastAPI
   - Role-based access control
   - Request validation and response formatting
   - Comprehensive error handling

3. **AuditExceptions** (`src/api/audit_exceptions.py`)
   - Custom exception classes for audit operations
   - Error sanitization and security
   - Metrics collection and monitoring
   - Standardized error responses

## API Endpoints

### Core Audit Endpoints

#### 1. Session Timeline - `GET /api/v1/audit/session/{loan_id}`

Retrieves complete session timeline for a loan with all events grouped by session.

**Parameters:**
- `loan_id` (path): Loan ID to retrieve timeline for

**Response:**
```json
{
  "loan_id": "uuid",
  "total_events": 45,
  "total_sessions": 3,
  "timeline_start": "2024-01-01T10:00:00Z",
  "timeline_end": "2024-01-01T10:30:00Z",
  "sessions": [
    {
      "session_id": "session_123",
      "user_id": "user_456",
      "session_start": "2024-01-01T10:00:00Z",
      "session_end": "2024-01-01T10:15:00Z",
      "event_count": 15,
      "error_count": 0
    }
  ],
  "events": [
    {
      "id": "event_uuid",
      "event_type": "loan_request_created",
      "timestamp": "2024-01-01T10:00:00Z",
      "event_data": {...},
      "service_name": "lending-workflow",
      "session_info": {...}
    }
  ]
}
```

#### 2. Decision Breakdown - `GET /api/v1/audit/decisions/{loan_id}`

Retrieves decision breakdown with reasoning chains for regulatory compliance.

**Response:**
```json
{
  "loan_id": "uuid",
  "total_decisions": 5,
  "decision_types": ["risk_assessment", "credit_approval"],
  "average_risk_score": 65.5,
  "average_confidence": 0.85,
  "decision_chain": [
    {
      "type": "risk_assessment",
      "timestamp": "2024-01-01T10:05:00Z",
      "outcome": "medium_risk",
      "confidence": 0.85
    }
  ],
  "decisions": [
    {
      "id": "decision_uuid",
      "decision_type": "risk_assessment",
      "decision_maker": "RiskAssessmentAgent",
      "decision_rationale": "Analysis of borrower credit history...",
      "decision_outcome": "medium_risk",
      "input_data": {...},
      "risk_factors": ["limited_credit_history"],
      "compliance_flags": [],
      "confidence_score": 0.85,
      "risk_score": 65.5
    }
  ]
}
```

#### 3. Tool Usage Analysis - `GET /api/v1/audit/tools/{loan_id}`

Retrieves tool usage and impact analysis for loan processing.

**Response:**
```json
{
  "loan_id": "uuid",
  "total_tool_executions": 12,
  "unique_tools_used": 4,
  "total_errors": 0,
  "total_warnings": 1,
  "success_rate": 1.0,
  "average_processing_time_ms": 250.5,
  "tool_performance": [
    {
      "tool_name": "algorand_balance_check",
      "execution_count": 3,
      "avg_processing_time_ms": 150.0,
      "success_rate": 1.0,
      "error_count": 0
    }
  ],
  "tool_executions": [...]
}
```

#### 4. Raw Events - `GET /api/v1/audit/events/{session_id}`

Retrieves raw audit events for a specific session with pagination.

**Parameters:**
- `session_id` (path): Session ID to retrieve events for
- `limit` (query): Maximum events to return (1-1000, default 100)
- `offset` (query): Events to skip (default 0)

**Response:**
```json
{
  "session_id": "session_123",
  "total_events": 250,
  "returned_events": 100,
  "limit": 100,
  "offset": 0,
  "has_more": true,
  "events": [...]
}
```

#### 5. Visual Timeline - `GET /api/v1/audit/timeline/{loan_id}`

Retrieves timeline data optimized for visualization and dashboards.

**Response:**
```json
{
  "loan_id": "uuid",
  "timeline_buckets": 15,
  "event_types": ["loan_request_created", "risk_assessment", "approval"],
  "severity_distribution": {
    "info": 40,
    "warning": 2,
    "error": 0
  },
  "milestones": [
    {
      "timestamp": "2024-01-01T10:00:00Z",
      "event_type": "loan_request_created",
      "status": "requested",
      "amount_micro_algos": 100000000
    }
  ],
  "timeline_data": [...]
}
```

### Utility Endpoints

#### Search Events - `GET /api/v1/audit/search`

Search audit events using full-text search with optional filters.

**Parameters:**
- `query` (query): Search query string
- `loan_id` (query, optional): Filter by loan ID
- `start_date` (query, optional): Filter by start date
- `end_date` (query, optional): Filter by end date
- `limit` (query): Maximum results (1-1000, default 100)

#### Health Check - `GET /api/v1/audit/health`

Check audit service health and status.

#### Metrics - `GET /api/v1/audit/metrics`

Retrieve API performance and error metrics (admin/developer only).

## Authentication & Authorization

### Role-Based Access Control

The audit API implements comprehensive role-based access control:

- **Admin**: Full access to all audit data and metrics
- **Auditor**: Access to audit trails and compliance data
- **Compliance Officer**: Access to compliance events and decision data
- **Developer**: Access to raw events and metrics for debugging
- **Borrower/Lender**: Access only to their own loan data

### Token-Based Authentication

All endpoints require valid JWT tokens in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Demo Tokens

For testing, you can generate demo tokens for different roles:

```python
from src.api.auth import create_demo_token

# Generate tokens for different roles
admin_token = create_demo_token("admin")
auditor_token = create_demo_token("auditor")
developer_token = create_demo_token("developer")
```

## Error Handling

### Custom Exception Classes

- `AuditAPIError`: Base exception for audit operations
- `AuditAccessError`: Access permission issues (403)
- `AuditNotFoundError`: Data not found (404)
- `AuditServiceError`: Internal service errors (500)
- `AuditDatabaseError`: Database connectivity issues (503)
- `AuditValidationError`: Request validation failures (400)

### Error Response Format

```json
{
  "success": false,
  "error_code": "AUDIT_ACCESS_DENIED",
  "message": "Access denied to audit data",
  "timestamp": "2024-01-01T10:00:00Z",
  "request_id": "req_123",
  "details": {...},
  "support_reference": "AUD-20240101-1000-1234"
}
```

### Error Monitoring

All errors are logged with structured logging and metrics collection:
- Error counts by type
- Response time tracking
- Operation success rates
- Performance bottleneck identification

## Performance Considerations

### Database Optimization

- **Connection Pooling**: 5-20 concurrent connections
- **Query Optimization**: Indexed JSONB queries for sub-second response
- **Partition Management**: Monthly partitions for scalability
- **Read Replicas**: Support for read-only replicas

### Caching Strategy

- **Query Result Caching**: Redis cache for frequently accessed data
- **Session Data**: In-memory caching for active sessions
- **Metrics Aggregation**: Periodic metric calculations

### Rate Limiting

- **Per-user Limits**: 100 requests/minute for regular users
- **Admin Limits**: 1000 requests/minute for admin users
- **Burst Allowance**: 10-request burst capacity

## Security Features

### Data Sanitization

- **Sensitive Data Removal**: Automatic redaction of passwords, tokens, keys
- **SQL Injection Prevention**: Parameterized queries only
- **Input Validation**: Comprehensive request validation

### Access Logging

- **Audit Access Tracking**: All audit data access is logged
- **Compliance Reporting**: GDPR/CCPA compliance support
- **Forensic Capabilities**: Tamper-evident audit trails

### Encryption

- **Data at Rest**: Database-level encryption
- **Data in Transit**: TLS 1.3 for all communications
- **Token Security**: JWT with strong secret keys

## Configuration

### Environment Variables

```bash
# Database Configuration
AUDIT_DATABASE_URL=postgresql://user:pass@localhost:5432/audit_db

# Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
CORS_ORIGINS=http://localhost:8000,http://localhost:8081

# Service Configuration
PORT=8003
HOST=0.0.0.0

# External Services
ADK_WEB_BASE_URL=http://localhost:8000
```

### Database Setup

1. Install PostgreSQL 14+
2. Create audit database
3. Run migration script: `src/core/audit/database/migrations.py`
4. Verify schema: `src/core/audit/database/schema.sql`

## Usage Examples

### Basic Timeline Retrieval

```python
import httpx

headers = {"Authorization": f"Bearer {token}"}
response = httpx.get(
    "http://localhost:8003/api/v1/audit/session/loan_123",
    headers=headers
)
timeline = response.json()
```

### Decision Analysis

```python
response = httpx.get(
    "http://localhost:8003/api/v1/audit/decisions/loan_123",
    headers=headers
)
decisions = response.json()

for decision in decisions["decisions"]:
    print(f"Decision: {decision['decision_type']}")
    print(f"Outcome: {decision['decision_outcome']}")
    print(f"Confidence: {decision['confidence_score']}")
```

### Search Functionality

```python
params = {
    "query": "risk assessment",
    "loan_id": "loan_123",
    "limit": 50
}
response = httpx.get(
    "http://localhost:8003/api/v1/audit/search",
    headers=headers,
    params=params
)
search_results = response.json()
```

## Monitoring & Metrics

### Health Monitoring

- **Service Health**: Database connectivity, response times
- **Error Rates**: Exception tracking and alerting
- **Performance Metrics**: Query times, cache hit rates

### Business Metrics

- **Audit Coverage**: Percentage of loans with complete audit trails
- **Compliance Status**: Regulatory requirement fulfillment
- **Data Quality**: Completeness and accuracy metrics

### Alerting

- **High Error Rates**: > 5% error rate triggers alert
- **Slow Responses**: > 2 second response time alert
- **Database Issues**: Connection pool exhaustion alert

## Development & Testing

### Running Locally

```bash
cd /home/mpo/algorand-showcase/apps/lending-platform
python -m uvicorn src.api.server:app --reload --port 8003
```

### API Documentation

- **OpenAPI Docs**: http://localhost:8003/api/v1/docs
- **ReDoc**: http://localhost:8003/api/v1/redoc

### Testing

```bash
# Unit tests
pytest src/tests/audit/

# Integration tests
pytest src/tests/integration/audit/

# Load testing
locust -f src/tests/load/audit_load_test.py
```

## Compliance & Regulatory

### Supported Regulations

- **GDPR**: Data protection and privacy rights
- **CCPA**: California consumer privacy rights
- **SOX**: Financial reporting compliance
- **PCI DSS**: Payment card industry standards

### Audit Trail Integrity

- **Immutable Records**: Write-once audit entries
- **Checksum Verification**: SHA-256 tamper detection
- **Retention Policies**: Configurable data retention
- **Export Capabilities**: Compliance reporting formats

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check AUDIT_DATABASE_URL configuration
   - Verify PostgreSQL service is running
   - Check connection pool limits

2. **Authentication Failures**
   - Verify JWT_SECRET_KEY matches token issuer
   - Check token expiration times
   - Validate user roles in token payload

3. **Performance Issues**
   - Monitor database query performance
   - Check connection pool utilization
   - Review index usage on large tables

### Support

For issues or questions:
- Check logs: `/var/log/audit-api/`
- Monitor metrics: `/api/v1/audit/metrics`
- Health check: `/api/v1/audit/health`

---

## Summary

This Audit Trail API implementation provides:

✅ **Complete session timeline reconstruction**
✅ **Decision reasoning chains for compliance**
✅ **Tool usage analytics and performance metrics**
✅ **Raw event access for debugging**
✅ **Visual timeline data for dashboards**
✅ **Sub-second response times**
✅ **Comprehensive error handling**
✅ **Role-based access control**
✅ **Production-ready monitoring**
✅ **Regulatory compliance support**

The implementation is ready for production deployment and provides the foundation for advanced audit analytics and compliance reporting.