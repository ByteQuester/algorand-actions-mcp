"""
NFT Portfolio Analyzer

Analyzes NFT holdings, creation activity, and community engagement
to assess cultural participation and long-term ecosystem commitment.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class NFTHolding:
    """Individual NFT holding"""
    asset_id: int
    collection_name: str
    token_name: str
    rarity_rank: Optional[int]
    floor_price: float
    current_value: float
    acquisition_date: datetime
    acquisition_method: str  # 'purchase', 'mint', 'airdrop', 'trade'
    hold_duration_days: int


@dataclass
class CollectionAnalysis:
    """Analysis of holdings in a specific collection"""
    collection_name: str
    tokens_owned: int
    total_value: float
    average_rarity: float
    floor_exposure: float
    collection_tier: str
    first_acquisition: datetime
    holding_strategy: str  # 'collector', 'trader', 'speculator'


@dataclass
class CreatorActivity:
    """NFT creation and community activity"""
    collections_created: int
    tokens_minted: int
    total_sales_volume: float
    creator_royalties_earned: float
    community_engagement_score: float
    artistic_reputation_score: float


class NFTPortfolioAnalyzer:
    """
    Analyzes NFT portfolio composition, collection strategies, and creator
    activity to assess cultural engagement and ecosystem commitment.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.nft_config = config.get('nft_portfolio', {})
        self.collection_registry = self._load_collection_registry()

    async def analyze_nft_portfolio(self, wallet_address: str) -> Dict[str, Any]:
        """
        Analyze complete NFT portfolio and activity.

        Args:
            wallet_address: Algorand wallet address to analyze

        Returns:
            Dictionary containing NFT portfolio analysis
        """
        logger.info(f"Analyzing NFT portfolio for {wallet_address}")

        try:
            # Parallel data collection
            tasks = [
                self._fetch_nft_holdings(wallet_address),
                self._fetch_nft_trading_history(wallet_address),
                self._fetch_creator_activity(wallet_address),
                self._fetch_community_engagement(wallet_address)
            ]

            holdings, trading_history, creator_activity, community_engagement = await asyncio.gather(*tasks)

            # Portfolio composition analysis
            portfolio_composition = self._analyze_portfolio_composition(holdings)

            # Collection strategy analysis
            collection_strategies = await self._analyze_collection_strategies(
                holdings, trading_history
            )

            # Value and risk analysis
            value_analysis = self._analyze_portfolio_value_risk(holdings)

            # Trading behavior analysis
            trading_behavior = self._analyze_trading_behavior(trading_history)

            # Creator activity analysis
            creator_analysis = self._analyze_creator_activity(creator_activity)

            # Community engagement analysis
            community_analysis = self._analyze_community_engagement(community_engagement)

            # Calculate overall scores
            nft_scores = self._calculate_nft_scores(
                portfolio_composition, value_analysis, trading_behavior,
                creator_analysis, community_analysis
            )

            return {
                'portfolio_composition': portfolio_composition,
                'collection_strategies': collection_strategies,
                'value_analysis': value_analysis,
                'trading_behavior': trading_behavior,
                'creator_analysis': creator_analysis,
                'community_analysis': community_analysis,
                'nft_scores': nft_scores,
                'nft_count': len(holdings),
                'collection_count': len(set(h.collection_name for h in holdings)),
                'total_value': sum(h.current_value for h in holdings),
                'creator_activity': creator_activity.get('collections_created', 0) > 0,
                'avg_hold_time': self._calculate_average_hold_time(holdings)
            }

        except Exception as e:
            logger.error(f"NFT portfolio analysis failed for {wallet_address}: {e}")
            raise

    async def analyze_collection_behavior(
        self,
        wallet_address: str,
        collection_name: str
    ) -> Dict[str, Any]:
        """
        Analyze behavior within a specific NFT collection.

        Args:
            wallet_address: Algorand wallet address to analyze
            collection_name: Specific collection to analyze

        Returns:
            Collection-specific behavior analysis
        """
        logger.info(f"Analyzing collection behavior for {collection_name}")

        try:
            # Get collection-specific data
            holdings = await self._fetch_nft_holdings(wallet_address)
            collection_holdings = [h for h in holdings if h.collection_name == collection_name]

            trading_history = await self._fetch_nft_trading_history(wallet_address)
            collection_trades = [t for t in trading_history if t.get('collection') == collection_name]

            if not collection_holdings and not collection_trades:
                return {'error': f'No activity found in collection {collection_name}'}

            # Analyze collection-specific patterns
            collection_analysis = await self._analyze_single_collection(
                collection_name, collection_holdings, collection_trades
            )

            return {
                'collection_name': collection_name,
                'analysis': collection_analysis,
                'current_holdings': len(collection_holdings),
                'total_trades': len(collection_trades),
                'engagement_level': self._determine_collection_engagement_level(collection_analysis)
            }

        except Exception as e:
            logger.error(f"Collection behavior analysis failed: {e}")
            raise

    async def _fetch_nft_holdings(self, wallet_address: str) -> List[NFTHolding]:
        """Fetch current NFT holdings"""
        # Mock implementation - would integrate with NFT indexers
        return [
            NFTHolding(
                asset_id=123456789,
                collection_name='Algorand Pandas',
                token_name='Panda #1234',
                rarity_rank=156,
                floor_price=45.0,
                current_value=52.0,
                acquisition_date=datetime.utcnow() - timedelta(days=120),
                acquisition_method='purchase',
                hold_duration_days=120
            ),
            NFTHolding(
                asset_id=234567890,
                collection_name='AlgoGems',
                token_name='Gem #5678',
                rarity_rank=890,
                floor_price=12.0,
                current_value=15.0,
                acquisition_date=datetime.utcnow() - timedelta(days=45),
                acquisition_method='mint',
                hold_duration_days=45
            ),
            NFTHolding(
                asset_id=345678901,
                collection_name='Algorand Pandas',
                token_name='Panda #2468',
                rarity_rank=45,
                floor_price=45.0,
                current_value=120.0,
                acquisition_date=datetime.utcnow() - timedelta(days=200),
                acquisition_method='purchase',
                hold_duration_days=200
            )
        ]

    async def _fetch_nft_trading_history(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch NFT trading history"""
        # Mock implementation
        return [
            {
                'timestamp': datetime.utcnow() - timedelta(days=30),
                'collection': 'Algorand Pandas',
                'token_id': 9999,
                'action': 'sell',
                'price': 55.0,
                'profit_loss': 10.0
            },
            {
                'timestamp': datetime.utcnow() - timedelta(days=60),
                'collection': 'AlgoGems',
                'token_id': 1111,
                'action': 'buy',
                'price': 8.0,
                'profit_loss': 0.0
            },
            {
                'timestamp': datetime.utcnow() - timedelta(days=90),
                'collection': 'Cosmic Champs',
                'token_id': 2222,
                'action': 'sell',
                'price': 25.0,
                'profit_loss': 15.0
            }
        ]

    async def _fetch_creator_activity(self, wallet_address: str) -> CreatorActivity:
        """Fetch creator activity data"""
        # Mock implementation
        return CreatorActivity(
            collections_created=1,
            tokens_minted=25,
            total_sales_volume=1250.0,
            creator_royalties_earned=62.5,
            community_engagement_score=0.75,
            artistic_reputation_score=0.68
        )

    async def _fetch_community_engagement(self, wallet_address: str) -> Dict[str, Any]:
        """Fetch community engagement data"""
        # Mock implementation
        return {
            'discord_activity': True,
            'twitter_engagement': 0.6,
            'collection_votes_cast': 5,
            'community_proposals': 1,
            'social_influence_score': 0.4
        }

    def _analyze_portfolio_composition(self, holdings: List[NFTHolding]) -> Dict[str, Any]:
        """Analyze NFT portfolio composition"""
        if not holdings:
            return {'total_value': 0, 'collection_count': 0, 'diversification_score': 0}

        # Collection distribution
        collection_counts = Counter(h.collection_name for h in holdings)
        collection_values = defaultdict(float)
        for holding in holdings:
            collection_values[holding.collection_name] += holding.current_value

        total_value = sum(h.current_value for h in holdings)

        # Diversification analysis
        collection_percentages = [v / total_value for v in collection_values.values()] if total_value > 0 else []
        hhi = sum(p ** 2 for p in collection_percentages)
        diversification_score = 1 - hhi if len(collection_counts) > 1 else 0

        # Tier analysis
        tier_distribution = self._analyze_tier_distribution(holdings)

        # Acquisition method analysis
        acquisition_methods = Counter(h.acquisition_method for h in holdings)

        return {
            'total_value': total_value,
            'collection_count': len(collection_counts),
            'total_tokens': len(holdings),
            'diversification_score': diversification_score,
            'largest_collection_percentage': max(collection_percentages) if collection_percentages else 0,
            'tier_distribution': tier_distribution,
            'acquisition_methods': dict(acquisition_methods),
            'collection_distribution': dict(collection_counts),
            'average_token_value': total_value / len(holdings) if holdings else 0
        }

    async def _analyze_collection_strategies(
        self,
        holdings: List[NFTHolding],
        trading_history: List[Dict[str, Any]]
    ) -> List[CollectionAnalysis]:
        """Analyze strategies for each collection"""
        collection_analyses = []

        # Group holdings by collection
        collection_holdings = defaultdict(list)
        for holding in holdings:
            collection_holdings[holding.collection_name].append(holding)

        # Analyze each collection
        for collection_name, collection_tokens in collection_holdings.items():
            analysis = await self._analyze_single_collection(
                collection_name, collection_tokens, trading_history
            )
            collection_analyses.append(analysis)

        return collection_analyses

    async def _analyze_single_collection(
        self,
        collection_name: str,
        holdings: List[NFTHolding],
        trading_history: List[Dict[str, Any]]
    ) -> CollectionAnalysis:
        """Analyze strategy for a single collection"""

        if not holdings:
            # Return empty analysis for collections with no current holdings
            return CollectionAnalysis(
                collection_name=collection_name,
                tokens_owned=0,
                total_value=0.0,
                average_rarity=0.0,
                floor_exposure=0.0,
                collection_tier='unknown',
                first_acquisition=datetime.utcnow(),
                holding_strategy='none'
            )

        tokens_owned = len(holdings)
        total_value = sum(h.current_value for h in holdings)

        # Rarity analysis
        rarities = [h.rarity_rank for h in holdings if h.rarity_rank is not None]
        average_rarity = sum(rarities) / len(rarities) if rarities else 0

        # Floor exposure
        floor_prices = [h.floor_price for h in holdings]
        floor_value = sum(floor_prices)
        floor_exposure = floor_value / total_value if total_value > 0 else 0

        # Collection tier
        collection_tier = self._determine_collection_tier(collection_name)

        # First acquisition
        first_acquisition = min(h.acquisition_date for h in holdings)

        # Holding strategy
        holding_strategy = self._determine_holding_strategy(holdings, trading_history)

        return CollectionAnalysis(
            collection_name=collection_name,
            tokens_owned=tokens_owned,
            total_value=total_value,
            average_rarity=average_rarity,
            floor_exposure=floor_exposure,
            collection_tier=collection_tier,
            first_acquisition=first_acquisition,
            holding_strategy=holding_strategy
        )

    def _analyze_portfolio_value_risk(self, holdings: List[NFTHolding]) -> Dict[str, Any]:
        """Analyze portfolio value and risk characteristics"""
        if not holdings:
            return {}

        total_value = sum(h.current_value for h in holdings)
        floor_values = [h.floor_price for h in holdings]
        current_values = [h.current_value for h in holdings]

        # Value metrics
        total_floor_value = sum(floor_values)
        premium_to_floor = (total_value - total_floor_value) / total_floor_value if total_floor_value > 0 else 0

        # Risk metrics
        largest_position = max(current_values) / total_value if total_value > 0 else 0
        collection_concentration = self._calculate_collection_concentration(holdings)

        # Liquidity risk
        illiquid_tokens = sum(1 for h in holdings if h.floor_price < 1.0)  # Very low floor = illiquid
        liquidity_risk = illiquid_tokens / len(holdings)

        return {
            'total_portfolio_value': total_value,
            'total_floor_value': total_floor_value,
            'premium_to_floor': premium_to_floor,
            'largest_position_percentage': largest_position,
            'collection_concentration': collection_concentration,
            'liquidity_risk': liquidity_risk,
            'average_token_value': total_value / len(holdings),
            'value_at_risk_floor': 1.0 - (total_floor_value / total_value) if total_value > 0 else 0
        }

    def _analyze_trading_behavior(self, trading_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze NFT trading behavior patterns"""
        if not trading_history:
            return {'trading_activity': False}

        # Trading frequency
        trading_frequency = len(trading_history)

        # Profit/loss analysis
        profits_losses = [t.get('profit_loss', 0) for t in trading_history if 'profit_loss' in t]
        total_pnl = sum(profits_losses) if profits_losses else 0
        profitable_trades = sum(1 for pnl in profits_losses if pnl > 0)
        win_rate = profitable_trades / len(profits_losses) if profits_losses else 0

        # Trading patterns
        buy_count = sum(1 for t in trading_history if t.get('action') == 'buy')
        sell_count = sum(1 for t in trading_history if t.get('action') == 'sell')

        # Determine trading style
        trading_style = self._determine_trading_style(trading_history)

        return {
            'trading_activity': True,
            'total_trades': trading_frequency,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'trading_style': trading_style,
            'avg_profit_per_trade': total_pnl / len(profits_losses) if profits_losses else 0
        }

    def _analyze_creator_activity(self, creator_activity: CreatorActivity) -> Dict[str, Any]:
        """Analyze creator activity and reputation"""
        return {
            'is_creator': creator_activity.collections_created > 0,
            'collections_created': creator_activity.collections_created,
            'tokens_minted': creator_activity.tokens_minted,
            'total_sales_volume': creator_activity.total_sales_volume,
            'royalties_earned': creator_activity.creator_royalties_earned,
            'community_engagement': creator_activity.community_engagement_score,
            'artistic_reputation': creator_activity.artistic_reputation_score,
            'creator_sophistication': self._calculate_creator_sophistication(creator_activity)
        }

    def _analyze_community_engagement(self, community_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze community engagement metrics"""
        return {
            'discord_activity': community_data.get('discord_activity', False),
            'twitter_engagement': community_data.get('twitter_engagement', 0),
            'governance_participation': community_data.get('collection_votes_cast', 0) > 0,
            'community_proposals': community_data.get('community_proposals', 0),
            'social_influence': community_data.get('social_influence_score', 0),
            'overall_engagement': self._calculate_overall_community_engagement(community_data)
        }

    def _calculate_nft_scores(self, *analyses) -> Dict[str, float]:
        """Calculate comprehensive NFT portfolio scores"""
        portfolio_composition, value_analysis, trading_behavior, creator_analysis, community_analysis = analyses

        scores = {}

        # Diversity score
        scores['diversity_score'] = portfolio_composition.get('diversification_score', 0) * 100

        # Quality score (based on tier distribution and rarity)
        tier_dist = portfolio_composition.get('tier_distribution', {})
        blue_chip_ratio = tier_dist.get('blue_chip', 0)
        quality_score = blue_chip_ratio * 70 + tier_dist.get('established', 0) * 50
        scores['quality_score'] = min(quality_score, 100)

        # Trading sophistication
        trading_sophistication = 50  # Base score
        if trading_behavior.get('trading_activity', False):
            win_rate = trading_behavior.get('win_rate', 0)
            trading_sophistication += win_rate * 30
            if trading_behavior.get('total_pnl', 0) > 0:
                trading_sophistication += 20
        scores['trading_sophistication'] = min(trading_sophistication, 100)

        # Creator score
        creator_score = 0
        if creator_analysis.get('is_creator', False):
            creator_score = creator_analysis.get('creator_sophistication', 0) * 100
        scores['creator_score'] = creator_score

        # Community engagement score
        scores['community_engagement_score'] = community_analysis.get('overall_engagement', 0) * 100

        # Overall NFT sophistication
        weights = {
            'diversity_score': 0.2,
            'quality_score': 0.3,
            'trading_sophistication': 0.2,
            'creator_score': 0.15,
            'community_engagement_score': 0.15
        }

        overall_score = sum(scores[key] * weight for key, weight in weights.items() if key in scores)
        scores['overall_nft_score'] = overall_score

        return scores

    def _analyze_tier_distribution(self, holdings: List[NFTHolding]) -> Dict[str, float]:
        """Analyze distribution across collection tiers"""
        if not holdings:
            return {}

        total_value = sum(h.current_value for h in holdings)
        tier_values = defaultdict(float)

        for holding in holdings:
            tier = self._determine_collection_tier(holding.collection_name)
            tier_values[tier] += holding.current_value

        # Convert to percentages
        tier_percentages = {}
        for tier, value in tier_values.items():
            tier_percentages[tier] = value / total_value if total_value > 0 else 0

        return tier_percentages

    def _determine_collection_tier(self, collection_name: str) -> str:
        """Determine the tier of a collection"""
        # Mock implementation - would use real collection data
        blue_chip_collections = ['Algorand Pandas', 'AlgoGems Genesis']
        established_collections = ['Cosmic Champs', 'AlgoGems']

        if collection_name in blue_chip_collections:
            return 'blue_chip'
        elif collection_name in established_collections:
            return 'established'
        else:
            return 'emerging'

    def _determine_holding_strategy(
        self,
        holdings: List[NFTHolding],
        trading_history: List[Dict[str, Any]]
    ) -> str:
        """Determine holding strategy for a collection"""
        # Calculate average hold time
        avg_hold_time = sum(h.hold_duration_days for h in holdings) / len(holdings)

        # Check trading activity
        collection_name = holdings[0].collection_name if holdings else ''
        collection_trades = [t for t in trading_history if t.get('collection') == collection_name]

        if avg_hold_time > 180:  # 6+ months
            return 'long_term_collector'
        elif len(collection_trades) > len(holdings):
            return 'active_trader'
        elif avg_hold_time > 30:
            return 'medium_term_holder'
        else:
            return 'short_term_speculator'

    def _calculate_collection_concentration(self, holdings: List[NFTHolding]) -> float:
        """Calculate concentration risk across collections"""
        collection_values = defaultdict(float)
        total_value = sum(h.current_value for h in holdings)

        for holding in holdings:
            collection_values[holding.collection_name] += holding.current_value

        if total_value == 0:
            return 0

        # Calculate Herfindahl-Hirschman Index
        percentages = [v / total_value for v in collection_values.values()]
        hhi = sum(p ** 2 for p in percentages)

        return hhi

    def _determine_trading_style(self, trading_history: List[Dict[str, Any]]) -> str:
        """Determine overall trading style"""
        if len(trading_history) < 3:
            return 'minimal_trader'

        # Calculate trade frequency
        if len(trading_history) > 20:
            return 'active_trader'
        elif len(trading_history) > 10:
            return 'moderate_trader'
        else:
            return 'occasional_trader'

    def _calculate_creator_sophistication(self, creator_activity: CreatorActivity) -> float:
        """Calculate creator sophistication score"""
        if creator_activity.collections_created == 0:
            return 0.0

        base_score = 0.3  # Base for being a creator

        # Volume bonus
        if creator_activity.total_sales_volume > 1000:
            base_score += 0.3
        elif creator_activity.total_sales_volume > 100:
            base_score += 0.2

        # Community engagement bonus
        base_score += creator_activity.community_engagement_score * 0.2

        # Artistic reputation bonus
        base_score += creator_activity.artistic_reputation_score * 0.2

        return min(base_score, 1.0)

    def _calculate_overall_community_engagement(self, community_data: Dict[str, Any]) -> float:
        """Calculate overall community engagement score"""
        engagement_score = 0.0

        # Discord activity
        if community_data.get('discord_activity', False):
            engagement_score += 0.25

        # Twitter engagement
        engagement_score += community_data.get('twitter_engagement', 0) * 0.25

        # Governance participation
        if community_data.get('collection_votes_cast', 0) > 0:
            engagement_score += 0.25

        # Social influence
        engagement_score += community_data.get('social_influence_score', 0) * 0.25

        return min(engagement_score, 1.0)

    def _calculate_average_hold_time(self, holdings: List[NFTHolding]) -> float:
        """Calculate average holding time across all NFTs"""
        if not holdings:
            return 0.0

        return sum(h.hold_duration_days for h in holdings) / len(holdings)

    def _determine_collection_engagement_level(self, analysis: CollectionAnalysis) -> str:
        """Determine engagement level with a specific collection"""
        if analysis.tokens_owned == 0:
            return 'no_engagement'
        elif analysis.tokens_owned == 1:
            return 'minimal_engagement'
        elif analysis.tokens_owned <= 5:
            return 'moderate_engagement'
        else:
            return 'high_engagement'

    def _load_collection_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load collection registry with metadata"""
        return {
            'Algorand Pandas': {
                'tier': 'blue_chip',
                'floor_price': 45.0,
                'market_cap': 450000.0,
                'category': 'pfp'
            },
            'AlgoGems': {
                'tier': 'established',
                'floor_price': 12.0,
                'market_cap': 120000.0,
                'category': 'gaming'
            },
            'Cosmic Champs': {
                'tier': 'established',
                'floor_price': 25.0,
                'market_cap': 250000.0,
                'category': 'gaming'
            }
        }