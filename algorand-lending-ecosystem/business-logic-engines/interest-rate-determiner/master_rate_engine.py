"""
Master Rate Calculation Engine

End-to-end DeFi lending rate calculation system combining all 6 Algorand-native engines
for real-time, blockchain-based interest rate determination.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from algosdk.v2client import algod, indexer

from .engines import (
    AlgoStakingEngine,
    StakingMetrics,
    DeFiYieldEngine,
    DeFiProtocolData,
    ReputationEngine,
    ReputationScore,
    ASARiskEngine,
    ASARiskMetrics,
    NetworkActivityEngine,
    NetworkMetrics,
    LiquidityPoolEngine,
    LiquidityMetrics
)

logger = logging.getLogger(__name__)

@dataclass
class LoanParameters:
    """Loan parameters for rate calculation"""
    principal_amount: Decimal
    term_days: int
    borrower_address: Optional[str] = None
    collateral_asset_id: Optional[int] = None
    collateral_amount: Optional[Decimal] = None
    loan_purpose: Optional[str] = None
    request_timestamp: datetime = None

    def __post_init__(self):
        if self.request_timestamp is None:
            self.request_timestamp = datetime.utcnow()

@dataclass
class RateCalculationResult:
    """Complete rate calculation result"""
    loan_id: str
    loan_parameters: LoanParameters
    final_interest_rate: Decimal
    effective_apr: Decimal

    # Component rates
    base_staking_rate: Decimal
    defi_market_rate: Decimal
    reputation_adjustment: Decimal
    collateral_risk_adjustment: Decimal
    network_adjustment: Decimal
    liquidity_adjustment: Decimal

    # Loan terms
    annual_interest_amount: Decimal
    monthly_payment: Decimal
    total_repayment: Decimal

    # Risk metrics
    loan_to_value_ratio: Optional[Decimal]
    collateral_factor: Optional[Decimal]
    risk_level: str

    # Engine data
    staking_metrics: Optional[StakingMetrics]
    defi_metrics: Optional[DeFiProtocolData]
    reputation_data: Optional[ReputationScore]
    collateral_data: Optional[ASARiskMetrics]
    network_data: Optional[NetworkMetrics]
    liquidity_data: Optional[LiquidityMetrics]

    # Metadata
    calculation_timestamp: datetime
    confidence_score: Decimal
    rate_valid_until: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'loan_id': self.loan_id,
            'calculation_timestamp': self.calculation_timestamp.isoformat(),
            'rate_valid_until': self.rate_valid_until.isoformat(),
            'loan_parameters': {
                'principal_amount': float(self.loan_parameters.principal_amount),
                'term_days': self.loan_parameters.term_days,
                'borrower_address': self.loan_parameters.borrower_address,
                'collateral_asset_id': self.loan_parameters.collateral_asset_id,
                'collateral_amount': float(self.loan_parameters.collateral_amount) if self.loan_parameters.collateral_amount else None,
                'loan_purpose': self.loan_parameters.loan_purpose
            },
            'rate_breakdown': {
                'final_interest_rate': float(self.final_interest_rate),
                'effective_apr': float(self.effective_apr),
                'base_staking_rate': float(self.base_staking_rate),
                'defi_market_rate': float(self.defi_market_rate),
                'reputation_adjustment': float(self.reputation_adjustment),
                'collateral_risk_adjustment': float(self.collateral_risk_adjustment),
                'network_adjustment': float(self.network_adjustment),
                'liquidity_adjustment': float(self.liquidity_adjustment)
            },
            'loan_terms': {
                'annual_interest_amount': float(self.annual_interest_amount),
                'monthly_payment': float(self.monthly_payment),
                'total_repayment': float(self.total_repayment)
            },
            'risk_assessment': {
                'loan_to_value_ratio': float(self.loan_to_value_ratio) if self.loan_to_value_ratio else None,
                'collateral_factor': float(self.collateral_factor) if self.collateral_factor else None,
                'risk_level': self.risk_level,
                'confidence_score': float(self.confidence_score)
            }
        }

class MasterRateEngine:
    """
    Master engine that orchestrates all 6 Algorand-native engines
    to provide comprehensive, real-time interest rate calculations.
    """

    def __init__(
        self,
        algod_client: algod.AlgodClient,
        indexer_client: indexer.IndexerClient,
        protocol_apis: Optional[Dict[str, str]] = None,
        mcp_reader_url: Optional[str] = None,
        mcp_writer_url: Optional[str] = None,
        cache_ttl: int = 300
    ):
        self.algod_client = algod_client
        self.indexer_client = indexer_client
        self.protocol_apis = protocol_apis or {}
        self.mcp_reader_url = mcp_reader_url
        self.mcp_writer_url = mcp_writer_url
        self.cache_ttl = cache_ttl

        # Initialize all engines
        self.staking_engine = AlgoStakingEngine(algod_client, cache_ttl=cache_ttl)
        self.defi_engine = DeFiYieldEngine(algod_client, protocol_apis, cache_ttl=cache_ttl)
        self.reputation_engine = ReputationEngine(algod_client, indexer_client, cache_ttl=cache_ttl*2)  # Longer cache
        self.asa_risk_engine = ASARiskEngine(algod_client, indexer_client, {}, cache_ttl=cache_ttl)
        self.network_engine = NetworkActivityEngine(algod_client)
        self.liquidity_engine = LiquidityPoolEngine(algod_client)

        # Rate calculation configuration
        self.config = {
            'min_interest_rate': Decimal('0.02'),  # 2% minimum
            'max_interest_rate': Decimal('0.30'),  # 30% maximum
            'default_rate_validity_hours': 1,      # Rates valid for 1 hour
            'component_weights': {
                'staking': Decimal('0.3'),
                'defi': Decimal('0.3'),
                'reputation': Decimal('0.15'),
                'collateral': Decimal('0.15'),
                'network': Decimal('0.05'),
                'liquidity': Decimal('0.05')
            }
        }

    async def calculate_comprehensive_rate(
        self,
        loan_parameters: LoanParameters,
        include_real_time_data: bool = True
    ) -> RateCalculationResult:
        """
        Calculate comprehensive interest rate using all engines
        """
        loan_id = f"loan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(loan_parameters))%10000:04d}"

        logger.info(f"Starting comprehensive rate calculation for loan {loan_id}")

        try:
            # Step 1: Gather data from all engines
            engine_data = await self._gather_engine_data(
                loan_parameters,
                include_real_time_data
            )

            # Step 2: Calculate component rates
            component_rates = await self._calculate_component_rates(
                loan_parameters,
                engine_data
            )

            # Step 3: Apply risk adjustments
            risk_adjustments = await self._calculate_risk_adjustments(
                loan_parameters,
                engine_data
            )

            # Step 4: Calculate final rate
            final_rate = await self._calculate_final_rate(
                component_rates,
                risk_adjustments
            )

            # Step 5: Calculate loan terms
            loan_terms = self._calculate_loan_terms(
                loan_parameters.principal_amount,
                loan_parameters.term_days,
                final_rate
            )

            # Step 6: Assess overall risk and confidence
            risk_assessment = await self._assess_overall_risk(
                loan_parameters,
                engine_data,
                final_rate
            )

            # Step 7: Create result
            result = RateCalculationResult(
                loan_id=loan_id,
                loan_parameters=loan_parameters,
                final_interest_rate=final_rate,
                effective_apr=final_rate,  # For simple interest

                # Component rates
                base_staking_rate=component_rates['staking'],
                defi_market_rate=component_rates['defi'],
                reputation_adjustment=risk_adjustments['reputation'],
                collateral_risk_adjustment=risk_adjustments['collateral'],
                network_adjustment=risk_adjustments['network'],
                liquidity_adjustment=risk_adjustments['liquidity'],

                # Loan terms
                annual_interest_amount=loan_terms['annual_interest'],
                monthly_payment=loan_terms['monthly_payment'],
                total_repayment=loan_terms['total_repayment'],

                # Risk metrics
                loan_to_value_ratio=risk_assessment['ltv'],
                collateral_factor=risk_assessment['collateral_factor'],
                risk_level=risk_assessment['risk_level'],

                # Engine data
                staking_metrics=engine_data.get('staking'),
                defi_metrics=engine_data.get('defi'),
                reputation_data=engine_data.get('reputation'),
                collateral_data=engine_data.get('collateral'),
                network_data=engine_data.get('network'),
                liquidity_data=engine_data.get('liquidity'),

                # Metadata
                calculation_timestamp=datetime.utcnow(),
                confidence_score=risk_assessment['confidence'],
                rate_valid_until=datetime.utcnow() + timedelta(hours=self.config['default_rate_validity_hours'])
            )

            logger.info(f"Rate calculation completed for loan {loan_id}: {final_rate:.4f}")
            return result

        except Exception as e:
            logger.error(f"Error in comprehensive rate calculation: {e}")
            raise

    async def _gather_engine_data(
        self,
        loan_parameters: LoanParameters,
        include_real_time: bool
    ) -> Dict:
        """Gather data from all engines in parallel"""

        tasks = {}

        # Always get staking and DeFi data
        tasks['staking'] = self.staking_engine.calculate_staking_rate()
        tasks['defi'] = self.defi_engine.calculate_defi_rates()

        # Always get network and liquidity data
        tasks['network'] = self.network_engine.analyze_network_activity()
        tasks['liquidity'] = self.liquidity_engine.analyze_liquidity_health()

        # Optional: reputation analysis
        if loan_parameters.borrower_address:
            tasks['reputation'] = self.reputation_engine.calculate_reputation(
                loan_parameters.borrower_address
            )

        # Optional: collateral analysis
        if loan_parameters.collateral_asset_id:
            tasks['collateral'] = self.asa_risk_engine.analyze_asa_risk(
                loan_parameters.collateral_asset_id
            )

        # Execute all tasks
        results = {}
        completed_tasks = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
        )

        # Map results back to engines
        for i, (engine_name, task) in enumerate(tasks.items()):
            result = completed_tasks[i]
            if isinstance(result, Exception):
                logger.warning(f"Engine {engine_name} failed: {result}")
                results[engine_name] = None
            else:
                results[engine_name] = result

        return results

    async def _calculate_component_rates(
        self,
        loan_parameters: LoanParameters,
        engine_data: Dict
    ) -> Dict[str, Decimal]:
        """Calculate base component rates from engine data"""

        component_rates = {}

        # Staking rate component
        staking_data = engine_data.get('staking')
        if staking_data:
            component_rates['staking'] = staking_data.risk_adjusted_yield()
        else:
            component_rates['staking'] = Decimal('0.06')  # 6% fallback

        # DeFi market rate component
        defi_data = engine_data.get('defi')
        if defi_data:
            component_rates['defi'] = defi_data.risk_adjusted_apy
        else:
            component_rates['defi'] = Decimal('0.10')  # 10% fallback

        return component_rates

    async def _calculate_risk_adjustments(
        self,
        loan_parameters: LoanParameters,
        engine_data: Dict
    ) -> Dict[str, Decimal]:
        """Calculate risk adjustments from engine data"""

        adjustments = {
            'reputation': Decimal('0'),
            'collateral': Decimal('0'),
            'network': Decimal('0'),
            'liquidity': Decimal('0')
        }

        # Reputation adjustment
        reputation_data = engine_data.get('reputation')
        if reputation_data:
            adjustments['reputation'] = (
                reputation_data.rate_discount() - reputation_data.rate_premium()
            )

        # Collateral risk adjustment
        collateral_data = engine_data.get('collateral')
        if collateral_data:
            adjustments['collateral'] = collateral_data.rate_adjustment()

        # Network congestion adjustment
        network_data = engine_data.get('network')
        if network_data:
            adjustments['network'] = network_data.congestion_score * Decimal('0.01')  # Up to 1% penalty

        # Liquidity health adjustment
        liquidity_data = engine_data.get('liquidity')
        if liquidity_data:
            # Good liquidity reduces rates
            adjustments['liquidity'] = -(liquidity_data.health_score - Decimal('0.5')) * Decimal('0.01')

        return adjustments

    async def _calculate_final_rate(
        self,
        component_rates: Dict[str, Decimal],
        risk_adjustments: Dict[str, Decimal]
    ) -> Decimal:
        """Calculate final interest rate from components and adjustments"""

        # Base rate calculation (weighted average of staking and DeFi)
        base_rate = (
            component_rates['staking'] * self.config['component_weights']['staking'] +
            component_rates['defi'] * self.config['component_weights']['defi']
        ) / (self.config['component_weights']['staking'] + self.config['component_weights']['defi'])

        # Apply all adjustments
        total_adjustment = sum(risk_adjustments.values())

        # Calculate final rate
        final_rate = base_rate + total_adjustment

        # Apply bounds
        final_rate = max(
            self.config['min_interest_rate'],
            min(final_rate, self.config['max_interest_rate'])
        )

        return final_rate

    def _calculate_loan_terms(
        self,
        principal: Decimal,
        term_days: int,
        interest_rate: Decimal
    ) -> Dict[str, Decimal]:
        """Calculate loan payment terms"""

        # Simple interest calculation (can be enhanced to compound interest)
        annual_interest = principal * interest_rate
        total_repayment = principal + annual_interest

        # Scale by term
        term_years = Decimal(term_days) / Decimal('365')
        actual_interest = annual_interest * term_years
        actual_total = principal + actual_interest

        # Monthly payment
        months = Decimal(term_days) / Decimal('30.44')  # Average month length
        monthly_payment = actual_total / months if months > 0 else actual_total

        return {
            'annual_interest': annual_interest,
            'actual_interest': actual_interest,
            'total_repayment': actual_total,
            'monthly_payment': monthly_payment
        }

    async def _assess_overall_risk(
        self,
        loan_parameters: LoanParameters,
        engine_data: Dict,
        final_rate: Decimal
    ) -> Dict:
        """Assess overall loan risk and calculation confidence"""

        risk_factors = []
        confidence_factors = []

        # Collateral assessment
        ltv = None
        collateral_factor = None
        collateral_data = engine_data.get('collateral')

        if collateral_data and loan_parameters.collateral_amount:
            collateral_factor = collateral_data.collateral_factor
            # Estimate collateral value (simplified)
            collateral_value = loan_parameters.collateral_amount  # Assume 1:1 for now
            ltv = loan_parameters.principal_amount / collateral_value

            if ltv > collateral_factor:
                risk_factors.append("High LTV ratio")

        # Reputation assessment
        reputation_data = engine_data.get('reputation')
        if reputation_data:
            confidence_factors.append(reputation_data.confidence_level)
            if reputation_data.overall_score < Decimal('0.5'):
                risk_factors.append("Low borrower reputation")

        # Market conditions
        defi_data = engine_data.get('defi')
        if defi_data:
            confidence_factors.append(Decimal('1') - defi_data.volatility_score)
            if defi_data.volatility_score > Decimal('0.7'):
                risk_factors.append("High market volatility")

        # Network conditions
        network_data = engine_data.get('network')
        if network_data:
            if network_data.congestion_score > Decimal('0.7'):
                risk_factors.append("High network congestion")

        # Determine risk level
        risk_score = len(risk_factors) / 5.0  # Normalize to 0-1
        if risk_score <= 0.2:
            risk_level = "LOW"
        elif risk_score <= 0.4:
            risk_level = "MEDIUM"
        elif risk_score <= 0.6:
            risk_level = "HIGH"
        else:
            risk_level = "VERY_HIGH"

        # Calculate confidence
        if confidence_factors:
            confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            confidence = Decimal('0.5')  # Medium confidence by default

        return {
            'ltv': ltv,
            'collateral_factor': collateral_factor,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'confidence': confidence
        }

    async def get_rate_quote(
        self,
        principal_amount: float,
        term_days: int = 365,
        borrower_address: str = None,
        collateral_asset_id: int = None,
        collateral_amount: float = None
    ) -> Dict:
        """
        Quick rate quote interface
        """
        loan_params = LoanParameters(
            principal_amount=Decimal(str(principal_amount)),
            term_days=term_days,
            borrower_address=borrower_address,
            collateral_asset_id=collateral_asset_id,
            collateral_amount=Decimal(str(collateral_amount)) if collateral_amount else None
        )

        result = await self.calculate_comprehensive_rate(loan_params)
        return result.to_dict()

    async def stream_rate_updates(
        self,
        loan_parameters: LoanParameters,
        update_interval: int = 60,
        duration: int = 3600
    ):
        """
        Stream real-time rate updates for monitoring
        """
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=duration)

        while datetime.utcnow() < end_time:
            try:
                result = await self.calculate_comprehensive_rate(loan_parameters)
                yield {
                    'timestamp': datetime.utcnow().isoformat(),
                    'rate': float(result.final_interest_rate),
                    'confidence': float(result.confidence_score),
                    'risk_level': result.risk_level
                }

                await asyncio.sleep(update_interval)

            except Exception as e:
                logger.error(f"Error in rate stream: {e}")
                yield {
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': str(e)
                }
                await asyncio.sleep(update_interval)

# Example usage and factory functions
async def create_master_engine(
    algod_url: str = "https://mainnet-api.algonode.cloud",
    indexer_url: str = "https://mainnet-idx.algonode.cloud",
    **kwargs
) -> MasterRateEngine:
    """Create a configured master rate engine"""

    algod_client = algod.AlgodClient("", algod_url)
    indexer_client = indexer.IndexerClient("", indexer_url)

    return MasterRateEngine(
        algod_client=algod_client,
        indexer_client=indexer_client,
        **kwargs
    )

async def quick_rate_calculation(
    principal_amount: float,
    term_days: int = 365,
    borrower_address: str = None,
    collateral_asset_id: int = None,
    collateral_amount: float = None
) -> Dict:
    """Quick rate calculation without engine setup"""

    engine = await create_master_engine()
    return await engine.get_rate_quote(
        principal_amount=principal_amount,
        term_days=term_days,
        borrower_address=borrower_address,
        collateral_asset_id=collateral_asset_id,
        collateral_amount=collateral_amount
    )