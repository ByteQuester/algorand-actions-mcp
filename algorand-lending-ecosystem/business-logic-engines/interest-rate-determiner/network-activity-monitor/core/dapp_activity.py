"""
DApp Activity Monitor
Monitors smart contract activity, DeFi protocol usage, and ecosystem engagement.
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
class ProtocolActivity:
    """Activity metrics for a specific protocol"""
    protocol_name: str
    app_ids: List[int]

    # Transaction metrics
    total_transactions: int
    daily_transactions: int
    transaction_growth: float

    # Value metrics
    total_volume_usd: float
    daily_volume_usd: float
    volume_growth: float

    # User metrics
    unique_users: int
    daily_active_users: int
    user_growth: float

    # Protocol-specific metrics
    custom_metrics: Dict[str, float]


@dataclass
class DeFiMetrics:
    """DeFi ecosystem activity metrics"""
    # Trading activity
    dex_volume_24h: float
    dex_trades_count: int
    swap_protocols: List[ProtocolActivity]

    # Lending activity
    lending_volume_24h: float
    borrows_count: int
    supplies_count: int
    lending_protocols: List[ProtocolActivity]

    # Liquidity provision
    total_liquidity_pools: int
    total_tvl_usd: float
    liquidity_growth: float

    # Yield farming
    farming_protocols: int
    staking_volume: float
    average_apr: float


@dataclass
class NFTActivity:
    """NFT marketplace activity"""
    # Marketplace metrics
    total_marketplaces: int
    daily_sales_count: int
    daily_sales_volume: float

    # Creation metrics
    new_collections: int
    new_nfts_minted: int
    creator_count: int

    # Trading metrics
    floor_price_changes: Dict[str, float]
    volume_by_marketplace: Dict[str, float]


@dataclass
class GovernanceActivity:
    """Governance participation metrics"""
    # Participation metrics
    total_participants: int
    participation_rate: float
    algo_committed: float

    # Voting metrics
    active_proposals: int
    votes_cast: int
    voting_participation: float

    # Delegation metrics
    delegated_stake: float
    delegation_rate: float


@dataclass
class SmartContractMetrics:
    """Overall smart contract activity"""
    # Application metrics
    total_app_calls: int
    daily_app_calls: int
    unique_apps_used: int

    # Popular applications
    top_apps_by_calls: List[Tuple[int, int]]  # (app_id, call_count)
    top_apps_by_users: List[Tuple[int, int]]   # (app_id, user_count)

    # Growth metrics
    new_applications: int
    app_call_growth: float
    user_adoption_rate: float


@dataclass
class DAppActivityReport:
    """Comprehensive DApp activity report"""
    timestamp: datetime

    # Core metrics
    smart_contract_metrics: SmartContractMetrics
    defi_metrics: DeFiMetrics
    nft_activity: NFTActivity
    governance_activity: GovernanceActivity

    # Aggregate scores
    defi_activity_score: float
    nft_activity_score: float
    governance_activity_score: float
    overall_activity_score: float

    # Ecosystem health
    ecosystem_status: str
    activity_trend: str
    growth_indicators: List[str]
    recommendations: List[str]


class DAppActivityMonitor:
    """Monitors DApp activity and ecosystem engagement"""

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
        self.dapp_config = config['dapp_monitoring']
        self.activity_thresholds = config['dapp_monitoring']['activity_levels']

        # Protocol configurations
        self.defi_protocols = self.dapp_config['defi_protocols']
        self.nft_platforms = self.dapp_config['nft_platforms']

    async def get_dapp_activity_report(self) -> DAppActivityReport:
        """Generate comprehensive DApp activity report"""
        try:
            self.logger.info("Generating DApp activity report")

            # Collect metrics in parallel
            results = await asyncio.gather(
                self._analyze_smart_contract_activity(),
                self._analyze_defi_activity(),
                self._analyze_nft_activity(),
                self._analyze_governance_activity(),
                return_exceptions=True
            )

            # Extract results
            sc_metrics = results[0] if not isinstance(results[0], Exception) else self._default_sc_metrics()
            defi_metrics = results[1] if not isinstance(results[1], Exception) else self._default_defi_metrics()
            nft_activity = results[2] if not isinstance(results[2], Exception) else self._default_nft_activity()
            governance_activity = results[3] if not isinstance(results[3], Exception) else self._default_governance_activity()

            # Calculate activity scores
            defi_score = self._calculate_defi_activity_score(defi_metrics)
            nft_score = self._calculate_nft_activity_score(nft_activity)
            governance_score = self._calculate_governance_activity_score(governance_activity)

            # Overall activity score
            overall_score = self._calculate_overall_activity_score(
                defi_score, nft_score, governance_score, sc_metrics
            )

            # Determine ecosystem status
            ecosystem_status = self._determine_ecosystem_status(overall_score)

            # Analyze trends
            activity_trend = self._analyze_activity_trend(defi_metrics, nft_activity, governance_activity)

            # Generate insights
            growth_indicators = self._identify_growth_indicators(
                defi_metrics, nft_activity, governance_activity, sc_metrics
            )
            recommendations = self._generate_activity_recommendations(
                defi_metrics, nft_activity, governance_activity, overall_score
            )

            return DAppActivityReport(
                timestamp=datetime.utcnow(),
                smart_contract_metrics=sc_metrics,
                defi_metrics=defi_metrics,
                nft_activity=nft_activity,
                governance_activity=governance_activity,
                defi_activity_score=defi_score,
                nft_activity_score=nft_score,
                governance_activity_score=governance_score,
                overall_activity_score=overall_score,
                ecosystem_status=ecosystem_status,
                activity_trend=activity_trend,
                growth_indicators=growth_indicators,
                recommendations=recommendations
            )

        except Exception as e:
            self.logger.error(f"Error generating DApp activity report: {e}")
            raise

    async def _analyze_smart_contract_activity(self) -> SmartContractMetrics:
        """Analyze overall smart contract activity"""
        try:
            # Get application call transactions for the last 24 hours
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)

            # Query application transactions
            response = self.indexer_client.search_transactions(
                txn_type='appl',
                min_timestamp=int(start_time.timestamp()),
                max_timestamp=int(end_time.timestamp()),
                limit=10000
            )

            transactions = response.get('transactions', [])

            # Analyze application usage
            app_call_counts = {}
            app_users = {}
            total_app_calls = len(transactions)

            for tx in transactions:
                app_tx = tx.get('application-transaction', {})
                app_id = app_tx.get('application-id', 0)
                sender = tx.get('sender', '')

                if app_id > 0:
                    app_call_counts[app_id] = app_call_counts.get(app_id, 0) + 1

                    if app_id not in app_users:
                        app_users[app_id] = set()
                    app_users[app_id].add(sender)

            # Get top applications
            top_apps_by_calls = sorted(app_call_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_apps_by_users = sorted(
                [(app_id, len(users)) for app_id, users in app_users.items()],
                key=lambda x: x[1], reverse=True
            )[:10]

            # Count unique applications used
            unique_apps_used = len(app_call_counts)

            # Estimate growth (simplified)
            app_call_growth = await self._estimate_app_call_growth()
            user_adoption_rate = await self._estimate_user_adoption_rate()

            # Count new applications (simplified)
            new_applications = await self._count_new_applications()

            return SmartContractMetrics(
                total_app_calls=total_app_calls,
                daily_app_calls=total_app_calls,  # Already 24h data
                unique_apps_used=unique_apps_used,
                top_apps_by_calls=top_apps_by_calls,
                top_apps_by_users=top_apps_by_users,
                new_applications=new_applications,
                app_call_growth=app_call_growth,
                user_adoption_rate=user_adoption_rate
            )

        except Exception as e:
            self.logger.error(f"Error analyzing smart contract activity: {e}")
            return self._default_sc_metrics()

    async def _analyze_defi_activity(self) -> DeFiMetrics:
        """Analyze DeFi protocol activity"""
        try:
            # Analyze each DeFi protocol
            protocol_activities = []

            for protocol_name, protocol_config in self.defi_protocols.items():
                activity = await self._analyze_protocol_activity(
                    protocol_name, protocol_config['app_ids'], protocol_config['metrics']
                )
                protocol_activities.append(activity)

            # Aggregate DeFi metrics
            dex_protocols = [p for p in protocol_activities if 'tinyman' in p.protocol_name.lower() or 'pact' in p.protocol_name.lower()]
            lending_protocols = [p for p in protocol_activities if 'algofi' in p.protocol_name.lower() or 'folks' in p.protocol_name.lower()]

            # Calculate aggregate metrics
            dex_volume_24h = sum(p.daily_volume_usd for p in dex_protocols)
            dex_trades_count = sum(p.daily_transactions for p in dex_protocols)

            lending_volume_24h = sum(p.daily_volume_usd for p in lending_protocols)
            borrows_count = sum(p.daily_transactions for p in lending_protocols) // 2  # Estimate
            supplies_count = sum(p.daily_transactions for p in lending_protocols) // 2  # Estimate

            # TVL and liquidity metrics (simplified)
            total_tvl_usd = await self._estimate_total_tvl()
            total_liquidity_pools = await self._count_liquidity_pools()
            liquidity_growth = await self._calculate_liquidity_growth()

            # Yield farming metrics
            farming_protocols = len([p for p in protocol_activities if 'farm' in str(p.custom_metrics)])
            staking_volume = await self._estimate_staking_volume()
            average_apr = await self._estimate_average_apr()

            return DeFiMetrics(
                dex_volume_24h=dex_volume_24h,
                dex_trades_count=dex_trades_count,
                swap_protocols=dex_protocols,
                lending_volume_24h=lending_volume_24h,
                borrows_count=borrows_count,
                supplies_count=supplies_count,
                lending_protocols=lending_protocols,
                total_liquidity_pools=total_liquidity_pools,
                total_tvl_usd=total_tvl_usd,
                liquidity_growth=liquidity_growth,
                farming_protocols=farming_protocols,
                staking_volume=staking_volume,
                average_apr=average_apr
            )

        except Exception as e:
            self.logger.error(f"Error analyzing DeFi activity: {e}")
            return self._default_defi_metrics()

    async def _analyze_nft_activity(self) -> NFTActivity:
        """Analyze NFT marketplace activity"""
        try:
            # Analyze NFT platforms
            total_marketplaces = len(self.nft_platforms)
            daily_sales_data = []

            for platform_name, platform_config in self.nft_platforms.items():
                platform_activity = await self._analyze_nft_platform_activity(
                    platform_name, platform_config['app_ids']
                )
                daily_sales_data.append(platform_activity)

            # Aggregate NFT metrics
            daily_sales_count = sum(data.get('sales_count', 0) for data in daily_sales_data)
            daily_sales_volume = sum(data.get('sales_volume', 0) for data in daily_sales_data)

            # Creation metrics
            new_collections = await self._count_new_nft_collections()
            new_nfts_minted = await self._count_new_nfts_minted()
            creator_count = await self._count_active_nft_creators()

            # Trading metrics
            floor_price_changes = await self._analyze_floor_price_changes()
            volume_by_marketplace = {
                data.get('marketplace', 'unknown'): data.get('sales_volume', 0)
                for data in daily_sales_data
            }

            return NFTActivity(
                total_marketplaces=total_marketplaces,
                daily_sales_count=daily_sales_count,
                daily_sales_volume=daily_sales_volume,
                new_collections=new_collections,
                new_nfts_minted=new_nfts_minted,
                creator_count=creator_count,
                floor_price_changes=floor_price_changes,
                volume_by_marketplace=volume_by_marketplace
            )

        except Exception as e:
            self.logger.error(f"Error analyzing NFT activity: {e}")
            return self._default_nft_activity()

    async def _analyze_governance_activity(self) -> GovernanceActivity:
        """Analyze governance participation"""
        try:
            # This would analyze current governance period activity
            # For now, return estimates

            # Governance participation metrics
            total_participants = await self._count_governance_participants()
            total_algo_supply = 10_000_000_000  # 10B ALGO
            participation_rate = total_participants / 1_000_000  # Estimate

            # ALGO commitment
            algo_committed = await self._get_committed_algo()

            # Voting metrics
            active_proposals = await self._count_active_proposals()
            votes_cast = await self._count_recent_votes()
            voting_participation = votes_cast / max(total_participants, 1)

            # Delegation (if applicable)
            delegated_stake = await self._get_delegated_stake()
            delegation_rate = delegated_stake / max(algo_committed, 1)

            return GovernanceActivity(
                total_participants=total_participants,
                participation_rate=participation_rate,
                algo_committed=algo_committed,
                active_proposals=active_proposals,
                votes_cast=votes_cast,
                voting_participation=voting_participation,
                delegated_stake=delegated_stake,
                delegation_rate=delegation_rate
            )

        except Exception as e:
            self.logger.error(f"Error analyzing governance activity: {e}")
            return self._default_governance_activity()

    async def _analyze_protocol_activity(
        self, protocol_name: str, app_ids: List[int], metrics: List[str]
    ) -> ProtocolActivity:
        """Analyze activity for a specific protocol"""
        try:
            # Get transactions for all app IDs
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)

            total_transactions = 0
            unique_users = set()
            total_volume = 0.0

            for app_id in app_ids:
                try:
                    response = self.indexer_client.search_transactions(
                        application_id=app_id,
                        min_timestamp=int(start_time.timestamp()),
                        max_timestamp=int(end_time.timestamp()),
                        limit=5000
                    )

                    transactions = response.get('transactions', [])
                    total_transactions += len(transactions)

                    for tx in transactions:
                        sender = tx.get('sender', '')
                        if sender:
                            unique_users.add(sender)

                        # Estimate volume (simplified)
                        if 'payment-transaction' in tx:
                            amount = tx['payment-transaction'].get('amount', 0) / 1e6
                            total_volume += amount

                except Exception as e:
                    self.logger.error(f"Error analyzing app {app_id}: {e}")
                    continue

            # Calculate growth (simplified)
            transaction_growth = await self._estimate_protocol_growth(protocol_name, 'transactions')
            volume_growth = await self._estimate_protocol_growth(protocol_name, 'volume')
            user_growth = await self._estimate_protocol_growth(protocol_name, 'users')

            # Protocol-specific metrics
            custom_metrics = await self._get_protocol_custom_metrics(protocol_name, app_ids)

            return ProtocolActivity(
                protocol_name=protocol_name,
                app_ids=app_ids,
                total_transactions=total_transactions,
                daily_transactions=total_transactions,  # Already 24h data
                transaction_growth=transaction_growth,
                total_volume_usd=total_volume,  # Simplified - would convert to USD
                daily_volume_usd=total_volume,
                volume_growth=volume_growth,
                unique_users=len(unique_users),
                daily_active_users=len(unique_users),
                user_growth=user_growth,
                custom_metrics=custom_metrics
            )

        except Exception as e:
            self.logger.error(f"Error analyzing protocol {protocol_name}: {e}")
            return ProtocolActivity(
                protocol_name=protocol_name,
                app_ids=app_ids,
                total_transactions=0,
                daily_transactions=0,
                transaction_growth=0.0,
                total_volume_usd=0.0,
                daily_volume_usd=0.0,
                volume_growth=0.0,
                unique_users=0,
                daily_active_users=0,
                user_growth=0.0,
                custom_metrics={}
            )

    async def _analyze_nft_platform_activity(self, platform_name: str, app_ids: List[int]) -> Dict:
        """Analyze NFT platform activity"""
        try:
            # Analyze NFT-related transactions
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)

            sales_count = 0
            sales_volume = 0.0

            for app_id in app_ids:
                try:
                    response = self.indexer_client.search_transactions(
                        application_id=app_id,
                        min_timestamp=int(start_time.timestamp()),
                        max_timestamp=int(end_time.timestamp()),
                        limit=1000
                    )

                    transactions = response.get('transactions', [])

                    # Analyze for NFT sales (simplified)
                    for tx in transactions:
                        # Look for asset transfer transactions that might be NFT sales
                        if 'asset-transfer-transaction' in tx:
                            sales_count += 1
                            # Estimate sale volume (would need more sophisticated parsing)
                            sales_volume += 10.0  # Placeholder

                except Exception as e:
                    self.logger.error(f"Error analyzing NFT app {app_id}: {e}")
                    continue

            return {
                'marketplace': platform_name,
                'sales_count': sales_count,
                'sales_volume': sales_volume
            }

        except Exception as e:
            self.logger.error(f"Error analyzing NFT platform {platform_name}: {e}")
            return {'marketplace': platform_name, 'sales_count': 0, 'sales_volume': 0.0}

    # Helper methods for estimates and calculations (simplified implementations)
    async def _estimate_app_call_growth(self) -> float:
        """Estimate application call growth rate"""
        return 0.15  # 15% growth estimate

    async def _estimate_user_adoption_rate(self) -> float:
        """Estimate user adoption rate"""
        return 0.12  # 12% growth estimate

    async def _count_new_applications(self) -> int:
        """Count newly created applications"""
        return 25  # Estimate

    async def _estimate_total_tvl(self) -> float:
        """Estimate total value locked in DeFi"""
        return 150_000_000.0  # $150M estimate

    async def _count_liquidity_pools(self) -> int:
        """Count active liquidity pools"""
        return 500  # Estimate

    async def _calculate_liquidity_growth(self) -> float:
        """Calculate liquidity growth rate"""
        return 0.08  # 8% growth estimate

    async def _estimate_staking_volume(self) -> float:
        """Estimate staking volume"""
        return 50_000_000.0  # $50M estimate

    async def _estimate_average_apr(self) -> float:
        """Estimate average APR across protocols"""
        return 0.12  # 12% APR estimate

    async def _count_new_nft_collections(self) -> int:
        """Count new NFT collections"""
        return 15  # Estimate

    async def _count_new_nfts_minted(self) -> int:
        """Count newly minted NFTs"""
        return 500  # Estimate

    async def _count_active_nft_creators(self) -> int:
        """Count active NFT creators"""
        return 150  # Estimate

    async def _analyze_floor_price_changes(self) -> Dict[str, float]:
        """Analyze floor price changes for major collections"""
        return {
            'algogems_featured': 0.05,   # 5% increase
            'rand_gallery_top': -0.02,  # 2% decrease
            'average_collection': 0.01   # 1% increase
        }

    async def _count_governance_participants(self) -> int:
        """Count governance participants"""
        return 75_000  # Estimate

    async def _get_committed_algo(self) -> float:
        """Get committed ALGO amount"""
        return 2_500_000_000.0  # 2.5B ALGO estimate

    async def _count_active_proposals(self) -> int:
        """Count active governance proposals"""
        return 3  # Estimate

    async def _count_recent_votes(self) -> int:
        """Count recent votes cast"""
        return 45_000  # Estimate

    async def _get_delegated_stake(self) -> float:
        """Get delegated stake amount"""
        return 500_000_000.0  # 500M ALGO estimate

    async def _estimate_protocol_growth(self, protocol_name: str, metric_type: str) -> float:
        """Estimate protocol growth rate"""
        # Simplified growth estimates
        growth_rates = {
            'tinyman': {'transactions': 0.20, 'volume': 0.15, 'users': 0.18},
            'algofi': {'transactions': 0.25, 'volume': 0.22, 'users': 0.20},
            'folks_finance': {'transactions': 0.30, 'volume': 0.28, 'users': 0.25},
            'pact': {'transactions': 0.15, 'volume': 0.12, 'users': 0.14}
        }

        return growth_rates.get(protocol_name, {}).get(metric_type, 0.10)

    async def _get_protocol_custom_metrics(self, protocol_name: str, app_ids: List[int]) -> Dict[str, float]:
        """Get protocol-specific custom metrics"""
        # Protocol-specific metrics would be calculated here
        if 'tinyman' in protocol_name.lower():
            return {'liquidity_pools': 150, 'swap_fee_revenue': 5000}
        elif 'algofi' in protocol_name.lower():
            return {'utilization_rate': 0.65, 'liquidations': 5}
        else:
            return {}

    def _calculate_defi_activity_score(self, defi_metrics: DeFiMetrics) -> float:
        """Calculate DeFi activity score"""
        # Score based on volume, transactions, and TVL
        volume_score = min(1.0, defi_metrics.dex_volume_24h / 1_000_000)  # Normalize to $1M
        transaction_score = min(1.0, defi_metrics.dex_trades_count / 10_000)  # Normalize to 10k trades
        tvl_score = min(1.0, defi_metrics.total_tvl_usd / 200_000_000)  # Normalize to $200M

        return (volume_score + transaction_score + tvl_score) / 3

    def _calculate_nft_activity_score(self, nft_activity: NFTActivity) -> float:
        """Calculate NFT activity score"""
        # Score based on sales volume and creation activity
        sales_score = min(1.0, nft_activity.daily_sales_volume / 100_000)  # Normalize to $100k
        creation_score = min(1.0, nft_activity.new_nfts_minted / 1000)  # Normalize to 1k NFTs

        return (sales_score + creation_score) / 2

    def _calculate_governance_activity_score(self, governance: GovernanceActivity) -> float:
        """Calculate governance activity score"""
        # Score based on participation and voting
        participation_score = min(1.0, governance.participation_rate / 0.1)  # Normalize to 10%
        voting_score = min(1.0, governance.voting_participation)

        return (participation_score + voting_score) / 2

    def _calculate_overall_activity_score(
        self, defi_score: float, nft_score: float, governance_score: float, sc_metrics: SmartContractMetrics
    ) -> float:
        """Calculate overall ecosystem activity score"""
        weights = self.config['network_monitoring']['dapp_weights']

        # Base score from individual components
        base_score = (
            defi_score * weights['defi_protocol_usage'] +
            nft_score * weights['nft_marketplace_activity'] +
            governance_score * weights['governance_activity']
        )

        # Smart contract activity component
        sc_score = min(1.0, sc_metrics.daily_app_calls / 50_000)  # Normalize to 50k calls
        total_score = base_score + sc_score * weights['smart_contract_activity']

        return min(1.0, total_score)

    def _determine_ecosystem_status(self, score: float) -> str:
        """Determine ecosystem activity status"""
        if score >= 0.8:
            return "very_active"
        elif score >= 0.6:
            return "active"
        elif score >= 0.4:
            return "moderate"
        elif score >= 0.2:
            return "low"
        else:
            return "minimal"

    def _analyze_activity_trend(
        self, defi_metrics: DeFiMetrics, nft_activity: NFTActivity, governance_activity: GovernanceActivity
    ) -> str:
        """Analyze overall activity trend"""
        # Simplified trend analysis based on growth metrics
        avg_growth = statistics.mean([
            defi_metrics.liquidity_growth,
            governance_activity.participation_rate * 0.1,  # Convert to growth-like metric
            0.1  # Placeholder for NFT growth
        ])

        if avg_growth > 0.15:
            return "strong_growth"
        elif avg_growth > 0.05:
            return "growth"
        elif avg_growth > -0.05:
            return "stable"
        else:
            return "declining"

    def _identify_growth_indicators(
        self, defi_metrics: DeFiMetrics, nft_activity: NFTActivity,
        governance_activity: GovernanceActivity, sc_metrics: SmartContractMetrics
    ) -> List[str]:
        """Identify positive growth indicators"""
        indicators = []

        if defi_metrics.total_tvl_usd > 100_000_000:
            indicators.append("Strong DeFi TVL ($100M+)")

        if defi_metrics.dex_volume_24h > 1_000_000:
            indicators.append("High DEX trading volume ($1M+ daily)")

        if governance_activity.participation_rate > 0.08:
            indicators.append("Strong governance participation (8%+ of supply)")

        if sc_metrics.daily_app_calls > 30_000:
            indicators.append("High smart contract activity (30k+ daily calls)")

        if nft_activity.daily_sales_count > 100:
            indicators.append("Active NFT marketplace (100+ daily sales)")

        return indicators

    def _generate_activity_recommendations(
        self, defi_metrics: DeFiMetrics, nft_activity: NFTActivity,
        governance_activity: GovernanceActivity, overall_score: float
    ) -> List[str]:
        """Generate recommendations for ecosystem improvement"""
        recommendations = []

        if overall_score < 0.5:
            recommendations.append("Focus on increasing overall ecosystem activity")

        if defi_metrics.total_tvl_usd < 50_000_000:
            recommendations.append("Encourage DeFi protocol development and liquidity provision")

        if governance_activity.participation_rate < 0.05:
            recommendations.append("Promote governance participation through education and incentives")

        if nft_activity.daily_sales_volume < 10_000:
            recommendations.append("Support NFT marketplace growth and creator tools")

        if not recommendations:
            recommendations.append("Ecosystem showing healthy activity levels")

        return recommendations

    # Default metrics for error cases
    def _default_sc_metrics(self) -> SmartContractMetrics:
        """Default smart contract metrics"""
        return SmartContractMetrics(
            total_app_calls=0,
            daily_app_calls=0,
            unique_apps_used=0,
            top_apps_by_calls=[],
            top_apps_by_users=[],
            new_applications=0,
            app_call_growth=0.0,
            user_adoption_rate=0.0
        )

    def _default_defi_metrics(self) -> DeFiMetrics:
        """Default DeFi metrics"""
        return DeFiMetrics(
            dex_volume_24h=0.0,
            dex_trades_count=0,
            swap_protocols=[],
            lending_volume_24h=0.0,
            borrows_count=0,
            supplies_count=0,
            lending_protocols=[],
            total_liquidity_pools=0,
            total_tvl_usd=0.0,
            liquidity_growth=0.0,
            farming_protocols=0,
            staking_volume=0.0,
            average_apr=0.0
        )

    def _default_nft_activity(self) -> NFTActivity:
        """Default NFT activity"""
        return NFTActivity(
            total_marketplaces=0,
            daily_sales_count=0,
            daily_sales_volume=0.0,
            new_collections=0,
            new_nfts_minted=0,
            creator_count=0,
            floor_price_changes={},
            volume_by_marketplace={}
        )

    def _default_governance_activity(self) -> GovernanceActivity:
        """Default governance activity"""
        return GovernanceActivity(
            total_participants=0,
            participation_rate=0.0,
            algo_committed=0.0,
            active_proposals=0,
            votes_cast=0,
            voting_participation=0.0,
            delegated_stake=0.0,
            delegation_rate=0.0
        )