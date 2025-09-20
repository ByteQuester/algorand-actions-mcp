"""
Holistic Decision Orchestrator - Master Engine for Algorand-Native Loan Approval

This is the core orchestrator that combines all 5 specialized engines to make
holistic loan approval decisions based on Algorand ecosystem participation
rather than traditional banking metrics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import yaml
import json

from .holistic_scoring import HolisticScorer
from .approval_logic import ApprovalLogic
from .conditions_generator import ConditionsGenerator
from .alternative_proposer import AlternativeProposer
from .monitoring_scheduler import MonitoringScheduler


class DecisionConfidence(Enum):
    """Decision confidence levels"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class LoanDecision(Enum):
    """Loan decision outcomes"""
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class BorrowerProfile:
    """Complete borrower profile aggregated from all engines"""
    address: str
    ecosystem_score: float
    ecosystem_confidence: float
    ecosystem_data: Dict[str, Any]

    defi_score: float
    defi_confidence: float
    defi_data: Dict[str, Any]

    collateral_score: float
    collateral_confidence: float
    collateral_data: Dict[str, Any]

    governance_score: float
    governance_confidence: float
    governance_data: Dict[str, Any]

    risk_score: float
    risk_confidence: float
    risk_data: Dict[str, Any]

    timestamp: datetime
    data_completeness: float


@dataclass
class LoanApplication:
    """Loan application with complete context"""
    application_id: str
    borrower_address: str
    loan_amount: float
    requested_term: int  # days
    collateral_assets: List[Dict[str, Any]]
    purpose: str
    timestamp: datetime

    # Additional context
    market_conditions: Dict[str, Any]
    network_health: Dict[str, Any]


@dataclass
class HolisticDecision:
    """Complete holistic decision output"""
    application_id: str
    decision: LoanDecision
    confidence: DecisionConfidence
    overall_score: float

    # Individual scores
    ecosystem_score: float
    defi_score: float
    collateral_score: float
    governance_score: float
    risk_score: float

    # Decision rationale
    primary_factors: List[str]
    risk_factors: List[str]
    positive_factors: List[str]

    # Loan terms if approved
    approved_amount: Optional[float]
    interest_rate: Optional[float]
    loan_term: Optional[int]
    ltv_ratio: Optional[float]
    conditions: List[str]

    # Monitoring requirements
    monitoring_frequency: str
    monitoring_parameters: List[str]

    # Alternatives if rejected
    alternatives: List[Dict[str, Any]]

    # Metadata
    decision_timestamp: datetime
    expires_at: datetime
    processing_time: float


