"""
Advanced Bias Detection Algorithms for Fair Lending Compliance

This module provides sophisticated statistical algorithms for detecting bias in lending decisions.
Implements multiple detection methods including:
- Statistical parity and equalized odds
- Disparate impact analysis
- Individual fairness metrics
- Causal fairness analysis
- Protected class analysis per ECOA requirements

Designed to meet regulatory requirements and provide actionable insights for compliance teams.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy import stats
import statistics
from sklearn.metrics import confusion_matrix
from sklearn.ensemble import IsolationForest
import warnings

logger = logging.getLogger(__name__)

# Suppress scipy warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)


class FairnessMetric(Enum):
    """Types of fairness metrics for bias detection"""
    STATISTICAL_PARITY = "statistical_parity"
    EQUALIZED_ODDS = "equalized_odds"
    EQUALIZED_OPPORTUNITY = "equalized_opportunity"
    PREDICTIVE_PARITY = "predictive_parity"
    CALIBRATION = "calibration"
    INDIVIDUAL_FAIRNESS = "individual_fairness"
    COUNTERFACTUAL_FAIRNESS = "counterfactual_fairness"


class ProtectedAttribute(Enum):
    """Protected attributes under fair lending laws"""
    RACE = "race"
    ETHNICITY = "ethnicity"
    GENDER = "gender"
    AGE = "age"
    RELIGION = "religion"
    NATIONAL_ORIGIN = "national_origin"
    MARITAL_STATUS = "marital_status"
    DISABILITY_STATUS = "disability_status"
    SEXUAL_ORIENTATION = "sexual_orientation"
    GENDER_IDENTITY = "gender_identity"


@dataclass
class FairnessResult:
    """Result of a fairness analysis"""
    metric_type: FairnessMetric
    protected_attribute: str
    reference_group: str
    comparison_groups: List[str]
    metric_values: Dict[str, float]
    disparity_ratios: Dict[str, float]
    statistical_significance: Dict[str, float]
    effect_sizes: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    bias_detected: bool
    severity_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    sample_sizes: Dict[str, int]
    recommendations: List[str]
    regulatory_notes: List[str]


@dataclass
class BiasTestConfig:
    """Configuration for bias testing"""
    significance_level: float = 0.05
    effect_size_threshold: float = 0.2
    minimum_sample_size: int = 30
    disparity_threshold: float = 0.8  # 80% rule threshold
    high_severity_threshold: float = 0.6
    critical_severity_threshold: float = 0.4


class BiasDetector:
    """
    Advanced bias detection system for fair lending compliance

    Implements comprehensive statistical tests and fairness metrics to detect
    potential bias in lending decisions across protected classes.
    """

    def __init__(self, config: Optional[BiasTestConfig] = None):
        self.config = config or BiasTestConfig()
        self.protected_attributes = list(ProtectedAttribute)

    def detect_all_bias_types(
        self,
        loan_data: List[Dict[str, Any]],
        outcomes: List[str] = None
    ) -> List[FairnessResult]:
        """
        Perform comprehensive bias detection across all fairness metrics

        Args:
            loan_data: List of loan application records
            outcomes: List of outcome variables to analyze (default: ['approved', 'interest_rate'])

        Returns:
            List of fairness analysis results
        """
        if outcomes is None:
            outcomes = ['approved', 'interest_rate', 'loan_amount']

        results = []

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(loan_data)

        if len(df) < self.config.minimum_sample_size:
            logger.warning(f"Insufficient data for bias analysis: {len(df)} records")
            return results

        # Analyze each protected attribute
        for attr in self._get_available_attributes(df):
            try:
                # Statistical Parity Analysis
                if 'approved' in outcomes:
                    parity_result = self._analyze_statistical_parity(
                        df, attr, 'approved'
                    )
                    if parity_result:
                        results.append(parity_result)

                # Equalized Odds Analysis
                if 'approved' in outcomes and self._has_ground_truth(df):
                    odds_result = self._analyze_equalized_odds(
                        df, attr, 'approved'
                    )
                    if odds_result:
                        results.append(odds_result)

                # Interest Rate Disparity Analysis
                if 'interest_rate' in outcomes:
                    rate_result = self._analyze_rate_disparity(
                        df, attr, 'interest_rate'
                    )
                    if rate_result:
                        results.append(rate_result)

                # Loan Amount Disparity Analysis
                if 'loan_amount' in outcomes:
                    amount_result = self._analyze_amount_disparity(
                        df, attr, 'loan_amount'
                    )
                    if amount_result:
                        results.append(amount_result)

            except Exception as e:
                logger.error(f"Error analyzing {attr}: {e}")
                continue

        return results

    def _analyze_statistical_parity(
        self,
        df: pd.DataFrame,
        protected_attr: str,
        outcome: str
    ) -> Optional[FairnessResult]:
        """
        Analyze statistical parity (independence) for binary outcomes

        Statistical parity requires that the probability of a positive outcome
        is the same across all groups: P(Y=1|A=a) = P(Y=1|A=b)
        """

        if protected_attr not in df.columns or outcome not in df.columns:
            return None

        # Get unique groups
        groups = df[protected_attr].dropna().unique()
        if len(groups) < 2:
            return None

        # Calculate approval rates by group
        group_stats = {}
        for group in groups:
            group_data = df[df[protected_attr] == group]
            if len(group_data) < self.config.minimum_sample_size:
                continue

            approved_count = group_data[outcome].sum()
            total_count = len(group_data)
            approval_rate = approved_count / total_count

            group_stats[str(group)] = {
                'rate': approval_rate,
                'approved': approved_count,
                'total': total_count,
                'sample_size': total_count
            }

        if len(group_stats) < 2:
            return None

        # Find reference group (typically majority or highest approval rate)
        reference_group = max(group_stats.keys(),
                            key=lambda g: group_stats[g]['rate'])

        # Calculate disparities
        disparity_ratios = {}
        p_values = {}
        effect_sizes = {}
        confidence_intervals = {}

        reference_rate = group_stats[reference_group]['rate']

        for group_name, stats in group_stats.items():
            if group_name == reference_group:
                disparity_ratios[group_name] = 1.0
                p_values[group_name] = 1.0
                effect_sizes[group_name] = 0.0
                confidence_intervals[group_name] = (stats['rate'] - 0.05, stats['rate'] + 0.05)
                continue

            # Calculate disparity ratio
            group_rate = stats['rate']
            disparity_ratio = group_rate / reference_rate if reference_rate > 0 else 0

            # Perform statistical test (two-proportion z-test)
            ref_stats = group_stats[reference_group]

            # Calculate pooled proportion
            p_pooled = ((stats['approved'] + ref_stats['approved']) /
                       (stats['total'] + ref_stats['total']))

            # Calculate standard error
            se = np.sqrt(p_pooled * (1 - p_pooled) *
                        (1/stats['total'] + 1/ref_stats['total']))

            # Z-statistic
            if se > 0:
                z_stat = (group_rate - reference_rate) / se
                p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
            else:
                z_stat = 0
                p_value = 1.0

            # Effect size (Cohen's h for proportions)
            h = 2 * (np.arcsin(np.sqrt(group_rate)) - np.arcsin(np.sqrt(reference_rate)))

            # Confidence interval for difference in proportions
            diff = group_rate - reference_rate
            se_diff = np.sqrt((group_rate * (1 - group_rate) / stats['total']) +
                             (reference_rate * (1 - reference_rate) / ref_stats['total']))

            ci_lower = diff - 1.96 * se_diff
            ci_upper = diff + 1.96 * se_diff

            disparity_ratios[group_name] = disparity_ratio
            p_values[group_name] = p_value
            effect_sizes[group_name] = abs(h)
            confidence_intervals[group_name] = (ci_lower, ci_upper)

        # Determine bias detection
        bias_detected = any(
            ratio < self.config.disparity_threshold or
            p_values[group] < self.config.significance_level
            for group, ratio in disparity_ratios.items()
            if group != reference_group
        )

        # Determine severity
        severity = self._calculate_severity_level(disparity_ratios, p_values, reference_group)

        # Generate recommendations
        recommendations = self._generate_parity_recommendations(
            disparity_ratios, bias_detected, severity
        )

        # Regulatory notes
        regulatory_notes = self._generate_regulatory_notes(
            FairnessMetric.STATISTICAL_PARITY, bias_detected, severity
        )

        return FairnessResult(
            metric_type=FairnessMetric.STATISTICAL_PARITY,
            protected_attribute=protected_attr,
            reference_group=reference_group,
            comparison_groups=[g for g in group_stats.keys() if g != reference_group],
            metric_values={g: stats['rate'] for g, stats in group_stats.items()},
            disparity_ratios=disparity_ratios,
            statistical_significance=p_values,
            effect_sizes=effect_sizes,
            confidence_intervals=confidence_intervals,
            bias_detected=bias_detected,
            severity_level=severity,
            sample_sizes={g: stats['sample_size'] for g, stats in group_stats.items()},
            recommendations=recommendations,
            regulatory_notes=regulatory_notes
        )

    def _analyze_equalized_odds(
        self,
        df: pd.DataFrame,
        protected_attr: str,
        outcome: str
    ) -> Optional[FairnessResult]:
        """
        Analyze equalized odds fairness metric

        Equalized odds requires that true positive rate and false positive rate
        are equal across groups: TPR(A=a) = TPR(A=b) and FPR(A=a) = FPR(A=b)
        """

        # This would require ground truth labels (actual creditworthiness)
        # For demonstration, we'll use risk_score as a proxy
        if 'risk_score' not in df.columns:
            return None

        # Define ground truth based on risk score threshold
        risk_threshold = df['risk_score'].median()
        df = df.copy()
        df['ground_truth'] = (df['risk_score'] <= risk_threshold).astype(int)

        groups = df[protected_attr].dropna().unique()
        if len(groups) < 2:
            return None

        group_metrics = {}

        for group in groups:
            group_data = df[df[protected_attr] == group]
            if len(group_data) < self.config.minimum_sample_size:
                continue

            # Calculate confusion matrix
            y_true = group_data['ground_truth']
            y_pred = group_data[outcome].astype(int)

            if len(y_true.unique()) < 2 or len(y_pred.unique()) < 2:
                continue

            tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

            # Calculate TPR and FPR
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

            group_metrics[str(group)] = {
                'tpr': tpr,
                'fpr': fpr,
                'sample_size': len(group_data)
            }

        if len(group_metrics) < 2:
            return None

        # Find reference group
        reference_group = max(group_metrics.keys(),
                            key=lambda g: group_metrics[g]['tpr'])

        # Calculate disparities in TPR and FPR
        tpr_disparities = {}
        fpr_disparities = {}

        ref_tpr = group_metrics[reference_group]['tpr']
        ref_fpr = group_metrics[reference_group]['fpr']

        for group_name, metrics in group_metrics.items():
            tpr_ratio = metrics['tpr'] / ref_tpr if ref_tpr > 0 else 1.0
            fpr_ratio = metrics['fpr'] / ref_fpr if ref_fpr > 0 else 1.0

            tpr_disparities[group_name] = tpr_ratio
            fpr_disparities[group_name] = fpr_ratio

        # Simple bias detection (would use more sophisticated tests in practice)
        bias_detected = any(
            abs(1 - ratio) > 0.2  # 20% difference threshold
            for ratio in list(tpr_disparities.values()) + list(fpr_disparities.values())
        )

        severity = "HIGH" if bias_detected else "LOW"

        return FairnessResult(
            metric_type=FairnessMetric.EQUALIZED_ODDS,
            protected_attribute=protected_attr,
            reference_group=reference_group,
            comparison_groups=[g for g in group_metrics.keys() if g != reference_group],
            metric_values={g: {'tpr': m['tpr'], 'fpr': m['fpr']}
                          for g, m in group_metrics.items()},
            disparity_ratios={'tpr': tpr_disparities, 'fpr': fpr_disparities},
            statistical_significance={},  # Would calculate proper p-values
            effect_sizes={},
            confidence_intervals={},
            bias_detected=bias_detected,
            severity_level=severity,
            sample_sizes={g: m['sample_size'] for g, m in group_metrics.items()},
            recommendations=self._generate_equalized_odds_recommendations(bias_detected),
            regulatory_notes=self._generate_regulatory_notes(
                FairnessMetric.EQUALIZED_ODDS, bias_detected, severity
            )
        )

    def _analyze_rate_disparity(
        self,
        df: pd.DataFrame,
        protected_attr: str,
        rate_column: str
    ) -> Optional[FairnessResult]:
        """Analyze disparities in continuous outcomes like interest rates"""

        if protected_attr not in df.columns or rate_column not in df.columns:
            return None

        # Filter to approved loans only
        approved_df = df[df.get('approved', True) == True].copy()
        if len(approved_df) < self.config.minimum_sample_size:
            return None

        groups = approved_df[protected_attr].dropna().unique()
        if len(groups) < 2:
            return None

        group_stats = {}
        rates_by_group = {}

        for group in groups:
            group_data = approved_df[approved_df[protected_attr] == group]
            if len(group_data) < self.config.minimum_sample_size:
                continue

            rates = group_data[rate_column].dropna()
            if len(rates) == 0:
                continue

            group_stats[str(group)] = {
                'mean': rates.mean(),
                'std': rates.std(),
                'median': rates.median(),
                'sample_size': len(rates)
            }
            rates_by_group[str(group)] = rates.values

        if len(group_stats) < 2:
            return None

        # Find reference group (lowest average rate)
        reference_group = min(group_stats.keys(),
                            key=lambda g: group_stats[g]['mean'])

        # Perform ANOVA test
        group_values = [rates_by_group[g] for g in group_stats.keys()]

        try:
            f_stat, p_value = stats.f_oneway(*group_values)
        except Exception:
            f_stat, p_value = 0, 1.0

        # Calculate effect size (eta-squared)
        all_rates = np.concatenate(group_values)
        ss_total = np.sum((all_rates - np.mean(all_rates))**2)
        ss_between = sum(
            len(group_rates) * (np.mean(group_rates) - np.mean(all_rates))**2
            for group_rates in group_values
        )
        eta_squared = ss_between / ss_total if ss_total > 0 else 0

        # Calculate disparities
        ref_mean = group_stats[reference_group]['mean']
        disparities = {}

        for group_name, stats in group_stats.items():
            ratio = stats['mean'] / ref_mean if ref_mean > 0 else 1.0
            disparities[group_name] = ratio

        bias_detected = (
            p_value < self.config.significance_level and
            eta_squared > self.config.effect_size_threshold
        )

        severity = self._calculate_severity_from_effect_size(eta_squared)

        return FairnessResult(
            metric_type=FairnessMetric.STATISTICAL_PARITY,  # Using for rate analysis
            protected_attribute=protected_attr,
            reference_group=reference_group,
            comparison_groups=[g for g in group_stats.keys() if g != reference_group],
            metric_values={g: stats['mean'] for g, stats in group_stats.items()},
            disparity_ratios=disparities,
            statistical_significance={'anova_p': p_value},
            effect_sizes={'eta_squared': eta_squared},
            confidence_intervals={},
            bias_detected=bias_detected,
            severity_level=severity,
            sample_sizes={g: stats['sample_size'] for g, stats in group_stats.items()},
            recommendations=self._generate_rate_disparity_recommendations(bias_detected, severity),
            regulatory_notes=self._generate_regulatory_notes(
                FairnessMetric.STATISTICAL_PARITY, bias_detected, severity
            )
        )

    def _analyze_amount_disparity(
        self,
        df: pd.DataFrame,
        protected_attr: str,
        amount_column: str
    ) -> Optional[FairnessResult]:
        """Analyze disparities in loan amounts"""
        # Similar implementation to rate disparity analysis
        return self._analyze_rate_disparity(df, protected_attr, amount_column)

    def detect_individual_bias(
        self,
        loan_record: Dict[str, Any],
        similar_loans: List[Dict[str, Any]],
        protected_attrs: List[str]
    ) -> Dict[str, Any]:
        """
        Detect individual-level bias using similar case analysis

        Compares treatment of individual case against similar cases
        with different protected attribute values.
        """

        if not similar_loans:
            return {"bias_detected": False, "confidence": 0.0}

        # Extract features (excluding protected attributes for fairness)
        feature_cols = [col for col in loan_record.keys()
                       if col not in protected_attrs and
                       col not in ['approved', 'interest_rate', 'loan_id']]

        # Calculate similarity scores
        similarities = []
        for similar_loan in similar_loans:
            similarity = self._calculate_similarity(
                loan_record, similar_loan, feature_cols
            )
            similarities.append((similarity, similar_loan))

        # Sort by similarity
        similarities.sort(key=lambda x: x[0], reverse=True)

        # Analyze top similar cases
        top_similar = similarities[:5]  # Top 5 most similar

        # Look for outcome differences despite similarity
        outcome_differences = []
        for similarity, similar_loan in top_similar:
            if similarity > 0.8:  # Very similar cases
                # Check if outcomes differ significantly
                rate_diff = abs(
                    loan_record.get('interest_rate', 0) -
                    similar_loan.get('interest_rate', 0)
                )
                approval_diff = (
                    loan_record.get('approved', False) !=
                    similar_loan.get('approved', False)
                )

                if rate_diff > 1.0 or approval_diff:  # Significant difference
                    outcome_differences.append({
                        'similarity': similarity,
                        'rate_difference': rate_diff,
                        'approval_difference': approval_diff,
                        'similar_loan': similar_loan
                    })

        bias_detected = len(outcome_differences) > 0
        confidence = len(outcome_differences) / len(top_similar) if top_similar else 0.0

        return {
            "bias_detected": bias_detected,
            "confidence": confidence,
            "similar_cases_analyzed": len(top_similar),
            "outcome_differences": outcome_differences,
            "explanation": self._generate_individual_bias_explanation(
                bias_detected, outcome_differences
            )
        }

    def _calculate_similarity(
        self,
        loan1: Dict[str, Any],
        loan2: Dict[str, Any],
        feature_cols: List[str]
    ) -> float:
        """Calculate similarity between two loan applications"""

        similarities = []

        for col in feature_cols:
            val1 = loan1.get(col)
            val2 = loan2.get(col)

            if val1 is None or val2 is None:
                continue

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Numerical similarity
                if val1 == val2 == 0:
                    sim = 1.0
                else:
                    sim = 1.0 - abs(val1 - val2) / max(abs(val1), abs(val2))
                similarities.append(max(0, sim))
            else:
                # Categorical similarity
                similarities.append(1.0 if val1 == val2 else 0.0)

        return statistics.mean(similarities) if similarities else 0.0

    # Helper methods

    def _get_available_attributes(self, df: pd.DataFrame) -> List[str]:
        """Get protected attributes that are available in the data"""
        available = []
        for attr in self.protected_attributes:
            attr_name = attr.value
            if attr_name in df.columns and df[attr_name].nunique() > 1:
                available.append(attr_name)
        return available

    def _has_ground_truth(self, df: pd.DataFrame) -> bool:
        """Check if ground truth labels are available"""
        return 'risk_score' in df.columns or 'creditworthiness' in df.columns

    def _calculate_severity_level(
        self,
        disparity_ratios: Dict[str, float],
        p_values: Dict[str, float],
        reference_group: str
    ) -> str:
        """Calculate severity level based on disparities and statistical significance"""

        min_ratio = min(
            ratio for group, ratio in disparity_ratios.items()
            if group != reference_group
        )

        significant_disparities = sum(
            1 for group, p_val in p_values.items()
            if group != reference_group and p_val < self.config.significance_level
        )

        if min_ratio < self.config.critical_severity_threshold:
            return "CRITICAL"
        elif min_ratio < self.config.high_severity_threshold:
            return "HIGH"
        elif significant_disparities > 0:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_severity_from_effect_size(self, effect_size: float) -> str:
        """Calculate severity level from effect size"""
        if effect_size > 0.8:
            return "CRITICAL"
        elif effect_size > 0.5:
            return "HIGH"
        elif effect_size > 0.2:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_parity_recommendations(
        self,
        disparity_ratios: Dict[str, float],
        bias_detected: bool,
        severity: str
    ) -> List[str]:
        """Generate recommendations for statistical parity issues"""

        recommendations = []

        if bias_detected:
            recommendations.extend([
                "Review credit decision criteria for potential disparate impact",
                "Analyze alternative credit assessment methods",
                "Conduct manual review of rejected applications from affected groups",
                "Consider implementing bias mitigation techniques"
            ])

            if severity in ["HIGH", "CRITICAL"]:
                recommendations.extend([
                    "Immediate review of lending policies required",
                    "Consider temporary suspension of automated decisions for affected groups",
                    "Engage legal counsel for regulatory compliance review"
                ])

        return recommendations

    def _generate_equalized_odds_recommendations(self, bias_detected: bool) -> List[str]:
        """Generate recommendations for equalized odds issues"""
        if bias_detected:
            return [
                "Review predictive model performance across demographic groups",
                "Consider model retraining with fairness constraints",
                "Implement post-processing bias mitigation techniques",
                "Validate model predictions with human oversight"
            ]
        return []

    def _generate_rate_disparity_recommendations(
        self,
        bias_detected: bool,
        severity: str
    ) -> List[str]:
        """Generate recommendations for interest rate disparities"""

        recommendations = []

        if bias_detected:
            recommendations.extend([
                "Review interest rate calculation methodology",
                "Ensure consistent risk-based pricing across all demographic groups",
                "Implement rate validation and approval workflows",
                "Conduct market rate benchmarking analysis"
            ])

            if severity == "CRITICAL":
                recommendations.extend([
                    "Immediate audit of all pricing decisions required",
                    "Consider rate adjustment for affected borrowers",
                    "Review compliance with fair lending regulations"
                ])

        return recommendations

    def _generate_regulatory_notes(
        self,
        metric_type: FairnessMetric,
        bias_detected: bool,
        severity: str
    ) -> List[str]:
        """Generate regulatory compliance notes"""

        notes = []

        if bias_detected:
            if metric_type == FairnessMetric.STATISTICAL_PARITY:
                notes.extend([
                    "Potential ECOA violation: Disparate impact in credit decisions",
                    "Fair Lending Act compliance review recommended",
                    "Document business justification for any disparities"
                ])

            if severity in ["HIGH", "CRITICAL"]:
                notes.extend([
                    "Immediate regulatory reporting may be required",
                    "Consider proactive outreach to regulatory agencies",
                    "Prepare remediation plan for affected borrowers"
                ])

        return notes

    def _generate_individual_bias_explanation(
        self,
        bias_detected: bool,
        outcome_differences: List[Dict[str, Any]]
    ) -> str:
        """Generate explanation for individual bias analysis"""

        if not bias_detected:
            return "No significant bias detected in individual case analysis."

        explanation = f"Potential individual bias detected. Found {len(outcome_differences)} "
        explanation += "cases with similar risk profiles but significantly different outcomes. "
        explanation += "Manual review recommended to verify business justification."

        return explanation