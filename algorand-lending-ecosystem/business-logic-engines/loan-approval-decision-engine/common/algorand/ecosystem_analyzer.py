"""
Ecosystem Analyzer

Comprehensive analysis of borrower's complete Algorand ecosystem footprint
including DeFi participation, governance, and cross-protocol activity.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..models.decision_models import (
    AlgorandBorrower, EcosystemFootprint, DeFiBehaviorPattern,
    GovernanceParticipation, CrossProtocolActivity, HolisticRiskProfile,
    RiskLevel, ParticipationType
)

logger = logging.getLogger(__name__)


@dataclass
class EcosystemAnalysisConfig:
    """Configuration for ecosystem analysis"""
    analysis_period_days: int = 365
    min_transaction_threshold: int = 10
    governance_weight: float = 0.3
    defi_weight: float = 0.4
    cross_protocol_weight: float = 0.3
    enable_deep_analysis: bool = True


class EcosystemAnalyzer:
    """
    Analyzes complete Algorand ecosystem participation for holistic
    borrower assessment and risk profiling.
    """

    def __init__(self, config: Optional[EcosystemAnalysisConfig] = None):
        self.config = config or EcosystemAnalysisConfig()
        self.known_protocols = self._load_protocol_registry()
        self.risk_indicators = self._load_risk_indicators()

    async def analyze_borrower_ecosystem(
        self,
        wallet_address: str,
        requested_amount: float
    ) -> Tuple[AlgorandBorrower, HolisticRiskProfile]:
        """
        Perform comprehensive ecosystem analysis for a borrower.

        Args:
            wallet_address: Algorand wallet address to analyze
            requested_amount: Loan amount requested for context

        Returns:
            Tuple of (borrower profile, risk profile)
        """
        logger.info(f"Starting ecosystem analysis for {wallet_address}")

        try:
            # Parallel analysis of different ecosystem aspects
            tasks = [
                self._analyze_wallet_fundamentals(wallet_address),
                self._analyze_transaction_patterns(wallet_address),
                self._analyze_asset_portfolio(wallet_address),
                self._analyze_defi_participation(wallet_address),
                self._analyze_governance_activity(wallet_address),
                self._analyze_cross_protocol_activity(wallet_address),
                self._analyze_nft_engagement(wallet_address),
                self._analyze_smart_contract_interactions(wallet_address)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Extract results (handle any exceptions)
            wallet_data = results[0] if not isinstance(results[0], Exception) else {}
            transaction_data = results[1] if not isinstance(results[1], Exception) else {}
            asset_data = results[2] if not isinstance(results[2], Exception) else {}
            defi_data = results[3] if not isinstance(results[3], Exception) else {}
            governance_data = results[4] if not isinstance(results[4], Exception) else {}
            cross_protocol_data = results[5] if not isinstance(results[5], Exception) else {}
            nft_data = results[6] if not isinstance(results[6], Exception) else {}
            contract_data = results[7] if not isinstance(results[7], Exception) else {}

            # Build comprehensive borrower profile
            borrower = self._build_borrower_profile(
                wallet_address, wallet_data, transaction_data, asset_data,
                defi_data, governance_data, cross_protocol_data,
                nft_data, contract_data
            )

            # Generate holistic risk profile
            risk_profile = await self._generate_risk_profile(
                borrower, requested_amount, {
                    'defi': defi_data,
                    'governance': governance_data,
                    'cross_protocol': cross_protocol_data,
                    'assets': asset_data,
                    'transactions': transaction_data
                }
            )

            logger.info(f"Ecosystem analysis completed for {wallet_address}")
            return borrower, risk_profile

        except Exception as e:
            logger.error(f"Ecosystem analysis failed for {wallet_address}: {e}")
            raise

    async def _analyze_wallet_fundamentals(self, address: str) -> Dict:
        """Analyze basic wallet characteristics"""
        # Mock implementation - would integrate with Algorand indexer
        return {
            'creation_date': datetime.utcnow() - timedelta(days=500),
            'total_transactions': 1247,
            'algo_balance': 15642.5,
            'opted_in_apps': 23,
            'opted_in_assets': 45,
            'reputation_indicators': ['verified_identity', 'long_term_holder']
        }

    async def _analyze_transaction_patterns(self, address: str) -> Dict:
        """Analyze transaction patterns and behavior"""
        # Mock implementation - would analyze on-chain transaction history
        return {
            'avg_daily_transactions': 3.2,
            'transaction_diversity_score': 0.78,
            'gas_optimization_score': 0.85,
            'time_consistency_score': 0.92,
            'weekend_activity_ratio': 0.65,
            'large_transaction_frequency': 0.12,
            'micro_transaction_ratio': 0.34
        }

    async def _analyze_asset_portfolio(self, address: str) -> Dict:
        """Analyze asset holdings and diversification"""
        # Mock implementation - would analyze asset holdings
        return {
            'total_asset_value_usd': 45230.50,
            'asset_count': 15,
            'asset_diversity_score': 0.73,
            'stable_asset_percentage': 0.45,
            'native_algo_percentage': 0.35,
            'exotic_asset_percentage': 0.20,
            'largest_position_percentage': 0.25,
            'portfolio_volatility_score': 0.62
        }

    async def _analyze_defi_participation(self, address: str) -> Dict:
        """Analyze DeFi protocol participation and behavior"""
        # Mock implementation - would analyze DeFi interactions
        return {
            'protocols_used': ['Tinyman', 'Algofi', 'Folks Finance', 'Pact'],
            'total_defi_volume': 125000.0,
            'yield_farming_active': True,
            'liquidity_provision_score': 0.82,
            'lending_borrowing_history': True,
            'advanced_strategy_usage': True,
            'defi_sophistication_score': 0.88,
            'risk_adjusted_returns': 0.14
        }

    async def _analyze_governance_activity(self, address: str) -> Dict:
        """Analyze governance participation"""
        # Mock implementation - would analyze governance data
        return {
            'participation_type': ParticipationType.VOTER,
            'votes_cast': 15,
            'proposals_submitted': 2,
            'delegation_received': 5000.0,
            'continuous_participation_months': 18,
            'vote_consistency_score': 0.94,
            'community_engagement_score': 0.76
        }

    async def _analyze_cross_protocol_activity(self, address: str) -> Dict:
        """Analyze cross-protocol and bridge activity"""
        # Mock implementation - would analyze bridge usage
        return {
            'bridge_protocols_used': ['Wormhole', 'Portal Bridge'],
            'cross_chain_volume': 25000.0,
            'bridge_frequency': 8,
            'algorand_native_percentage': 0.75,
            'return_frequency_score': 0.85,
            'multi_chain_sophistication': 0.68
        }

    async def _analyze_nft_engagement(self, address: str) -> Dict:
        """Analyze NFT holdings and creation activity"""
        # Mock implementation - would analyze NFT data
        return {
            'nft_count': 12,
            'nft_creation_activity': True,
            'nft_trading_volume': 1500.0,
            'rare_nft_holdings': 3,
            'nft_portfolio_value': 8500.0,
            'creator_reputation_score': 0.65
        }

    async def _analyze_smart_contract_interactions(self, address: str) -> Dict:
        """Analyze smart contract interaction patterns"""
        # Mock implementation - would analyze contract interactions
        return {
            'unique_contracts_interacted': 45,
            'contract_interaction_frequency': 0.85,
            'advanced_contract_usage': True,
            'contract_creation_count': 3,
            'technical_sophistication_score': 0.79,
            'security_conscious_behavior': 0.91
        }

    def _build_borrower_profile(
        self,
        address: str,
        wallet_data: Dict,
        transaction_data: Dict,
        asset_data: Dict,
        defi_data: Dict,
        governance_data: Dict,
        cross_protocol_data: Dict,
        nft_data: Dict,
        contract_data: Dict
    ) -> AlgorandBorrower:
        """Build comprehensive borrower profile from analysis results"""

        creation_date = wallet_data.get('creation_date', datetime.utcnow())
        wallet_age = (datetime.utcnow() - creation_date).days

        return AlgorandBorrower(
            wallet_address=address,
            wallet_age_days=wallet_age,
            total_transaction_count=wallet_data.get('total_transactions', 0),
            total_volume_algo=defi_data.get('total_defi_volume', 0.0),
            asset_count=asset_data.get('asset_count', 0),
            nft_count=nft_data.get('nft_count', 0),
            smart_contract_interactions=contract_data.get('unique_contracts_interacted', 0),
            dapp_count=len(defi_data.get('protocols_used', [])),
            governance_participation=governance_data.get('votes_cast', 0) > 0,
            validator_participation=governance_data.get('participation_type') == ParticipationType.VALIDATOR,
            reputation_score=self._calculate_reputation_score(
                wallet_data, governance_data, defi_data
            ),
            ecosystem_tenure_months=governance_data.get('continuous_participation_months', 0),
            metadata={
                'defi_sophistication': defi_data.get('defi_sophistication_score', 0.0),
                'technical_sophistication': contract_data.get('technical_sophistication_score', 0.0),
                'risk_management_score': asset_data.get('portfolio_volatility_score', 0.0)
            }
        )

    async def _generate_risk_profile(
        self,
        borrower: AlgorandBorrower,
        requested_amount: float,
        analysis_data: Dict
    ) -> HolisticRiskProfile:
        """Generate comprehensive risk profile"""

        # Calculate component scores
        ecosystem_trust = self._calculate_ecosystem_trust_score(borrower, analysis_data)
        financial_sophistication = self._calculate_financial_sophistication_score(analysis_data)
        long_term_commitment = self._calculate_long_term_commitment_score(borrower, analysis_data)
        community_standing = self._calculate_community_standing_score(analysis_data)

        # Calculate risk factors
        volatility_exposure = self._calculate_volatility_exposure_risk(analysis_data)
        concentration_risk = self._calculate_concentration_risk(analysis_data)
        counterparty_risk = self._calculate_counterparty_risk(analysis_data)
        technical_risk = self._calculate_technical_risk(analysis_data)

        # Calculate behavioral indicators
        consistency = self._calculate_consistency_score(analysis_data)
        growth_trajectory = self._calculate_growth_trajectory_score(borrower)
        adaptation = self._calculate_adaptation_score(analysis_data)

        # Overall risk calculation
        risk_score = self._calculate_overall_risk_score({
            'ecosystem_trust': ecosystem_trust,
            'financial_sophistication': financial_sophistication,
            'volatility_exposure': volatility_exposure,
            'concentration_risk': concentration_risk,
            'consistency': consistency
        })

        risk_level = self._determine_risk_level(risk_score)
        confidence = self._calculate_confidence_level(analysis_data)

        return HolisticRiskProfile(
            ecosystem_trust_score=ecosystem_trust,
            financial_sophistication_score=financial_sophistication,
            long_term_commitment_score=long_term_commitment,
            community_standing_score=community_standing,
            volatility_exposure_score=volatility_exposure,
            concentration_risk_score=concentration_risk,
            counterparty_risk_score=counterparty_risk,
            technical_risk_score=technical_risk,
            consistency_score=consistency,
            growth_trajectory_score=growth_trajectory,
            adaptation_score=adaptation,
            overall_risk_level=risk_level,
            risk_score=risk_score,
            confidence_level=confidence
        )

    def _calculate_reputation_score(
        self,
        wallet_data: Dict,
        governance_data: Dict,
        defi_data: Dict
    ) -> float:
        """Calculate overall reputation score (0-100)"""
        base_score = 50.0

        # Governance participation bonus
        if governance_data.get('votes_cast', 0) > 0:
            base_score += 15.0

        # DeFi sophistication bonus
        if defi_data.get('defi_sophistication_score', 0) > 0.7:
            base_score += 10.0

        # Long-term presence bonus
        if governance_data.get('continuous_participation_months', 0) > 12:
            base_score += 10.0

        # Community engagement bonus
        if governance_data.get('community_engagement_score', 0) > 0.8:
            base_score += 10.0

        # Reputation indicators bonus
        reputation_indicators = wallet_data.get('reputation_indicators', [])
        base_score += len(reputation_indicators) * 2.5

        return min(base_score, 100.0)

    def _calculate_ecosystem_trust_score(self, borrower: AlgorandBorrower, data: Dict) -> float:
        """Calculate ecosystem trust score based on participation depth"""
        trust_score = 0.0

        # Wallet age contribution (0-25 points)
        age_months = borrower.wallet_age_days / 30.0
        trust_score += min(age_months / 24.0 * 25.0, 25.0)

        # Transaction volume contribution (0-20 points)
        volume_score = min(borrower.total_volume_algo / 100000.0 * 20.0, 20.0)
        trust_score += volume_score

        # Governance participation (0-25 points)
        if borrower.governance_participation:
            governance_data = data.get('governance', {})
            participation_score = governance_data.get('vote_consistency_score', 0) * 25.0
            trust_score += participation_score

        # DeFi engagement depth (0-20 points)
        defi_data = data.get('defi', {})
        defi_score = defi_data.get('defi_sophistication_score', 0) * 20.0
        trust_score += defi_score

        # Community standing (0-10 points)
        governance_data = data.get('governance', {})
        community_score = governance_data.get('community_engagement_score', 0) * 10.0
        trust_score += community_score

        return min(trust_score, 100.0)

    def _calculate_financial_sophistication_score(self, data: Dict) -> float:
        """Calculate financial sophistication based on DeFi behavior"""
        sophistication_score = 0.0

        defi_data = data.get('defi', {})
        asset_data = data.get('assets', {})

        # DeFi sophistication (0-40 points)
        sophistication_score += defi_data.get('defi_sophistication_score', 0) * 40.0

        # Portfolio management (0-25 points)
        diversity_score = asset_data.get('asset_diversity_score', 0) * 25.0
        sophistication_score += diversity_score

        # Risk management (0-20 points)
        risk_adjusted_returns = defi_data.get('risk_adjusted_returns', 0)
        if risk_adjusted_returns > 0:
            sophistication_score += min(risk_adjusted_returns * 100, 20.0)

        # Advanced strategy usage (0-15 points)
        if defi_data.get('advanced_strategy_usage', False):
            sophistication_score += 15.0

        return min(sophistication_score, 100.0)

    def _calculate_long_term_commitment_score(self, borrower: AlgorandBorrower, data: Dict) -> float:
        """Calculate long-term commitment to Algorand ecosystem"""
        commitment_score = 0.0

        # Ecosystem tenure (0-30 points)
        tenure_months = borrower.ecosystem_tenure_months
        commitment_score += min(tenure_months / 24.0 * 30.0, 30.0)

        # Continuous participation (0-25 points)
        governance_data = data.get('governance', {})
        continuous_months = governance_data.get('continuous_participation_months', 0)
        commitment_score += min(continuous_months / 24.0 * 25.0, 25.0)

        # Algorand native preference (0-25 points)
        cross_protocol_data = data.get('cross_protocol', {})
        native_percentage = cross_protocol_data.get('algorand_native_percentage', 0)
        commitment_score += native_percentage * 25.0

        # Asset holding patterns (0-20 points)
        asset_data = data.get('assets', {})
        algo_percentage = asset_data.get('native_algo_percentage', 0)
        commitment_score += algo_percentage * 20.0

        return min(commitment_score, 100.0)

    def _calculate_community_standing_score(self, data: Dict) -> float:
        """Calculate community standing and engagement score"""
        standing_score = 0.0

        governance_data = data.get('governance', {})

        # Governance engagement (0-40 points)
        standing_score += governance_data.get('community_engagement_score', 0) * 40.0

        # Proposal quality (0-25 points)
        standing_score += governance_data.get('proposal_quality_score', 0) * 25.0

        # Vote consistency (0-20 points)
        standing_score += governance_data.get('vote_consistency_score', 0) * 20.0

        # Delegation received (0-15 points)
        delegation = governance_data.get('delegation_received', 0)
        if delegation > 0:
            standing_score += min(delegation / 10000.0 * 15.0, 15.0)

        return min(standing_score, 100.0)

    def _calculate_volatility_exposure_risk(self, data: Dict) -> float:
        """Calculate risk from volatility exposure"""
        asset_data = data.get('assets', {})

        volatility_score = asset_data.get('portfolio_volatility_score', 0.5)
        exotic_percentage = asset_data.get('exotic_asset_percentage', 0)

        # Higher volatility and exotic assets = higher risk
        risk_score = volatility_score * 60.0 + exotic_percentage * 40.0
        return min(risk_score, 100.0)

    def _calculate_concentration_risk(self, data: Dict) -> float:
        """Calculate concentration risk from portfolio diversification"""
        asset_data = data.get('assets', {})

        largest_position = asset_data.get('largest_position_percentage', 0)
        diversity_score = asset_data.get('asset_diversity_score', 1.0)

        # High concentration = high risk
        concentration_risk = largest_position * 100.0
        diversification_bonus = (1.0 - diversity_score) * 50.0

        return min(concentration_risk + diversification_bonus, 100.0)

    def _calculate_counterparty_risk(self, data: Dict) -> float:
        """Calculate counterparty risk from protocol interactions"""
        defi_data = data.get('defi', {})
        cross_protocol_data = data.get('cross_protocol', {})

        # More protocols = potentially higher counterparty risk
        protocol_count = len(defi_data.get('protocols_used', []))
        bridge_count = len(cross_protocol_data.get('bridge_protocols_used', []))

        protocol_risk = min(protocol_count / 10.0 * 30.0, 30.0)
        bridge_risk = min(bridge_count / 5.0 * 20.0, 20.0)

        # But sophistication reduces risk
        sophistication = defi_data.get('defi_sophistication_score', 0)
        sophistication_reduction = sophistication * 25.0

        return max(protocol_risk + bridge_risk - sophistication_reduction, 0.0)

    def _calculate_technical_risk(self, data: Dict) -> float:
        """Calculate technical risk from smart contract interactions"""
        contract_data = data.get('transactions', {})

        # Low technical sophistication = higher risk
        tech_sophistication = contract_data.get('technical_sophistication_score', 0.5)
        security_behavior = contract_data.get('security_conscious_behavior', 0.5)

        # Convert to risk score (inverse relationship)
        risk_score = (2.0 - tech_sophistication - security_behavior) * 50.0
        return min(max(risk_score, 0.0), 100.0)

    def _calculate_consistency_score(self, data: Dict) -> float:
        """Calculate behavioral consistency score"""
        transaction_data = data.get('transactions', {})
        governance_data = data.get('governance', {})

        time_consistency = transaction_data.get('time_consistency_score', 0.5)
        vote_consistency = governance_data.get('vote_consistency_score', 0.5)

        return (time_consistency + vote_consistency) / 2.0 * 100.0

    def _calculate_growth_trajectory_score(self, borrower: AlgorandBorrower) -> float:
        """Calculate growth trajectory based on historical data"""
        # Mock implementation - would analyze historical growth
        base_score = 50.0

        # More transactions and interactions suggest growth
        if borrower.total_transaction_count > 1000:
            base_score += 20.0

        if borrower.dapp_count > 5:
            base_score += 15.0

        if borrower.ecosystem_tenure_months > 12:
            base_score += 15.0

        return min(base_score, 100.0)

    def _calculate_adaptation_score(self, data: Dict) -> float:
        """Calculate adaptation to new protocols and features"""
        defi_data = data.get('defi', {})
        cross_protocol_data = data.get('cross_protocol', {})

        # Multi-protocol usage indicates adaptation
        protocol_diversity = len(defi_data.get('protocols_used', []))
        cross_chain_activity = len(cross_protocol_data.get('bridge_protocols_used', []))

        adaptation_score = min(protocol_diversity / 8.0 * 70.0, 70.0)
        adaptation_score += min(cross_chain_activity / 3.0 * 30.0, 30.0)

        return min(adaptation_score, 100.0)

    def _calculate_overall_risk_score(self, component_scores: Dict[str, float]) -> float:
        """Calculate weighted overall risk score"""
        weights = {
            'ecosystem_trust': 0.25,
            'financial_sophistication': 0.20,
            'volatility_exposure': 0.20,
            'concentration_risk': 0.15,
            'consistency': 0.20
        }

        weighted_score = 0.0
        for component, score in component_scores.items():
            weight = weights.get(component, 0.0)
            # For positive factors, convert to risk (inverse)
            if component in ['ecosystem_trust', 'financial_sophistication', 'consistency']:
                risk_contribution = (100.0 - score) * weight
            else:
                risk_contribution = score * weight
            weighted_score += risk_contribution

        return min(weighted_score, 100.0)

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from numeric score"""
        if risk_score <= 20:
            return RiskLevel.VERY_LOW
        elif risk_score <= 40:
            return RiskLevel.LOW
        elif risk_score <= 60:
            return RiskLevel.MEDIUM
        elif risk_score <= 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH

    def _calculate_confidence_level(self, data: Dict) -> float:
        """Calculate confidence in the analysis"""
        # Base confidence
        confidence = 0.7

        # More data points = higher confidence
        data_completeness = 0.0
        required_sections = ['defi', 'governance', 'assets', 'transactions']

        for section in required_sections:
            if section in data and data[section]:
                data_completeness += 0.25

        # Transaction history depth affects confidence
        transaction_data = data.get('transactions', {})
        transaction_count = transaction_data.get('total_transactions', 0)
        if transaction_count > 100:
            confidence += 0.1
        if transaction_count > 1000:
            confidence += 0.1

        final_confidence = min(confidence * data_completeness, 1.0)
        return max(final_confidence, 0.3)  # Minimum confidence threshold

    def _load_protocol_registry(self) -> Dict[str, Dict]:
        """Load known protocol information for analysis"""
        return {
            'tinyman': {'category': 'dex', 'risk_level': 'low'},
            'algofi': {'category': 'lending', 'risk_level': 'low'},
            'folks_finance': {'category': 'lending', 'risk_level': 'medium'},
            'pact': {'category': 'dex', 'risk_level': 'medium'},
            'wormhole': {'category': 'bridge', 'risk_level': 'high'}
        }

    def _load_risk_indicators(self) -> Dict[str, List[str]]:
        """Load known risk indicators and patterns"""
        return {
            'high_risk_patterns': [
                'frequent_bridge_usage',
                'exotic_asset_concentration',
                'flash_loan_abuse',
                'governance_manipulation'
            ],
            'positive_indicators': [
                'consistent_governance_participation',
                'diversified_defi_usage',
                'long_term_holding_patterns',
                'community_contribution'
            ]
        }