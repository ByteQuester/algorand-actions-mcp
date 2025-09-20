"""
Algorand Staking Engine

Calculates base interest rates from ALGO staking yields and network participation rewards.
Provides real-time and historical staking yield analysis for DeFi lending platforms.
"""

import asyncio
import logging
import aiohttp
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import statistics
import math

@dataclass
class StakingMetrics:
    """Represents current staking metrics from the Algorand network"""
    current_apy: float
    participation_rate: float
    total_stake: int
    online_stake: int
    rewards_per_round: int
    timestamp: datetime
    confidence_score: float

@dataclass
class BaseRateResult:
    """Result from base rate calculation"""
    base_rate: float
    staking_component: float
    participation_component: float
    governance_component: float
    network_security_component: float
    confidence_score: float
    timestamp: datetime
    metadata: Dict[str, Any]

class AlgoStakingEngine:
    """
    Engine for calculating base interest rates from Algorand staking yields.

    Analyzes ALGO staking rewards, consensus participation, and governance
    to determine risk-free base rates for DeFi lending protocols.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the staking engine with configuration"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.historical_data: List[StakingMetrics] = []
        self.cache = {}
        self.last_update = None

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
                'algo_staking': {
                    'base_reward_rate': 0.055,
                    'participation_threshold': 0.8,
                    'reward_period_seconds': 8
                },
                'mcp_services': {
                    'algorand_reader_url': 'http://localhost:8002'
                }
            }

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the engine"""
        logger = logging.getLogger('algo_staking_engine')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def get_current_staking_metrics(self) -> StakingMetrics:
        """
        Fetch current staking metrics from Algorand network

        Returns:
            StakingMetrics: Current network staking data
        """
        try:
            # Check cache first
            if self._is_cache_valid('staking_metrics'):
                return self.cache['staking_metrics']

            # Fetch from MCP service or direct API
            metrics = await self._fetch_network_metrics()

            # Calculate APY from metrics
            apy = self._calculate_staking_apy(metrics)

            result = StakingMetrics(
                current_apy=apy,
                participation_rate=metrics.get('participation_rate', 0.85),
                total_stake=metrics.get('total_stake', 0),
                online_stake=metrics.get('online_stake', 0),
                rewards_per_round=metrics.get('rewards_per_round', 0),
                timestamp=datetime.now(),
                confidence_score=self._calculate_confidence_score(metrics)
            )

            # Cache the result
            self.cache['staking_metrics'] = result
            self.cache['staking_metrics_timestamp'] = datetime.now()

            return result

        except Exception as e:
            self.logger.error(f"Error fetching staking metrics: {e}")
            return self._get_fallback_metrics()

    async def _fetch_network_metrics(self) -> Dict:
        """Fetch metrics from Algorand network via MCP or direct API"""
        try:
            # Try MCP service first
            mcp_url = self.config['mcp_services']['algorand_reader_url']
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{mcp_url}/network/status") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            self.logger.warning(f"MCP service unavailable, using direct API: {e}")

        # Fallback to direct Algorand API
        return await self._fetch_direct_algorand_metrics()

    async def _fetch_direct_algorand_metrics(self) -> Dict:
        """Fetch metrics directly from Algorand API"""
        try:
            algod_url = self.config.get('external_apis', {}).get(
                'algorand_node', 'https://mainnet-api.algonode.cloud'
            )

            async with aiohttp.ClientSession() as session:
                # Get network status
                async with session.get(f"{algod_url}/v2/status") as response:
                    status_data = await response.json()

                # Get supply information
                async with session.get(f"{algod_url}/v2/ledger/supply") as response:
                    supply_data = await response.json()

                # Calculate participation rate
                total_money = supply_data.get('total-money', 0)
                online_money = supply_data.get('online-money', 0)
                participation_rate = online_money / total_money if total_money > 0 else 0.85

                return {
                    'participation_rate': participation_rate,
                    'total_stake': total_money,
                    'online_stake': online_money,
                    'last_round': status_data.get('last-round', 0),
                    'rewards_per_round': self._estimate_rewards_per_round()
                }

        except Exception as e:
            self.logger.error(f"Error fetching direct Algorand metrics: {e}")
            return {}

    def _calculate_staking_apy(self, metrics: Dict) -> float:
        """Calculate current staking APY from network metrics"""
        try:
            base_rate = self.config['algo_staking']['base_reward_rate']
            participation_rate = metrics.get('participation_rate', 0.85)
            participation_threshold = self.config['algo_staking']['participation_threshold']

            # Adjust for participation rate
            if participation_rate >= participation_threshold:
                participation_bonus = self.config['network_health']['participation_bonus_multiplier']
                apy = base_rate * participation_bonus
            else:
                # Reduced rewards for low participation
                penalty_factor = participation_rate / participation_threshold
                apy = base_rate * penalty_factor

            # Apply governance bonus if applicable
            governance_bonus = self.config['consensus_participation']['governance_bonus']
            apy += governance_bonus

            return min(apy, 0.15)  # Cap at 15% APY

        except Exception as e:
            self.logger.error(f"Error calculating staking APY: {e}")
            return self.config['algo_staking']['base_reward_rate']

    def _estimate_rewards_per_round(self) -> int:
        """Estimate rewards per round based on network parameters"""
        # This is a simplified estimation - in practice would use actual network data
        base_rewards = 10000000  # 10 ALGO per round (example)
        return base_rewards

    def _calculate_confidence_score(self, metrics: Dict) -> float:
        """Calculate confidence score for the metrics"""
        score = 1.0

        # Reduce confidence if data is missing
        if not metrics.get('participation_rate'):
            score *= 0.8
        if not metrics.get('total_stake'):
            score *= 0.9

        # Reduce confidence for extreme values
        participation_rate = metrics.get('participation_rate', 0.85)
        if participation_rate < 0.5 or participation_rate > 0.99:
            score *= 0.7

        return max(score, 0.1)

    def _get_fallback_metrics(self) -> StakingMetrics:
        """Return fallback metrics when live data is unavailable"""
        return StakingMetrics(
            current_apy=self.config['emergency_conditions']['data_unavailable_rate'],
            participation_rate=0.85,
            total_stake=0,
            online_stake=0,
            rewards_per_round=0,
            timestamp=datetime.now(),
            confidence_score=0.5
        )

    async def calculate_base_rate(self,
                                lookback_days: Optional[int] = None) -> BaseRateResult:
        """
        Calculate base interest rate from staking yields

        Args:
            lookback_days: Days of historical data to consider

        Returns:
            BaseRateResult: Calculated base rate with components
        """
        try:
            if lookback_days is None:
                lookback_days = self.config['yield_calculation']['lookback_days']

            # Get current metrics
            current_metrics = await self.get_current_staking_metrics()

            # Get historical data for trend analysis
            historical_rates = await self._get_historical_rates(lookback_days)

            # Calculate components
            staking_component = self._calculate_staking_component(
                current_metrics, historical_rates
            )
            participation_component = self._calculate_participation_component(
                current_metrics
            )
            governance_component = self._calculate_governance_component()
            security_component = self._calculate_network_security_component(
                current_metrics
            )

            # Weight the components
            weights = self.config['base_rate_components']
            base_rate = (
                staking_component * weights['staking_yield_weight'] +
                participation_component * weights['consensus_reward_weight'] +
                governance_component * weights['governance_weight'] +
                security_component * weights['network_security_weight']
            )

            # Apply market condition adjustments
            base_rate = self._apply_market_adjustments(base_rate)

            # Apply smoothing if enabled
            if self.config['calculation_methodology']['smoothing_enabled']:
                base_rate = self._apply_smoothing(base_rate)

            return BaseRateResult(
                base_rate=base_rate,
                staking_component=staking_component,
                participation_component=participation_component,
                governance_component=governance_component,
                network_security_component=security_component,
                confidence_score=current_metrics.confidence_score,
                timestamp=datetime.now(),
                metadata={
                    'lookback_days': lookback_days,
                    'participation_rate': current_metrics.participation_rate,
                    'data_sources': ['algorand_network', 'historical_analysis'],
                    'calculation_method': self.config['calculation_methodology']['primary_method']
                }
            )

        except Exception as e:
            self.logger.error(f"Error calculating base rate: {e}")
            return self._get_fallback_base_rate()

    def _calculate_staking_component(self,
                                   current_metrics: StakingMetrics,
                                   historical_rates: List[float]) -> float:
        """Calculate the staking yield component"""
        if historical_rates:
            # Use moving average of historical rates
            avg_historical = statistics.mean(historical_rates)
            # Weight current vs historical (80% current, 20% historical)
            return 0.8 * current_metrics.current_apy + 0.2 * avg_historical
        else:
            return current_metrics.current_apy

    def _calculate_participation_component(self, metrics: StakingMetrics) -> float:
        """Calculate consensus participation reward component"""
        base_participation_reward = 0.01  # 1% base

        # Bonus for high participation
        if metrics.participation_rate > 0.9:
            return base_participation_reward * 1.5
        elif metrics.participation_rate > 0.8:
            return base_participation_reward * 1.2
        else:
            return base_participation_reward * metrics.participation_rate

    def _calculate_governance_component(self) -> float:
        """Calculate governance participation component"""
        return self.config['consensus_participation']['governance_bonus']

    def _calculate_network_security_component(self, metrics: StakingMetrics) -> float:
        """Calculate network security component"""
        security_bonus = 0.005  # 0.5% base security bonus

        # Higher security bonus for higher participation
        if metrics.participation_rate > 0.85:
            return security_bonus * self.config['network_health']['security_multiplier']
        else:
            return security_bonus

    async def _get_historical_rates(self, days: int) -> List[float]:
        """Get historical staking rates for trend analysis"""
        # In a real implementation, this would fetch from database or API
        # For now, simulate some historical data
        rates = []
        base_rate = 0.055

        for i in range(days):
            # Add some realistic variation
            variation = math.sin(i * 0.1) * 0.005  # Small daily variations
            rate = base_rate + variation
            rates.append(max(0.03, min(0.08, rate)))  # Clamp between 3% and 8%

        return rates

    def _apply_market_adjustments(self, base_rate: float) -> float:
        """Apply market condition adjustments to base rate"""
        # This would analyze current market conditions
        # For now, apply a small default adjustment
        adjustments = self.config['market_conditions']

        # Example: detect market condition (simplified)
        # In practice, this would use market data analysis
        market_condition = "normal"  # Default

        if market_condition == "bull_market":
            base_rate += adjustments['bull_market_adjustment']
        elif market_condition == "bear_market":
            base_rate += adjustments['bear_market_adjustment']

        return base_rate

    def _apply_smoothing(self, new_rate: float) -> float:
        """Apply rate smoothing to prevent sudden changes"""
        if hasattr(self, 'last_rate') and self.last_rate is not None:
            smoothing_factor = self.config['data_quality']['smoothing_factor']
            smoothed_rate = (
                (1 - smoothing_factor) * self.last_rate +
                smoothing_factor * new_rate
            )
            self.last_rate = smoothed_rate
            return smoothed_rate
        else:
            self.last_rate = new_rate
            return new_rate

    def _get_fallback_base_rate(self) -> BaseRateResult:
        """Return fallback base rate when calculation fails"""
        fallback_rate = self.config['emergency_conditions']['data_unavailable_rate']

        return BaseRateResult(
            base_rate=fallback_rate,
            staking_component=fallback_rate * 0.6,
            participation_component=fallback_rate * 0.25,
            governance_component=fallback_rate * 0.1,
            network_security_component=fallback_rate * 0.05,
            confidence_score=0.3,
            timestamp=datetime.now(),
            metadata={
                'fallback': True,
                'reason': 'calculation_error'
            }
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

    async def get_historical_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        Get historical analysis of staking rates

        Args:
            days: Number of days to analyze

        Returns:
            Dict containing historical analysis
        """
        try:
            rates = await self._get_historical_rates(days)

            if not rates:
                return {"error": "No historical data available"}

            return {
                "period_days": days,
                "average_rate": statistics.mean(rates),
                "median_rate": statistics.median(rates),
                "min_rate": min(rates),
                "max_rate": max(rates),
                "std_deviation": statistics.stdev(rates) if len(rates) > 1 else 0,
                "trend": "increasing" if rates[-1] > rates[0] else "decreasing",
                "volatility": statistics.stdev(rates) / statistics.mean(rates) if len(rates) > 1 else 0,
                "data_points": len(rates),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in historical analysis: {e}")
            return {"error": str(e)}

# Example usage and testing
async def main():
    """Example usage of the AlgoStakingEngine"""
    engine = AlgoStakingEngine()

    print("=== Algorand Staking Engine Demo ===")

    # Get current staking metrics
    print("\n1. Current Staking Metrics:")
    metrics = await engine.get_current_staking_metrics()
    print(f"   APY: {metrics.current_apy:.2%}")
    print(f"   Participation Rate: {metrics.participation_rate:.2%}")
    print(f"   Confidence Score: {metrics.confidence_score:.2f}")

    # Calculate base rate
    print("\n2. Base Rate Calculation:")
    result = await engine.calculate_base_rate()
    print(f"   Base Rate: {result.base_rate:.2%}")
    print(f"   Staking Component: {result.staking_component:.2%}")
    print(f"   Participation Component: {result.participation_component:.2%}")
    print(f"   Governance Component: {result.governance_component:.2%}")
    print(f"   Security Component: {result.network_security_component:.2%}")

    # Historical analysis
    print("\n3. Historical Analysis (30 days):")
    analysis = await engine.get_historical_analysis(30)
    if "error" not in analysis:
        print(f"   Average Rate: {analysis['average_rate']:.2%}")
        print(f"   Volatility: {analysis['volatility']:.2%}")
        print(f"   Trend: {analysis['trend']}")

if __name__ == "__main__":
    asyncio.run(main())