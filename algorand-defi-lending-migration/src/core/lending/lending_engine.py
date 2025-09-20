"""
Pure Lending Engine - NO configuration dependencies
All configuration injected via constructor
"""

import uuid
import asyncio
from typing import Dict, Any, Optional, List, Protocol
from datetime import datetime

from .models import LoanRequest, LoanResult, LoanStatus, LoanTerms, AgentResult, CollateralType
from .agents import NegotiationAgent, LiquidityAgent, ExecutionAgent

class BlockchainProvider(Protocol):
    """Protocol for blockchain operations - dependency injection"""
    async def get_account_balance(self, address: str) -> Dict[str, Any]: ...
    async def create_transaction(self, **kwargs) -> Dict[str, Any]: ...
    async def submit_transaction(self, transaction_data: Dict[str, Any]) -> str: ...

class LendingEngine:
    """
    Pure lending business logic engine

    NO hardcoded configuration
    NO environment variables
    NO production dependencies

    All external dependencies injected via constructor
    """

    def __init__(
        self,
        blockchain_provider: BlockchainProvider,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize lending engine with injected dependencies

        Args:
            blockchain_provider: Injected blockchain client
            config: Runtime configuration (optional)
        """
        self.blockchain_provider = blockchain_provider
        self.config = config or {}

        # Initialize agents with injected config
        agent_config = self.config.get('agents', {})

        self.negotiation_agent = NegotiationAgent(agent_config.get('negotiation', {}))
        self.liquidity_agent = LiquidityAgent(agent_config.get('liquidity', {}))
        self.execution_agent = ExecutionAgent(agent_config.get('execution', {}))

        # Runtime state (in-memory by default)
        self.loans: Dict[str, LoanResult] = {}

    async def process_loan_request(self, request: LoanRequest) -> LoanResult:
        """
        Process loan request through A2A workflow

        Pure business logic - no side effects except through injected dependencies
        """
        loan_id = str(uuid.uuid4())

        try:
            # Validate request
            validation_errors = request.validate()
            if validation_errors:
                return LoanResult(
                    loan_id=loan_id,
                    status=LoanStatus.CANCELLED,
                    terms=None,
                    transaction_id=None,
                    error_message=f"Validation failed: {'; '.join(validation_errors)}",
                    created_at=datetime.utcnow()
                )

            # Step 1: Liquidity discovery
            liquidity_result = await self._discover_liquidity(request)
            if not liquidity_result.success:
                return LoanResult(
                    loan_id=loan_id,
                    status=LoanStatus.CANCELLED,
                    terms=None,
                    transaction_id=None,
                    error_message=f"Liquidity discovery failed: {liquidity_result.error}",
                    created_at=datetime.utcnow()
                )

            # Step 2: Term negotiation
            negotiation_result = await self._negotiate_terms(request, liquidity_result.data)
            if not negotiation_result.success:
                return LoanResult(
                    loan_id=loan_id,
                    status=LoanStatus.CANCELLED,
                    terms=None,
                    transaction_id=None,
                    error_message=f"Negotiation failed: {negotiation_result.error}",
                    created_at=datetime.utcnow()
                )

            # Step 3: Execution preparation
            execution_result = await self._prepare_execution(loan_id, negotiation_result.data)
            if not execution_result.success:
                return LoanResult(
                    loan_id=loan_id,
                    status=LoanStatus.CANCELLED,
                    terms=None,
                    transaction_id=None,
                    error_message=f"Execution preparation failed: {execution_result.error}",
                    created_at=datetime.utcnow()
                )

            # Create loan terms
            terms_data = negotiation_result.data
            terms = LoanTerms(
                amount=terms_data.get('amount', request.amount_micro_algos),
                interest_rate=terms_data.get('interest_rate', request.max_interest_rate),
                duration_days=request.duration_days,
                collateral_amount=terms_data.get('collateral_amount', 0),
                collateral_type=request.collateral_type,
                lender=terms_data.get('lender', request.lender_address),
                borrower=request.borrower_address
            )

            # Create successful result
            result = LoanResult(
                loan_id=loan_id,
                status=LoanStatus.APPROVED,
                terms=terms,
                transaction_id=execution_result.data.get('transaction_id'),
                error_message=None,
                created_at=datetime.utcnow()
            )

            # Store in memory (or injected storage)
            self.loans[loan_id] = result

            return result

        except Exception as e:
            return LoanResult(
                loan_id=loan_id,
                status=LoanStatus.CANCELLED,
                terms=None,
                transaction_id=None,
                error_message=f"Unexpected error: {str(e)}",
                created_at=datetime.utcnow()
            )

    async def get_loan_status(self, loan_id: str) -> Optional[LoanResult]:
        """Get loan status - pure lookup"""
        return self.loans.get(loan_id)

    async def get_account_balance(self, address: str) -> Dict[str, Any]:
        """Get account balance via injected blockchain provider"""
        try:
            return await self.blockchain_provider.get_account_balance(address)
        except Exception as e:
            # Return fallback data instead of failing
            return {
                "address": address,
                "algo_balance_micro": 0,
                "algo_balance": 0.0,
                "error": str(e)
            }

    # Private methods for agent orchestration
    async def _discover_liquidity(self, request: LoanRequest) -> AgentResult:
        """Discover available liquidity"""
        try:
            # Get account balances via injected provider
            if request.lender_address:
                lender_balance = await self.blockchain_provider.get_account_balance(request.lender_address)
            else:
                # Let liquidity agent find lenders
                lender_balance = None

            borrower_balance = await self.blockchain_provider.get_account_balance(request.borrower_address)

            # Process through liquidity agent
            result = await self.liquidity_agent.process({
                'loan_request': request.__dict__,
                'lender_balance': lender_balance,
                'borrower_balance': borrower_balance
            })

            return AgentResult(
                agent_type="liquidity",
                success=True,
                data=result
            )

        except Exception as e:
            return AgentResult(
                agent_type="liquidity",
                success=False,
                data={},
                error=str(e)
            )

    async def _negotiate_terms(self, request: LoanRequest, liquidity_data: Dict[str, Any]) -> AgentResult:
        """Negotiate loan terms"""
        try:
            result = await self.negotiation_agent.process({
                'loan_request': request.__dict__,
                'liquidity_data': liquidity_data
            })

            return AgentResult(
                agent_type="negotiation",
                success=True,
                data=result
            )

        except Exception as e:
            return AgentResult(
                agent_type="negotiation",
                success=False,
                data={},
                error=str(e)
            )

    async def _prepare_execution(self, loan_id: str, terms_data: Dict[str, Any]) -> AgentResult:
        """Prepare loan execution"""
        try:
            result = await self.execution_agent.process({
                'loan_id': loan_id,
                'terms': terms_data
            })

            return AgentResult(
                agent_type="execution",
                success=True,
                data=result
            )

        except Exception as e:
            return AgentResult(
                agent_type="execution",
                success=False,
                data={},
                error=str(e)
            )