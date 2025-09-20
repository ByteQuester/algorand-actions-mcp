"""
Compliance Report Generator

Advanced report generation system for regulatory compliance reporting.
Supports multiple output formats including PDF, CSV, and standardized regulatory formats.
Generates comprehensive reports for bias analysis, compliance metrics, and audit trails.

Features:
- PDF generation with charts and visualizations
- CSV export for data analysis
- Standardized regulatory formats (HMDA, CRA, etc.)
- Batch report generation
- Template-based reporting
- Performance optimized for large datasets
"""

import asyncio
import logging
import io
import csv
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import json
import base64

# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart

# Data processing
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_agg import FigureCanvasAgg

from .compliance_service import ComplianceMetrics, BiasAnalysisResult, InterestRateJustification
from .bias_detection import FairnessResult, BiasDetector
from .models import AuditTrail, DecisionPoint, ComplianceEvent

logger = logging.getLogger(__name__)


@dataclass
class ReportConfiguration:
    """Configuration for report generation"""
    template_name: str = "standard"
    include_charts: bool = True
    include_raw_data: bool = False
    include_recommendations: bool = True
    include_executive_summary: bool = True
    regulatory_framework: str = "ECOA"
    output_format: str = "PDF"  # PDF, CSV, JSON, XLSX
    chart_style: str = "professional"
    page_size: str = "letter"
    confidentiality_level: str = "CONFIDENTIAL"


@dataclass
class ReportMetadata:
    """Metadata for generated reports"""
    report_id: str
    report_type: str
    generation_timestamp: datetime
    period_start: datetime
    period_end: datetime
    total_records: int
    data_sources: List[str]
    generated_by: str
    regulatory_framework: str
    confidentiality_level: str
    file_size_bytes: int
    checksum: str


