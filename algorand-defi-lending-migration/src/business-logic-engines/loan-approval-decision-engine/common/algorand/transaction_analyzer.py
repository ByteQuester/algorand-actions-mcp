"""
Transaction Analyzer

Analyzes historical transaction patterns to understand borrower behavior,
financial habits, and risk indicators from on-chain activity.
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
class TransactionPattern:
    """Represents identified transaction patterns"""
    pattern_type: str
    frequency: float
    significance: float
    risk_indicator: bool
    description: str


@dataclass
class TransactionAnalysisResult:
    """Results of comprehensive transaction analysis"""
    total_transactions: int
    analysis_period_days: int
    avg_daily_frequency: float
    transaction_patterns: List[TransactionPattern]
    risk_score: float
    sophistication_score: float
    consistency_score: float
    behavior_summary: Dict[str, Any]


class TransactionAnalyzer:
    """
    Analyzes transaction history to extract behavioral patterns,
    risk indicators, and financial sophistication metrics.
    """

    def __init__(self):
        self.pattern_definitions = self._load_pattern_definitions()
        self.risk_thresholds = self._load_risk_thresholds()

    async def analyze_transaction_history(
        self,
        wallet_address: str,
        analysis_period_days: int = 365
    ) -> TransactionAnalysisResult:
        """
        Analyze complete transaction history for behavioral patterns.

        Args:
            wallet_address: Address to analyze
            analysis_period_days: Period to analyze (default 365 days)

        Returns:
            Comprehensive transaction analysis results
        """
        logger.info(f"Analyzing transaction history for {wallet_address}")

        try:
            # Fetch transaction data
            transactions = await self._fetch_transaction_data(
                wallet_address, analysis_period_days
            )

            if not transactions:
                logger.warning(f"No transactions found for {wallet_address}")
                return self._create_empty_analysis_result()

            # Parallel analysis of different aspects
            tasks = [
                self._analyze_frequency_patterns(transactions),
                self._analyze_volume_patterns(transactions),
                self._analyze_timing_patterns(transactions),
                self._analyze_counterparty_patterns(transactions),
                self._analyze_gas_patterns(transactions),
                self._analyze_application_patterns(transactions),
                self._detect_risk_patterns(transactions),
                self._assess_sophistication_indicators(transactions)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Extract analysis results
            frequency_analysis = results[0] if not isinstance(results[0], Exception) else {}
            volume_analysis = results[1] if not isinstance(results[1], Exception) else {}
            timing_analysis = results[2] if not isinstance(results[2], Exception) else {}
            counterparty_analysis = results[3] if not isinstance(results[3], Exception) else {}
            gas_analysis = results[4] if not isinstance(results[4], Exception) else {}
            application_analysis = results[5] if not isinstance(results[5], Exception) else {}
            risk_analysis = results[6] if not isinstance(results[6], Exception) else {}
            sophistication_analysis = results[7] if not isinstance(results[7], Exception) else {}

            # Compile comprehensive results
            patterns = self._compile_transaction_patterns(
                frequency_analysis, volume_analysis, timing_analysis,
                counterparty_analysis, gas_analysis, application_analysis
            )

            risk_score = self._calculate_risk_score(risk_analysis, patterns)
            sophistication_score = self._calculate_sophistication_score(sophistication_analysis)
            consistency_score = self._calculate_consistency_score(timing_analysis, frequency_analysis)

            behavior_summary = self._generate_behavior_summary(
                frequency_analysis, volume_analysis, timing_analysis,
                counterparty_analysis, application_analysis
            )

            return TransactionAnalysisResult(
                total_transactions=len(transactions),
                analysis_period_days=analysis_period_days,
                avg_daily_frequency=len(transactions) / analysis_period_days,
                transaction_patterns=patterns,
                risk_score=risk_score,
                sophistication_score=sophistication_score,
                consistency_score=consistency_score,
                behavior_summary=behavior_summary
            )

        except Exception as e:
            logger.error(f"Transaction analysis failed for {wallet_address}: {e}")
            raise

    async def _fetch_transaction_data(
        self,
        address: str,
        period_days: int
    ) -> List[Dict[str, Any]]:
        """Fetch transaction data from Algorand indexer"""
        # Mock implementation - would integrate with Algorand indexer API
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=period_days)

        # Generate mock transaction data
        transactions = []
        current_time = start_time

        # Simulate various transaction patterns
        while current_time < end_time:
            # Regular DeFi activity
            if current_time.weekday() < 5:  # Weekdays
                if 9 <= current_time.hour <= 17:  # Business hours
                    # Higher activity during business hours
                    tx_count = 2
                else:
                    tx_count = 1
            else:  # Weekends
                tx_count = 1

            for _ in range(tx_count):
                tx = self._generate_mock_transaction(current_time, address)
                transactions.append(tx)

            # Move to next day with some randomness
            current_time += timedelta(days=1, hours=0.5)

        return sorted(transactions, key=lambda x: x['timestamp'])

    def _generate_mock_transaction(self, timestamp: datetime, address: str) -> Dict[str, Any]:
        """Generate mock transaction data for testing"""
        import random

        tx_types = ['payment', 'app_call', 'asset_transfer', 'asset_config']
        app_types = ['swap', 'lend', 'stake', 'governance', 'nft']

        return {
            'id': f"tx_{timestamp.isoformat()}_{random.randint(1000, 9999)}",
            'timestamp': timestamp,
            'sender': address,
            'type': random.choice(tx_types),
            'amount': random.uniform(10, 10000),
            'fee': random.uniform(0.001, 0.01),
            'app_id': random.randint(1, 1000) if random.random() > 0.3 else None,
            'app_type': random.choice(app_types) if random.random() > 0.3 else None,
            'asset_id': random.randint(1, 1000000) if random.random() > 0.5 else None,
            'receiver': f"receiver_{random.randint(1, 100)}",
            'note': f"Transaction note {random.randint(1, 100)}",
            'group_id': f"group_{random.randint(1, 50)}" if random.random() > 0.8 else None
        }

    async def _analyze_frequency_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction frequency patterns"""
        daily_counts = defaultdict(int)

        for tx in transactions:
            date = tx['timestamp'].date()
            daily_counts[date] += 1

        if not daily_counts:
            return {}

        counts = list(daily_counts.values())
        return {
            'avg_daily_transactions': statistics.mean(counts),
            'median_daily_transactions': statistics.median(counts),
            'max_daily_transactions': max(counts),
            'std_daily_transactions': statistics.stdev(counts) if len(counts) > 1 else 0,
            'zero_activity_days': sum(1 for count in counts if count == 0),
            'high_activity_days': sum(1 for count in counts if count > statistics.mean(counts) * 2),
            'frequency_consistency': 1.0 - (statistics.stdev(counts) / statistics.mean(counts)) if statistics.mean(counts) > 0 else 0
        }

    async def _analyze_volume_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction volume patterns"""
        volumes = [tx['amount'] for tx in transactions if tx.get('amount', 0) > 0]

        if not volumes:
            return {}

        total_volume = sum(volumes)
        return {
            'total_volume': total_volume,
            'avg_transaction_size': statistics.mean(volumes),
            'median_transaction_size': statistics.median(volumes),
            'max_transaction_size': max(volumes),
            'volume_concentration': max(volumes) / total_volume if total_volume > 0 else 0,
            'large_transaction_ratio': sum(1 for v in volumes if v > statistics.mean(volumes) * 5) / len(volumes),
            'micro_transaction_ratio': sum(1 for v in volumes if v < 10) / len(volumes),
            'volume_consistency': 1.0 - (statistics.stdev(volumes) / statistics.mean(volumes)) if statistics.mean(volumes) > 0 else 0
        }

    async def _analyze_timing_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction timing patterns"""
        hours = [tx['timestamp'].hour for tx in transactions]
        weekdays = [tx['timestamp'].weekday() for tx in transactions]

        hour_distribution = {hour: hours.count(hour) for hour in range(24)}
        weekday_distribution = {day: weekdays.count(day) for day in range(7)}

        # Calculate peak activity periods
        peak_hour = max(hour_distribution, key=hour_distribution.get)
        business_hours_ratio = sum(hour_distribution[h] for h in range(9, 18)) / len(transactions)
        weekend_ratio = sum(weekday_distribution[d] for d in [5, 6]) / len(transactions)

        return {
            'peak_activity_hour': peak_hour,
            'business_hours_ratio': business_hours_ratio,
            'weekend_activity_ratio': weekend_ratio,
            'hour_distribution': hour_distribution,
            'weekday_distribution': weekday_distribution,
            'time_zone_consistency': self._calculate_timezone_consistency(hours),
            'activity_spread': len([h for h in hour_distribution.values() if h > 0]) / 24
        }

    async def _analyze_counterparty_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in transaction counterparties"""
        receivers = [tx.get('receiver') for tx in transactions if tx.get('receiver')]
        receiver_counts = defaultdict(int)

        for receiver in receivers:
            receiver_counts[receiver] += 1

        unique_counterparties = len(receiver_counts)
        total_transactions = len(receivers)

        if total_transactions == 0:
            return {}

        # Calculate concentration
        max_counterparty_count = max(receiver_counts.values()) if receiver_counts else 0
        concentration_ratio = max_counterparty_count / total_transactions

        return {
            'unique_counterparties': unique_counterparties,
            'counterparty_diversity': unique_counterparties / total_transactions,
            'max_counterparty_frequency': max_counterparty_count,
            'counterparty_concentration': concentration_ratio,
            'new_counterparty_ratio': self._calculate_new_counterparty_ratio(transactions),
            'repeat_interaction_score': 1.0 - (unique_counterparties / total_transactions)
        }

    async def _analyze_gas_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze gas fee patterns for optimization insights"""
        fees = [tx.get('fee', 0) for tx in transactions if tx.get('fee', 0) > 0]

        if not fees:
            return {}

        avg_fee = statistics.mean(fees)
        return {
            'avg_fee': avg_fee,
            'median_fee': statistics.median(fees),
            'max_fee': max(fees),
            'min_fee': min(fees),
            'fee_consistency': 1.0 - (statistics.stdev(fees) / avg_fee) if avg_fee > 0 else 0,
            'gas_optimization_score': self._calculate_gas_optimization_score(fees),
            'overpayment_frequency': sum(1 for f in fees if f > avg_fee * 1.5) / len(fees)
        }

    async def _analyze_application_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze smart contract and application interaction patterns"""
        app_interactions = [tx for tx in transactions if tx.get('app_id')]
        app_types = [tx.get('app_type') for tx in app_interactions if tx.get('app_type')]

        unique_apps = len(set(tx.get('app_id') for tx in app_interactions))
        app_type_distribution = defaultdict(int)

        for app_type in app_types:
            app_type_distribution[app_type] += 1

        return {
            'total_app_interactions': len(app_interactions),
            'unique_apps_interacted': unique_apps,
            'app_interaction_ratio': len(app_interactions) / len(transactions) if transactions else 0,
            'app_type_distribution': dict(app_type_distribution),
            'app_diversity_score': unique_apps / len(app_interactions) if app_interactions else 0,
            'defi_interaction_ratio': app_type_distribution.get('swap', 0) + app_type_distribution.get('lend', 0) / len(app_interactions) if app_interactions else 0
        }

    async def _detect_risk_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Detect patterns that might indicate risk"""
        risk_indicators = {
            'rapid_succession_transactions': 0,
            'unusual_timing_patterns': 0,
            'suspicious_volume_spikes': 0,
            'potential_wash_trading': 0,
            'high_fee_transactions': 0
        }

        # Detect rapid succession (transactions within 1 minute)
        sorted_txs = sorted(transactions, key=lambda x: x['timestamp'])
        for i in range(1, len(sorted_txs)):
            time_diff = (sorted_txs[i]['timestamp'] - sorted_txs[i-1]['timestamp']).total_seconds()
            if time_diff < 60:  # Less than 1 minute
                risk_indicators['rapid_succession_transactions'] += 1

        # Detect unusual timing (3 AM - 6 AM activity)
        unusual_time_count = sum(1 for tx in transactions if 3 <= tx['timestamp'].hour <= 6)
        risk_indicators['unusual_timing_patterns'] = unusual_time_count

        # Detect volume spikes
        volumes = [tx.get('amount', 0) for tx in transactions if tx.get('amount', 0) > 0]
        if volumes:
            avg_volume = statistics.mean(volumes)
            spike_count = sum(1 for v in volumes if v > avg_volume * 10)
            risk_indicators['suspicious_volume_spikes'] = spike_count

        # Detect potential wash trading (same counterparty multiple times in short period)
        risk_indicators['potential_wash_trading'] = self._detect_wash_trading_patterns(transactions)

        # High fee transactions (potential urgency or mistakes)
        fees = [tx.get('fee', 0) for tx in transactions if tx.get('fee', 0) > 0]
        if fees:
            avg_fee = statistics.mean(fees)
            high_fee_count = sum(1 for f in fees if f > avg_fee * 3)
            risk_indicators['high_fee_transactions'] = high_fee_count

        return risk_indicators

    async def _assess_sophistication_indicators(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Assess indicators of financial and technical sophistication"""
        sophistication_indicators = {
            'multi_asset_usage': 0,
            'complex_application_usage': 0,
            'optimization_behaviors': 0,
            'advanced_features_usage': 0,
            'strategic_timing': 0
        }

        # Multi-asset usage
        unique_assets = len(set(tx.get('asset_id') for tx in transactions if tx.get('asset_id')))
        sophistication_indicators['multi_asset_usage'] = unique_assets

        # Complex application usage
        complex_apps = ['lend', 'stake', 'governance']
        complex_interactions = sum(1 for tx in transactions
                                 if tx.get('app_type') in complex_apps)
        sophistication_indicators['complex_application_usage'] = complex_interactions

        # Fee optimization behaviors
        fees = [tx.get('fee', 0) for tx in transactions if tx.get('fee', 0) > 0]
        if fees:
            fee_variance = statistics.stdev(fees) / statistics.mean(fees) if statistics.mean(fees) > 0 else 1
            sophistication_indicators['optimization_behaviors'] = 1.0 - min(fee_variance, 1.0)

        # Group transactions (batch operations)
        grouped_txs = sum(1 for tx in transactions if tx.get('group_id'))
        sophistication_indicators['advanced_features_usage'] = grouped_txs

        # Strategic timing (avoiding high activity periods)
        business_hour_txs = sum(1 for tx in transactions if 9 <= tx['timestamp'].hour <= 17)
        strategic_timing_score = 1.0 - (business_hour_txs / len(transactions)) if transactions else 0
        sophistication_indicators['strategic_timing'] = strategic_timing_score

        return sophistication_indicators

    def _compile_transaction_patterns(self, *analysis_results) -> List[TransactionPattern]:
        """Compile identified patterns into structured format"""
        patterns = []

        frequency_analysis, volume_analysis, timing_analysis, counterparty_analysis, gas_analysis, application_analysis = analysis_results

        # Frequency patterns
        if frequency_analysis.get('frequency_consistency', 0) > 0.8:
            patterns.append(TransactionPattern(
                pattern_type="consistent_activity",
                frequency=frequency_analysis.get('avg_daily_transactions', 0),
                significance=frequency_analysis.get('frequency_consistency', 0),
                risk_indicator=False,
                description="Consistent daily transaction activity"
            ))

        # Volume patterns
        if volume_analysis.get('large_transaction_ratio', 0) > 0.1:
            patterns.append(TransactionPattern(
                pattern_type="large_transaction_pattern",
                frequency=volume_analysis.get('large_transaction_ratio', 0),
                significance=0.7,
                risk_indicator=True,
                description="Frequent large transactions"
            ))

        # Timing patterns
        if timing_analysis.get('weekend_activity_ratio', 0) > 0.3:
            patterns.append(TransactionPattern(
                pattern_type="weekend_activity",
                frequency=timing_analysis.get('weekend_activity_ratio', 0),
                significance=0.6,
                risk_indicator=False,
                description="Active weekend trading"
            ))

        # Gas optimization
        if gas_analysis.get('gas_optimization_score', 0) > 0.8:
            patterns.append(TransactionPattern(
                pattern_type="gas_optimization",
                frequency=gas_analysis.get('gas_optimization_score', 0),
                significance=0.8,
                risk_indicator=False,
                description="Consistent gas fee optimization"
            ))

        return patterns

    def _calculate_risk_score(self, risk_analysis: Dict, patterns: List[TransactionPattern]) -> float:
        """Calculate overall risk score from analysis"""
        base_risk = 30.0  # Base risk score

        # Add risk from detected indicators
        risk_factors = risk_analysis.get('rapid_succession_transactions', 0)
        base_risk += min(risk_factors * 2, 20)

        suspicious_volumes = risk_analysis.get('suspicious_volume_spikes', 0)
        base_risk += min(suspicious_volumes * 3, 15)

        wash_trading = risk_analysis.get('potential_wash_trading', 0)
        base_risk += min(wash_trading * 5, 25)

        # Reduce risk for positive patterns
        positive_patterns = [p for p in patterns if not p.risk_indicator]
        risk_reduction = len(positive_patterns) * 3
        base_risk = max(base_risk - risk_reduction, 10)

        return min(base_risk, 100.0)

    def _calculate_sophistication_score(self, sophistication_analysis: Dict) -> float:
        """Calculate sophistication score"""
        base_score = 30.0

        # Multi-asset usage
        asset_diversity = sophistication_analysis.get('multi_asset_usage', 0)
        base_score += min(asset_diversity * 2, 20)

        # Complex application usage
        complex_usage = sophistication_analysis.get('complex_application_usage', 0)
        base_score += min(complex_usage * 0.5, 15)

        # Optimization behaviors
        optimization = sophistication_analysis.get('optimization_behaviors', 0)
        base_score += optimization * 20

        # Advanced features
        advanced_usage = sophistication_analysis.get('advanced_features_usage', 0)
        base_score += min(advanced_usage * 0.2, 10)

        # Strategic timing
        strategic_timing = sophistication_analysis.get('strategic_timing', 0)
        base_score += strategic_timing * 5

        return min(base_score, 100.0)

    def _calculate_consistency_score(self, timing_analysis: Dict, frequency_analysis: Dict) -> float:
        """Calculate behavioral consistency score"""
        timing_consistency = timing_analysis.get('time_zone_consistency', 0.5)
        frequency_consistency = frequency_analysis.get('frequency_consistency', 0.5)

        return ((timing_consistency + frequency_consistency) / 2) * 100

    def _generate_behavior_summary(self, *analysis_results) -> Dict[str, Any]:
        """Generate comprehensive behavior summary"""
        frequency_analysis, volume_analysis, timing_analysis, counterparty_analysis, application_analysis = analysis_results

        return {
            'primary_activity_period': self._determine_primary_activity_period(timing_analysis),
            'transaction_size_profile': self._determine_transaction_size_profile(volume_analysis),
            'counterparty_behavior': self._determine_counterparty_behavior(counterparty_analysis),
            'application_usage_profile': self._determine_application_usage_profile(application_analysis),
            'overall_activity_level': self._determine_activity_level(frequency_analysis)
        }

    def _determine_primary_activity_period(self, timing_analysis: Dict) -> str:
        """Determine primary activity period"""
        business_ratio = timing_analysis.get('business_hours_ratio', 0)
        weekend_ratio = timing_analysis.get('weekend_activity_ratio', 0)

        if business_ratio > 0.6:
            return "business_hours"
        elif weekend_ratio > 0.4:
            return "weekend_active"
        else:
            return "distributed"

    def _determine_transaction_size_profile(self, volume_analysis: Dict) -> str:
        """Determine transaction size profile"""
        large_ratio = volume_analysis.get('large_transaction_ratio', 0)
        micro_ratio = volume_analysis.get('micro_transaction_ratio', 0)

        if large_ratio > 0.2:
            return "large_transaction_focused"
        elif micro_ratio > 0.5:
            return "micro_transaction_focused"
        else:
            return "balanced"

    def _determine_counterparty_behavior(self, counterparty_analysis: Dict) -> str:
        """Determine counterparty interaction behavior"""
        diversity = counterparty_analysis.get('counterparty_diversity', 0)
        concentration = counterparty_analysis.get('counterparty_concentration', 0)

        if diversity > 0.7:
            return "highly_diversified"
        elif concentration > 0.5:
            return "concentrated"
        else:
            return "moderately_diversified"

    def _determine_application_usage_profile(self, application_analysis: Dict) -> str:
        """Determine application usage profile"""
        app_ratio = application_analysis.get('app_interaction_ratio', 0)
        defi_ratio = application_analysis.get('defi_interaction_ratio', 0)

        if app_ratio > 0.7 and defi_ratio > 0.5:
            return "defi_power_user"
        elif app_ratio > 0.4:
            return "active_dapp_user"
        else:
            return "basic_user"

    def _determine_activity_level(self, frequency_analysis: Dict) -> str:
        """Determine overall activity level"""
        avg_daily = frequency_analysis.get('avg_daily_transactions', 0)

        if avg_daily > 5:
            return "very_active"
        elif avg_daily > 2:
            return "active"
        elif avg_daily > 0.5:
            return "moderate"
        else:
            return "low"

    def _calculate_timezone_consistency(self, hours: List[int]) -> float:
        """Calculate consistency in timezone/activity hours"""
        if not hours:
            return 0.0

        hour_counts = defaultdict(int)
        for hour in hours:
            hour_counts[hour] += 1

        # Calculate entropy-like measure
        total = len(hours)
        entropy = 0
        for count in hour_counts.values():
            p = count / total
            entropy -= p * (p if p == 0 else __import__('math').log2(p))

        # Normalize to 0-1 (lower entropy = higher consistency)
        max_entropy = __import__('math').log2(24)
        consistency = 1.0 - (entropy / max_entropy)
        return max(consistency, 0.0)

    def _calculate_new_counterparty_ratio(self, transactions: List[Dict]) -> float:
        """Calculate ratio of new vs returning counterparties over time"""
        seen_counterparties = set()
        new_counterparty_count = 0

        for tx in sorted(transactions, key=lambda x: x['timestamp']):
            counterparty = tx.get('receiver')
            if counterparty and counterparty not in seen_counterparties:
                new_counterparty_count += 1
                seen_counterparties.add(counterparty)

        return new_counterparty_count / len(transactions) if transactions else 0

    def _calculate_gas_optimization_score(self, fees: List[float]) -> float:
        """Calculate gas optimization score based on fee consistency"""
        if not fees or len(fees) < 2:
            return 0.5

        avg_fee = statistics.mean(fees)
        fee_variance = statistics.stdev(fees)

        # Lower variance relative to mean indicates better optimization
        if avg_fee == 0:
            return 0.5

        optimization_score = 1.0 - min(fee_variance / avg_fee, 1.0)
        return max(optimization_score, 0.0)

    def _detect_wash_trading_patterns(self, transactions: List[Dict]) -> int:
        """Detect potential wash trading patterns"""
        # Look for rapid back-and-forth transactions with same counterparty
        wash_trading_count = 0
        counterparty_times = defaultdict(list)

        for tx in transactions:
            counterparty = tx.get('receiver')
            if counterparty:
                counterparty_times[counterparty].append(tx['timestamp'])

        # Check for rapid sequences
        for counterparty, times in counterparty_times.items():
            if len(times) < 3:
                continue

            sorted_times = sorted(times)
            for i in range(len(sorted_times) - 2):
                # Check if 3+ transactions within 1 hour
                time_span = sorted_times[i + 2] - sorted_times[i]
                if time_span.total_seconds() < 3600:  # 1 hour
                    wash_trading_count += 1

        return wash_trading_count

    def _create_empty_analysis_result(self) -> TransactionAnalysisResult:
        """Create empty analysis result for addresses with no transactions"""
        return TransactionAnalysisResult(
            total_transactions=0,
            analysis_period_days=0,
            avg_daily_frequency=0.0,
            transaction_patterns=[],
            risk_score=50.0,  # Medium risk for no data
            sophistication_score=0.0,
            consistency_score=0.0,
            behavior_summary={}
        )

    def _load_pattern_definitions(self) -> Dict[str, Dict]:
        """Load transaction pattern definitions"""
        return {
            'consistent_activity': {
                'description': 'Regular transaction frequency',
                'risk_weight': -0.1,
                'sophistication_weight': 0.1
            },
            'large_transaction_pattern': {
                'description': 'Frequent large value transactions',
                'risk_weight': 0.2,
                'sophistication_weight': 0.0
            },
            'gas_optimization': {
                'description': 'Optimized gas fee usage',
                'risk_weight': -0.05,
                'sophistication_weight': 0.15
            }
        }

    def _load_risk_thresholds(self) -> Dict[str, float]:
        """Load risk detection thresholds"""
        return {
            'rapid_succession_threshold': 60,  # seconds
            'volume_spike_multiplier': 10,
            'high_fee_multiplier': 3,
            'wash_trading_time_window': 3600  # seconds
        }