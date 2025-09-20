# Audit Trail & Compliance System

High-performance audit trail system designed for regulatory compliance and operational monitoring in the Algorand lending platform.

## Features

- **High Performance**: JSONB storage with optimized indexes for sub-second queries on millions of records
- **Scalable Architecture**: Automatic table partitioning by month for efficient data management
- **Regulatory Compliance**: Built-in support for KYC, AML, GDPR, CCPA, and other regulations
- **Immutable Audit Trails**: Tamper-evident design with checksums and frozen data models
- **Full-Text Search**: Advanced search capabilities across all event data
- **Privacy Controls**: User-configurable retention policies and data sharing preferences
- **Comprehensive Tracking**: Loan decisions, blockchain operations, agent activities, and system events

## Architecture

### Core Components

1. **Data Models** (`models.py`)
   - Pydantic models for validation and serialization
   - Immutable design for audit integrity
   - Flexible JSONB event data storage

2. **Database Schema** (`database/schema.sql`)
   - Partitioned tables for scalability
   - Optimized indexes for fast queries
   - Automatic partition management

3. **Migration System** (`database/migrations.py`)
   - Schema deployment and updates
   - Partition lifecycle management
   - Database maintenance automation

### Database Tables

- **`audit_trails`**: Main audit event storage (partitioned by timestamp)
- **`decision_points`**: Key lending decisions for regulatory compliance
- **`compliance_events`**: Regulatory event tracking
- **`audit_sessions`**: Session grouping and management
- **`user_audit_profiles`**: Privacy preferences and retention policies

## Quick Start

### 1. Setup Database

```python
from src.core.audit.database import setup_audit_database, DatabaseConfig

config = DatabaseConfig(
    host="localhost",
    database="lending_audit",
    username="audit_user",
    password="secure_password"
)

success = await setup_audit_database(config)
```

### 2. Create Audit Events

```python
from src.core.audit import create_loan_audit_event, AuditEventType

# Create a loan approval audit event
audit_event = create_loan_audit_event(
    event_type=AuditEventType.LOAN_APPROVED,
    loan_id="loan_123",
    borrower_address="ALGORAND_ADDRESS_HERE",
    service_name="lending-agent",
    amount_micro_algos=5000000,  # 5 ALGO
    interest_rate=8.5
)

print(audit_event.to_json())
```

### 3. Track Decisions

```python
from src.core.audit import create_decision_point, DecisionType

decision = create_decision_point(
    decision_type=DecisionType.CREDIT_APPROVAL,
    loan_id="loan_123",
    borrower_address="ALGORAND_ADDRESS_HERE",
    decision_maker="risk-assessment-agent",
    decision_rationale="Credit score above threshold, sufficient collateral",
    decision_outcome="approved",
    input_data={
        "credit_score": 750,
        "collateral_ratio": 1.5,
        "debt_to_income": 0.3
    },
    audit_event=audit_event
)
```

### 4. Compliance Tracking

```python
from src.core.audit import create_compliance_event

compliance = create_compliance_event(
    regulation_type="KYC",
    compliance_rule="Customer Identity Verification",
    compliance_status="compliant",
    audit_event=audit_event,
    jurisdiction="US"
)
```

## Database Management

### Run Migrations

```bash
cd /apps/lending-platform/src/core/audit/database
python migrations.py setup
```

### Maintenance Operations

```bash
# Run routine maintenance
python migrations.py maintenance

# Get database statistics
python migrations.py stats

# Backup audit data
python migrations.py backup \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --output /backup/audit_2024.json
```

### Programmatic Maintenance

```python
from src.core.audit.database import run_maintenance

# Run scheduled maintenance
results = await run_maintenance(config)
print(f"Created {results['partitions_created']} partitions")
print(f"Cleaned {results['partitions_cleaned']} old partitions")
```

## Performance Optimization

### Partition Management

The system automatically partitions the `audit_trails` table by month:

- **Automatic Creation**: Future partitions created automatically
- **Retention Cleanup**: Old partitions removed based on retention policies
- **Query Optimization**: Partition pruning for faster queries

### Index Strategy

- **JSONB GIN Indexes**: Fast queries on nested event data
- **Composite Indexes**: Optimized for common query patterns
- **Partial Indexes**: Memory-efficient indexes for specific conditions

