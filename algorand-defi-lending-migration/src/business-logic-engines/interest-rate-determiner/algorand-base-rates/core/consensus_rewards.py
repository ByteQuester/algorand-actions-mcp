"""
Consensus Rewards Analyzer

Analyzes Algorand consensus participation rewards and their impact on base interest rates.
Tracks validator participation, governance rewards, and network security metrics.
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
import json

@dataclass
class ConsensusMetrics:
    """Represents consensus participation metrics"""
    online_stake_percentage: float
    participation_rewards_apy: float
    governance_rewards_apy: float
    validator_count: int
    average_uptime: float
    consensus_efficiency: float
    timestamp: datetime
    confidence_score: float

@dataclass
class GovernanceData:
    """Governance participation data"""
    current_period: int
    total_governors: int
    committed_algo: int
    governance_apy: float
    voting_participation_rate: float
    period_end_date: datetime

@dataclass
class RewardAnalysis:
    """Analysis of consensus and governance rewards"""
    total_reward_rate: float
    consensus_component: float
    governance_component: float
    security_premium: float
    participation_bonus: float
    risk_adjustment: float
    timestamp: datetime
    metadata: Dict[str, Any]

class ConsensusRewardsAnalyzer:
    """
    Analyzer for Algorand consensus participation rewards.

    Tracks validator participation, governance rewards, and network security
    to determine additional yield components for base interest rate calculation.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the consensus rewards analyzer"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.governance_cache = {}
        self.metrics_cache = {}
        self.historical_participation = []

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
                'consensus_participation': {
                    'governance_bonus': 0.015,
                    'online_stake_requirement': 0.9
                },
                'mcp_services': {
                    'algorand_reader_url': 'http://localhost:8002'
                }
            }

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the analyzer"""
        logger = logging.getLogger('consensus_rewards_analyzer')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def get_consensus_metrics(self) -> ConsensusMetrics:
        """
        Fetch current consensus participation metrics

        Returns:
            ConsensusMetrics: Current consensus and participation data
        """
        try:
            # Check cache first
            if self._is_cache_valid('consensus_metrics'):
                return self.metrics_cache['consensus_metrics']

            # Fetch from network
            network_data = await self._fetch_network_status()
            participation_data = await self._fetch_participation_data()

            # Calculate metrics
            online_percentage = self._calculate_online_stake_percentage(network_data)
            participation_apy = self._calculate_participation_apy(participation_data)
            governance_apy = await self._get_governance_apy()

            result = ConsensusMetrics(
                online_stake_percentage=online_percentage,
                participation_rewards_apy=participation_apy,
                governance_rewards_apy=governance_apy,
                validator_count=participation_data.get('validator_count', 0),
                average_uptime=participation_data.get('average_uptime', 0.95),
                consensus_efficiency=self._calculate_consensus_efficiency(network_data),
                timestamp=datetime.now(),
                confidence_score=self._calculate_metrics_confidence(network_data, participation_data)
            )

            # Cache the result
            self.metrics_cache['consensus_metrics'] = result
            self.metrics_cache['consensus_metrics_timestamp'] = datetime.now()

            return result

        except Exception as e:
            self.logger.error(f"Error fetching consensus metrics: {e}")
            return self._get_fallback_consensus_metrics()

    async def _fetch_network_status(self) -> Dict:
        """Fetch network status from Algorand node"""
        try:
            # Try MCP service first
            mcp_url = self.config['mcp_services']['algorand_reader_url']
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{mcp_url}/network/consensus") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            self.logger.warning(f"MCP service unavailable, using direct API: {e}")

        # Fallback to direct API
        return await self._fetch_direct_network_status()

    async def _fetch_direct_network_status(self) -> Dict:
        """Fetch network status directly from Algorand API"""
        try:
            algod_url = self.config.get('external_apis', {}).get(
                'algorand_node', 'https://mainnet-api.algonode.cloud'
            )

            async with aiohttp.ClientSession() as session:
                # Get network status
                async with session.get(f"{algod_url}/v2/status") as response:
                    status_data = await response.json()

                # Get supply information for stake calculations
                async with session.get(f"{algod_url}/v2/ledger/supply") as response:
                    supply_data = await response.json()

                return {
                    'last_round': status_data.get('last-round', 0),
                    'time_since_last_round': status_data.get('time-since-last-round', 0),
                    'total_money': supply_data.get('total-money', 0),
                    'online_money': supply_data.get('online-money', 0),
                    'rewards_level': supply_data.get('rewards-level', 0),
                    'rewards_rate': supply_data.get('rewards-rate', 0),
                    'rewards_residue': supply_data.get('rewards-residue', 0)
                }

        except Exception as e:
            self.logger.error(f"Error fetching network status: {e}")
            return {}

    async def _fetch_participation_data(self) -> Dict:
        """Fetch validator participation data"""
        try:
            # This would typically come from participation APIs or indexer
            # For now, simulate realistic participation data
            return {
                'validator_count': 1500,  # Approximate number of validators
                'average_uptime': 0.96,   # 96% average uptime
                'participation_rate': 0.85,  # 85% participation
                'consensus_rounds_per_day': 10800,  # ~8 second rounds
                'average_stake_per_validator': 50000000000  # 50k ALGO average
            }

        except Exception as e:
            self.logger.error(f"Error fetching participation data: {e}")
            return {}

    def _calculate_online_stake_percentage(self, network_data: Dict) -> float:
        """Calculate percentage of stake that is online"""
        total_money = network_data.get('total_money', 0)
        online_money = network_data.get('online_money', 0)

        if total_money > 0:
            return online_money / total_money
        else:
            return 0.85  # Default assumption

    def _calculate_participation_apy(self, participation_data: Dict) -> float:
        """Calculate APY from consensus participation rewards"""
        try:
            # Base participation reward rate
            base_rate = 0.04  # 4% base APY for participation

            # Adjust based on actual participation
            participation_rate = participation_data.get('participation_rate', 0.85)
            uptime = participation_data.get('average_uptime', 0.95)

            # Higher rewards for consistent participation
            consistency_bonus = min(uptime * 0.02, 0.015)  # Up to 1.5% bonus

            # Network security bonus
            if participation_rate > 0.8:
                security_bonus = 0.005  # 0.5% security bonus
            else:
                security_bonus = 0.0

            total_apy = base_rate + consistency_bonus + security_bonus

            return min(total_apy, 0.08)  # Cap at 8% APY

        except Exception as e:
            self.logger.error(f"Error calculating participation APY: {e}")
            return 0.04  # Default 4% APY

    async def _get_governance_apy(self) -> float:
        """Get current governance rewards APY"""
        try:
            # Check cache first
            if self._is_cache_valid('governance_apy'):
                return self.governance_cache['governance_apy']

            # Fetch governance data
            governance_data = await self._fetch_governance_data()

            # Calculate governance APY
            committed_algo = governance_data.get('committed_algo', 0)
            total_rewards = governance_data.get('total_rewards_algo', 0)

            if committed_algo > 0:
                # Annualized governance rewards (quarterly * 4)
                quarterly_rate = total_rewards / committed_algo
                annual_rate = quarterly_rate * 4  # 4 quarters per year
                governance_apy = annual_rate
            else:
                governance_apy = self.config['consensus_participation']['governance_bonus']

            # Cache the result
            self.governance_cache['governance_apy'] = governance_apy
            self.governance_cache['governance_apy_timestamp'] = datetime.now()

            return min(governance_apy, 0.05)  # Cap at 5% APY

        except Exception as e:
            self.logger.error(f"Error fetching governance APY: {e}")
            return self.config['consensus_participation']['governance_bonus']

    async def _fetch_governance_data(self) -> Dict:
        """Fetch current governance period data"""
        try:
            # This would typically fetch from governance API
            # For now, simulate realistic governance data
            return {
                'current_period': 6,
                'committed_algo': 2500000000000000,  # 2.5B ALGO committed
                'total_rewards_algo': 62500000000000,  # 62.5M ALGO rewards
                'total_governors': 75000,
                'voting_participation_rate': 0.68,
                'period_end_date': datetime.now() + timedelta(days=45)
            }

        except Exception as e:
            self.logger.error(f"Error fetching governance data: {e}")
            return {}

    def _calculate_consensus_efficiency(self, network_data: Dict) -> float:
        """Calculate consensus efficiency metric"""
        try:
            # Base efficiency on round times and participation
            time_since_last = network_data.get('time_since_last_round', 8)
            target_round_time = 8  # 8 second target

            # Efficiency based on round timing
            timing_efficiency = min(target_round_time / max(time_since_last, 1), 1.0)

            # Factor in online stake percentage
            online_percentage = self._calculate_online_stake_percentage(network_data)
            stake_efficiency = min(online_percentage / 0.85, 1.0)  # Target 85% online

            # Combined efficiency score
            return (timing_efficiency + stake_efficiency) / 2

        except Exception as e:
            self.logger.error(f"Error calculating consensus efficiency: {e}")
            return 0.9  # Default 90% efficiency

    def _calculate_metrics_confidence(self, network_data: Dict, participation_data: Dict) -> float:
        """Calculate confidence score for the metrics"""
        confidence = 1.0

        # Reduce confidence for missing data
        if not network_data:
            confidence *= 0.6
        if not participation_data:
            confidence *= 0.7

        # Reduce confidence for unrealistic values
        online_percentage = self._calculate_online_stake_percentage(network_data)
        if online_percentage < 0.5 or online_percentage > 0.98:
            confidence *= 0.8

        return max(confidence, 0.3)

    def _get_fallback_consensus_metrics(self) -> ConsensusMetrics:
        """Return fallback metrics when live data is unavailable"""
        return ConsensusMetrics(
            online_stake_percentage=0.85,
            participation_rewards_apy=0.04,
            governance_rewards_apy=self.config['consensus_participation']['governance_bonus'],
            validator_count=1500,
            average_uptime=0.95,
            consensus_efficiency=0.9,
            timestamp=datetime.now(),
            confidence_score=0.5
        )

    async def analyze_reward_components(self) -> RewardAnalysis:
        """
        Analyze all reward components and calculate total reward rate

        Returns:
            RewardAnalysis: Complete analysis of reward components
        """
        try:
            # Get current metrics
            metrics = await self.get_consensus_metrics()

            # Calculate individual components
            consensus_component = self._calculate_consensus_component(metrics)
            governance_component = self._calculate_governance_component(metrics)
            security_premium = self._calculate_security_premium(metrics)
            participation_bonus = self._calculate_participation_bonus(metrics)
            risk_adjustment = self._calculate_risk_adjustment(metrics)

            # Calculate total reward rate
            total_rate = (
                consensus_component +
                governance_component +
                security_premium +
                participation_bonus +
                risk_adjustment
            )

            return RewardAnalysis(
                total_reward_rate=total_rate,
                consensus_component=consensus_component,
                governance_component=governance_component,
                security_premium=security_premium,
                participation_bonus=participation_bonus,
                risk_adjustment=risk_adjustment,
                timestamp=datetime.now(),
                metadata={
                    'online_stake_percentage': metrics.online_stake_percentage,
                    'validator_count': metrics.validator_count,
                    'consensus_efficiency': metrics.consensus_efficiency,
                    'confidence_score': metrics.confidence_score
                }
            )

        except Exception as e:
            self.logger.error(f"Error analyzing reward components: {e}")
            return self._get_fallback_reward_analysis()

    def _calculate_consensus_component(self, metrics: ConsensusMetrics) -> float:
        """Calculate the consensus participation component"""
        base_component = metrics.participation_rewards_apy

        # Adjust for efficiency
        efficiency_multiplier = 0.8 + (metrics.consensus_efficiency * 0.4)  # 0.8 to 1.2
        adjusted_component = base_component * efficiency_multiplier

        return min(adjusted_component, 0.06)  # Cap at 6%

    def _calculate_governance_component(self, metrics: ConsensusMetrics) -> float:
        """Calculate the governance rewards component"""
        return metrics.governance_rewards_apy

    def _calculate_security_premium(self, metrics: ConsensusMetrics) -> float:
        """Calculate security premium based on network health"""
        base_premium = 0.005  # 0.5% base security premium

        # Higher premium for better security (more online stake)
        if metrics.online_stake_percentage > 0.9:
            return base_premium * 1.5
        elif metrics.online_stake_percentage > 0.85:
            return base_premium * 1.2
        elif metrics.online_stake_percentage > 0.8:
            return base_premium
        else:
            return base_premium * 0.5

    def _calculate_participation_bonus(self, metrics: ConsensusMetrics) -> float:
        """Calculate bonus for high participation"""
        if metrics.average_uptime > 0.98:
            return 0.003  # 0.3% bonus for excellent uptime
        elif metrics.average_uptime > 0.95:
            return 0.002  # 0.2% bonus for good uptime
        elif metrics.average_uptime > 0.9:
            return 0.001  # 0.1% bonus for decent uptime
        else:
            return 0.0

    def _calculate_risk_adjustment(self, metrics: ConsensusMetrics) -> float:
        """Calculate risk adjustment based on network conditions"""
        # Lower confidence means higher risk adjustment
        risk_factor = 1.0 - metrics.confidence_score
        max_risk_adjustment = 0.01  # 1% max risk adjustment

        return risk_factor * max_risk_adjustment

    def _get_fallback_reward_analysis(self) -> RewardAnalysis:
        """Return fallback analysis when calculation fails"""
        return RewardAnalysis(
            total_reward_rate=0.06,  # 6% fallback total rate
            consensus_component=0.04,
            governance_component=0.015,
            security_premium=0.005,
            participation_bonus=0.0,
            risk_adjustment=0.0,
            timestamp=datetime.now(),
            metadata={'fallback': True}
        )

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        cache_dict = self.metrics_cache if 'metrics' in key else self.governance_cache
        timestamp_key = f"{key}_timestamp"

        if key not in cache_dict or timestamp_key not in cache_dict:
            return False

        cache_expiry = self.config['historical_data']['cache_expiry_minutes']
        expiry_time = cache_dict[timestamp_key] + timedelta(minutes=cache_expiry)

        return datetime.now() < expiry_time

    async def get_governance_summary(self) -> GovernanceData:
        """
        Get current governance period summary

        Returns:
            GovernanceData: Current governance information
        """
        try:
            governance_data = await self._fetch_governance_data()

            return GovernanceData(
                current_period=governance_data.get('current_period', 0),
                total_governors=governance_data.get('total_governors', 0),
                committed_algo=governance_data.get('committed_algo', 0),
                governance_apy=await self._get_governance_apy(),
                voting_participation_rate=governance_data.get('voting_participation_rate', 0),
                period_end_date=governance_data.get('period_end_date', datetime.now())
            )

        except Exception as e:
            self.logger.error(f"Error getting governance summary: {e}")
            return GovernanceData(
                current_period=0,
                total_governors=0,
                committed_algo=0,
                governance_apy=0.015,
                voting_participation_rate=0.0,
                period_end_date=datetime.now()
            )

    async def get_participation_trend(self, days: int = 30) -> Dict[str, Any]:
        """
        Get participation trend analysis

        Args:
            days: Number of days to analyze

        Returns:
            Dict containing trend analysis
        """
        try:
            # Simulate historical participation data
            participation_history = []
            base_participation = 0.85

            for i in range(days):
                # Add realistic daily variation
                daily_variation = (i % 7) * 0.01 - 0.03  # Weekly patterns
                participation = max(0.7, min(0.95, base_participation + daily_variation))
                participation_history.append(participation)

            if not participation_history:
                return {"error": "No participation data available"}

            return {
                "period_days": days,
                "average_participation": statistics.mean(participation_history),
                "current_participation": participation_history[-1],
                "min_participation": min(participation_history),
                "max_participation": max(participation_history),
                "trend": "increasing" if participation_history[-1] > participation_history[0] else "decreasing",
                "volatility": statistics.stdev(participation_history) if len(participation_history) > 1 else 0,
                "above_target_days": sum(1 for p in participation_history if p > 0.85),
                "target_achievement_rate": sum(1 for p in participation_history if p > 0.85) / len(participation_history),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in participation trend analysis: {e}")
            return {"error": str(e)}

# Example usage and testing
async def main():
    """Example usage of the ConsensusRewardsAnalyzer"""
    analyzer = ConsensusRewardsAnalyzer()

    print("=== Consensus Rewards Analyzer Demo ===")

    # Get consensus metrics
    print("\n1. Current Consensus Metrics:")
    metrics = await analyzer.get_consensus_metrics()
    print(f"   Online Stake: {metrics.online_stake_percentage:.2%}")
    print(f"   Participation APY: {metrics.participation_rewards_apy:.2%}")
    print(f"   Governance APY: {metrics.governance_rewards_apy:.2%}")
    print(f"   Validator Count: {metrics.validator_count:,}")
    print(f"   Average Uptime: {metrics.average_uptime:.2%}")
    print(f"   Consensus Efficiency: {metrics.consensus_efficiency:.2%}")

    # Analyze reward components
    print("\n2. Reward Component Analysis:")
    analysis = await analyzer.analyze_reward_components()
    print(f"   Total Reward Rate: {analysis.total_reward_rate:.2%}")
    print(f"   Consensus Component: {analysis.consensus_component:.2%}")
    print(f"   Governance Component: {analysis.governance_component:.2%}")
    print(f"   Security Premium: {analysis.security_premium:.2%}")
    print(f"   Participation Bonus: {analysis.participation_bonus:.2%}")

    # Get governance summary
    print("\n3. Governance Summary:")
    governance = await analyzer.get_governance_summary()
    print(f"   Current Period: {governance.current_period}")
    print(f"   Total Governors: {governance.total_governors:,}")
    print(f"   Committed ALGO: {governance.committed_algo / 1_000_000:,.0f}M")
    print(f"   Governance APY: {governance.governance_apy:.2%}")

    # Get participation trend
    print("\n4. Participation Trend (30 days):")
    trend = await analyzer.get_participation_trend(30)
    if "error" not in trend:
        print(f"   Average Participation: {trend['average_participation']:.2%}")
        print(f"   Target Achievement: {trend['target_achievement_rate']:.2%}")
        print(f"   Trend: {trend['trend']}")

if __name__ == "__main__":
    asyncio.run(main())