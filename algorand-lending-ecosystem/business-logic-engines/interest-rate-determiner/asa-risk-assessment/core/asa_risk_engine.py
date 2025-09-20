"""
ASA Risk Assessment Engine
Main engine that combines volatility, liquidity, and security analysis for comprehensive ASA risk scoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import yaml

from .asa_volatility import ASAVolatilityAnalyzer, VolatilityMetrics
from .asa_liquidity import ASALiquidityAnalyzer, LiquidityMetrics
from .smart_contract_security import SmartContractSecurityAnalyzer, SecurityMetrics


@dataclass
class RiskComponents:
    """Individual risk component scores"""
    volatility_metrics: VolatilityMetrics
    liquidity_metrics: LiquidityMetrics
    security_metrics: SecurityMetrics
    combined_risk_score: float
    risk_tier: str
    max_ltv: float
    rate_adjustment: float


@dataclass
class ASARiskReport:
    """Comprehensive ASA risk assessment report"""
    asset_id: int
    asset_name: str
    overall_risk_score: float
    risk_tier: str
    max_ltv: float
    rate_adjustment: float
    components: RiskComponents
    risk_factors: List[str]
    recommendations: List[str]
    analysis_timestamp: datetime
    next_review_date: datetime
    monitoring_alerts: List[str]


@dataclass
class PortfolioRiskAnalysis:
    """Risk analysis for multiple ASAs"""
    asset_ids: List[int]
    individual_assessments: Dict[int, ASARiskReport]
    portfolio_risk_score: float
    correlation_matrix: Dict[int, Dict[int, float]]
    concentration_risk: float
    risk_distribution: Dict[str, int]
    recommendations: List[str]


class ASARiskEngine:
    """Main engine for comprehensive ASA risk assessment"""

    def __init__(self, config_path: str = None, config_dict: Dict = None):
        """Initialize with configuration file or dictionary"""
        if config_dict:
            self.config = config_dict
        else:
            config_path = config_path or "/home/mpo/algorand-showcase/algorand-lending-ecosystem/business-logic-engines/interest-rate-determiner/asa-risk-assessment/config/config.yaml"
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)

        self.logger = logging.getLogger(__name__)

        # Initialize component analyzers
        self.volatility_analyzer = ASAVolatilityAnalyzer(self.config)
        self.liquidity_analyzer = ASALiquidityAnalyzer(self.config)
        self.security_analyzer = SmartContractSecurityAnalyzer(self.config)

        # Risk tiers from config
        self.risk_tiers = self.config['risk_tiers']

    async def assess_asa_risk(self, asset_id: int) -> ASARiskReport:
        """Perform comprehensive risk assessment for an ASA"""
        try:
            self.logger.info(f"Starting risk assessment for ASA {asset_id}")

            # Run parallel analysis
            volatility_analysis, liquidity_analysis, security_analysis = await asyncio.gather(
                self.volatility_analyzer.analyze_asa_volatility(asset_id),
                self.liquidity_analyzer.analyze_asa_liquidity(asset_id),
                self.security_analyzer.analyze_contract_security(asset_id),
                return_exceptions=True
            )

            # Handle analysis errors
            if isinstance(volatility_analysis, Exception):
                self.logger.error(f"Volatility analysis failed: {volatility_analysis}")
                volatility_analysis = self._create_default_volatility_metrics(asset_id)

            if isinstance(liquidity_analysis, Exception):
                self.logger.error(f"Liquidity analysis failed: {liquidity_analysis}")
                liquidity_analysis = self._create_default_liquidity_metrics(asset_id)

            if isinstance(security_analysis, Exception):
                self.logger.error(f"Security analysis failed: {security_analysis}")
                security_analysis = self._create_default_security_metrics(asset_id)

            # Calculate combined risk score
            combined_risk_score = self._calculate_combined_risk_score(
                volatility_analysis, liquidity_analysis, security_analysis
            )

            # Determine risk tier and parameters
            risk_tier, max_ltv, rate_adjustment = self._determine_risk_tier(combined_risk_score)

            # Create risk components
            components = RiskComponents(
                volatility_metrics=volatility_analysis,
                liquidity_metrics=liquidity_analysis,
                security_metrics=security_analysis,
                combined_risk_score=combined_risk_score,
                risk_tier=risk_tier,
                max_ltv=max_ltv,
                rate_adjustment=rate_adjustment
            )

            # Identify risk factors
            risk_factors = self._identify_risk_factors(components)

            # Generate recommendations
            recommendations = self._generate_recommendations(components)

            # Generate monitoring alerts
            monitoring_alerts = self._generate_monitoring_alerts(components)

            # Calculate next review date
            next_review = self._calculate_next_review_date(risk_tier)

            asset_name = (volatility_analysis.asset_name or
                         liquidity_analysis.asset_name or
                         security_analysis.asset_name or
                         f'ASA-{asset_id}')

            return ASARiskReport(
                asset_id=asset_id,
                asset_name=asset_name,
                overall_risk_score=combined_risk_score,
                risk_tier=risk_tier,
                max_ltv=max_ltv,
                rate_adjustment=rate_adjustment,
                components=components,
                risk_factors=risk_factors,
                recommendations=recommendations,
                analysis_timestamp=datetime.utcnow(),
                next_review_date=next_review,
                monitoring_alerts=monitoring_alerts
            )

        except Exception as e:
            self.logger.error(f"Error in risk assessment for ASA {asset_id}: {e}")
            raise

    async def assess_portfolio_risk(self, asset_ids: List[int]) -> PortfolioRiskAnalysis:
        """Assess risk for a portfolio of ASAs"""
        try:
            self.logger.info(f"Analyzing portfolio risk for {len(asset_ids)} ASAs")

            # Assess individual ASAs in parallel (with concurrency limit)
            semaphore = asyncio.Semaphore(10)  # Limit concurrent API calls

            async def assess_with_semaphore(asset_id):
                async with semaphore:
                    return await self.assess_asa_risk(asset_id)

            # Run parallel assessment
            individual_reports = await asyncio.gather(
                *[assess_with_semaphore(asset_id) for asset_id in asset_ids],
                return_exceptions=True
            )

            # Process results
            individual_assessments = {}
            valid_scores = []
            risk_distribution = {tier: 0 for tier in self.risk_tiers.keys()}

            for i, report in enumerate(individual_reports):
                asset_id = asset_ids[i]

                if isinstance(report, Exception):
                    self.logger.error(f"Error assessing ASA {asset_id}: {report}")
                    # Create minimal report for failed assessment
                    report = self._create_default_risk_report(asset_id)

                individual_assessments[asset_id] = report
                valid_scores.append(report.overall_risk_score)
                risk_distribution[report.risk_tier] += 1

            # Calculate portfolio metrics
            portfolio_risk_score = self._calculate_portfolio_risk_score(individual_assessments)

            # Calculate correlation matrix
            correlation_matrix = await self._calculate_correlation_matrix(asset_ids)

            # Calculate concentration risk
            concentration_risk = self._calculate_concentration_risk(individual_assessments, correlation_matrix)

            # Generate portfolio recommendations
            portfolio_recommendations = self._generate_portfolio_recommendations(
                individual_assessments, portfolio_risk_score, concentration_risk, risk_distribution
            )

            return PortfolioRiskAnalysis(
                asset_ids=asset_ids,
                individual_assessments=individual_assessments,
                portfolio_risk_score=portfolio_risk_score,
                correlation_matrix=correlation_matrix,
                concentration_risk=concentration_risk,
                risk_distribution=risk_distribution,
                recommendations=portfolio_recommendations
            )

        except Exception as e:
            self.logger.error(f"Error in portfolio risk assessment: {e}")
            raise

    def _calculate_combined_risk_score(
        self, volatility: VolatilityMetrics, liquidity: LiquidityMetrics, security: SecurityMetrics
    ) -> float:
        """Calculate combined risk score from components"""
        weights = self.config['risk_assessment']['volatility_weights']

        # Convert to risk scores (1 - original score for inverse metrics)
        volatility_risk = volatility.volatility_score  # Already a risk score (higher = riskier)
        liquidity_risk = 1.0 - liquidity.overall_liquidity_score  # Convert to risk
        security_risk = 1.0 - security.overall_security_score  # Convert to risk

        # Weighted combination
        combined_risk = (
            volatility_risk * weights['price_volatility'] +
            liquidity_risk * weights['volume_volatility'] +  # Using as proxy
            security_risk * 0.3  # Security weight
        )

        return min(1.0, max(0.0, combined_risk))

    def _determine_risk_tier(self, risk_score: float) -> Tuple[str, float, float]:
        """Determine risk tier and associated parameters based on score"""
        # Convert risk score to quality score for tier matching
        quality_score = 1.0 - risk_score

        for tier, config in self.risk_tiers.items():
            if quality_score >= config['min_score']:
                return tier, config['max_ltv'], config.get('rate_adjustment', 0.0)

        # Default to worst tier
        worst_tier = list(self.risk_tiers.keys())[-1]
        worst_config = self.risk_tiers[worst_tier]
        return worst_tier, worst_config['max_ltv'], worst_config.get('rate_adjustment', 5.0)

    def _identify_risk_factors(self, components: RiskComponents) -> List[str]:
        """Identify key risk factors from component analysis"""
        risk_factors = []

        # Volatility risk factors
        vol_metrics = components.volatility_metrics
        if vol_metrics.daily_volatility > 0.5:
            risk_factors.append("High price volatility (>50% daily)")

        if vol_metrics.max_drawdown > 0.3:
            risk_factors.append(f"Significant maximum drawdown ({vol_metrics.max_drawdown:.1%})")

        if vol_metrics.volume_volatility > 0.5:
            risk_factors.append("High volume volatility")

        # Liquidity risk factors
        liq_metrics = components.liquidity_metrics
        if liq_metrics.trading_metrics.volume_24h < 10000:
            risk_factors.append("Low trading volume (<$10k daily)")

        if liq_metrics.bid_ask_spread > 0.05:
            risk_factors.append("Wide bid-ask spread (>5%)")

        if liq_metrics.market_depth.total_depth < 5000:
            risk_factors.append("Shallow market depth (<$5k)")

        if len(liq_metrics.pools) == 0:
            risk_factors.append("No liquidity pools found")

        # Security risk factors
        sec_metrics = components.security_metrics
        if sec_metrics.security_flags.clawback_risk:
            risk_factors.append("Clawback capability enabled")

        if sec_metrics.security_flags.freeze_risk:
            risk_factors.append("Freeze capability enabled")

        if sec_metrics.security_flags.unverified_creator:
            risk_factors.append("Unverified asset creator")

        if not sec_metrics.audits:
            risk_factors.append("No security audits found")

        if sec_metrics.security_flags.recent_creation:
            risk_factors.append("Recently created asset")

        return risk_factors

    def _generate_recommendations(self, components: RiskComponents) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        # Based on risk tier
        if components.risk_tier in ['c', 'cc', 'd']:
            recommendations.append("Consider excluding from lending due to high risk")

        elif components.risk_tier in ['b', 'bb', 'bbb']:
            recommendations.append("Implement enhanced monitoring and lower LTV ratios")

        # Volatility-based recommendations
        if components.volatility_metrics.daily_volatility > 0.3:
            recommendations.append("Implement dynamic LTV adjustments based on volatility")

        # Liquidity-based recommendations
        if components.liquidity_metrics.overall_liquidity_score < 0.5:
            recommendations.append("Monitor liquidity closely; consider liquidity requirements")

        if len(components.liquidity_metrics.pools) < 2:
            recommendations.append("Encourage multi-DEX liquidity provision")

        # Security-based recommendations
        if components.security_metrics.security_flags.clawback_risk:
            recommendations.append("Implement additional safeguards due to clawback risk")

        if not components.security_metrics.audits:
            recommendations.append("Require security audit before lending approval")

        if not recommendations:
            recommendations.append("Asset shows acceptable risk profile for lending")

        return recommendations

    def _generate_monitoring_alerts(self, components: RiskComponents) -> List[str]:
        """Generate monitoring alerts for the asset"""
        alerts = []

        # Volatility alerts
        if components.volatility_metrics.daily_volatility > 0.4:
            alerts.append("HIGH_VOLATILITY: Daily volatility exceeds 40%")

        # Liquidity alerts
        if components.liquidity_metrics.trading_metrics.volume_24h < 5000:
            alerts.append("LOW_VOLUME: 24h volume below $5k")

        if components.liquidity_metrics.slippage_5_percent > 0.1:
            alerts.append("HIGH_SLIPPAGE: Expected slippage >10% for large trades")

        # Security alerts
        if components.security_metrics.security_flags.centralized_control:
            alerts.append("CENTRALIZATION_RISK: Asset has centralized control")

        return alerts

    def _calculate_portfolio_risk_score(self, assessments: Dict[int, ASARiskReport]) -> float:
        """Calculate overall portfolio risk score"""
        if not assessments:
            return 1.0

        # Weight by asset exposure (simplified - could use actual exposure amounts)
        total_score = sum(report.overall_risk_score for report in assessments.values())
        return total_score / len(assessments)

    async def _calculate_correlation_matrix(self, asset_ids: List[int]) -> Dict[int, Dict[int, float]]:
        """Calculate correlation matrix between assets"""
        try:
            return await self.volatility_analyzer.analyze_correlation_risk(asset_ids)
        except Exception as e:
            self.logger.error(f"Error calculating correlation matrix: {e}")
            # Return identity matrix as fallback
            return {
                asset_id: {other_id: 1.0 if asset_id == other_id else 0.0
                          for other_id in asset_ids}
                for asset_id in asset_ids
            }

    def _calculate_concentration_risk(
        self, assessments: Dict[int, ASARiskReport], correlation_matrix: Dict[int, Dict[int, float]]
    ) -> float:
        """Calculate concentration risk based on correlations"""
        if len(assessments) <= 1:
            return 1.0  # Maximum concentration risk

        # Calculate average correlation
        correlations = []
        asset_ids = list(assessments.keys())

        for i, asset1 in enumerate(asset_ids):
            for j, asset2 in enumerate(asset_ids[i+1:], i+1):
                corr = correlation_matrix.get(asset1, {}).get(asset2, 0.0)
                correlations.append(abs(corr))

        avg_correlation = sum(correlations) / len(correlations) if correlations else 0.0

        # Higher correlation = higher concentration risk
        return avg_correlation

    def _generate_portfolio_recommendations(
        self, assessments: Dict[int, ASARiskReport], portfolio_risk: float,
        concentration_risk: float, risk_distribution: Dict[str, int]
    ) -> List[str]:
        """Generate portfolio-level recommendations"""
        recommendations = []

        # Portfolio risk level
        if portfolio_risk > 0.7:
            recommendations.append("Portfolio shows high overall risk - consider rebalancing")

        # Concentration risk
        if concentration_risk > 0.7:
            recommendations.append("High correlation between assets - diversify further")

        # Risk distribution analysis
        total_assets = sum(risk_distribution.values())
        high_risk_count = sum(risk_distribution.get(tier, 0) for tier in ['b', 'bb', 'c', 'cc', 'd'])
        high_risk_ratio = high_risk_count / max(total_assets, 1)

        if high_risk_ratio > 0.3:
            recommendations.append(f"Portfolio has {high_risk_ratio:.1%} high-risk assets")

        # Quality distribution
        excellent_count = risk_distribution.get('aaa', 0) + risk_distribution.get('aa', 0)
        if excellent_count > 0:
            recommendations.append(f"{excellent_count} assets rated AA+ - consider preferential terms")

        return recommendations

    def _calculate_next_review_date(self, risk_tier: str) -> datetime:
        """Calculate when next risk review should occur"""
        review_intervals = {
            'aaa': 90,     # 3 months
            'aa': 60,      # 2 months
            'a': 30,       # 1 month
            'bbb': 21,     # 3 weeks
            'bb': 14,      # 2 weeks
            'b': 7,        # 1 week
            'ccc': 3,      # 3 days
            'cc': 1,       # 1 day
            'c': 1,        # 1 day
            'd': 1         # 1 day
        }

        days = review_intervals.get(risk_tier, 7)
        return datetime.utcnow() + timedelta(days=days)

    def _create_default_volatility_metrics(self, asset_id: int) -> VolatilityMetrics:
        """Create default volatility metrics for failed analysis"""
        from .asa_volatility import VolatilityMetrics
        return VolatilityMetrics(
            asset_id=asset_id,
            asset_name=f'ASA-{asset_id}',
            current_price=0.0,
            daily_volatility=1.0,  # Maximum volatility
            weekly_volatility=1.0,
            monthly_volatility=1.0,
            price_range_7d=0.0,
            price_range_30d=0.0,
            max_drawdown=0.0,
            volume_volatility=1.0,
            avg_daily_volume=0.0,
            volume_trend="no_data",
            var_95=0.0,
            sharpe_ratio=0.0,
            volatility_score=1.0  # Maximum risk
        )

    def _create_default_liquidity_metrics(self, asset_id: int) -> LiquidityMetrics:
        """Create default liquidity metrics for failed analysis"""
        from .asa_liquidity import LiquidityMetrics, TradingMetrics, MarketDepth

        default_trading = TradingMetrics(
            volume_24h=0.0, volume_7d=0.0, volume_30d=0.0,
            trade_count_24h=0, avg_trade_size=0.0, largest_trade_24h=0.0,
            volume_trend="no_data"
        )

        default_depth = MarketDepth(
            bid_depth_1_percent=0.0, ask_depth_1_percent=0.0,
            bid_depth_5_percent=0.0, ask_depth_5_percent=0.0,
            total_depth=0.0, depth_imbalance=0.0
        )

        return LiquidityMetrics(
            asset_id=asset_id,
            asset_name=f'ASA-{asset_id}',
            trading_metrics=default_trading,
            market_depth=default_depth,
            pools=[],
            total_pool_liquidity=0.0,
            bid_ask_spread=1.0,  # Wide spread
            average_spread_24h=1.0,
            spread_volatility=1.0,
            active_market_makers=0,
            market_maker_concentration=1.0,
            volume_score=0.0,
            depth_score=0.0,
            spread_score=0.0,
            overall_liquidity_score=0.0,  # Minimum liquidity
            liquidity_risk_level="very_high",
            slippage_1_percent=1.0,
            slippage_5_percent=1.0
        )

    def _create_default_security_metrics(self, asset_id: int) -> SecurityMetrics:
        """Create default security metrics for failed analysis"""
        from .smart_contract_security import (
            SecurityMetrics, TechnicalParameters, SecurityFlags, CreatorAnalysis
        )

        default_params = TechnicalParameters(
            total_supply=0, decimals=6, default_frozen=True,
            freeze_enabled=True, clawback_enabled=True,
            manager_address="unknown", reserve_address=None,
            freeze_address=None, clawback_address=None,
            url=None, metadata_hash=None
        )

        default_flags = SecurityFlags(
            centralized_control=True, unlimited_minting=True,
            freeze_risk=True, clawback_risk=True,
            unverified_creator=True, recent_creation=True,
            suspicious_parameters=True, missing_metadata=True
        )

        default_creator = CreatorAnalysis(
            creator_address="unknown", is_verified=False,
            reputation_score=0.0, previous_assets=[],
            governance_participation=False, community_standing="unknown",
            kyc_status=False, social_presence={}
        )

        return SecurityMetrics(
            asset_id=asset_id,
            asset_name=f'ASA-{asset_id}',
            technical_params=default_params,
            security_flags=default_flags,
            audits=[],
            latest_audit_score=0.0,
            audit_coverage=0.0,
            creator_analysis=default_creator,
            contract_complexity=1.0,
            code_quality_score=0.0,
            upgrade_mechanism="unknown",
            technical_security_score=0.0,
            audit_security_score=0.0,
            creator_security_score=0.0,
            overall_security_score=0.0,  # Minimum security
            security_risk_level="very_high",
            recommendations=["Analysis failed - manual review required"]
        )

    def _create_default_risk_report(self, asset_id: int) -> ASARiskReport:
        """Create default risk report for failed assessment"""
        volatility_metrics = self._create_default_volatility_metrics(asset_id)
        liquidity_metrics = self._create_default_liquidity_metrics(asset_id)
        security_metrics = self._create_default_security_metrics(asset_id)

        components = RiskComponents(
            volatility_metrics=volatility_metrics,
            liquidity_metrics=liquidity_metrics,
            security_metrics=security_metrics,
            combined_risk_score=1.0,  # Maximum risk
            risk_tier='d',
            max_ltv=0.0,
            rate_adjustment=5.0
        )

        return ASARiskReport(
            asset_id=asset_id,
            asset_name=f'ASA-{asset_id}',
            overall_risk_score=1.0,
            risk_tier='d',
            max_ltv=0.0,
            rate_adjustment=5.0,
            components=components,
            risk_factors=["Analysis failed"],
            recommendations=["Manual review required"],
            analysis_timestamp=datetime.utcnow(),
            next_review_date=datetime.utcnow() + timedelta(days=1),
            monitoring_alerts=["ANALYSIS_FAILED"]
        )

    async def get_risk_summary(self, asset_ids: List[int]) -> Dict:
        """Get high-level risk summary for multiple ASAs"""
        try:
            portfolio = await self.assess_portfolio_risk(asset_ids)

            return {
                'total_assets': len(asset_ids),
                'portfolio_risk_score': portfolio.portfolio_risk_score,
                'concentration_risk': portfolio.concentration_risk,
                'risk_distribution': portfolio.risk_distribution,
                'high_risk_assets': sum(portfolio.risk_distribution.get(tier, 0)
                                      for tier in ['b', 'bb', 'c', 'cc', 'd']),
                'investment_grade_assets': sum(portfolio.risk_distribution.get(tier, 0)
                                             for tier in ['aaa', 'aa', 'a', 'bbb']),
                'recommendations_count': len(portfolio.recommendations),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error generating risk summary: {e}")
            return {
                'error': str(e),
                'total_assets': len(asset_ids),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }

    def export_risk_report(self, report: ASARiskReport, format: str = 'json') -> str:
        """Export risk report in specified format"""
        if format == 'json':
            return json.dumps({
                'asset_id': report.asset_id,
                'asset_name': report.asset_name,
                'overall_risk_score': report.overall_risk_score,
                'risk_tier': report.risk_tier,
                'max_ltv': report.max_ltv,
                'rate_adjustment': report.rate_adjustment,
                'risk_factors': report.risk_factors,
                'recommendations': report.recommendations,
                'analysis_timestamp': report.analysis_timestamp.isoformat(),
                'next_review_date': report.next_review_date.isoformat()
            }, indent=2)

        elif format == 'yaml':
            return yaml.dump({
                'asset_id': report.asset_id,
                'asset_name': report.asset_name,
                'overall_risk_score': float(report.overall_risk_score),
                'risk_tier': report.risk_tier,
                'max_ltv': float(report.max_ltv),
                'rate_adjustment': float(report.rate_adjustment),
                'risk_factors': report.risk_factors,
                'recommendations': report.recommendations,
                'analysis_timestamp': report.analysis_timestamp.isoformat()
            })

        else:
            raise ValueError(f"Unsupported format: {format}")