"""
Liquidity Behavior Analysis Engine

Analyzes LP provision patterns, impermanent loss management, and liquidity strategy
sophistication for comprehensive borrower assessment.
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
class LiquidityPosition:
    """Individual liquidity position data"""
    pool_id: str
    protocol: str
    token_pair: Tuple[str, str]
    entry_date: datetime
    exit_date: Optional[datetime]
    initial_value_usd: float
    current_value_usd: float
    fees_earned_usd: float
    impermanent_loss_usd: float
    duration_days: int
    apr_realized: float
    risk_level: str

@dataclass
class ImpermanentLossMetrics:
    """Impermanent loss management metrics"""
    total_il_experienced: float
    il_mitigation_strategies: List[str]
    correlation_awareness_score: float
    hedging_effectiveness: float
    stable_pair_preference: float
    timing_optimization_score: float

@dataclass
class LiquidityStrategyMetrics:
    """Liquidity provision strategy analysis"""
    pool_selection_sophistication: float
    duration_optimization: float
    fee_tier_optimization: float
    volume_analysis_score: float
    apr_sustainability_awareness: float
    risk_adjusted_returns: float
    rebalancing_discipline: float

@dataclass
class LiquidityBehaviorAnalysis:
    """Comprehensive liquidity behavior analysis"""
    address: str
    analysis_timestamp: datetime
    total_positions: int
    active_positions: int
    total_liquidity_provided_usd: float
    average_position_duration: float
    liquidity_positions: List[LiquidityPosition]
    il_metrics: ImpermanentLossMetrics
    strategy_metrics: LiquidityStrategyMetrics
    liquidity_sophistication_score: float
    risk_management_score: float
    overall_liquidity_score: float
    confidence_level: float

class LiquidityBehaviorAnalyzer:
    """Advanced liquidity provision behavior analyzer"""

    def __init__(self, config_path: str = None):
        """Initialize the liquidity behavior analyzer"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.liquidity_behavior = self.config['liquidity_behavior']
        self.protocols = self.config['protocols']

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Pool risk classifications
        self.pool_risk_levels = {
            'stable': ['USDC-USDT', 'USDC-STBL', 'USDT-STBL'],
            'low': ['ALGO-USDC', 'ALGO-USDT', 'goBTC-USDC'],
            'medium': ['ALGO-goETH', 'ASA1-USDC', 'ASA2-ALGO'],
            'high': ['MEME-ALGO', 'NEW_TOKEN-USDC'],
            'extreme': ['MICRO_CAP-ALGO', 'EXPERIMENTAL-TOKEN']
        }

    async def analyze_liquidity_behavior(self,
                                       protocol_activities: Dict[str, Any],
                                       market_data: Dict[str, Any],
                                       analysis_period_days: int = 365) -> LiquidityBehaviorAnalysis:
        """
        Comprehensive liquidity provision behavior analysis

        Args:
            protocol_activities: Cross-protocol activity data
            market_data: Market condition and price data
            analysis_period_days: Analysis period

        Returns:
            LiquidityBehaviorAnalysis with detailed LP behavior assessment
        """
        try:
            self.logger.info("Starting liquidity behavior analysis")

            # Extract liquidity positions from protocol activities
            liquidity_positions = await self._extract_liquidity_positions(
                protocol_activities, market_data, analysis_period_days
            )

            # Analyze impermanent loss metrics
            il_metrics = self._analyze_impermanent_loss_management(
                liquidity_positions, market_data
            )

            # Analyze strategy metrics
            strategy_metrics = self._analyze_liquidity_strategy(
                liquidity_positions, protocol_activities
            )

            # Calculate sophistication scores
            sophistication_score = self._calculate_liquidity_sophistication(
                liquidity_positions, strategy_metrics, il_metrics
            )

            # Calculate risk management score
            risk_management_score = self._calculate_risk_management_score(
                liquidity_positions, il_metrics, strategy_metrics
            )

            # Calculate overall score
            overall_score, confidence = self._calculate_overall_liquidity_score(
                sophistication_score, risk_management_score, len(liquidity_positions)
            )

            # Calculate aggregate metrics
            total_positions = len(liquidity_positions)
            active_positions = len([pos for pos in liquidity_positions if pos.exit_date is None])
            total_liquidity = sum(pos.initial_value_usd for pos in liquidity_positions)
            avg_duration = np.mean([pos.duration_days for pos in liquidity_positions]) if liquidity_positions else 0

            analysis = LiquidityBehaviorAnalysis(
                address=protocol_activities.get('address', 'unknown'),
                analysis_timestamp=datetime.now(),
                total_positions=total_positions,
                active_positions=active_positions,
                total_liquidity_provided_usd=total_liquidity,
                average_position_duration=avg_duration,
                liquidity_positions=liquidity_positions,
                il_metrics=il_metrics,
                strategy_metrics=strategy_metrics,
                liquidity_sophistication_score=sophistication_score,
                risk_management_score=risk_management_score,
                overall_liquidity_score=overall_score,
                confidence_level=confidence
            )

            self.logger.info("Liquidity behavior analysis completed successfully")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in liquidity behavior analysis: {str(e)}")
            raise

    async def _extract_liquidity_positions(self,
                                         protocol_activities: Dict[str, Any],
                                         market_data: Dict[str, Any],
                                         period_days: int) -> List[LiquidityPosition]:
        """Extract and analyze individual liquidity positions"""

        positions = []

        for protocol_id, activity in protocol_activities.items():
            if not hasattr(activity, 'protocol_specific_metrics'):
                continue

            # Extract LP-related transactions
            lp_transactions = self._filter_lp_transactions(
                activity.protocol_specific_metrics.get('transactions', [])
            )

            # Group transactions into positions
            position_groups = self._group_transactions_into_positions(lp_transactions)

            # Analyze each position
            for group in position_groups:
                position = await self._analyze_liquidity_position(
                    group, protocol_id, market_data
                )
                if position:
                    positions.append(position)

        return sorted(positions, key=lambda x: x.entry_date, reverse=True)

    def _filter_lp_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Filter transactions related to liquidity provision"""
        lp_keywords = [
            'add_liquidity', 'remove_liquidity', 'lp', 'pool',
            'mint', 'burn', 'liquidity_token', 'pool_token'
        ]

        lp_transactions = []
        for tx in transactions:
            tx_type = tx.get('type', '').lower()
            note = tx.get('note', '').lower()

            if any(keyword in tx_type or keyword in note for keyword in lp_keywords):
                lp_transactions.append(tx)

        return lp_transactions

    def _group_transactions_into_positions(self, transactions: List[Dict]) -> List[List[Dict]]:
        """Group LP transactions into individual positions"""
        # Group by pool/pair and time proximity
        positions = []
        current_position = []

        for tx in sorted(transactions, key=lambda x: x.get('timestamp', datetime.now())):
            if not current_position:
                current_position = [tx]
            else:
                # Check if this transaction belongs to the same position
                last_tx = current_position[-1]
                time_diff = (tx.get('timestamp', datetime.now()) -
                           last_tx.get('timestamp', datetime.now())).days

                same_pool = (tx.get('pool_id') == last_tx.get('pool_id') or
                           tx.get('asset_pair') == last_tx.get('asset_pair'))

                if same_pool and time_diff < 7:  # Same position if within 7 days
                    current_position.append(tx)
                else:
                    # Start new position
                    if current_position:
                        positions.append(current_position)
                    current_position = [tx]

        if current_position:
            positions.append(current_position)

        return positions

    async def _analyze_liquidity_position(self,
                                        transaction_group: List[Dict],
                                        protocol: str,
                                        market_data: Dict[str, Any]) -> Optional[LiquidityPosition]:
        """Analyze a single liquidity position"""
        try:
            if not transaction_group:
                return None

            # Sort transactions by timestamp
            transactions = sorted(transaction_group,
                                key=lambda x: x.get('timestamp', datetime.now()))

            # Extract position details
            entry_tx = transactions[0]
            exit_tx = transactions[-1] if len(transactions) > 1 else None

            # Determine if position is still active
            is_active = (exit_tx is None or
                        not any(keyword in exit_tx.get('type', '').lower()
                               for keyword in ['remove', 'withdraw', 'exit']))

            # Extract pool information
            pool_id = entry_tx.get('pool_id', 'unknown')
            token_pair = self._extract_token_pair(entry_tx)
            entry_date = entry_tx.get('timestamp', datetime.now())
            exit_date = exit_tx.get('timestamp') if exit_tx and not is_active else None

            # Calculate position metrics
            initial_value = entry_tx.get('amount_usd', 0)
            current_value = await self._calculate_current_position_value(
                token_pair, initial_value, entry_date, market_data
            )

            # Calculate fees earned
            fees_earned = self._calculate_fees_earned(transaction_group, market_data)

            # Calculate impermanent loss
            il_usd = await self._calculate_impermanent_loss(
                token_pair, initial_value, entry_date, market_data
            )

            # Calculate duration
            end_date = exit_date if exit_date else datetime.now()
            duration_days = (end_date - entry_date).days

            # Calculate realized APR
            apr_realized = self._calculate_realized_apr(
                initial_value, current_value, fees_earned, duration_days
            )

            # Determine risk level
            risk_level = self._determine_pool_risk_level(token_pair)

            position = LiquidityPosition(
                pool_id=pool_id,
                protocol=protocol,
                token_pair=token_pair,
                entry_date=entry_date,
                exit_date=exit_date,
                initial_value_usd=initial_value,
                current_value_usd=current_value,
                fees_earned_usd=fees_earned,
                impermanent_loss_usd=il_usd,
                duration_days=duration_days,
                apr_realized=apr_realized,
                risk_level=risk_level
            )

            return position

        except Exception as e:
            self.logger.error(f"Error analyzing liquidity position: {str(e)}")
            return None

    def _analyze_impermanent_loss_management(self,
                                           positions: List[LiquidityPosition],
                                           market_data: Dict[str, Any]) -> ImpermanentLossMetrics:
        """Analyze impermanent loss management strategies"""

        if not positions:
            return ImpermanentLossMetrics(
                total_il_experienced=0.0,
                il_mitigation_strategies=[],
                correlation_awareness_score=0.0,
                hedging_effectiveness=0.0,
                stable_pair_preference=0.0,
                timing_optimization_score=0.0
            )

        # Calculate total IL experienced
        total_il = sum(pos.impermanent_loss_usd for pos in positions)

        # Identify IL mitigation strategies
        mitigation_strategies = self._identify_il_mitigation_strategies(positions)

        # Assess correlation awareness
        correlation_awareness = self._assess_correlation_awareness(positions)

        # Assess hedging effectiveness
        hedging_effectiveness = self._assess_hedging_effectiveness(positions, market_data)

        # Calculate stable pair preference
        stable_positions = len([pos for pos in positions if pos.risk_level == 'stable'])
        stable_pair_preference = stable_positions / len(positions) if positions else 0

        # Assess timing optimization
        timing_optimization = self._assess_il_timing_optimization(positions, market_data)

        return ImpermanentLossMetrics(
            total_il_experienced=total_il,
            il_mitigation_strategies=mitigation_strategies,
            correlation_awareness_score=correlation_awareness,
            hedging_effectiveness=hedging_effectiveness,
            stable_pair_preference=stable_pair_preference,
            timing_optimization_score=timing_optimization
        )

    def _analyze_liquidity_strategy(self,
                                  positions: List[LiquidityPosition],
                                  protocol_activities: Dict[str, Any]) -> LiquidityStrategyMetrics:
        """Analyze overall liquidity provision strategy"""

        if not positions:
            return LiquidityStrategyMetrics(
                pool_selection_sophistication=0.0,
                duration_optimization=0.0,
                fee_tier_optimization=0.0,
                volume_analysis_score=0.0,
                apr_sustainability_awareness=0.0,
                risk_adjusted_returns=0.0,
                rebalancing_discipline=0.0
            )

        # Assess pool selection sophistication
        pool_sophistication = self._assess_pool_selection_sophistication(positions)

        # Assess duration optimization
        duration_optimization = self._assess_duration_optimization(positions)

        # Assess fee tier optimization (for protocols that support it)
        fee_tier_optimization = self._assess_fee_tier_optimization(positions)

        # Assess volume analysis capabilities
        volume_analysis = self._assess_volume_analysis_score(positions)

        # Assess APR sustainability awareness
        apr_sustainability = self._assess_apr_sustainability_awareness(positions)

        # Calculate risk-adjusted returns
        risk_adjusted_returns = self._calculate_risk_adjusted_returns(positions)

        # Assess rebalancing discipline
        rebalancing_discipline = self._assess_rebalancing_discipline(
            positions, protocol_activities
        )

        return LiquidityStrategyMetrics(
            pool_selection_sophistication=pool_sophistication,
            duration_optimization=duration_optimization,
            fee_tier_optimization=fee_tier_optimization,
            volume_analysis_score=volume_analysis,
            apr_sustainability_awareness=apr_sustainability,
            risk_adjusted_returns=risk_adjusted_returns,
            rebalancing_discipline=rebalancing_discipline
        )

    def _calculate_liquidity_sophistication(self,
                                          positions: List[LiquidityPosition],
                                          strategy_metrics: LiquidityStrategyMetrics,
                                          il_metrics: ImpermanentLossMetrics) -> float:
        """Calculate overall liquidity sophistication score"""

        sophistication_components = []

        # Strategy sophistication (40%)
        strategy_score = np.mean([
            strategy_metrics.pool_selection_sophistication,
            strategy_metrics.fee_tier_optimization,
            strategy_metrics.volume_analysis_score,
            strategy_metrics.apr_sustainability_awareness
        ])
        sophistication_components.append(strategy_score * 0.4)

        # IL management sophistication (30%)
        il_management_score = np.mean([
            il_metrics.correlation_awareness_score,
            il_metrics.hedging_effectiveness,
            il_metrics.timing_optimization_score
        ])
        sophistication_components.append(il_management_score * 0.3)

        # Duration and timing optimization (20%)
        timing_score = np.mean([
            strategy_metrics.duration_optimization,
            il_metrics.timing_optimization_score
        ])
        sophistication_components.append(timing_score * 0.2)

        # Risk-adjusted performance (10%)
        performance_score = strategy_metrics.risk_adjusted_returns
        sophistication_components.append(performance_score * 0.1)

        return round(sum(sophistication_components), 3)

    def _calculate_risk_management_score(self,
                                       positions: List[LiquidityPosition],
                                       il_metrics: ImpermanentLossMetrics,
                                       strategy_metrics: LiquidityStrategyMetrics) -> float:
        """Calculate liquidity risk management score"""

        risk_management_components = []

        # Diversification across risk levels
        if positions:
            risk_distribution = {}
            for pos in positions:
                risk_distribution[pos.risk_level] = risk_distribution.get(pos.risk_level, 0) + 1

            # Calculate diversification score (lower concentration = better)
            total_positions = len(positions)
            concentration_squares = sum(
                (count / total_positions) ** 2
                for count in risk_distribution.values()
            )
            diversification_score = 1 - concentration_squares
            risk_management_components.append(diversification_score)

        # IL mitigation effectiveness
        il_mitigation_score = len(il_metrics.il_mitigation_strategies) / 5  # Max 5 strategies
        il_mitigation_score = min(il_mitigation_score, 1.0)
        risk_management_components.append(il_mitigation_score)

        # Stable pair preference (conservative approach)
        stable_preference_bonus = il_metrics.stable_pair_preference * 0.5
        risk_management_components.append(stable_preference_bonus)

        # Rebalancing discipline
        risk_management_components.append(strategy_metrics.rebalancing_discipline)

        # Position sizing discipline
        if positions:
            position_sizes = [pos.initial_value_usd for pos in positions]
            size_cv = np.std(position_sizes) / np.mean(position_sizes) if np.mean(position_sizes) > 0 else 0
            sizing_discipline = max(0, 1 - size_cv / 2)  # Lower variation = better discipline
            risk_management_components.append(sizing_discipline)

        return round(np.mean(risk_management_components), 3) if risk_management_components else 0.0

    def _calculate_overall_liquidity_score(self,
                                         sophistication_score: float,
                                         risk_management_score: float,
                                         position_count: int) -> Tuple[float, float]:
        """Calculate overall liquidity behavior score and confidence"""

        # Weighted combination
        overall_score = (sophistication_score * 0.6) + (risk_management_score * 0.4)

        # Calculate confidence based on data quantity
        confidence = min(position_count / 20, 1.0)  # 20 positions = full confidence

        # Adjust confidence based on score consistency
        score_consistency = 1 - abs(sophistication_score - risk_management_score)
        confidence *= score_consistency

        return round(overall_score, 3), round(confidence, 3)

    # Helper methods for detailed analysis

    def _extract_token_pair(self, transaction: Dict) -> Tuple[str, str]:
        """Extract token pair from transaction"""
        pair = transaction.get('asset_pair', 'UNKNOWN-UNKNOWN')
        if '-' in pair:
            return tuple(pair.split('-', 1))
        return ('UNKNOWN', 'UNKNOWN')

    async def _calculate_current_position_value(self,
                                              token_pair: Tuple[str, str],
                                              initial_value: float,
                                              entry_date: datetime,
                                              market_data: Dict[str, Any]) -> float:
        """Calculate current value of LP position"""
        # Simplified calculation - in reality would use current pool data
        return initial_value * 1.05  # Assume 5% appreciation

    def _calculate_fees_earned(self, transactions: List[Dict], market_data: Dict[str, Any]) -> float:
        """Calculate fees earned from LP position"""
        # Extract fee claims from transactions
        fee_transactions = [
            tx for tx in transactions
            if any(keyword in tx.get('type', '').lower()
                  for keyword in ['fee', 'claim', 'reward'])
        ]

        return sum(tx.get('amount_usd', 0) for tx in fee_transactions)

    async def _calculate_impermanent_loss(self,
                                        token_pair: Tuple[str, str],
                                        initial_value: float,
                                        entry_date: datetime,
                                        market_data: Dict[str, Any]) -> float:
        """Calculate impermanent loss for the position"""
        # Simplified IL calculation
        # In reality, would use actual price changes and LP math
        token1, token2 = token_pair

        if token1 in ['USDC', 'USDT', 'STBL'] and token2 in ['USDC', 'USDT', 'STBL']:
            return 0.0  # Stable pairs have minimal IL

        # Estimate IL based on risk level
        risk_level = self._determine_pool_risk_level(token_pair)
        il_estimates = {
            'stable': 0.0,
            'low': initial_value * 0.02,
            'medium': initial_value * 0.05,
            'high': initial_value * 0.10,
            'extreme': initial_value * 0.20
        }

        return il_estimates.get(risk_level, initial_value * 0.05)

    def _calculate_realized_apr(self,
                              initial_value: float,
                              current_value: float,
                              fees_earned: float,
                              duration_days: int) -> float:
        """Calculate realized APR for the position"""
        if duration_days == 0 or initial_value == 0:
            return 0.0

        total_return = (current_value + fees_earned - initial_value) / initial_value
        annualized_return = (total_return * 365) / duration_days

        return round(annualized_return * 100, 2)  # Return as percentage

    def _determine_pool_risk_level(self, token_pair: Tuple[str, str]) -> str:
        """Determine risk level of token pair"""
        pair_str = f"{token_pair[0]}-{token_pair[1]}"

        for risk_level, pairs in self.pool_risk_levels.items():
            if pair_str in pairs or f"{token_pair[1]}-{token_pair[0]}" in pairs:
                return risk_level

        # Default risk assessment based on token types
        token1, token2 = token_pair

        if both_stablecoins := (token1 in ['USDC', 'USDT', 'STBL'] and
                               token2 in ['USDC', 'USDT', 'STBL']):
            return 'stable'
        elif 'ALGO' in [token1, token2] and any(stable in [token1, token2]
                                               for stable in ['USDC', 'USDT']):
            return 'low'
        else:
            return 'medium'

    def _identify_il_mitigation_strategies(self, positions: List[LiquidityPosition]) -> List[str]:
        """Identify IL mitigation strategies used"""
        strategies = []

        # Stable pair preference
        stable_ratio = len([pos for pos in positions if pos.risk_level == 'stable']) / len(positions)
        if stable_ratio > 0.3:
            strategies.append("Stable pair preference")

        # Correlated asset pairing
        correlated_pairs = 0
        for pos in positions:
            if self._is_correlated_pair(pos.token_pair):
                correlated_pairs += 1

        if correlated_pairs / len(positions) > 0.2:
            strategies.append("Correlated asset pairing")

        # Short duration positions (to limit IL exposure)
        short_positions = len([pos for pos in positions if pos.duration_days < 30])
        if short_positions / len(positions) > 0.4:
            strategies.append("Short-term positioning")

        # Diversification across protocols
        protocols_used = set(pos.protocol for pos in positions)
        if len(protocols_used) >= 3:
            strategies.append("Protocol diversification")

        return strategies

    def _assess_correlation_awareness(self, positions: List[LiquidityPosition]) -> float:
        """Assess awareness of asset correlation in pool selection"""
        if not positions:
            return 0.0

        correlation_scores = []
        for pos in positions:
            if self._is_correlated_pair(pos.token_pair):
                correlation_scores.append(0.8)  # Good correlation awareness
            elif pos.risk_level == 'stable':
                correlation_scores.append(1.0)  # Perfect correlation (stables)
            else:
                correlation_scores.append(0.3)  # Lower correlation awareness

        return round(np.mean(correlation_scores), 3)

    def _assess_hedging_effectiveness(self,
                                    positions: List[LiquidityPosition],
                                    market_data: Dict[str, Any]) -> float:
        """Assess effectiveness of hedging strategies"""
        # Simplified assessment - would require more complex analysis in reality
        total_il = sum(pos.impermanent_loss_usd for pos in positions)
        total_value = sum(pos.initial_value_usd for pos in positions)

        if total_value == 0:
            return 0.0

        il_ratio = total_il / total_value
        hedging_effectiveness = max(0, 1 - il_ratio / 0.1)  # 10% IL = 0 effectiveness

        return round(hedging_effectiveness, 3)

    def _assess_il_timing_optimization(self,
                                     positions: List[LiquidityPosition],
                                     market_data: Dict[str, Any]) -> float:
        """Assess timing optimization to minimize IL"""
        # Analyze if positions were entered during favorable conditions
        timing_scores = []

        for pos in positions:
            # Would analyze market volatility at entry time
            # For now, use simplified heuristic
            if pos.duration_days < 30:  # Short-term positions reduce IL risk
                timing_scores.append(0.7)
            elif pos.risk_level in ['stable', 'low']:
                timing_scores.append(0.8)
            else:
                timing_scores.append(0.4)

        return round(np.mean(timing_scores), 3) if timing_scores else 0.0

    def _assess_pool_selection_sophistication(self, positions: List[LiquidityPosition]) -> float:
        """Assess sophistication in pool selection"""
        sophistication_indicators = []

        if not positions:
            return 0.0

        # Risk-adjusted selection
        risk_distribution = {}
        for pos in positions:
            risk_distribution[pos.risk_level] = risk_distribution.get(pos.risk_level, 0) + 1

        # Prefer balanced risk distribution
        balanced_distribution = 1 - abs(0.5 - risk_distribution.get('low', 0) / len(positions))
        sophistication_indicators.append(balanced_distribution)

        # Protocol diversification
        protocols = set(pos.protocol for pos in positions)
        protocol_diversity = min(len(protocols) / 4, 1.0)  # 4 protocols = max
        sophistication_indicators.append(protocol_diversity)

        # Performance consistency
        if positions:
            aprs = [pos.apr_realized for pos in positions if pos.apr_realized > 0]
            if aprs:
                apr_consistency = 1 - (np.std(aprs) / np.mean(aprs)) if np.mean(aprs) > 0 else 0
                sophistication_indicators.append(max(apr_consistency, 0))

        return round(np.mean(sophistication_indicators), 3)

    def _assess_duration_optimization(self, positions: List[LiquidityPosition]) -> float:
        """Assess optimization of position duration"""
        if not positions:
            return 0.0

        duration_scores = []

        for pos in positions:
            # Optimal duration depends on risk level
            optimal_durations = {
                'stable': 90,    # Longer for stable pairs
                'low': 60,       # Medium for low risk
                'medium': 30,    # Shorter for medium risk
                'high': 14,      # Very short for high risk
                'extreme': 7     # Extremely short for extreme risk
            }

            optimal = optimal_durations.get(pos.risk_level, 30)
            duration_score = 1 - abs(pos.duration_days - optimal) / optimal
            duration_scores.append(max(duration_score, 0))

        return round(np.mean(duration_scores), 3)

    def _assess_fee_tier_optimization(self, positions: List[LiquidityPosition]) -> float:
        """Assess fee tier optimization (for applicable protocols)"""
        # Simplified assessment - would require protocol-specific analysis
        return 0.6  # Placeholder

    def _assess_volume_analysis_score(self, positions: List[LiquidityPosition]) -> float:
        """Assess volume analysis capabilities in pool selection"""
        # Would analyze if user selected high-volume pools
        return 0.7  # Placeholder

    def _assess_apr_sustainability_awareness(self, positions: List[LiquidityPosition]) -> float:
        """Assess awareness of APR sustainability"""
        if not positions:
            return 0.0

        # Check if user avoided obviously unsustainable APRs
        sustainable_positions = 0
        for pos in positions:
            if pos.apr_realized < 100:  # APRs below 100% considered sustainable
                sustainable_positions += 1

        return sustainable_positions / len(positions)

    def _calculate_risk_adjusted_returns(self, positions: List[LiquidityPosition]) -> float:
        """Calculate risk-adjusted returns across positions"""
        if not positions:
            return 0.0

        risk_weights = {'stable': 1.0, 'low': 0.8, 'medium': 0.6, 'high': 0.4, 'extreme': 0.2}

        weighted_returns = []
        for pos in positions:
            if pos.apr_realized > 0:
                risk_weight = risk_weights.get(pos.risk_level, 0.5)
                risk_adjusted_apr = pos.apr_realized * risk_weight
                weighted_returns.append(risk_adjusted_apr)

        return round(np.mean(weighted_returns), 2) if weighted_returns else 0.0

    def _assess_rebalancing_discipline(self,
                                     positions: List[LiquidityPosition],
                                     protocol_activities: Dict[str, Any]) -> float:
        """Assess rebalancing discipline"""
        # Count rebalancing events
        rebalancing_events = 0
        total_positions = len(positions)

        for pos in positions:
            # Check if position was actively managed
            if pos.duration_days > 30 and pos.exit_date is not None:
                rebalancing_events += 1

        rebalancing_ratio = rebalancing_events / total_positions if total_positions > 0 else 0
        return min(rebalancing_ratio * 2, 1.0)  # Normalize to [0, 1]

    def _is_correlated_pair(self, token_pair: Tuple[str, str]) -> bool:
        """Check if token pair consists of correlated assets"""
        token1, token2 = token_pair

        # Stablecoin pairs
        stablecoins = ['USDC', 'USDT', 'STBL']
        if token1 in stablecoins and token2 in stablecoins:
            return True

        # Governance tokens of same protocol
        governance_pairs = [
            ('ALGO', 'gALGO'),
            # Add other correlated pairs
        ]

        pair_check = (token1, token2) in governance_pairs or (token2, token1) in governance_pairs
        return pair_check