### Query Performance

Common query patterns optimized for sub-second response:

```sql
-- Find all events for a specific loan
SELECT * FROM audit_trails
WHERE event_data->>'loan_id' = 'loan_123'
ORDER BY timestamp DESC;

-- Search for compliance violations
SELECT * FROM compliance_events
WHERE compliance_status = 'non_compliant'
AND regulation_type = 'AML'
AND event_timestamp >= NOW() - INTERVAL '30 days';

-- Full-text search across audit events
SELECT * FROM audit_trails
WHERE search_vector @@ to_tsquery('english', 'transaction & failed');
```

## Regulatory Compliance

### Data Retention

- **User-Configurable**: Individual retention preferences
- **Regulatory Defaults**: 7 years for financial records
- **Automatic Cleanup**: Expired data removal
- **Compliance Override**: Critical records preserved beyond user preferences

### Privacy Controls

- **GDPR Compliance**: Right to be forgotten support
- **CCPA Compliance**: Data sharing preferences
- **Consent Tracking**: Privacy policy version management
- **Data Minimization**: Configurable audit levels

### Audit Trail Integrity

- **Immutable Records**: Frozen Pydantic models prevent modification
- **Tamper Detection**: SHA-256 checksums for critical events
- **Chain of Custody**: Parent-child event relationships
- **Digital Signatures**: Optional cryptographic signing

## Integration Examples

### Agent Integration

```python
from src.core.audit import AuditTrail, AuditEventType, AuditEventData

class LendingAgent:
    async def process_loan_request(self, loan_request):
        # Create audit event for loan processing
        audit_data = AuditEventData(
            loan_id=loan_request.id,
            borrower_address=loan_request.borrower_address,
            user_id=self.current_user_id,
            session_id=self.current_session_id,
            processing_time_ms=processing_time
        )

        audit_event = AuditTrail(
            event_type=AuditEventType.LOAN_REQUEST_CREATED,
            event_data=audit_data,
            service_name="lending-agent",
            service_version="1.0.0"
        )

        # Store audit event
        await self.audit_store.save(audit_event)
```

### Blockchain Integration

```python
from src.core.audit import AuditEventType

async def create_blockchain_transaction(self, transaction_data):
    # Audit transaction creation
    audit_event = create_loan_audit_event(
        event_type=AuditEventType.TRANSACTION_CREATED,
        loan_id=transaction_data.loan_id,
        borrower_address=transaction_data.borrower,
        service_name="blockchain-service",
        transaction_id=transaction_data.id,
        amount_micro_algos=transaction_data.amount
    )

    await self.audit_store.save(audit_event)
```

## Environment Configuration

Set up environment variables for database connection:

```bash
export AUDIT_DB_HOST=localhost
export AUDIT_DB_PORT=5432
export AUDIT_DB_NAME=lending_audit
export AUDIT_DB_USER=audit_user
export AUDIT_DB_PASSWORD=secure_password
```

## Monitoring and Alerting

### Key Metrics

- **Event Volume**: Track audit events per second/minute/hour
- **Error Rates**: Monitor failed audits and compliance violations
- **Query Performance**: Track database query response times
- **Storage Usage**: Monitor partition sizes and growth rates

### Health Checks

```python
from src.core.audit.database import AuditDatabaseManager

async def health_check():
    async with AuditDatabaseManager(config) as manager:
        status = await manager.get_health_status()

        # Check critical metrics
        if status['integrity_status']['foreign_key_constraints']:
            return "healthy"
        else:
            return "unhealthy"
```

## Security Considerations

- **Database Security**: Use dedicated audit database with restricted access
- **Network Security**: Encrypt connections with SSL/TLS
- **Access Control**: Role-based permissions for audit data
- **Data Encryption**: Encrypt sensitive data in event_data JSONB
- **Backup Security**: Encrypt audit data backups

## Testing

Run comprehensive tests for the audit system:

```bash
cd /apps/lending-platform
python -m pytest tests/core/audit/ -v
```

## Support

For questions or issues with the audit system:

1. Check the migration logs for database issues
2. Review database statistics for performance problems
3. Validate data integrity with built-in checks
4. Monitor compliance event status for regulatory issues