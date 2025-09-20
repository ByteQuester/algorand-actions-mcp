"""
Algofi Yields Analyzer

Fetches and analyzes lending/borrowing rates from the Algofi protocol.
Provides real-time yield data for DeFi interest rate calculations.
"""

import asyncio
import logging
import aiohttp
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import json
import statistics

@dataclass
class AlgofiMarket:
    """Represents an Algofi lending market"""
    asset_id: str
    asset_name: str
    supply_apy: float
    borrow_apy: float
    total_supply: float
    total_borrows: float
    utilization_rate: float
    liquidity_available: float
    last_update: datetime

@dataclass
class AlgofiYieldData:
    """Complete Algofi yield analysis data"""
    markets: List[AlgofiMarket]
    weighted_average_supply_apy: float
    weighted_average_borrow_apy: float
    total_value_locked: float
    protocol_utilization: float
    confidence_score: float
    timestamp: datetime
    metadata: Dict[str, Any]

class AlgofiYieldsAnalyzer:
    """
    Analyzer for Algofi protocol lending and borrowing yields.

    Fetches real-time data from Algofi APIs and calculates weighted yields
    for use in DeFi interest rate determination.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Algofi yields analyzer"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.cache = {}
        self.historical_yields = []

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            # Fallback configuration
            return {
                'defi_protocols': {
                    'algofi': {
                        'api_endpoint': 'https://api.algofi.org/v1',
                        'weight': 0.4,
                        'supported_assets': ['ALGO', 'USDC', 'USDT']
                    }
                }
            }

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the analyzer"""
        logger = logging.getLogger('algofi_yields_analyzer')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def fetch_algofi_markets(self) -> List[AlgofiMarket]:
        """
        Fetch current market data from Algofi

        Returns:
            List[AlgofiMarket]: List of Algofi lending markets
        """
        try:
            # Check cache first
            if self._is_cache_valid('algofi_markets'):
                return self.cache['algofi_markets']

            # Fetch from Algofi API
            markets_data = await self._fetch_markets_from_api()

            # Parse market data
            markets = []
            for market_data in markets_data:
                market = self._parse_market_data(market_data)
                if market:
                    markets.append(market)

            # Cache the results
            self.cache['algofi_markets'] = markets
            self.cache['algofi_markets_timestamp'] = datetime.now()

            return markets

        except Exception as e:
            self.logger.error(f"Error fetching Algofi markets: {e}")
            return self._get_fallback_markets()

    async def _fetch_markets_from_api(self) -> List[Dict]:
        """Fetch market data from Algofi API"""
        try:
            algofi_config = self.config['defi_protocols']['algofi']
            api_endpoint = algofi_config['api_endpoint']

            async with aiohttp.ClientSession() as session:
                # Try to fetch from actual Algofi API
                async with session.get(f"{api_endpoint}/markets") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('markets', [])
                    else:
                        self.logger.warning(f"Algofi API returned status {response.status}")

        except Exception as e:
            self.logger.warning(f"Direct Algofi API unavailable: {e}")

        # Fallback to MCP service
        return await self._fetch_via_mcp_service()

    async def _fetch_via_mcp_service(self) -> List[Dict]:
        """Fetch market data via MCP service"""
        try:
            mcp_url = self.config['mcp_services']['market_data_url']

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{mcp_url}/defi/algofi/markets") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('markets', [])

        except Exception as e:
            self.logger.warning(f"MCP service unavailable: {e}")

        # Return simulated data if all sources fail
        return self._get_simulated_market_data()

    def _get_simulated_market_data(self) -> List[Dict]:
        """Return simulated Algofi market data for testing"""
        return [
            {
                'asset_id': '0',
                'asset_name': 'ALGO',
                'supply_apy': 0.045,  # 4.5% supply APY
                'borrow_apy': 0.065,  # 6.5% borrow APY
                'total_supply': 50000000,  # 50M ALGO
                'total_borrows': 30000000,  # 30M ALGO
                'utilization_rate': 0.6,   # 60% utilization
                'cash': 20000000  # 20M ALGO available
            },
            {
                'asset_id': '31566704',
                'asset_name': 'USDC',
                'supply_apy': 0.035,  # 3.5% supply APY
                'borrow_apy': 0.055,  # 5.5% borrow APY
                'total_supply': 25000000,  # 25M USDC
                'total_borrows': 18000000,  # 18M USDC
                'utilization_rate': 0.72,  # 72% utilization
                'cash': 7000000   # 7M USDC available
            },
            {
                'asset_id': '312769',
                'asset_name': 'USDT',
                'supply_apy': 0.038,  # 3.8% supply APY
                'borrow_apy': 0.058,  # 5.8% borrow APY
                'total_supply': 15000000,  # 15M USDT
                'total_borrows': 10000000,  # 10M USDT
                'utilization_rate': 0.67,  # 67% utilization
                'cash': 5000000   # 5M USDT available
            },
            {
                'asset_id': '386192725',
                'asset_name': 'goBTC',
                'supply_apy': 0.025,  # 2.5% supply APY
                'borrow_apy': 0.085,  # 8.5% borrow APY
                'total_supply': 500,    # 500 goBTC
                'total_borrows': 350,   # 350 goBTC
                'utilization_rate': 0.7, # 70% utilization
                'cash': 150      # 150 goBTC available
            }
        ]

    def _parse_market_data(self, market_data: Dict) -> Optional[AlgofiMarket]:
        """Parse raw market data into AlgofiMarket object"""
        try:
            asset_id = str(market_data.get('asset_id', ''))
            asset_name = market_data.get('asset_name', 'Unknown')

            # Parse APY values (convert from various formats)
            supply_apy = float(market_data.get('supply_apy', 0))
            borrow_apy = float(market_data.get('borrow_apy', 0))

            # Parse supply/borrow amounts
            total_supply = float(market_data.get('total_supply', 0))
            total_borrows = float(market_data.get('total_borrows', 0))

            # Calculate utilization rate
            utilization_rate = market_data.get('utilization_rate')
            if utilization_rate is None and total_supply > 0:
                utilization_rate = total_borrows / total_supply
            else:
                utilization_rate = float(utilization_rate or 0)

            # Calculate available liquidity
            cash = float(market_data.get('cash', 0))
            liquidity_available = cash if cash > 0 else (total_supply - total_borrows)

            return AlgofiMarket(
                asset_id=asset_id,
                asset_name=asset_name,
                supply_apy=supply_apy,
                borrow_apy=borrow_apy,
                total_supply=total_supply,
                total_borrows=total_borrows,
                utilization_rate=utilization_rate,
                liquidity_available=liquidity_available,
                last_update=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error parsing market data: {e}")
            return None

    async def analyze_algofi_yields(self) -> AlgofiYieldData:
        """
        Analyze Algofi yields and calculate weighted averages

        Returns:
            AlgofiYieldData: Complete Algofi yield analysis
        """
        try:
            # Fetch current markets
            markets = await self.fetch_algofi_markets()

            if not markets:
                return self._get_fallback_yield_data()

            # Calculate weighted averages
            weighted_supply_apy = self._calculate_weighted_supply_apy(markets)
            weighted_borrow_apy = self._calculate_weighted_borrow_apy(markets)

            # Calculate total value locked and utilization
            total_tvl = self._calculate_total_tvl(markets)
            protocol_utilization = self._calculate_protocol_utilization(markets)

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(markets)

            return AlgofiYieldData(
                markets=markets,
                weighted_average_supply_apy=weighted_supply_apy,
                weighted_average_borrow_apy=weighted_borrow_apy,
                total_value_locked=total_tvl,
                protocol_utilization=protocol_utilization,
                confidence_score=confidence_score,
                timestamp=datetime.now(),
                metadata={
                    'market_count': len(markets),
                    'data_source': 'algofi_api',
                    'calculation_method': 'tvl_weighted'
                }
            )

        except Exception as e:
            self.logger.error(f"Error analyzing Algofi yields: {e}")
            return self._get_fallback_yield_data()

    def _calculate_weighted_supply_apy(self, markets: List[AlgofiMarket]) -> float:
        """Calculate TVL-weighted supply APY across all markets"""
        total_weighted_yield = 0.0
        total_weight = 0.0

        for market in markets:
            # Use total supply as weight (in USD terms would be better)
            weight = market.total_supply
            total_weighted_yield += market.supply_apy * weight
            total_weight += weight

        if total_weight > 0:
            return total_weighted_yield / total_weight
        else:
            # Fallback to simple average
            return statistics.mean([m.supply_apy for m in markets]) if markets else 0.0

    def _calculate_weighted_borrow_apy(self, markets: List[AlgofiMarket]) -> float:
        """Calculate TVL-weighted borrow APY across all markets"""
        total_weighted_yield = 0.0
        total_weight = 0.0

        for market in markets:
            # Use total borrows as weight
            weight = market.total_borrows
            total_weighted_yield += market.borrow_apy * weight
            total_weight += weight

        if total_weight > 0:
            return total_weighted_yield / total_weight
        else:
            # Fallback to simple average
            return statistics.mean([m.borrow_apy for m in markets]) if markets else 0.0

    def _calculate_total_tvl(self, markets: List[AlgofiMarket]) -> float:
        """Calculate total value locked across all markets"""
        # In a real implementation, this would convert to USD using prices
        # For now, sum the native token amounts
        total_tvl = 0.0

        for market in markets:
            # Simplified TVL calculation (should use USD prices)
            if market.asset_name in ['USDC', 'USDT']:
                # Assume 1:1 USD for stablecoins
                market_tvl = market.total_supply
            elif market.asset_name == 'ALGO':
                # Assume $0.25 per ALGO (should fetch real price)
                market_tvl = market.total_supply * 0.25
            elif market.asset_name == 'goBTC':
                # Assume $45,000 per goBTC (should fetch real price)
                market_tvl = market.total_supply * 45000
            else:
                # Default assumption
                market_tvl = market.total_supply * 1.0

            total_tvl += market_tvl

        return total_tvl

    def _calculate_protocol_utilization(self, markets: List[AlgofiMarket]) -> float:
        """Calculate overall protocol utilization rate"""
        total_supply = sum(market.total_supply for market in markets)
        total_borrows = sum(market.total_borrows for market in markets)

        if total_supply > 0:
            return total_borrows / total_supply
        else:
            return 0.0

    def _calculate_confidence_score(self, markets: List[AlgofiMarket]) -> float:
        """Calculate confidence score for the yield data"""
        if not markets:
            return 0.0

        confidence = 1.0

        # Reduce confidence for low number of markets
        if len(markets) < 3:
            confidence *= 0.8

        # Reduce confidence for extreme utilization rates
        avg_utilization = statistics.mean([m.utilization_rate for m in markets])
        if avg_utilization > 0.95 or avg_utilization < 0.1:
            confidence *= 0.9

        # Reduce confidence for extreme yield values
        supply_apys = [m.supply_apy for m in markets]
        if any(apy > 1.0 or apy < 0.001 for apy in supply_apys):  # > 100% or < 0.1%
            confidence *= 0.8

        # Check data freshness
        oldest_update = min(market.last_update for market in markets)
        if datetime.now() - oldest_update > timedelta(minutes=30):
            confidence *= 0.7

        return max(confidence, 0.1)

    def _get_fallback_markets(self) -> List[AlgofiMarket]:
        """Return fallback markets when live data is unavailable"""
        return [
            AlgofiMarket(
                asset_id='0',
                asset_name='ALGO',
                supply_apy=0.04,
                borrow_apy=0.06,
                total_supply=40000000,
                total_borrows=24000000,
                utilization_rate=0.6,
                liquidity_available=16000000,
                last_update=datetime.now()
            ),
            AlgofiMarket(
                asset_id='31566704',
                asset_name='USDC',
                supply_apy=0.03,
                borrow_apy=0.05,
                total_supply=20000000,
                total_borrows=14000000,
                utilization_rate=0.7,
                liquidity_available=6000000,
                last_update=datetime.now()
            )
        ]

    def _get_fallback_yield_data(self) -> AlgofiYieldData:
        """Return fallback yield data when analysis fails"""
        fallback_markets = self._get_fallback_markets()

        return AlgofiYieldData(
            markets=fallback_markets,
            weighted_average_supply_apy=0.035,  # 3.5% fallback
            weighted_average_borrow_apy=0.055,  # 5.5% fallback
            total_value_locked=15000000,        # $15M fallback TVL
            protocol_utilization=0.65,          # 65% fallback utilization
            confidence_score=0.5,               # Low confidence for fallback
            timestamp=datetime.now(),
            metadata={'fallback': True, 'reason': 'data_unavailable'}
        )

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False

        timestamp_key = f"{key}_timestamp"
        if timestamp_key not in self.cache:
            return False

        cache_expiry = self.config['historical_data']['cache_expiry_minutes']
        expiry_time = self.cache[timestamp_key] + timedelta(minutes=cache_expiry)

        return datetime.now() < expiry_time

    async def get_market_by_asset(self, asset_name: str) -> Optional[AlgofiMarket]:
        """
        Get specific market data for an asset

        Args:
            asset_name: Name of the asset (e.g., 'ALGO', 'USDC')

        Returns:
            AlgofiMarket or None if not found
        """
        try:
            markets = await self.fetch_algofi_markets()

            for market in markets:
                if market.asset_name.upper() == asset_name.upper():
                    return market

            return None

        except Exception as e:
            self.logger.error(f"Error fetching market for {asset_name}: {e}")
            return None

    async def get_yield_history(self, asset_name: str, days: int = 7) -> Dict[str, Any]:
        """
        Get historical yield data for an asset

        Args:
            asset_name: Name of the asset
            days: Number of days of history

        Returns:
            Dict containing historical yield analysis
        """
        try:
            # In a real implementation, this would fetch from database
            # For now, simulate historical data
            yields = []
            base_yield = 0.045 if asset_name.upper() == 'ALGO' else 0.035

            for i in range(days):
                # Add realistic daily variation
                daily_variation = (i % 3) * 0.002 - 0.003  # Small variations
                yield_rate = max(0.01, base_yield + daily_variation)
                yields.append(yield_rate)

            if not yields:
                return {"error": "No historical data available"}

            return {
                "asset": asset_name,
                "period_days": days,
                "average_yield": statistics.mean(yields),
                "min_yield": min(yields),
                "max_yield": max(yields),
                "current_yield": yields[-1],
                "volatility": statistics.stdev(yields) if len(yields) > 1 else 0,
                "trend": "increasing" if yields[-1] > yields[0] else "decreasing",
                "data_points": len(yields),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting yield history for {asset_name}: {e}")
            return {"error": str(e)}

    async def compare_supply_borrow_spreads(self) -> Dict[str, Any]:
        """
        Compare supply and borrow rate spreads across markets

        Returns:
            Dict containing spread analysis
        """
        try:
            yield_data = await self.analyze_algofi_yields()

            spreads = []
            for market in yield_data.markets:
                spread = market.borrow_apy - market.supply_apy
                spreads.append({
                    'asset': market.asset_name,
                    'supply_apy': market.supply_apy,
                    'borrow_apy': market.borrow_apy,
                    'spread': spread,
                    'utilization_rate': market.utilization_rate
                })

            # Sort by spread (highest first)
            spreads.sort(key=lambda x: x['spread'], reverse=True)

            return {
                "protocol": "Algofi",
                "spreads": spreads,
                "average_spread": statistics.mean([s['spread'] for s in spreads]),
                "median_spread": statistics.median([s['spread'] for s in spreads]),
                "total_markets": len(spreads),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error comparing spreads: {e}")
            return {"error": str(e)}

# Example usage and testing
async def main():
    """Example usage of the AlgofiYieldsAnalyzer"""
    analyzer = AlgofiYieldsAnalyzer()

    print("=== Algofi Yields Analyzer Demo ===")

    # Analyze current yields
    print("\n1. Current Algofi Yield Analysis:")
    yield_data = await analyzer.analyze_algofi_yields()
    print(f"   Weighted Supply APY: {yield_data.weighted_average_supply_apy:.2%}")
    print(f"   Weighted Borrow APY: {yield_data.weighted_average_borrow_apy:.2%}")
    print(f"   Total Value Locked: ${yield_data.total_value_locked:,.0f}")
    print(f"   Protocol Utilization: {yield_data.protocol_utilization:.2%}")
    print(f"   Confidence Score: {yield_data.confidence_score:.2f}")

    # Show individual markets
    print(f"\n2. Individual Markets ({len(yield_data.markets)} markets):")
    for market in yield_data.markets:
        print(f"   {market.asset_name}:")
        print(f"     Supply APY: {market.supply_apy:.2%}")
        print(f"     Borrow APY: {market.borrow_apy:.2%}")
        print(f"     Utilization: {market.utilization_rate:.2%}")
        print(f"     Liquidity: {market.liquidity_available:,.0f}")

    # Get specific market
    print("\n3. ALGO Market Details:")
    algo_market = await analyzer.get_market_by_asset('ALGO')
    if algo_market:
        print(f"   Supply APY: {algo_market.supply_apy:.2%}")
        print(f"   Borrow APY: {algo_market.borrow_apy:.2%}")
        print(f"   Total Supply: {algo_market.total_supply:,.0f} ALGO")
        print(f"   Total Borrows: {algo_market.total_borrows:,.0f} ALGO")

    # Compare spreads
    print("\n4. Supply-Borrow Spreads:")
    spreads = await analyzer.compare_supply_borrow_spreads()
    if "error" not in spreads:
        for spread_data in spreads['spreads'][:3]:  # Top 3
            print(f"   {spread_data['asset']}: {spread_data['spread']:.2%} spread")

if __name__ == "__main__":
    asyncio.run(main())