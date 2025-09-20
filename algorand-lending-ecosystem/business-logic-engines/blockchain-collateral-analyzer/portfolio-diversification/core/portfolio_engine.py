"""
Portfolio Diversification Engine

Main engine for calculating portfolio diversification scores using configurable parameters.
"""

import math
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import json

from .config import PortfolioDiversificationConfig, load_config


@dataclass
class AssetPosition:
    """Represents a position in a single asset"""
    symbol: str
    asset_type: str
    value_usd: float
    weight: float
    volatility_30d: float = 0.0
    daily_volume_usd: float = 0.0
    liquidity_tier: str = "medium"
    correlation_with_portfolio: float = 0.0


@dataclass
class Portfolio:
    """Represents a complete portfolio"""
    positions: List[AssetPosition]
    total_value_usd: float
    timestamp: datetime


@dataclass
class DiversificationAnalysis:
    """Results of portfolio diversification analysis"""
    portfolio: Portfolio
    hhi_score: float
    diversification_score: float
    diversification_level: str
    concentration_violations: List[str]
    correlation_risks: List[str]
    liquidity_risks: List[str]
    recommendations: List[str]
    risk_adjustments: Dict[str, float]
    confidence_score: float
    analysis_timestamp: datetime


class PortfolioDiversificationEngine:
    """Main engine for portfolio diversification analysis"""

    def __init__(self, config: Optional[PortfolioDiversificationConfig] = None):
        """Initialize the portfolio diversification engine"""
        self.config = config or load_config()
        self.db_path = Path(self.config.database.default_path)
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the database for storing analysis results"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS diversification_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    portfolio_value_usd REAL,
                    num_positions INTEGER,
                    hhi_score REAL,
                    diversification_score REAL,
                    diversification_level TEXT,
                    confidence_score REAL,
                    analysis_data TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    symbol TEXT,
                    asset_type TEXT,
                    value_usd REAL,
                    weight REAL,
                    volatility_30d REAL,
                    daily_volume_usd REAL,
                    liquidity_tier TEXT,
                    FOREIGN KEY (analysis_id) REFERENCES diversification_analysis (id)
                )
            """)

    def calculate_hhi_score(self, portfolio: Portfolio) -> float:
        """
        Calculate Herfindahl-Hirschman Index for the portfolio

        Args:
            portfolio: Portfolio to analyze

        Returns:
            HHI score (0-1, lower is more diversified)
        """
        if len(portfolio.positions) <= 1:
            return self.config.hhi_calculation.max_hhi

        total_value = portfolio.total_value_usd
        if total_value <= 0:
            return self.config.hhi_calculation.max_hhi

        # Calculate asset type distribution
        type_distribution = {}
        for position in portfolio.positions:
            asset_type = position.asset_type
            if asset_type not in type_distribution:
                type_distribution[asset_type] = 0
            type_distribution[asset_type] += position.value_usd

        # Convert to proportions and calculate HHI
        type_proportions = [v / total_value for v in type_distribution.values()]
        hhi = sum(p**2 for p in type_proportions)

        return hhi

    def calculate_diversification_score(self, hhi_score: float) -> float:
        """
        Convert HHI to diversification score (0-1, higher is better)

        Args:
            hhi_score: Herfindahl-Hirschman Index score

        Returns:
            Diversification score (0-1, higher is better)
        """
        max_hhi = self.config.hhi_calculation.max_hhi
        min_hhi = self.config.hhi_calculation.min_hhi

        diversification_score = (max_hhi - hhi_score) / (max_hhi - min_hhi)
        return max(0.0, min(1.0, diversification_score))

    def get_diversification_level(self, diversification_score: float) -> str:
        """
        Get diversification level based on score

        Args:
            diversification_score: Diversification score (0-1)

        Returns:
            Diversification level string
        """
        if diversification_score >= self.config.diversification_scoring.excellent_threshold:
            return "excellent"
        elif diversification_score >= self.config.diversification_scoring.good_threshold:
            return "good"
        elif diversification_score >= self.config.diversification_scoring.adequate_threshold:
            return "adequate"
        elif diversification_score >= self.config.diversification_scoring.poor_threshold:
            return "poor"
        else:
            return "very_poor"

    def check_concentration_violations(self, portfolio: Portfolio) -> List[str]:
        """
        Check for concentration limit violations

        Args:
            portfolio: Portfolio to analyze

        Returns:
            List of violation descriptions
        """
        violations = []
        total_value = portfolio.total_value_usd

        if total_value <= 0:
            return violations

        # Check single asset concentration
        for position in portfolio.positions:
            weight = position.value_usd / total_value
            if weight > self.config.concentration_limits.single_asset_max:
                violations.append(
                    f"Asset {position.symbol} concentration ({weight:.1%}) exceeds "
                    f"limit ({self.config.concentration_limits.single_asset_max:.1%})"
                )

        # Check asset type concentration
        type_totals = {}
        for position in portfolio.positions:
            asset_type = position.asset_type
            if asset_type not in type_totals:
                type_totals[asset_type] = 0
            type_totals[asset_type] += position.value_usd

        for asset_type, value in type_totals.items():
            weight = value / total_value
            if weight > self.config.concentration_limits.single_type_max:
                violations.append(
                    f"Asset type {asset_type} concentration ({weight:.1%}) exceeds "
                    f"limit ({self.config.concentration_limits.single_type_max:.1%})"
                )

        # Check low liquidity concentration
        low_liquidity_value = sum(
            pos.value_usd for pos in portfolio.positions
            if pos.liquidity_tier == "low"
        )
        low_liquidity_weight = low_liquidity_value / total_value
        if low_liquidity_weight > self.config.concentration_limits.low_liquidity_max:
            violations.append(
                f"Low-liquidity assets concentration ({low_liquidity_weight:.1%}) exceeds "
                f"limit ({self.config.concentration_limits.low_liquidity_max:.1%})"
            )

        return violations

    def analyze_correlation_risks(self, portfolio: Portfolio) -> List[str]:
        """
        Analyze correlation risks using configured correlation matrix

        Args:
            portfolio: Portfolio to analyze

        Returns:
            List of correlation risk descriptions
        """
        risks = []
        correlations = self.config.asset_type_correlations

        if not correlations:
            return risks

        # Group positions by asset type
        type_weights = {}
        for position in portfolio.positions:
            asset_type = position.asset_type
            if asset_type not in type_weights:
                type_weights[asset_type] = 0
            type_weights[asset_type] += position.weight

        # Check for high correlation exposures
        for type1, weight1 in type_weights.items():
            for type2, weight2 in type_weights.items():
                if type1 >= type2:  # Avoid duplicate checks
                    continue

                correlation = correlations.get(type1, {}).get(type2, 0.0)
                combined_weight = weight1 + weight2

                if (correlation >= self.config.correlation_analysis.high_correlation_threshold and
                    combined_weight > self.config.concentration_limits.correlated_assets_max):
                    risks.append(
                        f"High correlation ({correlation:.1%}) between {type1} and {type2} "
                        f"with combined weight {combined_weight:.1%}"
                    )

        return risks

    def analyze_liquidity_risks(self, portfolio: Portfolio) -> List[str]:
        """
        Analyze liquidity risks in the portfolio

        Args:
            portfolio: Portfolio to analyze

        Returns:
            List of liquidity risk descriptions
        """
        risks = []

        # Calculate liquidity distribution
        liquidity_weights = {"high": 0.0, "medium": 0.0, "low": 0.0}
        for position in portfolio.positions:
            liquidity_weights[position.liquidity_tier] += position.weight

        # Check minimum high-liquidity requirement
        required_high_liquidity = self.config.optimization_recommendations.risk_management.liquidity_requirement
        if liquidity_weights["high"] < required_high_liquidity:
            risks.append(
                f"High-liquidity assets ({liquidity_weights['high']:.1%}) below "
                f"requirement ({required_high_liquidity:.1%})"
            )

        # Check for excessive low-liquidity exposure
        max_low_liquidity = self.config.concentration_limits.low_liquidity_max
        if liquidity_weights["low"] > max_low_liquidity:
            risks.append(
                f"Low-liquidity assets ({liquidity_weights['low']:.1%}) exceed "
                f"limit ({max_low_liquidity:.1%})"
            )

        return risks

    def generate_recommendations(self, analysis: DiversificationAnalysis) -> List[str]:
        """
        Generate recommendations for improving portfolio diversification

        Args:
            analysis: Current diversification analysis

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Diversification recommendations
        if analysis.diversification_level in ["poor", "very_poor"]:
            recommendations.append(
                f"Improve diversification across asset types (current score: {analysis.diversification_score:.1%})"
            )

            target_types = self.config.optimization_recommendations.diversification_targets.target_asset_types
            current_types = len(set(pos.asset_type for pos in analysis.portfolio.positions))
            if current_types < target_types:
                recommendations.append(
                    f"Add positions in {target_types - current_types} additional asset types"
                )

        # Concentration recommendations
        for violation in analysis.concentration_violations:
            if "Asset " in violation and "concentration" in violation:
                recommendations.append("Reduce concentration in over-weighted assets")
                break

        # Correlation recommendations
        if analysis.correlation_risks:
            recommendations.append("Reduce exposure to highly correlated asset types")

        # Liquidity recommendations
        if analysis.liquidity_risks:
            recommendations.append("Increase allocation to high-liquidity assets")

        # Rebalancing recommendations
        threshold = self.config.position_thresholds.rebalancing_threshold
        recommendations.append(
            f"Consider rebalancing if any position deviates more than {threshold:.1%} from target"
        )

        return recommendations

    def calculate_risk_adjustments(self, diversification_level: str) -> Dict[str, float]:
        """
        Calculate risk adjustments based on diversification level

        Args:
            diversification_level: Diversification level string

        Returns:
            Dictionary of risk adjustments
        """
        adjustments = {}

        risk_config = getattr(self.config.risk_adjustments, f"{diversification_level}_diversification", None)
        if not risk_config:
            return adjustments

        if risk_config.collateral_ratio_reduction:
            adjustments["collateral_ratio_reduction"] = risk_config.collateral_ratio_reduction

        if risk_config.collateral_ratio_increase:
            adjustments["collateral_ratio_increase"] = risk_config.collateral_ratio_increase

        if risk_config.confidence_bonus:
            adjustments["confidence_bonus"] = risk_config.confidence_bonus

        if risk_config.confidence_penalty:
            adjustments["confidence_penalty"] = risk_config.confidence_penalty

        return adjustments

    def calculate_confidence_score(self, analysis: DiversificationAnalysis) -> float:
        """
        Calculate confidence score for the analysis

        Args:
            analysis: Diversification analysis

        Returns:
            Confidence score (0-1)
        """
        base_confidence = self.config.analysis.default_confidence_score

        # Adjust for diversification level
        risk_adjustments = analysis.risk_adjustments
        if "confidence_bonus" in risk_adjustments:
            base_confidence += risk_adjustments["confidence_bonus"]
        elif "confidence_penalty" in risk_adjustments:
            base_confidence -= risk_adjustments["confidence_penalty"]

        # Adjust for portfolio size
        portfolio_size = analysis.portfolio.total_value_usd
        min_size = self.config.position_thresholds.minimum_portfolio_usd
        if portfolio_size < min_size:
            size_penalty = (min_size - portfolio_size) / min_size * 0.2
            base_confidence -= size_penalty

        # Adjust for number of positions
        num_positions = len(analysis.portfolio.positions)
        if num_positions < 3:
            position_penalty = (3 - num_positions) * 0.1
            base_confidence -= position_penalty

        return max(0.0, min(1.0, base_confidence))

    def analyze_portfolio(self, portfolio: Portfolio) -> DiversificationAnalysis:
        """
        Perform complete diversification analysis on a portfolio

        Args:
            portfolio: Portfolio to analyze

        Returns:
            Complete diversification analysis
        """
        # Calculate HHI and diversification scores
        hhi_score = self.calculate_hhi_score(portfolio)
        diversification_score = self.calculate_diversification_score(hhi_score)
        diversification_level = self.get_diversification_level(diversification_score)

        # Analyze risks and violations
        concentration_violations = self.check_concentration_violations(portfolio)
        correlation_risks = self.analyze_correlation_risks(portfolio)
        liquidity_risks = self.analyze_liquidity_risks(portfolio)

        # Calculate risk adjustments
        risk_adjustments = self.calculate_risk_adjustments(diversification_level)

        # Create initial analysis object
        analysis = DiversificationAnalysis(
            portfolio=portfolio,
            hhi_score=hhi_score,
            diversification_score=diversification_score,
            diversification_level=diversification_level,
            concentration_violations=concentration_violations,
            correlation_risks=correlation_risks,
            liquidity_risks=liquidity_risks,
            recommendations=[],  # Will be populated below
            risk_adjustments=risk_adjustments,
            confidence_score=0.0,  # Will be calculated below
            analysis_timestamp=datetime.now()
        )

        # Generate recommendations and calculate confidence
        analysis.recommendations = self.generate_recommendations(analysis)
        analysis.confidence_score = self.calculate_confidence_score(analysis)

        # Store analysis in database
        self._store_analysis(analysis)

        return analysis

    def _store_analysis(self, analysis: DiversificationAnalysis):
        """Store analysis results in database"""
        if not self.config.database.backup_enabled:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Insert main analysis record
                cursor.execute("""
                    INSERT INTO diversification_analysis
                    (portfolio_value_usd, num_positions, hhi_score, diversification_score,
                     diversification_level, confidence_score, analysis_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis.portfolio.total_value_usd,
                    len(analysis.portfolio.positions),
                    analysis.hhi_score,
                    analysis.diversification_score,
                    analysis.diversification_level,
                    analysis.confidence_score,
                    json.dumps(asdict(analysis), default=str)
                ))

                analysis_id = cursor.lastrowid

                # Insert position records
                for position in analysis.portfolio.positions:
                    cursor.execute("""
                        INSERT INTO portfolio_positions
                        (analysis_id, symbol, asset_type, value_usd, weight,
                         volatility_30d, daily_volume_usd, liquidity_tier)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        analysis_id,
                        position.symbol,
                        position.asset_type,
                        position.value_usd,
                        position.weight,
                        position.volatility_30d,
                        position.daily_volume_usd,
                        position.liquidity_tier
                    ))

                conn.commit()

        except Exception as e:
            print(f"Warning: Could not store analysis in database: {e}")

    def get_analysis_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get historical analysis results

        Args:
            limit: Maximum number of records to return

        Returns:
            List of historical analysis records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM diversification_analysis
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Warning: Could not retrieve analysis history: {e}")
            return []


