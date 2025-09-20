"""
Collateral Monitor

Real-time monitoring system for collateral values, risk metrics, and market conditions.
Provides alerts and automated adjustments based on market movements.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from .config import CollateralAdjustmentConfig
from .constants import CollateralAdjustmentConstants
from .calculator import CollateralAsset, CollateralPortfolio, CollateralRateCalculator


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class CollateralAlert:
    """Represents a collateral monitoring alert"""
    alert_id: str
    level: AlertLevel
    asset_symbol: str
    alert_type: str
    message: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    portfolio_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringPosition:
    """Represents a position being monitored"""
    portfolio_id: str
    portfolio: CollateralPortfolio
    base_rate: float
    last_rate_adjustment: Optional[float] = None
    last_update: Optional[datetime] = None
    alert_history: List[CollateralAlert] = field(default_factory=list)
    monitoring_enabled: bool = True


class CollateralMonitor:
    """
    Real-time collateral monitoring system with automated alerts and adjustments
    """

    def __init__(self, config: CollateralAdjustmentConfig):
        """Initialize the monitor with configuration"""
        self.config = config
        self.constants = CollateralAdjustmentConstants()
        self.calculator = CollateralRateCalculator(config)

        self._monitored_positions: Dict[str, MonitoringPosition] = {}
        self._alert_callbacks: List[Callable[[CollateralAlert], None]] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # Monitoring state
        self._price_cache: Dict[str, Dict[str, Any]] = {}
        self._market_conditions: Dict[str, Any] = {}
        self._emergency_mode = False

        self.logger = logging.getLogger(__name__)

    async def start_monitoring(self) -> None:
        """Start the monitoring service"""
        if self._running:
            self.logger.warning("Monitor is already running")
            return

        self._running = True
        self.logger.info("Starting collateral monitoring service")

        # Start monitoring task
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop the monitoring service"""
        if not self._running:
            return

        self._running = False
        self.logger.info("Stopping collateral monitoring service")

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

    def add_position(
        self,
        portfolio_id: str,
        portfolio: CollateralPortfolio,
        base_rate: float
    ) -> None:
        """Add a position to monitor"""
        position = MonitoringPosition(
            portfolio_id=portfolio_id,
            portfolio=portfolio,
            base_rate=base_rate,
            last_update=datetime.now()
        )

        self._monitored_positions[portfolio_id] = position
        self.logger.info(f"Added position {portfolio_id} to monitoring")

    def remove_position(self, portfolio_id: str) -> None:
        """Remove a position from monitoring"""
        if portfolio_id in self._monitored_positions:
            del self._monitored_positions[portfolio_id]
            self.logger.info(f"Removed position {portfolio_id} from monitoring")

    def add_alert_callback(self, callback: Callable[[CollateralAlert], None]) -> None:
        """Add callback function for alerts"""
        self._alert_callbacks.append(callback)

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self._running:
            try:
                # Update market conditions
                await self._update_market_conditions()

                # Update asset prices
                await self._update_asset_prices()

                # Check all monitored positions
                for position_id, position in self._monitored_positions.items():
                    await self._check_position(position_id, position)

                # Determine sleep interval
                sleep_interval = (
                    self.config.monitoring.emergency_check_interval
                    if self._emergency_mode
                    else self.config.monitoring.price_update_interval
                )

                await asyncio.sleep(sleep_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.config.monitoring.price_update_interval)

    async def _update_market_conditions(self) -> None:
        """Update overall market conditions"""
        try:
            # This would integrate with external market data sources
            # For now, we'll simulate market condition detection

            # Check for market stress indicators
            self._market_conditions = {
                'market_stress': False,
                'liquidity_crisis': False,
                'protocol_exploit': False,
                'regulatory_uncertainty': False,
                'volatility_spike': False,
                'last_update': datetime.now()
            }

            # Example: Check if any major assets have high volatility
            high_volatility_count = 0
            for symbol, price_data in self._price_cache.items():
                if price_data.get('volatility_24h', 0) > self.constants.MONITORING_THRESHOLDS['volatility_spike']:
                    high_volatility_count += 1

            if high_volatility_count > 3:  # Threshold for market stress
                self._market_conditions['market_stress'] = True
                self._market_conditions['volatility_spike'] = True

        except Exception as e:
            self.logger.error(f"Error updating market conditions: {e}")

    async def _update_asset_prices(self) -> None:
        """Update asset prices for all monitored assets"""
        try:
            # Get unique asset symbols from all positions
            asset_symbols = set()
            for position in self._monitored_positions.values():
                for asset in position.portfolio.assets:
                    asset_symbols.add(asset.symbol)

            # Update prices for each asset
            for symbol in asset_symbols:
                await self._update_asset_price(symbol)

        except Exception as e:
            self.logger.error(f"Error updating asset prices: {e}")

    async def _update_asset_price(self, symbol: str) -> None:
        """Update price for a specific asset"""
        try:
            # This would integrate with MCP services or external APIs
            # For now, we'll simulate price updates

            current_data = self._price_cache.get(symbol, {})
            old_price = current_data.get('price', 100.0)

            # Simulate price movement (replace with real data source)
            import random
            price_change = random.uniform(-0.05, 0.05)  # ±5% movement
            new_price = old_price * (1 + price_change)

            # Calculate volatility
            price_history = current_data.get('price_history', [old_price])
            price_history.append(new_price)
            if len(price_history) > 24:  # Keep 24 hours of data
                price_history = price_history[-24:]

            volatility_24h = self._calculate_volatility(price_history)

            self._price_cache[symbol] = {
                'price': new_price,
                'price_change_24h': price_change,
                'volatility_24h': volatility_24h,
                'price_history': price_history,
                'last_update': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Error updating price for {symbol}: {e}")

    def _calculate_volatility(self, price_history: List[float]) -> float:
        """Calculate volatility from price history"""
        if len(price_history) < 2:
            return 0.0

        returns = []
        for i in range(1, len(price_history)):
            ret = (price_history[i] - price_history[i-1]) / price_history[i-1]
            returns.append(ret)

        if not returns:
            return 0.0

        # Calculate standard deviation of returns
        import statistics
        return statistics.stdev(returns) if len(returns) > 1 else 0.0

    async def _check_position(self, position_id: str, position: MonitoringPosition) -> None:
        """Check a specific position for alerts and adjustments"""
        try:
            # Update portfolio with current prices
            updated_portfolio = await self._update_portfolio_prices(position.portfolio)

            # Check for alerts
            alerts = await self._check_position_alerts(position_id, updated_portfolio)

            # Process alerts
            for alert in alerts:
                await self._process_alert(alert)
                position.alert_history.append(alert)

            # Calculate new rate adjustment if needed
            if self._should_recalculate_rate(position, alerts):
                await self._recalculate_position_rate(position_id, position, updated_portfolio)

            # Update position
            position.portfolio = updated_portfolio
            position.last_update = datetime.now()

        except Exception as e:
            self.logger.error(f"Error checking position {position_id}: {e}")

    async def _update_portfolio_prices(self, portfolio: CollateralPortfolio) -> CollateralPortfolio:
        """Update portfolio with current asset prices"""
        updated_assets = []

        for asset in portfolio.assets:
            price_data = self._price_cache.get(asset.symbol, {})
            new_price = price_data.get('price', asset.current_price)
            new_volatility = price_data.get('volatility_24h', asset.volatility_24h)

            updated_asset = CollateralAsset(
                symbol=asset.symbol,
                amount=asset.amount,
                current_price=new_price,
                market_cap=asset.market_cap,
                daily_volume=asset.daily_volume,
                volatility_24h=new_volatility,
                volatility_30d=asset.volatility_30d,
                liquidity_score=asset.liquidity_score,
                security_rating=asset.security_rating,
                asset_tier=asset.asset_tier,
                metadata=asset.metadata
            )
            updated_assets.append(updated_asset)

        # Recalculate portfolio metrics
        total_value = sum(asset.amount * asset.current_price for asset in updated_assets)
        new_ltv = portfolio.loan_amount_usd / total_value if total_value > 0 else 1.0

        return CollateralPortfolio(
            assets=updated_assets,
            total_value_usd=total_value,
            loan_amount_usd=portfolio.loan_amount_usd,
            current_ltv=new_ltv,
            diversification_score=portfolio.diversification_score,
            correlation_matrix=portfolio.correlation_matrix
        )

    async def _check_position_alerts(
        self,
        position_id: str,
        portfolio: CollateralPortfolio
    ) -> List[CollateralAlert]:
        """Check for alerts on a position"""
        alerts = []

        # LTV alerts
        if portfolio.current_ltv >= self.constants.MONITORING_THRESHOLDS['ltv_liquidation']:
            alerts.append(CollateralAlert(
                alert_id=f"{position_id}_ltv_liquidation_{datetime.now().isoformat()}",
                level=AlertLevel.EMERGENCY,
                asset_symbol="PORTFOLIO",
                alert_type="ltv_liquidation",
                message=f"LTV {portfolio.current_ltv:.1%} reached liquidation threshold",
                current_value=portfolio.current_ltv,
                threshold_value=self.constants.MONITORING_THRESHOLDS['ltv_liquidation'],
                timestamp=datetime.now(),
                portfolio_id=position_id
            ))
        elif portfolio.current_ltv >= self.constants.MONITORING_THRESHOLDS['ltv_critical']:
            alerts.append(CollateralAlert(
                alert_id=f"{position_id}_ltv_critical_{datetime.now().isoformat()}",
                level=AlertLevel.CRITICAL,
                asset_symbol="PORTFOLIO",
                alert_type="ltv_critical",
                message=f"LTV {portfolio.current_ltv:.1%} reached critical threshold",
                current_value=portfolio.current_ltv,
                threshold_value=self.constants.MONITORING_THRESHOLDS['ltv_critical'],
                timestamp=datetime.now(),
                portfolio_id=position_id
            ))
        elif portfolio.current_ltv >= self.constants.MONITORING_THRESHOLDS['ltv_warning']:
            alerts.append(CollateralAlert(
                alert_id=f"{position_id}_ltv_warning_{datetime.now().isoformat()}",
                level=AlertLevel.WARNING,
                asset_symbol="PORTFOLIO",
                alert_type="ltv_warning",
                message=f"LTV {portfolio.current_ltv:.1%} reached warning threshold",
                current_value=portfolio.current_ltv,
                threshold_value=self.constants.MONITORING_THRESHOLDS['ltv_warning'],
                timestamp=datetime.now(),
                portfolio_id=position_id
            ))

        # Price change alerts
        for asset in portfolio.assets:
            price_data = self._price_cache.get(asset.symbol, {})
            price_change = abs(price_data.get('price_change_24h', 0))

            if price_change >= self.constants.MONITORING_THRESHOLDS['price_change_alert']:
                alerts.append(CollateralAlert(
                    alert_id=f"{position_id}_{asset.symbol}_price_change_{datetime.now().isoformat()}",
                    level=AlertLevel.WARNING,
                    asset_symbol=asset.symbol,
                    alert_type="price_change",
                    message=f"{asset.symbol} price changed by {price_change:.1%} in 24h",
                    current_value=price_change,
                    threshold_value=self.constants.MONITORING_THRESHOLDS['price_change_alert'],
                    timestamp=datetime.now(),
                    portfolio_id=position_id
                ))

        # Volatility alerts
        for asset in portfolio.assets:
            volatility = asset.volatility_24h

            if volatility >= self.constants.MONITORING_THRESHOLDS['volatility_spike']:
                alerts.append(CollateralAlert(
                    alert_id=f"{position_id}_{asset.symbol}_volatility_{datetime.now().isoformat()}",
                    level=AlertLevel.WARNING,
                    asset_symbol=asset.symbol,
                    alert_type="volatility_spike",
                    message=f"{asset.symbol} volatility spiked to {volatility:.1%}",
                    current_value=volatility,
                    threshold_value=self.constants.MONITORING_THRESHOLDS['volatility_spike'],
                    timestamp=datetime.now(),
                    portfolio_id=position_id
                ))

        return alerts

    async def _process_alert(self, alert: CollateralAlert) -> None:
        """Process and distribute an alert"""
        self.logger.info(f"Processing alert: {alert.alert_type} for {alert.asset_symbol}")

        # Set emergency mode for critical alerts
        if alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
            self._emergency_mode = True

        # Call registered callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")

    def _should_recalculate_rate(
        self,
        position: MonitoringPosition,
        alerts: List[CollateralAlert]
    ) -> bool:
        """Determine if rate should be recalculated"""
        # Always recalculate if there are critical or emergency alerts
        if any(alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY] for alert in alerts):
            return True

        # Recalculate if it's been long enough since last calculation
        if position.last_update:
            time_since_update = (datetime.now() - position.last_update).seconds
            interval = (
                self.config.rate_calculation.emergency_recalculation_interval
                if self._emergency_mode
                else self.config.rate_calculation.rate_recalculation_interval
            )
            return time_since_update >= interval

        return True

    async def _recalculate_position_rate(
        self,
        position_id: str,
        position: MonitoringPosition,
        updated_portfolio: CollateralPortfolio
    ) -> None:
        """Recalculate rate adjustment for a position"""
        try:
            result = await self.calculator.calculate_adjusted_rate(
                base_rate=position.base_rate,
                portfolio=updated_portfolio,
                market_conditions=self._market_conditions
            )

            # Check if rate changed significantly
            if (position.last_rate_adjustment is None or
                abs(result.total_adjustment - position.last_rate_adjustment) > 0.001):  # 10 basis points

                position.last_rate_adjustment = result.total_adjustment

                # Create rate change alert
                alert = CollateralAlert(
                    alert_id=f"{position_id}_rate_change_{datetime.now().isoformat()}",
                    level=AlertLevel.INFO,
                    asset_symbol="PORTFOLIO",
                    alert_type="rate_adjustment",
                    message=f"Rate adjusted to {result.final_rate:.2%} (adjustment: {result.total_adjustment:+.2%})",
                    current_value=result.final_rate,
                    threshold_value=position.base_rate,
                    timestamp=datetime.now(),
                    portfolio_id=position_id,
                    metadata={'adjustment_breakdown': result.adjustment_breakdown}
                )

                await self._process_alert(alert)

        except Exception as e:
            self.logger.error(f"Error recalculating rate for position {position_id}: {e}")

    def get_position_status(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a monitored position"""
        position = self._monitored_positions.get(portfolio_id)
        if not position:
            return None

        recent_alerts = [
            alert for alert in position.alert_history
            if (datetime.now() - alert.timestamp).days < 1
        ]

        return {
            'portfolio_id': portfolio_id,
            'current_ltv': position.portfolio.current_ltv,
            'total_value_usd': position.portfolio.total_value_usd,
            'loan_amount_usd': position.portfolio.loan_amount_usd,
            'last_rate_adjustment': position.last_rate_adjustment,
            'last_update': position.last_update,
            'recent_alerts': len(recent_alerts),
            'monitoring_enabled': position.monitoring_enabled,
            'emergency_mode': self._emergency_mode
        }

    def get_all_positions_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all monitored positions"""
        return {
            portfolio_id: self.get_position_status(portfolio_id)
            for portfolio_id in self._monitored_positions.keys()
        }