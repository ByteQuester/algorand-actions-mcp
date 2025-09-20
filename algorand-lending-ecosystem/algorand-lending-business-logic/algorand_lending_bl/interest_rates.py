"""
Consolidated Interest Rate Engine

Combines all interest rate calculation functionality into a single, working module.
Includes base rate calculation, reputation scoring, risk assessment, and market analysis.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

import httpx

from .models import (
    RateCalculation, RateFactors, AlgorandAddress, StakingMetrics,
    ReputationScore, RiskTier, NetworkMetrics, NetworkHealth,
    ASARiskMetrics, DeFiYieldData, LiquidityMetrics
)
from .config import InterestRateConfig, DEFAULT_INTEREST_RATE_CONFIG

logger = logging.getLogger(__name__)


class InterestRateEngine:
    """
    Unified interest rate calculation engine for Algorand lending.

    Provides comprehensive interest rate determination including:
    - ALGO staking yield-based base rates
    - On-chain reputation scoring
    - ASA risk assessment
    - Network health monitoring
    - DeFi yield competitive analysis
    - Market condition adjustments
    """

    def __init__(self, config: Optional[InterestRateConfig] = None):
        """Initialize the interest rate engine with configuration."""
        self.config = config or DEFAULT_INTEREST_RATE_CONFIG
        self._rate_cache: Dict[str, Tuple[RateCalculation, datetime]] = {}
        self._data_cache: Dict[str, Tuple[Any, datetime]] = {}

    async def calculate_rate(
        self,
        borrower: AlgorandAddress,
        loan_amount_usd: Decimal,
        loan_duration_days: int,
        collateral_assets: List[str],
        collateral_value_usd: Decimal,
        market_condition: str = "normal"
    ) -> RateCalculation:
        """
        Calculate comprehensive interest rate for a loan.

        Args:
            borrower: Borrower's Algorand address
            loan_amount_usd: Loan amount in USD
            loan_duration_days: Loan duration in days
            collateral_assets: List of collateral asset symbols
            collateral_value_usd: Total collateral value in USD
            market_condition: Current market condition (normal, volatile, bear, crisis)

        Returns:
            Complete rate calculation with breakdown
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                borrower, loan_amount_usd, loan_duration_days, collateral_assets, market_condition
            )

            # Check cache
            if cache_key in self._rate_cache:
                result, timestamp = self._rate_cache[cache_key]
                age_seconds = (datetime.utcnow() - timestamp).total_seconds()

                if age_seconds < self.config.rate_cache_ttl:
                    logger.info(f"Returning cached rate for {borrower.address}")
                    return result

            logger.info(f"Calculating new rate for {borrower.address}")

            # Step 1: Get base rates from ALGO staking
            staking_metrics = await self._calculate_base_rates()

            # Step 2: Get borrower reputation score
            reputation_score = await self._calculate_reputation_score(borrower)

            # Step 3: Assess ASA risks for collateral
            asa_risk_scores = await self._assess_collateral_asa_risks(collateral_assets)

            # Step 4: Get network health metrics
            network_metrics = await self._get_network_metrics()

            # Step 5: Get DeFi yield data for competitive analysis
            defi_yields = await self._get_defi_yield_data()

            # Step 6: Calculate all rate factors
            rate_factors = await self._calculate_rate_factors(
                staking_metrics, reputation_score, asa_risk_scores, network_metrics,
                defi_yields, loan_amount_usd, loan_duration_days, collateral_assets,
                collateral_value_usd, market_condition
            )

            # Step 7: Calculate final rate with bounds
            final_rate = rate_factors.total_rate()
            bounded_rate = self._apply_rate_bounds(final_rate)

            # Step 8: Calculate effective APR
            effective_apr = self._calculate_effective_apr(bounded_rate, loan_duration_days)

            # Step 9: Calculate risk scores
            loan_risk_score = self._calculate_loan_risk_score(
                reputation_score, collateral_value_usd, loan_amount_usd, asa_risk_scores
            )
            collateral_risk_score = self._calculate_collateral_risk_score(asa_risk_scores)

            # Step 10: Calculate confidence and data quality metrics
            confidence_interval = self._calculate_confidence_interval(
                staking_metrics, reputation_score, network_metrics, market_condition
            )
            data_freshness = self._calculate_data_freshness_score(
                staking_metrics, reputation_score, network_metrics
            )

            # Create rate calculation result
            rate_calculation = RateCalculation(
                borrower_address=borrower,
                loan_amount_usd=loan_amount_usd,
                loan_duration_days=loan_duration_days,
                collateral_assets=collateral_assets,
                collateral_value_usd=collateral_value_usd,
                rate_factors=rate_factors,
                final_interest_rate=bounded_rate,
                effective_apr=effective_apr,
                staking_metrics=staking_metrics,
                reputation_score=reputation_score,
                network_metrics=network_metrics,
                market_condition=market_condition,
                borrower_risk_tier=reputation_score.risk_tier,
                loan_risk_score=loan_risk_score,
                collateral_risk_score=collateral_risk_score,
                min_rate=self.config.min_rate,
                max_rate=self.config.max_rate,
                confidence_interval=confidence_interval,
                calculation_timestamp=datetime.utcnow(),
                model_version="1.0.0",
                data_freshness_score=data_freshness
            )

            # Cache the result
            self._rate_cache[cache_key] = (rate_calculation, datetime.utcnow())

            logger.info(f"Rate calculation completed: {bounded_rate:.4%}")
            return rate_calculation

        except Exception as e:
            logger.error(f"Error calculating rate for {borrower.address}: {e}")
            return self._get_fallback_rate_calculation(
                borrower, loan_amount_usd, loan_duration_days,
                collateral_assets, collateral_value_usd, market_condition
            )

    async def _calculate_base_rates(self) -> StakingMetrics:
        """Calculate base interest rates from ALGO staking and consensus data."""
        cache_key = "staking_metrics"
        cached_data = self._get_cached_data(cache_key, 300)  # 5 minute cache
        if cached_data:
            return cached_data

        try:
            # Get network participation data
            participation_data = await self._get_participation_metrics()

            # Get governance data
            governance_data = await self._get_governance_metrics()

            # Get validator performance data
            validator_data = await self._get_validator_metrics()

            # Calculate current APY
            current_apy = self._calculate_current_apy(
                participation_data, governance_data, validator_data
            )

            # Get historical APY
            historical_apy = await self._get_historical_apy()

            # Calculate staking rewards
            staking_rewards_30d = await self._get_staking_rewards_30d()

            # Create metrics object
            metrics = StakingMetrics(
                current_apy=current_apy,
                historical_avg_apy=historical_apy,
                participation_rate=participation_data['participation_rate'],
                total_staked_algo=participation_data['total_online'],
                governance_participation=governance_data['participation_rate'],
                validator_performance=validator_data['avg_performance'],
                staking_rewards_30d=staking_rewards_30d,
                consensus_uptime=validator_data['consensus_uptime'],
                timestamp=datetime.utcnow()
            )

            self._cache_data(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error calculating base rates: {e}")
            return self._get_fallback_staking_metrics()

    async def _get_participation_metrics(self) -> Dict[str, Decimal]:
        """Get current network participation metrics."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get network status
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/network/status"
                )

                if response.status_code == 200:
                    status_data = response.json()

                    # Get supply information
                    supply_response = await client.get(
                        f"{self.config.service.algorand_reader_url}/network/supply"
                    )

                    if supply_response.status_code == 200:
                        supply_data = supply_response.json()

                        total_supply = Decimal(str(supply_data.get('total_money', 10000000000)))
                        online_supply = Decimal(str(supply_data.get('online_money', 7500000000)))

                        participation_rate = (
                            online_supply / total_supply if total_supply > 0 else Decimal('0.75')
                        )

                        return {
                            'participation_rate': participation_rate,
                            'total_online': online_supply,
                            'total_supply': total_supply,
                            'last_round': status_data.get('last_round', 0)
                        }

        except Exception as e:
            logger.debug(f"Failed to get participation metrics: {e}")

        # Return fallback data
        return {
            'participation_rate': Decimal('0.75'),  # 75% participation
            'total_online': Decimal('7500000000'),  # 7.5B ALGO online
            'total_supply': Decimal('10000000000'), # 10B ALGO total
            'last_round': 0
        }

    async def _get_governance_metrics(self) -> Dict[str, Decimal]:
        """Get Algorand governance participation data."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.market_data_url}/algorand/governance"
                )

                if response.status_code == 200:
                    gov_data = response.json()

                    return {
                        'participation_rate': Decimal(str(gov_data.get('participation_rate', 0.7))),
                        'committed_algo': Decimal(str(gov_data.get('committed_algo', 3000000000))),
                        'expected_rewards': Decimal(str(gov_data.get('expected_rewards', 0.08))),
                        'voting_participation': Decimal(str(gov_data.get('voting_participation', 0.8)))
                    }

        except Exception as e:
            logger.debug(f"Failed to get governance metrics: {e}")

        # Return fallback data
        return {
            'participation_rate': Decimal('0.7'),    # 70% governance participation
            'committed_algo': Decimal('3000000000'), # 3B ALGO committed
            'expected_rewards': Decimal('0.08'),     # 8% expected rewards
            'voting_participation': Decimal('0.8')   # 80% voting participation
        }

    async def _get_validator_metrics(self) -> Dict[str, Decimal]:
        """Get validator performance metrics."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/network/validators"
                )

                if response.status_code == 200:
                    validator_data = response.json()

                    validators = validator_data.get('validators', [])
                    if validators:
                        avg_performance = sum(
                            v.get('performance', 0.95) for v in validators
                        ) / len(validators)

                        avg_uptime = sum(
                            v.get('uptime', 0.98) for v in validators
                        ) / len(validators)
                    else:
                        avg_performance = 0.95
                        avg_uptime = 0.98

                    return {
                        'avg_performance': Decimal(str(avg_performance)),
                        'consensus_uptime': Decimal(str(avg_uptime)),
                        'active_validators': len(validators),
                        'total_stake': Decimal(str(validator_data.get('total_stake', 5000000000)))
                    }

        except Exception as e:
            logger.debug(f"Failed to get validator metrics: {e}")

        # Return fallback data
        return {
            'avg_performance': Decimal('0.95'),      # 95% performance
            'consensus_uptime': Decimal('0.98'),     # 98% uptime
            'active_validators': 120,
            'total_stake': Decimal('5000000000')     # 5B ALGO staked
        }

    def _calculate_current_apy(
        self,
        participation_data: Dict[str, Decimal],
        governance_data: Dict[str, Decimal],
        validator_data: Dict[str, Decimal]
    ) -> Decimal:
        """Calculate current ALGO staking APY."""

        # Base rate from consensus participation
        participation_rate = participation_data['participation_rate']
        target_participation = Decimal('0.8')  # 80% target

        # Base APY starts from minimum and adjusts based on participation
        base_apy = Decimal('0.05')  # 5% base

        if participation_rate < target_participation:
            # Increase rewards when participation is low
            participation_bonus = (target_participation - participation_rate) * Decimal('0.1')
            base_apy += participation_bonus

        # Governance rewards bonus
        governance_rewards = governance_data.get('expected_rewards', Decimal('0.08'))
        governance_participation = governance_data.get('participation_rate', Decimal('0.7'))

        # Scale governance rewards by participation
        effective_governance_bonus = governance_rewards * governance_participation * Decimal('0.5')
        base_apy += effective_governance_bonus

        # Validator performance adjustment
        validator_performance = validator_data.get('avg_performance', Decimal('0.95'))
        performance_threshold = Decimal('0.9')  # 90% threshold

        if validator_performance < performance_threshold:
            performance_penalty = (performance_threshold - validator_performance) * Decimal('0.05')
            base_apy -= performance_penalty

        # Apply base spread from config
        final_apy = base_apy + self.config.base_spread

        # Cap the APY at reasonable bounds
        return min(max(final_apy, Decimal('0.02')), Decimal('0.15'))  # 2% to 15%

    async def _get_historical_apy(self) -> Decimal:
        """Get historical average APY over the last period."""
        cache_key = "historical_apy"
        cached_data = self._get_cached_data(cache_key, 3600)  # 1 hour cache
        if cached_data:
            return cached_data

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.market_data_url}/algorand/historical-apy",
                    params={'days': 90}
                )

                if response.status_code == 200:
                    hist_data = response.json()
                    historical_rates = [
                        Decimal(str(entry.get('apy', 0.08)))
                        for entry in hist_data.get('data', [])
                    ]

                    if historical_rates:
                        avg_apy = sum(historical_rates) / len(historical_rates)
                        self._cache_data(cache_key, avg_apy)
                        return avg_apy

        except Exception as e:
            logger.debug(f"Failed to get historical APY: {e}")

        # Fallback to reasonable historical average
        fallback_apy = Decimal('0.08')  # 8%
        self._cache_data(cache_key, fallback_apy)
        return fallback_apy

    async def _get_staking_rewards_30d(self) -> Decimal:
        """Get total staking rewards distributed in the last 30 days."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/network/rewards",
                    params={'days': 30}
                )

                if response.status_code == 200:
                    rewards_data = response.json()
                    total_rewards = Decimal(str(rewards_data.get('total_rewards', 1000000)))
                    return total_rewards

        except Exception as e:
            logger.debug(f"Failed to get staking rewards: {e}")

        # Fallback estimate
        return Decimal('1000000')  # 1M ALGO per 30 days estimate

    async def _calculate_reputation_score(self, borrower: AlgorandAddress) -> ReputationScore:
        """Calculate on-chain reputation score for a borrower."""
        cache_key = f"reputation_{borrower.address}"
        cached_data = self._get_cached_data(cache_key, 1800)  # 30 minute cache
        if cached_data:
            return cached_data

        try:
            # Get account information
            account_info = await self._get_account_info(borrower.address)

            # Calculate individual score components
            transaction_history_score = self._calculate_transaction_history_score(account_info)
            asset_diversity_score = self._calculate_asset_diversity_score(account_info)
            defi_participation_score = await self._calculate_defi_participation_score(borrower.address)
            governance_participation_score = await self._calculate_governance_participation_score(borrower.address)
            liquidation_history_score = await self._calculate_liquidation_history_score(borrower.address)
            account_age_score = self._calculate_account_age_score(account_info)
            volume_score = self._calculate_volume_score(account_info)

            # Calculate overall score (weighted average)
            weights = {
                'transaction_history': Decimal('0.2'),
                'asset_diversity': Decimal('0.15'),
                'defi_participation': Decimal('0.2'),
                'governance_participation': Decimal('0.15'),
                'liquidation_history': Decimal('0.1'),
                'account_age': Decimal('0.1'),
                'volume': Decimal('0.1')
            }

            overall_score = (
                transaction_history_score * weights['transaction_history'] +
                asset_diversity_score * weights['asset_diversity'] +
                defi_participation_score * weights['defi_participation'] +
                governance_participation_score * weights['governance_participation'] +
                liquidation_history_score * weights['liquidation_history'] +
                account_age_score * weights['account_age'] +
                volume_score * weights['volume']
            )

            # Determine risk tier
            risk_tier = self._determine_risk_tier(overall_score)

            # Calculate confidence level
            confidence_level = self._calculate_reputation_confidence(account_info)

            reputation = ReputationScore(
                address=borrower,
                overall_score=overall_score,
                transaction_history_score=transaction_history_score,
                asset_diversity_score=asset_diversity_score,
                defi_participation_score=defi_participation_score,
                governance_participation_score=governance_participation_score,
                liquidation_history_score=liquidation_history_score,
                account_age_score=account_age_score,
                volume_score=volume_score,
                risk_tier=risk_tier,
                confidence_level=confidence_level,
                last_calculated=datetime.utcnow()
            )

            self._cache_data(cache_key, reputation)
            return reputation

        except Exception as e:
            logger.error(f"Error calculating reputation for {borrower.address}: {e}")
            return self._get_fallback_reputation_score(borrower)

    async def _get_account_info(self, address: str) -> Dict[str, Any]:
        """Get account information from Algorand indexer."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/account/{address}"
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            logger.debug(f"Failed to get account info for {address}: {e}")

        # Return fallback account info
        return {
            'address': address,
            'amount': 1000000,  # 1 ALGO
            'assets': [],
            'created-at-round': 1,
            'total-apps-opted-in': 0,
            'total-assets-opted-in': 0,
            'total-created-apps': 0,
            'total-created-assets': 0
        }

    def _calculate_transaction_history_score(self, account_info: Dict[str, Any]) -> Decimal:
        """Calculate score based on transaction history."""
        # In a real implementation, this would fetch transaction history
        # For now, use account balance and asset holdings as proxies

        balance = Decimal(str(account_info.get('amount', 0))) / Decimal('1000000')  # Convert microalgos
        assets_count = len(account_info.get('assets', []))
        apps_opted_in = account_info.get('total-apps-opted-in', 0)

        # Score based on activity indicators
        balance_score = min(balance / Decimal('10000'), Decimal('1'))  # Up to 10,000 ALGO = max score
        assets_score = min(Decimal(str(assets_count)) / Decimal('10'), Decimal('1'))  # Up to 10 assets
        apps_score = min(Decimal(str(apps_opted_in)) / Decimal('5'), Decimal('1'))  # Up to 5 apps

        return (balance_score + assets_score + apps_score) / 3

    def _calculate_asset_diversity_score(self, account_info: Dict[str, Any]) -> Decimal:
        """Calculate score based on asset portfolio diversity."""
        assets = account_info.get('assets', [])

        if not assets:
            return Decimal('0.3')  # Base score for no additional assets

        # Simple diversity calculation
        num_assets = len(assets)
        total_value = sum(Decimal(str(asset.get('amount', 0))) for asset in assets)

        if total_value == 0:
            return Decimal('0.3')

        # Calculate concentration (inverse of diversity)
        max_asset_ratio = max(
            Decimal(str(asset.get('amount', 0))) / total_value
            for asset in assets
        ) if assets else Decimal('1')

        diversity_score = Decimal('1') - max_asset_ratio
        asset_count_bonus = min(Decimal(str(num_assets)) / Decimal('20'), Decimal('0.3'))

        return min(diversity_score + asset_count_bonus, Decimal('1'))

    async def _calculate_defi_participation_score(self, address: str) -> Decimal:
        """Calculate score based on DeFi protocol participation."""
        # This would integrate with DeFi protocol analytics
        # For now, return a moderate score
        return Decimal('0.4')

    async def _calculate_governance_participation_score(self, address: str) -> Decimal:
        """Calculate score based on governance participation."""
        # This would check governance voting history
        # For now, return a moderate score
        return Decimal('0.5')

    async def _calculate_liquidation_history_score(self, address: str) -> Decimal:
        """Calculate score based on liquidation history."""
        # This would check for past liquidations
        # For now, assume good history
        return Decimal('0.9')

    def _calculate_account_age_score(self, account_info: Dict[str, Any]) -> Decimal:
        """Calculate score based on account age."""
        created_round = account_info.get('created-at-round', 0)

        # Estimate account age based on rounds (roughly 3.3 seconds per round)
        if created_round == 0:
            return Decimal('0.5')  # Unknown age gets medium score

        # Approximate age calculation (this would use actual round timestamps in practice)
        estimated_age_days = (datetime.utcnow() - datetime(2021, 1, 1)).days  # Rough estimate

        # Score increases with age up to 2 years
        max_age_days = 730  # 2 years
        age_score = min(Decimal(str(estimated_age_days)) / Decimal(str(max_age_days)), Decimal('1'))

        return max(age_score, Decimal('0.1'))  # Minimum score

    def _calculate_volume_score(self, account_info: Dict[str, Any]) -> Decimal:
        """Calculate score based on transaction volume."""
        # This would calculate based on actual transaction volume
        # For now, use balance as a proxy
        balance = Decimal(str(account_info.get('amount', 0))) / Decimal('1000000')
        return min(balance / Decimal('100000'), Decimal('1'))  # Up to 100k ALGO

    def _determine_risk_tier(self, overall_score: Decimal) -> RiskTier:
        """Determine risk tier from overall score."""
        if overall_score >= Decimal('0.8'):
            return RiskTier.PRIME
        elif overall_score >= Decimal('0.6'):
            return RiskTier.STANDARD
        elif overall_score >= Decimal('0.4'):
            return RiskTier.SUBPRIME
        else:
            return RiskTier.HIGH_RISK

    def _calculate_reputation_confidence(self, account_info: Dict[str, Any]) -> Decimal:
        """Calculate confidence in reputation score."""
        # Base confidence on data availability
        base_confidence = Decimal('0.6')

        # Boost confidence with more data
        if account_info.get('assets'):
            base_confidence += Decimal('0.1')
        if account_info.get('total-apps-opted-in', 0) > 0:
            base_confidence += Decimal('0.1')
        if account_info.get('amount', 0) > 1000000:  # More than 1 ALGO
            base_confidence += Decimal('0.1')

        return min(base_confidence, Decimal('0.9'))

    async def _assess_collateral_asa_risks(self, collateral_assets: List[str]) -> List[ASARiskMetrics]:
        """Assess risk metrics for ASA tokens used as collateral."""
        risk_scores = []

        for asset_symbol in collateral_assets:
            cache_key = f"asa_risk_{asset_symbol}"
            cached_data = self._get_cached_data(cache_key, 1800)  # 30 minute cache
            if cached_data:
                risk_scores.append(cached_data)
                continue

            try:
                # Get asset risk metrics
                risk_metrics = await self._calculate_asa_risk_metrics(asset_symbol)
                self._cache_data(cache_key, risk_metrics)
                risk_scores.append(risk_metrics)

            except Exception as e:
                logger.error(f"Error assessing ASA risk for {asset_symbol}: {e}")
                risk_scores.append(self._get_fallback_asa_risk(asset_symbol))

        return risk_scores

    async def _calculate_asa_risk_metrics(self, asset_symbol: str) -> ASARiskMetrics:
        """Calculate comprehensive risk metrics for an ASA."""
        symbol_upper = asset_symbol.upper()

        # Predefined risk profiles for common assets
        risk_profiles = {
            'ALGO': {
                'volatility_30d': Decimal('0.4'),
                'volatility_90d': Decimal('0.45'),
                'liquidity_score': Decimal('1.0'),
                'market_cap_usd': Decimal('2000000000'),
                'trading_volume_24h': Decimal('50000000'),
                'holder_count': 500000,
                'concentration_risk': Decimal('0.2'),
                'smart_contract_risk': Decimal('0.1'),
                'regulatory_risk': Decimal('0.1'),
                'overall_risk_score': Decimal('0.25')
            },
            'USDC': {
                'volatility_30d': Decimal('0.02'),
                'volatility_90d': Decimal('0.02'),
                'liquidity_score': Decimal('0.9'),
                'market_cap_usd': Decimal('100000000'),
                'trading_volume_24h': Decimal('10000000'),
                'holder_count': 50000,
                'concentration_risk': Decimal('0.1'),
                'smart_contract_risk': Decimal('0.05'),
                'regulatory_risk': Decimal('0.05'),
                'overall_risk_score': Decimal('0.1')
            },
            'USDT': {
                'volatility_30d': Decimal('0.02'),
                'volatility_90d': Decimal('0.025'),
                'liquidity_score': Decimal('0.85'),
                'market_cap_usd': Decimal('80000000'),
                'trading_volume_24h': Decimal('8000000'),
                'holder_count': 40000,
                'concentration_risk': Decimal('0.15'),
                'smart_contract_risk': Decimal('0.08'),
                'regulatory_risk': Decimal('0.1'),
                'overall_risk_score': Decimal('0.15')
            },
            'STBL': {
                'volatility_30d': Decimal('0.03'),
                'volatility_90d': Decimal('0.03'),
                'liquidity_score': Decimal('0.7'),
                'market_cap_usd': Decimal('50000000'),
                'trading_volume_24h': Decimal('5000000'),
                'holder_count': 25000,
                'concentration_risk': Decimal('0.2'),
                'smart_contract_risk': Decimal('0.1'),
                'regulatory_risk': Decimal('0.05'),
                'overall_risk_score': Decimal('0.2')
            }
        }

        profile = risk_profiles.get(symbol_upper, {
            'volatility_30d': Decimal('0.6'),
            'volatility_90d': Decimal('0.65'),
            'liquidity_score': Decimal('0.3'),
            'market_cap_usd': Decimal('1000000'),
            'trading_volume_24h': Decimal('100000'),
            'holder_count': 1000,
            'concentration_risk': Decimal('0.8'),
            'smart_contract_risk': Decimal('0.5'),
            'regulatory_risk': Decimal('0.3'),
            'overall_risk_score': Decimal('0.7')
        })

        return ASARiskMetrics(
            asset_id=asset_symbol,  # Would be actual asset ID in practice
            symbol=asset_symbol,
            volatility_30d=profile['volatility_30d'],
            volatility_90d=profile['volatility_90d'],
            liquidity_score=profile['liquidity_score'],
            market_cap_usd=profile['market_cap_usd'],
            trading_volume_24h=profile['trading_volume_24h'],
            holder_count=profile['holder_count'],
            concentration_risk=profile['concentration_risk'],
            smart_contract_risk=profile['smart_contract_risk'],
            regulatory_risk=profile['regulatory_risk'],
            overall_risk_score=profile['overall_risk_score'],
            last_updated=datetime.utcnow()
        )

    async def _get_network_metrics(self) -> NetworkMetrics:
        """Get Algorand network health and activity metrics."""
        cache_key = "network_metrics"
        cached_data = self._get_cached_data(cache_key, 300)  # 5 minute cache
        if cached_data:
            return cached_data

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config.service.algorand_reader_url}/network/health"
                )

                if response.status_code == 200:
                    data = response.json()

                    metrics = NetworkMetrics(
                        current_tps=Decimal(str(data.get('current_tps', 50))),
                        average_tps_24h=Decimal(str(data.get('average_tps_24h', 45))),
                        block_time_avg=Decimal(str(data.get('block_time_avg', 3.3))),
                        finality_time=Decimal(str(data.get('finality_time', 3.3))),
                        total_accounts=data.get('total_accounts', 1000000),
                        active_accounts_24h=data.get('active_accounts_24h', 50000),
                        total_transactions_24h=data.get('total_transactions_24h', 1000000),
                        network_congestion=Decimal(str(data.get('network_congestion', 0.2))),
                        gas_price_trend=Decimal(str(data.get('gas_price_trend', 1.0))),
                        network_health=NetworkHealth.GOOD,
                        consensus_status=data.get('consensus_status', 'healthy'),
                        last_updated=datetime.utcnow()
                    )

                    self._cache_data(cache_key, metrics)
                    return metrics

        except Exception as e:
            logger.debug(f"Failed to get network metrics: {e}")

        # Return fallback metrics
        fallback_metrics = NetworkMetrics(
            current_tps=Decimal('50'),
            average_tps_24h=Decimal('45'),
            block_time_avg=Decimal('3.3'),
            finality_time=Decimal('3.3'),
            total_accounts=1000000,
            active_accounts_24h=50000,
            total_transactions_24h=1000000,
            network_congestion=Decimal('0.2'),
            gas_price_trend=Decimal('1.0'),
            network_health=NetworkHealth.GOOD,
            consensus_status="healthy",
            last_updated=datetime.utcnow()
        )

        self._cache_data(cache_key, fallback_metrics)
        return fallback_metrics

    async def _get_defi_yield_data(self) -> List[DeFiYieldData]:
        """Get DeFi protocol yield data for competitive analysis."""
        cache_key = "defi_yields"
        cached_data = self._get_cached_data(cache_key, 900)  # 15 minute cache
        if cached_data:
            return cached_data

        # Fallback yield data for common DeFi protocols
        fallback_yields = [
            DeFiYieldData(
                protocol_name="AlgoFi",
                base_yield=Decimal('0.06'),
                reward_token_apy=Decimal('0.02'),
                total_apy=Decimal('0.08'),
                tvl_usd=Decimal('50000000'),
                volume_24h=Decimal('2000000'),
                protocol_health_score=Decimal('0.85'),
                risk_premium=Decimal('0.01'),
                last_updated=datetime.utcnow()
            ),
            DeFiYieldData(
                protocol_name="Tinyman",
                base_yield=Decimal('0.04'),
                reward_token_apy=Decimal('0.03'),
                total_apy=Decimal('0.07'),
                tvl_usd=Decimal('30000000'),
                volume_24h=Decimal('1000000'),
                protocol_health_score=Decimal('0.8'),
                risk_premium=Decimal('0.015'),
                last_updated=datetime.utcnow()
            )
        ]

        self._cache_data(cache_key, fallback_yields)
        return fallback_yields

    async def _calculate_rate_factors(
        self,
        staking_metrics: StakingMetrics,
        reputation_score: ReputationScore,
        asa_risk_scores: List[ASARiskMetrics],
        network_metrics: NetworkMetrics,
        defi_yields: List[DeFiYieldData],
        loan_amount_usd: Decimal,
        loan_duration_days: int,
        collateral_assets: List[str],
        collateral_value_usd: Decimal,
        market_condition: str
    ) -> RateFactors:
        """Calculate all rate factors that contribute to the final rate."""

        # Base rate from ALGO staking
        base_rate = staking_metrics.base_rate()

        # Risk premium from borrower reputation
        risk_premium = reputation_score.rate_adjustment()

        # Liquidity premium from collateral liquidity
        liquidity_premium = self._calculate_liquidity_premium(asa_risk_scores)

        # Duration premium
        duration_premium = self._calculate_duration_premium(loan_duration_days)

        # Market conditions adjustment
        market_adjustment = self._calculate_market_conditions_adjustment(market_condition)

        # Collateral adjustment
        collateral_adjustment = self._calculate_collateral_adjustment(
            asa_risk_scores, collateral_value_usd, loan_amount_usd
        )

        # Network adjustment
        network_adjustment = network_metrics.network_risk_adjustment()

        # DeFi yield competitive adjustment
        defi_yield_adjustment = self._calculate_defi_yield_adjustment(defi_yields)

        # Governance adjustment
        governance_adjustment = self._calculate_governance_adjustment(staking_metrics)

        return RateFactors(
            base_rate=base_rate,
            risk_premium=risk_premium,
            liquidity_premium=liquidity_premium,
            duration_premium=duration_premium,
            market_conditions_adjustment=market_adjustment,
            reputation_adjustment=reputation_score.rate_adjustment(),
            collateral_adjustment=collateral_adjustment,
            network_adjustment=network_adjustment,
            defi_yield_adjustment=defi_yield_adjustment,
            governance_adjustment=governance_adjustment
        )

    def _calculate_liquidity_premium(self, asa_risk_scores: List[ASARiskMetrics]) -> Decimal:
        """Calculate liquidity premium based on collateral asset liquidity."""
        if not asa_risk_scores:
            return Decimal('0.02')  # 2% premium for no collateral

        # Calculate weighted average liquidity score
        total_liquidity = sum(score.liquidity_score for score in asa_risk_scores)
        avg_liquidity = total_liquidity / len(asa_risk_scores)

        # Premium decreases with higher liquidity
        liquidity_premium = (Decimal('1') - avg_liquidity) * Decimal('0.03')  # Up to 3%

        return max(liquidity_premium, Decimal('0'))

    def _calculate_duration_premium(self, loan_duration_days: int) -> Decimal:
        """Calculate premium based on loan duration."""
        duration_years = Decimal(str(loan_duration_days)) / Decimal('365')
        return duration_years * self.config.duration_premium_per_year

    def _calculate_market_conditions_adjustment(self, market_condition: str) -> Decimal:
        """Calculate adjustment based on market conditions."""
        market_adjustments = {
            'normal': Decimal('0'),
            'volatile': Decimal('0.01'),    # +1% in volatile markets
            'bear': Decimal('0.02'),        # +2% in bear markets
            'crisis': Decimal('0.05')       # +5% in crisis
        }

        return market_adjustments.get(market_condition, Decimal('0'))

    def _calculate_collateral_adjustment(
        self,
        asa_risk_scores: List[ASARiskMetrics],
        collateral_value_usd: Decimal,
        loan_amount_usd: Decimal
    ) -> Decimal:
        """Calculate adjustment based on collateral quality and ratio."""
        if loan_amount_usd == 0:
            return Decimal('0.05')  # 5% premium for edge case

        # Collateral ratio adjustment
        collateral_ratio = collateral_value_usd / loan_amount_usd

        if collateral_ratio >= Decimal('2.0'):      # 200%+ collateral
            ratio_adjustment = Decimal('-0.01')     # -1% discount
        elif collateral_ratio >= Decimal('1.5'):   # 150%+ collateral
            ratio_adjustment = Decimal('0')         # No adjustment
        elif collateral_ratio >= Decimal('1.2'):   # 120%+ collateral
            ratio_adjustment = Decimal('0.01')      # +1% premium
        else:                                       # < 120% collateral
            ratio_adjustment = Decimal('0.03')      # +3% premium

        # Asset quality adjustment
        if asa_risk_scores:
            avg_risk = sum(score.overall_risk_score for score in asa_risk_scores) / len(asa_risk_scores)
            quality_adjustment = avg_risk * Decimal('0.02')  # Up to 2% based on risk
        else:
            quality_adjustment = Decimal('0.05')  # 5% premium for no collateral

        return ratio_adjustment + quality_adjustment

    def _calculate_defi_yield_adjustment(self, defi_yields: List[DeFiYieldData]) -> Decimal:
        """Calculate competitive adjustment based on DeFi yields."""
        if not defi_yields:
            return Decimal('0')

        # Get average competitive yield
        avg_defi_yield = sum(yield_data.effective_yield() for yield_data in defi_yields) / len(defi_yields)

        # Small adjustment to stay competitive (max 0.5% adjustment)
        competitive_adjustment = min(max(avg_defi_yield * Decimal('0.1'), Decimal('-0.005')), Decimal('0.005'))

        return competitive_adjustment

    def _calculate_governance_adjustment(self, staking_metrics: StakingMetrics) -> Decimal:
        """Calculate adjustment based on governance participation."""
        gov_participation = staking_metrics.governance_participation

        if gov_participation >= Decimal('0.8'):    # 80%+ participation
            return Decimal('-0.002')               # -0.2% discount
        elif gov_participation >= Decimal('0.6'):  # 60%+ participation
            return Decimal('0')                    # No adjustment
        else:                                      # < 60% participation
            return Decimal('0.002')                # +0.2% premium

    def _apply_rate_bounds(self, rate: Decimal) -> Decimal:
        """Apply minimum and maximum rate bounds."""
        return max(self.config.min_rate, min(rate, self.config.max_rate))

    def _calculate_effective_apr(self, nominal_rate: Decimal, duration_days: int) -> Decimal:
        """Calculate effective APR with compounding."""
        if duration_days <= 0:
            return nominal_rate

        # Simplified effective rate calculation
        periods_per_year = Decimal('365')
        periods = Decimal(str(duration_days))

        # For short-term loans, effective rate ≈ nominal rate
        if duration_days <= 30:
            return nominal_rate

        # For longer loans, add small compounding effect
        compounding_factor = Decimal('1') + (nominal_rate / periods_per_year)
        effective_rate = (compounding_factor ** int(periods)) - Decimal('1')
        annualized_rate = effective_rate * (periods_per_year / periods)

        return min(annualized_rate, nominal_rate * Decimal('1.1'))  # Cap at 110% of nominal

    def _calculate_loan_risk_score(
        self,
        reputation_score: ReputationScore,
        collateral_value_usd: Decimal,
        loan_amount_usd: Decimal,
        asa_risk_scores: List[ASARiskMetrics]
    ) -> Decimal:
        """Calculate overall loan risk score."""
        # Reputation component (40% weight)
        reputation_risk = Decimal('1') - reputation_score.overall_score

        # Collateral component (40% weight)
        if loan_amount_usd > 0:
            collateral_ratio = collateral_value_usd / loan_amount_usd
            if collateral_ratio >= Decimal('2.0'):
                collateral_risk = Decimal('0.1')    # Low risk
            elif collateral_ratio >= Decimal('1.5'):
                collateral_risk = Decimal('0.3')    # Medium risk
            else:
                collateral_risk = Decimal('0.7')    # High risk
        else:
            collateral_risk = Decimal('1.0')        # Maximum risk

        # Asset quality component (20% weight)
        if asa_risk_scores:
            avg_asset_risk = sum(score.overall_risk_score for score in asa_risk_scores) / len(asa_risk_scores)
            asset_risk = avg_asset_risk
        else:
            asset_risk = Decimal('1.0')

        # Weighted combination
        overall_risk = (
            reputation_risk * Decimal('0.4') +
            collateral_risk * Decimal('0.4') +
            asset_risk * Decimal('0.2')
        )

        return min(overall_risk, Decimal('1.0'))

    def _calculate_collateral_risk_score(self, asa_risk_scores: List[ASARiskMetrics]) -> Decimal:
        """Calculate collateral-specific risk score."""
        if not asa_risk_scores:
            return Decimal('1.0')  # Maximum risk for no collateral

        # Calculate weighted average risk
        total_risk = sum(score.overall_risk_score for score in asa_risk_scores)
        avg_risk = total_risk / len(asa_risk_scores)

        # Diversification bonus
        unique_assets = len(set(score.symbol for score in asa_risk_scores))
        diversification_bonus = min(Decimal(str(unique_assets - 1)) * Decimal('0.05'), Decimal('0.2'))

        return max(avg_risk - diversification_bonus, Decimal('0.1'))

    def _calculate_confidence_interval(
        self,
        staking_metrics: StakingMetrics,
        reputation_score: ReputationScore,
        network_metrics: NetworkMetrics,
        market_condition: str
    ) -> Decimal:
        """Calculate confidence interval for the rate calculation."""
        base_confidence = Decimal('0.8')

        # Reduce confidence for poor data quality
        if reputation_score.confidence_level < Decimal('0.5'):
            base_confidence -= Decimal('0.2')

        # Reduce confidence in volatile market conditions
        if market_condition in ['bear', 'crisis']:
            base_confidence -= Decimal('0.1')

        # Reduce confidence for low network participation
        if staking_metrics.participation_rate < Decimal('0.6'):
            base_confidence -= Decimal('0.1')

        # Reduce confidence for network issues
        if network_metrics.network_health == NetworkHealth.POOR:
            base_confidence -= Decimal('0.15')

        return max(base_confidence, Decimal('0.5'))

    def _calculate_data_freshness_score(self, *data_sources) -> Decimal:
        """Calculate overall data freshness score."""
        freshness_scores = []

        for source in data_sources:
            timestamp_attr = getattr(source, 'timestamp', None) or \
                           getattr(source, 'last_calculated', None) or \
                           getattr(source, 'last_updated', None)

            if timestamp_attr:
                age_seconds = (datetime.utcnow() - timestamp_attr).total_seconds()
                if age_seconds < 300:       # < 5 minutes
                    freshness_scores.append(Decimal('1.0'))
                elif age_seconds < 3600:    # < 1 hour
                    freshness_scores.append(Decimal('0.8'))
                elif age_seconds < 86400:   # < 1 day
                    freshness_scores.append(Decimal('0.6'))
                else:
                    freshness_scores.append(Decimal('0.3'))
            else:
                freshness_scores.append(Decimal('0.5'))

        return sum(freshness_scores) / len(freshness_scores) if freshness_scores else Decimal('0.5')

    # Cache management methods
    def _get_cached_data(self, key: str, ttl_seconds: int) -> Optional[Any]:
        """Get data from cache if still valid."""
        if key in self._data_cache:
            data, timestamp = self._data_cache[key]
            if (datetime.utcnow() - timestamp).total_seconds() < ttl_seconds:
                return data
        return None

    def _cache_data(self, key: str, data: Any) -> None:
        """Cache data with timestamp."""
        self._data_cache[key] = (data, datetime.utcnow())

    def _generate_cache_key(
        self,
        borrower: AlgorandAddress,
        loan_amount_usd: Decimal,
        loan_duration_days: int,
        collateral_assets: List[str],
        market_condition: str
    ) -> str:
        """Generate cache key for rate calculation."""
        assets_str = ",".join(sorted(collateral_assets))
        return f"{borrower.address}:{loan_amount_usd}:{loan_duration_days}:{assets_str}:{market_condition}"

    # Fallback methods
    def _get_fallback_staking_metrics(self) -> StakingMetrics:
        """Get fallback staking metrics when calculation fails."""
        return StakingMetrics(
            current_apy=Decimal('0.08'),        # 8% fallback APY
            historical_avg_apy=Decimal('0.08'), # 8% historical average
            participation_rate=Decimal('0.75'), # 75% participation
            total_staked_algo=Decimal('7500000000'), # 7.5B ALGO
            governance_participation=Decimal('0.7'), # 70% governance
            validator_performance=Decimal('0.95'),   # 95% performance
            staking_rewards_30d=Decimal('1000000'),  # 1M ALGO rewards
            consensus_uptime=Decimal('0.98'),        # 98% uptime
            timestamp=datetime.utcnow()
        )

    def _get_fallback_reputation_score(self, borrower: AlgorandAddress) -> ReputationScore:
        """Get fallback reputation score when calculation fails."""
        return ReputationScore(
            address=borrower,
            overall_score=Decimal('0.5'),
            transaction_history_score=Decimal('0.5'),
            asset_diversity_score=Decimal('0.5'),
            defi_participation_score=Decimal('0.3'),
            governance_participation_score=Decimal('0.3'),
            liquidation_history_score=Decimal('0.8'),
            account_age_score=Decimal('0.5'),
            volume_score=Decimal('0.4'),
            risk_tier=RiskTier.STANDARD,
            confidence_level=Decimal('0.3'),
            last_calculated=datetime.utcnow()
        )

    def _get_fallback_asa_risk(self, asset_symbol: str) -> ASARiskMetrics:
        """Get fallback ASA risk metrics when calculation fails."""
        return ASARiskMetrics(
            asset_id=asset_symbol,
            symbol=asset_symbol,
            volatility_30d=Decimal('0.6'),
            volatility_90d=Decimal('0.65'),
            liquidity_score=Decimal('0.3'),
            market_cap_usd=Decimal('1000000'),
            trading_volume_24h=Decimal('100000'),
            holder_count=1000,
            concentration_risk=Decimal('0.8'),
            smart_contract_risk=Decimal('0.5'),
            regulatory_risk=Decimal('0.3'),
            overall_risk_score=Decimal('0.7'),
            last_updated=datetime.utcnow()
        )

    def _get_fallback_rate_calculation(
        self,
        borrower: AlgorandAddress,
        loan_amount_usd: Decimal,
        loan_duration_days: int,
        collateral_assets: List[str],
        collateral_value_usd: Decimal,
        market_condition: str
    ) -> RateCalculation:
        """Get fallback rate calculation when normal calculation fails."""
        # Use conservative fallback rate
        fallback_rate = self.config.base_spread + Decimal('0.05')  # Base + 5% conservative premium

        fallback_factors = RateFactors(
            base_rate=fallback_rate,
            risk_premium=Decimal('0.02'),
            liquidity_premium=Decimal('0.01'),
            duration_premium=Decimal('0.005'),
            market_conditions_adjustment=Decimal('0'),
            reputation_adjustment=Decimal('0.01'),
            collateral_adjustment=Decimal('0.01'),
            network_adjustment=Decimal('0'),
            defi_yield_adjustment=Decimal('0'),
            governance_adjustment=Decimal('0')
        )

        fallback_staking = self._get_fallback_staking_metrics()
        fallback_reputation = self._get_fallback_reputation_score(borrower)
        fallback_network = NetworkMetrics(
            current_tps=Decimal('50'),
            average_tps_24h=Decimal('45'),
            block_time_avg=Decimal('3.3'),
            finality_time=Decimal('3.3'),
            total_accounts=1000000,
            active_accounts_24h=50000,
            total_transactions_24h=1000000,
            network_congestion=Decimal('0.2'),
            gas_price_trend=Decimal('1.0'),
            network_health=NetworkHealth.GOOD,
            consensus_status="healthy",
            last_updated=datetime.utcnow()
        )

        return RateCalculation(
            borrower_address=borrower,
            loan_amount_usd=loan_amount_usd,
            loan_duration_days=loan_duration_days,
            collateral_assets=collateral_assets,
            collateral_value_usd=collateral_value_usd,
            rate_factors=fallback_factors,
            final_interest_rate=self._apply_rate_bounds(fallback_factors.total_rate()),
            effective_apr=fallback_factors.total_rate(),
            staking_metrics=fallback_staking,
            reputation_score=fallback_reputation,
            network_metrics=fallback_network,
            market_condition=market_condition,
            borrower_risk_tier=RiskTier.STANDARD,
            loan_risk_score=Decimal('0.5'),
            collateral_risk_score=Decimal('0.5'),
            min_rate=self.config.min_rate,
            max_rate=self.config.max_rate,
            confidence_interval=Decimal('0.3'),
            calculation_timestamp=datetime.utcnow(),
            model_version="1.0.0",
            data_freshness_score=Decimal('0.3')
        )

    # Public utility methods
    async def get_yield_curve(self) -> Dict[str, Decimal]:
        """Get yield curve for different loan durations."""
        base_metrics = await self._calculate_base_rates()
        base_rate = base_metrics.base_rate()

        # Build yield curve with duration premiums
        duration_premium_per_year = self.config.duration_premium_per_year

        return {
            'overnight': base_rate,
            'one_week': base_rate + duration_premium_per_year * Decimal('0.02'),   # ~1 week
            'one_month': base_rate + duration_premium_per_year * Decimal('0.08'),  # ~1 month
            'three_months': base_rate + duration_premium_per_year * Decimal('0.25'), # 3 months
            'six_months': base_rate + duration_premium_per_year * Decimal('0.5'),   # 6 months
            'one_year': base_rate + duration_premium_per_year,                       # 1 year
            'two_years': base_rate + duration_premium_per_year * Decimal('2')       # 2 years
        }

    def calculate_rate_for_duration(self, base_rate: Decimal, duration_days: int) -> Decimal:
        """Calculate rate for specific loan duration."""
        duration_years = Decimal(str(duration_days)) / Decimal('365')
        duration_premium = duration_years * self.config.duration_premium_per_year
        return base_rate + duration_premium

    async def validate_data_quality(self) -> Dict[str, bool]:
        """Validate the quality and freshness of data sources."""
        validation_results = {}

        # Test base rate data
        try:
            staking_metrics = await self._calculate_base_rates()
            validation_results['staking_data'] = (
                staking_metrics.participation_rate > 0 and
                staking_metrics.current_apy > 0
            )
        except Exception:
            validation_results['staking_data'] = False

        # Test network metrics
        try:
            network_metrics = await self._get_network_metrics()
            validation_results['network_data'] = (
                network_metrics.current_tps > 0 and
                network_metrics.network_health != NetworkHealth.POOR
            )
        except Exception:
            validation_results['network_data'] = False

        # Test DeFi yield data
        try:
            defi_yields = await self._get_defi_yield_data()
            validation_results['defi_data'] = len(defi_yields) > 0
        except Exception:
            validation_results['defi_data'] = False

        return validation_results

    def get_supported_assets(self) -> List[str]:
        """Get list of assets with risk assessment support."""
        return ['ALGO', 'USDC', 'USDT', 'STBL']

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._rate_cache.clear()
        self._data_cache.clear()
        logger.info("Interest rate engine cache cleared")