"""
Liquidation Cascade Modeler - Advanced cascade effect modeling across Algorand DeFi ecosystem

This module models how liquidations propagate across multiple protocols and markets,
analyzing the cascade effects and systemic risks that emerge from interconnected liquidations.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CascadeLevel(Enum):
    """Cascade propagation levels"""
    PRIMARY = "primary"      # Initial liquidation
    SECONDARY = "secondary"  # Direct impact
    TERTIARY = "tertiary"    # Second-order effects
    SYSTEMIC = "systemic"    # System-wide effects

class ProtocolType(Enum):
    """Types of DeFi protocols"""
    LENDING = "lending"
    DEX = "dex"
    STABLECOIN = "stablecoin"
    BRIDGE = "bridge"
    SYNTHETIC = "synthetic"

@dataclass
class LiquidationEvent:
    """Represents a liquidation event"""
    protocol: str
    asset: str
    amount_usd: float
    collateral_asset: str
    collateral_amount: float
    liquidation_price: float
    timestamp: datetime
    cascade_level: CascadeLevel = CascadeLevel.PRIMARY
    triggered_by: Optional[str] = None
    market_impact: float = 0.0
    contagion_risk: float = 0.0

@dataclass
class ProtocolState:
    """Current state of a DeFi protocol"""
    name: str
    protocol_type: ProtocolType
    total_tvl: float
    available_liquidity: float
    utilization_rate: float
    health_factor: float
    liquidation_threshold: float
    outstanding_loans: float
    collateral_value: float
    risk_level: float = 0.0
    stress_multiplier: float = 1.0

@dataclass
class CascadeResult:
    """Result of cascade modeling"""
    initial_event: LiquidationEvent
    cascade_events: List[LiquidationEvent]
    total_impact_usd: float
    affected_protocols: List[str]
    max_cascade_level: CascadeLevel
    systemic_risk_score: float
    recovery_time_hours: float
    price_impacts: Dict[str, float]
    liquidity_impacts: Dict[str, float]

class LiquidationCascadeModeler:
    """
    Advanced liquidation cascade modeling engine that simulates how liquidations
    propagate across the Algorand DeFi ecosystem.
    """

    def __init__(self, config_path: str = None):
        """Initialize the cascade modeler"""
        self.config = self._load_config(config_path)
        self.protocols: Dict[str, ProtocolState] = {}
        self.connections: Dict[str, Dict[str, float]] = {}
        self.market_data: Dict[str, Any] = {}
        self.cascade_history: List[CascadeResult] = []

        # Cascade parameters from config
        self.max_cascade_depth = self.config['cascade']['max_cascade_depth']
        self.cascade_dampening = self.config['cascade']['cascade_dampening']
        self.contagion_threshold = self.config['cascade']['contagion_threshold']
        self.cross_protocol_impact = self.config['cascade']['cross_protocol_impact']

        # Initialize protocol network
        self._initialize_protocol_network()

        logger.info("Liquidation Cascade Modeler initialized")

    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _initialize_protocol_network(self):
        """Initialize the network of protocols and their connections"""
        # Define major Algorand DeFi protocols
        protocols = {
            'algofi': ProtocolState(
                name='algofi',
                protocol_type=ProtocolType.LENDING,
                total_tvl=50_000_000,
                available_liquidity=15_000_000,
                utilization_rate=0.7,
                health_factor=1.5,
                liquidation_threshold=0.85,
                outstanding_loans=35_000_000,
                collateral_value=45_000_000
            ),
            'folks_finance': ProtocolState(
                name='folks_finance',
                protocol_type=ProtocolType.LENDING,
                total_tvl=30_000_000,
                available_liquidity=10_000_000,
                utilization_rate=0.65,
                health_factor=1.6,
                liquidation_threshold=0.8,
                outstanding_loans=20_000_000,
                collateral_value=28_000_000
            ),
            'tinyman': ProtocolState(
                name='tinyman',
                protocol_type=ProtocolType.DEX,
                total_tvl=25_000_000,
                available_liquidity=20_000_000,
                utilization_rate=0.8,
                health_factor=1.8,
                liquidation_threshold=0.0,  # DEXs don't have liquidation
                outstanding_loans=0,
                collateral_value=0
            ),
            'pact': ProtocolState(
                name='pact',
                protocol_type=ProtocolType.DEX,
                total_tvl=15_000_000,
                available_liquidity=12_000_000,
                utilization_rate=0.75,
                health_factor=1.7,
                liquidation_threshold=0.0,
                outstanding_loans=0,
                collateral_value=0
            ),
            'gard': ProtocolState(
                name='gard',
                protocol_type=ProtocolType.STABLECOIN,
                total_tvl=10_000_000,
                available_liquidity=5_000_000,
                utilization_rate=0.5,
                health_factor=1.3,
                liquidation_threshold=0.9,
                outstanding_loans=8_000_000,
                collateral_value=12_000_000
            )
        }

        self.protocols = protocols

        # Define protocol connections (how liquidations can spread)
        self.connections = {
            'algofi': {
                'folks_finance': 0.6,  # High correlation due to similar user base
                'tinyman': 0.8,        # High due to liquidation execution
                'pact': 0.5,           # Medium correlation
                'gard': 0.7            # High due to stablecoin usage
            },
            'folks_finance': {
                'algofi': 0.6,
                'tinyman': 0.7,
                'pact': 0.4,
                'gard': 0.5
            },
            'tinyman': {
                'algofi': 0.8,
                'folks_finance': 0.7,
                'pact': 0.9,           # Very high DEX-to-DEX correlation
                'gard': 0.6
            },
            'pact': {
                'algofi': 0.5,
                'folks_finance': 0.4,
                'tinyman': 0.9,
                'gard': 0.4
            },
            'gard': {
                'algofi': 0.7,
                'folks_finance': 0.5,
                'tinyman': 0.6,
                'pact': 0.4
            }
        }

    async def model_liquidation_cascade(
        self,
        initial_liquidation: LiquidationEvent,
        market_conditions: Dict[str, float] = None
    ) -> CascadeResult:
        """
        Model the complete liquidation cascade from an initial event

        Args:
            initial_liquidation: The initial liquidation event
            market_conditions: Current market conditions (volatility, liquidity, etc.)

        Returns:
            Complete cascade analysis result
        """
        logger.info(f"Modeling liquidation cascade from {initial_liquidation.protocol}")

        if market_conditions is None:
            market_conditions = self._get_default_market_conditions()

        cascade_events = [initial_liquidation]
        affected_protocols = {initial_liquidation.protocol}
        price_impacts = {}
        liquidity_impacts = {}

        current_level = CascadeLevel.PRIMARY
        cascade_depth = 0
        total_impact = initial_liquidation.amount_usd

        # Track the cascade propagation
        events_to_process = [initial_liquidation]

        while events_to_process and cascade_depth < self.max_cascade_depth:
            cascade_depth += 1
            next_level_events = []

            for event in events_to_process:
                # Calculate secondary effects from this event
                secondary_events = await self._calculate_secondary_liquidations(
                    event, market_conditions, cascade_depth
                )

                for secondary_event in secondary_events:
                    if secondary_event.protocol not in affected_protocols:
                        affected_protocols.add(secondary_event.protocol)
                        cascade_events.append(secondary_event)
                        next_level_events.append(secondary_event)
                        total_impact += secondary_event.amount_usd

                        # Calculate price and liquidity impacts
                        price_impact = self._calculate_price_impact(secondary_event)
                        liquidity_impact = self._calculate_liquidity_impact(secondary_event)

                        price_impacts[secondary_event.asset] = price_impact
                        liquidity_impacts[secondary_event.protocol] = liquidity_impact

            events_to_process = next_level_events

            # Apply dampening - each level has reduced impact
            for event in events_to_process:
                event.amount_usd *= self.cascade_dampening
                event.market_impact *= self.cascade_dampening

        # Determine maximum cascade level reached
        max_level = self._determine_max_cascade_level(cascade_events)

        # Calculate systemic risk score
        systemic_risk = self._calculate_systemic_risk_score(
            cascade_events, affected_protocols, total_impact
        )

        # Estimate recovery time
        recovery_time = self._estimate_recovery_time(
            cascade_events, market_conditions
        )

        result = CascadeResult(
            initial_event=initial_liquidation,
            cascade_events=cascade_events[1:],  # Exclude initial event
            total_impact_usd=total_impact,
            affected_protocols=list(affected_protocols),
            max_cascade_level=max_level,
            systemic_risk_score=systemic_risk,
            recovery_time_hours=recovery_time,
            price_impacts=price_impacts,
            liquidity_impacts=liquidity_impacts
        )

        self.cascade_history.append(result)

        logger.info(f"Cascade modeling complete: {len(cascade_events)} events, "
                   f"${total_impact:,.0f} total impact")

        return result

    async def _calculate_secondary_liquidations(
        self,
        trigger_event: LiquidationEvent,
        market_conditions: Dict[str, float],
        cascade_depth: int
    ) -> List[LiquidationEvent]:
        """Calculate secondary liquidations triggered by an event"""
        secondary_events = []

        # Get protocols connected to the trigger event's protocol
        if trigger_event.protocol not in self.connections:
            return secondary_events

        connected_protocols = self.connections[trigger_event.protocol]

        for protocol_name, connection_strength in connected_protocols.items():
            if protocol_name == trigger_event.protocol:
                continue

            protocol = self.protocols.get(protocol_name)
            if not protocol:
                continue

            # Calculate contagion probability
            contagion_prob = self._calculate_contagion_probability(
                trigger_event, protocol, connection_strength, market_conditions
            )

            if contagion_prob > self.contagion_threshold:
                # Generate secondary liquidation event
                secondary_event = self._generate_secondary_event(
                    trigger_event, protocol, contagion_prob, cascade_depth
                )

                if secondary_event:
                    secondary_events.append(secondary_event)

        return secondary_events

    def _calculate_contagion_probability(
        self,
        trigger_event: LiquidationEvent,
        target_protocol: ProtocolState,
        connection_strength: float,
        market_conditions: Dict[str, float]
    ) -> float:
        """Calculate the probability of contagion to target protocol"""

        # Base contagion probability from connection strength
        base_prob = connection_strength * self.cross_protocol_impact

        # Adjust for trigger event size
        size_factor = min(trigger_event.amount_usd / 1_000_000, 2.0)  # Cap at 2x

        # Adjust for target protocol health
        health_factor = 2.0 - target_protocol.health_factor  # Lower health = higher risk
        health_factor = max(0.1, min(health_factor, 1.5))

        # Adjust for market conditions
        volatility = market_conditions.get('volatility', 0.2)
        liquidity_stress = market_conditions.get('liquidity_stress', 0.1)
        correlation_stress = market_conditions.get('correlation_stress', 0.1)

        market_stress_factor = 1.0 + volatility + liquidity_stress + correlation_stress

        # Calculate final contagion probability
        contagion_prob = base_prob * size_factor * health_factor * market_stress_factor

        return min(contagion_prob, 0.95)  # Cap at 95%

    def _generate_secondary_event(
        self,
        trigger_event: LiquidationEvent,
        target_protocol: ProtocolState,
        contagion_prob: float,
        cascade_depth: int
    ) -> Optional[LiquidationEvent]:
        """Generate a secondary liquidation event"""

        if target_protocol.protocol_type == ProtocolType.DEX:
            # DEXs don't have liquidations but can have liquidity impacts
            return None

        # Calculate liquidation amount based on trigger event and protocol state
        liquidation_ratio = contagion_prob * 0.1  # Max 10% of collateral
        liquidation_amount = target_protocol.collateral_value * liquidation_ratio

        if liquidation_amount < 1000:  # Minimum threshold
            return None

        # Determine cascade level
        cascade_level = self._get_cascade_level(cascade_depth)

        # Create secondary liquidation event
        secondary_event = LiquidationEvent(
            protocol=target_protocol.name,
            asset="ALGO",  # Simplified - could be more sophisticated
            amount_usd=liquidation_amount,
            collateral_asset="ALGO",
            collateral_amount=liquidation_amount / 0.5,  # Assume $0.5 ALGO price
            liquidation_price=0.5,
            timestamp=trigger_event.timestamp + timedelta(minutes=cascade_depth * 5),
            cascade_level=cascade_level,
            triggered_by=trigger_event.protocol,
            market_impact=contagion_prob * 0.05,  # 5% max market impact
            contagion_risk=contagion_prob
        )

        return secondary_event

    def _get_cascade_level(self, depth: int) -> CascadeLevel:
        """Determine cascade level based on depth"""
        if depth == 1:
            return CascadeLevel.SECONDARY
        elif depth == 2:
            return CascadeLevel.TERTIARY
        else:
            return CascadeLevel.SYSTEMIC

    def _calculate_price_impact(self, event: LiquidationEvent) -> float:
        """Calculate price impact of a liquidation event"""
        # Simplified price impact model
        # Real implementation would use order book data

        base_impact = event.market_impact
        size_impact = event.amount_usd / 10_000_000  # $10M reference

        total_impact = base_impact + size_impact * 0.02  # 2% per $10M

        return min(total_impact, 0.2)  # Cap at 20%

    def _calculate_liquidity_impact(self, event: LiquidationEvent) -> float:
        """Calculate liquidity impact on protocol"""
        protocol = self.protocols.get(event.protocol)
        if not protocol:
            return 0.0

        liquidity_ratio = event.amount_usd / protocol.available_liquidity

        return min(liquidity_ratio, 1.0)  # Cap at 100%

    def _determine_max_cascade_level(self, events: List[LiquidationEvent]) -> CascadeLevel:
        """Determine the maximum cascade level reached"""
        levels = [event.cascade_level for event in events]

        if CascadeLevel.SYSTEMIC in levels:
            return CascadeLevel.SYSTEMIC
        elif CascadeLevel.TERTIARY in levels:
            return CascadeLevel.TERTIARY
        elif CascadeLevel.SECONDARY in levels:
            return CascadeLevel.SECONDARY
        else:
            return CascadeLevel.PRIMARY

    def _calculate_systemic_risk_score(
        self,
        cascade_events: List[LiquidationEvent],
        affected_protocols: set,
        total_impact: float
    ) -> float:
        """Calculate overall systemic risk score (0-1)"""

        # Number of affected protocols
        protocol_factor = len(affected_protocols) / len(self.protocols)

        # Total impact relative to ecosystem TVL
        total_tvl = sum(p.total_tvl for p in self.protocols.values())
        impact_factor = total_impact / total_tvl

        # Cascade depth factor
        max_depth = max((0,) + tuple(
            i for i, event in enumerate(cascade_events)
            if event.cascade_level == CascadeLevel.SYSTEMIC
        ))
        depth_factor = min(max_depth / 5, 1.0)  # Normalize to 0-1

        # Contagion intensity
        contagion_factor = np.mean([event.contagion_risk for event in cascade_events])

        # Weighted systemic risk score
        systemic_risk = (
            0.3 * protocol_factor +
            0.3 * impact_factor +
            0.2 * depth_factor +
            0.2 * contagion_factor
        )

        return min(systemic_risk, 1.0)

    def _estimate_recovery_time(
        self,
        cascade_events: List[LiquidationEvent],
        market_conditions: Dict[str, float]
    ) -> float:
        """Estimate recovery time in hours"""

        # Base recovery time from config
        base_recovery = self.config['cascade']['recovery_period'] / 3600  # Convert to hours

        # Adjust for cascade severity
        severity_factor = len(cascade_events) / 10  # Normalize

        # Adjust for market conditions
        volatility = market_conditions.get('volatility', 0.2)
        liquidity_stress = market_conditions.get('liquidity_stress', 0.1)

        stress_factor = 1.0 + volatility + liquidity_stress

        # Calculate total recovery time
        recovery_time = base_recovery * (1 + severity_factor) * stress_factor

        return min(recovery_time, 72)  # Cap at 72 hours

    def _get_default_market_conditions(self) -> Dict[str, float]:
        """Get default market conditions"""
        return {
            'volatility': 0.2,
            'liquidity_stress': 0.1,
            'correlation_stress': 0.1,
            'market_depth': 0.8,
            'sentiment': 0.5
        }

    async def analyze_cascade_scenarios(
        self,
        scenarios: List[Dict[str, Any]]
    ) -> List[CascadeResult]:
        """Analyze multiple cascade scenarios"""
        results = []

        for scenario in scenarios:
            liquidation_event = LiquidationEvent(
                protocol=scenario['protocol'],
                asset=scenario['asset'],
                amount_usd=scenario['amount_usd'],
                collateral_asset=scenario.get('collateral_asset', 'ALGO'),
                collateral_amount=scenario.get('collateral_amount', scenario['amount_usd'] * 2),
                liquidation_price=scenario.get('liquidation_price', 0.5),
                timestamp=datetime.now()
            )

            market_conditions = scenario.get('market_conditions', self._get_default_market_conditions())

            result = await self.model_liquidation_cascade(liquidation_event, market_conditions)
            results.append(result)

        return results

    def get_cascade_statistics(self) -> Dict[str, Any]:
        """Get statistics about historical cascades"""
        if not self.cascade_history:
            return {"error": "No cascade history available"}

        return {
            "total_cascades": len(self.cascade_history),
            "avg_impact_usd": np.mean([r.total_impact_usd for r in self.cascade_history]),
            "max_impact_usd": max(r.total_impact_usd for r in self.cascade_history),
            "avg_affected_protocols": np.mean([len(r.affected_protocols) for r in self.cascade_history]),
            "avg_systemic_risk": np.mean([r.systemic_risk_score for r in self.cascade_history]),
            "avg_recovery_time": np.mean([r.recovery_time_hours for r in self.cascade_history]),
            "systemic_events": sum(1 for r in self.cascade_history if r.max_cascade_level == CascadeLevel.SYSTEMIC)
        }

    def update_protocol_state(self, protocol_name: str, new_state: Dict[str, Any]):
        """Update the state of a protocol"""
        if protocol_name not in self.protocols:
            logger.warning(f"Protocol {protocol_name} not found")
            return

        protocol = self.protocols[protocol_name]

        for key, value in new_state.items():
            if hasattr(protocol, key):
                setattr(protocol, key, value)

        # Recalculate risk level
        protocol.risk_level = self._calculate_protocol_risk_level(protocol)

        logger.info(f"Updated {protocol_name} state")

    def _calculate_protocol_risk_level(self, protocol: ProtocolState) -> float:
        """Calculate risk level for a protocol"""
        # Risk factors
        utilization_risk = protocol.utilization_rate
        health_risk = max(0, 2.0 - protocol.health_factor) / 2.0
        liquidity_risk = 1.0 - (protocol.available_liquidity / protocol.total_tvl)

        # Weighted risk score
        risk_level = (
            0.4 * utilization_risk +
            0.3 * health_risk +
            0.3 * liquidity_risk
        )

        return min(risk_level, 1.0)

    async def real_time_cascade_monitoring(self) -> Dict[str, Any]:
        """Monitor real-time cascade risk across all protocols"""
        cascade_risks = {}

        for protocol_name, protocol in self.protocols.items():
            if protocol.protocol_type == ProtocolType.LENDING:
                # Check if protocol is close to cascade conditions
                risk_indicators = {
                    'health_factor': protocol.health_factor,
                    'utilization_rate': protocol.utilization_rate,
                    'available_liquidity': protocol.available_liquidity,
                    'risk_level': protocol.risk_level
                }

                # Calculate immediate cascade probability
                cascade_prob = self._calculate_immediate_cascade_probability(protocol)

                cascade_risks[protocol_name] = {
                    'cascade_probability': cascade_prob,
                    'risk_indicators': risk_indicators,
                    'alert_level': self._get_alert_level(cascade_prob)
                }

        return {
            'timestamp': datetime.now().isoformat(),
            'protocol_risks': cascade_risks,
            'system_wide_risk': self._calculate_system_wide_cascade_risk(cascade_risks)
        }

    def _calculate_immediate_cascade_probability(self, protocol: ProtocolState) -> float:
        """Calculate immediate cascade probability for a protocol"""
        # Health factor risk
        health_risk = max(0, (1.5 - protocol.health_factor) / 1.5)

        # Utilization risk
        util_risk = max(0, (protocol.utilization_rate - 0.8) / 0.2)

        # Liquidity risk
        liquidity_ratio = protocol.available_liquidity / protocol.total_tvl
        liquidity_risk = max(0, (0.2 - liquidity_ratio) / 0.2)

        # Combined probability
        cascade_prob = (health_risk * 0.5 + util_risk * 0.3 + liquidity_risk * 0.2)

        return min(cascade_prob, 1.0)

    def _get_alert_level(self, cascade_prob: float) -> str:
        """Get alert level based on cascade probability"""
        if cascade_prob < 0.2:
            return "LOW"
        elif cascade_prob < 0.5:
            return "MEDIUM"
        elif cascade_prob < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"

    def _calculate_system_wide_cascade_risk(self, protocol_risks: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate system-wide cascade risk"""
        if not protocol_risks:
            return {"risk_level": 0.0, "alert_level": "LOW"}

        # Average cascade probability across protocols
        avg_cascade_prob = np.mean([
            risk['cascade_probability'] for risk in protocol_risks.values()
        ])

        # Number of high-risk protocols
        high_risk_count = sum(
            1 for risk in protocol_risks.values()
            if risk['cascade_probability'] > 0.5
        )

        # System interconnectedness factor
        interconnect_factor = len(protocol_risks) / len(self.protocols)

        # System-wide risk
        system_risk = avg_cascade_prob * interconnect_factor * (1 + high_risk_count * 0.1)

        return {
            'risk_level': min(system_risk, 1.0),
            'alert_level': self._get_alert_level(system_risk),
            'high_risk_protocols': high_risk_count,
            'interconnectedness': interconnect_factor
        }


