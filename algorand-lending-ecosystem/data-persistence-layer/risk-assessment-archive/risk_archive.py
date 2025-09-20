"""
Risk Assessment Archive

Repository for risk assessment storage, retrieval, and trend analysis
with comprehensive risk management capabilities.
"""

import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .risk_models import RiskAssessment, RiskLevel, RiskTrendData, RiskBenchmark
try:
    from .connection_factory import ConnectionFactory, DatabaseConfig, DatabaseConnectionError
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent / "database-schema-manager"))
    from connection_factory import ConnectionFactory, DatabaseConfig, DatabaseConnectionError


class RiskArchiveError(Exception):
    """Raised when risk archive operations fail"""
    pass


class RiskAssessmentArchive:
    """Stores and retrieves risk assessment data"""

    def __init__(self, db_path: Path, config: Optional[DatabaseConfig] = None):
        self.db_path = Path(db_path)
        self.connection_factory = ConnectionFactory(db_path, config)
        self.benchmark = RiskBenchmark()

    def store_assessment(self, loan_id: str, assessment_data: Dict[str, Any]) -> str:
        """Store risk assessment, return assessment_id"""
        assessment_id = str(uuid.uuid4())

        # Create RiskAssessment object
        assessment = RiskAssessment(
            assessment_id=assessment_id,
            loan_id=loan_id,
            credit_score=assessment_data.get('credit_score'),
            debt_to_income=assessment_data.get('debt_to_income'),
            payment_history_score=assessment_data.get('payment_history_score'),
            collateral_value=assessment_data.get('collateral_value'),
            final_risk_score=assessment_data.get('final_risk_score'),
            risk_level=RiskLevel(assessment_data['risk_level']) if assessment_data.get('risk_level') else None,
            timestamp=datetime.now()
        )

        # Validate assessment before storing
        validation = self.benchmark.validate_assessment(assessment)
        if not validation['all_valid']:
            raise RiskArchiveError(f"Invalid assessment data: {validation}")

        try:
            self.connection_factory.execute_query("""
                INSERT INTO risk_assessments (
                    assessment_id, loan_id, credit_score, debt_to_income,
                    payment_history_score, collateral_value, final_risk_score, risk_level, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                assessment.assessment_id,
                assessment.loan_id,
                assessment.credit_score,
                assessment.debt_to_income,
                assessment.payment_history_score,
                assessment.collateral_value,
                assessment.final_risk_score,
                assessment.risk_level.value if assessment.risk_level else None,
                assessment.timestamp.isoformat() if assessment.timestamp else None
            ))
            return assessment_id
        except Exception as e:
            raise RiskArchiveError(f"Failed to store risk assessment: {e}")

    def get_assessment_by_id(self, assessment_id: str) -> Optional[RiskAssessment]:
        """Get risk assessment by ID"""
        try:
            result = self.connection_factory.fetch_one(
                "SELECT * FROM risk_assessments WHERE assessment_id = ?",
                (assessment_id,)
            )
            return RiskAssessment.from_dict(result) if result else None
        except Exception as e:
            raise RiskArchiveError(f"Failed to retrieve assessment {assessment_id}: {e}")

    def get_assessment_by_loan(self, loan_id: str) -> Optional[RiskAssessment]:
        """Get risk assessment for specific loan (latest if multiple)"""
        try:
            result = self.connection_factory.fetch_one("""
                SELECT * FROM risk_assessments
                WHERE loan_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (loan_id,))
            return RiskAssessment.from_dict(result) if result else None
        except Exception as e:
            raise RiskArchiveError(f"Failed to retrieve assessment for loan {loan_id}: {e}")

    def get_all_assessments_for_loan(self, loan_id: str) -> List[RiskAssessment]:
        """Get all risk assessments for a loan (in case of reassessments)"""
        try:
            results = self.connection_factory.fetch_all("""
                SELECT * FROM risk_assessments
                WHERE loan_id = ?
                ORDER BY timestamp DESC
            """, (loan_id,))
            return [RiskAssessment.from_dict(row) for row in results]
        except Exception as e:
            raise RiskArchiveError(f"Failed to retrieve assessments for loan {loan_id}: {e}")

    def get_assessments_by_risk_level(self, risk_level: RiskLevel) -> List[RiskAssessment]:
        """Get assessments by risk level"""
        try:
            results = self.connection_factory.fetch_all("""
                SELECT * FROM risk_assessments
                WHERE risk_level = ?
                ORDER BY timestamp DESC
            """, (risk_level.value,))
            return [RiskAssessment.from_dict(row) for row in results]
        except Exception as e:
            raise RiskArchiveError(f"Failed to retrieve assessments by risk level: {e}")

    def get_risk_trends(self, days: int = 30) -> RiskTrendData:
        """Analyze risk assessment trends"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            results = self.connection_factory.fetch_all("""
                SELECT * FROM risk_assessments
                WHERE timestamp >= ?
                ORDER BY timestamp
            """, (cutoff_date.isoformat(),))

            assessments = [RiskAssessment.from_dict(row) for row in results]
            return RiskTrendData.from_assessments(assessments, days)
        except Exception as e:
            raise RiskArchiveError(f"Failed to analyze risk trends: {e}")

    def search_assessments(self, filters: Dict[str, Any]) -> List[RiskAssessment]:
        """Search risk assessments with flexible filters"""
        conditions = []
        params = []

        # Build WHERE clause dynamically
        if 'loan_id' in filters:
            conditions.append("loan_id = ?")
            params.append(filters['loan_id'])

        if 'risk_level' in filters:
            risk_level = filters['risk_level']
            conditions.append("risk_level = ?")
            params.append(risk_level.value if isinstance(risk_level, RiskLevel) else risk_level)

        if 'min_credit_score' in filters:
            conditions.append("credit_score >= ?")
            params.append(filters['min_credit_score'])

        if 'max_credit_score' in filters:
            conditions.append("credit_score <= ?")
            params.append(filters['max_credit_score'])

        if 'min_risk_score' in filters:
            conditions.append("final_risk_score >= ?")
            params.append(filters['min_risk_score'])

        if 'max_risk_score' in filters:
            conditions.append("final_risk_score <= ?")
            params.append(filters['max_risk_score'])

        if 'min_debt_to_income' in filters:
            conditions.append("debt_to_income >= ?")
            params.append(filters['min_debt_to_income'])

        if 'max_debt_to_income' in filters:
            conditions.append("debt_to_income <= ?")
            params.append(filters['max_debt_to_income'])

        if 'start_date' in filters:
            conditions.append("timestamp >= ?")
            start_date = filters['start_date']
            params.append(start_date.isoformat() if isinstance(start_date, datetime) else start_date)

        if 'end_date' in filters:
            conditions.append("timestamp <= ?")
            end_date = filters['end_date']
            params.append(end_date.isoformat() if isinstance(end_date, datetime) else end_date)

        # Build final query
        base_query = "SELECT * FROM risk_assessments"
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        base_query += " ORDER BY timestamp DESC"

        # Add limit if specified
        if 'limit' in filters:
            base_query += " LIMIT ?"
            params.append(filters['limit'])

        try:
            results = self.connection_factory.fetch_all(base_query, tuple(params))
            return [RiskAssessment.from_dict(row) for row in results]
        except Exception as e:
            raise RiskArchiveError(f"Failed to search assessments: {e}")

    def get_risk_statistics(self) -> Dict[str, Any]:
        """Get comprehensive risk statistics"""
        try:
            stats = {}

            # Total assessments
            result = self.connection_factory.fetch_one("SELECT COUNT(*) as count FROM risk_assessments")
            stats['total_assessments'] = result['count'] if result else 0

            # Average risk score
            result = self.connection_factory.fetch_one("""
                SELECT AVG(final_risk_score) as avg_score FROM risk_assessments
                WHERE final_risk_score IS NOT NULL
            """)
            stats['average_risk_score'] = round(result['avg_score'], 2) if result and result['avg_score'] else None

            # Risk level distribution
            results = self.connection_factory.fetch_all("""
                SELECT risk_level, COUNT(*) as count
                FROM risk_assessments
                WHERE risk_level IS NOT NULL
                GROUP BY risk_level
                ORDER BY count DESC
            """)
            stats['risk_level_distribution'] = {row['risk_level']: row['count'] for row in results}

            # Credit score statistics
            result = self.connection_factory.fetch_one("""
                SELECT
                    AVG(credit_score) as avg_credit,
                    MIN(credit_score) as min_credit,
                    MAX(credit_score) as max_credit
                FROM risk_assessments
                WHERE credit_score IS NOT NULL
            """)
            if result and result['avg_credit']:
                stats['credit_score_stats'] = {
                    'average': round(result['avg_credit'], 2),
                    'minimum': result['min_credit'],
                    'maximum': result['max_credit']
                }

            # Debt-to-income statistics
            result = self.connection_factory.fetch_one("""
                SELECT
                    AVG(debt_to_income) as avg_dti,
                    MIN(debt_to_income) as min_dti,
                    MAX(debt_to_income) as max_dti
                FROM risk_assessments
                WHERE debt_to_income IS NOT NULL
            """)
            if result and result['avg_dti']:
                stats['debt_to_income_stats'] = {
                    'average': round(result['avg_dti'], 3),
                    'minimum': round(result['min_dti'], 3),
                    'maximum': round(result['max_dti'], 3)
                }

            # High risk percentage
            high_risk_result = self.connection_factory.fetch_one("""
                SELECT COUNT(*) as high_risk_count FROM risk_assessments
                WHERE risk_level IN ('HIGH', 'VERY HIGH')
            """)
            if stats['total_assessments'] > 0:
                high_risk_count = high_risk_result['high_risk_count'] if high_risk_result else 0
                stats['high_risk_percentage'] = round((high_risk_count / stats['total_assessments']) * 100, 2)

            # Recent assessments (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            result = self.connection_factory.fetch_one("""
                SELECT COUNT(*) as count FROM risk_assessments
                WHERE timestamp >= ?
            """, (cutoff_date.isoformat(),))
            stats['assessments_last_30_days'] = result['count'] if result else 0

            return stats
        except Exception as e:
            raise RiskArchiveError(f"Failed to calculate risk statistics: {e}")

    def update_assessment(self, assessment_id: str, updates: Dict[str, Any]) -> None:
        """Update risk assessment (use with caution)"""
        allowed_fields = {
            'credit_score', 'debt_to_income', 'payment_history_score',
            'collateral_value', 'final_risk_score', 'risk_level'
        }

        # Filter to only allowed fields
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

        if not update_fields:
            return

        # Build dynamic update query
        set_clauses = []
        params = []
        for field, value in update_fields.items():
            set_clauses.append(f"{field} = ?")
            if field == 'risk_level' and isinstance(value, RiskLevel):
                params.append(value.value)
            else:
                params.append(value)

        params.append(assessment_id)

        query = f"UPDATE risk_assessments SET {', '.join(set_clauses)} WHERE assessment_id = ?"

        try:
            rows_affected = self.connection_factory.execute_query(query, tuple(params)).rowcount
            if rows_affected == 0:
                raise RiskArchiveError(f"Assessment {assessment_id} not found")
        except RiskArchiveError:
            raise
        except Exception as e:
            raise RiskArchiveError(f"Failed to update assessment: {e}")

    def delete_assessment(self, assessment_id: str) -> bool:
        """Delete risk assessment (use with extreme caution)"""
        try:
            rows_affected = self.connection_factory.execute_query(
                "DELETE FROM risk_assessments WHERE assessment_id = ?",
                (assessment_id,)
            ).rowcount
            return rows_affected > 0
        except Exception as e:
            raise RiskArchiveError(f"Failed to delete assessment: {e}")

    def export_assessments(self, filters: Optional[Dict[str, Any]] = None, format: str = 'json') -> str:
        """Export risk assessments in specified format"""
        try:
            if filters:
                assessments = self.search_assessments(filters)
            else:
                assessments = self.search_assessments({})

            if format.lower() == 'json':
                import json
                assessment_dicts = [assessment.to_dict() for assessment in assessments]
                return json.dumps(assessment_dicts, indent=2)

            elif format.lower() == 'csv':
                import csv
                import io
                output = io.StringIO()
                writer = csv.writer(output)

                # Header
                writer.writerow([
                    'assessment_id', 'loan_id', 'credit_score', 'debt_to_income',
                    'payment_history_score', 'collateral_value', 'final_risk_score',
                    'risk_level', 'timestamp'
                ])

                # Data
                for assessment in assessments:
                    writer.writerow([
                        assessment.assessment_id,
                        assessment.loan_id,
                        assessment.credit_score,
                        assessment.debt_to_income,
                        assessment.payment_history_score,
                        assessment.collateral_value,
                        assessment.final_risk_score,
                        assessment.risk_level.value if assessment.risk_level else '',
                        assessment.timestamp.isoformat() if assessment.timestamp else ''
                    ])

                return output.getvalue()

            else:
                raise RiskArchiveError(f"Unsupported export format: {format}")

        except Exception as e:
            raise RiskArchiveError(f"Failed to export assessments: {e}")

    def cleanup_old_assessments(self, days_to_keep: int = 365) -> int:
        """Clean up old risk assessments (use with extreme caution)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            rows_affected = self.connection_factory.execute_query(
                "DELETE FROM risk_assessments WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            ).rowcount
            return rows_affected
        except Exception as e:
            raise RiskArchiveError(f"Failed to cleanup old assessments: {e}")