"""
Risk Assessment Data Models

Clean data models for risk assessments and trend analysis.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY HIGH"


@dataclass
class RiskAssessment:
    """Risk assessment data model"""
    assessment_id: str
    loan_id: str
    credit_score: Optional[int] = None
    debt_to_income: Optional[float] = None
    payment_history_score: Optional[int] = None
    collateral_value: Optional[float] = None
    final_risk_score: Optional[int] = None
    risk_level: Optional[RiskLevel] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'assessment_id': self.assessment_id,
            'loan_id': self.loan_id,
            'credit_score': self.credit_score,
            'debt_to_income': self.debt_to_income,
            'payment_history_score': self.payment_history_score,
            'collateral_value': self.collateral_value,
            'final_risk_score': self.final_risk_score,
            'risk_level': self.risk_level.value if isinstance(self.risk_level, RiskLevel) else self.risk_level,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskAssessment':
        """Create from dictionary (database row)"""
        # Handle timestamp parsing
        timestamp = None
        if data.get('timestamp'):
            if isinstance(data['timestamp'], str):
                try:
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                except ValueError:
                    # Handle SQLite timestamp format
                    timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
            elif isinstance(data['timestamp'], datetime):
                timestamp = data['timestamp']

        # Handle risk level enum
        risk_level = None
        if data.get('risk_level'):
            try:
                risk_level = RiskLevel(data['risk_level'])
            except ValueError:
                risk_level = None

        return cls(
            assessment_id=data['assessment_id'],
            loan_id=data['loan_id'],
            credit_score=int(data['credit_score']) if data.get('credit_score') is not None else None,
            debt_to_income=float(data['debt_to_income']) if data.get('debt_to_income') is not None else None,
            payment_history_score=int(data['payment_history_score']) if data.get('payment_history_score') is not None else None,
            collateral_value=float(data['collateral_value']) if data.get('collateral_value') is not None else None,
            final_risk_score=int(data['final_risk_score']) if data.get('final_risk_score') is not None else None,
            risk_level=risk_level,
            timestamp=timestamp
        )

    def is_high_risk(self) -> bool:
        """Check if assessment indicates high risk"""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]

    def is_low_risk(self) -> bool:
        """Check if assessment indicates low risk"""
        return self.risk_level == RiskLevel.LOW

    def get_risk_category(self) -> str:
        """Get risk category as string"""
        if self.final_risk_score is None:
            return "Unknown"

        if self.final_risk_score >= 80:
            return "Excellent"
        elif self.final_risk_score >= 70:
            return "Good"
        elif self.final_risk_score >= 60:
            return "Fair"
        elif self.final_risk_score >= 50:
            return "Poor"
        else:
            return "Very Poor"

    def calculate_risk_premium(self, base_rate: float = 5.0) -> float:
        """Calculate risk premium based on assessment"""
        if self.final_risk_score is None:
            return base_rate * 2.0  # High premium for unknown risk

        # Risk premium calculation based on score
        if self.final_risk_score >= 80:
            return base_rate * 0.5  # Low premium for low risk
        elif self.final_risk_score >= 70:
            return base_rate * 0.8
        elif self.final_risk_score >= 60:
            return base_rate * 1.2
        elif self.final_risk_score >= 50:
            return base_rate * 1.5
        else:
            return base_rate * 2.0  # High premium for high risk


@dataclass
class RiskTrendData:
    """Risk assessment trend analysis data"""
    period_days: int
    total_assessments: int
    average_risk_score: Optional[float]
    risk_distribution: Dict[RiskLevel, int]
    credit_score_trend: List[float]
    debt_to_income_trend: List[float]
    risk_score_trend: List[float]
    high_risk_percentage: float
    risk_improvement: Optional[float]  # Positive = improving, negative = deteriorating

    @classmethod
    def from_assessments(cls, assessments: List[RiskAssessment], days: int = 30) -> 'RiskTrendData':
        """Calculate trend data from list of risk assessments"""
        if not assessments:
            return cls(
                period_days=days,
                total_assessments=0,
                average_risk_score=None,
                risk_distribution={level: 0 for level in RiskLevel},
                credit_score_trend=[],
                debt_to_income_trend=[],
                risk_score_trend=[],
                high_risk_percentage=0.0,
                risk_improvement=None
            )

        # Filter assessments within the specified period
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_assessments = [
            a for a in assessments
            if a.timestamp and a.timestamp >= cutoff_date
        ]

        if not recent_assessments:
            return cls(
                period_days=days,
                total_assessments=0,
                average_risk_score=None,
                risk_distribution={level: 0 for level in RiskLevel},
                credit_score_trend=[],
                debt_to_income_trend=[],
                risk_score_trend=[],
                high_risk_percentage=0.0,
                risk_improvement=None
            )

        # Calculate average risk score
        risk_scores = [a.final_risk_score for a in recent_assessments if a.final_risk_score is not None]
        average_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else None

        # Calculate risk distribution
        risk_distribution = {level: 0 for level in RiskLevel}
        for assessment in recent_assessments:
            if assessment.risk_level:
                risk_distribution[assessment.risk_level] += 1

        # Calculate trends (simplified - could be enhanced with proper time series analysis)
        sorted_assessments = sorted(recent_assessments, key=lambda a: a.timestamp or datetime.min)

        credit_score_trend = [
            a.credit_score for a in sorted_assessments
            if a.credit_score is not None
        ]

        debt_to_income_trend = [
            a.debt_to_income for a in sorted_assessments
            if a.debt_to_income is not None
        ]

        risk_score_trend = [
            a.final_risk_score for a in sorted_assessments
            if a.final_risk_score is not None
        ]

        # Calculate high risk percentage
        high_risk_count = sum(
            1 for a in recent_assessments
            if a.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
        )
        high_risk_percentage = (high_risk_count / len(recent_assessments)) * 100

        # Calculate risk improvement (simple trend)
        risk_improvement = None
        if len(risk_score_trend) >= 2:
            early_scores = risk_score_trend[:len(risk_score_trend)//2]
            late_scores = risk_score_trend[len(risk_score_trend)//2:]
            if early_scores and late_scores:
                early_avg = sum(early_scores) / len(early_scores)
                late_avg = sum(late_scores) / len(late_scores)
                risk_improvement = late_avg - early_avg

        return cls(
            period_days=days,
            total_assessments=len(recent_assessments),
            average_risk_score=average_risk_score,
            risk_distribution=risk_distribution,
            credit_score_trend=credit_score_trend,
            debt_to_income_trend=debt_to_income_trend,
            risk_score_trend=risk_score_trend,
            high_risk_percentage=high_risk_percentage,
            risk_improvement=risk_improvement
        )


@dataclass
class RiskBenchmark:
    """Risk assessment benchmarks and thresholds"""
    excellent_threshold: int = 80
    good_threshold: int = 70
    fair_threshold: int = 60
    poor_threshold: int = 50
    min_credit_score: int = 300
    max_credit_score: int = 850
    max_debt_to_income: float = 0.6
    min_payment_history: int = 0
    max_payment_history: int = 100

    def validate_assessment(self, assessment: RiskAssessment) -> Dict[str, bool]:
        """Validate risk assessment against benchmarks"""
        validation = {}

        # Credit score validation
        if assessment.credit_score is not None:
            validation['credit_score_valid'] = (
                self.min_credit_score <= assessment.credit_score <= self.max_credit_score
            )
        else:
            validation['credit_score_valid'] = True

        # Debt-to-income validation
        if assessment.debt_to_income is not None:
            validation['debt_to_income_valid'] = (
                0 <= assessment.debt_to_income <= self.max_debt_to_income
            )
        else:
            validation['debt_to_income_valid'] = True

        # Payment history validation
        if assessment.payment_history_score is not None:
            validation['payment_history_valid'] = (
                self.min_payment_history <= assessment.payment_history_score <= self.max_payment_history
            )
        else:
            validation['payment_history_valid'] = True

        # Final risk score validation
        if assessment.final_risk_score is not None:
            validation['risk_score_valid'] = (
                0 <= assessment.final_risk_score <= 100
            )
        else:
            validation['risk_score_valid'] = True

        # Collateral validation
        if assessment.collateral_value is not None:
            validation['collateral_valid'] = assessment.collateral_value >= 0
        else:
            validation['collateral_valid'] = True

        # Overall validation
        validation['all_valid'] = all(validation.values())

        return validation