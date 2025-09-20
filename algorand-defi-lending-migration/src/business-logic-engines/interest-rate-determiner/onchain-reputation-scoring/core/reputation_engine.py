"""
Algorand On-chain Reputation Engine
Combines wallet behavior and governance participation for comprehensive reputation scoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import yaml

from .wallet_analyzer import WalletAnalyzer, WalletScore
from .governance_scorer import GovernanceScorer, GovernanceScore


@dataclass
class ReputationComponents:
    """Individual reputation component scores"""
    wallet_score: WalletScore
    governance_score: GovernanceScore
    combined_score: float
    risk_tier: str
    rate_adjustment: float


@dataclass
class ReputationReport:
    """Comprehensive reputation analysis report"""
    address: str
    overall_reputation_score: float
    risk_tier: str
    rate_adjustment: float
    components: ReputationComponents
    recommendations: List[str]
    analysis_timestamp: datetime
    next_review_date: datetime


@dataclass
class PortfolioReputation:
    """Reputation analysis for multiple addresses"""
    addresses: List[str]
    individual_scores: Dict[str, ReputationReport]
    portfolio_average: float
    risk_distribution: Dict[str, int]
    recommendations: List[str]


class ReputationEngine:
    """Main engine for Algorand on-chain reputation scoring"""

    def __init__(self, config_path: str = None, config_dict: Dict = None):
        """Initialize with configuration file or dictionary"""
        if config_dict:
            self.config = config_dict
        else:
            config_path = config_path or "/home/mpo/algorand-showcase/algorand-lending-ecosystem/business-logic-engines/interest-rate-determiner/onchain-reputation-scoring/config/config.yaml"
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)

        self.logger = logging.getLogger(__name__)

        # Initialize component analyzers
        self.wallet_analyzer = WalletAnalyzer(self.config)
        self.governance_scorer = GovernanceScorer(self.config)

        # Reputation tiers from config
        self.reputation_tiers = self.config['reputation_tiers']

    async def analyze_reputation(self, wallet_address: str) -> ReputationReport:
        """Perform comprehensive reputation analysis for a wallet"""
        try:
            self.logger.info(f"Starting reputation analysis for: {wallet_address}")

            # Run parallel analysis
            wallet_analysis, governance_analysis = await asyncio.gather(
                self.wallet_analyzer.analyze_wallet(wallet_address),
                self.governance_scorer.score_governance_participation(wallet_address),
                return_exceptions=True
            )

            # Handle analysis errors
            if isinstance(wallet_analysis, Exception):
                self.logger.error(f"Wallet analysis failed: {wallet_analysis}")
                wallet_analysis = self._create_default_wallet_score(wallet_address)

            if isinstance(governance_analysis, Exception):
                self.logger.error(f"Governance analysis failed: {governance_analysis}")
                governance_analysis = self._create_default_governance_score(wallet_address)

            # Calculate combined reputation score
            combined_score = self._calculate_combined_score(wallet_analysis, governance_analysis)

            # Determine risk tier and rate adjustment
            risk_tier, rate_adjustment = self._determine_risk_tier(combined_score)

            # Create reputation components
            components = ReputationComponents(
                wallet_score=wallet_analysis,
                governance_score=governance_analysis,
                combined_score=combined_score,
                risk_tier=risk_tier,
                rate_adjustment=rate_adjustment
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(components)

            # Calculate next review date
            next_review = self._calculate_next_review_date(risk_tier)

            return ReputationReport(
                address=wallet_address,
                overall_reputation_score=combined_score,
                risk_tier=risk_tier,
                rate_adjustment=rate_adjustment,
                components=components,
                recommendations=recommendations,
                analysis_timestamp=datetime.utcnow(),
                next_review_date=next_review
            )

        except Exception as e:
            self.logger.error(f"Error in reputation analysis for {wallet_address}: {e}")
            raise

    async def analyze_portfolio_reputation(self, wallet_addresses: List[str]) -> PortfolioReputation:
        """Analyze reputation for multiple wallets (portfolio view)"""
        try:
            self.logger.info(f"Analyzing portfolio reputation for {len(wallet_addresses)} addresses")

            # Analyze all addresses in parallel (with concurrency limit)
            semaphore = asyncio.Semaphore(10)  # Limit concurrent API calls

            async def analyze_with_semaphore(address):
                async with semaphore:
                    return await self.analyze_reputation(address)

            # Run parallel analysis
            individual_reports = await asyncio.gather(
                *[analyze_with_semaphore(addr) for addr in wallet_addresses],
                return_exceptions=True
            )

            # Process results
            individual_scores = {}
            valid_scores = []
            risk_distribution = {
                'excellent': 0,
                'good': 0,
                'average': 0,
                'poor': 0,
                'very_poor': 0
            }

            for i, report in enumerate(individual_reports):
                address = wallet_addresses[i]

                if isinstance(report, Exception):
                    self.logger.error(f"Error analyzing {address}: {report}")
                    # Create minimal report for failed analysis
                    report = self._create_default_reputation_report(address)

                individual_scores[address] = report
                valid_scores.append(report.overall_reputation_score)
                risk_distribution[report.risk_tier] += 1

            # Calculate portfolio statistics
            portfolio_average = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

            # Generate portfolio recommendations
            portfolio_recommendations = self._generate_portfolio_recommendations(
                individual_scores, portfolio_average, risk_distribution
            )

            return PortfolioReputation(
                addresses=wallet_addresses,
                individual_scores=individual_scores,
                portfolio_average=portfolio_average,
                risk_distribution=risk_distribution,
                recommendations=portfolio_recommendations
            )

        except Exception as e:
            self.logger.error(f"Error in portfolio reputation analysis: {e}")
            raise

    def _calculate_combined_score(self, wallet_score: WalletScore, governance_score: GovernanceScore) -> float:
        """Calculate combined reputation score from components"""
        # Weight configuration (governance participation is highly valued in Algorand)
        wallet_weight = 0.6
        governance_weight = 0.4

        combined = (
            wallet_score.overall_score * wallet_weight +
            governance_score.overall_score * governance_weight
        )

        return min(1.0, max(0.0, combined))

    def _determine_risk_tier(self, score: float) -> Tuple[str, float]:
        """Determine risk tier and rate adjustment based on score"""
        for tier, config in self.reputation_tiers.items():
            if score >= config['min_score']:
                return tier, config['rate_adjustment']

        # Default to worst tier
        return 'very_poor', self.reputation_tiers['very_poor']['rate_adjustment']

    def _generate_recommendations(self, components: ReputationComponents) -> List[str]:
        """Generate personalized recommendations for improving reputation"""
        recommendations = []

        wallet_score = components.wallet_score
        governance_score = components.governance_score

        # Wallet-based recommendations
        if wallet_score.transaction_score < 0.7:
            recommendations.append(
                "Increase transaction consistency by maintaining regular on-chain activity"
            )

        if wallet_score.balance_score < 0.7:
            recommendations.append(
                "Improve balance stability by maintaining higher ALGO balances with lower volatility"
            )

        if wallet_score.asset_score < 0.7:
            recommendations.append(
                "Diversify ASA holdings with quality tokens from the Algorand ecosystem"
            )

        if wallet_score.defi_score < 0.7:
            recommendations.append(
                "Increase DeFi engagement by participating in protocols like Tinyman, AlgoFi, or Folks Finance"
            )

        # Governance-based recommendations
        if governance_score.participation_score < 0.7:
            recommendations.append(
                "Participate in Algorand governance by registering and committing ALGO tokens"
            )

        if governance_score.voting_consistency_score < 0.7:
            recommendations.append(
                "Improve voting consistency by participating in all governance proposals"
            )

        if governance_score.staking_commitment_score < 0.7:
            recommendations.append(
                "Increase ALGO commitment amount in governance to demonstrate long-term alignment"
            )

        # Overall recommendations
        if components.combined_score < 0.5:
            recommendations.append(
                "Focus on building on-chain reputation through consistent governance participation and DeFi activity"
            )

        if not recommendations:
            recommendations.append("Excellent on-chain reputation! Continue current practices.")

        return recommendations

    def _generate_portfolio_recommendations(
        self, individual_scores: Dict[str, ReputationReport],
        portfolio_average: float,
        risk_distribution: Dict[str, int]
    ) -> List[str]:
        """Generate portfolio-level recommendations"""
        recommendations = []

        total_addresses = len(individual_scores)

        # Risk distribution analysis
        high_risk_count = risk_distribution['poor'] + risk_distribution['very_poor']
        high_risk_ratio = high_risk_count / total_addresses

        if high_risk_ratio > 0.3:
            recommendations.append(
                f"Portfolio has {high_risk_ratio:.1%} high-risk addresses - consider risk mitigation strategies"
            )

        if portfolio_average < 0.5:
            recommendations.append(
                "Overall portfolio reputation is below average - focus on improving governance participation"
            )

        # Address-specific recommendations
        excellent_count = risk_distribution['excellent']
        if excellent_count > 0:
            recommendations.append(
                f"{excellent_count} addresses have excellent reputation - consider preferential terms"
            )

        # Governance participation insights
        low_governance_count = sum(1 for report in individual_scores.values()
                                 if report.components.governance_score.overall_score < 0.3)

        if low_governance_count > total_addresses * 0.5:
            recommendations.append(
                "Majority of addresses have low governance participation - encourage community engagement"
            )

        return recommendations

    def _calculate_next_review_date(self, risk_tier: str) -> datetime:
        """Calculate when next reputation review should occur"""
        review_intervals = {
            'excellent': 90,    # 3 months
            'good': 60,         # 2 months
            'average': 30,      # 1 month
            'poor': 14,         # 2 weeks
            'very_poor': 7      # 1 week
        }

        days = review_intervals.get(risk_tier, 30)
        return datetime.utcnow() + timedelta(days=days)

    def _create_default_wallet_score(self, address: str) -> WalletScore:
        """Create default wallet score for failed analysis"""
        return WalletScore(
            address=address,
            transaction_score=0.0,
            balance_score=0.0,
            asset_score=0.0,
            defi_score=0.0,
            longevity_score=0.0,
            overall_score=0.0,
            analysis_timestamp=datetime.utcnow()
        )

    def _create_default_governance_score(self, address: str) -> GovernanceScore:
        """Create default governance score for failed analysis"""
        from .governance_scorer import GovernanceHistory

        default_history = GovernanceHistory(
            total_periods=0,
            participated_periods=0,
            participation_rate=0.0,
            avg_algo_committed=0.0,
            total_votes_cast=0,
            avg_voting_consistency=0.0,
            recent_activity=False
        )

        return GovernanceScore(
            address=address,
            participation_score=0.0,
            voting_consistency_score=0.0,
            staking_commitment_score=0.0,
            engagement_score=0.0,
            overall_score=0.0,
            governance_history=default_history,
            analysis_timestamp=datetime.utcnow()
        )

    def _create_default_reputation_report(self, address: str) -> ReputationReport:
        """Create default reputation report for failed analysis"""
        wallet_score = self._create_default_wallet_score(address)
        governance_score = self._create_default_governance_score(address)

        components = ReputationComponents(
            wallet_score=wallet_score,
            governance_score=governance_score,
            combined_score=0.0,
            risk_tier='very_poor',
            rate_adjustment=0.5
        )

        return ReputationReport(
            address=address,
            overall_reputation_score=0.0,
            risk_tier='very_poor',
            rate_adjustment=0.5,
            components=components,
            recommendations=["Analysis failed - manual review required"],
            analysis_timestamp=datetime.utcnow(),
            next_review_date=datetime.utcnow() + timedelta(days=1)
        )

    async def get_reputation_summary(self, addresses: List[str]) -> Dict:
        """Get high-level reputation summary for multiple addresses"""
        try:
            portfolio = await self.analyze_portfolio_reputation(addresses)

            return {
                'total_addresses': len(addresses),
                'portfolio_average_score': portfolio.portfolio_average,
                'risk_distribution': portfolio.risk_distribution,
                'high_risk_addresses': portfolio.risk_distribution['poor'] + portfolio.risk_distribution['very_poor'],
                'excellent_addresses': portfolio.risk_distribution['excellent'],
                'recommendations_count': len(portfolio.recommendations),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error generating reputation summary: {e}")
            return {
                'error': str(e),
                'total_addresses': len(addresses),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }

    def export_reputation_report(self, report: ReputationReport, format: str = 'json') -> str:
        """Export reputation report in specified format"""
        if format == 'json':
            return json.dumps({
                'address': report.address,
                'overall_score': report.overall_reputation_score,
                'risk_tier': report.risk_tier,
                'rate_adjustment': report.rate_adjustment,
                'wallet_score': {
                    'transaction_score': report.components.wallet_score.transaction_score,
                    'balance_score': report.components.wallet_score.balance_score,
                    'asset_score': report.components.wallet_score.asset_score,
                    'defi_score': report.components.wallet_score.defi_score,
                    'longevity_score': report.components.wallet_score.longevity_score,
                    'overall_score': report.components.wallet_score.overall_score
                },
                'governance_score': {
                    'participation_score': report.components.governance_score.participation_score,
                    'voting_consistency_score': report.components.governance_score.voting_consistency_score,
                    'staking_commitment_score': report.components.governance_score.staking_commitment_score,
                    'engagement_score': report.components.governance_score.engagement_score,
                    'overall_score': report.components.governance_score.overall_score
                },
                'recommendations': report.recommendations,
                'analysis_timestamp': report.analysis_timestamp.isoformat(),
                'next_review_date': report.next_review_date.isoformat()
            }, indent=2)

        elif format == 'yaml':
            import yaml
            return yaml.dump({
                'address': report.address,
                'overall_score': float(report.overall_reputation_score),
                'risk_tier': report.risk_tier,
                'rate_adjustment': float(report.rate_adjustment),
                'recommendations': report.recommendations,
                'analysis_timestamp': report.analysis_timestamp.isoformat()
            })

        else:
            raise ValueError(f"Unsupported format: {format}")

    async def batch_reputation_analysis(self, addresses: List[str], output_file: str = None) -> Dict:
        """Perform batch reputation analysis with optional file output"""
        try:
            portfolio = await self.analyze_portfolio_reputation(addresses)

            # Prepare batch results
            batch_results = {
                'summary': {
                    'total_addresses': len(addresses),
                    'portfolio_average': portfolio.portfolio_average,
                    'risk_distribution': portfolio.risk_distribution,
                    'analysis_timestamp': datetime.utcnow().isoformat()
                },
                'individual_results': {}
            }

            for address, report in portfolio.individual_scores.items():
                batch_results['individual_results'][address] = {
                    'overall_score': report.overall_reputation_score,
                    'risk_tier': report.risk_tier,
                    'rate_adjustment': report.rate_adjustment,
                    'recommendations': report.recommendations
                }

            # Save to file if requested
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(batch_results, f, indent=2)

            return batch_results

        except Exception as e:
            self.logger.error(f"Error in batch reputation analysis: {e}")
            raise