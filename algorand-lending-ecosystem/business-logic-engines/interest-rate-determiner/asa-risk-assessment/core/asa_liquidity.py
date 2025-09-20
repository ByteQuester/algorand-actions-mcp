"""
ASA Liquidity Analysis Engine
Analyzes trading volume, market depth, and liquidity characteristics of Algorand Standard Assets.
"""

import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics

from algosdk.v2client import algod, indexer


@dataclass
class LiquidityPool:
    """Liquidity pool information"""
    dex_name: str
    pool_address: str
    asset1_id: int
    asset2_id: int
    asset1_reserves: float
    asset2_reserves: float
    total_liquidity_usd: float
    volume_24h: float
    fees_24h: float
    apr: float


@dataclass
class MarketDepth:
    """Market depth analysis"""
    bid_depth_1_percent: float      # Liquidity within 1% of current price
    ask_depth_1_percent: float
    bid_depth_5_percent: float      # Liquidity within 5% of current price
    ask_depth_5_percent: float
    total_depth: float
    depth_imbalance: float          # Ratio of bid to ask depth


@dataclass
class TradingMetrics:
    """Trading activity metrics"""
    volume_24h: float
    volume_7d: float
    volume_30d: float
    trade_count_24h: int
    avg_trade_size: float
    largest_trade_24h: float
    volume_trend: str


@dataclass
class LiquidityMetrics:
    """Comprehensive liquidity analysis"""
    asset_id: int
    asset_name: str

    # Trading metrics
    trading_metrics: TradingMetrics

    # Market depth
    market_depth: MarketDepth

    # Liquidity pools
    pools: List[LiquidityPool]
    total_pool_liquidity: float

    # Spread analysis
    bid_ask_spread: float
    average_spread_24h: float
    spread_volatility: float

    # Market makers
    active_market_makers: int
    market_maker_concentration: float

    # Liquidity scores
    volume_score: float
    depth_score: float
    spread_score: float
    overall_liquidity_score: float

    # Risk indicators
    liquidity_risk_level: str
    slippage_1_percent: float        # Expected slippage for 1% of daily volume
    slippage_5_percent: float        # Expected slippage for 5% of daily volume


