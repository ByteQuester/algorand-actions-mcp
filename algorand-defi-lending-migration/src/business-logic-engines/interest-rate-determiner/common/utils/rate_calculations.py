"""
Specialized rate calculation utilities and components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timezone
import logging

from ..models.rate_models import RateRequest, RateComponent, RiskLevel
from ..models.market_data import MarketData
from ..models.credit_models import CreditProfile
from ..models.algorand_models import AlgorandWallet

logger = logging.getLogger(__name__)


class BaseCalculator(ABC):
    """Base class for all rate calculators"""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.last_calculation = None

    @abstractmethod
    def calculate(self, request: RateRequest, **kwargs) -> RateComponent:
        """Calculate rate component"""
        pass

    def get_confidence_score(self, **kwargs) -> float:
        """Calculate confidence score for this component"""
        return 1.0


class BaseRateCalculator(BaseCalculator):
    """Calculator for base interest rate"""

    def __init__(self):
        super().__init__("base_rate", weight=1.0)

    def calculate(self, request: RateRequest, market_data: MarketData, **kwargs) -> RateComponent:
        """
        Calculate base rate from market conditions.

        Args:
            request: Rate request
            market_data: Market data

        Returns:
            RateComponent for base rate
        """
        try:
            # Get federal funds rate as base
            fed_rate = market_data.federal_rates.federal_funds_rate

            # Add institutional margin (typically 2-4%)
            institutional_margin = Decimal('0.025')  # 2.5%

            # Adjust for market conditions
            market_stress = market_data.get_market_stress_indicator()
            stress_adjustment = Decimal(str(market_stress * 0.01))  # Up to 1% for stress

            # Calculate base rate
            base_rate = fed_rate + institutional_margin + stress_adjustment

            # Ensure minimum viable rate
            base_rate = max(base_rate, Decimal('0.01'))  # Minimum 1%

            confidence = self.get_confidence_score(market_data=market_data)

            return RateComponent(
                name=self.name,
                value=base_rate,
                weight=self.weight,
                description=f"Federal funds rate ({fed_rate:.3%}) + institutional margin ({institutional_margin:.3%}) + market stress adjustment ({stress_adjustment:.3%})",
                confidence=confidence,
                source="federal_reserve"
            )

        except Exception as e:
            logger.error(f"Error calculating base rate: {e}")
            # Fallback to default base rate
            fallback_rate = Decimal('0.05')  # 5% fallback
            return RateComponent(
                name=self.name,
                value=fallback_rate,
                weight=self.weight,
                description=f"Fallback base rate due to calculation error: {e}",
                confidence=0.3,
                source="fallback"
            )

    def get_confidence_score(self, market_data: MarketData, **kwargs) -> float:
        """Calculate confidence score based on data freshness and quality"""
        base_confidence = 0.9

        # Reduce confidence if data is stale
        if not market_data.is_data_fresh(max_age_minutes=60):
            base_confidence *= 0.8

        # Adjust for overall market data confidence
        base_confidence *= market_data.overall_confidence

        return min(max(base_confidence, 0.1), 1.0)


class RiskPremiumCalculator(BaseCalculator):
    """Calculator for risk premium based on borrower profile"""

    def __init__(self):
        super().__init__("risk_premium", weight=1.0)
        self.risk_multipliers = {
            RiskLevel.VERY_LOW: Decimal('0.005'),   # 0.5%
            RiskLevel.LOW: Decimal('0.015'),        # 1.5%
            RiskLevel.MEDIUM: Decimal('0.035'),     # 3.5%
            RiskLevel.HIGH: Decimal('0.065'),       # 6.5%
            RiskLevel.VERY_HIGH: Decimal('0.120'),  # 12%
            RiskLevel.EXTREME: Decimal('0.200')     # 20%
        }

    def calculate(self, request: RateRequest, credit_profile: Optional[CreditProfile] = None, **kwargs) -> RateComponent:
        """
        Calculate risk premium based on borrower risk profile.

        Args:
            request: Rate request
            credit_profile: Borrower credit profile

        Returns:
            RateComponent for risk premium
        """
        try:
            # Determine risk level
            if credit_profile:
                risk_level = self._assess_risk_from_profile(credit_profile)
            elif request.risk_score is not None:
                risk_level = self._risk_score_to_level(request.risk_score)
            else:
                risk_level = RiskLevel.MEDIUM  # Default to medium risk

            # Get base risk premium
            base_premium = self.risk_multipliers[risk_level]

            # Additional adjustments
            additional_premium = Decimal('0')

            # Credit score adjustment (if available)
            if credit_profile and credit_profile.traditional_credit_score:
                credit_adjustment = self._calculate_credit_score_adjustment(
                    credit_profile.traditional_credit_score
                )
                additional_premium += credit_adjustment

            # On-chain behavior adjustment
            if credit_profile:
                onchain_adjustment = self._calculate_onchain_adjustment(credit_profile)
                additional_premium += onchain_adjustment

            total_premium = base_premium + additional_premium

            confidence = self.get_confidence_score(
                credit_profile=credit_profile,
                risk_level=risk_level
            )

            return RateComponent(
                name=self.name,
                value=total_premium,
                weight=self.weight,
                description=f"Risk level: {risk_level.value}, base premium: {base_premium:.3%}, adjustments: {additional_premium:.3%}",
                confidence=confidence,
                source="credit_analysis"
            )

        except Exception as e:
            logger.error(f"Error calculating risk premium: {e}")
            # Conservative fallback
            fallback_premium = Decimal('0.05')  # 5%
            return RateComponent(
                name=self.name,
                value=fallback_premium,
                weight=self.weight,
                description=f"Fallback risk premium due to error: {e}",
                confidence=0.3,
                source="fallback"
            )

    def _assess_risk_from_profile(self, profile: CreditProfile) -> RiskLevel:
        """Assess risk level from credit profile"""
        if profile.credit_rating.value in ['AAA', 'AA']:
            return RiskLevel.VERY_LOW
        elif profile.credit_rating.value in ['A']:
            return RiskLevel.LOW
        elif profile.credit_rating.value in ['BBB']:
            return RiskLevel.MEDIUM
        elif profile.credit_rating.value in ['BB', 'B']:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH

    def _risk_score_to_level(self, risk_score: int) -> RiskLevel:
        """Convert numeric risk score to risk level"""
        if risk_score <= 15:
            return RiskLevel.VERY_LOW
        elif risk_score <= 30:
            return RiskLevel.LOW
        elif risk_score <= 50:
            return RiskLevel.MEDIUM
        elif risk_score <= 75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH

    def _calculate_credit_score_adjustment(self, credit_score: int) -> Decimal:
        """Calculate adjustment based on traditional credit score"""
        if credit_score >= 750:
            return Decimal('-0.01')  # -1% discount for excellent credit
        elif credit_score >= 700:
            return Decimal('-0.005')  # -0.5% discount for good credit
        elif credit_score >= 650:
            return Decimal('0')  # No adjustment
        elif credit_score >= 600:
            return Decimal('0.01')  # +1% premium for fair credit
        else:
            return Decimal('0.025')  # +2.5% premium for poor credit

    def _calculate_onchain_adjustment(self, profile: CreditProfile) -> Decimal:
        """Calculate adjustment based on on-chain behavior"""
        adjustment = Decimal('0')

        # Wallet age bonus
        if profile.on_chain_behavior.wallet_age_days > 730:  # 2+ years
            adjustment -= Decimal('0.005')  # -0.5% for mature wallet

        # DeFi participation bonus
        if len(profile.on_chain_behavior.defi_protocols_used) > 3:
            adjustment -= Decimal('0.003')  # -0.3% for active DeFi user

        # Governance participation bonus
        if profile.on_chain_behavior.governance_participation:
            adjustment -= Decimal('0.002')  # -0.2% for governance participation

        # High-risk asset penalty
        if profile.on_chain_behavior.high_risk_asa_exposure > 0.3:  # >30%
            adjustment += Decimal('0.01')  # +1% for high-risk exposure

        return adjustment

    def get_confidence_score(self, credit_profile: Optional[CreditProfile], risk_level: RiskLevel, **kwargs) -> float:
        """Calculate confidence score for risk assessment"""
        base_confidence = 0.7

        if credit_profile:
            # Increase confidence if we have comprehensive data
            base_confidence += 0.2

            # Adjust based on profile confidence
            base_confidence *= credit_profile.profile_confidence

            # Increase confidence for mature profiles
            if credit_profile.on_chain_behavior.wallet_age_days > 365:
                base_confidence += 0.1

        return min(max(base_confidence, 0.1), 1.0)


class DurationAdjustmentCalculator(BaseCalculator):
    """Calculator for duration-based rate adjustments"""

    def __init__(self):
        super().__init__("duration_adjustment", weight=1.0)

    def calculate(self, request: RateRequest, market_data: Optional[MarketData] = None, **kwargs) -> RateComponent:
        """
        Calculate duration adjustment based on loan term.

        Args:
            request: Rate request
            market_data: Market data for term structure

        Returns:
            RateComponent for duration adjustment
        """
        try:
            duration_years = request.duration_days / 365.0

            # Base term structure slope
            term_slope = Decimal('0.003')  # 0.3% per year default

            # Adjust slope based on market conditions
            if market_data:
                term_slope = Decimal(str(market_data.federal_rates.treasury_10y -
                                        market_data.federal_rates.treasury_1y)) / Decimal('9')
                term_slope = max(term_slope, Decimal('0.001'))  # Minimum 0.1%

            # Calculate adjustment
            if duration_years <= 1:
                adjustment = Decimal('0')
            elif duration_years <= 5:
                # Linear increase for medium term
                adjustment = Decimal(str(duration_years - 1)) * term_slope
            else:
                # Diminishing returns for long term
                base_adjustment = Decimal('4') * term_slope  # 5-year adjustment
                additional_years = Decimal(str(duration_years - 5))
                additional_adjustment = additional_years * term_slope * Decimal('0.5')
                adjustment = base_adjustment + additional_adjustment

            confidence = self.get_confidence_score(market_data=market_data)

            return RateComponent(
                name=self.name,
                value=adjustment,
                weight=self.weight,
                description=f"Duration: {duration_years:.1f} years, term slope: {term_slope:.3%}",
                confidence=confidence,
                source="term_structure"
            )

        except Exception as e:
            logger.error(f"Error calculating duration adjustment: {e}")
            # Simple fallback calculation
            duration_years = request.duration_days / 365.0
            fallback_adjustment = Decimal(str(max(0, duration_years - 1) * 0.002))
            return RateComponent(
                name=self.name,
                value=fallback_adjustment,
                weight=self.weight,
                description=f"Fallback duration adjustment: {fallback_adjustment:.3%}",
                confidence=0.5,
                source="fallback"
            )

    def get_confidence_score(self, market_data: Optional[MarketData], **kwargs) -> float:
        """Calculate confidence score for duration adjustment"""
        if market_data and market_data.is_data_fresh():
            return 0.95
        else:
            return 0.7


class CollateralDiscountCalculator(BaseCalculator):
    """Calculator for collateral-based rate discounts"""

    def __init__(self):
        super().__init__("collateral_discount", weight=1.0)

    def calculate(self, request: RateRequest, algorand_wallet: Optional[AlgorandWallet] = None, **kwargs) -> RateComponent:
        """
        Calculate discount based on collateral quality and coverage.

        Args:
            request: Rate request
            algorand_wallet: Algorand wallet analysis

        Returns:
            RateComponent for collateral discount
        """
        try:
            total_collateral_value = sum(request.collateral_values.values())

            if total_collateral_value == 0:
                return RateComponent(
                    name=self.name,
                    value=Decimal('0'),
                    weight=self.weight,
                    description="No collateral provided",
                    confidence=1.0,
                    source="collateral_analysis"
                )

            # Calculate coverage ratio
            coverage_ratio = total_collateral_value / request.loan_amount

            # Base discount based on coverage
            base_discount = self._calculate_coverage_discount(coverage_ratio)

            # Quality adjustment
            quality_adjustment = Decimal('0')
            if algorand_wallet:
                collateral_quality = algorand_wallet.get_collateral_quality_assessment()
                quality_score = collateral_quality['overall_quality_score']
                quality_adjustment = Decimal(str(quality_score * 0.01))  # Up to 1% for perfect quality

            total_discount = base_discount + quality_adjustment

            confidence = self.get_confidence_score(
                algorand_wallet=algorand_wallet,
                coverage_ratio=float(coverage_ratio)
            )

            return RateComponent(
                name=self.name,
                value=total_discount,
                weight=self.weight,
                description=f"Coverage ratio: {coverage_ratio:.2f}x, quality bonus: {quality_adjustment:.3%}",
                confidence=confidence,
                source="collateral_analysis"
            )

        except Exception as e:
            logger.error(f"Error calculating collateral discount: {e}")
            return RateComponent(
                name=self.name,
                value=Decimal('0'),
                weight=self.weight,
                description=f"Error calculating collateral discount: {e}",
                confidence=0.3,
                source="fallback"
            )

    def _calculate_coverage_discount(self, coverage_ratio: Decimal) -> Decimal:
        """Calculate discount based on collateral coverage ratio"""
        if coverage_ratio >= Decimal('3.0'):  # 300% coverage
            return Decimal('0.025')  # 2.5% discount
        elif coverage_ratio >= Decimal('2.0'):  # 200% coverage
            return Decimal('0.02')   # 2% discount
        elif coverage_ratio >= Decimal('1.5'):  # 150% coverage
            return Decimal('0.015')  # 1.5% discount
        elif coverage_ratio >= Decimal('1.2'):  # 120% coverage
            return Decimal('0.01')   # 1% discount
        elif coverage_ratio >= Decimal('1.0'):  # 100% coverage
            return Decimal('0.005')  # 0.5% discount
        else:
            return Decimal('0')      # No discount for under-collateralized

    def get_confidence_score(self, algorand_wallet: Optional[AlgorandWallet], coverage_ratio: float, **kwargs) -> float:
        """Calculate confidence score for collateral analysis"""
        base_confidence = 0.8

        if algorand_wallet:
            # Higher confidence with wallet analysis
            base_confidence = 0.9
            # Adjust based on analysis confidence
            base_confidence *= algorand_wallet.analysis_confidence

        # Reduce confidence for very high coverage ratios (might be overvalued)
        if coverage_ratio > 10:
            base_confidence *= 0.8

        return min(max(base_confidence, 0.1), 1.0)


class AlgorandAdjustmentCalculator(BaseCalculator):
    """Calculator for Algorand-specific adjustments"""

    def __init__(self):
        super().__init__("algorand_adjustment", weight=1.0)

    def calculate(self, request: RateRequest, algorand_wallet: Optional[AlgorandWallet] = None, **kwargs) -> RateComponent:
        """
        Calculate Algorand-specific rate adjustments.

        Args:
            request: Rate request
            algorand_wallet: Algorand wallet analysis

        Returns:
            RateComponent for Algorand adjustment
        """
        try:
            if not algorand_wallet:
                return RateComponent(
                    name=self.name,
                    value=Decimal('0'),
                    weight=self.weight,
                    description="No Algorand wallet analysis available",
                    confidence=0.5,
                    source="algorand_analysis"
                )

            total_adjustment = Decimal('0')
            adjustments = []

            # Wallet maturity bonus
            if algorand_wallet.wallet_age_days > 730:  # 2+ years
                maturity_bonus = Decimal('-0.005')  # -0.5%
                total_adjustment += maturity_bonus
                adjustments.append(f"Wallet maturity: {maturity_bonus:.3%}")

            # DeFi participation bonus
            if algorand_wallet.is_defi_active():
                defi_protocols = len([pos for pos in algorand_wallet.defi_positions])
                if defi_protocols > 3:
                    defi_bonus = Decimal('-0.003')  # -0.3%
                    total_adjustment += defi_bonus
                    adjustments.append(f"Active DeFi user: {defi_bonus:.3%}")

            # Governance participation bonus
            if algorand_wallet.governance_participation:
                governance_bonus = Decimal('-0.002')  # -0.2%
                total_adjustment += governance_bonus
                adjustments.append(f"Governance participation: {governance_bonus:.3%}")

            # ASA diversity bonus
            diversity_score = algorand_wallet.asa_valuation.diversity_score
            if diversity_score > 0.7:  # High diversity
                diversity_bonus = Decimal('-0.002')  # -0.2%
                total_adjustment += diversity_bonus
                adjustments.append(f"Portfolio diversity: {diversity_bonus:.3%}")

            # Risk penalties
            high_risk_exposure = algorand_wallet.asa_valuation.get_high_risk_exposure()
            if high_risk_exposure > 0.3:  # >30% in high-risk assets
                risk_penalty = Decimal('0.01')  # +1%
                total_adjustment += risk_penalty
                adjustments.append(f"High-risk exposure penalty: +{risk_penalty:.3%}")

            confidence = self.get_confidence_score(algorand_wallet=algorand_wallet)

            description = "; ".join(adjustments) if adjustments else "No Algorand-specific adjustments"

            return RateComponent(
                name=self.name,
                value=total_adjustment,
                weight=self.weight,
                description=description,
                confidence=confidence,
                source="algorand_analysis"
            )

        except Exception as e:
            logger.error(f"Error calculating Algorand adjustment: {e}")
            return RateComponent(
                name=self.name,
                value=Decimal('0'),
                weight=self.weight,
                description=f"Error in Algorand analysis: {e}",
                confidence=0.3,
                source="fallback"
            )

    def get_confidence_score(self, algorand_wallet: AlgorandWallet, **kwargs) -> float:
        """Calculate confidence score for Algorand analysis"""
        return algorand_wallet.analysis_confidence


class DeFiAdjustmentCalculator(BaseCalculator):
    """Calculator for DeFi market adjustments"""

    def __init__(self):
        super().__init__("defi_adjustment", weight=1.0)

    def calculate(self, request: RateRequest, market_data: Optional[MarketData] = None, **kwargs) -> RateComponent:
        """
        Calculate DeFi market-based adjustments.

        Args:
            request: Rate request
            market_data: Market data including DeFi rates

        Returns:
            RateComponent for DeFi adjustment
        """
        try:
            if not market_data or not market_data.defi_rates:
                return RateComponent(
                    name=self.name,
                    value=Decimal('0'),
                    weight=self.weight,
                    description="No DeFi market data available",
                    confidence=0.3,
                    source="defi_analysis"
                )

            # Calculate DeFi premium over traditional rates
            defi_premium = market_data.calculate_defi_premium()

            # Adjust based on volatility
            volatility_adjustment = Decimal('0')
            if market_data.algorand_market.algo_price_volatility > 0.5:  # High volatility
                volatility_adjustment = Decimal('0.005')  # +0.5% for high volatility

            # Adjust based on liquidity
            liquidity_score = market_data.liquidity_score
            if liquidity_score < 0.5:  # Low liquidity
                liquidity_adjustment = Decimal('0.003')  # +0.3% for low liquidity
            else:
                liquidity_adjustment = Decimal('0')

            total_adjustment = (defi_premium * Decimal('0.3') +  # 30% of DeFi premium
                               volatility_adjustment +
                               liquidity_adjustment)

            confidence = self.get_confidence_score(market_data=market_data)

            return RateComponent(
                name=self.name,
                value=total_adjustment,
                weight=self.weight,
                description=f"DeFi premium factor: {defi_premium:.3%}, volatility adj: {volatility_adjustment:.3%}, liquidity adj: {liquidity_adjustment:.3%}",
                confidence=confidence,
                source="defi_analysis"
            )

        except Exception as e:
            logger.error(f"Error calculating DeFi adjustment: {e}")
            return RateComponent(
                name=self.name,
                value=Decimal('0'),
                weight=self.weight,
                description=f"Error in DeFi analysis: {e}",
                confidence=0.3,
                source="fallback"
            )

    def get_confidence_score(self, market_data: MarketData, **kwargs) -> float:
        """Calculate confidence score for DeFi analysis"""
        base_confidence = 0.7

        # Adjust based on data quality
        base_confidence *= market_data.defi_rates.overall_data_quality

        # Reduce confidence if data is stale
        if not market_data.is_data_fresh(max_age_minutes=30):  # DeFi data should be fresh
            base_confidence *= 0.8

        return min(max(base_confidence, 0.1), 1.0)


class RateCalculator:
    """Main rate calculator that orchestrates all components"""

    def __init__(self):
        self.calculators = {
            'base_rate': BaseRateCalculator(),
            'risk_premium': RiskPremiumCalculator(),
            'duration_adjustment': DurationAdjustmentCalculator(),
            'collateral_discount': CollateralDiscountCalculator(),
            'algorand_adjustment': AlgorandAdjustmentCalculator(),
            'defi_adjustment': DeFiAdjustmentCalculator()
        }

    def calculate_all_components(
        self,
        request: RateRequest,
        market_data: Optional[MarketData] = None,
        credit_profile: Optional[CreditProfile] = None,
        algorand_wallet: Optional[AlgorandWallet] = None
    ) -> List[RateComponent]:
        """
        Calculate all rate components.

        Args:
            request: Rate request
            market_data: Market data
            credit_profile: Credit profile
            algorand_wallet: Algorand wallet analysis

        Returns:
            List of calculated rate components
        """
        components = []

        for name, calculator in self.calculators.items():
            try:
                component = calculator.calculate(
                    request=request,
                    market_data=market_data,
                    credit_profile=credit_profile,
                    algorand_wallet=algorand_wallet
                )
                components.append(component)
            except Exception as e:
                logger.error(f"Error calculating {name}: {e}")
                # Add error component
                error_component = RateComponent(
                    name=name,
                    value=Decimal('0'),
                    weight=0.0,
                    description=f"Calculation failed: {e}",
                    confidence=0.0,
                    source="error"
                )
                components.append(error_component)

        return components

    def calculate_final_rate(self, components: List[RateComponent]) -> Decimal:
        """
        Calculate final interest rate from components.

        Args:
            components: List of rate components

        Returns:
            Final annual interest rate
        """
        base_rate = Decimal('0')
        adjustments = Decimal('0')

        for component in components:
            if component.name == 'base_rate':
                base_rate = component.value
            elif component.name == 'collateral_discount':
                adjustments -= component.value  # Discount reduces rate
            else:
                adjustments += component.value  # Other components increase rate

        final_rate = base_rate + adjustments

        # Ensure minimum rate
        return max(final_rate, Decimal('0.005'))  # Minimum 0.5%