"""
Algorand Wallet Behavior Analysis Engine
Analyzes on-chain wallet transaction patterns, balance stability, and asset holdings.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
import math

from algosdk.v2client import algod, indexer
from algosdk import account


@dataclass
class TransactionPattern:
    """Transaction pattern analysis results"""
    total_transactions: int
    avg_transactions_per_day: float
    consistency_score: float
    large_transaction_ratio: float
    transaction_types: Dict[str, int]


@dataclass
class BalanceAnalysis:
    """Balance stability analysis results"""
    current_balance: float
    avg_balance: float
    balance_volatility: float
    stability_score: float
    min_balance: float
    max_balance: float


@dataclass
class AssetHoldings:
    """Asset holding diversity analysis"""
    total_assets: int
    asa_count: int
    asset_diversity_score: float
    quality_assets: List[Dict]
    total_value_algo: float


@dataclass
class WalletScore:
    """Complete wallet analysis score"""
    address: str
    transaction_score: float
    balance_score: float
    asset_score: float
    defi_score: float
    longevity_score: float
    overall_score: float
    analysis_timestamp: datetime


class WalletAnalyzer:
    """Analyzes Algorand wallet behavior for reputation scoring"""

    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize Algorand clients
        self.indexer_client = indexer.IndexerClient(
            indexer_token="",
            indexer_address=config['algorand_config']['indexer']['url']
        )

        self.algod_client = algod.AlgodClient(
            algod_token="",
            algod_address=config['algorand_config']['node']['url']
        )

        # Quality ASA list (major Algorand ecosystem tokens)
        self.quality_asas = {
            31566704: "USDC",      # USDC
            312769: "USDt",        # Tether USD
            465865291: "STBL",     # AlgoStable
            230946361: "OPUL",     # Opulous
            27165954: "PLANET",    # PlanetWatch
            287867876: "SMILE",    # SmileCoin
            552635992: "GARD",     # Gard Protocol
            226265212: "DEGEN",    # Degen Protocol
        }

    async def analyze_wallet(self, wallet_address: str) -> WalletScore:
        """Perform comprehensive wallet analysis"""
        try:
            self.logger.info(f"Analyzing wallet: {wallet_address}")

            # Validate wallet address
            if not self._is_valid_address(wallet_address):
                raise ValueError(f"Invalid Algorand address: {wallet_address}")

            # Run parallel analysis
            results = await asyncio.gather(
                self._analyze_transaction_patterns(wallet_address),
                self._analyze_balance_stability(wallet_address),
                self._analyze_asset_holdings(wallet_address),
                self._analyze_defi_engagement(wallet_address),
                self._analyze_account_longevity(wallet_address),
                return_exceptions=True
            )

            # Extract results (handle exceptions)
            transaction_analysis = results[0] if not isinstance(results[0], Exception) else None
            balance_analysis = results[1] if not isinstance(results[1], Exception) else None
            asset_analysis = results[2] if not isinstance(results[2], Exception) else None
            defi_score = results[3] if not isinstance(results[3], Exception) else 0.0
            longevity_score = results[4] if not isinstance(results[4], Exception) else 0.0

            # Calculate component scores
            transaction_score = self._calculate_transaction_score(transaction_analysis)
            balance_score = self._calculate_balance_score(balance_analysis)
            asset_score = self._calculate_asset_score(asset_analysis)

            # Calculate weighted overall score
            weights = self.config['reputation_scoring']['wallet_weights']
            overall_score = (
                transaction_score * weights['transaction_consistency'] +
                balance_score * weights['balance_stability'] +
                asset_score * weights['asset_diversity'] +
                defi_score * weights['defi_engagement'] +
                longevity_score * weights['network_longevity']
            )

            return WalletScore(
                address=wallet_address,
                transaction_score=transaction_score,
                balance_score=balance_score,
                asset_score=asset_score,
                defi_score=defi_score,
                longevity_score=longevity_score,
                overall_score=overall_score,
                analysis_timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Error analyzing wallet {wallet_address}: {e}")
            raise

    async def _analyze_transaction_patterns(self, address: str) -> Optional[TransactionPattern]:
        """Analyze transaction patterns and consistency"""
        try:
            # Get transaction history
            lookback_date = datetime.utcnow() - timedelta(
                days=self.config['reputation_scoring']['transaction_analysis']['lookback_days']
            )

            # Query transactions from indexer
            transactions = []
            next_token = None

            while True:
                response = self.indexer_client.search_transactions(
                    address=address,
                    min_timestamp=int(lookback_date.timestamp()),
                    limit=1000,
                    next_page=next_token
                )

                if 'transactions' in response:
                    transactions.extend(response['transactions'])

                if 'next-token' not in response:
                    break

                next_token = response['next-token']

            if not transactions:
                return None

            # Analyze transaction patterns
            total_txns = len(transactions)
            days_analyzed = (datetime.utcnow() - lookback_date).days
            avg_txns_per_day = total_txns / max(days_analyzed, 1)

            # Calculate consistency score (regularity of transactions)
            daily_counts = self._calculate_daily_transaction_counts(transactions, lookback_date)
            consistency_score = self._calculate_consistency_score(daily_counts)

            # Analyze transaction types
            tx_types = {}
            large_txns = 0

            for tx in transactions:
                tx_type = tx.get('tx-type', 'unknown')
                tx_types[tx_type] = tx_types.get(tx_type, 0) + 1

                # Check for unusually large transactions
                if tx_type == 'pay' and 'payment-transaction' in tx:
                    amount = tx['payment-transaction'].get('amount', 0) / 1e6
                    if amount > 10000:  # Large transaction threshold
                        large_txns += 1

            large_tx_ratio = large_txns / max(total_txns, 1)

            return TransactionPattern(
                total_transactions=total_txns,
                avg_transactions_per_day=avg_txns_per_day,
                consistency_score=consistency_score,
                large_transaction_ratio=large_tx_ratio,
                transaction_types=tx_types
            )

        except Exception as e:
            self.logger.error(f"Error analyzing transaction patterns: {e}")
            return None

    async def _analyze_balance_stability(self, address: str) -> Optional[BalanceAnalysis]:
        """Analyze balance stability over time"""
        try:
            # Get current account info
            account_info = self.algod_client.account_info(address)
            current_balance = account_info.get('amount', 0) / 1e6

            # Get historical balance data through transactions
            lookback_date = datetime.utcnow() - timedelta(
                days=self.config['reputation_scoring']['balance_analysis']['stability_window_days']
            )

            # Calculate balance over time by analyzing transactions
            balance_history = await self._calculate_balance_history(address, lookback_date)

            if not balance_history:
                return BalanceAnalysis(
                    current_balance=current_balance,
                    avg_balance=current_balance,
                    balance_volatility=1.0,
                    stability_score=0.5,
                    min_balance=current_balance,
                    max_balance=current_balance
                )

            # Calculate statistics
            balances = [b['balance'] for b in balance_history]
            avg_balance = statistics.mean(balances)
            min_balance = min(balances)
            max_balance = max(balances)

            # Calculate volatility (coefficient of variation)
            if avg_balance > 0:
                balance_volatility = statistics.stdev(balances) / avg_balance
            else:
                balance_volatility = 1.0

            # Calculate stability score (lower volatility = higher score)
            max_volatility = self.config['reputation_scoring']['balance_analysis']['volatility_threshold']
            stability_score = max(0, 1 - (balance_volatility / max_volatility))

            return BalanceAnalysis(
                current_balance=current_balance,
                avg_balance=avg_balance,
                balance_volatility=balance_volatility,
                stability_score=stability_score,
                min_balance=min_balance,
                max_balance=max_balance
            )

        except Exception as e:
            self.logger.error(f"Error analyzing balance stability: {e}")
            return None

    async def _analyze_asset_holdings(self, address: str) -> Optional[AssetHoldings]:
        """Analyze asset holding diversity and quality"""
        try:
            # Get account assets
            account_info = self.algod_client.account_info(address)
            assets = account_info.get('assets', [])

            total_assets = len(assets) + 1  # +1 for ALGO
            asa_count = len(assets)

            # Identify quality assets
            quality_assets = []
            total_value_algo = account_info.get('amount', 0) / 1e6

            for asset in assets:
                asset_id = asset['asset-id']
                amount = asset.get('amount', 0)

                if asset_id in self.quality_asas and amount > 0:
                    # Get asset info for better analysis
                    try:
                        asset_info = self.algod_client.asset_info(asset_id)
                        decimals = asset_info['params'].get('decimals', 0)

                        quality_assets.append({
                            'asset_id': asset_id,
                            'name': self.quality_asas[asset_id],
                            'amount': amount / (10 ** decimals),
                            'raw_amount': amount
                        })
                    except:
                        pass

            # Calculate diversity score
            if total_assets <= 1:
                diversity_score = 0.0
            else:
                # Higher diversity with quality assets gets better score
                quality_bonus = len(quality_assets) * 0.1
                base_score = min(1.0, asa_count / 10)  # Max score at 10+ ASAs
                diversity_score = min(1.0, base_score + quality_bonus)

            return AssetHoldings(
                total_assets=total_assets,
                asa_count=asa_count,
                asset_diversity_score=diversity_score,
                quality_assets=quality_assets,
                total_value_algo=total_value_algo
            )

        except Exception as e:
            self.logger.error(f"Error analyzing asset holdings: {e}")
            return None

    async def _analyze_defi_engagement(self, address: str) -> float:
        """Analyze DeFi protocol engagement"""
        try:
            # This would require specific protocol analysis
            # For now, return a placeholder based on transaction patterns

            # Get recent transactions
            lookback_date = datetime.utcnow() - timedelta(days=90)

            response = self.indexer_client.search_transactions(
                address=address,
                min_timestamp=int(lookback_date.timestamp()),
                limit=1000
            )

            transactions = response.get('transactions', [])

            # Look for DeFi-related transactions (app calls, asset transfers)
            defi_indicators = 0
            total_relevant_txns = 0

            for tx in transactions:
                tx_type = tx.get('tx-type')

                if tx_type in ['appl', 'axfer']:  # App calls and asset transfers
                    total_relevant_txns += 1

                    # Check for known DeFi app IDs (simplified)
                    if tx_type == 'appl':
                        app_id = tx.get('application-transaction', {}).get('application-id', 0)
                        if app_id > 0:  # Any app interaction is DeFi indicator
                            defi_indicators += 1

                    elif tx_type == 'axfer':
                        # Asset transfers often indicate DeFi activity
                        defi_indicators += 1

            # Calculate engagement score
            if total_relevant_txns == 0:
                return 0.0

            engagement_ratio = defi_indicators / max(total_relevant_txns, 1)
            return min(1.0, engagement_ratio * 2)  # Scale to 0-1

        except Exception as e:
            self.logger.error(f"Error analyzing DeFi engagement: {e}")
            return 0.0

    async def _analyze_account_longevity(self, address: str) -> float:
        """Analyze account age and consistent activity"""
        try:
            # Find first transaction
            response = self.indexer_client.search_transactions(
                address=address,
                limit=1
            )

            transactions = response.get('transactions', [])
            if not transactions:
                return 0.0

            # Get account creation time (approximate from first transaction)
            first_tx_time = transactions[0].get('round-time', 0)
            account_age_days = (datetime.utcnow().timestamp() - first_tx_time) / 86400

            # Score based on age (max score at 365+ days)
            longevity_score = min(1.0, account_age_days / 365)

            return longevity_score

        except Exception as e:
            self.logger.error(f"Error analyzing account longevity: {e}")
            return 0.0

    def _calculate_daily_transaction_counts(self, transactions: List[Dict], start_date: datetime) -> List[int]:
        """Calculate daily transaction counts"""
        days = (datetime.utcnow() - start_date).days
        daily_counts = [0] * days

        for tx in transactions:
            tx_time = datetime.fromtimestamp(tx.get('round-time', 0))
            day_index = (tx_time - start_date).days

            if 0 <= day_index < days:
                daily_counts[day_index] += 1

        return daily_counts

    def _calculate_consistency_score(self, daily_counts: List[int]) -> float:
        """Calculate transaction consistency score"""
        if not daily_counts:
            return 0.0

        # Count days with activity
        active_days = sum(1 for count in daily_counts if count > 0)
        total_days = len(daily_counts)

        # Calculate consistency as ratio of active days
        consistency = active_days / max(total_days, 1)

        # Apply threshold
        threshold = self.config['reputation_scoring']['transaction_analysis']['consistency_threshold']
        return min(1.0, consistency / threshold)

    async def _calculate_balance_history(self, address: str, start_date: datetime) -> List[Dict]:
        """Calculate balance history (simplified approximation)"""
        try:
            # This is a simplified version - in practice, you'd need to
            # reconstruct balance at each transaction
            current_info = self.algod_client.account_info(address)
            current_balance = current_info.get('amount', 0) / 1e6

            # Return current balance as history point
            return [{'timestamp': datetime.utcnow(), 'balance': current_balance}]

        except Exception as e:
            self.logger.error(f"Error calculating balance history: {e}")
            return []

    def _calculate_transaction_score(self, analysis: Optional[TransactionPattern]) -> float:
        """Calculate transaction behavior score"""
        if not analysis:
            return 0.0

        min_txns = self.config['reputation_scoring']['transaction_analysis']['min_transactions']

        # Check minimum transaction requirement
        if analysis.total_transactions < min_txns:
            return 0.0

        # Combine consistency and activity level
        activity_score = min(1.0, analysis.avg_transactions_per_day / 5.0)  # Max at 5 txns/day
        consistency_score = analysis.consistency_score

        # Penalty for too many large transactions (potential manipulation)
        large_tx_penalty = analysis.large_transaction_ratio * 0.3

        return max(0.0, (activity_score + consistency_score) / 2 - large_tx_penalty)

    def _calculate_balance_score(self, analysis: Optional[BalanceAnalysis]) -> float:
        """Calculate balance stability score"""
        if not analysis:
            return 0.0

        min_balance = self.config['reputation_scoring']['balance_analysis']['min_balance_algo']

        # Check minimum balance requirement
        if analysis.current_balance < min_balance:
            return 0.0

        # Base score from stability
        base_score = analysis.stability_score

        # Bonus for higher balance (logarithmic scale)
        balance_bonus = min(0.3, math.log10(analysis.current_balance + 1) / 10)

        return min(1.0, base_score + balance_bonus)

    def _calculate_asset_score(self, analysis: Optional[AssetHoldings]) -> float:
        """Calculate asset diversity score"""
        if not analysis:
            return 0.0

        base_score = analysis.asset_diversity_score

        # Bonus for quality ASA holdings
        quality_bonus = len(analysis.quality_assets) * self.config['reputation_scoring']['balance_analysis']['asa_holding_bonus']

        return min(1.0, base_score + quality_bonus)

    def _is_valid_address(self, address: str) -> bool:
        """Validate Algorand address format"""
        try:
            # Basic validation - should be 58 characters
            if len(address) != 58:
                return False

            # Try to decode (this will raise exception if invalid)
            account.address_from_private_key(account.generate_account()[0])
            return True
        except:
            return False