def create_sample_portfolio() -> Portfolio:
    """Create a sample portfolio for testing"""
    positions = [
        AssetPosition(
            symbol="BTC",
            asset_type="cryptocurrency",
            value_usd=50000,
            weight=0.5,
            volatility_30d=0.15,
            daily_volume_usd=25_000_000_000,
            liquidity_tier="high"
        ),
        AssetPosition(
            symbol="ETH",
            asset_type="cryptocurrency",
            value_usd=25000,
            weight=0.25,
            volatility_30d=0.18,
            daily_volume_usd=15_000_000_000,
            liquidity_tier="high"
        ),
        AssetPosition(
            symbol="USDC",
            asset_type="stablecoin",
            value_usd=15000,
            weight=0.15,
            volatility_30d=0.02,
            daily_volume_usd=5_000_000_000,
            liquidity_tier="high"
        ),
        AssetPosition(
            symbol="UNI",
            asset_type="defi_token",
            value_usd=8000,
            weight=0.08,
            volatility_30d=0.25,
            daily_volume_usd=200_000_000,
            liquidity_tier="medium"
        ),
        AssetPosition(
            symbol="APE",
            asset_type="nft",
            value_usd=2000,
            weight=0.02,
            volatility_30d=0.35,
            daily_volume_usd=50_000_000,
            liquidity_tier="low"
        )
    ]

    total_value = sum(pos.value_usd for pos in positions)

    return Portfolio(
        positions=positions,
        total_value_usd=total_value,
        timestamp=datetime.now()
    )