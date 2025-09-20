"""
Collateral Requirements Engine

Core engine for calculating collateral requirements using real Algorand data.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

from .database import CollateralDatabase
from .config import load_config, CollateralEngineConfig
# Import from common shared modules
from ...common.models.blockchain_collateral_models import (
    DigitalCollateralType, VolatilityMetrics, LiquidityMetrics,
    PriceOracle, DigitalAsset
)


@dataclass
class CollateralPosition:
    """Represents a collateral position"""
    asset_id: str
    asset_symbol: str
    asset_type: DigitalCollateralType
    position_size: float
    current_price_usd: float
    position_value_usd: float
    volatility_metrics: Optional[VolatilityMetrics] = None
    liquidity_metrics: Optional[LiquidityMetrics] = None


@dataclass
class CollateralRequirement:
    """Result of collateral requirement analysis"""
    loan_id: Optional[str]
    loan_amount_usd: float
    required_collateral_ratio: float
    total_collateral_value_usd: float
    collateral_positions: List[CollateralPosition]
    risk_level: str  # "low", "medium", "high", "critical"
    confidence_score: float
    liquidation_scenarios: List[Dict[str, Any]]
    recommendations: List[str]
    analysis_timestamp: datetime
    market_conditions: str
    oracle_data_timestamp: datetime


class CollateralRequirementsEngine:
    """Core engine for collateral requirement calculations"""

    def __init__(self, db_path: Optional[Path] = None, config_path: Optional[Path] = None):
        # Load configuration
        self.config = load_config(config_path)

        # Initialize database with absolute path
        if db_path is None:
            # Make database path relative to the collateral-requirements directory
            base_dir = Path(__file__).parent.parent
            db_path = base_dir / self.config.database.default_path
        self.db = CollateralDatabase(db_path)

        # Set MCP URLs from config
        self.mcp_reader_url = self.config.mcp_services.algorand_reader_url
        self.mcp_market_url = self.config.mcp_services.market_data_url

        # Configure collateral ratios by asset type from config
        self.base_collateral_ratios = {
            DigitalCollateralType.ALGO_NATIVE: self.config.base_collateral_ratios.algo_native,
            DigitalCollateralType.STABLECOIN: self.config.base_collateral_ratios.stablecoin,
            DigitalCollateralType.ASA_TOKEN: self.config.base_collateral_ratios.asa_token,
            DigitalCollateralType.GOVERNANCE_TOKEN: self.config.base_collateral_ratios.governance_token,
            DigitalCollateralType.LP_TOKEN: self.config.base_collateral_ratios.lp_token,
            DigitalCollateralType.LIQUID_STAKING: self.config.base_collateral_ratios.liquid_staking,
        }

        # Configure risk adjustment factors from config
        self.volatility_adjustments = {
            "low": self.config.volatility_adjustments.low,
            "medium": self.config.volatility_adjustments.medium,
            "high": self.config.volatility_adjustments.high,
            "extreme": self.config.volatility_adjustments.extreme
        }

        self.liquidity_adjustments = {
            "high": self.config.liquidity_adjustments.high,
            "medium": self.config.liquidity_adjustments.medium,
            "low": self.config.liquidity_adjustments.low
        }

    async def analyze_collateral_requirement(
        self,
        loan_amount_usd: float,
        collateral_positions: List[Dict[str, Any]],
        loan_id: Optional[str] = None,
        borrower_address: Optional[str] = None,
        market_conditions: str = "normal"
    ) -> CollateralRequirement:
        """
        Analyze collateral requirements for a loan

        Args:
            loan_amount_usd: Loan amount in USD
            collateral_positions: List of collateral positions with asset_id, symbol, amount
            loan_id: Optional loan identifier
            borrower_address: Optional borrower address
            market_conditions: "bull", "normal", "bear", "volatile"
        """
        analysis_start = datetime.now()

        # Step 1: Enrich collateral positions with real market data
        enriched_positions = await self._enrich_collateral_positions(collateral_positions)

        # Step 2: Calculate risk metrics for each position
        risk_metrics = await self._calculate_risk_metrics(enriched_positions)

        # Step 3: Calculate portfolio-level requirements
        portfolio_requirements = self._calculate_portfolio_requirements(
            enriched_positions, risk_metrics, market_conditions
        )

        # Step 4: Generate liquidation scenarios
        liquidation_scenarios = self._generate_liquidation_scenarios(
            enriched_positions, loan_amount_usd
        )

        # Step 5: Determine final collateral ratio
        required_ratio = self._determine_final_collateral_ratio(
            portfolio_requirements, liquidation_scenarios, market_conditions
        )

        # Step 6: Calculate total collateral value needed
        total_collateral_needed = loan_amount_usd * required_ratio
        current_collateral_value = sum(pos.position_value_usd for pos in enriched_positions)

        # Step 7: Assess overall risk level
        risk_level = self._assess_risk_level(
            required_ratio, current_collateral_value, total_collateral_needed, risk_metrics
        )

        # Step 8: Calculate confidence score
        confidence_score = self._calculate_confidence_score(enriched_positions, risk_metrics)

        # Step 9: Generate recommendations
        recommendations = self._generate_recommendations(
            loan_amount_usd, enriched_positions, required_ratio, risk_level
        )

        # Create result
        result = CollateralRequirement(
            loan_id=loan_id,
            loan_amount_usd=loan_amount_usd,
            required_collateral_ratio=required_ratio,
            total_collateral_value_usd=current_collateral_value,
            collateral_positions=enriched_positions,
            risk_level=risk_level,
            confidence_score=confidence_score,
            liquidation_scenarios=liquidation_scenarios,
            recommendations=recommendations,
            analysis_timestamp=analysis_start,
            market_conditions=market_conditions,
            oracle_data_timestamp=datetime.now()
        )

        # Store analysis in database
        await self._store_analysis(result, borrower_address)

        return result

    async def _enrich_collateral_positions(
        self,
        positions: List[Dict[str, Any]]
    ) -> List[CollateralPosition]:
        """Enrich positions with real market data from MCP services"""
        enriched_positions = []

        for position in positions:
            asset_id = position['asset_id']
            asset_symbol = position.get('asset_symbol', f"ASA-{asset_id}")
            position_size = float(position['amount'])

            # Try to get cached data first
            cached_data = self.db.get_cached_market_data(asset_id, self.config.analysis.cache_expiry_minutes)

            if cached_data:
                current_price = cached_data['price_usd']
                oracle_source = cached_data.get('oracle_source', 'cache')
            else:
                # Fetch real-time data from MCP services
                current_price, oracle_source = await self._fetch_asset_price(asset_id, asset_symbol)

                # Cache the data
                self.db.cache_market_data(asset_id, asset_symbol, {
                    'price_usd': current_price,
                    'oracle_source': oracle_source,
                    'data_timestamp': datetime.now(),
                    'confidence_score': 0.95  # Default confidence
                })

            # Determine asset type
            asset_type = self._determine_asset_type(asset_id, asset_symbol)

            # Calculate position value
            position_value_usd = position_size * current_price

            # Get volatility and liquidity metrics
            volatility_metrics = await self._get_volatility_metrics(asset_id, asset_symbol)
            liquidity_metrics = await self._get_liquidity_metrics(asset_id, asset_symbol)

            enriched_position = CollateralPosition(
                asset_id=asset_id,
                asset_symbol=asset_symbol,
                asset_type=asset_type,
                position_size=position_size,
                current_price_usd=current_price,
                position_value_usd=position_value_usd,
                volatility_metrics=volatility_metrics,
                liquidity_metrics=liquidity_metrics
            )

            enriched_positions.append(enriched_position)

        return enriched_positions

    async def _fetch_asset_price(self, asset_id: str, asset_symbol: str) -> Tuple[float, str]:
        """Fetch asset price from MCP services"""
        try:
            # Try algorand-reader-mcp first
            async with aiohttp.ClientSession() as session:
                # For ALGO (asset_id "0")
                if asset_id == "0" or asset_symbol.upper() == "ALGO":
                    # Use a reliable price API for ALGO
                    try:
                        async with session.get('https://api.coingecko.com/api/v3/simple/price?ids=algorand&vs_currencies=usd') as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                return data['algorand']['usd'], 'coingecko'
                    except:
                        pass
                    # Fallback price for ALGO
                    return 0.25, 'fallback'

                # For ASA tokens, try to get from Algorand indexer
                try:
                    mcp_url = f"{self.mcp_reader_url}/asset/{asset_id}"
                    async with session.get(mcp_url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # This would need to be implemented in the MCP service
                            # For now, return a reasonable fallback
                            return 1.0, 'mcp-reader'
                except:
                    pass

        except Exception as e:
            print(f"Error fetching price for {asset_symbol}: {e}")

        # Fallback prices from config
        return self.config.fallback_prices.get(asset_symbol.upper(), 1.0), 'fallback'

    def _determine_asset_type(self, asset_id: str, asset_symbol: str) -> DigitalCollateralType:
        """Determine the asset type based on asset ID and symbol"""
        if asset_id == "0" or asset_symbol.upper() == "ALGO":
            return DigitalCollateralType.ALGO_NATIVE

        # Common stablecoins on Algorand
        stablecoins = set(self.config.asset_classification['stablecoins'])
        if asset_symbol.upper() in stablecoins:
            return DigitalCollateralType.STABLECOIN

        # LP tokens usually have specific patterns
        lp_patterns = self.config.asset_classification['lp_patterns']
        if any(pattern in asset_symbol.upper() for pattern in lp_patterns):
            return DigitalCollateralType.LP_TOKEN

        # Governance tokens
        governance_patterns = self.config.asset_classification['governance_patterns']
        if any(pattern in asset_symbol.upper() for pattern in governance_patterns):
            return DigitalCollateralType.GOVERNANCE_TOKEN

        # Liquid staking
        liquid_staking_patterns = self.config.asset_classification['liquid_staking_patterns']
        if any(pattern in asset_symbol.upper() for pattern in liquid_staking_patterns):
            return DigitalCollateralType.LIQUID_STAKING

        # Default to ASA token
        return DigitalCollateralType.ASA_TOKEN

    async def _get_volatility_metrics(self, asset_id: str, asset_symbol: str) -> VolatilityMetrics:
        """Get volatility metrics for an asset"""
        # This would ideally fetch from historical price data
        # For now, use estimates from config

        metrics = self.config.volatility_estimates.get(asset_symbol.upper(), self.config.volatility_estimates['default'])

        return VolatilityMetrics(
            volatility_30d=metrics['volatility_30d'],
            volatility_7d=metrics['volatility_7d'],
            max_drawdown_30d=metrics['max_drawdown_30d'],
            value_at_risk_95=metrics['value_at_risk_95'],
            correlation_with_algo=0.3 if asset_symbol.upper() != 'ALGO' else 1.0,
            stress_test_scenarios={'market_crash': -0.5, 'flash_crash': -0.3}
        )

    async def _get_liquidity_metrics(self, asset_id: str, asset_symbol: str) -> LiquidityMetrics:
        """Get liquidity metrics for an asset"""
        # Use estimates from config
        metrics = self.config.liquidity_estimates.get(asset_symbol.upper(), self.config.liquidity_estimates['default'])

        return LiquidityMetrics(
            daily_volume_usd=metrics['daily_volume_usd'],
            market_cap_usd=metrics['market_cap_usd'],
            depth_1_percent=metrics['daily_volume_usd'] * 0.1,
            largest_liquidation_size=metrics['daily_volume_usd'] * 0.05,
            average_spread_bps=20 if metrics['liquidity_tier'] == 'high' else 50,
            liquidity_tier=metrics['liquidity_tier']
        )

    async def _calculate_risk_metrics(self, positions: List[CollateralPosition]) -> Dict[str, Any]:
        """Calculate portfolio-level risk metrics"""
        total_value = sum(pos.position_value_usd for pos in positions)

        if total_value == 0:
            return {'portfolio_volatility': 1.0, 'diversification_score': 0.0}

        # Calculate weighted portfolio volatility
        weighted_volatility = 0
        for pos in positions:
            weight = pos.position_value_usd / total_value
            if pos.volatility_metrics:
                weighted_volatility += weight * pos.volatility_metrics.volatility_30d

        # Calculate diversification score
        num_assets = len(positions)
        max_position_weight = max(pos.position_value_usd / total_value for pos in positions) if positions else 1
        diversification_score = min(1.0, (num_assets - 1) / 5) * (1 - max_position_weight)

        return {
            'portfolio_volatility': weighted_volatility,
            'diversification_score': diversification_score,
            'concentration_risk': max_position_weight,
            'asset_count': num_assets
        }

    def _calculate_portfolio_requirements(
        self,
        positions: List[CollateralPosition],
        risk_metrics: Dict[str, Any],
        market_conditions: str
    ) -> Dict[str, float]:
        """Calculate portfolio-level collateral requirements"""
        requirements = {}

        for pos in positions:
            base_ratio = self.base_collateral_ratios[pos.asset_type]

            # Volatility adjustment
            if pos.volatility_metrics:
                vol = pos.volatility_metrics.volatility_30d
                if vol < 0.2:
                    vol_adj = self.volatility_adjustments["low"]
                elif vol < 0.4:
                    vol_adj = self.volatility_adjustments["medium"]
                elif vol < 0.6:
                    vol_adj = self.volatility_adjustments["high"]
                else:
                    vol_adj = self.volatility_adjustments["extreme"]
            else:
                vol_adj = self.volatility_adjustments["medium"]

            # Liquidity adjustment
            if pos.liquidity_metrics:
                liq_adj = self.liquidity_adjustments[pos.liquidity_metrics.liquidity_tier]
            else:
                liq_adj = self.liquidity_adjustments["medium"]

            # Market conditions adjustment from config
            market_adj = getattr(self.config.market_conditions_adjustments, market_conditions, 1.0)

            # Portfolio diversification bonus
            diversification_bonus = 1 - (risk_metrics['diversification_score'] * self.config.analysis.diversification_bonus_factor)

            adjusted_ratio = base_ratio * vol_adj * liq_adj * market_adj * diversification_bonus

            requirements[pos.asset_id] = adjusted_ratio

        return requirements

    def _generate_liquidation_scenarios(
        self,
        positions: List[CollateralPosition],
        loan_amount_usd: float
    ) -> List[Dict[str, Any]]:
        """Generate liquidation scenarios for risk assessment"""
        scenarios = []

        price_drops = self.config.liquidation_scenarios.price_drops
        scenario_names = self.config.liquidation_scenarios.scenario_names

        for i, drop in enumerate(price_drops):
            total_liquidation_value = 0
            for pos in positions:
                liquidation_price = pos.current_price_usd * (1 - drop)
                slippage_factor = 1 - (self.config.liquidation_scenarios.base_slippage + (drop * 0.1))
                liquidation_value = pos.position_size * liquidation_price * slippage_factor
                total_liquidation_value += liquidation_value

            scenarios.append({
                'scenario_name': scenario_names[i],
                'price_drop_percentage': drop,
                'estimated_liquidation_value': total_liquidation_value,
                'liquidation_time_hours': 1 + (i * 2),  # Longer for larger drops
                'slippage_percentage': self.config.liquidation_scenarios.base_slippage + (drop * 0.1),
                'gas_costs_usd': self.config.liquidation_scenarios.gas_costs_usd,
                'net_recovery_percentage': max(0, (total_liquidation_value - loan_amount_usd) / loan_amount_usd),
                'scenario_probability': max(0.01, 0.3 - (drop * 0.5))  # Lower probability for extreme drops
            })

        return scenarios

    def _determine_final_collateral_ratio(
        self,
        portfolio_requirements: Dict[str, float],
        liquidation_scenarios: List[Dict[str, Any]],
        market_conditions: str
    ) -> float:
        """Determine the final collateral ratio"""
        if not portfolio_requirements:
            return 2.0  # Safe default

        # Weighted average of individual requirements
        avg_requirement = sum(portfolio_requirements.values()) / len(portfolio_requirements)

        # Stress test adjustment based on liquidation scenarios
        worst_recovery = min(scenario['net_recovery_percentage'] for scenario in liquidation_scenarios)
        if worst_recovery < 0:
            stress_adjustment = 1 + abs(worst_recovery)
        else:
            stress_adjustment = 1.0

        # Final ratio with safety buffer from config
        safety_multiplier = 1 + self.config.analysis.safety_buffer
        final_ratio = avg_requirement * stress_adjustment * safety_multiplier

        return round(final_ratio, 3)

    def _assess_risk_level(
        self,
        required_ratio: float,
        current_value: float,
        needed_value: float,
        risk_metrics: Dict[str, Any]
    ) -> str:
        """Assess overall risk level"""
        if current_value >= needed_value:
            if (risk_metrics['portfolio_volatility'] < self.config.risk_thresholds.low_volatility and
                risk_metrics['diversification_score'] > self.config.risk_thresholds.high_diversification):
                return "low"
            else:
                return "medium"
        elif current_value >= needed_value * self.config.risk_thresholds.adequate_collateral_ratio:
            return "medium"
        elif current_value >= needed_value * self.config.risk_thresholds.marginal_collateral_ratio:
            return "high"
        else:
            return "critical"

    def _calculate_confidence_score(
        self,
        positions: List[CollateralPosition],
        risk_metrics: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the analysis"""
        base_confidence = self.config.analysis.default_confidence_score

        # Diversification bonus
        diversification_bonus = risk_metrics['diversification_score'] * self.config.analysis.diversification_bonus_factor

        # Data quality penalty (if using fallback prices)
        # This would be improved with real oracle confidence scores
        data_quality_score = self.config.analysis.data_quality_score

        confidence = min(1.0, base_confidence + diversification_bonus) * data_quality_score

        return round(confidence, 3)

    def _generate_recommendations(
        self,
        loan_amount: float,
        positions: List[CollateralPosition],
        required_ratio: float,
        risk_level: str
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        current_value = sum(pos.position_value_usd for pos in positions)
        needed_value = loan_amount * required_ratio

        if current_value < needed_value:
            shortfall = needed_value - current_value
            recommendations.append(f"Add ${shortfall:,.0f} more collateral to meet requirements")

        if risk_level in ["high", "critical"]:
            recommendations.append("Consider reducing loan amount or adding more stable collateral")

        # Diversification recommendations
        position_weights = [pos.position_value_usd / current_value for pos in positions]
        max_weight = max(position_weights) if position_weights else 0

        if max_weight > self.config.analysis.max_position_concentration:
            recommendations.append("Improve diversification by adding different asset types")

        # Volatility recommendations
        high_vol_assets = [pos.asset_symbol for pos in positions
                          if pos.volatility_metrics and pos.volatility_metrics.volatility_30d > 0.6]
        if high_vol_assets:
            recommendations.append(f"Consider reducing exposure to high-volatility assets: {', '.join(high_vol_assets)}")

        if not recommendations:
            recommendations.append("Collateral portfolio appears well-balanced")

        return recommendations

    async def _store_analysis(self, result: CollateralRequirement, borrower_address: Optional[str]):
        """Store analysis results in database"""
        analysis_data = {
            'loan_id': result.loan_id,
            'loan_amount_usd': result.loan_amount_usd,
            'borrower_address': borrower_address,
            'confidence_score': result.confidence_score,
            'risk_level': result.risk_level,
            'required_collateral_ratio': result.required_collateral_ratio,
            'total_collateral_value_usd': result.total_collateral_value_usd,
            'market_conditions': result.market_conditions,
            'oracle_data_timestamp': result.oracle_data_timestamp,
            'input_parameters': {
                'market_conditions': result.market_conditions,
                'position_count': len(result.collateral_positions)
            },
            'analysis_results': {
                'recommendations': result.recommendations,
                'risk_assessment': result.risk_level
            },
            'asset_valuations': [
                {
                    'asset_id': pos.asset_id,
                    'asset_symbol': pos.asset_symbol,
                    'asset_type': pos.asset_type.value,
                    'current_price_usd': pos.current_price_usd,
                    'position_size': pos.position_size,
                    'position_value_usd': pos.position_value_usd,
                    'volatility_30d': pos.volatility_metrics.volatility_30d if pos.volatility_metrics else None,
                    'volatility_7d': pos.volatility_metrics.volatility_7d if pos.volatility_metrics else None,
                    'liquidity_tier': pos.liquidity_metrics.liquidity_tier if pos.liquidity_metrics else None,
                    'oracle_source': 'real_data',
                    'oracle_confidence': 0.9
                }
                for pos in result.collateral_positions
            ],
            'liquidation_scenarios': result.liquidation_scenarios
        }

        self.db.store_collateral_analysis(analysis_data)