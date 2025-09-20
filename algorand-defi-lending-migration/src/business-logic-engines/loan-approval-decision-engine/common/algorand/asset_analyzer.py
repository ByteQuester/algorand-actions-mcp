"""
Asset Analyzer

Analyzes borrower's asset portfolio and management patterns to assess
financial sophistication, diversification, and risk management capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class AssetHolding:
    """Represents a single asset holding"""
    asset_id: int
    asset_name: str
    asset_type: str  # 'native', 'asa', 'nft', 'stable'
    balance: float
    value_usd: float
    percentage_of_portfolio: float
    holding_period_days: int
    acquisition_method: str  # 'purchase', 'earned', 'airdrop', 'minted'


@dataclass
class PortfolioMetrics:
    """Portfolio analysis metrics"""
    total_value_usd: float
    asset_count: int
    diversification_score: float
    concentration_risk: float
    volatility_score: float
    stable_asset_percentage: float
    native_algo_percentage: float
    exotic_asset_percentage: float
    largest_position_percentage: float


@dataclass
class AssetAnalysisResult:
    """Comprehensive asset analysis results"""
    portfolio_metrics: PortfolioMetrics
    holdings: List[AssetHolding]
    risk_assessment: Dict[str, float]
    sophistication_indicators: Dict[str, Any]
    behavioral_patterns: Dict[str, Any]
    recommendations: List[str]


class AssetAnalyzer:
    """
    Analyzes asset portfolios to understand financial behavior,
    risk management, and investment sophistication.
    """

    def __init__(self):
        self.asset_registry = self._load_asset_registry()
        self.risk_parameters = self._load_risk_parameters()

    async def analyze_asset_portfolio(
        self,
        wallet_address: str,
        analysis_depth: str = "comprehensive"
    ) -> AssetAnalysisResult:
        """
        Analyze complete asset portfolio for risk and sophistication assessment.

        Args:
            wallet_address: Address to analyze
            analysis_depth: Level of analysis ('basic', 'standard', 'comprehensive')

        Returns:
            Comprehensive asset analysis results
        """
        logger.info(f"Analyzing asset portfolio for {wallet_address}")

        try:
            # Fetch current holdings
            current_holdings = await self._fetch_current_holdings(wallet_address)

            if not current_holdings:
                logger.warning(f"No assets found for {wallet_address}")
                return self._create_empty_analysis_result()

            # Fetch historical data if comprehensive analysis
            historical_data = []
            if analysis_depth == "comprehensive":
                historical_data = await self._fetch_historical_holdings(wallet_address)

            # Parallel analysis of different aspects
            tasks = [
                self._analyze_portfolio_composition(current_holdings),
                self._analyze_diversification(current_holdings),
                self._analyze_risk_exposure(current_holdings),
                self._analyze_asset_quality(current_holdings),
                self._analyze_holding_patterns(current_holdings, historical_data),
                self._analyze_asset_acquisition_behavior(historical_data),
                self._detect_portfolio_management_sophistication(current_holdings, historical_data)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Extract analysis results
            composition_analysis = results[0] if not isinstance(results[0], Exception) else {}
            diversification_analysis = results[1] if not isinstance(results[1], Exception) else {}
            risk_analysis = results[2] if not isinstance(results[2], Exception) else {}
            quality_analysis = results[3] if not isinstance(results[3], Exception) else {}
            pattern_analysis = results[4] if not isinstance(results[4], Exception) else {}
            acquisition_analysis = results[5] if not isinstance(results[5], Exception) else {}
            sophistication_analysis = results[6] if not isinstance(results[6], Exception) else {}

            # Compile results
            portfolio_metrics = self._compile_portfolio_metrics(
                composition_analysis, diversification_analysis, risk_analysis
            )

            holdings = self._process_holdings_data(current_holdings, portfolio_metrics.total_value_usd)

            risk_assessment = self._compile_risk_assessment(
                risk_analysis, diversification_analysis, quality_analysis
            )

            sophistication_indicators = self._compile_sophistication_indicators(
                sophistication_analysis, acquisition_analysis, pattern_analysis
            )

            behavioral_patterns = self._compile_behavioral_patterns(
                pattern_analysis, acquisition_analysis
            )

            recommendations = self._generate_recommendations(
                portfolio_metrics, risk_assessment, sophistication_indicators
            )

            return AssetAnalysisResult(
                portfolio_metrics=portfolio_metrics,
                holdings=holdings,
                risk_assessment=risk_assessment,
                sophistication_indicators=sophistication_indicators,
                behavioral_patterns=behavioral_patterns,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Asset analysis failed for {wallet_address}: {e}")
            raise

    async def _fetch_current_holdings(self, address: str) -> List[Dict[str, Any]]:
        """Fetch current asset holdings from Algorand indexer"""
        # Mock implementation - would integrate with Algorand indexer API
        return [
            {
                'asset_id': 0,  # ALGO
                'asset_name': 'Algorand',
                'balance': 15642.5,
                'decimals': 6,
                'creator': 'algorand',
                'unit_name': 'ALGO',
                'asset_type': 'native',
                'verified': True,
                'price_usd': 0.25
            },
            {
                'asset_id': 31566704,  # USDC
                'asset_name': 'USD Coin',
                'balance': 5000.0,
                'decimals': 6,
                'creator': 'centre',
                'unit_name': 'USDC',
                'asset_type': 'stable',
                'verified': True,
                'price_usd': 1.0
            },
            {
                'asset_id': 386192725,  # goBTC
                'asset_name': 'Wrapped Bitcoin',
                'balance': 0.5,
                'decimals': 8,
                'creator': 'algorand',
                'unit_name': 'goBTC',
                'asset_type': 'wrapped',
                'verified': True,
                'price_usd': 45000.0
            },
            {
                'asset_id': 444108880,  # Tinyman Token
                'asset_name': 'Tinyman Pool Token',
                'balance': 1000.0,
                'decimals': 6,
                'creator': 'tinyman',
                'unit_name': 'TMPOOL1',
                'asset_type': 'lp_token',
                'verified': True,
                'price_usd': 2.5
            },
            {
                'asset_id': 123456789,  # Some random ASA
                'asset_name': 'Random Token',
                'balance': 10000.0,
                'decimals': 6,
                'creator': 'unknown',
                'unit_name': 'RAND',
                'asset_type': 'asa',
                'verified': False,
                'price_usd': 0.01
            }
        ]

    async def _fetch_historical_holdings(self, address: str) -> List[Dict[str, Any]]:
        """Fetch historical holdings data for pattern analysis"""
        # Mock implementation - would fetch historical snapshots
        return [
            {
                'timestamp': datetime.utcnow() - timedelta(days=30),
                'holdings': [
                    {'asset_id': 0, 'balance': 12000.0, 'value_usd': 3000.0},
                    {'asset_id': 31566704, 'balance': 3000.0, 'value_usd': 3000.0}
                ]
            },
            {
                'timestamp': datetime.utcnow() - timedelta(days=60),
                'holdings': [
                    {'asset_id': 0, 'balance': 8000.0, 'value_usd': 2000.0},
                    {'asset_id': 31566704, 'balance': 2000.0, 'value_usd': 2000.0}
                ]
            }
        ]

    async def _analyze_portfolio_composition(self, holdings: List[Dict]) -> Dict[str, Any]:
        """Analyze basic portfolio composition"""
        total_value = sum(holding['balance'] * holding['price_usd'] for holding in holdings)

        composition = {
            'total_value_usd': total_value,
            'asset_count': len(holdings),
            'native_algo_value': 0.0,
            'stable_asset_value': 0.0,
            'exotic_asset_value': 0.0,
            'verified_asset_value': 0.0
        }

        for holding in holdings:
            value = holding['balance'] * holding['price_usd']

            if holding['asset_type'] == 'native':
                composition['native_algo_value'] += value
            elif holding['asset_type'] == 'stable':
                composition['stable_asset_value'] += value
            elif holding['asset_type'] in ['asa', 'wrapped']:
                if not holding.get('verified', False):
                    composition['exotic_asset_value'] += value

            if holding.get('verified', False):
                composition['verified_asset_value'] += value

        # Calculate percentages
        if total_value > 0:
            composition['native_algo_percentage'] = composition['native_algo_value'] / total_value
            composition['stable_asset_percentage'] = composition['stable_asset_value'] / total_value
            composition['exotic_asset_percentage'] = composition['exotic_asset_value'] / total_value
            composition['verified_percentage'] = composition['verified_asset_value'] / total_value

        return composition

    async def _analyze_diversification(self, holdings: List[Dict]) -> Dict[str, Any]:
        """Analyze portfolio diversification"""
        if not holdings:
            return {}

        total_value = sum(holding['balance'] * holding['price_usd'] for holding in holdings)

        # Calculate position sizes
        position_sizes = [holding['balance'] * holding['price_usd'] / total_value for holding in holdings if total_value > 0]

        # Herfindahl-Hirschman Index for concentration
        hhi = sum(size ** 2 for size in position_sizes)

        # Diversification score (inverse of concentration)
        diversification_score = (1 - hhi) if len(holdings) > 1 else 0

        # Largest position percentage
        largest_position = max(position_sizes) if position_sizes else 0

        # Asset type diversity
        asset_types = set(holding['asset_type'] for holding in holdings)
        type_diversity_score = len(asset_types) / 5.0  # Normalize by max expected types

        return {
            'diversification_score': diversification_score,
            'concentration_risk': hhi,
            'largest_position_percentage': largest_position,
            'asset_type_count': len(asset_types),
            'type_diversity_score': type_diversity_score,
            'position_sizes': position_sizes
        }

    async def _analyze_risk_exposure(self, holdings: List[Dict]) -> Dict[str, Any]:
        """Analyze risk exposure of the portfolio"""
        risk_metrics = {
            'high_volatility_exposure': 0.0,
            'unverified_asset_exposure': 0.0,
            'single_creator_risk': 0.0,
            'liquidity_risk': 0.0,
            'counterparty_risk': 0.0
        }

        total_value = sum(holding['balance'] * holding['price_usd'] for holding in holdings)

        if total_value == 0:
            return risk_metrics

        # High volatility assets (non-stable, non-native)
        volatile_value = sum(
            holding['balance'] * holding['price_usd']
            for holding in holdings
            if holding['asset_type'] not in ['stable', 'native']
        )
        risk_metrics['high_volatility_exposure'] = volatile_value / total_value

        # Unverified assets
        unverified_value = sum(
            holding['balance'] * holding['price_usd']
            for holding in holdings
            if not holding.get('verified', False)
        )
        risk_metrics['unverified_asset_exposure'] = unverified_value / total_value

        # Single creator concentration
        creator_values = defaultdict(float)
        for holding in holdings:
            creator = holding.get('creator', 'unknown')
            creator_values[creator] += holding['balance'] * holding['price_usd']

        max_creator_exposure = max(creator_values.values()) / total_value if creator_values else 0
        risk_metrics['single_creator_risk'] = max_creator_exposure

        # Liquidity risk (small assets, LP tokens)
        illiquid_types = ['lp_token', 'nft']
        illiquid_value = sum(
            holding['balance'] * holding['price_usd']
            for holding in holdings
            if holding['asset_type'] in illiquid_types
        )
        risk_metrics['liquidity_risk'] = illiquid_value / total_value

        # Calculate overall risk score
        risk_metrics['overall_risk_score'] = (
            risk_metrics['high_volatility_exposure'] * 0.3 +
            risk_metrics['unverified_asset_exposure'] * 0.4 +
            risk_metrics['single_creator_risk'] * 0.2 +
            risk_metrics['liquidity_risk'] * 0.1
        ) * 100

        return risk_metrics

    async def _analyze_asset_quality(self, holdings: List[Dict]) -> Dict[str, Any]:
        """Analyze quality of assets in portfolio"""
        quality_metrics = {
            'verified_asset_ratio': 0.0,
            'established_asset_ratio': 0.0,
            'blue_chip_ratio': 0.0,
            'quality_score': 0.0
        }

        if not holdings:
            return quality_metrics

        total_count = len(holdings)
        total_value = sum(holding['balance'] * holding['price_usd'] for holding in holdings)

        # Verified assets
        verified_count = sum(1 for holding in holdings if holding.get('verified', False))
        quality_metrics['verified_asset_ratio'] = verified_count / total_count

        # Established assets (in our registry)
        established_assets = set(self.asset_registry.get('established', []))
        established_count = sum(
            1 for holding in holdings
            if holding['asset_id'] in established_assets
        )
        quality_metrics['established_asset_ratio'] = established_count / total_count

        # Blue chip assets
        blue_chip_assets = set(self.asset_registry.get('blue_chip', []))
        blue_chip_value = sum(
            holding['balance'] * holding['price_usd']
            for holding in holdings
            if holding['asset_id'] in blue_chip_assets
        )
        quality_metrics['blue_chip_ratio'] = blue_chip_value / total_value if total_value > 0 else 0

        # Overall quality score
        quality_metrics['quality_score'] = (
            quality_metrics['verified_asset_ratio'] * 0.3 +
            quality_metrics['established_asset_ratio'] * 0.4 +
            quality_metrics['blue_chip_ratio'] * 0.3
        ) * 100

        return quality_metrics

    async def _analyze_holding_patterns(
        self,
        current_holdings: List[Dict],
        historical_data: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze holding patterns and portfolio management behavior"""
        patterns = {
            'avg_holding_period': 0.0,
            'portfolio_turnover': 0.0,
            'rebalancing_frequency': 0.0,
            'growth_pattern': 'unknown',
            'stability_score': 0.0
        }

        if not historical_data or len(historical_data) < 2:
            return patterns

        # Calculate portfolio changes over time
        portfolio_values = []
        asset_counts = []

        for snapshot in historical_data:
            total_value = sum(h['value_usd'] for h in snapshot['holdings'])
            asset_count = len(snapshot['holdings'])
            portfolio_values.append(total_value)
            asset_counts.append(asset_count)

        if portfolio_values:
            # Growth pattern analysis
            if len(portfolio_values) >= 2:
                recent_growth = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0] if portfolio_values[0] > 0 else 0
                if recent_growth > 0.2:
                    patterns['growth_pattern'] = 'growing'
                elif recent_growth < -0.2:
                    patterns['growth_pattern'] = 'declining'
                else:
                    patterns['growth_pattern'] = 'stable'

            # Stability score (inverse of volatility)
            if len(portfolio_values) > 2:
                value_volatility = statistics.stdev(portfolio_values) / statistics.mean(portfolio_values) if statistics.mean(portfolio_values) > 0 else 1
                patterns['stability_score'] = max(0, 1 - value_volatility) * 100

            # Portfolio turnover (asset count changes)
            if len(asset_counts) > 1:
                turnover_events = sum(1 for i in range(1, len(asset_counts)) if asset_counts[i] != asset_counts[i-1])
                patterns['portfolio_turnover'] = turnover_events / len(asset_counts)

        return patterns

    async def _analyze_asset_acquisition_behavior(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze how assets are acquired and managed"""
        acquisition_behavior = {
            'acquisition_pattern': 'unknown',
            'dca_behavior': False,
            'opportunistic_buying': False,
            'panic_selling_tendency': False,
            'diamond_hands_score': 0.0
        }

        # Mock analysis - would analyze actual acquisition transactions
        if historical_data:
            acquisition_behavior.update({
                'acquisition_pattern': 'gradual_accumulation',
                'dca_behavior': True,
                'opportunistic_buying': False,
                'panic_selling_tendency': False,
                'diamond_hands_score': 75.0
            })

        return acquisition_behavior

    async def _detect_portfolio_management_sophistication(
        self,
        current_holdings: List[Dict],
        historical_data: List[Dict]
    ) -> Dict[str, Any]:
        """Detect sophisticated portfolio management behaviors"""
        sophistication = {
            'rebalancing_behavior': False,
            'risk_management_score': 0.0,
            'diversification_maintenance': False,
            'yield_optimization': False,
            'tax_efficiency_indicators': False
        }

        # Diversification maintenance
        total_value = sum(holding['balance'] * holding['price_usd'] for holding in current_holdings)
        if total_value > 0:
            largest_position = max(holding['balance'] * holding['price_usd'] / total_value for holding in current_holdings)
            if largest_position < 0.5:  # No position > 50%
                sophistication['diversification_maintenance'] = True

        # Risk management (stable assets + diversification)
        stable_ratio = sum(
            holding['balance'] * holding['price_usd']
            for holding in current_holdings
            if holding['asset_type'] == 'stable'
        ) / total_value if total_value > 0 else 0

        diversification_score = (1 - largest_position) if total_value > 0 else 0
        sophistication['risk_management_score'] = (stable_ratio * 0.4 + diversification_score * 0.6) * 100

        # Yield optimization (LP tokens, staking)
        yield_assets = sum(
            1 for holding in current_holdings
            if holding['asset_type'] in ['lp_token', 'staking_token']
        )
        sophistication['yield_optimization'] = yield_assets > 0

        return sophistication

    def _compile_portfolio_metrics(
        self,
        composition: Dict,
        diversification: Dict,
        risk: Dict
    ) -> PortfolioMetrics:
        """Compile portfolio metrics into structured format"""
        return PortfolioMetrics(
            total_value_usd=composition.get('total_value_usd', 0.0),
            asset_count=composition.get('asset_count', 0),
            diversification_score=diversification.get('diversification_score', 0.0),
            concentration_risk=diversification.get('concentration_risk', 1.0),
            volatility_score=risk.get('high_volatility_exposure', 0.0),
            stable_asset_percentage=composition.get('stable_asset_percentage', 0.0),
            native_algo_percentage=composition.get('native_algo_percentage', 0.0),
            exotic_asset_percentage=composition.get('exotic_asset_percentage', 0.0),
            largest_position_percentage=diversification.get('largest_position_percentage', 0.0)
        )

    def _process_holdings_data(self, holdings_data: List[Dict], total_value: float) -> List[AssetHolding]:
        """Process raw holdings data into structured format"""
        holdings = []

        for holding_data in holdings_data:
            value_usd = holding_data['balance'] * holding_data['price_usd']
            percentage = (value_usd / total_value * 100) if total_value > 0 else 0

            holding = AssetHolding(
                asset_id=holding_data['asset_id'],
                asset_name=holding_data['asset_name'],
                asset_type=holding_data['asset_type'],
                balance=holding_data['balance'],
                value_usd=value_usd,
                percentage_of_portfolio=percentage,
                holding_period_days=30,  # Mock data
                acquisition_method='purchase'  # Mock data
            )
            holdings.append(holding)

        return sorted(holdings, key=lambda x: x.value_usd, reverse=True)

    def _compile_risk_assessment(
        self,
        risk_analysis: Dict,
        diversification_analysis: Dict,
        quality_analysis: Dict
    ) -> Dict[str, float]:
        """Compile comprehensive risk assessment"""
        return {
            'concentration_risk': diversification_analysis.get('concentration_risk', 0.5) * 100,
            'volatility_risk': risk_analysis.get('high_volatility_exposure', 0.0) * 100,
            'liquidity_risk': risk_analysis.get('liquidity_risk', 0.0) * 100,
            'counterparty_risk': risk_analysis.get('single_creator_risk', 0.0) * 100,
            'quality_risk': 100 - quality_analysis.get('quality_score', 50.0),
            'overall_risk': risk_analysis.get('overall_risk_score', 50.0)
        }

    def _compile_sophistication_indicators(
        self,
        sophistication_analysis: Dict,
        acquisition_analysis: Dict,
        pattern_analysis: Dict
    ) -> Dict[str, Any]:
        """Compile sophistication indicators"""
        return {
            'portfolio_management_score': sophistication_analysis.get('risk_management_score', 50.0),
            'yield_optimization': sophistication_analysis.get('yield_optimization', False),
            'rebalancing_behavior': sophistication_analysis.get('rebalancing_behavior', False),
            'dca_behavior': acquisition_analysis.get('dca_behavior', False),
            'diamond_hands_score': acquisition_analysis.get('diamond_hands_score', 50.0),
            'diversification_maintenance': sophistication_analysis.get('diversification_maintenance', False)
        }

    def _compile_behavioral_patterns(
        self,
        pattern_analysis: Dict,
        acquisition_analysis: Dict
    ) -> Dict[str, Any]:
        """Compile behavioral patterns"""
        return {
            'holding_pattern': pattern_analysis.get('growth_pattern', 'unknown'),
            'acquisition_pattern': acquisition_analysis.get('acquisition_pattern', 'unknown'),
            'stability_score': pattern_analysis.get('stability_score', 50.0),
            'turnover_frequency': pattern_analysis.get('portfolio_turnover', 0.0),
            'panic_selling_tendency': acquisition_analysis.get('panic_selling_tendency', False)
        }

    def _generate_recommendations(
        self,
        portfolio_metrics: PortfolioMetrics,
        risk_assessment: Dict[str, float],
        sophistication_indicators: Dict[str, Any]
    ) -> List[str]:
        """Generate portfolio improvement recommendations"""
        recommendations = []

        # Concentration risk
        if portfolio_metrics.largest_position_percentage > 0.5:
            recommendations.append("Consider reducing largest position to improve diversification")

        # Lack of stable assets
        if portfolio_metrics.stable_asset_percentage < 0.2:
            recommendations.append("Consider increasing stable asset allocation for risk management")

        # Too much in unverified/exotic assets
        if portfolio_metrics.exotic_asset_percentage > 0.3:
            recommendations.append("High exposure to unverified assets - consider rebalancing")

        # Low diversification
        if portfolio_metrics.diversification_score < 0.5:
            recommendations.append("Portfolio lacks diversification - consider adding more asset types")

        # High volatility exposure
        if risk_assessment.get('volatility_risk', 0) > 70:
            recommendations.append("High volatility exposure - consider defensive positioning")

        # Lack of yield optimization
        if not sophistication_indicators.get('yield_optimization', False) and portfolio_metrics.total_value_usd > 10000:
            recommendations.append("Consider yield-generating strategies for idle assets")

        return recommendations

    def _create_empty_analysis_result(self) -> AssetAnalysisResult:
        """Create empty analysis result for addresses with no assets"""
        empty_metrics = PortfolioMetrics(
            total_value_usd=0.0,
            asset_count=0,
            diversification_score=0.0,
            concentration_risk=1.0,
            volatility_score=0.0,
            stable_asset_percentage=0.0,
            native_algo_percentage=0.0,
            exotic_asset_percentage=0.0,
            largest_position_percentage=0.0
        )

        return AssetAnalysisResult(
            portfolio_metrics=empty_metrics,
            holdings=[],
            risk_assessment={'overall_risk': 100.0},
            sophistication_indicators={},
            behavioral_patterns={},
            recommendations=['No assets found - unable to assess portfolio']
        )

    def _load_asset_registry(self) -> Dict[str, List[int]]:
        """Load registry of known asset categories"""
        return {
            'blue_chip': [0, 31566704, 386192725],  # ALGO, USDC, goBTC
            'established': [0, 31566704, 386192725, 444108880],  # Add Tinyman
            'stablecoins': [31566704, 465865291],  # USDC, USDT
            'defi_tokens': [444108880, 511484048],  # Tinyman, Algofi
            'high_risk': [123456789]  # Random/unverified tokens
        }

    def _load_risk_parameters(self) -> Dict[str, float]:
        """Load risk assessment parameters"""
        return {
            'max_single_position': 0.4,  # 40% max in single asset
            'min_stable_allocation': 0.1,  # 10% minimum in stablecoins
            'max_unverified_exposure': 0.1,  # 10% max in unverified assets
            'min_diversification_score': 0.3,  # Minimum diversification
            'volatility_risk_threshold': 0.6  # 60% max in volatile assets
        }