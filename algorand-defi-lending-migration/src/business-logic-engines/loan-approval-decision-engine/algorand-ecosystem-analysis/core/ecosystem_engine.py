"""
Ecosystem Analysis Engine

Main engine orchestrating complete borrower ecosystem analysis across all
Algorand protocols, dApps, governance, and cross-chain activities.
"""

import asyncio
import logging
import yaml
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

from .wallet_footprint import WalletFootprintAnalyzer
from .dapp_engagement import DAppEngagementAnalyzer
from .nft_portfolio import NFTPortfolioAnalyzer
from ..common.models.decision_models import (
    AlgorandBorrower, EcosystemFootprint, DeFiBehaviorPattern,
    GovernanceParticipation, CrossProtocolActivity, HolisticRiskProfile
)
from ..common.algorand.ecosystem_analyzer import EcosystemAnalyzer
from ..common.utils.pattern_recognition import PatternRecognitionEngine

logger = logging.getLogger(__name__)


@dataclass
class EcosystemAnalysisResult:
    """Complete ecosystem analysis result"""
    borrower_profile: AlgorandBorrower
    ecosystem_footprint: EcosystemFootprint
    defi_behavior: DeFiBehaviorPattern
    governance_participation: GovernanceParticipation
    cross_protocol_activity: CrossProtocolActivity
    risk_profile: HolisticRiskProfile
    detected_patterns: List[Dict[str, Any]]
    analysis_metadata: Dict[str, Any]
    confidence_score: float


