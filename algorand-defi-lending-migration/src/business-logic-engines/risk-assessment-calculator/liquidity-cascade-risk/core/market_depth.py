"""
Market Depth Analyzer - Comprehensive DEX liquidity depth analysis across Algorand ecosystem

This module analyzes market depth across all major Algorand DEXs to assess liquidity availability,
price impact, and potential cascade effects from large liquidation events.
"""

import asyncio
import aiohttp
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DEXType(Enum):
    """Types of DEXs on Algorand"""
    AMM = "amm"          # Automated Market Maker
    ORDERBOOK = "orderbook"  # Order book based
    HYBRID = "hybrid"    # Hybrid model

@dataclass
class OrderBookLevel:
    """Order book level data"""
    price: float
    quantity: float
    cumulative_quantity: float
    cumulative_usd: float

@dataclass
class MarketDepthData:
    """Market depth data for a trading pair"""
    pair: str
    dex: str
    timestamp: datetime
    base_asset: str
    quote_asset: str
    bid_levels: List[OrderBookLevel]
    ask_levels: List[OrderBookLevel]
    mid_price: float
    spread_bps: float
    total_bid_liquidity: float
    total_ask_liquidity: float
    depth_1pct: float  # Liquidity within 1% of mid price
    depth_5pct: float  # Liquidity within 5% of mid price
    depth_10pct: float # Liquidity within 10% of mid price

@dataclass
class DEXLiquidityState:
    """Current liquidity state of a DEX"""
    dex_name: str
    dex_type: DEXType
    total_tvl: float
    active_pairs: int
    avg_spread_bps: float
    depth_score: float  # 0-1 liquidity depth score
    market_share: float
    last_updated: datetime

@dataclass
class AggregatedDepth:
    """Aggregated market depth across all DEXs"""
    asset_pair: str
    total_liquidity: float
    weighted_mid_price: float
    aggregated_spread_bps: float
    dex_breakdown: Dict[str, float]  # Liquidity per DEX
    depth_distribution: Dict[str, float]  # Depth at various price levels
    concentration_risk: float  # Risk of liquidity concentration