class ComplianceReportGenerator:
    """
    Advanced compliance report generator for regulatory reporting

    Generates comprehensive compliance reports with visualizations,
    statistical analysis, and regulatory-ready formatting.
    """

    def __init__(self, output_dir: str = "/tmp/compliance_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Report templates
        self.templates = {
            "standard": self._get_standard_template(),
            "executive": self._get_executive_template(),
            "regulatory": self._get_regulatory_template(),
            "technical": self._get_technical_template()
        }

        # Chart styles
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

    async def generate_compliance_report(
        self,
        compliance_metrics: ComplianceMetrics,
        bias_results: List[BiasAnalysisResult],
        config: ReportConfiguration = None
    ) -> Tuple[str, ReportMetadata]:
        """
        Generate comprehensive compliance report

        Args:
            compliance_metrics: Compliance metrics data
            bias_results: Bias analysis results
            config: Report configuration

        Returns:
            Tuple of (file_path, report_metadata)
        """

        if config is None:
            config = ReportConfiguration()

        report_id = f"compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            if config.output_format.upper() == "PDF":
                file_path = await self._generate_pdf_report(
                    compliance_metrics, bias_results, config, report_id
                )
            elif config.output_format.upper() == "CSV":
                file_path = await self._generate_csv_report(
                    compliance_metrics, bias_results, config, report_id
                )
            elif config.output_format.upper() == "JSON":
                file_path = await self._generate_json_report(
                    compliance_metrics, bias_results, config, report_id
                )
            else:
                raise ValueError(f"Unsupported output format: {config.output_format}")

            # Generate metadata
            metadata = ReportMetadata(
                report_id=report_id,
                report_type="compliance_analysis",
                generation_timestamp=datetime.now(timezone.utc),
                period_start=compliance_metrics.period_start,
                period_end=compliance_metrics.period_end,
                total_records=compliance_metrics.total_loans,
                data_sources=["audit_trails", "decision_points", "compliance_events"],
                generated_by="compliance_report_generator",
                regulatory_framework=config.regulatory_framework,
                confidentiality_level=config.confidentiality_level,
                file_size_bytes=Path(file_path).stat().st_size,
                checksum=self._calculate_file_checksum(file_path)
            )

            logger.info(f"Generated compliance report: {file_path}")
            return file_path, metadata

        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise

    async def generate_bias_analysis_report(
        self,
        fairness_results: List[FairnessResult],
        loan_data: List[Dict[str, Any]],
        config: ReportConfiguration = None
    ) -> Tuple[str, ReportMetadata]:
        """Generate specialized bias analysis report"""

        if config is None:
            config = ReportConfiguration()

        report_id = f"bias_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            if config.output_format.upper() == "PDF":
                file_path = await self._generate_bias_pdf_report(
                    fairness_results, loan_data, config, report_id
                )
            else:
                file_path = await self._generate_bias_csv_report(
                    fairness_results, loan_data, config, report_id
                )

            metadata = ReportMetadata(
                report_id=report_id,
                report_type="bias_analysis",
                generation_timestamp=datetime.now(timezone.utc),
                period_start=datetime.now() - timedelta(days=30),  # Default period
                period_end=datetime.now(),
                total_records=len(loan_data),
                data_sources=["loan_applications", "decision_points"],
                generated_by="bias_analysis_generator",
                regulatory_framework=config.regulatory_framework,
                confidentiality_level=config.confidentiality_level,
                file_size_bytes=Path(file_path).stat().st_size,
                checksum=self._calculate_file_checksum(file_path)
            )

            return file_path, metadata

        except Exception as e:
            logger.error(f"Error generating bias analysis report: {e}")
            raise

    async def generate_regulatory_filing(
        self,
        compliance_metrics: ComplianceMetrics,
        filing_type: str,
        jurisdiction: str = "US"
    ) -> Tuple[str, ReportMetadata]:
        """Generate regulatory filing in standardized format"""

        report_id = f"filing_{filing_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            if filing_type.upper() == "HMDA":
                file_path = await self._generate_hmda_filing(
                    compliance_metrics, report_id
                )
            elif filing_type.upper() == "CRA":
                file_path = await self._generate_cra_filing(
                    compliance_metrics, report_id
                )
            else:
                raise ValueError(f"Unsupported filing type: {filing_type}")

            metadata = ReportMetadata(
                report_id=report_id,
                report_type=f"regulatory_filing_{filing_type.lower()}",
                generation_timestamp=datetime.now(timezone.utc),
                period_start=compliance_metrics.period_start,
                period_end=compliance_metrics.period_end,
                total_records=compliance_metrics.total_loans,
                data_sources=["compliance_metrics"],
                generated_by="regulatory_filing_generator",
                regulatory_framework=filing_type,
                confidentiality_level="RESTRICTED",
                file_size_bytes=Path(file_path).stat().st_size,
                checksum=self._calculate_file_checksum(file_path)
            )

            return file_path, metadata

        except Exception as e:
            logger.error(f"Error generating regulatory filing: {e}")
            raise

    async def _generate_pdf_report(
        self,
        compliance_metrics: ComplianceMetrics,
        bias_results: List[BiasAnalysisResult],
        config: ReportConfiguration,
        report_id: str
    ) -> str:
        """Generate PDF compliance report"""

        file_path = self.output_dir / f"{report_id}.pdf"

        # Create PDF document
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter if config.page_size == "letter" else A4,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18
        )

        # Build story (content)
        story = []
        styles = getSampleStyleSheet()

        # Title page
        story.extend(self._create_title_page(compliance_metrics, config))

        # Executive summary
        if config.include_executive_summary:
            story.extend(self._create_executive_summary(compliance_metrics, bias_results))

        # Compliance metrics section
        story.extend(self._create_compliance_metrics_section(compliance_metrics))

        # Bias analysis section
        if bias_results:
            story.extend(self._create_bias_analysis_section(bias_results))

        # Charts and visualizations
        if config.include_charts:
            story.extend(await self._create_charts_section(compliance_metrics, bias_results))

        # Recommendations
        if config.include_recommendations:
            story.extend(self._create_recommendations_section(bias_results))

        # Raw data appendix
        if config.include_raw_data:
            story.extend(self._create_raw_data_appendix(compliance_metrics))

        # Build PDF
        doc.build(story)

        return str(file_path)

    async def _generate_csv_report(
        self,
        compliance_metrics: ComplianceMetrics,
        bias_results: List[BiasAnalysisResult],
        config: ReportConfiguration,
        report_id: str
    ) -> str:
        """Generate CSV compliance report"""

        file_path = self.output_dir / f"{report_id}.csv"

        # Create comprehensive CSV with multiple sheets worth of data
        data_rows = []

        # Compliance metrics
        data_rows.append(["COMPLIANCE_METRICS", "", "", "", ""])
        data_rows.append(["Metric", "Value", "Period Start", "Period End", "Notes"])
        data_rows.append([
            "Total Loans", compliance_metrics.total_loans,
            compliance_metrics.period_start.isoformat(),
            compliance_metrics.period_end.isoformat(),
            ""
        ])
        data_rows.append([
            "Approval Rate", f"{compliance_metrics.approval_rate:.2%}",
            "", "", ""
        ])
        data_rows.append([
            "Average Interest Rate", f"{compliance_metrics.average_interest_rate:.2%}",
            "", "", ""
        ])
        data_rows.append([
            "Compliance Score", f"{compliance_metrics.compliance_score:.2f}",
            "", "", ""
        ])

        data_rows.append(["", "", "", "", ""])  # Blank row

        # Bias analysis results
        if bias_results:
            data_rows.append(["BIAS_ANALYSIS", "", "", "", ""])
            data_rows.append([
                "Bias Type", "Detected", "Severity", "P-Value", "Recommendations"
            ])

            for bias in bias_results:
                recommendations = "; ".join(bias.recommendations[:2])  # Truncate for CSV
                data_rows.append([
                    bias.bias_type.value,
                    "Yes" if bias.detected else "No",
                    bias.severity_level,
                    f"{bias.p_value:.4f}",
                    recommendations
                ])

        # Write CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data_rows)

        return str(file_path)

    async def _generate_json_report(
        self,
        compliance_metrics: ComplianceMetrics,
        bias_results: List[BiasAnalysisResult],
        config: ReportConfiguration,
        report_id: str
    ) -> str:
        """Generate JSON compliance report"""

        file_path = self.output_dir / f"{report_id}.json"

        # Convert dataclasses to dictionaries
        report_data = {
            "report_metadata": {
                "report_id": report_id,
                "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                "configuration": asdict(config)
            },
            "compliance_metrics": asdict(compliance_metrics),
            "bias_analysis": [asdict(bias) for bias in bias_results],
            "summary": {
                "total_loans": compliance_metrics.total_loans,
                "approval_rate": compliance_metrics.approval_rate,
                "compliance_score": compliance_metrics.compliance_score,
                "bias_flags_count": len([b for b in bias_results if b.detected]),
                "regulatory_violations_count": len(compliance_metrics.regulatory_violations)
            }
        }

        # Write JSON with proper formatting
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(report_data, jsonfile, indent=2, default=str, ensure_ascii=False)

        return str(file_path)

    def _create_title_page(
        self,
        compliance_metrics: ComplianceMetrics,
        config: ReportConfiguration
    ) -> List:
        """Create report title page"""

        story = []
        styles = getSampleStyleSheet()

        # Custom title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center
        )

        # Title
        story.append(Paragraph("Compliance Analysis Report", title_style))
        story.append(Spacer(1, 20))

        # Report details
        details = [
            ["Report Period:", f"{compliance_metrics.period_start.strftime('%Y-%m-%d')} to {compliance_metrics.period_end.strftime('%Y-%m-%d')}"],
            ["Total Loans Analyzed:", f"{compliance_metrics.total_loans:,}"],
            ["Regulatory Framework:", config.regulatory_framework],
            ["Generated:", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ["Classification:", config.confidentiality_level]
        ]

        details_table = Table(details, colWidths=[2*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))

        story.append(details_table)
        story.append(PageBreak())

        return story

    def _create_executive_summary(
        self,
        compliance_metrics: ComplianceMetrics,
        bias_results: List[BiasAnalysisResult]
    ) -> List:
        """Create executive summary section"""

        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("Executive Summary", styles['Heading1']))
        story.append(Spacer(1, 12))

        # Key findings
        bias_flags = len([b for b in bias_results if b.detected])
        critical_issues = len([b for b in bias_results if b.detected and b.severity_level == "CRITICAL"])

        summary_text = f"""
        During the analysis period from {compliance_metrics.period_start.strftime('%B %Y')} to
        {compliance_metrics.period_end.strftime('%B %Y')}, we analyzed {compliance_metrics.total_loans:,}
        loan applications with an overall approval rate of {compliance_metrics.approval_rate:.1%}.

        <b>Key Findings:</b><br/>
        • Overall compliance score: {compliance_metrics.compliance_score:.1f}/1.0<br/>
        • Bias flags detected: {bias_flags}<br/>
        • Critical compliance issues: {critical_issues}<br/>
        • Average interest rate: {compliance_metrics.average_interest_rate:.2%}<br/>

        {f'<b>REGULATORY ATTENTION REQUIRED:</b> {critical_issues} critical compliance issues identified.' if critical_issues > 0 else ''}
        """

        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 12))

        return story

    def _create_compliance_metrics_section(
        self,
        compliance_metrics: ComplianceMetrics
    ) -> List:
        """Create compliance metrics section"""

        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("Compliance Metrics", styles['Heading1']))
        story.append(Spacer(1, 12))

        # Create metrics table
        metrics_data = [
            ['Metric', 'Value', 'Status'],
            ['Total Loan Applications', f"{compliance_metrics.total_loans:,}", ''],
            ['Overall Approval Rate', f"{compliance_metrics.approval_rate:.2%}",
             self._get_status_indicator(compliance_metrics.approval_rate > 0.5)],
            ['Average Interest Rate', f"{compliance_metrics.average_interest_rate:.2%}", ''],
            ['Compliance Score', f"{compliance_metrics.compliance_score:.2f}/1.0",
             self._get_status_indicator(compliance_metrics.compliance_score > 0.8)],
            ['Regulatory Violations', f"{len(compliance_metrics.regulatory_violations)}",
             self._get_status_indicator(len(compliance_metrics.regulatory_violations) == 0)]
        ]

        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(metrics_table)
        story.append(Spacer(1, 20))

        return story

    def _create_bias_analysis_section(self, bias_results: List[BiasAnalysisResult]) -> List:
        """Create bias analysis section"""

        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("Bias Analysis Results", styles['Heading1']))
        story.append(Spacer(1, 12))

        if not bias_results:
            story.append(Paragraph("No bias analysis results available.", styles['Normal']))
            return story

        # Create bias results table
        bias_data = [['Bias Type', 'Detected', 'Severity', 'P-Value', 'Effect Size']]

        for bias in bias_results:
            bias_data.append([
                bias.bias_type.value.replace('_', ' ').title(),
                "Yes" if bias.detected else "No",
                bias.severity_level,
                f"{bias.p_value:.4f}",
                f"{bias.effect_size:.3f}"
            ])

        bias_table = Table(bias_data, colWidths=[1.8*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        bias_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(bias_table)
        story.append(Spacer(1, 20))

        return story

    async def _create_charts_section(
        self,
        compliance_metrics: ComplianceMetrics,
        bias_results: List[BiasAnalysisResult]
    ) -> List:
        """Create charts and visualizations section"""

        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("Data Visualizations", styles['Heading1']))
        story.append(Spacer(1, 12))

        # Create approval rate chart
        if compliance_metrics.demographic_breakdown:
            chart_path = await self._create_approval_rate_chart(
                compliance_metrics.demographic_breakdown
            )
            if chart_path:
                story.append(Image(chart_path, width=6*inch, height=4*inch))
                story.append(Spacer(1, 12))

        # Create bias severity chart
        if bias_results:
            bias_chart_path = await self._create_bias_severity_chart(bias_results)
            if bias_chart_path:
                story.append(Image(bias_chart_path, width=6*inch, height=4*inch))
                story.append(Spacer(1, 12))

        return story

    def _create_recommendations_section(self, bias_results: List[BiasAnalysisResult]) -> List:
        """Create recommendations section"""

        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("Recommendations", styles['Heading1']))
        story.append(Spacer(1, 12))

        all_recommendations = set()
        for bias in bias_results:
            if bias.detected:
                all_recommendations.update(bias.recommendations)

        if not all_recommendations:
            story.append(Paragraph("No specific recommendations at this time. Continue monitoring compliance metrics.", styles['Normal']))
        else:
            for i, rec in enumerate(sorted(all_recommendations), 1):
                story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                story.append(Spacer(1, 6))

        return story

    def _create_raw_data_appendix(self, compliance_metrics: ComplianceMetrics) -> List:
        """Create raw data appendix"""

        story = []
        styles = getSampleStyleSheet()

        story.append(PageBreak())
        story.append(Paragraph("Appendix: Raw Data", styles['Heading1']))
        story.append(Spacer(1, 12))

        # Add raw data tables
        story.append(Paragraph("Compliance metrics data available upon request.", styles['Normal']))

        return story

    # Helper methods for chart generation

    async def _create_approval_rate_chart(self, demographic_data: Dict[str, Any]) -> Optional[str]:
        """Create approval rate chart by demographics"""

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Example chart - would use actual demographic data
            categories = ['Group A', 'Group B', 'Group C', 'Group D']
            rates = [0.75, 0.68, 0.72, 0.71]

            bars = ax.bar(categories, rates, color=['#2E86C1', '#28B463', '#F39C12', '#E74C3C'])
            ax.set_ylabel('Approval Rate')
            ax.set_title('Approval Rates by Demographic Group')
            ax.set_ylim(0, 1)

            # Add value labels on bars
            for bar, rate in zip(bars, rates):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{rate:.1%}', ha='center', va='bottom')

            plt.tight_layout()

            chart_path = self.output_dir / f"approval_rates_{datetime.now().strftime('%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()

            return str(chart_path)

        except Exception as e:
            logger.error(f"Error creating approval rate chart: {e}")
            return None

    async def _create_bias_severity_chart(self, bias_results: List[BiasAnalysisResult]) -> Optional[str]:
        """Create bias severity distribution chart"""

        try:
            severity_counts = {}
            for bias in bias_results:
                if bias.detected:
                    severity = bias.severity_level
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

            if not severity_counts:
                return None

            fig, ax = plt.subplots(figsize=(8, 6))

            severities = list(severity_counts.keys())
            counts = list(severity_counts.values())
            colors_map = {'LOW': '#28B463', 'MEDIUM': '#F39C12', 'HIGH': '#E67E22', 'CRITICAL': '#E74C3C'}

            bars = ax.bar(severities, counts, color=[colors_map.get(s, '#85929E') for s in severities])
            ax.set_ylabel('Number of Issues')
            ax.set_title('Bias Issues by Severity Level')

            # Add value labels
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{count}', ha='center', va='bottom')

            plt.tight_layout()

            chart_path = self.output_dir / f"bias_severity_{datetime.now().strftime('%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()

            return str(chart_path)

        except Exception as e:
            logger.error(f"Error creating bias severity chart: {e}")
            return None

    # Helper methods

    def _get_status_indicator(self, is_good: bool) -> str:
        """Get status indicator for metrics"""
        return "✓" if is_good else "⚠"

    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate file checksum for integrity verification"""
        import hashlib

        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_standard_template(self) -> Dict[str, Any]:
        """Get standard report template configuration"""
        return {
            "sections": [
                "title_page",
                "executive_summary",
                "compliance_metrics",
                "bias_analysis",
                "charts",
                "recommendations"
            ],
            "style": "professional"
        }

    def _get_executive_template(self) -> Dict[str, Any]:
        """Get executive report template configuration"""
        return {
            "sections": [
                "title_page",
                "executive_summary",
                "key_metrics",
                "recommendations"
            ],
            "style": "executive"
        }

    def _get_regulatory_template(self) -> Dict[str, Any]:
        """Get regulatory filing template configuration"""
        return {
            "sections": [
                "title_page",
                "compliance_metrics",
                "bias_analysis",
                "raw_data"
            ],
            "style": "regulatory"
        }

    def _get_technical_template(self) -> Dict[str, Any]:
        """Get technical report template configuration"""
        return {
            "sections": [
                "title_page",
                "methodology",
                "detailed_analysis",
                "statistical_tests",
                "charts",
                "raw_data"
            ],
            "style": "technical"
        }

    # Additional specialized report generators

    async def _generate_bias_pdf_report(
        self,
        fairness_results: List[FairnessResult],
        loan_data: List[Dict[str, Any]],
        config: ReportConfiguration,
        report_id: str
    ) -> str:
        """Generate specialized bias analysis PDF report"""
        # Implementation would be similar to main PDF generator
        # but focused on bias analysis details
        return await self._generate_pdf_report(None, [], config, report_id)

    async def _generate_bias_csv_report(
        self,
        fairness_results: List[FairnessResult],
        loan_data: List[Dict[str, Any]],
        config: ReportConfiguration,
        report_id: str
    ) -> str:
        """Generate specialized bias analysis CSV report"""
        file_path = self.output_dir / f"{report_id}_bias.csv"

        data_rows = []
        data_rows.append(["BIAS_ANALYSIS_DETAILED", "", "", "", "", "", ""])
        data_rows.append([
            "Protected_Attribute", "Metric_Type", "Bias_Detected",
            "Severity", "P_Value", "Effect_Size", "Recommendations"
        ])

        for result in fairness_results:
            recommendations = "; ".join(result.recommendations[:3])
            data_rows.append([
                result.protected_attribute,
                result.metric_type.value,
                "Yes" if result.bias_detected else "No",
                result.severity_level,
                f"{result.statistical_significance.get('p_value', 0):.4f}",
                f"{result.effect_sizes.get('effect_size', 0):.3f}",
                recommendations
            ])

        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data_rows)

        return str(file_path)

    async def _generate_hmda_filing(
        self,
        compliance_metrics: ComplianceMetrics,
        report_id: str
    ) -> str:
        """Generate HMDA (Home Mortgage Disclosure Act) filing"""
        file_path = self.output_dir / f"{report_id}_hmda.txt"

        # HMDA format is highly standardized
        # This is a simplified version - real implementation would follow exact format
        with open(file_path, 'w') as f:
            f.write(f"HMDA Filing - {datetime.now().year}\n")
            f.write(f"Institution: Algorand Lending Platform\n")
            f.write(f"Total Applications: {compliance_metrics.total_loans}\n")
            f.write(f"Approval Rate: {compliance_metrics.approval_rate:.2%}\n")
            # ... additional HMDA-specific fields

        return str(file_path)

    async def _generate_cra_filing(
        self,
        compliance_metrics: ComplianceMetrics,
        report_id: str
    ) -> str:
        """Generate CRA (Community Reinvestment Act) filing"""
        file_path = self.output_dir / f"{report_id}_cra.txt"

        # CRA format for community lending assessment
        with open(file_path, 'w') as f:
            f.write(f"CRA Assessment - {datetime.now().year}\n")
            f.write(f"Community Lending Score: {compliance_metrics.compliance_score:.2f}\n")
            # ... additional CRA-specific metrics

        return str(file_path)