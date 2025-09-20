# Compliance Reporting System

A comprehensive regulatory compliance reporting and bias detection system designed for fair lending requirements and regulatory oversight.

## Overview

This system provides automated compliance monitoring, bias detection, and regulatory reporting capabilities for the Algorand lending platform. It implements advanced statistical algorithms to detect potential bias in lending decisions and generates regulatory-ready reports.

## Features

### 🔍 Bias Detection
- **Statistical Parity Analysis** - Ensures equal approval rates across protected classes
- **Equalized Odds Assessment** - Validates consistent true positive/false positive rates
- **Interest Rate Disparity Analysis** - Detects pricing bias across demographic groups
- **Individual Fairness Testing** - Compares similar applications for consistent treatment
- **Protected Class Monitoring** - Comprehensive coverage of ECOA protected attributes

### 📊 Compliance Metrics
- **Real-time Compliance Scoring** - Continuous monitoring with 0-1.0 scoring
- **Approval Rate Tracking** - Demographic breakdown and trend analysis
- **Interest Rate Justification** - Market benchmark comparison and risk premium analysis
- **Decision Consistency Validation** - Cross-demographic consistency checking
- **Regulatory Violation Detection** - Automated flagging of potential violations

### 📈 Advanced Analytics
- **Statistical Significance Testing** - Chi-square, ANOVA, and other robust tests
- **Effect Size Calculation** - Cohen's h, eta-squared, and other metrics
- **Confidence Interval Analysis** - Precise uncertainty quantification
- **Sample Size Validation** - Ensures statistical power for meaningful analysis
- **Multi-framework Support** - ECOA, Fair Lending Act, CRA, and others

### 📄 Report Generation
- **PDF Reports** - Professional regulatory filings with charts and visualizations
- **CSV Export** - Data analysis-ready formats for statistical software
- **JSON Output** - API-friendly structured data for integration
- **HMDA/CRA Filings** - Standardized regulatory filing formats
- **Executive Summaries** - High-level compliance overview for leadership

## Architecture

```
src/core/audit/
├── compliance_service.py       # Core compliance analysis engine
├── bias_detection.py          # Advanced bias detection algorithms
├── report_generator.py        # Multi-format report generation
├── models.py                  # Data models and schemas
├── audit_service.py           # Audit trail integration
└── compliance_example.py      # Usage examples and demos
```

### API Integration

```
src/api/
└── compliance_router.py       # RESTful compliance API endpoints
```

## Quick Start

### 1. Initialize Services

```python
from src.core.audit import ComplianceService, BiasDetector, ComplianceReportGenerator

# Initialize compliance service
compliance_service = ComplianceService("postgresql://localhost/lending")
await compliance_service.initialize()

# Initialize bias detector
bias_detector = BiasDetector()

# Initialize report generator
report_generator = ComplianceReportGenerator()
```

### 2. Generate Compliance Metrics

```python
from datetime import datetime, timedelta

# Set analysis period
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Generate comprehensive compliance metrics
metrics = await compliance_service.generate_compliance_metrics(
    start_date=start_date,
    end_date=end_date,
    frameworks=[RegulatoryFramework.ECOA, RegulatoryFramework.FAIR_LENDING_ACT]
)

print(f"Compliance Score: {metrics.compliance_score:.2f}")
print(f"Bias Flags: {len(metrics.bias_flags)}")
print(f"Violations: {len(metrics.regulatory_violations)}")
```

### 3. Perform Bias Analysis

```python
# Detect bias across all fairness metrics
bias_results = await compliance_service.detect_bias(
    loan_data=loan_applications,
    bias_types=[BiasType.APPROVAL_RATE_BIAS, BiasType.INTEREST_RATE_BIAS]
)

for result in bias_results:
    if result.detected:
        print(f"⚠️ {result.bias_type.value}: Severity {result.severity_score:.2f}")
        print(f"   Affected groups: {result.affected_groups}")
        print(f"   P-value: {result.p_value:.4f}")
```

### 4. Generate Reports

```python
# Generate PDF compliance report
config = ReportConfiguration(
    template_name="regulatory",
    output_format="PDF",
    include_charts=True,
    regulatory_framework="ECOA"
)

file_path, metadata = await report_generator.generate_compliance_report(
    compliance_metrics=metrics,
    bias_results=bias_results,
    config=config
)

print(f"Report generated: {file_path}")
```

### 5. Validate Individual Loans

```python
# Justify interest rate for specific loan
justification = await compliance_service.justify_interest_rate(
    loan_id="LOAN_123",
    borrower_profile=borrower_data,
    assigned_rate=0.085
)

print(f"Rate justified: {justification.justified}")
print(f"Market benchmark: {justification.market_benchmark:.2%}")
print(f"Risk premium: {justification.risk_premium:.2%}")
```

## API Endpoints

### Compliance Metrics
- `GET /api/v1/audit/compliance/metrics` - Real-time compliance metrics
- `GET /api/v1/audit/compliance/bias-analysis` - Comprehensive bias analysis

