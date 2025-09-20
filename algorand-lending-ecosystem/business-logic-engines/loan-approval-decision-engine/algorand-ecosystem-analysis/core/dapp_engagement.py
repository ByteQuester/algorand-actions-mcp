"""
DApp Engagement Analyzer

Analyzes smart contract interactions, dApp usage patterns, and DeFi
behavior to assess financial sophistication and protocol engagement.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class ProtocolEngagement:
    """Protocol engagement metrics"""
    protocol_name: str
    interaction_count: int
    total_volume: float
    first_interaction: datetime
    last_interaction: datetime
    sophistication_score: float
    risk_indicators: List[str]


@dataclass
class DeFiStrategy:
    """Detected DeFi strategy"""
    strategy_type: str
    confidence: float
    evidence: List[str]
    risk_level: str
    sophistication_indicator: bool


class DAppEngagementAnalyzer:
    """
    Analyzes dApp engagement patterns, DeFi strategies, and protocol
    sophistication to assess borrower's financial behavior.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dapp_config = config.get('dapp_engagement', {})
        self.known_protocols = self._load_known_protocols()

    async def analyze_defi_engagement(self, wallet_address: str) -> Dict[str, Any]:
        """
        Analyze comprehensive DeFi engagement patterns.

        Args:
            wallet_address: Algorand wallet address to analyze

        Returns:
            Dictionary containing DeFi engagement analysis
        """
        logger.info(f"Analyzing DeFi engagement for {wallet_address}")

        try:
            # Parallel data collection
            tasks = [
                self._fetch_smart_contract_interactions(wallet_address),
                self._fetch_dex_transactions(wallet_address),
                self._fetch_lending_activities(wallet_address),
                self._fetch_staking_activities(wallet_address),
                self._fetch_yield_farming_activities(wallet_address)
            ]

            contract_interactions, dex_txs, lending_activities, staking_activities, yield_farming = await asyncio.gather(*tasks)

            # Analyze protocol engagement
            protocol_engagement = await self._analyze_protocol_engagement(
                contract_interactions, dex_txs, lending_activities, staking_activities
            )

            # Detect DeFi strategies
            detected_strategies = await self._detect_defi_strategies(
                dex_txs, lending_activities, staking_activities, yield_farming
            )

            # Calculate sophistication metrics
            sophistication_metrics = self._calculate_sophistication_metrics(
                protocol_engagement, detected_strategies
            )

            # Analyze risk patterns
            risk_analysis = self._analyze_defi_risk_patterns(
                contract_interactions, detected_strategies
            )

            # Calculate overall scores
            engagement_scores = self._calculate_engagement_scores(
                protocol_engagement, sophistication_metrics, risk_analysis
            )

            return {
                'protocol_engagement': protocol_engagement,
                'detected_strategies': detected_strategies,
                'sophistication_metrics': sophistication_metrics,
                'risk_analysis': risk_analysis,
                'engagement_scores': engagement_scores,
                'protocols_used': [p.protocol_name for p in protocol_engagement],
                'contract_interactions': sum(p.interaction_count for p in protocol_engagement),
                'dex_volume': sum(tx.get('amount', 0) for tx in dex_txs),
                'yield_farming': len(yield_farming) > 0,
                'liquidity_provision': any(s.strategy_type == 'liquidity_provision' for s in detected_strategies),
                'advanced_strategies': any(s.sophistication_indicator for s in detected_strategies),
                'defi_sophistication_score': sophistication_metrics.get('overall_sophistication', 0.0),
                'high_risk_count': len(risk_analysis.get('high_risk_interactions', [])),
                'suspicious_flags': risk_analysis.get('suspicious_flags', []),
                'blacklisted_count': risk_analysis.get('blacklisted_interactions', 0)
            }

        except Exception as e:
            logger.error(f"DeFi engagement analysis failed for {wallet_address}: {e}")
            raise

    async def analyze_protocol_sophistication(
        self,
        wallet_address: str,
        protocol_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze sophistication in specific protocol usage.

        Args:
            wallet_address: Algorand wallet address to analyze
            protocol_filter: Optional list of protocols to focus on

        Returns:
            Protocol-specific sophistication analysis
        """
        logger.info(f"Analyzing protocol sophistication for {wallet_address}")

        try:
            # Get all interactions
            interactions = await self._fetch_smart_contract_interactions(wallet_address)

            if protocol_filter:
                interactions = [i for i in interactions if i.get('protocol') in protocol_filter]

            # Analyze by protocol
            protocol_analysis = {}
            for protocol in set(i.get('protocol') for i in interactions if i.get('protocol')):
                protocol_interactions = [i for i in interactions if i.get('protocol') == protocol]
                protocol_analysis[protocol] = await self._analyze_single_protocol(
                    protocol, protocol_interactions
                )

            return {
                'protocol_analysis': protocol_analysis,
                'overall_sophistication': self._calculate_overall_sophistication(protocol_analysis),
                'protocol_diversity': len(protocol_analysis),
                'advanced_features_used': self._count_advanced_features(protocol_analysis)
            }

        except Exception as e:
            logger.error(f"Protocol sophistication analysis failed: {e}")
            raise

    async def _fetch_smart_contract_interactions(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch smart contract interactions"""
        # Mock implementation - would integrate with Algorand indexer
        return [
            {
                'timestamp': datetime.utcnow() - timedelta(days=5),
                'app_id': 350338509,  # Tinyman
                'protocol': 'tinyman',
                'function': 'swap',
                'amount': 1000.0,
                'gas_used': 0.001
            },
            {
                'timestamp': datetime.utcnow() - timedelta(days=10),
                'app_id': 465814065,  # Algofi
                'protocol': 'algofi',
                'function': 'supply',
                'amount': 5000.0,
                'gas_used': 0.002
            },
            {
                'timestamp': datetime.utcnow() - timedelta(days=15),
                'app_id': 552635992,  # Folks Finance
                'protocol': 'folks_finance',
                'function': 'borrow',
                'amount': 2000.0,
                'gas_used': 0.003
            }
        ]

    async def _fetch_dex_transactions(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch DEX trading transactions"""
        # Mock implementation
        return [
            {
                'timestamp': datetime.utcnow() - timedelta(days=2),
                'protocol': 'tinyman',
                'type': 'swap',
                'input_asset': 0,  # ALGO
                'output_asset': 31566704,  # USDC
                'input_amount': 400.0,
                'output_amount': 100.0,
                'slippage': 0.005
            },
            {
                'timestamp': datetime.utcnow() - timedelta(days=7),
                'protocol': 'pact',
                'type': 'swap',
                'input_asset': 31566704,  # USDC
                'output_asset': 386192725,  # goBTC
                'input_amount': 1500.0,
                'output_amount': 0.035,
                'slippage': 0.003
            }
        ]

    async def _fetch_lending_activities(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch lending platform activities"""
        # Mock implementation
        return [
            {
                'timestamp': datetime.utcnow() - timedelta(days=30),
                'protocol': 'algofi',
                'action': 'supply',
                'asset': 31566704,  # USDC
                'amount': 5000.0,
                'apy': 0.045
            },
            {
                'timestamp': datetime.utcnow() - timedelta(days=35),
                'protocol': 'folks_finance',
                'action': 'borrow',
                'asset': 0,  # ALGO
                'amount': 2000.0,
                'apy': 0.065
            }
        ]

    async def _fetch_staking_activities(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch staking activities"""
        # Mock implementation
        return [
            {
                'timestamp': datetime.utcnow() - timedelta(days=60),
                'type': 'governance_stake',
                'amount': 10000.0,
                'duration_days': 90,
                'rewards_earned': 150.0
            }
        ]

    async def _fetch_yield_farming_activities(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch yield farming activities"""
        # Mock implementation
        return [
            {
                'timestamp': datetime.utcnow() - timedelta(days=45),
                'protocol': 'tinyman',
                'pool': 'ALGO-USDC',
                'action': 'add_liquidity',
                'algo_amount': 1000.0,
                'usdc_amount': 250.0,
                'lp_tokens': 500.0
            }
        ]

    async def _analyze_protocol_engagement(
        self,
        contract_interactions: List[Dict[str, Any]],
        dex_txs: List[Dict[str, Any]],
        lending_activities: List[Dict[str, Any]],
        staking_activities: List[Dict[str, Any]]
    ) -> List[ProtocolEngagement]:
        """Analyze engagement with each protocol"""

        protocol_data = defaultdict(list)

        # Aggregate all interactions by protocol
        for interaction in contract_interactions:
            protocol = interaction.get('protocol')
            if protocol:
                protocol_data[protocol].append(interaction)

        for tx in dex_txs:
            protocol = tx.get('protocol')
            if protocol:
                protocol_data[protocol].append(tx)

        for activity in lending_activities:
            protocol = activity.get('protocol')
            if protocol:
                protocol_data[protocol].append(activity)

        # Analyze each protocol
        engagements = []
        for protocol, activities in protocol_data.items():
            engagement = await self._analyze_single_protocol_engagement(protocol, activities)
            engagements.append(engagement)

        return engagements

    async def _analyze_single_protocol_engagement(
        self,
        protocol: str,
        activities: List[Dict[str, Any]]
    ) -> ProtocolEngagement:
        """Analyze engagement with a single protocol"""

        if not activities:
            return ProtocolEngagement(protocol, 0, 0.0, datetime.utcnow(), datetime.utcnow(), 0.0, [])

        interaction_count = len(activities)
        total_volume = sum(a.get('amount', 0) for a in activities)

        timestamps = [a['timestamp'] for a in activities if 'timestamp' in a]
        first_interaction = min(timestamps) if timestamps else datetime.utcnow()
        last_interaction = max(timestamps) if timestamps else datetime.utcnow()

        # Calculate sophistication score
        sophistication_score = self._calculate_protocol_sophistication(protocol, activities)

        # Detect risk indicators
        risk_indicators = self._detect_protocol_risk_indicators(protocol, activities)

        return ProtocolEngagement(
            protocol_name=protocol,
            interaction_count=interaction_count,
            total_volume=total_volume,
            first_interaction=first_interaction,
            last_interaction=last_interaction,
            sophistication_score=sophistication_score,
            risk_indicators=risk_indicators
        )

    async def _detect_defi_strategies(
        self,
        dex_txs: List[Dict[str, Any]],
        lending_activities: List[Dict[str, Any]],
        staking_activities: List[Dict[str, Any]],
        yield_farming: List[Dict[str, Any]]
    ) -> List[DeFiStrategy]:
        """Detect DeFi strategies from transaction patterns"""

        strategies = []

        # Arbitrage detection
        arbitrage = await self._detect_arbitrage_strategy(dex_txs)
        if arbitrage:
            strategies.append(arbitrage)

        # Yield farming detection
        yield_strategy = await self._detect_yield_farming_strategy(yield_farming, staking_activities)
        if yield_strategy:
            strategies.append(yield_strategy)

        # Leverage trading detection
        leverage = await self._detect_leverage_strategy(lending_activities, dex_txs)
        if leverage:
            strategies.append(leverage)

        # Dollar cost averaging detection
        dca = await self._detect_dca_strategy(dex_txs)
        if dca:
            strategies.append(dca)

        # Liquidity provision strategy
        lp_strategy = await self._detect_liquidity_provision_strategy(yield_farming)
        if lp_strategy:
            strategies.append(lp_strategy)

        return strategies

    async def _detect_arbitrage_strategy(self, dex_txs: List[Dict[str, Any]]) -> Optional[DeFiStrategy]:
        """Detect arbitrage trading patterns"""
        if len(dex_txs) < 2:
            return None

        # Look for quick buy/sell patterns
        arbitrage_count = 0
        for i in range(len(dex_txs) - 1):
            current_tx = dex_txs[i]
            next_tx = dex_txs[i + 1]

            time_diff = (next_tx['timestamp'] - current_tx['timestamp']).total_seconds()
            if time_diff < 300:  # Within 5 minutes
                arbitrage_count += 1

        if arbitrage_count > 3:
            return DeFiStrategy(
                strategy_type="arbitrage",
                confidence=min(arbitrage_count / 10, 1.0),
                evidence=[f"{arbitrage_count} potential arbitrage sequences detected"],
                risk_level="medium",
                sophistication_indicator=True
            )

        return None

    async def _detect_yield_farming_strategy(
        self,
        yield_farming: List[Dict[str, Any]],
        staking_activities: List[Dict[str, Any]]
    ) -> Optional[DeFiStrategy]:
        """Detect yield farming strategy"""
        total_yield_activities = len(yield_farming) + len(staking_activities)

        if total_yield_activities >= 3:
            return DeFiStrategy(
                strategy_type="yield_farming",
                confidence=min(total_yield_activities / 10, 1.0),
                evidence=[f"{total_yield_activities} yield-generating activities"],
                risk_level="low",
                sophistication_indicator=True
            )

        return None

    async def _detect_leverage_strategy(
        self,
        lending_activities: List[Dict[str, Any]],
        dex_txs: List[Dict[str, Any]]
    ) -> Optional[DeFiStrategy]:
        """Detect leverage trading strategy"""
        borrows = [a for a in lending_activities if a.get('action') == 'borrow']
        supplies = [a for a in lending_activities if a.get('action') == 'supply']

        if len(borrows) > 0 and len(dex_txs) > len(borrows):
            return DeFiStrategy(
                strategy_type="leverage_trading",
                confidence=0.7,
                evidence=[f"{len(borrows)} borrows with {len(dex_txs)} trades"],
                risk_level="high",
                sophistication_indicator=True
            )

        return None

    async def _detect_dca_strategy(self, dex_txs: List[Dict[str, Any]]) -> Optional[DeFiStrategy]:
        """Detect dollar cost averaging strategy"""
        if len(dex_txs) < 5:
            return None

        # Check for regular, similar-sized purchases
        buy_txs = [tx for tx in dex_txs if tx.get('type') == 'swap']
        if len(buy_txs) < 5:
            return None

        amounts = [tx.get('input_amount', 0) for tx in buy_txs]
        if not amounts:
            return None

        # Check amount consistency
        avg_amount = sum(amounts) / len(amounts)
        amount_variance = sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)
        cv = (amount_variance ** 0.5) / avg_amount if avg_amount > 0 else 1

        if cv < 0.3:  # Low variance indicates DCA
            return DeFiStrategy(
                strategy_type="dollar_cost_averaging",
                confidence=1.0 - cv,
                evidence=[f"Consistent amounts with CV {cv:.2f}"],
                risk_level="low",
                sophistication_indicator=False
            )

        return None

    async def _detect_liquidity_provision_strategy(
        self,
        yield_farming: List[Dict[str, Any]]
    ) -> Optional[DeFiStrategy]:
        """Detect liquidity provision strategy"""
        lp_activities = [y for y in yield_farming if y.get('action') == 'add_liquidity']

        if len(lp_activities) >= 2:
            return DeFiStrategy(
                strategy_type="liquidity_provision",
                confidence=min(len(lp_activities) / 5, 1.0),
                evidence=[f"{len(lp_activities)} liquidity provision events"],
                risk_level="medium",
                sophistication_indicator=True
            )

        return None

    def _calculate_sophistication_metrics(
        self,
        protocol_engagement: List[ProtocolEngagement],
        detected_strategies: List[DeFiStrategy]
    ) -> Dict[str, float]:
        """Calculate sophistication metrics"""

        # Protocol diversity
        protocol_count = len(protocol_engagement)
        protocol_diversity_score = min(protocol_count / 5, 1.0)  # Normalize to 5 protocols

        # Strategy sophistication
        sophisticated_strategies = [s for s in detected_strategies if s.sophistication_indicator]
        strategy_sophistication = len(sophisticated_strategies) / max(len(detected_strategies), 1)

        # Interaction depth
        total_interactions = sum(p.interaction_count for p in protocol_engagement)
        interaction_depth_score = min(total_interactions / 50, 1.0)  # Normalize to 50 interactions

        # Volume sophistication
        total_volume = sum(p.total_volume for p in protocol_engagement)
        volume_sophistication = min(total_volume / 100000, 1.0)  # Normalize to 100K

        # Advanced features usage
        advanced_protocols = ['algofi', 'folks_finance']  # More sophisticated protocols
        advanced_usage = sum(1 for p in protocol_engagement if p.protocol_name in advanced_protocols)
        advanced_feature_score = min(advanced_usage / 2, 1.0)

        # Overall sophistication
        overall_sophistication = (
            protocol_diversity_score * 0.25 +
            strategy_sophistication * 0.25 +
            interaction_depth_score * 0.20 +
            volume_sophistication * 0.15 +
            advanced_feature_score * 0.15
        )

        return {
            'protocol_diversity_score': protocol_diversity_score,
            'strategy_sophistication': strategy_sophistication,
            'interaction_depth_score': interaction_depth_score,
            'volume_sophistication': volume_sophistication,
            'advanced_feature_score': advanced_feature_score,
            'overall_sophistication': overall_sophistication
        }

    def _analyze_defi_risk_patterns(
        self,
        contract_interactions: List[Dict[str, Any]],
        detected_strategies: List[DeFiStrategy]
    ) -> Dict[str, Any]:
        """Analyze DeFi-related risk patterns"""

        risk_analysis = {
            'high_risk_interactions': [],
            'suspicious_flags': [],
            'blacklisted_interactions': 0,
            'risk_score': 0.0
        }

        # Check for high-risk protocols
        high_risk_protocols = ['unknown_protocol', 'new_protocol']  # Would be configurable
        high_risk_interactions = [
            i for i in contract_interactions
            if i.get('protocol') in high_risk_protocols
        ]
        risk_analysis['high_risk_interactions'] = high_risk_interactions

        # Check for high-risk strategies
        high_risk_strategies = [s for s in detected_strategies if s.risk_level == 'high']
        if high_risk_strategies:
            risk_analysis['suspicious_flags'].append('high_risk_strategies_detected')

        # Flash loan usage (high sophistication but potential risk)
        flash_loan_count = sum(1 for i in contract_interactions if 'flash' in str(i).lower())
        if flash_loan_count > 0:
            risk_analysis['suspicious_flags'].append('flash_loan_usage')

        # Calculate overall risk score
        base_risk = 20.0  # Base DeFi risk
        base_risk += len(high_risk_interactions) * 10
        base_risk += len(high_risk_strategies) * 15
        base_risk += flash_loan_count * 5

        risk_analysis['risk_score'] = min(base_risk, 100.0)

        return risk_analysis

    def _calculate_engagement_scores(
        self,
        protocol_engagement: List[ProtocolEngagement],
        sophistication_metrics: Dict[str, float],
        risk_analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate overall engagement scores"""

        # Engagement breadth (number of protocols)
        breadth_score = min(len(protocol_engagement) / 5 * 100, 100)

        # Engagement depth (total interactions)
        total_interactions = sum(p.interaction_count for p in protocol_engagement)
        depth_score = min(total_interactions / 50 * 100, 100)

        # Quality score (sophistication)
        quality_score = sophistication_metrics.get('overall_sophistication', 0) * 100

        # Risk-adjusted score
        risk_penalty = risk_analysis.get('risk_score', 0) * 0.5
        risk_adjusted_score = max((breadth_score + depth_score + quality_score) / 3 - risk_penalty, 0)

        return {
            'breadth_score': breadth_score,
            'depth_score': depth_score,
            'quality_score': quality_score,
            'risk_adjusted_score': risk_adjusted_score,
            'overall_engagement_score': (breadth_score + depth_score + quality_score) / 3
        }

    def _calculate_protocol_sophistication(
        self,
        protocol: str,
        activities: List[Dict[str, Any]]
    ) -> float:
        """Calculate sophistication score for a specific protocol"""

        base_score = 0.5  # Base sophistication

        # Protocol complexity bonus
        complex_protocols = {
            'algofi': 0.8,
            'folks_finance': 0.8,
            'tinyman': 0.6,
            'pact': 0.6
        }
        base_score += complex_protocols.get(protocol, 0.3)

        # Activity diversity bonus
        function_types = set(a.get('function', a.get('action', '')) for a in activities)
        diversity_bonus = min(len(function_types) / 5, 0.3)
        base_score += diversity_bonus

        # Volume bonus
        total_volume = sum(a.get('amount', 0) for a in activities)
        volume_bonus = min(total_volume / 10000, 0.2)
        base_score += volume_bonus

        return min(base_score, 1.0)

    def _detect_protocol_risk_indicators(
        self,
        protocol: str,
        activities: List[Dict[str, Any]]
    ) -> List[str]:
        """Detect risk indicators for protocol usage"""

        risk_indicators = []

        # High frequency (potential bot activity)
        if len(activities) > 50:
            risk_indicators.append('high_frequency_usage')

        # Large volumes (potential market manipulation)
        total_volume = sum(a.get('amount', 0) for a in activities)
        if total_volume > 100000:
            risk_indicators.append('high_volume_activity')

        # Unknown protocol
        known_protocols = ['tinyman', 'algofi', 'folks_finance', 'pact']
        if protocol not in known_protocols:
            risk_indicators.append('unknown_protocol')

        return risk_indicators

    async def _analyze_single_protocol(
        self,
        protocol: str,
        interactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze sophistication for a single protocol"""

        if not interactions:
            return {'sophistication_score': 0.0, 'features_used': []}

        # Function diversity
        functions_used = set(i.get('function', i.get('action', '')) for i in interactions)

        # Advanced features
        advanced_features = {
            'algofi': ['borrow', 'leverage', 'farm'],
            'folks_finance': ['borrow', 'stake', 'governance'],
            'tinyman': ['add_liquidity', 'remove_liquidity'],
            'pact': ['limit_order', 'stop_loss']
        }

        protocol_advanced = set(advanced_features.get(protocol, []))
        advanced_used = functions_used.intersection(protocol_advanced)

        sophistication_score = len(advanced_used) / max(len(protocol_advanced), 1) if protocol_advanced else 0

        return {
            'sophistication_score': sophistication_score,
            'functions_used': list(functions_used),
            'advanced_features_used': list(advanced_used),
            'interaction_count': len(interactions)
        }

    def _calculate_overall_sophistication(self, protocol_analysis: Dict[str, Dict]) -> float:
        """Calculate overall sophistication across all protocols"""
        if not protocol_analysis:
            return 0.0

        sophistication_scores = [p.get('sophistication_score', 0) for p in protocol_analysis.values()]
        return sum(sophistication_scores) / len(sophistication_scores)

    def _count_advanced_features(self, protocol_analysis: Dict[str, Dict]) -> int:
        """Count total advanced features used across all protocols"""
        total_advanced = 0
        for analysis in protocol_analysis.values():
            total_advanced += len(analysis.get('advanced_features_used', []))
        return total_advanced

    def _load_known_protocols(self) -> Dict[str, Dict[str, Any]]:
        """Load known protocol information"""
        return {
            'tinyman': {
                'category': 'dex',
                'risk_level': 'low',
                'sophistication_tier': 'intermediate'
            },
            'algofi': {
                'category': 'lending',
                'risk_level': 'low',
                'sophistication_tier': 'advanced'
            },
            'folks_finance': {
                'category': 'lending',
                'risk_level': 'medium',
                'sophistication_tier': 'advanced'
            },
            'pact': {
                'category': 'dex',
                'risk_level': 'medium',
                'sophistication_tier': 'advanced'
            }
        }