# Example usage and testing
async def main():
    """Example usage of the liquidation cascade modeler"""
    modeler = LiquidationCascadeModeler()

    # Create a test liquidation event
    test_liquidation = LiquidationEvent(
        protocol="algofi",
        asset="ALGO",
        amount_usd=5_000_000,  # $5M liquidation
        collateral_asset="ALGO",
        collateral_amount=10_000_000,  # $10M collateral
        liquidation_price=0.5,
        timestamp=datetime.now()
    )

    # Model the cascade
    result = await modeler.model_liquidation_cascade(test_liquidation)

    print(f"Cascade Analysis Results:")
    print(f"Total Impact: ${result.total_impact_usd:,.0f}")
    print(f"Affected Protocols: {result.affected_protocols}")
    print(f"Max Cascade Level: {result.max_cascade_level.value}")
    print(f"Systemic Risk Score: {result.systemic_risk_score:.3f}")
    print(f"Recovery Time: {result.recovery_time_hours:.1f} hours")

    # Monitor real-time risks
    risk_monitor = await modeler.real_time_cascade_monitoring()
    print(f"\nReal-time Risk Monitoring:")
    print(f"System Risk Level: {risk_monitor['system_wide_risk']['risk_level']:.3f}")
    print(f"Alert Level: {risk_monitor['system_wide_risk']['alert_level']}")

if __name__ == "__main__":
    asyncio.run(main())