### Report Generation
- `POST /api/v1/audit/export/regulatory` - Generate compliance reports
- `GET /api/v1/audit/compliance/reports/{id}/download` - Download generated reports

### Loan Validation
- `POST /api/v1/audit/compliance/validate/{loan_id}` - Validate specific loan compliance

### Example API Usage

```bash
# Get compliance metrics
curl -X GET "https://api.lending.com/api/v1/audit/compliance/metrics?start_date=2024-01-01&end_date=2024-01-31"

# Generate PDF report
curl -X POST "https://api.lending.com/api/v1/audit/export/regulatory" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "compliance",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "output_format": "PDF",
    "template_name": "regulatory"
  }'

# Validate loan compliance
curl -X POST "https://api.lending.com/api/v1/audit/compliance/validate/LOAN_123" \
  -H "Content-Type: application/json" \
  -d '{
    "validation_types": ["compliance", "bias", "interest_rate"],
    "include_similar_loans": true
  }'
```

## Bias Detection Algorithms

### Statistical Parity
Tests whether the probability of a positive outcome is equal across all demographic groups:
```
P(Y=1|A=a) = P(Y=1|A=b) for all groups a, b
```

### Equalized Odds
Ensures equal true positive and false positive rates across groups:
```
TPR(A=a) = TPR(A=b) and FPR(A=a) = FPR(A=b)
```

### Individual Fairness
Validates that similar individuals receive similar treatment using distance metrics and similarity thresholds.

### Disparate Impact
Implements the "80% rule" and other regulatory thresholds to detect disparate impact.

## Regulatory Frameworks

### ECOA (Equal Credit Opportunity Act)
- Protected classes: Race, color, religion, national origin, sex, marital status, age
- Disparate impact testing
- Adverse action requirements

### Fair Lending Act
- Interest rate justification
- Pricing consistency analysis
- Market benchmark comparison

### CRA (Community Reinvestment Act)
- Geographic distribution analysis
- Community lending assessment
- Service area compliance

## Performance Specifications

- **Analysis Speed**: <30 seconds for comprehensive compliance reports
- **Bias Detection**: Statistical significance testing with p-values <0.05
- **Sample Size**: Minimum 30 records per group for statistical validity
- **Report Generation**: Multi-format export in under 2 minutes
- **Database Performance**: Sub-second query response for real-time metrics

## Security & Privacy

- **Data Classification**: Supports CONFIDENTIAL, RESTRICTED, and other levels
- **Audit Trails**: Immutable logs of all compliance activities
- **Access Controls**: Role-based permissions for compliance data
- **Data Retention**: Configurable retention periods for regulatory requirements
- **Encryption**: All sensitive data encrypted at rest and in transit

## Regulatory Compliance

### Fair Lending Requirements
✅ Disparate impact testing
✅ Statistical significance validation
✅ Protected class coverage
✅ Interest rate justification
✅ Decision consistency tracking

### Audit Trail Requirements
✅ Immutable event logging
✅ Full decision reasoning capture
✅ Temporal data integrity
✅ Privacy controls
✅ Regulatory retention periods

### Reporting Requirements
✅ HMDA filing format support
✅ Executive summary generation
✅ Statistical analysis documentation
✅ Recommendation tracking
✅ Violation identification

## Integration Examples

### With Existing Audit System
```python
# Compliance analysis integrates seamlessly with audit trails
audit_events = await audit_service.get_session_events(session_id)
compliance_events = [e for e in audit_events if e.event_type in compliance_types]
```

### With Lending Engine
```python
# Real-time compliance checking during loan processing
compliance_check = await compliance_service.validate_loan_realtime(loan_request)
if not compliance_check.compliant:
    await flag_for_manual_review(loan_request, compliance_check.issues)
```

### With Reporting Pipeline
```python
# Automated daily compliance monitoring
async def daily_compliance_check():
    yesterday = datetime.now() - timedelta(days=1)
    metrics = await compliance_service.generate_compliance_metrics(
        start_date=yesterday,
        end_date=datetime.now()
    )

    if metrics.compliance_score < 0.8:
        await send_compliance_alert(metrics)
```

## Testing & Validation

The compliance system includes comprehensive test coverage:

- Unit tests for all bias detection algorithms
- Integration tests with audit system
- Performance benchmarks for large datasets
- Regulatory scenario testing
- API endpoint validation

Run tests with:
```bash
python -m pytest src/core/audit/tests/test_compliance.py -v
python -m pytest src/api/tests/test_compliance_router.py -v
```

## Support & Documentation

For additional support:
- Review `compliance_example.py` for detailed usage patterns
- Check API documentation at `/api/v1/docs`
- Consult regulatory framework documentation
- Review audit trail integration examples

## Contributing

When contributing to the compliance system:
1. Ensure all bias detection algorithms are statistically sound
2. Add appropriate test coverage for new features
3. Document regulatory justification for changes
4. Validate performance requirements are met
5. Include example usage in documentation