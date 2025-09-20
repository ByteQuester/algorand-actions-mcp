"""
Wallet Footprint Analyzer

Analyzes wallet age, transaction volume, asset diversity, and basic
on-chain behavior patterns for foundational risk assessment.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class WalletMetrics:
    """Basic wallet metrics"""
    creation_date: datetime
    age_days: int
    total_transactions: int
    total_volume_algo: float
    unique_counterparties: int
    asset_count: int
    nft_count: int
    average_transaction_size: float
    transaction_frequency: float


@dataclass
class AssetDistribution:
    """Asset portfolio distribution"""
    total_value_usd: float
    algo_percentage: float
    stable_percentage: float
    asa_percentage: float
    nft_percentage: float
    diversity_score: float
    largest_position_percentage: float


@dataclass
class ActivityPatterns:
    """Transaction activity patterns"""
    daily_avg_transactions: float
    weekly_pattern: List[float]
    hourly_pattern: List[float]
    consistency_score: float
    burst_activity_detected: bool
    dormancy_periods: List[Tuple[datetime, datetime]]


class WalletFootprintAnalyzer:
    """
    Analyzes fundamental wallet characteristics including age, transaction
    patterns, asset holdings, and basic behavioral indicators.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.wallet_config = config.get('wallet_footprint', {})

    async def analyze_wallet_fundamentals(self, wallet_address: str) -> Dict[str, Any]:
        """
        Analyze fundamental wallet characteristics.

        Args:
            wallet_address: Algorand wallet address to analyze

        Returns:
            Dictionary containing wallet fundamental analysis
        """
        logger.info(f"Analyzing wallet fundamentals for {wallet_address}")

        try:
            # Parallel data collection
            tasks = [
                self._fetch_wallet_creation_data(wallet_address),
                self._fetch_transaction_history(wallet_address),
                self._fetch_asset_holdings(wallet_address),
                self._fetch_nft_holdings(wallet_address)
            ]

            creation_data, tx_history, asset_holdings, nft_holdings = await asyncio.gather(*tasks)

            # Calculate wallet metrics
            wallet_metrics = self._calculate_wallet_metrics(
                creation_data, tx_history, asset_holdings, nft_holdings
            )

            # Analyze asset distribution
            asset_distribution = self._analyze_asset_distribution(asset_holdings)

            # Analyze activity patterns
            activity_patterns = self._analyze_activity_patterns(tx_history)

            # Calculate scoring
            scores = self._calculate_wallet_scores(
                wallet_metrics, asset_distribution, activity_patterns
            )

            return {
                'wallet_metrics': wallet_metrics,
                'asset_distribution': asset_distribution,
                'activity_patterns': activity_patterns,
                'scores': scores,
                'analysis_timestamp': datetime.utcnow(),
                'wallet_age_days': wallet_metrics.age_days,
                'total_transactions': wallet_metrics.total_transactions,
                'total_volume_algo': wallet_metrics.total_volume_algo,
                'asset_count': wallet_metrics.asset_count,
                'nft_count': wallet_metrics.nft_count,
                'diversity_score': asset_distribution.diversity_score,
                'frequency_score': activity_patterns.consistency_score
            }

        except Exception as e:
            logger.error(f"Wallet fundamentals analysis failed for {wallet_address}: {e}")
            raise

    async def analyze_transaction_patterns(self, wallet_address: str) -> Dict[str, Any]:
        """
        Analyze detailed transaction patterns and behaviors.

        Args:
            wallet_address: Algorand wallet address to analyze

        Returns:
            Dictionary containing transaction pattern analysis
        """
        logger.info(f"Analyzing transaction patterns for {wallet_address}")

        try:
            # Fetch transaction history
            tx_history = await self._fetch_transaction_history(wallet_address)

            if not tx_history:
                return self._empty_transaction_analysis()

            # Parallel pattern analysis
            tasks = [
                self._analyze_temporal_patterns(tx_history),
                self._analyze_volume_patterns(tx_history),
                self._analyze_counterparty_patterns(tx_history),
                self._analyze_fee_patterns(tx_history),
                self._detect_automation_patterns(tx_history)
            ]

            temporal, volume, counterparty, fee, automation = await asyncio.gather(*tasks)

            # Calculate overall pattern scores
            pattern_scores = self._calculate_pattern_scores(
                temporal, volume, counterparty, fee, automation
            )

            return {
                'temporal_patterns': temporal,
                'volume_patterns': volume,
                'counterparty_patterns': counterparty,
                'fee_patterns': fee,
                'automation_patterns': automation,
                'pattern_scores': pattern_scores,
                'total_transactions': len(tx_history),
                'analysis_period_days': self._calculate_analysis_period(tx_history),
                'frequency_score': pattern_scores.get('consistency', 0.0),
                'timezone_consistency': temporal.get('timezone_consistency', 0.0),
                'gas_optimization': fee.get('optimization_score', 0.0),
                'weekend_ratio': temporal.get('weekend_ratio', 0.0)
            }

        except Exception as e:
            logger.error(f"Transaction pattern analysis failed for {wallet_address}: {e}")
            raise

    async def analyze_asset_portfolio(self, wallet_address: str) -> Dict[str, Any]:
        """
        Analyze asset portfolio composition and management patterns.

        Args:
            wallet_address: Algorand wallet address to analyze

        Returns:
            Dictionary containing asset portfolio analysis
        """
        logger.info(f"Analyzing asset portfolio for {wallet_address}")

        try:
            # Fetch current and historical asset data
            current_holdings = await self._fetch_asset_holdings(wallet_address)
            historical_holdings = await self._fetch_historical_asset_data(wallet_address)
            nft_holdings = await self._fetch_nft_holdings(wallet_address)

            # Asset composition analysis
            composition = self._analyze_asset_composition(current_holdings)

            # Diversification analysis
            diversification = self._analyze_portfolio_diversification(current_holdings)

            # Risk analysis
            risk_analysis = self._analyze_portfolio_risk(current_holdings)

            # Management patterns
            management_patterns = self._analyze_portfolio_management(
                current_holdings, historical_holdings
            )

            # NFT analysis
            nft_analysis = self._analyze_nft_portfolio(nft_holdings)

            # Calculate portfolio scores
            portfolio_scores = self._calculate_portfolio_scores(
                composition, diversification, risk_analysis, management_patterns
            )

            return {
                'composition': composition,
                'diversification': diversification,
                'risk_analysis': risk_analysis,
                'management_patterns': management_patterns,
                'nft_analysis': nft_analysis,
                'portfolio_scores': portfolio_scores,
                'asset_count': len(current_holdings),
                'nft_count': len(nft_holdings),
                'diversity_score': diversification.get('diversity_score', 0.0),
                'stable_percentage': composition.get('stable_percentage', 0.0),
                'algo_percentage': composition.get('algo_percentage', 0.0),
                'exotic_percentage': composition.get('exotic_percentage', 0.0)
            }

        except Exception as e:
            logger.error(f"Asset portfolio analysis failed for {wallet_address}: {e}")
            raise

    async def _fetch_wallet_creation_data(self, wallet_address: str) -> Dict[str, Any]:
        """Fetch wallet creation and basic data"""
        # Mock implementation - would integrate with Algorand indexer
        return {
            'creation_date': datetime.utcnow() - timedelta(days=547),
            'first_transaction_date': datetime.utcnow() - timedelta(days=545),
            'is_multisig': False,
            'account_type': 'standard'
        }

    async def _fetch_transaction_history(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch complete transaction history"""
        # Mock implementation - would integrate with Algorand indexer
        transactions = []
        start_date = datetime.utcnow() - timedelta(days=365)

        # Generate mock transaction data
        current_date = start_date
        while current_date < datetime.utcnow():
            # Simulate varying activity levels
            if current_date.weekday() < 5:  # Weekdays
                num_txs = 2 if __import__('random').random() > 0.7 else 1
            else:  # Weekends
                num_txs = 1 if __import__('random').random() > 0.8 else 0

            for _ in range(num_txs):
                tx = {
                    'id': f"tx_{current_date.isoformat()}_{__import__('random').randint(1000, 9999)}",
                    'timestamp': current_date,
                    'type': __import__('random').choice(['payment', 'app_call', 'asset_transfer']),
                    'amount': __import__('random').uniform(1, 1000),
                    'fee': __import__('random').uniform(0.001, 0.01),
                    'sender': wallet_address,
                    'receiver': f"receiver_{__import__('random').randint(1, 50)}",
                    'asset_id': __import__('random').choice([0, 31566704, 386192725, None])
                }
                transactions.append(tx)

            current_date += timedelta(days=1, hours=__import__('random').uniform(0, 2))

        return sorted(transactions, key=lambda x: x['timestamp'])

    async def _fetch_asset_holdings(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch current asset holdings"""
        # Mock implementation
        return [
            {
                'asset_id': 0,
                'asset_name': 'Algorand',
                'balance': 12547.83,
                'value_usd': 3137.0,
                'percentage': 45.2
            },
            {
                'asset_id': 31566704,
                'asset_name': 'USDC',
                'balance': 2500.0,
                'value_usd': 2500.0,
                'percentage': 36.0
            },
            {
                'asset_id': 386192725,
                'asset_name': 'goBTC',
                'balance': 0.03,
                'value_usd': 1300.0,
                'percentage': 18.8
            }
        ]

    async def _fetch_nft_holdings(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch NFT holdings"""
        # Mock implementation
        return [
            {
                'asset_id': 123456789,
                'collection': 'Algorand Pandas',
                'name': 'Panda #1234',
                'rarity_rank': 156,
                'floor_price': 45.0,
                'owned_since': datetime.utcnow() - timedelta(days=120)
            },
            {
                'asset_id': 234567890,
                'collection': 'AlgoGems',
                'name': 'Gem #5678',
                'rarity_rank': 890,
                'floor_price': 12.0,
                'owned_since': datetime.utcnow() - timedelta(days=45)
            }
        ]

    async def _fetch_historical_asset_data(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch historical asset holdings snapshots"""
        # Mock implementation
        return [
            {
                'timestamp': datetime.utcnow() - timedelta(days=30),
                'total_value_usd': 6500.0,
                'asset_count': 3,
                'portfolio_composition': {'algo': 0.5, 'usdc': 0.3, 'other': 0.2}
            },
            {
                'timestamp': datetime.utcnow() - timedelta(days=60),
                'total_value_usd': 5800.0,
                'asset_count': 2,
                'portfolio_composition': {'algo': 0.6, 'usdc': 0.4}
            }
        ]

    def _calculate_wallet_metrics(
        self,
        creation_data: Dict[str, Any],
        tx_history: List[Dict[str, Any]],
        asset_holdings: List[Dict[str, Any]],
        nft_holdings: List[Dict[str, Any]]
    ) -> WalletMetrics:
        """Calculate comprehensive wallet metrics"""

        creation_date = creation_data['creation_date']
        age_days = (datetime.utcnow() - creation_date).days

        # Transaction metrics
        total_transactions = len(tx_history)
        total_volume = sum(tx.get('amount', 0) for tx in tx_history)

        # Counterparty analysis
        unique_counterparties = len(set(
            tx.get('receiver') for tx in tx_history if tx.get('receiver')
        ))

        # Asset metrics
        asset_count = len(asset_holdings)
        nft_count = len(nft_holdings)

        # Calculate averages
        avg_tx_size = total_volume / total_transactions if total_transactions > 0 else 0
        tx_frequency = total_transactions / age_days if age_days > 0 else 0

        return WalletMetrics(
            creation_date=creation_date,
            age_days=age_days,
            total_transactions=total_transactions,
            total_volume_algo=total_volume,
            unique_counterparties=unique_counterparties,
            asset_count=asset_count,
            nft_count=nft_count,
            average_transaction_size=avg_tx_size,
            transaction_frequency=tx_frequency
        )

    def _analyze_asset_distribution(self, asset_holdings: List[Dict[str, Any]]) -> AssetDistribution:
        """Analyze asset portfolio distribution"""

        if not asset_holdings:
            return AssetDistribution(0, 0, 0, 0, 0, 0, 0)

        total_value = sum(holding['value_usd'] for holding in asset_holdings)

        # Calculate percentages
        algo_value = sum(h['value_usd'] for h in asset_holdings if h['asset_id'] == 0)
        stable_value = sum(h['value_usd'] for h in asset_holdings
                          if h['asset_id'] in [31566704, 465865291])  # USDC, USDT
        asa_value = sum(h['value_usd'] for h in asset_holdings
                       if h['asset_id'] != 0 and h['asset_id'] not in [31566704, 465865291])

        algo_pct = algo_value / total_value if total_value > 0 else 0
        stable_pct = stable_value / total_value if total_value > 0 else 0
        asa_pct = asa_value / total_value if total_value > 0 else 0

        # Calculate diversity score (Herfindahl-Hirschman Index)
        percentages = [h['value_usd'] / total_value for h in asset_holdings if total_value > 0]
        hhi = sum(p ** 2 for p in percentages)
        diversity_score = 1 - hhi if len(asset_holdings) > 1 else 0

        # Largest position
        largest_position = max(percentages) if percentages else 0

        return AssetDistribution(
            total_value_usd=total_value,
            algo_percentage=algo_pct,
            stable_percentage=stable_pct,
            asa_percentage=asa_pct,
            nft_percentage=0.0,  # Would be calculated separately
            diversity_score=diversity_score,
            largest_position_percentage=largest_position
        )

    def _analyze_activity_patterns(self, tx_history: List[Dict[str, Any]]) -> ActivityPatterns:
        """Analyze transaction activity patterns"""

        if not tx_history:
            return ActivityPatterns(0, [0]*7, [0]*24, 0, False, [])

        # Daily transaction counts
        daily_counts = defaultdict(int)
        for tx in tx_history:
            date = tx['timestamp'].date()
            daily_counts[date] += 1

        daily_avg = sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0

        # Weekly pattern (0=Monday, 6=Sunday)
        weekly_counts = [0] * 7
        for tx in tx_history:
            weekday = tx['timestamp'].weekday()
            weekly_counts[weekday] += 1

        # Normalize to percentages
        total_txs = len(tx_history)
        weekly_pattern = [count / total_txs for count in weekly_counts] if total_txs > 0 else [0]*7

        # Hourly pattern
        hourly_counts = [0] * 24
        for tx in tx_history:
            hour = tx['timestamp'].hour
            hourly_counts[hour] += 1

        hourly_pattern = [count / total_txs for count in hourly_counts] if total_txs > 0 else [0]*24

        # Consistency score (inverse of coefficient of variation)
        daily_values = list(daily_counts.values())
        if len(daily_values) > 1:
            cv = statistics.stdev(daily_values) / statistics.mean(daily_values)
            consistency_score = max(0, 1 - cv)
        else:
            consistency_score = 0

        # Burst activity detection
        max_daily = max(daily_values) if daily_values else 0
        avg_daily = statistics.mean(daily_values) if daily_values else 0
        burst_detected = max_daily > avg_daily * 5 if avg_daily > 0 else False

        # Dormancy periods (gaps > 7 days)
        dormancy_periods = []
        if len(tx_history) > 1:
            sorted_txs = sorted(tx_history, key=lambda x: x['timestamp'])
            for i in range(1, len(sorted_txs)):
                gap = (sorted_txs[i]['timestamp'] - sorted_txs[i-1]['timestamp']).days
                if gap > 7:
                    dormancy_periods.append((sorted_txs[i-1]['timestamp'], sorted_txs[i]['timestamp']))

        return ActivityPatterns(
            daily_avg_transactions=daily_avg,
            weekly_pattern=weekly_pattern,
            hourly_pattern=hourly_pattern,
            consistency_score=consistency_score,
            burst_activity_detected=burst_detected,
            dormancy_periods=dormancy_periods
        )

    def _calculate_wallet_scores(
        self,
        wallet_metrics: WalletMetrics,
        asset_distribution: AssetDistribution,
        activity_patterns: ActivityPatterns
    ) -> Dict[str, float]:
        """Calculate comprehensive wallet scoring"""

        scores = {}

        # Age score (0-100)
        age_thresholds = self.wallet_config.get('age_scoring', {})
        if wallet_metrics.age_days >= age_thresholds.get('excellent_threshold_days', 730):
            scores['age_score'] = 95
        elif wallet_metrics.age_days >= age_thresholds.get('good_threshold_days', 365):
            scores['age_score'] = 80
        elif wallet_metrics.age_days >= age_thresholds.get('fair_threshold_days', 180):
            scores['age_score'] = 60
        elif wallet_metrics.age_days >= age_thresholds.get('poor_threshold_days', 90):
            scores['age_score'] = 40
        else:
            scores['age_score'] = 20

        # Volume score (0-100)
        volume_thresholds = self.wallet_config.get('volume_scoring', {})
        if wallet_metrics.total_volume_algo >= volume_thresholds.get('excellent_threshold', 100000):
            scores['volume_score'] = 95
        elif wallet_metrics.total_volume_algo >= volume_thresholds.get('good_threshold', 10000):
            scores['volume_score'] = 80
        elif wallet_metrics.total_volume_algo >= volume_thresholds.get('fair_threshold', 1000):
            scores['volume_score'] = 60
        elif wallet_metrics.total_volume_algo >= volume_thresholds.get('poor_threshold', 100):
            scores['volume_score'] = 40
        else:
            scores['volume_score'] = 20

        # Activity score
        scores['activity_score'] = min(wallet_metrics.transaction_frequency * 365 / 5 * 100, 100)

        # Diversity score
        scores['diversity_score'] = asset_distribution.diversity_score * 100

        # Consistency score
        scores['consistency_score'] = activity_patterns.consistency_score * 100

        # Overall score (weighted average)
        weights = {
            'age_score': 0.25,
            'volume_score': 0.25,
            'activity_score': 0.20,
            'diversity_score': 0.15,
            'consistency_score': 0.15
        }

        overall_score = sum(scores[key] * weight for key, weight in weights.items())
        scores['overall_score'] = overall_score

        return scores

    async def _analyze_temporal_patterns(self, tx_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal transaction patterns"""
        if not tx_history:
            return {}

        # Time zone consistency
        hours = [tx['timestamp'].hour for tx in tx_history]
        hour_variance = statistics.variance(hours) if len(hours) > 1 else 0
        timezone_consistency = max(0, 1 - hour_variance / 144)  # Normalize

        # Weekend activity
        weekend_txs = sum(1 for tx in tx_history if tx['timestamp'].weekday() >= 5)
        weekend_ratio = weekend_txs / len(tx_history)

        # Business hours activity
        business_hours = list(range(9, 18))
        business_txs = sum(1 for tx in tx_history if tx['timestamp'].hour in business_hours)
        business_ratio = business_txs / len(tx_history)

        return {
            'timezone_consistency': timezone_consistency,
            'weekend_ratio': weekend_ratio,
            'business_hours_ratio': business_ratio,
            'peak_activity_hour': max(set(hours), key=hours.count) if hours else 12
        }

    async def _analyze_volume_patterns(self, tx_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze transaction volume patterns"""
        amounts = [tx.get('amount', 0) for tx in tx_history if tx.get('amount', 0) > 0]

        if not amounts:
            return {}

        return {
            'total_volume': sum(amounts),
            'average_amount': statistics.mean(amounts),
            'median_amount': statistics.median(amounts),
            'volume_variance': statistics.variance(amounts),
            'large_transaction_ratio': sum(1 for a in amounts if a > statistics.mean(amounts) * 3) / len(amounts)
        }

    async def _analyze_counterparty_patterns(self, tx_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze counterparty interaction patterns"""
        receivers = [tx.get('receiver') for tx in tx_history if tx.get('receiver')]

        if not receivers:
            return {}

        unique_receivers = set(receivers)
        receiver_counts = {r: receivers.count(r) for r in unique_receivers}

        return {
            'unique_counterparties': len(unique_receivers),
            'repeat_interaction_ratio': 1 - len(unique_receivers) / len(receivers),
            'most_frequent_counterparty_count': max(receiver_counts.values()),
            'counterparty_concentration': max(receiver_counts.values()) / len(receivers)
        }

    async def _analyze_fee_patterns(self, tx_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze transaction fee patterns"""
        fees = [tx.get('fee', 0) for tx in tx_history if tx.get('fee', 0) > 0]

        if not fees:
            return {}

        avg_fee = statistics.mean(fees)
        fee_variance = statistics.variance(fees) if len(fees) > 1 else 0

        return {
            'average_fee': avg_fee,
            'fee_variance': fee_variance,
            'optimization_score': max(0, 1 - fee_variance / avg_fee if avg_fee > 0 else 0),
            'overpayment_frequency': sum(1 for f in fees if f > avg_fee * 2) / len(fees)
        }

    async def _detect_automation_patterns(self, tx_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect automated transaction patterns"""
        if len(tx_history) < 5:
            return {'automation_detected': False}

        # Check for regular intervals
        timestamps = sorted([tx['timestamp'] for tx in tx_history])
        intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]

        if len(intervals) > 2:
            interval_cv = statistics.stdev(intervals) / statistics.mean(intervals)
            automation_detected = interval_cv < 0.1  # Very regular intervals
        else:
            automation_detected = False

        return {
            'automation_detected': automation_detected,
            'interval_regularity': 1 - min(interval_cv, 1.0) if len(intervals) > 2 else 0
        }

    def _calculate_pattern_scores(self, *pattern_analyses) -> Dict[str, float]:
        """Calculate overall pattern scores"""
        temporal, volume, counterparty, fee, automation = pattern_analyses

        scores = {
            'consistency': temporal.get('timezone_consistency', 0.5),
            'diversity': 1 - counterparty.get('counterparty_concentration', 0.5),
            'optimization': fee.get('optimization_score', 0.5),
            'sophistication': 1.0 if automation.get('automation_detected', False) else 0.5
        }

        return scores

    def _analyze_asset_composition(self, current_holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze asset composition"""
        if not current_holdings:
            return {}

        total_value = sum(h['value_usd'] for h in current_holdings)

        # Calculate percentages by type
        algo_value = sum(h['value_usd'] for h in current_holdings if h['asset_id'] == 0)
        stable_value = sum(h['value_usd'] for h in current_holdings
                          if h['asset_id'] in [31566704, 465865291])

        return {
            'total_value': total_value,
            'asset_count': len(current_holdings),
            'algo_percentage': algo_value / total_value if total_value > 0 else 0,
            'stable_percentage': stable_value / total_value if total_value > 0 else 0,
            'exotic_percentage': 1 - (algo_value + stable_value) / total_value if total_value > 0 else 0
        }

    def _analyze_portfolio_diversification(self, current_holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze portfolio diversification"""
        if not current_holdings:
            return {'diversity_score': 0.0}

        total_value = sum(h['value_usd'] for h in current_holdings)
        percentages = [h['value_usd'] / total_value for h in current_holdings if total_value > 0]

        # Herfindahl-Hirschman Index
        hhi = sum(p ** 2 for p in percentages)
        diversity_score = 1 - hhi if len(current_holdings) > 1 else 0

        return {
            'diversity_score': diversity_score,
            'largest_position': max(percentages) if percentages else 0,
            'position_count': len(current_holdings)
        }

    def _analyze_portfolio_risk(self, current_holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze portfolio risk characteristics"""
        # Mock implementation
        return {
            'volatility_score': 0.6,
            'correlation_risk': 0.4,
            'liquidity_risk': 0.3
        }

    def _analyze_portfolio_management(
        self,
        current_holdings: List[Dict[str, Any]],
        historical_holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze portfolio management patterns"""
        # Mock implementation
        return {
            'rebalancing_frequency': 2,  # Times per year
            'growth_pattern': 'steady',
            'management_sophistication': 0.7
        }

    def _analyze_nft_portfolio(self, nft_holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze NFT portfolio"""
        if not nft_holdings:
            return {'nft_count': 0}

        total_floor_value = sum(nft.get('floor_price', 0) for nft in nft_holdings)
        collections = set(nft.get('collection') for nft in nft_holdings)

        return {
            'nft_count': len(nft_holdings),
            'collection_count': len(collections),
            'total_floor_value': total_floor_value,
            'average_hold_time': 60  # Mock data
        }

    def _calculate_portfolio_scores(self, *analyses) -> Dict[str, float]:
        """Calculate portfolio scores"""
        composition, diversification, risk_analysis, management_patterns = analyses

        return {
            'diversification_score': diversification.get('diversity_score', 0) * 100,
            'risk_score': (1 - risk_analysis.get('volatility_score', 0.5)) * 100,
            'management_score': management_patterns.get('management_sophistication', 0.5) * 100
        }

    def _empty_transaction_analysis(self) -> Dict[str, Any]:
        """Return empty transaction analysis for wallets with no transactions"""
        return {
            'temporal_patterns': {},
            'volume_patterns': {},
            'counterparty_patterns': {},
            'fee_patterns': {},
            'automation_patterns': {'automation_detected': False},
            'pattern_scores': {'consistency': 0, 'diversity': 0, 'optimization': 0, 'sophistication': 0},
            'total_transactions': 0,
            'analysis_period_days': 0
        }

    def _calculate_analysis_period(self, tx_history: List[Dict[str, Any]]) -> int:
        """Calculate analysis period from transaction history"""
        if not tx_history:
            return 0

        sorted_txs = sorted(tx_history, key=lambda x: x['timestamp'])
        return (sorted_txs[-1]['timestamp'] - sorted_txs[0]['timestamp']).days