class EcosystemAnalysisEngine:
    """
    Main engine for comprehensive Algorand ecosystem analysis.
    Orchestrates all analysis components for holistic borrower assessment.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.wallet_analyzer = WalletFootprintAnalyzer(self.config)
        self.dapp_analyzer = DAppEngagementAnalyzer(self.config)
        self.nft_analyzer = NFTPortfolioAnalyzer(self.config)
        self.ecosystem_analyzer = EcosystemAnalyzer()
        self.pattern_engine = PatternRecognitionEngine()

    async def analyze_complete_ecosystem(
        self,
        wallet_address: str,
        analysis_depth: str = "comprehensive",
        requested_loan_amount: Optional[float] = None
    ) -> EcosystemAnalysisResult:
        """
        Perform complete ecosystem analysis for a borrower.

        Args:
            wallet_address: Algorand wallet address to analyze
            analysis_depth: Level of analysis (basic, standard, comprehensive)
            requested_loan_amount: Loan amount context for risk assessment

        Returns:
            Complete ecosystem analysis result
        """
        logger.info(f"Starting comprehensive ecosystem analysis for {wallet_address}")

        try:
            analysis_start = datetime.utcnow()

            # Validate analysis depth
            if analysis_depth not in self.config['analysis']['depth_levels']:
                raise ValueError(f"Invalid analysis depth: {analysis_depth}")

            # Parallel execution of all analysis components
            analysis_tasks = self._create_analysis_tasks(
                wallet_address, analysis_depth, requested_loan_amount
            )

            # Execute all analyses concurrently
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            # Process results
            analysis_results = self._process_analysis_results(results)

            # Generate comprehensive ecosystem analysis
            ecosystem_result = await self._synthesize_ecosystem_analysis(
                wallet_address, analysis_results, analysis_depth,
                requested_loan_amount, analysis_start
            )

            analysis_duration = (datetime.utcnow() - analysis_start).total_seconds()
            logger.info(f"Ecosystem analysis completed in {analysis_duration:.2f} seconds")

            return ecosystem_result

        except Exception as e:
            logger.error(f"Ecosystem analysis failed for {wallet_address}: {e}")
            raise

    def _create_analysis_tasks(
        self,
        wallet_address: str,
        analysis_depth: str,
        requested_loan_amount: Optional[float]
    ) -> List[asyncio.Task]:
        """Create analysis tasks based on requested depth"""

        tasks = []
        depth_components = self.config['analysis']['depth_levels'][analysis_depth].split(',')

        # Always include wallet fundamentals
        tasks.append(asyncio.create_task(
            self.wallet_analyzer.analyze_wallet_fundamentals(wallet_address),
            name="wallet_fundamentals"
        ))

        # Transaction patterns analysis
        if 'transaction_patterns' in depth_components:
            tasks.append(asyncio.create_task(
                self.wallet_analyzer.analyze_transaction_patterns(wallet_address),
                name="transaction_patterns"
            ))

        # Asset analysis
        if 'asset_analysis' in depth_components:
            tasks.append(asyncio.create_task(
                self.wallet_analyzer.analyze_asset_portfolio(wallet_address),
                name="asset_analysis"
            ))

        # Governance analysis
        if any(comp in depth_components for comp in ['governance_basic', 'governance_detailed']):
            detail_level = 'detailed' if 'governance_detailed' in depth_components else 'basic'
            tasks.append(asyncio.create_task(
                self._analyze_governance_participation(wallet_address, detail_level),
                name="governance_analysis"
            ))

        # DeFi analysis
        if 'defi_analysis' in depth_components:
            tasks.append(asyncio.create_task(
                self.dapp_analyzer.analyze_defi_engagement(wallet_address),
                name="defi_analysis"
            ))

        # NFT analysis
        if 'nft_analysis' in depth_components:
            tasks.append(asyncio.create_task(
                self.nft_analyzer.analyze_nft_portfolio(wallet_address),
                name="nft_analysis"
            ))

        # Cross-protocol analysis
        if 'cross_protocol' in depth_components:
            tasks.append(asyncio.create_task(
                self._analyze_cross_protocol_activity(wallet_address),
                name="cross_protocol"
            ))

        # Pattern recognition (always for comprehensive analysis)
        if analysis_depth == 'comprehensive':
            tasks.append(asyncio.create_task(
                self._detect_behavioral_patterns(wallet_address),
                name="pattern_recognition"
            ))

        return tasks

    def _process_analysis_results(self, results: List[Any]) -> Dict[str, Any]:
        """Process and organize analysis results"""
        processed_results = {}

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Analysis task {i} failed: {result}")
                continue

            # Extract task name and result
            if hasattr(result, '_task_name'):
                task_name = result._task_name
            else:
                task_name = f"task_{i}"

            processed_results[task_name] = result

        return processed_results

    async def _synthesize_ecosystem_analysis(
        self,
        wallet_address: str,
        analysis_results: Dict[str, Any],
        analysis_depth: str,
        requested_loan_amount: Optional[float],
        analysis_start: datetime
    ) -> EcosystemAnalysisResult:
        """Synthesize all analysis results into comprehensive ecosystem view"""

        # Build borrower profile
        borrower_profile = self._build_borrower_profile(
            wallet_address, analysis_results
        )

        # Build ecosystem footprint
        ecosystem_footprint = self._build_ecosystem_footprint(
            analysis_results
        )

        # Build DeFi behavior pattern
        defi_behavior = self._build_defi_behavior_pattern(
            analysis_results
        )

        # Build governance participation
        governance_participation = self._build_governance_participation(
            analysis_results
        )

        # Build cross-protocol activity
        cross_protocol_activity = self._build_cross_protocol_activity(
            analysis_results
        )

        # Generate holistic risk profile using ecosystem analyzer
        borrower_profile_full, risk_profile = await self.ecosystem_analyzer.analyze_borrower_ecosystem(
            wallet_address, requested_loan_amount or 10000
        )

        # Extract detected patterns
        detected_patterns = analysis_results.get('pattern_recognition', [])

        # Calculate overall confidence
        confidence_score = self._calculate_analysis_confidence(analysis_results)

        # Create analysis metadata
        analysis_metadata = {
            'analysis_depth': analysis_depth,
            'analysis_duration_seconds': (datetime.utcnow() - analysis_start).total_seconds(),
            'components_analyzed': list(analysis_results.keys()),
            'data_freshness': self._assess_data_freshness(analysis_results),
            'algorithm_version': '1.0',
            'config_version': self.config.get('version', '1.0')
        }

        return EcosystemAnalysisResult(
            borrower_profile=borrower_profile,
            ecosystem_footprint=ecosystem_footprint,
            defi_behavior=defi_behavior,
            governance_participation=governance_participation,
            cross_protocol_activity=cross_protocol_activity,
            risk_profile=risk_profile,
            detected_patterns=detected_patterns,
            analysis_metadata=analysis_metadata,
            confidence_score=confidence_score
        )

    def _build_borrower_profile(
        self,
        wallet_address: str,
        analysis_results: Dict[str, Any]
    ) -> AlgorandBorrower:
        """Build comprehensive borrower profile from analysis results"""

        wallet_data = analysis_results.get('wallet_fundamentals', {})
        transaction_data = analysis_results.get('transaction_patterns', {})
        asset_data = analysis_results.get('asset_analysis', {})
        defi_data = analysis_results.get('defi_analysis', {})
        governance_data = analysis_results.get('governance_analysis', {})

        # Extract basic metrics
        wallet_age = wallet_data.get('wallet_age_days', 0)
        transaction_count = transaction_data.get('total_transactions', 0)
        total_volume = transaction_data.get('total_volume_algo', 0.0)
        asset_count = asset_data.get('asset_count', 0)
        nft_count = asset_data.get('nft_count', 0)
        contract_interactions = defi_data.get('contract_interactions', 0)
        dapp_count = len(defi_data.get('protocols_used', []))

        # Governance and validation participation
        governance_participation = governance_data.get('participates', False)
        validator_participation = governance_data.get('is_validator', False)

        # Reputation and tenure
        reputation_score = self._calculate_reputation_score(analysis_results)
        ecosystem_tenure = governance_data.get('tenure_months', 0)

        return AlgorandBorrower(
            wallet_address=wallet_address,
            wallet_age_days=wallet_age,
            total_transaction_count=transaction_count,
            total_volume_algo=total_volume,
            asset_count=asset_count,
            nft_count=nft_count,
            smart_contract_interactions=contract_interactions,
            dapp_count=dapp_count,
            governance_participation=governance_participation,
            validator_participation=validator_participation,
            reputation_score=reputation_score,
            ecosystem_tenure_months=ecosystem_tenure,
            metadata={
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'data_sources': list(analysis_results.keys())
            }
        )

    def _build_ecosystem_footprint(
        self,
        analysis_results: Dict[str, Any]
    ) -> EcosystemFootprint:
        """Build ecosystem footprint from analysis results"""

        defi_data = analysis_results.get('defi_analysis', {})
        asset_data = analysis_results.get('asset_analysis', {})
        transaction_data = analysis_results.get('transaction_patterns', {})
        cross_protocol_data = analysis_results.get('cross_protocol', {})

        return EcosystemFootprint(
            defi_protocols_used=defi_data.get('protocols_used', []),
            dex_trading_volume=defi_data.get('dex_volume', 0.0),
            lending_platform_history=defi_data.get('lending_platforms', []),
            yield_farming_participation=defi_data.get('yield_farming', False),
            liquidity_provision_history=defi_data.get('liquidity_provision', False),
            asset_diversity_score=asset_data.get('diversity_score', 0.0),
            stable_asset_percentage=asset_data.get('stable_percentage', 0.0),
            native_algo_percentage=asset_data.get('algo_percentage', 0.0),
            exotic_asset_percentage=asset_data.get('exotic_percentage', 0.0),
            transaction_frequency_score=transaction_data.get('frequency_score', 0.0),
            weekend_activity_ratio=transaction_data.get('weekend_ratio', 0.0),
            time_zone_consistency=transaction_data.get('timezone_consistency', 0.0),
            gas_optimization_score=transaction_data.get('gas_optimization', 0.0),
            high_risk_interactions=defi_data.get('high_risk_count', 0),
            suspicious_activity_flags=defi_data.get('suspicious_flags', []),
            blacklisted_interactions=defi_data.get('blacklisted_count', 0),
            bridge_protocols_used=cross_protocol_data.get('bridge_protocols', []),
            cross_chain_volume=cross_protocol_data.get('cross_chain_volume', 0.0),
            bridge_frequency=cross_protocol_data.get('bridge_frequency', 0),
            algorand_native_percentage=cross_protocol_data.get('algorand_native_pct', 1.0),
            return_frequency_to_algorand=cross_protocol_data.get('return_frequency', 1.0)
        )

    def _build_defi_behavior_pattern(
        self,
        analysis_results: Dict[str, Any]
    ) -> DeFiBehaviorPattern:
        """Build DeFi behavior pattern from analysis results"""

        defi_data = analysis_results.get('defi_analysis', {})
        asset_data = analysis_results.get('asset_analysis', {})

        return DeFiBehaviorPattern(
            average_hold_time_days=defi_data.get('avg_hold_time', 0.0),
            profit_loss_ratio=defi_data.get('profit_loss_ratio', 0.0),
            maximum_drawdown=defi_data.get('max_drawdown', 0.0),
            risk_adjusted_returns=defi_data.get('risk_adjusted_returns', 0.0),
            liquidity_provision_consistency=defi_data.get('lp_consistency', 0.0),
            impermanent_loss_tolerance=defi_data.get('il_tolerance', 0.0),
            staking_behavior_score=defi_data.get('staking_score', 0.0),
            diversification_score=asset_data.get('diversity_score', 0.0),
            leverage_usage_frequency=defi_data.get('leverage_frequency', 0),
            stop_loss_usage=defi_data.get('stop_loss_usage', 0.0),
            position_sizing_consistency=defi_data.get('position_sizing', 0.0),
            protocol_diversity=len(defi_data.get('protocols_used', [])),
            advanced_strategy_usage=defi_data.get('advanced_strategies', False),
            yield_optimization_score=defi_data.get('yield_optimization', 0.0),
            flash_loan_usage=defi_data.get('flash_loan_count', 0)
        )

    def _build_governance_participation(
        self,
        analysis_results: Dict[str, Any]
    ) -> GovernanceParticipation:
        """Build governance participation from analysis results"""

        from ..common.models.decision_models import ParticipationType

        governance_data = analysis_results.get('governance_analysis', {})

        # Determine participation type
        participation_type = ParticipationType.NONE
        if governance_data.get('votes_cast', 0) > 0:
            participation_type = ParticipationType.VOTER
        if governance_data.get('proposals_submitted', 0) > 0:
            participation_type = ParticipationType.PROPOSER
        if governance_data.get('delegation_received', 0) > 1000:
            participation_type = ParticipationType.DELEGATOR

        return GovernanceParticipation(
            participation_type=participation_type,
            votes_cast=governance_data.get('votes_cast', 0),
            proposals_submitted=governance_data.get('proposals_submitted', 0),
            delegation_received_algo=governance_data.get('delegation_received', 0.0),
            delegation_given_algo=governance_data.get('delegation_given', 0.0),
            vote_consistency_score=governance_data.get('vote_consistency', 0.0),
            proposal_quality_score=governance_data.get('proposal_quality', 0.0),
            community_engagement_score=governance_data.get('community_engagement', 0.0),
            participation_start_date=governance_data.get('start_date'),
            continuous_participation_months=governance_data.get('continuous_months', 0),
            governance_rewards_earned=governance_data.get('rewards_earned', 0.0)
        )

    def _build_cross_protocol_activity(
        self,
        analysis_results: Dict[str, Any]
    ) -> CrossProtocolActivity:
        """Build cross-protocol activity from analysis results"""

        cross_protocol_data = analysis_results.get('cross_protocol', {})

        return CrossProtocolActivity(
            bridge_protocols_used=cross_protocol_data.get('bridge_protocols', []),
            cross_chain_volume=cross_protocol_data.get('cross_chain_volume', 0.0),
            bridge_frequency=cross_protocol_data.get('bridge_frequency', 0),
            simultaneous_protocol_usage=cross_protocol_data.get('simultaneous_protocols', 0),
            protocol_migration_patterns=cross_protocol_data.get('migration_patterns', []),
            arbitrage_activity=cross_protocol_data.get('arbitrage_detected', False),
            algorand_native_percentage=cross_protocol_data.get('algorand_native_pct', 1.0),
            external_chain_activity=cross_protocol_data.get('external_activity', {}),
            return_frequency_to_algorand=cross_protocol_data.get('return_frequency', 1.0)
        )

    async def _analyze_governance_participation(
        self,
        wallet_address: str,
        detail_level: str
    ) -> Dict[str, Any]:
        """Analyze governance participation"""
        # Mock implementation - would integrate with governance APIs
        return {
            'participates': True,
            'votes_cast': 15,
            'proposals_submitted': 2,
            'delegation_received': 5000.0,
            'delegation_given': 0.0,
            'vote_consistency': 0.85,
            'proposal_quality': 0.90,
            'community_engagement': 0.75,
            'tenure_months': 18,
            'continuous_months': 12,
            'rewards_earned': 150.0,
            'is_validator': False
        }

    async def _analyze_cross_protocol_activity(
        self,
        wallet_address: str
    ) -> Dict[str, Any]:
        """Analyze cross-protocol and bridge activity"""
        # Mock implementation - would integrate with bridge APIs
        return {
            'bridge_protocols': ['wormhole', 'portal_bridge'],
            'cross_chain_volume': 15000.0,
            'bridge_frequency': 8,
            'simultaneous_protocols': 3,
            'migration_patterns': ['ethereum_to_algorand'],
            'arbitrage_detected': False,
            'algorand_native_pct': 0.75,
            'external_activity': {'ethereum': 0.15, 'polygon': 0.10},
            'return_frequency': 0.85
        }

    async def _detect_behavioral_patterns(
        self,
        wallet_address: str
    ) -> List[Dict[str, Any]]:
        """Detect behavioral patterns using pattern recognition engine"""
        # Would integrate with pattern recognition engine
        return [
            {
                'pattern_type': 'consistent_governance_voter',
                'confidence': 0.85,
                'significance': 0.75,
                'description': 'Consistent governance participation pattern',
                'risk_indicator': False
            },
            {
                'pattern_type': 'defi_yield_optimizer',
                'confidence': 0.70,
                'significance': 0.80,
                'description': 'Active yield optimization strategies',
                'risk_indicator': False
            }
        ]

    def _calculate_reputation_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall reputation score from analysis results"""
        base_score = 50.0

        # Governance participation bonus
        governance_data = analysis_results.get('governance_analysis', {})
        if governance_data.get('participates', False):
            base_score += 15.0

        # DeFi sophistication bonus
        defi_data = analysis_results.get('defi_analysis', {})
        if len(defi_data.get('protocols_used', [])) > 3:
            base_score += 10.0

        # Long-term participation bonus
        if governance_data.get('continuous_months', 0) > 12:
            base_score += 10.0

        # Asset diversity bonus
        asset_data = analysis_results.get('asset_analysis', {})
        if asset_data.get('diversity_score', 0) > 0.7:
            base_score += 10.0

        # Transaction consistency bonus
        transaction_data = analysis_results.get('transaction_patterns', {})
        if transaction_data.get('frequency_score', 0) > 0.8:
            base_score += 5.0

        return min(base_score, 100.0)

    def _calculate_analysis_confidence(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall confidence in analysis results"""
        base_confidence = 0.7

        # Data completeness factor
        expected_components = ['wallet_fundamentals', 'transaction_patterns', 'asset_analysis']
        actual_components = len(analysis_results)
        completeness_factor = min(actual_components / len(expected_components), 1.0)

        # Data quality factor
        quality_factor = 0.0
        for component, data in analysis_results.items():
            if isinstance(data, dict) and data:
                quality_factor += 1
        quality_factor = quality_factor / len(analysis_results) if analysis_results else 0

        # Transaction history depth
        transaction_data = analysis_results.get('transaction_patterns', {})
        transaction_count = transaction_data.get('total_transactions', 0)
        history_factor = min(transaction_count / 100, 1.0)  # 100+ transactions = full confidence

        final_confidence = base_confidence * completeness_factor * quality_factor * history_factor
        return max(min(final_confidence, 0.95), 0.3)  # Between 30% and 95%

    def _assess_data_freshness(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess freshness of data used in analysis"""
        current_time = datetime.utcnow()
        max_age_hours = self.config['analysis']['max_data_age_hours']

        freshness_assessment = {
            'overall_fresh': True,
            'stale_components': [],
            'data_age_hours': 0  # Mock - would be calculated from actual data timestamps
        }

        # In practice, would check timestamps of actual data
        # For now, assume data is fresh
        return freshness_assessment

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Return default configuration
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file loading fails"""
        return {
            'analysis': {
                'default_analysis_period_days': 365,
                'depth_levels': {
                    'basic': 'wallet_fundamentals,transaction_patterns',
                    'standard': 'wallet_fundamentals,transaction_patterns,asset_analysis,governance_basic',
                    'comprehensive': 'wallet_fundamentals,transaction_patterns,asset_analysis,governance_detailed,defi_analysis,nft_analysis,cross_protocol'
                }
            },
            'scoring_weights': {
                'wallet_age': 0.15,
                'transaction_activity': 0.20,
                'asset_diversity': 0.15,
                'governance_participation': 0.20,
                'defi_engagement': 0.20,
                'cross_protocol_activity': 0.10
            }
        }

    async def get_analysis_summary(
        self,
        wallet_address: str
    ) -> Dict[str, Any]:
        """Get a quick analysis summary for dashboard display"""
        try:
            # Perform basic analysis
            result = await self.analyze_complete_ecosystem(
                wallet_address, analysis_depth="basic"
            )

            return {
                'wallet_address': wallet_address,
                'ecosystem_maturity': self._calculate_ecosystem_maturity(result),
                'risk_level': result.risk_profile.overall_risk_level.value,
                'governance_participation': result.borrower_profile.governance_participation,
                'defi_sophistication': len(result.ecosystem_footprint.defi_protocols_used),
                'analysis_confidence': result.confidence_score,
                'last_analyzed': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get analysis summary for {wallet_address}: {e}")
            return {
                'wallet_address': wallet_address,
                'error': str(e),
                'last_analyzed': datetime.utcnow().isoformat()
            }

    def _calculate_ecosystem_maturity(self, result: EcosystemAnalysisResult) -> str:
        """Calculate ecosystem maturity level"""
        score = 0

        # Wallet age factor
        if result.borrower_profile.wallet_age_days > 730:
            score += 30
        elif result.borrower_profile.wallet_age_days > 365:
            score += 20
        elif result.borrower_profile.wallet_age_days > 180:
            score += 10

        # Activity factor
        if result.borrower_profile.total_transaction_count > 500:
            score += 25
        elif result.borrower_profile.total_transaction_count > 100:
            score += 15
        elif result.borrower_profile.total_transaction_count > 50:
            score += 10

        # Governance factor
        if result.borrower_profile.governance_participation:
            score += 25

        # DeFi sophistication factor
        if len(result.ecosystem_footprint.defi_protocols_used) > 5:
            score += 20
        elif len(result.ecosystem_footprint.defi_protocols_used) > 2:
            score += 10

        if score >= 80:
            return "highly_mature"
        elif score >= 60:
            return "mature"
        elif score >= 40:
            return "developing"
        else:
            return "nascent"