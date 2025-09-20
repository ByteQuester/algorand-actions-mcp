"""
DeFi Protocol Exposure Analysis
Analyzes cross-protocol exposure and concentration risk across the Algorand DeFi ecosystem
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml
import aiohttp
import numpy as np
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProtocolExposure:
    """Protocol exposure data structure"""
    protocol_name: str
    category: str
    tvl_usd: float
    tvl_percentage: float
    risk_tier: str
    user_exposure_usd: float
    exposure_percentage: float
    concentration_risk_score: float
    liquidity_risk_score: float

@dataclass
class CrossProtocolExposure:
    """Cross-protocol exposure analysis result"""
    total_exposure_usd: float
    protocol_exposures: List[ProtocolExposure]
    concentration_risk_score: float
    diversification_score: float
    systemic_risk_score: float
    risk_level: str
    recommendations: List[str]
    timestamp: datetime

class ProtocolExposureAnalyzer:
    """Analyzes DeFi protocol exposure and concentration risks"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the protocol exposure analyzer"""
        self.config = self._load_config(config_path)
        self.session = None

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_protocol_data(self, protocol_name: str) -> Dict[str, Any]:
        """Fetch protocol data from various APIs"""
        protocol_config = self.config['algorand_protocols'].get(protocol_name, {})

        # Simulate API calls to get protocol data
        # In production, this would call actual protocol APIs
        mock_data = {
            'algofi': {
                'tvl_usd': 45000000,  # $45M TVL
                'total_borrowed': 25000000,
                'total_supplied': 55000000,
                'active_users': 2500,
                'pools': ['ALGO', 'USDC', 'USDT', 'goBTC', 'goETH'],
                'governance_token_price': 0.15,
                'governance_market_cap': 15000000
            },
            'folks_finance': {
                'tvl_usd': 32000000,  # $32M TVL
                'total_borrowed': 18000000,
                'total_supplied': 40000000,
                'active_users': 1800,
                'pools': ['ALGO', 'USDC', 'USDT', 'gALGO'],
                'governance_token_price': 0.08,
                'governance_market_cap': 8000000
            },
            'tinyman': {
                'tvl_usd': 25000000,  # $25M TVL
                'total_volume_24h': 2000000,
                'active_users': 3000,
                'pools': ['ALGO/USDC', 'ALGO/USDT', 'USDC/USDT'],
                'governance_token_price': 0.12,
                'governance_market_cap': 12000000
            },
            'pact': {
                'tvl_usd': 12000000,  # $12M TVL
                'total_volume_24h': 800000,
                'active_users': 1200,
                'pools': ['ALGO/USDC', 'ALGO/PACT'],
                'governance_token_price': 0.05,
                'governance_market_cap': 5000000
            },
            'humble_defi': {
                'tvl_usd': 6000000,  # $6M TVL
                'total_staked': 8000000,
                'active_users': 800,
                'pools': ['ALGO', 'HMBL'],
                'governance_token_price': 0.03,
                'governance_market_cap': 3000000
            }
        }

        return mock_data.get(protocol_name, {})

    async def calculate_protocol_exposure(self, user_positions: Dict[str, float]) -> CrossProtocolExposure:
        """Calculate cross-protocol exposure analysis"""
        logger.info("Analyzing DeFi protocol exposure...")

        # Get total DeFi TVL for percentage calculations
        total_defi_tvl = await self._get_total_defi_tvl()
        total_user_exposure = sum(user_positions.values())

        protocol_exposures = []

        for protocol_name, user_exposure_usd in user_positions.items():
            if user_exposure_usd <= 0:
                continue

            # Get protocol data
            protocol_data = await self.get_protocol_data(protocol_name)
            protocol_config = self.config['algorand_protocols'].get(protocol_name, {})

            if not protocol_data:
                logger.warning(f"No data available for protocol: {protocol_name}")
                continue

            # Calculate TVL percentage
            protocol_tvl = protocol_data.get('tvl_usd', 0)
            tvl_percentage = (protocol_tvl / total_defi_tvl) * 100 if total_defi_tvl > 0 else 0

            # Calculate user exposure percentage
            exposure_percentage = (user_exposure_usd / total_user_exposure) * 100

            # Calculate concentration risk score
            concentration_risk = self._calculate_concentration_risk(
                exposure_percentage,
                tvl_percentage,
                protocol_config.get('risk_tier', 'tier_3')
            )

            # Calculate liquidity risk score
            liquidity_risk = self._calculate_liquidity_risk(protocol_data, protocol_config)

            exposure = ProtocolExposure(
                protocol_name=protocol_name,
                category=protocol_config.get('category', 'unknown'),
                tvl_usd=protocol_tvl,
                tvl_percentage=tvl_percentage,
                risk_tier=protocol_config.get('risk_tier', 'tier_3'),
                user_exposure_usd=user_exposure_usd,
                exposure_percentage=exposure_percentage,
                concentration_risk_score=concentration_risk,
                liquidity_risk_score=liquidity_risk
            )

            protocol_exposures.append(exposure)

        # Calculate overall risk scores
        concentration_score = self._calculate_overall_concentration_risk(protocol_exposures)
        diversification_score = self._calculate_diversification_score(protocol_exposures)
        systemic_risk_score = self._calculate_systemic_risk_score(protocol_exposures)

        # Determine risk level
        risk_level = self._determine_risk_level(concentration_score, systemic_risk_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(protocol_exposures, concentration_score, diversification_score)

        return CrossProtocolExposure(
            total_exposure_usd=total_user_exposure,
            protocol_exposures=protocol_exposures,
            concentration_risk_score=concentration_score,
            diversification_score=diversification_score,
            systemic_risk_score=systemic_risk_score,
            risk_level=risk_level,
            recommendations=recommendations,
            timestamp=datetime.now()
        )

    async def _get_total_defi_tvl(self) -> float:
        """Get total Algorand DeFi TVL"""
        # Mock total DeFi TVL - in production, fetch from DeFiLlama or similar
        return 125000000  # $125M total Algorand DeFi TVL

    def _calculate_concentration_risk(self, exposure_percentage: float, tvl_percentage: float, risk_tier: str) -> float:
        """Calculate concentration risk score for a protocol"""
        # Base concentration risk from exposure percentage
        base_risk = min(exposure_percentage / 40, 1.0)  # 40% = max concentration

        # Adjust for protocol size (TVL percentage)
        size_adjustment = 1.0 - (tvl_percentage / 100) * 0.2  # Larger protocols = lower risk

        # Adjust for risk tier
        tier_multipliers = {
            'tier_1': 0.8,   # 20% risk reduction for tier 1
            'tier_2': 1.0,   # No adjustment for tier 2
            'tier_3': 1.3    # 30% risk increase for tier 3
        }
        tier_multiplier = tier_multipliers.get(risk_tier, 1.2)

        concentration_risk = base_risk * size_adjustment * tier_multiplier
        return min(concentration_risk, 1.0)

    def _calculate_liquidity_risk(self, protocol_data: Dict, protocol_config: Dict) -> float:
        """Calculate liquidity risk score for a protocol"""
        tvl = protocol_data.get('tvl_usd', 0)
        volume_24h = protocol_data.get('total_volume_24h', protocol_data.get('total_borrowed', 0) * 0.1)

        # Calculate volume to TVL ratio
        volume_tvl_ratio = volume_24h / tvl if tvl > 0 else 0

        # Base liquidity risk (higher volume/TVL ratio = lower risk)
        base_liquidity_risk = max(0.1, 1.0 - (volume_tvl_ratio * 10))  # 10% volume/TVL = good liquidity

        # Adjust for category
        category_adjustments = {
            'lending': 1.2,    # Lending protocols have higher liquidity risk
            'dex': 0.8,        # DEXs have lower liquidity risk
            'staking': 1.1,    # Staking protocols have moderate risk
            'bridge': 1.4      # Bridges have highest liquidity risk
        }
        category = protocol_config.get('category', 'unknown')
        category_multiplier = category_adjustments.get(category, 1.0)

        liquidity_risk = base_liquidity_risk * category_multiplier
        return min(liquidity_risk, 1.0)

    def _calculate_overall_concentration_risk(self, exposures: List[ProtocolExposure]) -> float:
        """Calculate overall portfolio concentration risk"""
        if not exposures:
            return 0.0

        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum((exp.exposure_percentage / 100) ** 2 for exp in exposures)

        # Convert HHI to risk score (0-1, where 1 is maximum concentration)
        concentration_risk = min(hhi, 1.0)

        # Adjust for individual protocol concentration risks
        weighted_protocol_risk = sum(
            exp.concentration_risk_score * (exp.exposure_percentage / 100)
            for exp in exposures
        )

        # Combine HHI and weighted protocol risks
        overall_risk = (concentration_risk * 0.6) + (weighted_protocol_risk * 0.4)

        return min(overall_risk, 1.0)

    def _calculate_diversification_score(self, exposures: List[ProtocolExposure]) -> float:
        """Calculate portfolio diversification score"""
        if not exposures:
            return 0.0

        # Count unique categories
        categories = set(exp.category for exp in exposures)
        category_count = len(categories)

        # Count unique risk tiers
        risk_tiers = set(exp.risk_tier for exp in exposures)
        tier_count = len(risk_tiers)

        # Calculate category diversification
        category_weights = {}
        for exp in exposures:
            category_weights[exp.category] = category_weights.get(exp.category, 0) + exp.exposure_percentage

        # Shannon diversity index for categories
        total_weight = sum(category_weights.values())
        category_entropy = 0
        if total_weight > 0:
            for weight in category_weights.values():
                if weight > 0:
                    p = weight / total_weight
                    category_entropy -= p * np.log2(p)

        # Normalize entropy (max entropy for 4 categories ≈ 2)
        max_entropy = np.log2(min(4, len(category_weights))) if category_weights else 1
        normalized_entropy = category_entropy / max_entropy if max_entropy > 0 else 0

        # Protocol count bonus
        protocol_count_score = min(len(exposures) / 5, 1.0)  # 5 protocols = perfect count score

        # Tier diversification bonus
        tier_score = min(tier_count / 2, 1.0)  # 2+ tiers = perfect tier score

        # Combine scores
        diversification_score = (normalized_entropy * 0.5) + (protocol_count_score * 0.3) + (tier_score * 0.2)

        return min(diversification_score, 1.0)

    def _calculate_systemic_risk_score(self, exposures: List[ProtocolExposure]) -> float:
        """Calculate systemic risk score based on protocol correlations"""
        if len(exposures) < 2:
            return 0.0

        correlations = self.config.get('protocol_correlations', {})
        total_systemic_risk = 0.0
        pair_count = 0

        # Calculate weighted correlation risk
        for i, exp1 in enumerate(exposures):
            for j, exp2 in enumerate(exposures[i+1:], i+1):
                # Get correlation between protocols
                correlation_key = f"{exp1.protocol_name}_{exp2.protocol_name}"
                reverse_key = f"{exp2.protocol_name}_{exp1.protocol_name}"

                correlation = correlations.get(correlation_key, correlations.get(reverse_key, 0.5))

                # If same category, use category correlation
                if exp1.category == exp2.category:
                    category_corr_key = f"{exp1.category}_protocols_correlation"
                    correlation = max(correlation, correlations.get(category_corr_key, 0.6))

                # Weight by exposure sizes
                weight1 = exp1.exposure_percentage / 100
                weight2 = exp2.exposure_percentage / 100
                combined_weight = weight1 * weight2

                # Systemic risk increases with correlation and combined exposure
                pair_systemic_risk = correlation * combined_weight * 2  # 2x multiplier for pairs
                total_systemic_risk += pair_systemic_risk
                pair_count += 1

        # Normalize by number of pairs
        if pair_count > 0:
            avg_systemic_risk = total_systemic_risk / pair_count
        else:
            avg_systemic_risk = 0.0

        return min(avg_systemic_risk, 1.0)

    def _determine_risk_level(self, concentration_score: float, systemic_risk_score: float) -> str:
        """Determine overall risk level based on risk scores"""
        combined_risk = (concentration_score * 0.6) + (systemic_risk_score * 0.4)

        if combined_risk >= 0.8:
            return "CRITICAL"
        elif combined_risk >= 0.6:
            return "HIGH"
        elif combined_risk >= 0.4:
            return "MODERATE"
        elif combined_risk >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"

    def _generate_recommendations(self, exposures: List[ProtocolExposure],
                                concentration_score: float, diversification_score: float) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []

        # Concentration risk recommendations
        if concentration_score > 0.6:
            # Find most concentrated positions
            max_exposure = max(exposures, key=lambda x: x.exposure_percentage)
            if max_exposure.exposure_percentage > 40:
                recommendations.append(
                    f"CRITICAL: Reduce {max_exposure.protocol_name} exposure below 40% "
                    f"(currently {max_exposure.exposure_percentage:.1f}%)"
                )

        # Category concentration recommendations
        category_exposures = {}
        for exp in exposures:
            category_exposures[exp.category] = category_exposures.get(exp.category, 0) + exp.exposure_percentage

        for category, total_exposure in category_exposures.items():
            if total_exposure > 60:
                recommendations.append(
                    f"HIGH: Reduce {category} protocol exposure below 60% "
                    f"(currently {total_exposure:.1f}%)"
                )

        # Diversification recommendations
        if diversification_score < 0.4:
            unique_categories = set(exp.category for exp in exposures)
            if len(unique_categories) < 3:
                recommendations.append(
                    "MEDIUM: Diversify across more protocol categories (lending, DEX, staking)"
                )

            if len(exposures) < 3:
                recommendations.append(
                    "MEDIUM: Increase protocol diversification to at least 3 different protocols"
                )

        # Risk tier recommendations
        tier_3_exposure = sum(exp.exposure_percentage for exp in exposures if exp.risk_tier == 'tier_3')
        if tier_3_exposure > 20:
            recommendations.append(
                f"MEDIUM: Reduce Tier 3 protocol exposure below 20% (currently {tier_3_exposure:.1f}%)"
            )

        # High liquidity risk recommendations
        high_liquidity_risk_protocols = [
            exp for exp in exposures if exp.liquidity_risk_score > 0.7
        ]
        if high_liquidity_risk_protocols:
            protocol_names = [exp.protocol_name for exp in high_liquidity_risk_protocols]
            recommendations.append(
                f"HIGH: Monitor liquidity risk in protocols: {', '.join(protocol_names)}"
            )

        if not recommendations:
            recommendations.append("Good diversification! Continue monitoring protocol risks.")

        return recommendations

    async def monitor_protocol_exposure(self, user_positions: Dict[str, float],
                                      alert_threshold: float = 0.1) -> Dict[str, Any]:
        """Monitor protocol exposure changes and generate alerts"""
        current_analysis = await self.calculate_protocol_exposure(user_positions)

        alerts = []

        # Check concentration alerts
        for exposure in current_analysis.protocol_exposures:
            if exposure.concentration_risk_score > 0.7:
                alerts.append({
                    'type': 'concentration_risk',
                    'severity': 'HIGH',
                    'protocol': exposure.protocol_name,
                    'message': f"High concentration risk in {exposure.protocol_name}: "
                              f"{exposure.exposure_percentage:.1f}% exposure"
                })

        # Check systemic risk alerts
        if current_analysis.systemic_risk_score > 0.6:
            alerts.append({
                'type': 'systemic_risk',
                'severity': 'HIGH',
                'message': f"High systemic risk detected: {current_analysis.systemic_risk_score:.2f}"
            })

        return {
            'analysis': current_analysis,
            'alerts': alerts,
            'monitoring_timestamp': datetime.now()
        }

# Example usage
async def main():
    """Example usage of the protocol exposure analyzer"""
    async with ProtocolExposureAnalyzer() as analyzer:
        # Example user positions across Algorand DeFi protocols
        user_positions = {
            'algofi': 50000,      # $50k in Algofi
            'folks_finance': 30000, # $30k in Folks Finance
            'tinyman': 15000,     # $15k in Tinyman
            'pact': 5000          # $5k in Pact
        }

        # Analyze protocol exposure
        exposure_analysis = await analyzer.calculate_protocol_exposure(user_positions)

        print(f"\n=== DeFi Protocol Exposure Analysis ===")
        print(f"Total Exposure: ${exposure_analysis.total_exposure_usd:,.2f}")
        print(f"Risk Level: {exposure_analysis.risk_level}")
        print(f"Concentration Risk: {exposure_analysis.concentration_risk_score:.2f}")
        print(f"Diversification Score: {exposure_analysis.diversification_score:.2f}")
        print(f"Systemic Risk: {exposure_analysis.systemic_risk_score:.2f}")

        print(f"\n=== Protocol Breakdown ===")
        for exp in exposure_analysis.protocol_exposures:
            print(f"{exp.protocol_name} ({exp.category}):")
            print(f"  Exposure: ${exp.user_exposure_usd:,.2f} ({exp.exposure_percentage:.1f}%)")
            print(f"  Risk Tier: {exp.risk_tier}")
            print(f"  Concentration Risk: {exp.concentration_risk_score:.2f}")
            print(f"  Liquidity Risk: {exp.liquidity_risk_score:.2f}")

        print(f"\n=== Recommendations ===")
        for i, rec in enumerate(exposure_analysis.recommendations, 1):
            print(f"{i}. {rec}")

if __name__ == "__main__":
    asyncio.run(main())