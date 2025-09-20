"""
DeFi Behavior Pattern Analysis Engine

Analyzes risk tolerance, yield farming strategies, portfolio management patterns,
and overall DeFi sophistication of borrowers.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import yaml
import logging
from pathlib import Path
from collections import defaultdict
import statistics

@dataclass
class BehaviorMetrics:
    """Comprehensive behavior metrics"""
    risk_tolerance_score: float
    yield_strategy_sophistication: float
    portfolio_management_score: float
    market_timing_ability: float
    diversification_discipline: float
    loss_management_score: float
    profit_taking_discipline: float
    consistency_score: float

@dataclass
class MarketCycleBehavior:
    """Behavior during different market cycles"""
    bull_market_behavior: Dict[str, float]
    bear_market_behavior: Dict[str, float]
    volatility_response: Dict[str, float]
    cycle_adaptation_score: float

@dataclass
class BehaviorPatternAnalysis:
    """Complete behavior pattern analysis results"""
    address: str
    analysis_timestamp: datetime
    behavior_metrics: BehaviorMetrics
    market_cycle_behavior: MarketCycleBehavior
    risk_profile_evolution: Dict[str, Any]
    strategy_patterns: List[str]
    behavioral_red_flags: List[str]
    behavioral_strengths: List[str]
    overall_behavior_score: float
    confidence_level: float

class BehaviorPatternAnalyzer:
    """Advanced DeFi behavior pattern analysis engine"""

    def __init__(self, config_path: str = None):
        """Initialize the behavior pattern analyzer"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.behavior_scoring = self.config['behavior_scoring']
        self.risk_thresholds = self.config['risk_thresholds']
        self.pattern_analysis = self.config['pattern_analysis']
        self.market_cycle_analysis = self.config['market_cycle_analysis']

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def analyze_behavior_patterns(self,
                                      protocol_activities: Dict[str, Any],
                                      market_data: Dict[str, Any],
                                      historical_period_days: int = 365) -> BehaviorPatternAnalysis:
        """
        Comprehensive behavior pattern analysis

        Args:
            protocol_activities: Cross-protocol activity data
            market_data: Historical market condition data
            historical_period_days: Analysis period

        Returns:
            BehaviorPatternAnalysis with detailed behavioral assessment
        """
        try:
            self.logger.info("Starting comprehensive behavior pattern analysis")

            # Extract transaction timeline for analysis
            transaction_timeline = self._build_transaction_timeline(protocol_activities)

            # Analyze behavior metrics
            behavior_metrics = self._analyze_behavior_metrics(
                transaction_timeline, protocol_activities
            )

            # Analyze market cycle behavior
            market_cycle_behavior = self._analyze_market_cycle_behavior(
                transaction_timeline, market_data
            )

            # Track risk profile evolution
            risk_profile_evolution = self._analyze_risk_profile_evolution(
                transaction_timeline, market_data
            )

            # Identify strategy patterns
            strategy_patterns = self._identify_strategy_patterns(
                transaction_timeline, protocol_activities
            )

            # Detect behavioral red flags
            behavioral_red_flags = self._detect_behavioral_red_flags(
                behavior_metrics, market_cycle_behavior, transaction_timeline
            )

            # Identify behavioral strengths
            behavioral_strengths = self._identify_behavioral_strengths(
                behavior_metrics, market_cycle_behavior
            )

            # Calculate overall behavior score
            overall_score, confidence = self._calculate_overall_behavior_score(
                behavior_metrics, market_cycle_behavior, len(transaction_timeline)
            )

            analysis = BehaviorPatternAnalysis(
                address=protocol_activities.get('address', 'unknown'),
                analysis_timestamp=datetime.now(),
                behavior_metrics=behavior_metrics,
                market_cycle_behavior=market_cycle_behavior,
                risk_profile_evolution=risk_profile_evolution,
                strategy_patterns=strategy_patterns,
                behavioral_red_flags=behavioral_red_flags,
                behavioral_strengths=behavioral_strengths,
                overall_behavior_score=overall_score,
                confidence_level=confidence
            )

            self.logger.info("Behavior pattern analysis completed successfully")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in behavior pattern analysis: {str(e)}")
            raise

    def _build_transaction_timeline(self, protocol_activities: Dict[str, Any]) -> List[Dict]:
        """Build chronological transaction timeline across all protocols"""
        timeline = []

        for protocol_id, activity in protocol_activities.items():
            if hasattr(activity, 'protocol_specific_metrics'):
                # Extract individual transactions with timestamps
                transactions = activity.protocol_specific_metrics.get('transactions', [])
                for tx in transactions:
                    timeline.append({
                        'timestamp': tx.get('timestamp', datetime.now()),
                        'protocol': protocol_id,
                        'type': tx.get('type', 'unknown'),
                        'amount_usd': tx.get('amount_usd', 0),
                        'risk_level': tx.get('risk_level', 'medium'),
                        'market_condition': tx.get('market_condition', 'normal'),
                        'transaction_data': tx
                    })

        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        return timeline

    def _analyze_behavior_metrics(self, timeline: List[Dict],
                                protocol_activities: Dict[str, Any]) -> BehaviorMetrics:
        """Analyze core behavioral metrics"""

        # Risk tolerance analysis
        risk_tolerance = self._calculate_risk_tolerance(timeline)

        # Yield strategy sophistication
        yield_sophistication = self._assess_yield_strategy_sophistication(
            timeline, protocol_activities
        )

        # Portfolio management score
        portfolio_management = self._assess_portfolio_management(timeline)

        # Market timing ability
        market_timing = self._assess_market_timing_ability(timeline)

        # Diversification discipline
        diversification = self._assess_diversification_discipline(
            timeline, protocol_activities
        )

        # Loss management
        loss_management = self._assess_loss_management(timeline)

        # Profit taking discipline
        profit_taking = self._assess_profit_taking_discipline(timeline)

        # Consistency score
        consistency = self._assess_behavioral_consistency(timeline)

        return BehaviorMetrics(
            risk_tolerance_score=risk_tolerance,
            yield_strategy_sophistication=yield_sophistication,
            portfolio_management_score=portfolio_management,
            market_timing_ability=market_timing,
            diversification_discipline=diversification,
            loss_management_score=loss_management,
            profit_taking_discipline=profit_taking,
            consistency_score=consistency
        )

    def _calculate_risk_tolerance(self, timeline: List[Dict]) -> float:
        """Calculate risk tolerance based on transaction patterns"""
        if not timeline:
            return 0.0

        risk_indicators = []

        # Analyze risk levels of transactions
        risk_levels = [tx.get('risk_level', 'medium') for tx in timeline]
        high_risk_ratio = risk_levels.count('high') / len(risk_levels)
        risk_indicators.append(high_risk_ratio)

        # Analyze position sizes relative to portfolio
        amounts = [tx.get('amount_usd', 0) for tx in timeline if tx.get('amount_usd', 0) > 0]
        if amounts:
            position_size_variation = np.std(amounts) / np.mean(amounts) if np.mean(amounts) > 0 else 0
            risk_indicators.append(min(position_size_variation / 2.0, 1.0))

        # Analyze leverage usage patterns
        leverage_transactions = [
            tx for tx in timeline
            if 'leverage' in tx.get('type', '').lower() or
               tx.get('transaction_data', {}).get('leverage_ratio', 1.0) > 1.0
        ]
        leverage_ratio = len(leverage_transactions) / len(timeline)
        risk_indicators.append(leverage_ratio)

        # Analyze protocol risk distribution
        protocol_risks = defaultdict(int)
        for tx in timeline:
            protocol = tx.get('protocol', 'unknown')
            protocol_risks[protocol] += 1

        # Weight by protocol risk factors
        weighted_protocol_risk = 0
        total_transactions = len(timeline)

        for protocol, count in protocol_risks.items():
            if protocol in self.config.get('protocols', {}):
                risk_factor = self.config['protocols'][protocol].get('risk_factor', 1.0)
                weighted_protocol_risk += (count / total_transactions) * (risk_factor - 1.0)

        risk_indicators.append(min(weighted_protocol_risk, 1.0))

        # Calculate overall risk tolerance score
        risk_tolerance = np.mean(risk_indicators)
        return round(min(risk_tolerance, 1.0), 3)

    def _assess_yield_strategy_sophistication(self, timeline: List[Dict],
                                            protocol_activities: Dict[str, Any]) -> float:
        """Assess sophistication of yield farming strategies"""

        sophistication_indicators = []

        # Multi-protocol yield strategies
        yield_protocols = set()
        for tx in timeline:
            if any(keyword in tx.get('type', '').lower()
                  for keyword in ['yield', 'farm', 'stake', 'lp']):
                yield_protocols.add(tx.get('protocol'))

        multi_protocol_score = min(len(yield_protocols) / 4.0, 1.0)  # 4+ protocols = max
        sophistication_indicators.append(multi_protocol_score)

        # Strategy complexity analysis
        complex_strategies = 0
        for tx in timeline:
            tx_data = tx.get('transaction_data', {})

            # Auto-compounding strategies
            if tx_data.get('auto_compound', False):
                complex_strategies += 1

            # Cross-protocol arbitrage
            if 'arbitrage' in tx.get('type', '').lower():
                complex_strategies += 2

            # Leveraged yield farming
            if (tx_data.get('leverage_ratio', 1.0) > 1.0 and
                any(keyword in tx.get('type', '').lower() for keyword in ['yield', 'farm'])):
                complex_strategies += 2

        complexity_score = min(complex_strategies / len(timeline), 1.0) if timeline else 0
        sophistication_indicators.append(complexity_score)

        # Risk-adjusted yield optimization
        yield_transactions = [tx for tx in timeline if 'yield' in tx.get('type', '').lower()]
        if yield_transactions:
            # Analyze if user seeks high-risk high-reward vs stable yields
            risk_adjusted_choices = 0
            for tx in yield_transactions:
                risk_level = tx.get('risk_level', 'medium')
                amount = tx.get('amount_usd', 0)

                # Preference for balanced risk-reward
                if risk_level == 'medium' and amount > 1000:  # Substantial amounts in medium risk
                    risk_adjusted_choices += 1
                elif risk_level == 'low' and amount > 5000:  # Large amounts in low risk
                    risk_adjusted_choices += 1

            risk_adjustment_score = risk_adjusted_choices / len(yield_transactions)
            sophistication_indicators.append(risk_adjustment_score)

        # Timing of yield strategy deployment
        market_timing_score = self._assess_yield_timing(yield_transactions)
        sophistication_indicators.append(market_timing_score)

        return round(np.mean(sophistication_indicators), 3) if sophistication_indicators else 0.0

    def _assess_portfolio_management(self, timeline: List[Dict]) -> float:
        """Assess portfolio management discipline and skills"""

        management_indicators = []

        if not timeline:
            return 0.0

        # Position sizing discipline
        amounts = [tx.get('amount_usd', 0) for tx in timeline if tx.get('amount_usd', 0) > 0]
        if amounts:
            # Check for consistent position sizing (lower coefficient of variation = better)
            cv = np.std(amounts) / np.mean(amounts) if np.mean(amounts) > 0 else 0
            position_sizing_score = max(0, 1 - cv / 2)  # Lower variation = higher score
            management_indicators.append(position_sizing_score)

        # Rebalancing activity
        rebalancing_events = len([
            tx for tx in timeline
            if any(keyword in tx.get('type', '').lower()
                  for keyword in ['rebalance', 'withdraw', 'adjust'])
        ])
        rebalancing_frequency = rebalancing_events / (len(timeline) / 30)  # Per month
        rebalancing_score = min(rebalancing_frequency / 2, 1.0)  # 2 rebalances/month = optimal
        management_indicators.append(rebalancing_score)

        # Diversification maintenance
        monthly_protocols = defaultdict(set)
        for tx in timeline:
            month_key = tx['timestamp'].strftime('%Y-%m')
            monthly_protocols[month_key].add(tx.get('protocol'))

        diversification_consistency = []
        for month, protocols in monthly_protocols.items():
            diversification_consistency.append(len(protocols))

        if diversification_consistency:
            diversification_score = min(np.mean(diversification_consistency) / 5, 1.0)
            management_indicators.append(diversification_score)

        # Risk management discipline
        risk_management_score = self._assess_risk_management_discipline(timeline)
        management_indicators.append(risk_management_score)

        return round(np.mean(management_indicators), 3) if management_indicators else 0.0

    def _assess_market_timing_ability(self, timeline: List[Dict]) -> float:
        """Assess market timing skills"""

        timing_indicators = []

        if len(timeline) < 10:  # Need sufficient data
            return 0.5  # Neutral score

        # Analyze entry timing during market conditions
        entries_by_condition = defaultdict(int)
        exits_by_condition = defaultdict(int)

        for tx in timeline:
            market_condition = tx.get('market_condition', 'normal')
            tx_type = tx.get('type', '').lower()

            if any(keyword in tx_type for keyword in ['deposit', 'stake', 'add_liquidity', 'buy']):
                entries_by_condition[market_condition] += 1
            elif any(keyword in tx_type for keyword in ['withdraw', 'unstake', 'remove_liquidity', 'sell']):
                exits_by_condition[market_condition] += 1

        # Good timing: more entries during bear/dip, more exits during bull
        total_entries = sum(entries_by_condition.values())
        total_exits = sum(exits_by_condition.values())

        if total_entries > 0:
            bear_entry_ratio = (entries_by_condition['bear'] + entries_by_condition['dip']) / total_entries
            timing_indicators.append(bear_entry_ratio)

        if total_exits > 0:
            bull_exit_ratio = entries_by_condition['bull'] / total_exits
            timing_indicators.append(bull_exit_ratio)

        # Volatility timing
        volatile_period_performance = self._assess_volatility_timing(timeline)
        timing_indicators.append(volatile_period_performance)

        # Consistency of timing decisions
        timing_consistency = self._assess_timing_consistency(timeline)
        timing_indicators.append(timing_consistency)

        return round(np.mean(timing_indicators), 3) if timing_indicators else 0.5

    def _assess_diversification_discipline(self, timeline: List[Dict],
                                         protocol_activities: Dict[str, Any]) -> float:
        """Assess diversification discipline over time"""

        if not timeline:
            return 0.0

        # Protocol diversification over time
        monthly_diversification = defaultdict(set)
        for tx in timeline:
            month_key = tx['timestamp'].strftime('%Y-%m')
            monthly_diversification[month_key].add(tx.get('protocol'))

        diversification_scores = []
        for month, protocols in monthly_diversification.items():
            # Score based on number of protocols used (diminishing returns)
            score = min(len(protocols) / 5, 1.0)  # 5 protocols = max score
            diversification_scores.append(score)

        # Asset type diversification
        asset_types = defaultdict(int)
        for tx in timeline:
            tx_data = tx.get('transaction_data', {})
            asset_type = tx_data.get('asset_type', 'unknown')
            asset_types[asset_type] += 1

        asset_diversification = min(len(asset_types) / 4, 1.0)  # 4 asset types = max

        # Geographic/chain diversification (for cross-chain protocols)
        chain_diversification = self._assess_chain_diversification(timeline)

        # Risk level diversification
        risk_levels = [tx.get('risk_level', 'medium') for tx in timeline]
        risk_diversification = len(set(risk_levels)) / 3  # low, medium, high

        # Combine diversification metrics
        diversification_components = [
            np.mean(diversification_scores) if diversification_scores else 0,
            asset_diversification,
            chain_diversification,
            risk_diversification
        ]

        return round(np.mean(diversification_components), 3)

    def _assess_loss_management(self, timeline: List[Dict]) -> float:
        """Assess loss management and risk mitigation skills"""

        loss_management_indicators = []

        # Stop-loss behavior detection
        stop_loss_events = len([
            tx for tx in timeline
            if any(keyword in tx.get('type', '').lower()
                  for keyword in ['stop', 'emergency', 'liquidate'])
        ])

        stop_loss_discipline = min(stop_loss_events / max(len(timeline) * 0.1, 1), 1.0)
        loss_management_indicators.append(stop_loss_discipline)

        # Recovery behavior after losses
        loss_recovery_score = self._assess_loss_recovery_behavior(timeline)
        loss_management_indicators.append(loss_recovery_score)

        # Hedging activity
        hedging_transactions = len([
            tx for tx in timeline
            if any(keyword in tx.get('type', '').lower()
                  for keyword in ['hedge', 'insurance', 'protection'])
        ])

        hedging_score = min(hedging_transactions / max(len(timeline) * 0.05, 1), 1.0)
        loss_management_indicators.append(hedging_score)

        # Position management during stress
        stress_management_score = self._assess_stress_position_management(timeline)
        loss_management_indicators.append(stress_management_score)

        return round(np.mean(loss_management_indicators), 3) if loss_management_indicators else 0.0

    def _assess_profit_taking_discipline(self, timeline: List[Dict]) -> float:
        """Assess profit-taking discipline and strategy"""

        if not timeline:
            return 0.0

        profit_indicators = []

        # Systematic profit taking
        profit_taking_events = [
            tx for tx in timeline
            if any(keyword in tx.get('type', '').lower()
                  for keyword in ['withdraw', 'sell', 'claim'])
        ]

        if len(profit_taking_events) > 0:
            # Regular profit taking vs holding too long
            profit_frequency = len(profit_taking_events) / (len(timeline) / 30)  # Per month
            optimal_frequency_score = 1 - abs(profit_frequency - 1) / 2  # 1 per month optimal
            profit_indicators.append(max(optimal_frequency_score, 0))

            # Profit taking during favorable conditions
            bull_market_profit_taking = len([
                tx for tx in profit_taking_events
                if tx.get('market_condition') == 'bull'
            ])

            if len(profit_taking_events) > 0:
                bull_profit_ratio = bull_market_profit_taking / len(profit_taking_events)
                profit_indicators.append(bull_profit_ratio)

        # Avoiding greed patterns
        greed_avoidance = self._assess_greed_avoidance(timeline)
        profit_indicators.append(greed_avoidance)

        return round(np.mean(profit_indicators), 3) if profit_indicators else 0.0

    def _assess_behavioral_consistency(self, timeline: List[Dict]) -> float:
        """Assess consistency of behavioral patterns over time"""

        if len(timeline) < 20:  # Need sufficient data
            return 0.5

        # Analyze behavioral consistency across time windows
        time_windows = self._split_timeline_into_windows(timeline, window_days=30)

        consistency_metrics = []

        # Transaction frequency consistency
        window_frequencies = [len(window) for window in time_windows]
        freq_consistency = 1 - (np.std(window_frequencies) / np.mean(window_frequencies)) if window_frequencies and np.mean(window_frequencies) > 0 else 0
        consistency_metrics.append(max(freq_consistency, 0))

        # Risk level consistency
        risk_consistencies = []
        for window in time_windows:
            if window:
                risk_levels = [tx.get('risk_level', 'medium') for tx in window]
                risk_distribution = {level: risk_levels.count(level) / len(risk_levels) for level in set(risk_levels)}
                risk_consistencies.append(risk_distribution)

        if len(risk_consistencies) > 1:
            risk_consistency_score = self._calculate_distribution_consistency(risk_consistencies)
            consistency_metrics.append(risk_consistency_score)

        # Strategy consistency
        strategy_consistency = self._assess_strategy_consistency(time_windows)
        consistency_metrics.append(strategy_consistency)

        return round(np.mean(consistency_metrics), 3) if consistency_metrics else 0.5

    def _analyze_market_cycle_behavior(self, timeline: List[Dict],
                                     market_data: Dict[str, Any]) -> MarketCycleBehavior:
        """Analyze behavior during different market cycles"""

        # Categorize transactions by market conditions
        bull_transactions = [tx for tx in timeline if tx.get('market_condition') == 'bull']
        bear_transactions = [tx for tx in timeline if tx.get('market_condition') == 'bear']
        volatile_transactions = [tx for tx in timeline if tx.get('market_condition') == 'volatile']

        # Bull market behavior analysis
        bull_behavior = {
            'risk_escalation': self._calculate_risk_escalation_in_bull(bull_transactions),
            'profit_taking_discipline': self._assess_bull_profit_taking(bull_transactions),
            'leverage_usage': self._assess_bull_leverage_usage(bull_transactions),
            'fomo_resistance': self._assess_fomo_resistance(bull_transactions),
            'position_sizing_discipline': self._assess_bull_position_sizing(bull_transactions)
        }

        # Bear market behavior analysis
        bear_behavior = {
            'position_management': self._assess_bear_position_management(bear_transactions),
            'panic_selling_resistance': self._assess_panic_resistance(bear_transactions),
            'opportunity_recognition': self._assess_bear_opportunity_recognition(bear_transactions),
            'defensive_strategies': self._assess_defensive_strategies(bear_transactions),
            'liquidity_management': self._assess_bear_liquidity_management(bear_transactions)
        }

        # Volatility response analysis
        volatility_response = {
            'volatility_tolerance': self._assess_volatility_tolerance(volatile_transactions),
            'hedging_activation': self._assess_volatility_hedging(volatile_transactions),
            'opportunistic_trading': self._assess_volatility_opportunities(volatile_transactions),
            'stability_seeking': self._assess_stability_seeking(volatile_transactions)
        }

        # Calculate cycle adaptation score
        cycle_adaptation_score = self._calculate_cycle_adaptation_score(
            bull_behavior, bear_behavior, volatility_response
        )

        return MarketCycleBehavior(
            bull_market_behavior=bull_behavior,
            bear_market_behavior=bear_behavior,
            volatility_response=volatility_response,
            cycle_adaptation_score=cycle_adaptation_score
        )

    def _analyze_risk_profile_evolution(self, timeline: List[Dict],
                                      market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how risk profile evolves over time"""

        # Split timeline into quarters
        quarterly_data = self._split_timeline_by_quarters(timeline)

        risk_evolution = {
            'quarterly_risk_scores': [],
            'risk_trend': 'stable',
            'risk_adaptation_events': [],
            'learning_indicators': [],
            'maturity_progression': 0.0
        }

        for quarter, transactions in quarterly_data.items():
            if transactions:
                quarter_risk = self._calculate_risk_tolerance(transactions)
                risk_evolution['quarterly_risk_scores'].append({
                    'quarter': quarter,
                    'risk_score': quarter_risk,
                    'transaction_count': len(transactions)
                })

        # Determine risk trend
        if len(risk_evolution['quarterly_risk_scores']) >= 2:
            scores = [q['risk_score'] for q in risk_evolution['quarterly_risk_scores']]
            trend_slope = np.polyfit(range(len(scores)), scores, 1)[0]

            if trend_slope > 0.1:
                risk_evolution['risk_trend'] = 'increasing'
            elif trend_slope < -0.1:
                risk_evolution['risk_trend'] = 'decreasing'
            else:
                risk_evolution['risk_trend'] = 'stable'

        # Identify adaptation events
        risk_evolution['risk_adaptation_events'] = self._identify_risk_adaptation_events(timeline)

        # Learning indicators
        risk_evolution['learning_indicators'] = self._identify_learning_indicators(timeline)

        # Maturity progression
        risk_evolution['maturity_progression'] = self._calculate_maturity_progression(timeline)

        return risk_evolution

    def _identify_strategy_patterns(self, timeline: List[Dict],
                                  protocol_activities: Dict[str, Any]) -> List[str]:
        """Identify sophisticated DeFi strategy patterns"""

        patterns = []

        # Analyze transaction sequences for patterns
        sequences = self._extract_transaction_sequences(timeline)

        # Dollar-cost averaging pattern
        if self._detect_dca_pattern(sequences):
            patterns.append("Dollar-Cost Averaging")

        # Yield optimization pattern
        if self._detect_yield_optimization_pattern(sequences, protocol_activities):
            patterns.append("Active Yield Optimization")

        # Arbitrage pattern
        if self._detect_arbitrage_pattern(sequences):
            patterns.append("Cross-Protocol Arbitrage")

        # Market timing pattern
        if self._detect_market_timing_pattern(sequences):
            patterns.append("Strategic Market Timing")

        # Risk management pattern
        if self._detect_risk_management_pattern(sequences):
            patterns.append("Active Risk Management")

        # Liquidity provision optimization
        if self._detect_lp_optimization_pattern(sequences):
            patterns.append("Liquidity Provision Optimization")

        # Cross-chain strategies
        if self._detect_cross_chain_pattern(sequences):
            patterns.append("Cross-Chain Yield Strategies")

        return patterns

    def _detect_behavioral_red_flags(self, behavior_metrics: BehaviorMetrics,
                                   market_cycle_behavior: MarketCycleBehavior,
                                   timeline: List[Dict]) -> List[str]:
        """Detect behavioral red flags that indicate high risk"""

        red_flags = []

        # High risk tolerance without sophistication
        if (behavior_metrics.risk_tolerance_score > 0.8 and
            behavior_metrics.yield_strategy_sophistication < 0.4):
            red_flags.append("High risk appetite without adequate sophistication")

        # Poor loss management
        if behavior_metrics.loss_management_score < 0.3:
            red_flags.append("Inadequate loss management and risk mitigation")

        # Panic selling tendency
        if market_cycle_behavior.bear_market_behavior.get('panic_selling_resistance', 0) < 0.3:
            red_flags.append("High tendency for panic selling during market stress")

        # FOMO behavior
        if market_cycle_behavior.bull_market_behavior.get('fomo_resistance', 0) < 0.3:
            red_flags.append("Susceptible to FOMO and market euphoria")

        # Inconsistent behavior
        if behavior_metrics.consistency_score < 0.4:
            red_flags.append("Highly inconsistent behavioral patterns")

        # Over-leverage tendency
        if market_cycle_behavior.bull_market_behavior.get('leverage_usage', 0) > 0.8:
            red_flags.append("Excessive leverage usage during bull markets")

        # Poor diversification discipline
        if behavior_metrics.diversification_discipline < 0.3:
            red_flags.append("Poor diversification and concentration risk")

        # Inadequate profit-taking
        if behavior_metrics.profit_taking_discipline < 0.3:
            red_flags.append("Poor profit-taking discipline")

        # Recent high-risk behavior increase
        recent_transactions = [tx for tx in timeline if
                             (datetime.now() - tx['timestamp']).days < 30]
        if recent_transactions:
            recent_risk = self._calculate_risk_tolerance(recent_transactions)
            historical_risk = self._calculate_risk_tolerance(timeline[:-len(recent_transactions)])
            if recent_risk - historical_risk > 0.3:
                red_flags.append("Recent significant increase in risk-taking behavior")

        return red_flags

    def _identify_behavioral_strengths(self, behavior_metrics: BehaviorMetrics,
                                     market_cycle_behavior: MarketCycleBehavior) -> List[str]:
        """Identify behavioral strengths that indicate lower risk"""

        strengths = []

        # Strong risk management
        if behavior_metrics.loss_management_score > 0.7:
            strengths.append("Excellent risk management and loss mitigation")

        # Market timing skills
        if behavior_metrics.market_timing_ability > 0.7:
            strengths.append("Strong market timing and cycle awareness")

        # Diversification discipline
        if behavior_metrics.diversification_discipline > 0.7:
            strengths.append("Excellent diversification discipline")

        # Behavioral consistency
        if behavior_metrics.consistency_score > 0.7:
            strengths.append("Highly consistent behavioral patterns")

        # Sophisticated yield strategies
        if behavior_metrics.yield_strategy_sophistication > 0.7:
            strengths.append("Sophisticated yield optimization strategies")

        # Strong portfolio management
        if behavior_metrics.portfolio_management_score > 0.7:
            strengths.append("Excellent portfolio management skills")

        # Panic resistance
        if market_cycle_behavior.bear_market_behavior.get('panic_selling_resistance', 0) > 0.7:
            strengths.append("Strong resistance to panic selling")

        # FOMO resistance
        if market_cycle_behavior.bull_market_behavior.get('fomo_resistance', 0) > 0.7:
            strengths.append("Strong resistance to FOMO and market euphoria")

        # Cycle adaptation
        if market_cycle_behavior.cycle_adaptation_score > 0.7:
            strengths.append("Excellent market cycle adaptation")

        # Profit-taking discipline
        if behavior_metrics.profit_taking_discipline > 0.7:
            strengths.append("Strong profit-taking discipline")

        return strengths

    def _calculate_overall_behavior_score(self, behavior_metrics: BehaviorMetrics,
                                        market_cycle_behavior: MarketCycleBehavior,
                                        transaction_count: int) -> Tuple[float, float]:
        """Calculate overall behavior score and confidence level"""

        # Core behavior metrics weights
        core_weights = {
            'risk_tolerance': 0.15,
            'sophistication': 0.20,
            'portfolio_management': 0.15,
            'market_timing': 0.10,
            'diversification': 0.15,
            'loss_management': 0.15,
            'profit_taking': 0.10
        }

        # Calculate weighted core score
        core_score = (
            behavior_metrics.risk_tolerance_score * core_weights['risk_tolerance'] +
            behavior_metrics.yield_strategy_sophistication * core_weights['sophistication'] +
            behavior_metrics.portfolio_management_score * core_weights['portfolio_management'] +
            behavior_metrics.market_timing_ability * core_weights['market_timing'] +
            behavior_metrics.diversification_discipline * core_weights['diversification'] +
            behavior_metrics.loss_management_score * core_weights['loss_management'] +
            behavior_metrics.profit_taking_discipline * core_weights['profit_taking']
        )

        # Market cycle behavior adjustment
        cycle_adjustment = market_cycle_behavior.cycle_adaptation_score * 0.1

        # Consistency bonus/penalty
        consistency_adjustment = (behavior_metrics.consistency_score - 0.5) * 0.1

        # Calculate final score
        final_score = core_score + cycle_adjustment + consistency_adjustment
        final_score = max(0.0, min(1.0, final_score))  # Clamp to [0, 1]

        # Calculate confidence level based on data quantity and quality
        confidence = self._calculate_confidence_level(transaction_count, behavior_metrics)

        return round(final_score, 3), round(confidence, 3)

    def _calculate_confidence_level(self, transaction_count: int,
                                  behavior_metrics: BehaviorMetrics) -> float:
        """Calculate confidence level in the behavior analysis"""

        confidence_factors = []

        # Transaction count factor
        count_confidence = min(transaction_count / 100, 1.0)  # 100 transactions = full confidence
        confidence_factors.append(count_confidence)

        # Consistency factor (higher consistency = higher confidence)
        confidence_factors.append(behavior_metrics.consistency_score)

        # Data quality factor (based on metric completeness)
        metrics_values = [
            behavior_metrics.risk_tolerance_score,
            behavior_metrics.yield_strategy_sophistication,
            behavior_metrics.portfolio_management_score,
            behavior_metrics.market_timing_ability,
            behavior_metrics.diversification_discipline,
            behavior_metrics.loss_management_score,
            behavior_metrics.profit_taking_discipline
        ]

        data_quality = len([v for v in metrics_values if v > 0]) / len(metrics_values)
        confidence_factors.append(data_quality)

        return np.mean(confidence_factors)

    # Placeholder methods for detailed behavioral analysis
    # These would be implemented with more sophisticated algorithms in production

    def _assess_yield_timing(self, yield_transactions: List[Dict]) -> float:
        """Assess timing of yield strategy deployment"""
        return 0.6  # Placeholder

    def _assess_risk_management_discipline(self, timeline: List[Dict]) -> float:
        """Assess risk management discipline"""
        return 0.7  # Placeholder

    def _assess_volatility_timing(self, timeline: List[Dict]) -> float:
        """Assess performance during volatile periods"""
        return 0.6  # Placeholder

    def _assess_timing_consistency(self, timeline: List[Dict]) -> float:
        """Assess consistency of timing decisions"""
        return 0.7  # Placeholder

    def _assess_chain_diversification(self, timeline: List[Dict]) -> float:
        """Assess cross-chain diversification"""
        return 0.5  # Placeholder

    def _assess_loss_recovery_behavior(self, timeline: List[Dict]) -> float:
        """Assess behavior after losses"""
        return 0.6  # Placeholder

    def _assess_stress_position_management(self, timeline: List[Dict]) -> float:
        """Assess position management during stress"""
        return 0.7  # Placeholder

    def _assess_greed_avoidance(self, timeline: List[Dict]) -> float:
        """Assess avoidance of greed patterns"""
        return 0.6  # Placeholder

    def _split_timeline_into_windows(self, timeline: List[Dict], window_days: int) -> List[List[Dict]]:
        """Split timeline into time windows"""
        # Placeholder implementation
        return [timeline[i:i+10] for i in range(0, len(timeline), 10)]

    def _calculate_distribution_consistency(self, distributions: List[Dict]) -> float:
        """Calculate consistency across distributions"""
        return 0.7  # Placeholder

    def _assess_strategy_consistency(self, time_windows: List[List[Dict]]) -> float:
        """Assess strategy consistency across time windows"""
        return 0.6  # Placeholder

    # Market cycle behavior assessment methods (placeholders)
    def _calculate_risk_escalation_in_bull(self, transactions: List[Dict]) -> float:
        return 0.5

    def _assess_bull_profit_taking(self, transactions: List[Dict]) -> float:
        return 0.6

    def _assess_bull_leverage_usage(self, transactions: List[Dict]) -> float:
        return 0.4

    def _assess_fomo_resistance(self, transactions: List[Dict]) -> float:
        return 0.7

    def _assess_bull_position_sizing(self, transactions: List[Dict]) -> float:
        return 0.6

    def _assess_bear_position_management(self, transactions: List[Dict]) -> float:
        return 0.7

    def _assess_panic_resistance(self, transactions: List[Dict]) -> float:
        return 0.8

    def _assess_bear_opportunity_recognition(self, transactions: List[Dict]) -> float:
        return 0.6

    def _assess_defensive_strategies(self, transactions: List[Dict]) -> float:
        return 0.7

    def _assess_bear_liquidity_management(self, transactions: List[Dict]) -> float:
        return 0.6

    def _assess_volatility_tolerance(self, transactions: List[Dict]) -> float:
        return 0.6

    def _assess_volatility_hedging(self, transactions: List[Dict]) -> float:
        return 0.5

    def _assess_volatility_opportunities(self, transactions: List[Dict]) -> float:
        return 0.6

    def _assess_stability_seeking(self, transactions: List[Dict]) -> float:
        return 0.7

    def _calculate_cycle_adaptation_score(self, bull_behavior: Dict, bear_behavior: Dict,
                                        volatility_response: Dict) -> float:
        return 0.7

    def _split_timeline_by_quarters(self, timeline: List[Dict]) -> Dict[str, List[Dict]]:
        return {"Q1": timeline[:len(timeline)//4], "Q2": timeline[len(timeline)//4:]}

    def _identify_risk_adaptation_events(self, timeline: List[Dict]) -> List[Dict]:
        return []

    def _identify_learning_indicators(self, timeline: List[Dict]) -> List[str]:
        return ["Strategy refinement", "Risk awareness improvement"]

    def _calculate_maturity_progression(self, timeline: List[Dict]) -> float:
        return 0.7

    def _extract_transaction_sequences(self, timeline: List[Dict]) -> List[List[Dict]]:
        return [timeline[i:i+5] for i in range(0, len(timeline), 5)]

    def _detect_dca_pattern(self, sequences: List[List[Dict]]) -> bool:
        return True  # Placeholder

    def _detect_yield_optimization_pattern(self, sequences: List[List[Dict]],
                                         protocol_activities: Dict) -> bool:
        return True  # Placeholder

    def _detect_arbitrage_pattern(self, sequences: List[List[Dict]]) -> bool:
        return False  # Placeholder

    def _detect_market_timing_pattern(self, sequences: List[List[Dict]]) -> bool:
        return True  # Placeholder

    def _detect_risk_management_pattern(self, sequences: List[List[Dict]]) -> bool:
        return True  # Placeholder

    def _detect_lp_optimization_pattern(self, sequences: List[List[Dict]]) -> bool:
        return False  # Placeholder

    def _detect_cross_chain_pattern(self, sequences: List[List[Dict]]) -> bool:
        return False  # Placeholder