class ASALiquidityAnalyzer:
    """Analyzes ASA liquidity characteristics"""

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

        # Configuration
        self.liquidity_config = config['liquidity_analysis']
        self.dex_config = config['dex_config']

    async def analyze_asa_liquidity(self, asset_id: int) -> LiquidityMetrics:
        """Perform comprehensive liquidity analysis for an ASA"""
        try:
            self.logger.info(f"Analyzing liquidity for ASA {asset_id}")

            # Get asset information
            asset_info = await self._get_asset_info(asset_id)
            if not asset_info:
                raise ValueError(f"Could not retrieve asset info for {asset_id}")

            asset_name = asset_info.get('params', {}).get('name', f'ASA-{asset_id}')

            # Run parallel analysis
            results = await asyncio.gather(
                self._analyze_trading_metrics(asset_id),
                self._analyze_market_depth(asset_id),
                self._analyze_liquidity_pools(asset_id),
                self._analyze_spread_metrics(asset_id),
                self._analyze_market_makers(asset_id),
                return_exceptions=True
            )

            # Extract results
            trading_metrics = results[0] if not isinstance(results[0], Exception) else self._default_trading_metrics()
            market_depth = results[1] if not isinstance(results[1], Exception) else self._default_market_depth()
            pools = results[2] if not isinstance(results[2], Exception) else []
            spread_metrics = results[3] if not isinstance(results[3], Exception) else (0.1, 0.1, 0.5)  # spread, avg_spread, volatility
            market_maker_info = results[4] if not isinstance(results[4], Exception) else (0, 1.0)  # count, concentration

            # Calculate derived metrics
            total_pool_liquidity = sum(pool.total_liquidity_usd for pool in pools)
            bid_ask_spread, average_spread_24h, spread_volatility = spread_metrics
            active_market_makers, market_maker_concentration = market_maker_info

            # Calculate liquidity scores
            volume_score = self._calculate_volume_score(trading_metrics)
            depth_score = self._calculate_depth_score(market_depth)
            spread_score = self._calculate_spread_score(bid_ask_spread, average_spread_24h)

            # Overall liquidity score
            overall_score = self._calculate_overall_liquidity_score(
                volume_score, depth_score, spread_score, len(pools)
            )

            # Determine risk level
            liquidity_risk_level = self._determine_liquidity_risk_level(overall_score)

            # Calculate slippage estimates
            slippage_1_percent = self._estimate_slippage(trading_metrics.volume_24h * 0.01, market_depth)
            slippage_5_percent = self._estimate_slippage(trading_metrics.volume_24h * 0.05, market_depth)

            return LiquidityMetrics(
                asset_id=asset_id,
                asset_name=asset_name,
                trading_metrics=trading_metrics,
                market_depth=market_depth,
                pools=pools,
                total_pool_liquidity=total_pool_liquidity,
                bid_ask_spread=bid_ask_spread,
                average_spread_24h=average_spread_24h,
                spread_volatility=spread_volatility,
                active_market_makers=active_market_makers,
                market_maker_concentration=market_maker_concentration,
                volume_score=volume_score,
                depth_score=depth_score,
                spread_score=spread_score,
                overall_liquidity_score=overall_score,
                liquidity_risk_level=liquidity_risk_level,
                slippage_1_percent=slippage_1_percent,
                slippage_5_percent=slippage_5_percent
            )

        except Exception as e:
            self.logger.error(f"Error analyzing liquidity for ASA {asset_id}: {e}")
            raise

    async def _analyze_trading_metrics(self, asset_id: int) -> TradingMetrics:
        """Analyze trading volume and activity metrics"""
        try:
            # Get trading data from multiple DEXes
            trading_data = []

            # Tinyman data
            tinyman_data = await self._get_tinyman_trading_data(asset_id)
            trading_data.extend(tinyman_data)

            # Other DEX data (parallel)
            dex_tasks = [
                self._get_algofi_trading_data(asset_id),
                self._get_pact_trading_data(asset_id),
            ]

            additional_data = await asyncio.gather(*dex_tasks, return_exceptions=True)
            for data in additional_data:
                if isinstance(data, list):
                    trading_data.extend(data)

            if not trading_data:
                return self._default_trading_metrics()

            # Aggregate metrics
            current_time = datetime.utcnow()
            day_ago = current_time - timedelta(days=1)
            week_ago = current_time - timedelta(days=7)
            month_ago = current_time - timedelta(days=30)

            # Filter by time periods
            trades_24h = [t for t in trading_data if t['timestamp'] >= day_ago]
            trades_7d = [t for t in trading_data if t['timestamp'] >= week_ago]
            trades_30d = [t for t in trading_data if t['timestamp'] >= month_ago]

            # Calculate metrics
            volume_24h = sum(t['volume_usd'] for t in trades_24h)
            volume_7d = sum(t['volume_usd'] for t in trades_7d)
            volume_30d = sum(t['volume_usd'] for t in trades_30d)

            trade_count_24h = len(trades_24h)
            avg_trade_size = volume_24h / max(trade_count_24h, 1)
            largest_trade_24h = max([t['volume_usd'] for t in trades_24h], default=0)

            # Determine volume trend
            if len(trades_7d) >= 7:
                recent_avg = volume_24h
                older_avg = (volume_7d - volume_24h) / 6 if volume_7d > volume_24h else 0

                if recent_avg > older_avg * 1.2:
                    volume_trend = "increasing"
                elif recent_avg < older_avg * 0.8:
                    volume_trend = "decreasing"
                else:
                    volume_trend = "stable"
            else:
                volume_trend = "insufficient_data"

            return TradingMetrics(
                volume_24h=volume_24h,
                volume_7d=volume_7d,
                volume_30d=volume_30d,
                trade_count_24h=trade_count_24h,
                avg_trade_size=avg_trade_size,
                largest_trade_24h=largest_trade_24h,
                volume_trend=volume_trend
            )

        except Exception as e:
            self.logger.error(f"Error analyzing trading metrics: {e}")
            return self._default_trading_metrics()

    async def _analyze_market_depth(self, asset_id: int) -> MarketDepth:
        """Analyze market depth and order book"""
        try:
            # Get order book data from DEXes
            depth_data = await self._get_orderbook_data(asset_id)

            if not depth_data:
                return self._default_market_depth()

            # Aggregate depth from all sources
            total_bid_1 = sum(d['bid_depth_1_percent'] for d in depth_data)
            total_ask_1 = sum(d['ask_depth_1_percent'] for d in depth_data)
            total_bid_5 = sum(d['bid_depth_5_percent'] for d in depth_data)
            total_ask_5 = sum(d['ask_depth_5_percent'] for d in depth_data)

            total_depth = total_bid_1 + total_ask_1 + total_bid_5 + total_ask_5

            # Calculate depth imbalance
            total_bid = total_bid_1 + total_bid_5
            total_ask = total_ask_1 + total_ask_5

            if total_ask > 0:
                depth_imbalance = total_bid / total_ask
            else:
                depth_imbalance = 1.0 if total_bid > 0 else 0.0

            return MarketDepth(
                bid_depth_1_percent=total_bid_1,
                ask_depth_1_percent=total_ask_1,
                bid_depth_5_percent=total_bid_5,
                ask_depth_5_percent=total_ask_5,
                total_depth=total_depth,
                depth_imbalance=depth_imbalance
            )

        except Exception as e:
            self.logger.error(f"Error analyzing market depth: {e}")
            return self._default_market_depth()

    async def _analyze_liquidity_pools(self, asset_id: int) -> List[LiquidityPool]:
        """Analyze liquidity pools across DEXes"""
        try:
            pools = []

            # Get pools from different DEXes
            pool_tasks = [
                self._get_tinyman_pools(asset_id),
                self._get_algofi_pools(asset_id),
                self._get_pact_pools(asset_id),
            ]

            pool_results = await asyncio.gather(*pool_tasks, return_exceptions=True)

            for result in pool_results:
                if isinstance(result, list):
                    pools.extend(result)

            return pools

        except Exception as e:
            self.logger.error(f"Error analyzing liquidity pools: {e}")
            return []

    async def _analyze_spread_metrics(self, asset_id: int) -> Tuple[float, float, float]:
        """Analyze bid-ask spread metrics"""
        try:
            # Get spread data from DEXes
            spread_data = await self._get_spread_data(asset_id)

            if not spread_data:
                return 0.1, 0.1, 0.5  # Default high spreads

            # Calculate current spread (best available)
            current_spread = min(d['current_spread'] for d in spread_data)

            # Calculate average spread over 24h
            all_spreads = []
            for data in spread_data:
                all_spreads.extend(data.get('historical_spreads', []))

            if all_spreads:
                average_spread_24h = statistics.mean(all_spreads)
                spread_volatility = statistics.stdev(all_spreads) if len(all_spreads) > 1 else 0
            else:
                average_spread_24h = current_spread
                spread_volatility = 0.0

            return current_spread, average_spread_24h, spread_volatility

        except Exception as e:
            self.logger.error(f"Error analyzing spread metrics: {e}")
            return 0.1, 0.1, 0.5

    async def _analyze_market_makers(self, asset_id: int) -> Tuple[int, float]:
        """Analyze market maker presence and concentration"""
        try:
            # Get market maker data
            mm_data = await self._get_market_maker_data(asset_id)

            if not mm_data:
                return 0, 1.0

            active_makers = len(mm_data)

            # Calculate concentration (Herfindahl index)
            total_volume = sum(mm['volume_24h'] for mm in mm_data)

            if total_volume > 0:
                market_shares = [mm['volume_24h'] / total_volume for mm in mm_data]
                concentration = sum(share ** 2 for share in market_shares)
            else:
                concentration = 1.0

            return active_makers, concentration

        except Exception as e:
            self.logger.error(f"Error analyzing market makers: {e}")
            return 0, 1.0

    async def _get_tinyman_trading_data(self, asset_id: int) -> List[Dict]:
        """Get trading data from Tinyman"""
        try:
            trading_data = []
            url = f"{self.dex_config['tinyman']['api_url']}/api/v1/assets/{asset_id}/trades"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'trades' in data:
                            for trade in data['trades']:
                                trading_data.append({
                                    'timestamp': datetime.fromtimestamp(trade['timestamp']),
                                    'volume_usd': trade.get('volume_usd', 0),
                                    'price': trade.get('price', 0),
                                    'source': 'tinyman'
                                })

            return trading_data

        except Exception as e:
            self.logger.error(f"Error getting Tinyman trading data: {e}")
            return []

    async def _get_algofi_trading_data(self, asset_id: int) -> List[Dict]:
        """Get trading data from AlgoFi"""
        # Placeholder - would implement AlgoFi API integration
        return []

    async def _get_pact_trading_data(self, asset_id: int) -> List[Dict]:
        """Get trading data from Pact"""
        # Placeholder - would implement Pact API integration
        return []

    async def _get_orderbook_data(self, asset_id: int) -> List[Dict]:
        """Get order book depth data"""
        try:
            depth_data = []

            # Get from Algodex (has order book)
            algodex_url = f"{self.dex_config['algodex']['api_url']}/v1/orderbook/{asset_id}/0"

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(algodex_url, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Parse order book data
                            bids = data.get('bids', [])
                            asks = data.get('asks', [])

                            # Calculate depth within price ranges
                            if bids and asks:
                                best_bid = max(bids, key=lambda x: x['price'])['price']
                                best_ask = min(asks, key=lambda x: x['price'])['price']
                                mid_price = (best_bid + best_ask) / 2

                                bid_depth_1 = sum(
                                    order['amount'] * order['price']
                                    for order in bids
                                    if order['price'] >= mid_price * 0.99
                                )

                                ask_depth_1 = sum(
                                    order['amount'] * order['price']
                                    for order in asks
                                    if order['price'] <= mid_price * 1.01
                                )

                                bid_depth_5 = sum(
                                    order['amount'] * order['price']
                                    for order in bids
                                    if order['price'] >= mid_price * 0.95
                                )

                                ask_depth_5 = sum(
                                    order['amount'] * order['price']
                                    for order in asks
                                    if order['price'] <= mid_price * 1.05
                                )

                                depth_data.append({
                                    'bid_depth_1_percent': bid_depth_1,
                                    'ask_depth_1_percent': ask_depth_1,
                                    'bid_depth_5_percent': bid_depth_5,
                                    'ask_depth_5_percent': ask_depth_5,
                                    'source': 'algodex'
                                })

                except Exception as e:
                    self.logger.error(f"Error getting Algodex order book: {e}")

            return depth_data

        except Exception as e:
            self.logger.error(f"Error getting order book data: {e}")
            return []

    async def _get_tinyman_pools(self, asset_id: int) -> List[LiquidityPool]:
        """Get Tinyman liquidity pools"""
        try:
            pools = []
            url = f"{self.dex_config['tinyman']['api_url']}/api/v1/pools/"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'pools' in data:
                            for pool_data in data['pools']:
                                if (pool_data.get('asset_1_id') == asset_id or
                                    pool_data.get('asset_2_id') == asset_id):

                                    pools.append(LiquidityPool(
                                        dex_name='tinyman',
                                        pool_address=pool_data.get('address', ''),
                                        asset1_id=pool_data.get('asset_1_id', 0),
                                        asset2_id=pool_data.get('asset_2_id', 0),
                                        asset1_reserves=pool_data.get('asset_1_reserves', 0),
                                        asset2_reserves=pool_data.get('asset_2_reserves', 0),
                                        total_liquidity_usd=pool_data.get('liquidity_usd', 0),
                                        volume_24h=pool_data.get('volume_24h', 0),
                                        fees_24h=pool_data.get('fees_24h', 0),
                                        apr=pool_data.get('apr', 0)
                                    ))

            return pools

        except Exception as e:
            self.logger.error(f"Error getting Tinyman pools: {e}")
            return []

    async def _get_algofi_pools(self, asset_id: int) -> List[LiquidityPool]:
        """Get AlgoFi liquidity pools"""
        # Placeholder - would implement AlgoFi API integration
        return []

    async def _get_pact_pools(self, asset_id: int) -> List[LiquidityPool]:
        """Get Pact liquidity pools"""
        # Placeholder - would implement Pact API integration
        return []

    async def _get_spread_data(self, asset_id: int) -> List[Dict]:
        """Get spread data from DEXes"""
        # Placeholder - would implement spread data collection
        return []

    async def _get_market_maker_data(self, asset_id: int) -> List[Dict]:
        """Get market maker activity data"""
        # Placeholder - would implement market maker analysis
        return []

    def _calculate_volume_score(self, trading_metrics: TradingMetrics) -> float:
        """Calculate volume-based liquidity score"""
        volume_categories = self.liquidity_config['volume_categories']

        if trading_metrics.volume_24h >= volume_categories['large']:
            return 1.0
        elif trading_metrics.volume_24h >= volume_categories['medium']:
            return 0.8
        elif trading_metrics.volume_24h >= volume_categories['small']:
            return 0.6
        elif trading_metrics.volume_24h >= volume_categories['micro']:
            return 0.4
        elif trading_metrics.volume_24h >= volume_categories['nano']:
            return 0.2
        else:
            return 0.0

    def _calculate_depth_score(self, market_depth: MarketDepth) -> float:
        """Calculate depth-based liquidity score"""
        # Score based on total depth and balance
        if market_depth.total_depth >= 100000:  # $100k depth
            depth_score = 1.0
        elif market_depth.total_depth >= 50000:  # $50k depth
            depth_score = 0.8
        elif market_depth.total_depth >= 10000:  # $10k depth
            depth_score = 0.6
        elif market_depth.total_depth >= 1000:   # $1k depth
            depth_score = 0.4
        else:
            depth_score = 0.2

        # Penalty for imbalanced depth
        imbalance_penalty = abs(1.0 - market_depth.depth_imbalance) * 0.2
        return max(0.0, depth_score - imbalance_penalty)

    def _calculate_spread_score(self, current_spread: float, avg_spread: float) -> float:
        """Calculate spread-based liquidity score"""
        spread_thresholds = self.liquidity_config['spread_thresholds']

        # Use average spread for scoring
        if avg_spread <= spread_thresholds['tight']:
            return 1.0
        elif avg_spread <= spread_thresholds['normal']:
            return 0.8
        elif avg_spread <= spread_thresholds['wide']:
            return 0.6
        elif avg_spread <= spread_thresholds['very_wide']:
            return 0.4
        else:
            return 0.2

    def _calculate_overall_liquidity_score(
        self, volume_score: float, depth_score: float, spread_score: float, pool_count: int
    ) -> float:
        """Calculate overall liquidity score"""
        # Weighted combination
        weights = self.config['risk_assessment']['liquidity_weights']

        base_score = (
            volume_score * weights['trading_volume'] +
            depth_score * weights['market_makers'] +  # Using depth as proxy for market makers
            spread_score * weights['spread_analysis']
        )

        # Pool diversity bonus
        pool_bonus = min(0.2, pool_count * 0.05)  # Max 20% bonus for 4+ pools

        return min(1.0, base_score + pool_bonus)

    def _determine_liquidity_risk_level(self, score: float) -> str:
        """Determine liquidity risk level based on score"""
        if score >= 0.8:
            return "very_low"
        elif score >= 0.6:
            return "low"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "high"
        else:
            return "very_high"

    def _estimate_slippage(self, trade_size_usd: float, market_depth: MarketDepth) -> float:
        """Estimate slippage for a given trade size"""
        if market_depth.total_depth == 0:
            return 1.0  # 100% slippage if no depth

        # Simple linear model for slippage estimation
        slippage_factor = trade_size_usd / market_depth.total_depth

        # Non-linear slippage (gets worse with larger trades)
        estimated_slippage = slippage_factor * (1 + slippage_factor)

        return min(1.0, estimated_slippage)

    def _default_trading_metrics(self) -> TradingMetrics:
        """Default trading metrics for no data"""
        return TradingMetrics(
            volume_24h=0.0,
            volume_7d=0.0,
            volume_30d=0.0,
            trade_count_24h=0,
            avg_trade_size=0.0,
            largest_trade_24h=0.0,
            volume_trend="no_data"
        )

    def _default_market_depth(self) -> MarketDepth:
        """Default market depth for no data"""
        return MarketDepth(
            bid_depth_1_percent=0.0,
            ask_depth_1_percent=0.0,
            bid_depth_5_percent=0.0,
            ask_depth_5_percent=0.0,
            total_depth=0.0,
            depth_imbalance=0.0
        )

    async def _get_asset_info(self, asset_id: int) -> Optional[Dict]:
        """Get asset information from Algorand"""
        try:
            return self.algod_client.asset_info(asset_id)
        except Exception as e:
            self.logger.error(f"Error getting asset info for {asset_id}: {e}")
            return None