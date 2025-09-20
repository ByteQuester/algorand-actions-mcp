"""
Ecosystem Commitment Analyzer

Analyzes long-term holding patterns, protocol engagement, investment patterns,
and market cycle loyalty for comprehensive ecosystem commitment assessment.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class AssetType(Enum):
    ALGO = "algo"
    ASA = "asa"
    NFT = "nft"
    LP_TOKEN = "lp_token"
    PROTOCOL_TOKEN = "protocol_token"


class MarketCondition(Enum):
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"


@dataclass
class HoldingRecord:
    """Individual asset holding record"""
    asset_id: str
    asset_type: AssetType
    asset_name: str
    amount: float
    value_usd: float
    first_acquired: datetime
    last_transaction: datetime
    holding_duration_days: int
    transaction_count: int
    net_flow: float  # Positive = accumulation, Negative = distribution
    average_cost_basis: float
    current_roi: float


@dataclass
class ProtocolEngagement:
    """Protocol-specific engagement metrics"""
    protocol_name: str
    first_interaction: datetime
    total_transactions: int
    total_volume_usd: float
    unique_features_used: List[str]
    governance_participation: bool
    liquidity_provided: float
    staking_amount: float
    engagement_consistency: float
    loyalty_score: float


@dataclass
class EcosystemCommitmentProfile:
    """Comprehensive ecosystem commitment analysis"""
    address: str
    overall_commitment_score: float
    holding_patterns_score: float
    protocol_engagement_score: float
    investment_patterns_score: float
    loyalty_metrics_score: float
    total_portfolio_value: float
    algo_holding_percentage: float
    portfolio_diversification: float
    average_holding_duration: float
    market_cycle_consistency: float
    protocol_relationships: List[ProtocolEngagement]
    commitment_indicators: List[str]
    risk_factors: List[str]
    recommendations: List[str]
    analysis_period: Tuple[datetime, datetime]


class EcosystemCommitmentAnalyzer:
    """Analyzes ecosystem commitment for governance reputation"""

    def __init__(self, config_path: str = None):
        """Initialize ecosystem commitment analyzer"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.commitment_config = self.config['ecosystem_commitment']
        self.data_sources = self.config['data_sources']

    async def analyze_ecosystem_commitment(self, address: str,
                                         start_date: Optional[datetime] = None,
                                         end_date: Optional[datetime] = None) -> EcosystemCommitmentProfile:
        """
        Analyze comprehensive ecosystem commitment for an address

        Args:
            address: Algorand address to analyze
            start_date: Analysis start date (default: 2 years ago)
            end_date: Analysis end date (default: now)

        Returns:
            EcosystemCommitmentProfile with detailed commitment analysis
        """
        try:
            if end_date is None:
                end_date = datetime.utcnow()
            if start_date is None:
                start_date = end_date - timedelta(days=730)  # 2 years

            logger.info(f"Analyzing ecosystem commitment for {address} from {start_date} to {end_date}")

            # Gather commitment data from multiple sources
            holding_records = await self._fetch_holding_records(address, start_date, end_date)
            protocol_engagements = await self._fetch_protocol_engagements(address, start_date, end_date)
            market_data = await self._fetch_market_data(start_date, end_date)
            defi_activities = await self._fetch_defi_activities(address, start_date, end_date)

            # Calculate commitment scores
            holding_patterns_score = self._calculate_holding_patterns_score(holding_records, market_data)
            protocol_engagement_score = self._calculate_protocol_engagement_score(protocol_engagements)
            investment_patterns_score = self._calculate_investment_patterns_score(holding_records)
            loyalty_metrics_score = self._calculate_loyalty_metrics_score(holding_records, protocol_engagements, market_data)

            # Calculate overall commitment score
            overall_score = self._calculate_overall_commitment_score(
                holding_patterns_score, protocol_engagement_score,
                investment_patterns_score, loyalty_metrics_score
            )

            # Calculate aggregate metrics
            total_portfolio_value = sum(h.value_usd for h in holding_records)
            algo_holdings = [h for h in holding_records if h.asset_type == AssetType.ALGO]
            algo_value = sum(h.value_usd for h in algo_holdings)
            algo_percentage = (algo_value / total_portfolio_value) if total_portfolio_value > 0 else 0

            portfolio_diversification = self._calculate_portfolio_diversification(holding_records)
            avg_holding_duration = self._calculate_average_holding_duration(holding_records)
            market_cycle_consistency = self._calculate_market_cycle_consistency(holding_records, market_data)

            # Analyze patterns and indicators
            commitment_indicators = self._identify_commitment_indicators(holding_records, protocol_engagements)
            risk_factors = self._identify_commitment_risks(holding_records, protocol_engagements)
            recommendations = self._generate_commitment_recommendations(
                holding_patterns_score, protocol_engagement_score,
                investment_patterns_score, loyalty_metrics_score
            )

            return EcosystemCommitmentProfile(
                address=address,
                overall_commitment_score=overall_score,
                holding_patterns_score=holding_patterns_score,
                protocol_engagement_score=protocol_engagement_score,
                investment_patterns_score=investment_patterns_score,
                loyalty_metrics_score=loyalty_metrics_score,
                total_portfolio_value=total_portfolio_value,
                algo_holding_percentage=algo_percentage,
                portfolio_diversification=portfolio_diversification,
                average_holding_duration=avg_holding_duration,
                market_cycle_consistency=market_cycle_consistency,
                protocol_relationships=protocol_engagements,
                commitment_indicators=commitment_indicators,
                risk_factors=risk_factors,
                recommendations=recommendations,
                analysis_period=(start_date, end_date)
            )

        except Exception as e:
            logger.error(f"Error analyzing ecosystem commitment for {address}: {e}")
            raise

    async def _fetch_holding_records(self, address: str, start_date: datetime,
                                   end_date: datetime) -> List[HoldingRecord]:
        """Fetch asset holding records for the address"""
        try:
            # Simulate holding records data
            holding_records = [
                HoldingRecord(
                    asset_id="0",  # ALGO
                    asset_type=AssetType.ALGO,
                    asset_name="Algorand",
                    amount=125000.0,
                    value_usd=87500.0,
                    first_acquired=datetime(2021, 3, 15),
                    last_transaction=datetime(2022, 5, 20),
                    holding_duration_days=430,
                    transaction_count=45,
                    net_flow=75000.0,  # Net accumulation
                    average_cost_basis=0.65,
                    current_roi=0.08
                ),
                HoldingRecord(
                    asset_id="31566704",  # USDC
                    asset_type=AssetType.ASA,
                    asset_name="USD Coin",
                    amount=15000.0,
                    value_usd=15000.0,
                    first_acquired=datetime(2021, 8, 10),
                    last_transaction=datetime(2022, 5, 25),
                    holding_duration_days=288,
                    transaction_count=67,
                    net_flow=5000.0,
                    average_cost_basis=1.0,
                    current_roi=0.0
                ),
                HoldingRecord(
                    asset_id="467020179",  # TinyMan LP Token
                    asset_type=AssetType.LP_TOKEN,
                    asset_name="ALGO/USDC LP",
                    amount=5000.0,
                    value_usd=12500.0,
                    first_acquired=datetime(2021, 10, 5),
                    last_transaction=datetime(2022, 4, 15),
                    holding_duration_days=192,
                    transaction_count=23,
                    net_flow=3000.0,
                    average_cost_basis=2.3,
                    current_roi=0.15
                ),
                HoldingRecord(
                    asset_id="386192725",  # Folks Finance Token
                    asset_type=AssetType.PROTOCOL_TOKEN,
                    asset_name="Folks Token",
                    amount=25000.0,
                    value_usd=7500.0,
                    first_acquired=datetime(2022, 1, 20),
                    last_transaction=datetime(2022, 5, 10),
                    holding_duration_days=110,
                    transaction_count=12,
                    net_flow=15000.0,
                    average_cost_basis=0.28,
                    current_roi=0.07
                )
            ]

            return holding_records

        except Exception as e:
            logger.error(f"Error fetching holding records: {e}")
            return []

    async def _fetch_protocol_engagements(self, address: str, start_date: datetime,
                                        end_date: datetime) -> List[ProtocolEngagement]:
        """Fetch protocol engagement data"""
        try:
            # Simulate protocol engagement data
            engagements = [
                ProtocolEngagement(
                    protocol_name="Tinyman",
                    first_interaction=datetime(2021, 9, 1),
                    total_transactions=89,
                    total_volume_usd=245000.0,
                    unique_features_used=["swap", "add_liquidity", "remove_liquidity", "farming"],
                    governance_participation=True,
                    liquidity_provided=12500.0,
                    staking_amount=0.0,
                    engagement_consistency=0.87,
                    loyalty_score=0.92
                ),
                ProtocolEngagement(
                    protocol_name="Folks Finance",
                    first_interaction=datetime(2021, 12, 15),
                    total_transactions=34,
                    total_volume_usd=89000.0,
                    unique_features_used=["lending", "borrowing", "collateral_management"],
                    governance_participation=True,
                    liquidity_provided=0.0,
                    staking_amount=25000.0,
                    engagement_consistency=0.78,
                    loyalty_score=0.85
                ),
                ProtocolEngagement(
                    protocol_name="AlgoFi",
                    first_interaction=datetime(2022, 2, 10),
                    total_transactions=56,
                    total_volume_usd=156000.0,
                    unique_features_used=["lending", "vault_strategies", "swap"],
                    governance_participation=False,
                    liquidity_provided=0.0,
                    staking_amount=15000.0,
                    engagement_consistency=0.82,
                    loyalty_score=0.79
                ),
                ProtocolEngagement(
                    protocol_name="Yieldly",
                    first_interaction=datetime(2021, 7, 20),
                    total_transactions=123,
                    total_volume_usd=67000.0,
                    unique_features_used=["staking", "no_loss_lottery", "asset_staking"],
                    governance_participation=False,
                    liquidity_provided=0.0,
                    staking_amount=45000.0,
                    engagement_consistency=0.65,
                    loyalty_score=0.71
                )
            ]

            return engagements

        except Exception as e:
            logger.error(f"Error fetching protocol engagements: {e}")
            return []

    async def _fetch_market_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch market condition data for the analysis period"""
        try:
            # Simulate market data
            market_data = {
                "periods": [
                    {
                        "start_date": "2021-03-01",
                        "end_date": "2021-11-30",
                        "condition": MarketCondition.BULL_MARKET,
                        "algo_price_start": 0.35,
                        "algo_price_end": 1.85,
                        "volatility": 0.65
                    },
                    {
                        "start_date": "2021-12-01",
                        "end_date": "2022-06-30",
                        "condition": MarketCondition.BEAR_MARKET,
                        "algo_price_start": 1.85,
                        "algo_price_end": 0.35,
                        "volatility": 0.78
                    }
                ],
                "current_cycle": MarketCondition.BEAR_MARKET,
                "algo_historical_high": 2.95,
                "algo_historical_low": 0.08
            }

            return market_data

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {}

    async def _fetch_defi_activities(self, address: str, start_date: datetime,
                                   end_date: datetime) -> Dict[str, Any]:
        """Fetch DeFi activity data"""
        try:
            # Simulate DeFi activities
            defi_data = {
                "total_defi_transactions": 234,
                "total_defi_volume": 567000.0,
                "protocols_used": 6,
                "yield_farming_participation": True,
                "lending_borrowing_ratio": 2.3,
                "average_position_duration": 156,  # days
                "risk_adjusted_returns": 0.12
            }

            return defi_data

        except Exception as e:
            logger.error(f"Error fetching DeFi activities: {e}")
            return {}

    def _calculate_holding_patterns_score(self, holding_records: List[HoldingRecord],
                                        market_data: Dict[str, Any]) -> float:
        """Calculate holding patterns score based on duration and consistency"""
        try:
            if not holding_records:
                return 0.0

            config = self.commitment_config['holding_patterns']

            # Calculate ALGO holding metrics
            algo_holdings = [h for h in holding_records if h.asset_type == AssetType.ALGO]
            algo_score = 0.0

            if algo_holdings:
                # Duration score
                max_duration = max(h.holding_duration_days for h in algo_holdings)
                duration_score = min(1.0, max_duration / 365) * 100  # Normalize to 1 year

                # Consistency score (based on net accumulation)
                total_net_flow = sum(h.net_flow for h in algo_holdings)
                consistency_score = 100 if total_net_flow > 0 else 50  # Accumulation vs distribution

                # Accumulation pattern score
                accumulation_pattern = self._analyze_accumulation_pattern(algo_holdings)

                algo_score = (
                    duration_score * config['algo_holding_duration'] +
                    consistency_score * config['holding_consistency'] +
                    accumulation_pattern * config['accumulation_patterns']
                )

            return min(100.0, algo_score)

        except Exception as e:
            logger.error(f"Error calculating holding patterns score: {e}")
            return 0.0

    def _calculate_protocol_engagement_score(self, protocol_engagements: List[ProtocolEngagement]) -> float:
        """Calculate protocol engagement score"""
        try:
            if not protocol_engagements:
                return 0.0

            config = self.commitment_config['protocol_engagement']

            # DeFi participation score
            defi_protocols = [p for p in protocol_engagements if any(
                feature in ["lending", "borrowing", "swap", "add_liquidity"]
                for feature in p.unique_features_used
            )]
            defi_score = min(100, len(defi_protocols) * 25)

            # NFT ecosystem score
            nft_protocols = [p for p in protocol_engagements if any(
                "nft" in feature.lower() for feature in p.unique_features_used
            )]
            nft_score = min(100, len(nft_protocols) * 30)

            # DApp usage diversity
            total_protocols = len(protocol_engagements)
            dapp_score = min(100, total_protocols * 20)

            # Apply config weights
            weighted_score = (
                defi_score * config['defi_participation'] +
                nft_score * config['nft_ecosystem'] +
                dapp_score * config['dapp_usage']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating protocol engagement score: {e}")
            return 0.0

    def _calculate_investment_patterns_score(self, holding_records: List[HoldingRecord]) -> float:
        """Calculate investment diversification and pattern score"""
        try:
            if not holding_records:
                return 0.0

            config = self.commitment_config['investment_patterns']

            # ASA investment score
            asa_holdings = [h for h in holding_records if h.asset_type == AssetType.ASA]
            asa_score = min(100, len(asa_holdings) * 20)

            # Protocol token score
            protocol_tokens = [h for h in holding_records if h.asset_type == AssetType.PROTOCOL_TOKEN]
            protocol_score = min(100, len(protocol_tokens) * 25)

            # Ecosystem projects score (LP tokens, etc.)
            ecosystem_holdings = [h for h in holding_records if h.asset_type in [AssetType.LP_TOKEN, AssetType.NFT]]
            ecosystem_score = min(100, len(ecosystem_holdings) * 30)

            # Apply config weights
            weighted_score = (
                asa_score * config['asa_investments'] +
                protocol_score * config['protocol_tokens'] +
                ecosystem_score * config['ecosystem_projects']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating investment patterns score: {e}")
            return 0.0

    def _calculate_loyalty_metrics_score(self, holding_records: List[HoldingRecord],
                                       protocol_engagements: List[ProtocolEngagement],
                                       market_data: Dict[str, Any]) -> float:
        """Calculate loyalty and market cycle consistency score"""
        try:
            config = self.commitment_config['loyalty_metrics']

            # Bear market activity score
            bear_market_score = self._calculate_bear_market_activity(holding_records, market_data)

            # Consistent usage score
            consistent_usage_score = self._calculate_consistent_usage(protocol_engagements)

            # Protocol evangelism score (based on governance participation)
            evangelism_score = self._calculate_evangelism_score(protocol_engagements)

            # Apply config weights
            weighted_score = (
                bear_market_score * config['bear_market_activity'] +
                consistent_usage_score * config['consistent_usage'] +
                evangelism_score * config['protocol_evangelism']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating loyalty metrics score: {e}")
            return 0.0

    def _calculate_overall_commitment_score(self, holding_patterns_score: float,
                                          protocol_engagement_score: float,
                                          investment_patterns_score: float,
                                          loyalty_metrics_score: float) -> float:
        """Calculate overall ecosystem commitment score"""
        try:
            weights = self.commitment_config['category_weights']

            weighted_score = (
                holding_patterns_score * weights['holding_patterns'] +
                protocol_engagement_score * weights['protocol_engagement'] +
                investment_patterns_score * weights['investment_patterns'] +
                loyalty_metrics_score * weights['loyalty_metrics']
            )

            return min(100.0, weighted_score)

        except Exception as e:
            logger.error(f"Error calculating overall commitment score: {e}")
            return 0.0

    def _analyze_accumulation_pattern(self, algo_holdings: List[HoldingRecord]) -> float:
        """Analyze ALGO accumulation patterns"""
        try:
            if not algo_holdings:
                return 0.0

            # Calculate net accumulation rate
            total_net_flow = sum(h.net_flow for h in algo_holdings)
            total_transactions = sum(h.transaction_count for h in algo_holdings)

            if total_transactions == 0:
                return 0.0

            # Positive net flow indicates accumulation
            accumulation_rate = total_net_flow / total_transactions

            # Normalize to 0-100 scale
            return min(100.0, max(0.0, accumulation_rate / 1000 * 100))

        except Exception as e:
            logger.error(f"Error analyzing accumulation pattern: {e}")
            return 0.0

    def _calculate_portfolio_diversification(self, holding_records: List[HoldingRecord]) -> float:
        """Calculate portfolio diversification score"""
        try:
            if not holding_records:
                return 0.0

            # Count unique asset types
            asset_types = set(h.asset_type for h in holding_records)
            type_diversity = len(asset_types) / len(AssetType)

            # Calculate value distribution
            total_value = sum(h.value_usd for h in holding_records)
            if total_value == 0:
                return 0.0

            # Calculate Herfindahl-Hirschman Index for concentration
            shares = [h.value_usd / total_value for h in holding_records]
            hhi = sum(share ** 2 for share in shares)

            # Convert to diversification score (lower HHI = higher diversification)
            diversification = 1 - hhi

            # Combine type diversity and value diversification
            return (type_diversity * 0.6 + diversification * 0.4) * 100

        except Exception as e:
            logger.error(f"Error calculating portfolio diversification: {e}")
            return 0.0

    def _calculate_average_holding_duration(self, holding_records: List[HoldingRecord]) -> float:
        """Calculate average holding duration in days"""
        try:
            if not holding_records:
                return 0.0

            durations = [h.holding_duration_days for h in holding_records]
            return sum(durations) / len(durations)

        except Exception as e:
            logger.error(f"Error calculating average holding duration: {e}")
            return 0.0

    def _calculate_market_cycle_consistency(self, holding_records: List[HoldingRecord],
                                          market_data: Dict[str, Any]) -> float:
        """Calculate consistency across market cycles"""
        try:
            # Simplified market cycle analysis
            # In practice, this would analyze holding behavior during different market conditions
            algo_holdings = [h for h in holding_records if h.asset_type == AssetType.ALGO]

            if not algo_holdings:
                return 0.0

            # Check for long-term holding across market cycles
            max_duration = max(h.holding_duration_days for h in algo_holdings)

            # Score based on holding through market cycles (>365 days = full cycle)
            cycle_score = min(1.0, max_duration / 365)

            return cycle_score * 100

        except Exception as e:
            logger.error(f"Error calculating market cycle consistency: {e}")
            return 0.0

    def _calculate_bear_market_activity(self, holding_records: List[HoldingRecord],
                                      market_data: Dict[str, Any]) -> float:
        """Calculate activity and accumulation during bear markets"""
        try:
            # Simplified bear market analysis
            # Check for net accumulation during recent periods
            recent_holdings = [h for h in holding_records if h.last_transaction > datetime.utcnow() - timedelta(days=180)]

            if not recent_holdings:
                return 50.0  # Neutral score for no recent activity

            # Calculate net flow in recent period
            total_net_flow = sum(h.net_flow for h in recent_holdings)

            # Positive flow during bear market indicates strong commitment
            if total_net_flow > 0:
                return 90.0
            elif total_net_flow < -10000:  # Significant selling
                return 20.0
            else:
                return 60.0  # Holding steady

        except Exception as e:
            logger.error(f"Error calculating bear market activity: {e}")
            return 50.0

    def _calculate_consistent_usage(self, protocol_engagements: List[ProtocolEngagement]) -> float:
        """Calculate consistent protocol usage score"""
        try:
            if not protocol_engagements:
                return 0.0

            # Calculate average engagement consistency
            avg_consistency = sum(p.engagement_consistency for p in protocol_engagements) / len(protocol_engagements)

            # Bonus for long-term protocol relationships
            long_term_protocols = [p for p in protocol_engagements if
                                 (datetime.utcnow() - p.first_interaction).days > 180]

            long_term_bonus = min(30, len(long_term_protocols) * 10)

            return min(100.0, avg_consistency * 70 + long_term_bonus)

        except Exception as e:
            logger.error(f"Error calculating consistent usage: {e}")
            return 0.0

    def _calculate_evangelism_score(self, protocol_engagements: List[ProtocolEngagement]) -> float:
        """Calculate protocol evangelism score based on governance participation"""
        try:
            if not protocol_engagements:
                return 0.0

            # Count governance participation
            governance_participants = [p for p in protocol_engagements if p.governance_participation]
            participation_rate = len(governance_participants) / len(protocol_engagements)

            # Calculate loyalty score
            avg_loyalty = sum(p.loyalty_score for p in protocol_engagements) / len(protocol_engagements)

            return (participation_rate * 50 + avg_loyalty * 50)

        except Exception as e:
            logger.error(f"Error calculating evangelism score: {e}")
            return 0.0

    def _identify_commitment_indicators(self, holding_records: List[HoldingRecord],
                                      protocol_engagements: List[ProtocolEngagement]) -> List[str]:
        """Identify positive commitment indicators"""
        indicators = []

        try:
            # Check for long-term ALGO holding
            algo_holdings = [h for h in holding_records if h.asset_type == AssetType.ALGO]
            if algo_holdings:
                max_duration = max(h.holding_duration_days for h in algo_holdings)
                if max_duration > 365:
                    indicators.append(f"Long-term ALGO holder ({max_duration} days)")

            # Check for diverse protocol engagement
            if len(protocol_engagements) > 3:
                indicators.append(f"Active across {len(protocol_engagements)} protocols")

            # Check for governance participation
            governance_protocols = [p for p in protocol_engagements if p.governance_participation]
            if governance_protocols:
                indicators.append(f"Governance participant in {len(governance_protocols)} protocols")

            # Check for DeFi participation
            defi_protocols = [p for p in protocol_engagements if any(
                feature in ["lending", "borrowing", "liquidity"]
                for feature in p.unique_features_used
            )]
            if defi_protocols:
                indicators.append("Active DeFi participant")

            # Check for ecosystem investment
            protocol_tokens = [h for h in holding_records if h.asset_type == AssetType.PROTOCOL_TOKEN]
            if protocol_tokens:
                indicators.append(f"Invested in {len(protocol_tokens)} ecosystem projects")

            # Check for high portfolio value
            total_value = sum(h.value_usd for h in holding_records)
            if total_value > 100000:
                indicators.append(f"High-value ecosystem participant (${total_value:,.0f})")

        except Exception as e:
            logger.error(f"Error identifying commitment indicators: {e}")

        return indicators

    def _identify_commitment_risks(self, holding_records: List[HoldingRecord],
                                 protocol_engagements: List[ProtocolEngagement]) -> List[str]:
        """Identify potential commitment risks"""
        risks = []

        try:
            # Check for recent selling activity
            recent_holdings = [h for h in holding_records if h.last_transaction > datetime.utcnow() - timedelta(days=90)]
            recent_sellers = [h for h in recent_holdings if h.net_flow < 0]

            if len(recent_sellers) > len(recent_holdings) * 0.5:
                risks.append("Recent selling activity detected")

            # Check for low ALGO percentage
            total_value = sum(h.value_usd for h in holding_records)
            algo_value = sum(h.value_usd for h in holding_records if h.asset_type == AssetType.ALGO)
            algo_percentage = (algo_value / total_value) if total_value > 0 else 0

            if algo_percentage < 0.3:
                risks.append("Low ALGO allocation in portfolio")

            # Check for protocol disengagement
            inactive_protocols = [p for p in protocol_engagements if p.engagement_consistency < 0.5]
            if len(inactive_protocols) > len(protocol_engagements) * 0.4:
                risks.append("Declining engagement with some protocols")

            # Check for short holding periods
            short_holdings = [h for h in holding_records if h.holding_duration_days < 90]
            if len(short_holdings) > len(holding_records) * 0.6:
                risks.append("Many short-term holdings suggest weak commitment")

            # Check for lack of governance participation
            governance_protocols = [p for p in protocol_engagements if p.governance_participation]
            if len(governance_protocols) == 0 and len(protocol_engagements) > 0:
                risks.append("No governance participation despite protocol usage")

        except Exception as e:
            logger.error(f"Error identifying commitment risks: {e}")

        return risks

    def _generate_commitment_recommendations(self, holding_patterns_score: float,
                                           protocol_engagement_score: float,
                                           investment_patterns_score: float,
                                           loyalty_metrics_score: float) -> List[str]:
        """Generate recommendations for improving ecosystem commitment"""
        recommendations = []

        try:
            if holding_patterns_score < 50:
                recommendations.append("Consider increasing long-term ALGO holdings and accumulation")

            if protocol_engagement_score < 40:
                recommendations.append("Engage with more DeFi protocols and ecosystem applications")

            if investment_patterns_score < 30:
                recommendations.append("Diversify into ecosystem projects and protocol tokens")

            if loyalty_metrics_score < 40:
                recommendations.append("Participate in protocol governance and maintain consistency")

            # Positive reinforcement for strong areas
            if holding_patterns_score > 80 and loyalty_metrics_score > 70:
                recommendations.append("Excellent long-term commitment - consider increasing protocol governance participation")

            if protocol_engagement_score > 80:
                recommendations.append("Strong protocol engagement - consider sharing knowledge with community")

        except Exception as e:
            logger.error(f"Error generating commitment recommendations: {e}")

        return recommendations