class HolisticDecisionOrchestrator:
    """
    Master orchestrator for holistic loan approval decisions.

    Combines ecosystem analysis, DeFi behavior, collateral intelligence,
    governance reputation, and network risk monitoring into unified decisions.
    """

    def __init__(self, config_path: str = None):
        """Initialize the orchestrator with configuration"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Initialize components
        self.scorer = HolisticScorer(self.config)
        self.approval_logic = ApprovalLogic(self.config)
        self.conditions_generator = ConditionsGenerator(self.config)
        self.alternative_proposer = AlternativeProposer(self.config)
        self.monitoring_scheduler = MonitoringScheduler(self.config)

        # Engine clients (would be actual API clients in production)
        self.ecosystem_engine = None
        self.defi_engine = None
        self.collateral_engine = None
        self.governance_engine = None
        self.risk_engine = None

        self.logger.info("Holistic Decision Orchestrator initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not config_path:
            config_path = "config/config.yaml"

        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            # Default configuration
            return {
                'engine_weights': {
                    'ecosystem_analysis': 0.30,
                    'defi_behavior': 0.25,
                    'collateral_intelligence': 0.20,
                    'governance_reputation': 0.15,
                    'network_risk_monitoring': 0.10
                },
                'approval_thresholds': {
                    'excellent': 0.85,
                    'good': 0.70,
                    'fair': 0.55,
                    'poor': 0.40,
                    'reject': 0.39
                },
                'confidence_requirements': {
                    'minimum_confidence': 0.75,
                    'high_confidence': 0.90
                }
            }

    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging"""
        logger = logging.getLogger("holistic_orchestrator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def process_loan_application(
        self,
        application: LoanApplication
    ) -> HolisticDecision:
        """
        Process a complete loan application through holistic analysis.

        This is the main entry point that orchestrates all engines and
        produces a final decision.
        """
        start_time = datetime.now()

        self.logger.info(
            f"Processing loan application {application.application_id} "
            f"for borrower {application.borrower_address}"
        )

        try:
            # Step 1: Gather borrower profile from all engines
            borrower_profile = await self._build_borrower_profile(
                application.borrower_address
            )

            # Step 2: Calculate holistic scores
            holistic_scores = await self.scorer.calculate_holistic_scores(
                borrower_profile, application
            )

            # Step 3: Make approval decision
            decision_result = await self.approval_logic.make_decision(
                holistic_scores, application, borrower_profile
            )

            # Step 4: Generate loan conditions if approved
            conditions = []
            if decision_result['decision'] in [LoanDecision.APPROVED, LoanDecision.CONDITIONALLY_APPROVED]:
                conditions = await self.conditions_generator.generate_conditions(
                    holistic_scores, application, borrower_profile
                )

            # Step 5: Generate alternatives if rejected
            alternatives = []
            if decision_result['decision'] == LoanDecision.REJECTED:
                alternatives = await self.alternative_proposer.propose_alternatives(
                    holistic_scores, application, borrower_profile
                )

            # Step 6: Set up monitoring requirements
            monitoring = await self.monitoring_scheduler.schedule_monitoring(
                decision_result, application, borrower_profile
            )

            # Step 7: Compile final decision
            processing_time = (datetime.now() - start_time).total_seconds()

            decision = HolisticDecision(
                application_id=application.application_id,
                decision=decision_result['decision'],
                confidence=decision_result['confidence'],
                overall_score=holistic_scores['overall_score'],

                ecosystem_score=holistic_scores['ecosystem_score'],
                defi_score=holistic_scores['defi_score'],
                collateral_score=holistic_scores['collateral_score'],
                governance_score=holistic_scores['governance_score'],
                risk_score=holistic_scores['risk_score'],

                primary_factors=decision_result['primary_factors'],
                risk_factors=decision_result['risk_factors'],
                positive_factors=decision_result['positive_factors'],

                approved_amount=decision_result.get('approved_amount'),
                interest_rate=decision_result.get('interest_rate'),
                loan_term=decision_result.get('loan_term'),
                ltv_ratio=decision_result.get('ltv_ratio'),
                conditions=conditions,

                monitoring_frequency=monitoring['frequency'],
                monitoring_parameters=monitoring['parameters'],

                alternatives=alternatives,

                decision_timestamp=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7),
                processing_time=processing_time
            )

            self.logger.info(
                f"Decision completed for {application.application_id}: "
                f"{decision.decision.value} with {decision.confidence.value} confidence"
            )

            # Store decision for audit trail
            await self._store_decision(decision, borrower_profile)

            return decision

        except Exception as e:
            self.logger.error(
                f"Error processing application {application.application_id}: {str(e)}"
            )

            # Return error decision
            return HolisticDecision(
                application_id=application.application_id,
                decision=LoanDecision.REQUIRES_REVIEW,
                confidence=DecisionConfidence.VERY_LOW,
                overall_score=0.0,
                ecosystem_score=0.0,
                defi_score=0.0,
                collateral_score=0.0,
                governance_score=0.0,
                risk_score=0.0,
                primary_factors=[f"Processing error: {str(e)}"],
                risk_factors=["System error"],
                positive_factors=[],
                approved_amount=None,
                interest_rate=None,
                loan_term=None,
                ltv_ratio=None,
                conditions=[],
                monitoring_frequency="manual_review",
                monitoring_parameters=[],
                alternatives=[],
                decision_timestamp=datetime.now(),
                expires_at=datetime.now() + timedelta(days=1),
                processing_time=(datetime.now() - start_time).total_seconds()
            )

    async def _build_borrower_profile(self, address: str) -> BorrowerProfile:
        """
        Build comprehensive borrower profile by calling all 5 engines.

        This aggregates data from:
        - Ecosystem Analysis Engine
        - DeFi Behavior Engine
        - Collateral Intelligence Engine
        - Governance Reputation Engine
        - Network Risk Monitoring Engine
        """
        self.logger.debug(f"Building borrower profile for {address}")

        # Execute all engine calls in parallel for efficiency
        results = await asyncio.gather(
            self._get_ecosystem_analysis(address),
            self._get_defi_behavior(address),
            self._get_collateral_intelligence(address),
            self._get_governance_reputation(address),
            self._get_network_risk_assessment(address),
            return_exceptions=True
        )

        # Process results and handle any failures
        ecosystem_result = results[0] if not isinstance(results[0], Exception) else self._default_engine_result()
        defi_result = results[1] if not isinstance(results[1], Exception) else self._default_engine_result()
        collateral_result = results[2] if not isinstance(results[2], Exception) else self._default_engine_result()
        governance_result = results[3] if not isinstance(results[3], Exception) else self._default_engine_result()
        risk_result = results[4] if not isinstance(results[4], Exception) else self._default_engine_result()

        # Calculate data completeness
        completeness_scores = [
            ecosystem_result['confidence'],
            defi_result['confidence'],
            collateral_result['confidence'],
            governance_result['confidence'],
            risk_result['confidence']
        ]
        data_completeness = sum(completeness_scores) / len(completeness_scores)

        return BorrowerProfile(
            address=address,
            ecosystem_score=ecosystem_result['score'],
            ecosystem_confidence=ecosystem_result['confidence'],
            ecosystem_data=ecosystem_result['data'],

            defi_score=defi_result['score'],
            defi_confidence=defi_result['confidence'],
            defi_data=defi_result['data'],

            collateral_score=collateral_result['score'],
            collateral_confidence=collateral_result['confidence'],
            collateral_data=collateral_result['data'],

            governance_score=governance_result['score'],
            governance_confidence=governance_result['confidence'],
            governance_data=governance_result['data'],

            risk_score=risk_result['score'],
            risk_confidence=risk_result['confidence'],
            risk_data=risk_result['data'],

            timestamp=datetime.now(),
            data_completeness=data_completeness
        )

    async def _get_ecosystem_analysis(self, address: str) -> Dict[str, Any]:
        """Get ecosystem analysis from dedicated engine"""
        # In production, this would call the actual ecosystem analysis engine
        # For now, return mock data that represents real analysis

        # Simulate API call delay
        await asyncio.sleep(0.1)

        return {
            'score': 0.75,  # Strong ecosystem participation
            'confidence': 0.90,
            'data': {
                'wallet_age_days': 456,
                'total_transactions': 1247,
                'asset_diversity': 12,
                'dapp_interactions': 8,
                'avg_balance_algo': 15750,
                'smart_contract_usage': True,
                'defi_protocols_used': ['Tinyman', 'Pact', 'AlgoFi'],
                'nft_holdings': 23,
                'participation_consistency': 0.85
            }
        }

    async def _get_defi_behavior(self, address: str) -> Dict[str, Any]:
        """Get DeFi behavior analysis from dedicated engine"""
        await asyncio.sleep(0.1)

        return {
            'score': 0.68,
            'confidence': 0.85,
            'data': {
                'defi_experience_months': 18,
                'protocols_used': 5,
                'liquidity_provision': True,
                'yield_farming_active': True,
                'risk_management_score': 0.72,
                'impermanent_loss_exposure': 0.15,
                'leverage_usage': False,
                'cross_protocol_arbitrage': True,
                'avg_position_size': 5500
            }
        }

    async def _get_collateral_intelligence(self, address: str) -> Dict[str, Any]:
        """Get collateral intelligence from dedicated engine"""
        await asyncio.sleep(0.1)

        return {
            'score': 0.82,
            'confidence': 0.95,
            'data': {
                'total_collateral_value': 25000,
                'asset_quality_score': 0.88,
                'diversification_score': 0.75,
                'liquidity_score': 0.90,
                'volatility_score': 0.65,
                'correlation_risk': 0.30,
                'liquidation_risk': 0.15,
                'assets': [
                    {'asset': 'ALGO', 'amount': 15000, 'quality': 0.95},
                    {'asset': 'USDC', 'amount': 8000, 'quality': 0.98},
                    {'asset': 'OPUL', 'amount': 2000, 'quality': 0.70}
                ]
            }
        }

    async def _get_governance_reputation(self, address: str) -> Dict[str, Any]:
        """Get governance reputation from dedicated engine"""
        await asyncio.sleep(0.1)

        return {
            'score': 0.58,
            'confidence': 0.80,
            'data': {
                'governance_participation': True,
                'voting_history': 12,
                'consensus_participation': True,
                'community_engagement_score': 0.65,
                'development_contributions': False,
                'forum_activity': 'moderate',
                'proposal_submissions': 0,
                'delegation_received': 1500,
                'reputation_age_days': 280
            }
        }

    async def _get_network_risk_assessment(self, address: str) -> Dict[str, Any]:
        """Get network risk assessment from dedicated engine"""
        await asyncio.sleep(0.1)

        return {
            'score': 0.78,  # Lower score means lower risk
            'confidence': 0.88,
            'data': {
                'network_health': 0.92,
                'systemic_risk_level': 'low',
                'market_volatility': 0.25,
                'protocol_risk_exposure': 0.20,
                'concentration_risk': 0.15,
                'counterparty_risk': 0.10,
                'technical_risk': 0.05,
                'regulatory_risk': 0.30
            }
        }

    def _default_engine_result(self) -> Dict[str, Any]:
        """Default result when engine call fails"""
        return {
            'score': 0.5,
            'confidence': 0.0,
            'data': {'error': 'Engine unavailable'}
        }

    async def _store_decision(
        self,
        decision: HolisticDecision,
        profile: BorrowerProfile
    ) -> None:
        """Store decision and profile for audit trail"""
        # In production, this would store to a database
        audit_record = {
            'decision': decision.__dict__,
            'profile': profile.__dict__,
            'timestamp': datetime.now().isoformat()
        }

        self.logger.debug(f"Storing audit record for {decision.application_id}")
        # Implementation would store to persistent storage

    async def get_decision_status(self, application_id: str) -> Dict[str, Any]:
        """Get current status of a loan decision"""
        # Implementation would query decision storage
        return {
            'application_id': application_id,
            'status': 'processed',
            'timestamp': datetime.now()
        }

    async def update_monitoring_data(
        self,
        application_id: str,
        monitoring_data: Dict[str, Any]
    ) -> None:
        """Update ongoing monitoring data for active loans"""
        self.logger.info(f"Updating monitoring data for {application_id}")
        # Implementation would update monitoring records

    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get decision statistics and performance metrics"""
        return {
            'total_decisions': 0,
            'approval_rate': 0.0,
            'avg_processing_time': 0.0,
            'confidence_distribution': {},
            'engine_performance': {}
        }