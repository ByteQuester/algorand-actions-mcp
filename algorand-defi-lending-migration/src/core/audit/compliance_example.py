"""
Compliance System Usage Examples

This script demonstrates how to use the comprehensive compliance reporting
and bias detection system for regulatory compliance.

Usage:
    python compliance_example.py
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import json

from .compliance_service import ComplianceService, RegulatoryFramework
from .bias_detection import BiasDetector, BiasTestConfig
from .report_generator import ComplianceReportGenerator, ReportConfiguration
from .models import create_loan_audit_event, AuditEventType

logger = logging.getLogger(__name__)


async def demonstrate_compliance_system():
    """Demonstrate comprehensive compliance system functionality"""

    print("🔍 Algorand Lending Platform - Compliance System Demo")
    print("=" * 60)

    # Initialize services
    database_url = "postgresql://localhost:5432/lending_platform"
    compliance_service = ComplianceService(database_url)
    await compliance_service.initialize()

    bias_detector = BiasDetector(BiasTestConfig(significance_level=0.05))
    report_generator = ComplianceReportGenerator()

    # Set analysis period
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)

    print(f"📊 Analysis Period: {start_date.date()} to {end_date.date()}")
    print()

    try:
        # 1. Generate Compliance Metrics
        print("1️⃣ GENERATING COMPLIANCE METRICS")
        print("-" * 40)

        compliance_metrics = await compliance_service.generate_compliance_metrics(
            start_date=start_date,
            end_date=end_date,
            frameworks=[RegulatoryFramework.ECOA, RegulatoryFramework.FAIR_LENDING_ACT]
        )

        print(f"✅ Total Loans Analyzed: {compliance_metrics.total_loans:,}")
        print(f"✅ Approval Rate: {compliance_metrics.approval_rate:.1%}")
        print(f"✅ Average Interest Rate: {compliance_metrics.average_interest_rate:.2%}")
        print(f"✅ Compliance Score: {compliance_metrics.compliance_score:.2f}/1.0")
        print(f"⚠️ Bias Flags: {len(compliance_metrics.bias_flags)}")
        print(f"🚨 Violations: {len(compliance_metrics.regulatory_violations)}")

        if compliance_metrics.regulatory_violations:
            print("\n🚨 REGULATORY VIOLATIONS DETECTED:")
            for violation in compliance_metrics.regulatory_violations:
                print(f"   • {violation}")

        print()

        # 2. Detailed Bias Analysis
        print("2️⃣ DETAILED BIAS ANALYSIS")
        print("-" * 40)

        # Create sample loan data for demonstration
        sample_loan_data = create_sample_loan_data()

        bias_results = await compliance_service.detect_bias(
            loan_data=sample_loan_data,
            bias_types=None  # Analyze all bias types
        )

        print(f"🔍 Analyzed {len(sample_loan_data)} loan records")
        print(f"📊 Bias Tests Performed: {len(bias_results)}")

        for bias_result in bias_results:
            status = "🚨 DETECTED" if bias_result.detected else "✅ CLEAR"
            print(f"{status} {bias_result.bias_type.value.replace('_', ' ').title()}")

            if bias_result.detected:
                print(f"   Severity: {bias_result.severity_score:.2f}")
                print(f"   P-Value: {bias_result.p_value:.4f}")
                print(f"   Affected Groups: {', '.join(bias_result.affected_groups)}")
                print(f"   Recommendations: {len(bias_result.recommendations)} actions")

        print()

        # 3. Interest Rate Justification Analysis
        print("3️⃣ INTEREST RATE JUSTIFICATION")
        print("-" * 40)

        # Analyze a sample loan's interest rate
        if sample_loan_data:
            sample_loan = sample_loan_data[0]
            if sample_loan.get('interest_rate'):

                rate_justification = await compliance_service.justify_interest_rate(
                    loan_id=sample_loan['loan_id'],
                    borrower_profile=sample_loan,
                    assigned_rate=sample_loan['interest_rate']
                )

                print(f"🏦 Loan ID: {rate_justification.loan_id}")
                print(f"📈 Assigned Rate: {rate_justification.assigned_rate:.2%}")
                print(f"📊 Market Benchmark: {rate_justification.market_benchmark:.2%}")
                print(f"⚠️ Risk Premium: {rate_justification.risk_premium:.2%}")
                print(f"✅ Justified: {'Yes' if rate_justification.justified else 'No'}")
                print(f"📋 Explanation: {rate_justification.explanation}")

        print()

        # 4. Decision Consistency Analysis
        print("4️⃣ DECISION CONSISTENCY ANALYSIS")
        print("-" * 40)

        from .models import DecisionType
        consistency_analysis = await compliance_service.validate_decision_consistency(
            start_date=start_date,
            end_date=end_date,
            decision_type=DecisionType.CREDIT_APPROVAL
        )

        print(f"🎯 Decision Type: {consistency_analysis['decision_type']}")
        print(f"📊 Total Decisions: {consistency_analysis['total_decisions']}")
        print(f"👥 Demographic Groups: {consistency_analysis['demographic_groups']}")
        print(f"📈 Consistency Score: {consistency_analysis['overall_consistency_score']:.2f}")

        if consistency_analysis['recommendations']:
            print("💡 Recommendations:")
            for rec in consistency_analysis['recommendations'][:3]:
                print(f"   • {rec}")

        print()

        # 5. Generate Compliance Reports
        print("5️⃣ COMPLIANCE REPORT GENERATION")
        print("-" * 40)

        # PDF Report
        pdf_config = ReportConfiguration(
            template_name="standard",
            output_format="PDF",
            include_charts=True,
            include_recommendations=True,
            regulatory_framework="ECOA"
        )

        pdf_path, pdf_metadata = await report_generator.generate_compliance_report(
            compliance_metrics=compliance_metrics,
            bias_results=compliance_metrics.bias_flags,
            config=pdf_config
        )

        print(f"📄 PDF Report: {pdf_path}")
        print(f"   Size: {pdf_metadata.file_size_bytes:,} bytes")
        print(f"   Records: {pdf_metadata.total_records:,}")

        # CSV Report
        csv_config = ReportConfiguration(
            template_name="standard",
            output_format="CSV",
            regulatory_framework="FAIR_LENDING_ACT"
        )

        csv_path, csv_metadata = await report_generator.generate_compliance_report(
            compliance_metrics=compliance_metrics,
            bias_results=compliance_metrics.bias_flags,
            config=csv_config
        )

        print(f"📊 CSV Report: {csv_path}")
        print(f"   Size: {csv_metadata.file_size_bytes:,} bytes")

        print()

        # 6. Regulatory Filing Generation
        print("6️⃣ REGULATORY FILING GENERATION")
        print("-" * 40)

        hmda_filing, hmda_metadata = await report_generator.generate_regulatory_filing(
            compliance_metrics=compliance_metrics,
            filing_type="HMDA",
            jurisdiction="US"
        )

        print(f"🏛️ HMDA Filing: {hmda_filing}")
        print(f"   Framework: {hmda_metadata.regulatory_framework}")
        print(f"   Classification: {hmda_metadata.confidentiality_level}")

        print()

        # 7. Individual Loan Validation
        print("7️⃣ INDIVIDUAL LOAN VALIDATION")
        print("-" * 40)

        if sample_loan_data:
            # Use bias detector for individual loan analysis
            similar_loans = sample_loan_data[1:6]  # Mock similar loans

            individual_bias = bias_detector.detect_individual_bias(
                loan_record=sample_loan_data[0],
                similar_loans=similar_loans,
                protected_attrs=["race", "gender", "age"]
            )

            print(f"🔍 Individual Loan Analysis:")
            print(f"   Loan ID: {sample_loan_data[0]['loan_id']}")
            print(f"   Bias Detected: {'Yes' if individual_bias['bias_detected'] else 'No'}")
            print(f"   Confidence: {individual_bias['confidence']:.1%}")
            print(f"   Similar Cases Analyzed: {individual_bias['similar_cases_analyzed']}")
            print(f"   Explanation: {individual_bias['explanation']}")

        print()

        # 8. Real-time Monitoring Metrics
        print("8️⃣ REAL-TIME MONITORING")
        print("-" * 40)

        # Simulate real-time metrics
        monitoring_metrics = {
            "active_loans": 1245,
            "approval_rate_24h": 0.73,
            "avg_processing_time_ms": 2150,
            "bias_alerts": 2,
            "compliance_score": compliance_metrics.compliance_score,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        print("📊 Real-time Compliance Dashboard:")
        for metric, value in monitoring_metrics.items():
            if isinstance(value, float) and 0 <= value <= 1:
                print(f"   {metric.replace('_', ' ').title()}: {value:.1%}")
            elif isinstance(value, (int, float)):
                print(f"   {metric.replace('_', ' ').title()}: {value:,.0f}")
            else:
                print(f"   {metric.replace('_', ' ').title()}: {value}")

        print()
        print("✅ COMPLIANCE SYSTEM DEMONSTRATION COMPLETE")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Error in compliance demonstration: {e}")
        raise

    finally:
        await compliance_service.close()


def create_sample_loan_data() -> List[Dict[str, Any]]:
    """Create sample loan data for demonstration purposes"""

    sample_data = []

    # Create diverse sample loans for bias testing
    loans = [
        {
            "loan_id": "LOAN_001",
            "borrower_address": "ADDR_001",
            "approved": True,
            "loan_amount": 50000,
            "interest_rate": 0.08,
            "credit_score": 750,
            "debt_to_income": 0.3,
            "risk_score": 25.0,
            "employment_status": "employed",
            "annual_income": 80000,
            "race": "white",
            "gender": "male",
            "age": 35
        },
        {
            "loan_id": "LOAN_002",
            "borrower_address": "ADDR_002",
            "approved": True,
            "loan_amount": 45000,
            "interest_rate": 0.09,
            "credit_score": 720,
            "debt_to_income": 0.35,
            "risk_score": 30.0,
            "employment_status": "employed",
            "annual_income": 75000,
            "race": "black",
            "gender": "female",
            "age": 32
        },
        {
            "loan_id": "LOAN_003",
            "borrower_address": "ADDR_003",
            "approved": False,
            "loan_amount": 60000,
            "interest_rate": None,
            "credit_score": 650,
            "debt_to_income": 0.45,
            "risk_score": 65.0,
            "employment_status": "employed",
            "annual_income": 70000,
            "race": "hispanic",
            "gender": "male",
            "age": 28
        },
        {
            "loan_id": "LOAN_004",
            "borrower_address": "ADDR_004",
            "approved": True,
            "loan_amount": 40000,
            "interest_rate": 0.07,
            "credit_score": 780,
            "debt_to_income": 0.25,
            "risk_score": 20.0,
            "employment_status": "employed",
            "annual_income": 90000,
            "race": "asian",
            "gender": "female",
            "age": 40
        },
        {
            "loan_id": "LOAN_005",
            "borrower_address": "ADDR_005",
            "approved": True,
            "loan_amount": 55000,
            "interest_rate": 0.085,
            "credit_score": 730,
            "debt_to_income": 0.32,
            "risk_score": 28.0,
            "employment_status": "self_employed",
            "annual_income": 85000,
            "race": "white",
            "gender": "male",
            "age": 45
        }
    ]

    return loans


async def demonstrate_api_integration():
    """Demonstrate how the compliance system integrates with the API"""

    print("🔗 API INTEGRATION EXAMPLES")
    print("=" * 60)

    print("Available API Endpoints:")
    endpoints = [
        "GET /api/v1/audit/compliance/metrics",
        "GET /api/v1/audit/compliance/bias-analysis",
        "POST /api/v1/audit/export/regulatory",
        "POST /api/v1/audit/compliance/validate/{loan_id}"
    ]

    for endpoint in endpoints:
        print(f"   📡 {endpoint}")

    print("\nExample API Usage:")
    print("   curl -X GET 'https://api.lending-platform.com/api/v1/audit/compliance/metrics?start_date=2024-01-01&end_date=2024-01-31'")
    print("   curl -X POST 'https://api.lending-platform.com/api/v1/audit/export/regulatory' -d '{\"report_type\":\"compliance\", \"output_format\":\"PDF\"}'")

    print()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run demonstration
    asyncio.run(demonstrate_compliance_system())
    asyncio.run(demonstrate_api_integration())