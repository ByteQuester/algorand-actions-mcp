"""
Collateral Adjustment Engine

Main engine interface for collateral-based interest rate determination.
Integrates with blockchain collateral analyzer and provides comprehensive
rate adjustment capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from .config import CollateralAdjustmentConfig, load_config
from .constants import CollateralAdjustmentConstants
from .calculator import (
    CollateralRateCalculator, CollateralAsset, CollateralPortfolio,
    RateAdjustmentResult
)
from .monitor import CollateralMonitor, CollateralAlert, MonitoringPosition


class CollateralAdjustmentEngine:
    """
    Main engine for collateral-based interest rate adjustments

    Provides comprehensive collateral analysis, real-time monitoring,
    and sophisticated rate adjustment calculations for Algorand lending platforms.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the collateral adjustment engine"""
        self.config = load_config(config_path)
        self.constants = CollateralAdjustmentConstants(config_path)
        self.calculator = CollateralRateCalculator(self.config)
        self.monitor = CollateralMonitor(self.config)

        self.logger = logging.getLogger(__name__)
        self._initialized = False
        self._integration_clients = {}

    async def initialize(self) -> None:
        """Initialize the engine and its components"""
        if self._initialized:
            return

        self.logger.info("Initializing Collateral Adjustment Engine")

        # Initialize integrations
        await self._initialize_integrations()

        # Start monitoring service if enabled
        if self.config.monitoring.price_update_interval > 0:
            await self.monitor.start_monitoring()

        # Register alert callbacks
        self.monitor.add_alert_callback(self._handle_alert)

        self._initialized = True
        self.logger.info("Collateral Adjustment Engine initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown the engine and cleanup resources"""
        self.logger.info("Shutting down Collateral Adjustment Engine")

        # Stop monitoring
        await self.monitor.stop_monitoring()

        # Cleanup integrations
        await self._cleanup_integrations()

        self._initialized = False

    async def calculate_rate_adjustment(
        self,
        base_rate: float,
        collateral_assets: List[Dict[str, Any]],
        loan_amount_usd: float,
        loan_duration_days: int = 30,
        portfolio_id: Optional[str] = None,
        enable_monitoring: bool = True
    ) -> RateAdjustmentResult:
        """
        Calculate interest rate adjustment based on collateral

        Args:
            base_rate: Base interest rate before adjustments
            collateral_assets: List of collateral asset information
            loan_amount_usd: Loan amount in USD
            loan_duration_days: Loan duration in days
            portfolio_id: Optional portfolio identifier for monitoring
            enable_monitoring: Whether to enable real-time monitoring

        Returns:
            RateAdjustmentResult: Comprehensive adjustment result
        """
        if not self._initialized:
            await self.initialize()

        # Convert asset data to CollateralAsset objects
        assets = await self._create_collateral_assets(collateral_assets)

        # Create portfolio
        portfolio = await self._create_collateral_portfolio(assets, loan_amount_usd)

        # Get current market conditions
        market_conditions = await self._get_market_conditions()

        # Calculate rate adjustment
        result = await self.calculator.calculate_adjusted_rate(
            base_rate=base_rate,
            portfolio=portfolio,
            loan_duration_days=loan_duration_days,
            market_conditions=market_conditions
        )

        # Add to monitoring if requested
        if enable_monitoring and portfolio_id:
            self.monitor.add_position(portfolio_id, portfolio, base_rate)

        self.logger.info(
            f"Calculated rate adjustment: {result.total_adjustment:+.4f} "
            f"(final rate: {result.final_rate:.4f})"
        )

        return result

    async def get_asset_valuation(
        self,
        asset_symbol: str,
        amount: float,
        include_risk_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive asset valuation with risk metrics

        Args:
            asset_symbol: Asset symbol (e.g., 'ALGO', 'USDC')
            amount: Amount of the asset
            include_risk_metrics: Whether to include detailed risk metrics

        Returns:
            Dict containing valuation and risk information
        """
        try:
            # Get asset price and metadata
            asset_data = await self._get_asset_data(asset_symbol)

            current_price = asset_data.get('price', 0.0)
            total_value = amount * current_price

            result = {
                'symbol': asset_symbol,
                'amount': amount,
                'current_price': current_price,
                'total_value_usd': total_value,
                'price_change_24h': asset_data.get('price_change_24h', 0.0),
                'market_cap': asset_data.get('market_cap', 0.0),
                'daily_volume': asset_data.get('daily_volume', 0.0),
                'last_updated': datetime.now().isoformat()
            }

            if include_risk_metrics:
                # Add risk metrics
                risk_metrics = await self._calculate_asset_risk_metrics(asset_symbol, asset_data)
                result.update(risk_metrics)

            return result

        except Exception as e:
            self.logger.error(f"Error getting asset valuation for {asset_symbol}: {e}")
            raise

    async def analyze_portfolio_risk(
        self,
        collateral_assets: List[Dict[str, Any]],
        loan_amount_usd: float
    ) -> Dict[str, Any]:
        """
        Analyze comprehensive portfolio risk metrics

        Args:
            collateral_assets: List of collateral asset information
            loan_amount_usd: Loan amount in USD

        Returns:
            Dict containing detailed risk analysis
        """
        try:
            # Create portfolio
            assets = await self._create_collateral_assets(collateral_assets)
            portfolio = await self._create_collateral_portfolio(assets, loan_amount_usd)

            # Calculate risk metrics
            risk_analysis = {
                'portfolio_summary': {
                    'total_assets': len(portfolio.assets),
                    'total_value_usd': portfolio.total_value_usd,
                    'loan_amount_usd': portfolio.loan_amount_usd,
                    'current_ltv': portfolio.current_ltv,
                    'diversification_score': portfolio.diversification_score
                },
                'asset_breakdown': [],
                'risk_factors': {},
                'recommendations': [],
                'liquidation_scenarios': {}
            }

            # Analyze each asset
            for asset in portfolio.assets:
                asset_analysis = {
                    'symbol': asset.symbol,
                    'value_usd': asset.amount * asset.current_price,
                    'portfolio_weight': (asset.amount * asset.current_price) / portfolio.total_value_usd,
                    'volatility_30d': asset.volatility_30d,
                    'liquidity_score': asset.liquidity_score,
                    'security_rating': asset.security_rating,
                    'asset_tier': asset.asset_tier.value,
                    'risk_premium': self.calculator._get_asset_risk_premium(asset)
                }
                risk_analysis['asset_breakdown'].append(asset_analysis)

            # Calculate portfolio-level risks
            risk_analysis['risk_factors'] = await self._analyze_portfolio_risks(portfolio)

            # Generate liquidation scenarios
            risk_analysis['liquidation_scenarios'] = await self._analyze_liquidation_scenarios(portfolio)

            # Generate recommendations
            risk_analysis['recommendations'] = await self._generate_risk_recommendations(portfolio, risk_analysis['risk_factors'])

            return risk_analysis

        except Exception as e:
            self.logger.error(f"Error analyzing portfolio risk: {e}")
            raise

    async def get_monitoring_status(self, portfolio_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get monitoring status for portfolios

        Args:
            portfolio_id: Specific portfolio ID or None for all portfolios

        Returns:
            Dict containing monitoring status information
        """
        if portfolio_id:
            return self.monitor.get_position_status(portfolio_id)
        else:
            return self.monitor.get_all_positions_status()

    async def update_market_conditions(self, conditions: Dict[str, Any]) -> None:
        """
        Update market conditions for rate calculations

        Args:
            conditions: Market condition flags and values
        """
        # This would integrate with external market data sources
        # For now, we'll store the conditions for use in calculations
        self._market_conditions = {
            **conditions,
            'last_update': datetime.now()
        }

        self.logger.info(f"Updated market conditions: {conditions}")

    async def _initialize_integrations(self) -> None:
        """Initialize external integrations"""
        try:
            # Initialize blockchain collateral analyzer integration
            if self.config.integration.collateral_analyzer_enabled:
                await self._initialize_collateral_analyzer()

            # Initialize MCP services integration
            if self.config.integration.mcp_services_enabled:
                await self._initialize_mcp_services()

            self.logger.info("Integrations initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing integrations: {e}")

    async def _initialize_collateral_analyzer(self) -> None:
        """Initialize blockchain collateral analyzer integration"""
        # This would establish connection to the blockchain collateral analyzer
        self.logger.info("Initializing blockchain collateral analyzer integration")

    async def _initialize_mcp_services(self) -> None:
        """Initialize MCP services integration"""
        # This would establish connections to MCP services
        self.logger.info("Initializing MCP services integration")

    async def _cleanup_integrations(self) -> None:
        """Cleanup integration resources"""
        self.logger.info("Cleaning up integrations")

    async def _create_collateral_assets(self, asset_data: List[Dict[str, Any]]) -> List[CollateralAsset]:
        """Create CollateralAsset objects from input data"""
        assets = []

        for data in asset_data:
            symbol = data['symbol']
            amount = data['amount']

            # Get additional asset information
            asset_info = await self._get_asset_data(symbol)

            # Determine asset tier
            asset_tier = self.constants.get_collateral_tier(symbol, asset_info)

            asset = CollateralAsset(
                symbol=symbol,
                amount=amount,
                current_price=asset_info.get('price', data.get('price', 0.0)),
                market_cap=asset_info.get('market_cap', 0.0),
                daily_volume=asset_info.get('daily_volume', 0.0),
                volatility_24h=asset_info.get('volatility_24h', 0.0),
                volatility_30d=asset_info.get('volatility_30d', 0.0),
                liquidity_score=asset_info.get('liquidity_score', 0.5),
                security_rating=asset_info.get('security_rating', 'UNRATED'),
                asset_tier=asset_tier,
                metadata=asset_info.get('metadata', {})
            )
            assets.append(asset)

        return assets

    async def _create_collateral_portfolio(
        self,
        assets: List[CollateralAsset],
        loan_amount_usd: float
    ) -> CollateralPortfolio:
        """Create CollateralPortfolio from assets"""
        total_value = sum(asset.amount * asset.current_price for asset in assets)
        current_ltv = loan_amount_usd / total_value if total_value > 0 else 1.0

        # Calculate diversification score
        diversification_score = self._calculate_diversification_score(assets)

        return CollateralPortfolio(
            assets=assets,
            total_value_usd=total_value,
            loan_amount_usd=loan_amount_usd,
            current_ltv=current_ltv,
            diversification_score=diversification_score
        )

    def _calculate_diversification_score(self, assets: List[CollateralAsset]) -> float:
        """Calculate portfolio diversification score (0-1)"""
        if len(assets) <= 1:
            return 0.0

        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        total_value = sum(asset.amount * asset.current_price for asset in assets)
        if total_value == 0:
            return 0.0

        hhi = sum(((asset.amount * asset.current_price) / total_value) ** 2 for asset in assets)

        # Convert HHI to diversification score (inverse relationship)
        # HHI ranges from 1/n to 1, where n is number of assets
        # We want diversification score to range from 0 to 1
        max_hhi = 1.0
        min_hhi = 1.0 / len(assets)
        diversification_score = (max_hhi - hhi) / (max_hhi - min_hhi)

        return min(1.0, max(0.0, diversification_score))

    async def _get_asset_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive asset data"""
        # This would integrate with MCP services, APIs, or cached data
        # For now, we'll return mock data based on symbol

        mock_data = {
            'ALGO': {
                'price': 0.25,
                'market_cap': 2_000_000_000,
                'daily_volume': 50_000_000,
                'volatility_24h': 0.05,
                'volatility_30d': 0.15,
                'liquidity_score': 0.9,
                'security_rating': 'AAA',
                'verified': True
            },
            'USDC': {
                'price': 1.00,
                'market_cap': 25_000_000_000,
                'daily_volume': 2_000_000_000,
                'volatility_24h': 0.001,
                'volatility_30d': 0.003,
                'liquidity_score': 0.95,
                'security_rating': 'AAA',
                'verified': True
            },
            'USDT': {
                'price': 1.00,
                'market_cap': 80_000_000_000,
                'daily_volume': 20_000_000_000,
                'volatility_24h': 0.002,
                'volatility_30d': 0.005,
                'liquidity_score': 0.98,
                'security_rating': 'AA',
                'verified': True
            }
        }

        return mock_data.get(symbol, {
            'price': 1.0,
            'market_cap': 1_000_000,
            'daily_volume': 100_000,
            'volatility_24h': 0.1,
            'volatility_30d': 0.3,
            'liquidity_score': 0.3,
            'security_rating': 'UNRATED',
            'verified': False
        })

    async def _calculate_asset_risk_metrics(self, symbol: str, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed risk metrics for an asset"""
        return {
            'volatility_risk': 'high' if asset_data.get('volatility_30d', 0) > 0.3 else 'medium' if asset_data.get('volatility_30d', 0) > 0.1 else 'low',
            'liquidity_risk': 'high' if asset_data.get('liquidity_score', 0) < 0.3 else 'medium' if asset_data.get('liquidity_score', 0) < 0.7 else 'low',
            'security_risk': 'high' if asset_data.get('security_rating') in ['B', 'UNRATED'] else 'medium' if asset_data.get('security_rating') in ['BBB', 'BB'] else 'low',
            'market_cap_risk': 'high' if asset_data.get('market_cap', 0) < 10_000_000 else 'medium' if asset_data.get('market_cap', 0) < 100_000_000 else 'low',
            'volume_risk': 'high' if asset_data.get('daily_volume', 0) < 100_000 else 'medium' if asset_data.get('daily_volume', 0) < 1_000_000 else 'low'
        }

    async def _get_market_conditions(self) -> Dict[str, Any]:
        """Get current market conditions"""
        return getattr(self, '_market_conditions', {
            'market_stress': False,
            'liquidity_crisis': False,
            'protocol_exploit': False,
            'regulatory_uncertainty': False
        })

    async def _analyze_portfolio_risks(self, portfolio: CollateralPortfolio) -> Dict[str, Any]:
        """Analyze portfolio-level risks"""
        risks = {}

        # LTV risk
        if portfolio.current_ltv > 0.8:
            risks['high_ltv'] = {
                'level': 'critical' if portfolio.current_ltv > 0.9 else 'high',
                'value': portfolio.current_ltv,
                'description': f'LTV of {portfolio.current_ltv:.1%} is above safe thresholds'
            }

        # Concentration risk
        if len(portfolio.assets) == 1:
            risks['concentration'] = {
                'level': 'high',
                'description': 'Portfolio is concentrated in a single asset'
            }
        elif portfolio.diversification_score < 0.3:
            risks['concentration'] = {
                'level': 'medium',
                'description': 'Portfolio has low diversification'
            }

        # Volatility risk
        avg_volatility = sum(asset.volatility_30d for asset in portfolio.assets) / len(portfolio.assets)
        if avg_volatility > 0.5:
            risks['high_volatility'] = {
                'level': 'high',
                'value': avg_volatility,
                'description': f'High average volatility of {avg_volatility:.1%}'
            }

        return risks

    async def _analyze_liquidation_scenarios(self, portfolio: CollateralPortfolio) -> Dict[str, Any]:
        """Analyze liquidation scenarios"""
        scenarios = {}

        # Calculate liquidation prices for different scenarios
        for scenario_name, price_drop in [('mild_stress', 0.1), ('moderate_stress', 0.3), ('severe_stress', 0.5)]:
            liquidation_ltv = self.constants.MONITORING_THRESHOLDS['ltv_liquidation']

            # Calculate how much total portfolio value can drop before liquidation
            current_value = portfolio.total_value_usd
            liquidation_value = portfolio.loan_amount_usd / liquidation_ltv
            max_drop = (current_value - liquidation_value) / current_value

            scenarios[scenario_name] = {
                'price_drop': price_drop,
                'liquidation_triggered': price_drop > max_drop,
                'max_sustainable_drop': max_drop,
                'time_to_liquidation': 'immediate' if price_drop > max_drop else 'safe'
            }

        return scenarios

    async def _generate_risk_recommendations(
        self,
        portfolio: CollateralPortfolio,
        risk_factors: Dict[str, Any]
    ) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        if 'high_ltv' in risk_factors:
            recommendations.append("Reduce LTV by adding more collateral or paying down loan")

        if 'concentration' in risk_factors:
            recommendations.append("Diversify portfolio by adding different asset types")

        if 'high_volatility' in risk_factors:
            recommendations.append("Add stable assets (USDC, USDT) to reduce portfolio volatility")

        low_liquidity_assets = [
            asset for asset in portfolio.assets
            if asset.liquidity_score < 0.5
        ]
        if low_liquidity_assets:
            recommendations.append(f"Consider replacing low-liquidity assets: {', '.join(asset.symbol for asset in low_liquidity_assets)}")

        unrated_assets = [
            asset for asset in portfolio.assets
            if asset.security_rating == 'UNRATED'
        ]
        if unrated_assets:
            recommendations.append(f"Get security audits for: {', '.join(asset.symbol for asset in unrated_assets)}")

        return recommendations

    def _handle_alert(self, alert: CollateralAlert) -> None:
        """Handle monitoring alerts"""
        self.logger.warning(f"Collateral alert: {alert.alert_type} - {alert.message}")

        # Here you could implement additional alert handling logic such as:
        # - Sending notifications
        # - Triggering automated actions
        # - Logging to external systems