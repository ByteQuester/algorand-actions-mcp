"""
ASA Volatility Analysis Engine
Analyzes price volatility, volume patterns, and market behavior of Algorand Standard Assets.
"""

import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
import math
import numpy as np

from algosdk.v2client import algod, indexer


@dataclass
class PriceData:
    """Price data point"""
    timestamp: datetime
    price_usd: float
    price_algo: float
    volume_24h: float
    market_cap: float
    source: str


@dataclass
class VolatilityMetrics:
    """Volatility analysis metrics"""
    asset_id: int
    asset_name: str
    current_price: float

    # Volatility measures
    daily_volatility: float
    weekly_volatility: float
    monthly_volatility: float

    # Price statistics
    price_range_7d: float
    price_range_30d: float
    max_drawdown: float

    # Volume analysis
    volume_volatility: float
    avg_daily_volume: float
    volume_trend: str

    # Risk metrics
    var_95: float                    # Value at Risk (95% confidence)
    sharpe_ratio: float
    volatility_score: float


@dataclass
class VolatilityComparison:
    """Comparison with market benchmarks"""
    asset_volatility: float
    algo_volatility: float
    market_average: float
    relative_volatility: float       # Compared to ALGO
    volatility_rank: int             # Percentile rank
    stability_score: float


class ASAVolatilityAnalyzer:
    """Analyzes ASA price volatility and market behavior"""

    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize clients
        self.indexer_client = indexer.IndexerClient(
            indexer_token="",
            indexer_address=config['algorand_config']['indexer']['url']
        )

        self.algod_client = algod.AlgodClient(
            algod_token="",
            algod_address=config['algorand_config']['node']['url']
        )

        # Volatility configuration
        self.volatility_config = config['volatility_analysis']
        self.dex_config = config['dex_config']

    async def analyze_asa_volatility(self, asset_id: int) -> VolatilityMetrics:
        """Perform comprehensive volatility analysis for an ASA"""
        try:
            self.logger.info(f"Analyzing volatility for ASA {asset_id}")

            # Get asset information
            asset_info = await self._get_asset_info(asset_id)
            if not asset_info:
                raise ValueError(f"Could not retrieve asset info for {asset_id}")

            # Gather price data from multiple sources
            price_data = await self._collect_price_data(asset_id)

            if len(price_data) < 7:  # Need at least 7 days of data
                self.logger.warning(f"Insufficient price data for {asset_id}")
                return self._create_default_metrics(asset_id, asset_info)

            # Calculate volatility metrics
            volatility_metrics = await self._calculate_volatility_metrics(
                asset_id, asset_info, price_data
            )

            return volatility_metrics

        except Exception as e:
            self.logger.error(f"Error analyzing volatility for ASA {asset_id}: {e}")
            raise

    async def compare_volatility_to_market(self, asset_id: int) -> VolatilityComparison:
        """Compare ASA volatility to market benchmarks"""
        try:
            # Get asset volatility
            asset_metrics = await self.analyze_asa_volatility(asset_id)

            # Get ALGO volatility as benchmark
            algo_volatility = await self._get_algo_volatility()

            # Calculate market average (simplified)
            market_average = await self._get_market_average_volatility()

            # Calculate relative metrics
            relative_volatility = asset_metrics.daily_volatility / max(algo_volatility, 0.01)

            # Determine stability score
            stability_score = self._calculate_stability_score(
                asset_metrics.daily_volatility, algo_volatility, market_average
            )

            return VolatilityComparison(
                asset_volatility=asset_metrics.daily_volatility,
                algo_volatility=algo_volatility,
                market_average=market_average,
                relative_volatility=relative_volatility,
                volatility_rank=50,  # Placeholder - would calculate from larger dataset
                stability_score=stability_score
            )

        except Exception as e:
            self.logger.error(f"Error comparing volatility for ASA {asset_id}: {e}")
            raise

    async def _collect_price_data(self, asset_id: int) -> List[PriceData]:
        """Collect price data from multiple DEX sources"""
        try:
            price_data = []

            # Collect from Tinyman
            tinyman_data = await self._get_tinyman_price_data(asset_id)
            price_data.extend(tinyman_data)

            # Collect from other DEXes (parallel)
            dex_tasks = [
                self._get_algofi_price_data(asset_id),
                self._get_pact_price_data(asset_id),
            ]

            additional_data = await asyncio.gather(*dex_tasks, return_exceptions=True)

            for data in additional_data:
                if isinstance(data, list):
                    price_data.extend(data)

            # Sort by timestamp
            price_data.sort(key=lambda x: x.timestamp)

            # Remove duplicates and outliers
            price_data = self._clean_price_data(price_data)

            return price_data

        except Exception as e:
            self.logger.error(f"Error collecting price data for {asset_id}: {e}")
            return []

    async def _get_tinyman_price_data(self, asset_id: int) -> List[PriceData]:
        """Get price data from Tinyman DEX"""
        try:
            price_data = []
            url = f"{self.dex_config['tinyman']['api_url']}/api/v1/assets/{asset_id}/price"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Parse Tinyman response format
                        if 'price_history' in data:
                            for entry in data['price_history']:
                                price_data.append(PriceData(
                                    timestamp=datetime.fromtimestamp(entry['timestamp']),
                                    price_usd=entry.get('price_usd', 0),
                                    price_algo=entry.get('price_algo', 0),
                                    volume_24h=entry.get('volume_24h', 0),
                                    market_cap=entry.get('market_cap', 0),
                                    source='tinyman'
                                ))

            return price_data

        except Exception as e:
            self.logger.error(f"Error getting Tinyman data for {asset_id}: {e}")
            return []

    async def _get_algofi_price_data(self, asset_id: int) -> List[PriceData]:
        """Get price data from AlgoFi"""
        try:
            price_data = []
            # Implementation would connect to AlgoFi API
            # For now, return empty list
            return price_data

        except Exception as e:
            self.logger.error(f"Error getting AlgoFi data for {asset_id}: {e}")
            return []

    async def _get_pact_price_data(self, asset_id: int) -> List[PriceData]:
        """Get price data from Pact"""
        try:
            price_data = []
            # Implementation would connect to Pact API
            # For now, return empty list
            return price_data

        except Exception as e:
            self.logger.error(f"Error getting Pact data for {asset_id}: {e}")
            return []

    def _clean_price_data(self, price_data: List[PriceData]) -> List[PriceData]:
        """Remove outliers and invalid data points"""
        if not price_data:
            return []

        # Remove zero prices
        price_data = [p for p in price_data if p.price_usd > 0]

        if len(price_data) < 2:
            return price_data

        # Remove extreme outliers (more than 3 standard deviations)
        prices = [p.price_usd for p in price_data]
        mean_price = statistics.mean(prices)
        std_price = statistics.stdev(prices) if len(prices) > 1 else 0

        if std_price > 0:
            cleaned_data = []
            for point in price_data:
                z_score = abs((point.price_usd - mean_price) / std_price)
                if z_score <= 3:  # Keep points within 3 standard deviations
                    cleaned_data.append(point)

            return cleaned_data if cleaned_data else price_data[:1]  # Keep at least one point

        return price_data

    async def _calculate_volatility_metrics(
        self, asset_id: int, asset_info: Dict, price_data: List[PriceData]
    ) -> VolatilityMetrics:
        """Calculate comprehensive volatility metrics"""
        try:
            asset_name = asset_info.get('params', {}).get('name', f'ASA-{asset_id}')
            current_price = price_data[-1].price_usd if price_data else 0

            # Calculate price returns
            returns = self._calculate_returns(price_data)

            # Calculate volatility measures
            daily_volatility = self._calculate_daily_volatility(returns)
            weekly_volatility = daily_volatility * math.sqrt(7)
            monthly_volatility = daily_volatility * math.sqrt(30)

            # Calculate price ranges
            prices_7d = [p.price_usd for p in price_data[-7:]]
            prices_30d = [p.price_usd for p in price_data[-30:]]

            price_range_7d = (max(prices_7d) - min(prices_7d)) / min(prices_7d) if prices_7d else 0
            price_range_30d = (max(prices_30d) - min(prices_30d)) / min(prices_30d) if prices_30d else 0

            # Calculate maximum drawdown
            max_drawdown = self._calculate_max_drawdown(price_data)

            # Volume analysis
            volumes = [p.volume_24h for p in price_data if p.volume_24h > 0]
            volume_volatility = statistics.stdev(volumes) / statistics.mean(volumes) if len(volumes) > 1 else 0
            avg_daily_volume = statistics.mean(volumes) if volumes else 0
            volume_trend = self._analyze_volume_trend(price_data)

            # Risk metrics
            var_95 = self._calculate_var(returns, 0.95)
            sharpe_ratio = self._calculate_sharpe_ratio(returns, daily_volatility)

            # Overall volatility score
            volatility_score = self._calculate_volatility_score(
                daily_volatility, volume_volatility, max_drawdown
            )

            return VolatilityMetrics(
                asset_id=asset_id,
                asset_name=asset_name,
                current_price=current_price,
                daily_volatility=daily_volatility,
                weekly_volatility=weekly_volatility,
                monthly_volatility=monthly_volatility,
                price_range_7d=price_range_7d,
                price_range_30d=price_range_30d,
                max_drawdown=max_drawdown,
                volume_volatility=volume_volatility,
                avg_daily_volume=avg_daily_volume,
                volume_trend=volume_trend,
                var_95=var_95,
                sharpe_ratio=sharpe_ratio,
                volatility_score=volatility_score
            )

        except Exception as e:
            self.logger.error(f"Error calculating volatility metrics: {e}")
            raise

    def _calculate_returns(self, price_data: List[PriceData]) -> List[float]:
        """Calculate price returns"""
        if len(price_data) < 2:
            return []

        returns = []
        for i in range(1, len(price_data)):
            if price_data[i-1].price_usd > 0:
                return_val = (price_data[i].price_usd - price_data[i-1].price_usd) / price_data[i-1].price_usd
                returns.append(return_val)

        return returns

    def _calculate_daily_volatility(self, returns: List[float]) -> float:
        """Calculate daily volatility (standard deviation of returns)"""
        if len(returns) < 2:
            return 0.0

        return statistics.stdev(returns)

    def _calculate_max_drawdown(self, price_data: List[PriceData]) -> float:
        """Calculate maximum drawdown from peak"""
        if len(price_data) < 2:
            return 0.0

        prices = [p.price_usd for p in price_data]
        peak = prices[0]
        max_drawdown = 0.0

        for price in prices[1:]:
            if price > peak:
                peak = price
            else:
                drawdown = (peak - price) / peak
                max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _analyze_volume_trend(self, price_data: List[PriceData]) -> str:
        """Analyze volume trend direction"""
        if len(price_data) < 5:
            return "insufficient_data"

        recent_volumes = [p.volume_24h for p in price_data[-5:]]
        older_volumes = [p.volume_24h for p in price_data[-10:-5]] if len(price_data) >= 10 else recent_volumes

        recent_avg = statistics.mean(recent_volumes) if recent_volumes else 0
        older_avg = statistics.mean(older_volumes) if older_volumes else 0

        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        else:
            return "stable"

    def _calculate_var(self, returns: List[float], confidence: float) -> float:
        """Calculate Value at Risk"""
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return abs(sorted_returns[index]) if index < len(sorted_returns) else 0.0

    def _calculate_sharpe_ratio(self, returns: List[float], volatility: float) -> float:
        """Calculate Sharpe ratio (assuming 0 risk-free rate)"""
        if not returns or volatility == 0:
            return 0.0

        mean_return = statistics.mean(returns)
        return mean_return / volatility

    def _calculate_volatility_score(self, daily_vol: float, volume_vol: float, max_dd: float) -> float:
        """Calculate overall volatility score (0-1, lower is better)"""
        thresholds = self.volatility_config['volatility_thresholds']

        # Score daily volatility
        if daily_vol <= thresholds['very_low']:
            vol_score = 0.1
        elif daily_vol <= thresholds['low']:
            vol_score = 0.3
        elif daily_vol <= thresholds['medium']:
            vol_score = 0.5
        elif daily_vol <= thresholds['high']:
            vol_score = 0.7
        else:
            vol_score = 1.0

        # Score volume volatility
        volume_score = min(1.0, volume_vol / 0.5)  # Normalize to 50% volume volatility

        # Score maximum drawdown
        drawdown_score = min(1.0, max_dd / 0.5)  # Normalize to 50% drawdown

        # Weighted combination
        overall_score = (vol_score * 0.5 + volume_score * 0.25 + drawdown_score * 0.25)

        return min(1.0, max(0.0, overall_score))

    async def _get_asset_info(self, asset_id: int) -> Optional[Dict]:
        """Get asset information from Algorand"""
        try:
            return self.algod_client.asset_info(asset_id)
        except Exception as e:
            self.logger.error(f"Error getting asset info for {asset_id}: {e}")
            return None

    async def _get_algo_volatility(self) -> float:
        """Get ALGO volatility as benchmark"""
        try:
            # This would fetch ALGO price data and calculate volatility
            # For now, return a typical ALGO volatility estimate
            return 0.25  # 25% daily volatility estimate

        except Exception as e:
            self.logger.error(f"Error getting ALGO volatility: {e}")
            return 0.25

    async def _get_market_average_volatility(self) -> float:
        """Get market average volatility"""
        try:
            # This would calculate average volatility across major ASAs
            # For now, return an estimate
            return 0.35  # 35% average daily volatility estimate

        except Exception as e:
            self.logger.error(f"Error getting market average volatility: {e}")
            return 0.35

    def _calculate_stability_score(self, asset_vol: float, algo_vol: float, market_avg: float) -> float:
        """Calculate stability score compared to benchmarks"""
        # Score based on relative volatility to ALGO and market
        relative_to_algo = asset_vol / max(algo_vol, 0.01)
        relative_to_market = asset_vol / max(market_avg, 0.01)

        # Lower relative volatility = higher stability score
        if relative_to_algo <= 0.5:  # Much more stable than ALGO
            algo_score = 1.0
        elif relative_to_algo <= 1.0:  # Similar to ALGO
            algo_score = 0.8
        elif relative_to_algo <= 1.5:  # Somewhat more volatile
            algo_score = 0.6
        elif relative_to_algo <= 2.0:  # Much more volatile
            algo_score = 0.4
        else:  # Extremely volatile
            algo_score = 0.2

        # Similar scoring for market comparison
        if relative_to_market <= 0.5:
            market_score = 1.0
        elif relative_to_market <= 1.0:
            market_score = 0.8
        elif relative_to_market <= 1.5:
            market_score = 0.6
        elif relative_to_market <= 2.0:
            market_score = 0.4
        else:
            market_score = 0.2

        # Combined stability score
        return (algo_score + market_score) / 2

    def _create_default_metrics(self, asset_id: int, asset_info: Dict) -> VolatilityMetrics:
        """Create default metrics for assets with insufficient data"""
        asset_name = asset_info.get('params', {}).get('name', f'ASA-{asset_id}')

        return VolatilityMetrics(
            asset_id=asset_id,
            asset_name=asset_name,
            current_price=0.0,
            daily_volatility=1.0,  # Maximum volatility for no data
            weekly_volatility=1.0,
            monthly_volatility=1.0,
            price_range_7d=0.0,
            price_range_30d=0.0,
            max_drawdown=0.0,
            volume_volatility=1.0,
            avg_daily_volume=0.0,
            volume_trend="insufficient_data",
            var_95=0.0,
            sharpe_ratio=0.0,
            volatility_score=1.0  # Worst score for no data
        )

    async def analyze_correlation_risk(self, asset_ids: List[int]) -> Dict[int, Dict[int, float]]:
        """Analyze correlation risk between multiple ASAs"""
        try:
            correlation_matrix = {}

            # Get price data for all assets
            price_data_dict = {}
            for asset_id in asset_ids:
                price_data_dict[asset_id] = await self._collect_price_data(asset_id)

            # Calculate correlations
            for i, asset1 in enumerate(asset_ids):
                correlation_matrix[asset1] = {}
                for j, asset2 in enumerate(asset_ids):
                    if i == j:
                        correlation_matrix[asset1][asset2] = 1.0
                    else:
                        corr = self._calculate_correlation(
                            price_data_dict.get(asset1, []),
                            price_data_dict.get(asset2, [])
                        )
                        correlation_matrix[asset1][asset2] = corr

            return correlation_matrix

        except Exception as e:
            self.logger.error(f"Error analyzing correlation risk: {e}")
            return {}

    def _calculate_correlation(self, data1: List[PriceData], data2: List[PriceData]) -> float:
        """Calculate correlation between two price series"""
        if not data1 or not data2:
            return 0.0

        # Align data by timestamp
        prices1, prices2 = self._align_price_series(data1, data2)

        if len(prices1) < 2 or len(prices2) < 2:
            return 0.0

        # Calculate returns
        returns1 = [(prices1[i] - prices1[i-1]) / prices1[i-1] for i in range(1, len(prices1))]
        returns2 = [(prices2[i] - prices2[i-1]) / prices2[i-1] for i in range(1, len(prices2))]

        if len(returns1) < 2:
            return 0.0

        # Calculate correlation coefficient
        try:
            correlation = np.corrcoef(returns1, returns2)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0
        except:
            return 0.0

    def _align_price_series(self, data1: List[PriceData], data2: List[PriceData]) -> Tuple[List[float], List[float]]:
        """Align two price series by timestamp"""
        # Create dictionaries for quick lookup
        prices1_dict = {d.timestamp: d.price_usd for d in data1}
        prices2_dict = {d.timestamp: d.price_usd for d in data2}

        # Find common timestamps
        common_timestamps = set(prices1_dict.keys()) & set(prices2_dict.keys())
        common_timestamps = sorted(common_timestamps)

        # Extract aligned prices
        aligned_prices1 = [prices1_dict[ts] for ts in common_timestamps]
        aligned_prices2 = [prices2_dict[ts] for ts in common_timestamps]

        return aligned_prices1, aligned_prices2