class MarketDepthAnalyzer:
    """
    Comprehensive market depth analyzer for Algorand DEX ecosystem.
    Provides real-time liquidity analysis and depth assessment.
    """

    def __init__(self, config_path: str = None):
        """Initialize the market depth analyzer"""
        self.config = self._load_config(config_path)
        self.dex_configs = self.config['market_depth']['dexes']
        self.depth_levels = self.config['market_depth']['depth_levels']
        self.min_liquidity = self.config['market_depth']['min_liquidity_threshold']

        # Initialize DEX states
        self.dex_states: Dict[str, DEXLiquidityState] = {}
        self.market_data_cache: Dict[str, MarketDepthData] = {}
        self.depth_history: List[Dict[str, Any]] = []

        # Session for HTTP requests
        self.session: Optional[aiohttp.ClientSession] = None

        logger.info("Market Depth Analyzer initialized")

    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def analyze_market_depth(
        self,
        asset_pairs: List[str] = None
    ) -> Dict[str, AggregatedDepth]:
        """
        Analyze market depth across all DEXs for specified asset pairs

        Args:
            asset_pairs: List of asset pairs to analyze (e.g., ['ALGO/USDC', 'GARD/ALGO'])

        Returns:
            Dictionary of aggregated depth data per asset pair
        """
        if asset_pairs is None:
            asset_pairs = ['ALGO/USDC', 'ALGO/USDT', 'GARD/ALGO', 'BANK/ALGO', 'OPUL/ALGO']

        if not self.session:
            self.session = aiohttp.ClientSession()

        aggregated_depths = {}

        for pair in asset_pairs:
            logger.info(f"Analyzing market depth for {pair}")

            # Collect depth data from all DEXs
            dex_depths = await self._collect_dex_depths(pair)

            if dex_depths:
                # Aggregate depth across DEXs
                aggregated_depth = self._aggregate_market_depth(pair, dex_depths)
                aggregated_depths[pair] = aggregated_depth

        return aggregated_depths

    async def _collect_dex_depths(self, asset_pair: str) -> Dict[str, MarketDepthData]:
        """Collect market depth data from all DEXs for an asset pair"""
        dex_depths = {}

        # Collect data from each DEX concurrently
        tasks = []
        for dex_name in self.dex_configs.keys():
            task = self._fetch_dex_depth(dex_name, asset_pair)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for dex_name, result in zip(self.dex_configs.keys(), results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch depth from {dex_name}: {result}")
            elif result:
                dex_depths[dex_name] = result

        return dex_depths

    async def _fetch_dex_depth(self, dex_name: str, asset_pair: str) -> Optional[MarketDepthData]:
        """Fetch market depth data from a specific DEX"""
        try:
            if dex_name == 'tinyman':
                return await self._fetch_tinyman_depth(asset_pair)
            elif dex_name == 'pact':
                return await self._fetch_pact_depth(asset_pair)
            elif dex_name == 'algofi_dex':
                return await self._fetch_algofi_depth(asset_pair)
            elif dex_name == 'algodex':
                return await self._fetch_algodex_depth(asset_pair)
            elif dex_name == 'humble':
                return await self._fetch_humble_depth(asset_pair)
            else:
                logger.warning(f"Unknown DEX: {dex_name}")
                return None

        except Exception as e:
            logger.error(f"Error fetching depth from {dex_name}: {e}")
            return None

    async def _fetch_tinyman_depth(self, asset_pair: str) -> Optional[MarketDepthData]:
        """Fetch market depth from Tinyman"""
        # Parse asset pair
        base_asset, quote_asset = asset_pair.split('/')

        # Mock implementation - replace with actual Tinyman API calls
        # In production, this would call Tinyman's analytics API
        mock_depth = self._generate_mock_depth_data(
            pair=asset_pair,
            dex='tinyman',
            base_asset=base_asset,
            quote_asset=quote_asset,
            mid_price=0.5 if base_asset == 'ALGO' else 1.0,
            liquidity_factor=1.0
        )

        return mock_depth

    async def _fetch_pact_depth(self, asset_pair: str) -> Optional[MarketDepthData]:
        """Fetch market depth from Pact"""
        base_asset, quote_asset = asset_pair.split('/')

        mock_depth = self._generate_mock_depth_data(
            pair=asset_pair,
            dex='pact',
            base_asset=base_asset,
            quote_asset=quote_asset,
            mid_price=0.5 if base_asset == 'ALGO' else 1.0,
            liquidity_factor=0.7
        )

        return mock_depth

    async def _fetch_algofi_depth(self, asset_pair: str) -> Optional[MarketDepthData]:
        """Fetch market depth from Algofi DEX"""
        base_asset, quote_asset = asset_pair.split('/')

        mock_depth = self._generate_mock_depth_data(
            pair=asset_pair,
            dex='algofi_dex',
            base_asset=base_asset,
            quote_asset=quote_asset,
            mid_price=0.5 if base_asset == 'ALGO' else 1.0,
            liquidity_factor=0.6
        )

        return mock_depth

    async def _fetch_algodex_depth(self, asset_pair: str) -> Optional[MarketDepthData]:
        """Fetch market depth from Algodex"""
        base_asset, quote_asset = asset_pair.split('/')

        mock_depth = self._generate_mock_depth_data(
            pair=asset_pair,
            dex='algodex',
            base_asset=base_asset,
            quote_asset=quote_asset,
            mid_price=0.5 if base_asset == 'ALGO' else 1.0,
            liquidity_factor=0.4
        )

        return mock_depth

    async def _fetch_humble_depth(self, asset_pair: str) -> Optional[MarketDepthData]:
        """Fetch market depth from Humble"""
        base_asset, quote_asset = asset_pair.split('/')

        mock_depth = self._generate_mock_depth_data(
            pair=asset_pair,
            dex='humble',
            base_asset=base_asset,
            quote_asset=quote_asset,
            mid_price=0.5 if base_asset == 'ALGO' else 1.0,
            liquidity_factor=0.2
        )

        return mock_depth

    def _generate_mock_depth_data(
        self,
        pair: str,
        dex: str,
        base_asset: str,
        quote_asset: str,
        mid_price: float,
        liquidity_factor: float
    ) -> MarketDepthData:
        """Generate mock market depth data for testing"""

        # Generate realistic order book levels
        bid_levels = []
        ask_levels = []

        # Base liquidity amounts (scaled by DEX factor)
        base_liquidity = 100000 * liquidity_factor  # Base $100k liquidity

        # Generate bid levels (below mid price)
        cumulative_qty = 0
        cumulative_usd = 0
        for i in range(20):  # 20 levels
            price_offset = (i + 1) * 0.001  # 0.1% increments
            price = mid_price * (1 - price_offset)
            quantity = base_liquidity * np.exp(-i * 0.3) / price  # Exponential decay
            cumulative_qty += quantity
            cumulative_usd += quantity * price

            bid_levels.append(OrderBookLevel(
                price=price,
                quantity=quantity,
                cumulative_quantity=cumulative_qty,
                cumulative_usd=cumulative_usd
            ))

        # Generate ask levels (above mid price)
        cumulative_qty = 0
        cumulative_usd = 0
        for i in range(20):  # 20 levels
            price_offset = (i + 1) * 0.001  # 0.1% increments
            price = mid_price * (1 + price_offset)
            quantity = base_liquidity * np.exp(-i * 0.3) / price  # Exponential decay
            cumulative_qty += quantity
            cumulative_usd += quantity * price

            ask_levels.append(OrderBookLevel(
                price=price,
                quantity=quantity,
                cumulative_quantity=cumulative_qty,
                cumulative_usd=cumulative_usd
            ))

        # Calculate depth metrics
        spread_bps = ((ask_levels[0].price - bid_levels[0].price) / mid_price) * 10000

        # Calculate depth at various price levels
        depth_1pct = self._calculate_depth_at_price_level(bid_levels, ask_levels, mid_price, 0.01)
        depth_5pct = self._calculate_depth_at_price_level(bid_levels, ask_levels, mid_price, 0.05)
        depth_10pct = self._calculate_depth_at_price_level(bid_levels, ask_levels, mid_price, 0.10)

        return MarketDepthData(
            pair=pair,
            dex=dex,
            timestamp=datetime.now(),
            base_asset=base_asset,
            quote_asset=quote_asset,
            bid_levels=bid_levels,
            ask_levels=ask_levels,
            mid_price=mid_price,
            spread_bps=spread_bps,
            total_bid_liquidity=sum(level.quantity * level.price for level in bid_levels),
            total_ask_liquidity=sum(level.quantity * level.price for level in ask_levels),
            depth_1pct=depth_1pct,
            depth_5pct=depth_5pct,
            depth_10pct=depth_10pct
        )

    def _calculate_depth_at_price_level(
        self,
        bid_levels: List[OrderBookLevel],
        ask_levels: List[OrderBookLevel],
        mid_price: float,
        price_threshold: float
    ) -> float:
        """Calculate total liquidity within a price threshold"""
        min_bid_price = mid_price * (1 - price_threshold)
        max_ask_price = mid_price * (1 + price_threshold)

        bid_liquidity = sum(
            level.quantity * level.price for level in bid_levels
            if level.price >= min_bid_price
        )

        ask_liquidity = sum(
            level.quantity * level.price for level in ask_levels
            if level.price <= max_ask_price
        )

        return bid_liquidity + ask_liquidity

    def _aggregate_market_depth(
        self,
        asset_pair: str,
        dex_depths: Dict[str, MarketDepthData]
    ) -> AggregatedDepth:
        """Aggregate market depth across multiple DEXs"""

        if not dex_depths:
            return AggregatedDepth(
                asset_pair=asset_pair,
                total_liquidity=0,
                weighted_mid_price=0,
                aggregated_spread_bps=0,
                dex_breakdown={},
                depth_distribution={},
                concentration_risk=1.0
            )

        # Calculate total liquidity and weights
        total_liquidity = 0
        dex_breakdown = {}
        liquidity_weights = {}

        for dex, depth in dex_depths.items():
            dex_liquidity = depth.total_bid_liquidity + depth.total_ask_liquidity
            total_liquidity += dex_liquidity
            dex_breakdown[dex] = dex_liquidity

        # Calculate weights
        for dex, liquidity in dex_breakdown.items():
            liquidity_weights[dex] = liquidity / total_liquidity if total_liquidity > 0 else 0

        # Calculate weighted mid price
        weighted_mid_price = sum(
            depth.mid_price * liquidity_weights[dex]
            for dex, depth in dex_depths.items()
        )

        # Calculate aggregated spread
        aggregated_spread = sum(
            depth.spread_bps * liquidity_weights[dex]
            for dex, depth in dex_depths.items()
        )

        # Calculate depth distribution
        depth_distribution = {}
        for level in self.depth_levels:
            level_depth = sum(
                self._calculate_depth_at_price_level(
                    depth.bid_levels, depth.ask_levels, depth.mid_price, level / 100
                ) * liquidity_weights[dex]
                for dex, depth in dex_depths.items()
            )
            depth_distribution[f"{level}%"] = level_depth

        # Calculate concentration risk (Herfindahl-Hirschman Index)
        concentration_risk = sum(weight ** 2 for weight in liquidity_weights.values())

        return AggregatedDepth(
            asset_pair=asset_pair,
            total_liquidity=total_liquidity,
            weighted_mid_price=weighted_mid_price,
            aggregated_spread_bps=aggregated_spread,
            dex_breakdown=dex_breakdown,
            depth_distribution=depth_distribution,
            concentration_risk=concentration_risk
        )

    async def analyze_liquidation_impact(
        self,
        asset_pair: str,
        liquidation_amount_usd: float,
        side: str = "sell"  # "buy" or "sell"
    ) -> Dict[str, Any]:
        """
        Analyze the market impact of a large liquidation event

        Args:
            asset_pair: Trading pair for liquidation
            liquidation_amount_usd: USD amount to be liquidated
            side: "buy" or "sell" direction

        Returns:
            Analysis of market impact including price impact and slippage
        """
        logger.info(f"Analyzing liquidation impact for {liquidation_amount_usd:,.0f} USD {side} of {asset_pair}")

        # Get current market depth
        depth_data = await self.analyze_market_depth([asset_pair])

        if asset_pair not in depth_data:
            return {"error": f"No depth data available for {asset_pair}"}

        aggregated_depth = depth_data[asset_pair]

        # Calculate price impact across DEXs
        dex_impacts = {}
        total_filled = 0
        weighted_avg_price = 0

        for dex_name in self.dex_configs.keys():
            dex_liquidity = aggregated_depth.dex_breakdown.get(dex_name, 0)

            if dex_liquidity > 0:
                # Calculate proportion of liquidation to execute on this DEX
                dex_proportion = dex_liquidity / aggregated_depth.total_liquidity
                dex_amount = liquidation_amount_usd * dex_proportion

                # Simulate order execution
                impact = self._simulate_order_execution(
                    dex_name, asset_pair, dex_amount, side
                )

                dex_impacts[dex_name] = impact
                total_filled += impact['filled_amount']
                weighted_avg_price += impact['avg_price'] * impact['filled_amount']

        # Calculate overall impact
        overall_avg_price = weighted_avg_price / total_filled if total_filled > 0 else 0
        price_impact_pct = abs(overall_avg_price - aggregated_depth.weighted_mid_price) / aggregated_depth.weighted_mid_price

        # Calculate market recovery time
        recovery_time = self._estimate_market_recovery_time(
            asset_pair, liquidation_amount_usd, price_impact_pct
        )

        return {
            'asset_pair': asset_pair,
            'liquidation_amount_usd': liquidation_amount_usd,
            'side': side,
            'total_filled': total_filled,
            'fill_ratio': total_filled / liquidation_amount_usd,
            'average_execution_price': overall_avg_price,
            'mid_price': aggregated_depth.weighted_mid_price,
            'price_impact_pct': price_impact_pct,
            'slippage_bps': price_impact_pct * 10000,
            'dex_breakdown': dex_impacts,
            'estimated_recovery_minutes': recovery_time,
            'market_depth_consumed': liquidation_amount_usd / aggregated_depth.total_liquidity
        }

    def _simulate_order_execution(
        self,
        dex_name: str,
        asset_pair: str,
        amount_usd: float,
        side: str
    ) -> Dict[str, Any]:
        """Simulate order execution on a specific DEX"""

        # Get DEX-specific slippage multiplier
        slippage_multiplier = self.dex_configs[dex_name].get('slippage_multiplier', 1.0)

        # Simple slippage model - in production this would use actual order book data
        base_slippage = 0.001  # 0.1% base slippage
        size_impact = amount_usd / 1_000_000  # Additional impact per $1M

        total_slippage = (base_slippage + size_impact * 0.002) * slippage_multiplier

        # Simulate execution
        mid_price = 0.5  # Simplified - would get from actual market data

        if side == "sell":
            avg_price = mid_price * (1 - total_slippage)
        else:
            avg_price = mid_price * (1 + total_slippage)

        # Assume full fill for now - could model partial fills
        filled_amount = amount_usd

        return {
            'dex': dex_name,
            'filled_amount': filled_amount,
            'avg_price': avg_price,
            'slippage_pct': total_slippage,
            'slippage_bps': total_slippage * 10000
        }

    def _estimate_market_recovery_time(
        self,
        asset_pair: str,
        impact_amount: float,
        price_impact_pct: float
    ) -> float:
        """Estimate time for market to recover from large trade impact"""

        # Base recovery time factors
        base_recovery_minutes = 15  # 15 minutes base recovery

        # Size impact factor
        size_factor = impact_amount / 1_000_000  # Per $1M

        # Price impact factor
        impact_factor = price_impact_pct * 100  # Per 1% impact

        # Market liquidity factor (lower liquidity = longer recovery)
        liquidity_factor = 1.0  # Would calculate from actual depth data

        recovery_time = base_recovery_minutes * (1 + size_factor * 0.5 + impact_factor * 2.0) * liquidity_factor

        return min(recovery_time, 240)  # Cap at 4 hours

    async def get_real_time_depth_metrics(self) -> Dict[str, Any]:
        """Get real-time depth metrics across all DEXs"""

        # Analyze major pairs
        major_pairs = ['ALGO/USDC', 'ALGO/USDT', 'GARD/ALGO']
        depth_analysis = await self.analyze_market_depth(major_pairs)

        # Calculate system-wide metrics
        total_liquidity = sum(depth.total_liquidity for depth in depth_analysis.values())

        avg_spread = np.mean([depth.aggregated_spread_bps for depth in depth_analysis.values()])

        max_concentration_risk = max(depth.concentration_risk for depth in depth_analysis.values())

        # DEX market shares
        dex_market_shares = {}
        for dex in self.dex_configs.keys():
            dex_liquidity = sum(
                depth.dex_breakdown.get(dex, 0) for depth in depth_analysis.values()
            )
            dex_market_shares[dex] = dex_liquidity / total_liquidity if total_liquidity > 0 else 0

        return {
            'timestamp': datetime.now().isoformat(),
            'total_ecosystem_liquidity': total_liquidity,
            'average_spread_bps': avg_spread,
            'max_concentration_risk': max_concentration_risk,
            'dex_market_shares': dex_market_shares,
            'pair_analysis': {
                pair: {
                    'liquidity': depth.total_liquidity,
                    'spread_bps': depth.aggregated_spread_bps,
                    'concentration_risk': depth.concentration_risk
                }
                for pair, depth in depth_analysis.items()
            },
            'liquidity_distribution': self._calculate_liquidity_distribution(depth_analysis)
        }

    def _calculate_liquidity_distribution(self, depth_analysis: Dict[str, AggregatedDepth]) -> Dict[str, float]:
        """Calculate liquidity distribution across price levels"""

        distribution = {}

        for level in self.depth_levels:
            level_key = f"{level}%"
            total_level_liquidity = sum(
                depth.depth_distribution.get(level_key, 0)
                for depth in depth_analysis.values()
            )
            distribution[level_key] = total_level_liquidity

        return distribution

    async def monitor_depth_changes(self, monitoring_duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """Monitor market depth changes over time"""

        logger.info(f"Starting depth monitoring for {monitoring_duration_minutes} minutes")

        monitoring_data = []
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < monitoring_duration_minutes * 60:
            # Get current depth metrics
            current_metrics = await self.get_real_time_depth_metrics()
            monitoring_data.append(current_metrics)

            # Wait for next measurement
            await asyncio.sleep(self.config['market_depth']['refresh_interval'])

        return monitoring_data

    def calculate_depth_score(self, depth_data: MarketDepthData) -> float:
        """Calculate a depth score (0-1) for market quality"""

        # Factors for depth scoring
        spread_score = max(0, 1 - depth_data.spread_bps / 1000)  # Penalize wide spreads

        liquidity_score = min(1, depth_data.total_bid_liquidity + depth_data.total_ask_liquidity / 1_000_000)

        depth_distribution_score = (
            depth_data.depth_1pct * 0.4 +
            depth_data.depth_5pct * 0.4 +
            depth_data.depth_10pct * 0.2
        ) / 1_000_000  # Normalize to millions

        depth_distribution_score = min(1, depth_distribution_score)

        # Weighted depth score
        depth_score = (
            spread_score * 0.3 +
            liquidity_score * 0.4 +
            depth_distribution_score * 0.3
        )

        return depth_score

    async def assess_cascade_liquidity_risk(
        self,
        potential_liquidations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess liquidity risk for potential cascade liquidations"""

        total_cascade_volume = sum(liq['amount_usd'] for liq in potential_liquidations)

        # Analyze each asset that might be liquidated
        asset_impacts = {}
        total_market_impact = 0

        for liquidation in potential_liquidations:
            asset = liquidation['asset']
            amount = liquidation['amount_usd']

            # Find relevant trading pair
            pair = f"{asset}/USDC" if asset != "USDC" else "ALGO/USDC"

            # Analyze liquidation impact
            impact = await self.analyze_liquidation_impact(pair, amount, "sell")
            asset_impacts[asset] = impact

            total_market_impact += impact.get('price_impact_pct', 0)

        # Calculate system-wide liquidity stress
        current_depth = await self.get_real_time_depth_metrics()

        liquidity_stress_ratio = total_cascade_volume / current_depth['total_ecosystem_liquidity']

        # Assess recovery capability
        estimated_recovery_time = max(
            impact.get('estimated_recovery_minutes', 0) for impact in asset_impacts.values()
        )

        risk_level = self._calculate_cascade_liquidity_risk_level(
            liquidity_stress_ratio, total_market_impact, estimated_recovery_time
        )

        return {
            'total_cascade_volume_usd': total_cascade_volume,
            'liquidity_stress_ratio': liquidity_stress_ratio,
            'total_market_impact_pct': total_market_impact,
            'estimated_recovery_minutes': estimated_recovery_time,
            'risk_level': risk_level,
            'asset_impacts': asset_impacts,
            'ecosystem_liquidity': current_depth['total_ecosystem_liquidity']
        }

    def _calculate_cascade_liquidity_risk_level(
        self,
        stress_ratio: float,
        market_impact: float,
        recovery_time: float
    ) -> str:
        """Calculate overall cascade liquidity risk level"""

        # Risk scoring
        stress_score = min(stress_ratio * 10, 1.0)  # 10% stress = max score
        impact_score = min(market_impact * 20, 1.0)  # 5% impact = max score
        recovery_score = min(recovery_time / 240, 1.0)  # 4 hours = max score

        overall_score = (stress_score * 0.4 + impact_score * 0.4 + recovery_score * 0.2)

        if overall_score < 0.3:
            return "LOW"
        elif overall_score < 0.6:
            return "MEDIUM"
        elif overall_score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"


# Example usage and testing
async def main():
    """Example usage of the market depth analyzer"""
    async with MarketDepthAnalyzer() as analyzer:

        # Analyze current market depth
        depth_analysis = await analyzer.analyze_market_depth(['ALGO/USDC', 'GARD/ALGO'])

        print("Market Depth Analysis:")
        for pair, depth in depth_analysis.items():
            print(f"\n{pair}:")
            print(f"  Total Liquidity: ${depth.total_liquidity:,.0f}")
            print(f"  Spread: {depth.aggregated_spread_bps:.1f} bps")
            print(f"  Concentration Risk: {depth.concentration_risk:.3f}")

        # Analyze liquidation impact
        liquidation_impact = await analyzer.analyze_liquidation_impact(
            'ALGO/USDC', 5_000_000, 'sell'
        )

        print(f"\nLiquidation Impact Analysis:")
        print(f"Price Impact: {liquidation_impact['price_impact_pct']:.2%}")
        print(f"Slippage: {liquidation_impact['slippage_bps']:.1f} bps")
        print(f"Recovery Time: {liquidation_impact['estimated_recovery_minutes']:.1f} minutes")

        # Get real-time metrics
        real_time_metrics = await analyzer.get_real_time_depth_metrics()
        print(f"\nReal-time Metrics:")
        print(f"Total Ecosystem Liquidity: ${real_time_metrics['total_ecosystem_liquidity']:,.0f}")
        print(f"Average Spread: {real_time_metrics['average_spread_bps']:.1f} bps")

if __name__ == "__main__":
    asyncio.run(main())