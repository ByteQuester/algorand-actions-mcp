"""
Pure agent logic - NO external dependencies
Configuration injected via constructor
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base agent with injected configuration"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize with injected config - NO environment variables"""
        self.config = config

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results"""
        pass

class NegotiationAgent(BaseAgent):
    """Agent for negotiating loan terms"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Negotiate loan terms based on request and liquidity data

        Pure business logic - no external calls
        """
        loan_request = input_data.get('loan_request', {})
        liquidity_data = input_data.get('liquidity_data', {})

        # Extract parameters
        amount = loan_request.get('amount_micro_algos', 0)
        max_interest_rate = loan_request.get('max_interest_rate', 0)
        duration_days = loan_request.get('duration_days', 30)
        collateral_type = loan_request.get('collateral_type', 'ALGO')

        # Business logic for term negotiation
        negotiated_terms = {
            'amount': amount,
            'interest_rate': self._calculate_interest_rate(
                amount, duration_days, max_interest_rate
            ),
            'duration_days': duration_days,
            'collateral_amount': self._calculate_collateral(amount, collateral_type),
            'lender': liquidity_data.get('best_lender', 'MOCK_LENDER_ADDRESS'),
            'borrower': loan_request.get('borrower_address'),
            'collateral_type': collateral_type
        }

        # Simulate negotiation rounds
        negotiation_rounds = []
        for round_num in range(1, 4):
            negotiation_rounds.append({
                'round': round_num,
                'proposal': f"Round {round_num} proposal",
                'status': 'accepted' if round_num == 3 else 'counter-proposal'
            })

        return {
            'terms': negotiated_terms,
            'negotiation_rounds': negotiation_rounds,
            'final_status': 'agreed',
            'processing_time_ms': 250  # Simulated processing time
        }

    def _calculate_interest_rate(
        self,
        amount: int,
        duration_days: int,
        max_rate: float
    ) -> float:
        """Calculate competitive interest rate"""
        # Simple business logic for interest calculation
        base_rate = 3.0  # Base 3% annual rate
        risk_factor = min(amount / 10_000_000, 2.0)  # Risk based on amount
        duration_factor = duration_days / 365  # Pro-rate for duration

        calculated_rate = (base_rate + risk_factor) * duration_factor

        # Don't exceed borrower's max rate
        return min(calculated_rate, max_rate)

    def _calculate_collateral(self, amount: int, collateral_type: str) -> int:
        """Calculate required collateral"""
        # Standard 130% collateralization for ALGO
        if collateral_type == 'ALGO':
            return int(amount * 1.3)
        elif collateral_type == 'USDC':
            return int(amount * 1.2)  # Lower for stable coins
        else:
            return int(amount * 1.5)  # Higher for other assets

class LiquidityAgent(BaseAgent):
    """Agent for discovering and matching liquidity"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Discover available lenders and assess borrower creditworthiness

        Pure business logic - external data passed in
        """
        loan_request = input_data.get('loan_request', {})
        lender_balance = input_data.get('lender_balance')
        borrower_balance = input_data.get('borrower_balance', {})

        amount_needed = loan_request.get('amount_micro_algos', 0)

        # Assess borrower risk based on balance data
        borrower_assessment = self._assess_borrower_risk(borrower_balance)

        # Find suitable lenders
        suitable_lenders = self._find_lenders(
            amount_needed,
            borrower_assessment,
            lender_balance
        )

        return {
            'borrower_assessment': borrower_assessment,
            'suitable_lenders': suitable_lenders,
            'best_lender': suitable_lenders[0] if suitable_lenders else None,
            'liquidity_available': len(suitable_lenders) > 0,
            'total_available_liquidity': sum(
                lender.get('available_amount', 0) for lender in suitable_lenders
            )
        }

    def _assess_borrower_risk(self, balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess borrower creditworthiness"""
        algo_balance = balance_data.get('algo_balance_micro', 0)
        usdc_balance = balance_data.get('usdc_balance_micro', 0)

        # Simple risk assessment logic
        total_balance_value = algo_balance + usdc_balance

        if total_balance_value > 100_000_000:  # > 100 ALGO equivalent
            risk_level = 'low'
            score = 85
        elif total_balance_value > 10_000_000:  # > 10 ALGO equivalent
            risk_level = 'medium'
            score = 70
        else:
            risk_level = 'high'
            score = 50

        return {
            'risk_level': risk_level,
            'credit_score': score,
            'total_balance_value': total_balance_value,
            'assessment_factors': [
                'balance_history',
                'transaction_patterns',
                'collateral_strength'
            ]
        }

    def _find_lenders(
        self,
        amount_needed: int,
        borrower_assessment: Dict[str, Any],
        specific_lender_balance: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find suitable lenders for the loan"""

        suitable_lenders = []

        # If specific lender provided, check their suitability
        if specific_lender_balance:
            lender_balance = specific_lender_balance.get('algo_balance_micro', 0)
            if lender_balance >= amount_needed * 1.1:  # 10% buffer
                suitable_lenders.append({
                    'address': specific_lender_balance.get('address', 'SPECIFIC_LENDER'),
                    'available_amount': lender_balance,
                    'interest_rate_offered': 4.5,
                    'reputation_score': 90,
                    'lending_history': 25
                })

        # Mock additional lenders based on market conditions
        mock_lenders = [
            {
                'address': 'MOCK_LENDER_1_ADDRESS_HERE',
                'available_amount': amount_needed * 2,
                'interest_rate_offered': 4.0,
                'reputation_score': 95,
                'lending_history': 50
            },
            {
                'address': 'MOCK_LENDER_2_ADDRESS_HERE',
                'available_amount': amount_needed * 1.5,
                'interest_rate_offered': 5.0,
                'reputation_score': 80,
                'lending_history': 30
            }
        ]

        # Filter based on borrower risk
        risk_level = borrower_assessment.get('risk_level', 'high')
        for lender in mock_lenders:
            if risk_level == 'low' or lender['reputation_score'] > 75:
                suitable_lenders.append(lender)

        # Sort by best terms (lowest interest rate, highest reputation)
        suitable_lenders.sort(
            key=lambda x: (x['interest_rate_offered'], -x['reputation_score'])
        )

        return suitable_lenders

class ExecutionAgent(BaseAgent):
    """Agent for loan execution and transaction preparation"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare loan execution and transaction data

        Pure business logic - no actual blockchain calls
        """
        loan_id = input_data.get('loan_id')
        terms = input_data.get('terms', {})

        # Generate transaction plan
        transaction_plan = self._create_transaction_plan(terms)

        # Calculate fees and timing
        execution_details = self._calculate_execution_details(terms)

        # Create execution result
        return {
            'loan_id': loan_id,
            'transaction_id': f'LENDING_TX_{uuid.uuid4().hex[:12].upper()}',
            'transaction_plan': transaction_plan,
            'execution_details': execution_details,
            'estimated_completion_time': '2-5 minutes',
            'requires_signatures': [
                terms.get('borrower'),
                terms.get('lender')
            ],
            'status': 'ready_for_execution'
        }

    def _create_transaction_plan(self, terms: Dict[str, Any]) -> Dict[str, Any]:
        """Create step-by-step transaction plan"""
        return {
            'steps': [
                {
                    'step': 1,
                    'type': 'collateral_deposit',
                    'from': terms.get('borrower'),
                    'to': 'ESCROW_CONTRACT_ADDRESS',
                    'amount': terms.get('collateral_amount', 0),
                    'description': 'Borrower deposits collateral'
                },
                {
                    'step': 2,
                    'type': 'loan_disbursement',
                    'from': terms.get('lender'),
                    'to': terms.get('borrower'),
                    'amount': terms.get('amount', 0),
                    'description': 'Lender disburses loan amount'
                }
            ],
            'execution_method': 'atomic_group',
            'total_transactions': 2
        }

    def _calculate_execution_details(self, terms: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate execution costs and timing"""
        base_fee = 1000  # Base transaction fee in microAlgos
        amount = terms.get('amount', 0)

        return {
            'estimated_fee': base_fee * 2,  # Two transactions
            'network_congestion': 'low',
            'confirmation_rounds': 4,
            'estimated_duration_seconds': 20,
            'gas_optimization': 'standard'
        }

class AgentOrchestrator:
    """Orchestrates the lending workflow between agents"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize with injected configuration"""
        self.config = config
        self.liquidity_agent = LiquidityAgent(config)
        self.negotiation_agent = NegotiationAgent(config)
        self.execution_agent = ExecutionAgent(config)

    async def process_loan_request(self, loan_request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a complete loan request through all agents"""

        # Step 1: Liquidity discovery
        liquidity_result = await self.liquidity_agent.process({
            'loan_request': loan_request,
            'lender_balance': loan_request.get('lender_balance'),
            'borrower_balance': loan_request.get('borrower_balance', {})
        })

        if not liquidity_result.get('liquidity_available'):
            return {
                'status': 'rejected',
                'reason': 'insufficient_liquidity',
                'details': liquidity_result
            }

        # Step 2: Term negotiation
        negotiation_result = await self.negotiation_agent.process({
            'loan_request': loan_request,
            'liquidity_data': liquidity_result
        })

        # Step 3: Execution preparation
        loan_id = f'LOAN_{uuid.uuid4().hex[:8].upper()}'
        execution_result = await self.execution_agent.process({
            'loan_id': loan_id,
            'terms': negotiation_result.get('terms', {})
        })

        return {
            'status': 'approved',
            'loan_id': loan_id,
            'liquidity_analysis': liquidity_result,
            'negotiated_terms': negotiation_result,
            'execution_plan': execution_result,
            'workflow_complete': True
        }