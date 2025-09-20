"""
Test suite for ASA Risk Assessment Engine
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from core.asa_volatility import ASAVolatilityAnalyzer, VolatilityMetrics
from core.asa_liquidity import ASALiquidityAnalyzer, LiquidityMetrics
from core.smart_contract_security import SmartContractSecurityAnalyzer, SecurityMetrics
from core.asa_risk_engine import ASARiskEngine, ASARiskReport


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'risk_assessment': {
            'volatility_weights': {
                'price_volatility': 0.35,
                'volume_volatility': 0.25,
                'market_depth': 0.25,
                'correlation_risk': 0.15
            },
            'liquidity_weights': {
                'trading_volume': 0.30,
                'market_makers': 0.25,
                'spread_analysis': 0.25,
                'pool_depth': 0.20
            },
            'security_weights': {
                'smart_contract_audit': 0.30,
                'creator_reputation': 0.25,
                'governance_model': 0.20,
                'technical_parameters': 0.25
            }
        },
        'volatility_analysis': {
            'lookback_periods': {'short_term': 7, 'medium_term': 30, 'long_term': 90},
            'volatility_thresholds': {
                'very_low': 0.05, 'low': 0.15, 'medium': 0.30,
                'high': 0.50, 'very_high': 1.0
            }
        },
        'liquidity_analysis': {
            'minimum_requirements': {
                'daily_volume_usd': 10000,
                'market_makers': 3,
                'pool_depth_ratio': 0.1
            },
            'volume_categories': {
                'nano': 1000, 'micro': 10000, 'small': 100000,
                'medium': 1000000, 'large': 10000000
            },
            'spread_thresholds': {
                'tight': 0.005, 'normal': 0.02, 'wide': 0.05, 'very_wide': 0.1
            }
        },
        'security_analysis': {
            'audit_requirements': {
                'required_auditors': ['certik', 'halborn'],
                'minimum_score': 85,
                'max_age_months': 12
            },
            'creator_verification': {
                'verified_creators': ['algorand_inc', 'algofi'],
                'kyc_required': True,
                'reputation_threshold': 0.8
            },
            'technical_checks': {
                'freeze_enabled': False,
                'clawback_enabled': False,
                'default_frozen': False
            }
        },
        'risk_tiers': {
            'aaa': {'min_score': 0.90, 'max_ltv': 0.85, 'rate_adjustment': -0.2},
            'aa': {'min_score': 0.80, 'max_ltv': 0.75, 'rate_adjustment': -0.1},
            'a': {'min_score': 0.70, 'max_ltv': 0.65, 'rate_adjustment': 0.0},
            'bbb': {'min_score': 0.60, 'max_ltv': 0.55, 'rate_adjustment': 0.1},
            'bb': {'min_score': 0.50, 'max_ltv': 0.45, 'rate_adjustment': 0.25},
            'b': {'min_score': 0.40, 'max_ltv': 0.35, 'rate_adjustment': 0.5},
            'ccc': {'min_score': 0.30, 'max_ltv': 0.25, 'rate_adjustment': 1.0},
            'cc': {'min_score': 0.20, 'max_ltv': 0.15, 'rate_adjustment': 2.0},
            'c': {'min_score': 0.10, 'max_ltv': 0.10, 'rate_adjustment': 3.0},
            'd': {'min_score': 0.0, 'max_ltv': 0.0, 'rate_adjustment': None}
        },
        'algorand_config': {
            'indexer': {'url': 'https://mainnet-idx.algonode.cloud'},
            'node': {'url': 'https://mainnet-api.algonode.cloud'}
        },
        'dex_config': {
            'tinyman': {'api_url': 'https://mainnet.analytics.tinyman.org'},
            'algofi': {'api_url': 'https://api.algofi.org'},
            'pact': {'api_url': 'https://api.pact.fi'},
            'algodex': {'api_url': 'https://api.algodex.com'}
        }
    }


@pytest.fixture
def volatility_analyzer(mock_config):
    """Create volatility analyzer with mock config"""
    return ASAVolatilityAnalyzer(mock_config)


@pytest.fixture
def liquidity_analyzer(mock_config):
    """Create liquidity analyzer with mock config"""
    return ASALiquidityAnalyzer(mock_config)


@pytest.fixture
def security_analyzer(mock_config):
    """Create security analyzer with mock config"""
    return SmartContractSecurityAnalyzer(mock_config)


@pytest.fixture
def risk_engine(mock_config):
    """Create risk engine with mock config"""
    return ASARiskEngine(config_dict=mock_config)


class TestVolatilityAnalyzer:
    """Test volatility analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_asa_volatility(self, volatility_analyzer):
        """Test ASA volatility analysis"""
        test_asset_id = 31566704  # USDC

        with patch.object(volatility_analyzer, 'algod_client') as mock_algod, \
             patch.object(volatility_analyzer, '_collect_price_data') as mock_price_data:

            # Mock asset info
            mock_algod.asset_info.return_value = {
                'params': {
                    'name': 'USD Coin',
                    'unit-name': 'USDC',
                    'decimals': 6
                }
            }

            # Mock price data
            from core.asa_volatility import PriceData
            mock_price_data.return_value = [
                PriceData(
                    timestamp=datetime.utcnow() - timedelta(days=i),
                    price_usd=1.0 + (i * 0.001),  # Slight price variation
                    price_algo=0.1,
                    volume_24h=1000000.0,
                    market_cap=50000000000.0,
                    source='tinyman'
                ) for i in range(30)
            ]

            result = await volatility_analyzer.analyze_asa_volatility(test_asset_id)

            assert isinstance(result, VolatilityMetrics)
            assert result.asset_id == test_asset_id
            assert result.asset_name == 'USD Coin'
            assert 0 <= result.volatility_score <= 1
            assert result.daily_volatility >= 0

    def test_calculate_returns(self, volatility_analyzer):
        """Test return calculation"""
        from core.asa_volatility import PriceData

        price_data = [
            PriceData(datetime.utcnow(), 1.0, 0.1, 100, 1000, 'test'),
            PriceData(datetime.utcnow(), 1.1, 0.11, 110, 1100, 'test'),
            PriceData(datetime.utcnow(), 1.05, 0.105, 105, 1050, 'test')
        ]

        returns = volatility_analyzer._calculate_returns(price_data)

        assert len(returns) == 2
        assert abs(returns[0] - 0.1) < 0.001  # (1.1 - 1.0) / 1.0
        assert abs(returns[1] - (-0.045454)) < 0.001  # (1.05 - 1.1) / 1.1

    def test_calculate_volatility_score(self, volatility_analyzer):
        """Test volatility score calculation"""
        # Test low volatility (good score)
        low_vol_score = volatility_analyzer._calculate_volatility_score(0.02, 0.1, 0.05)
        assert 0 <= low_vol_score <= 1
        assert low_vol_score < 0.5  # Lower is better for volatility

        # Test high volatility (poor score)
        high_vol_score = volatility_analyzer._calculate_volatility_score(0.8, 0.6, 0.4)
        assert 0 <= high_vol_score <= 1
        assert high_vol_score > 0.7  # Higher score = higher risk


class TestLiquidityAnalyzer:
    """Test liquidity analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_asa_liquidity(self, liquidity_analyzer):
        """Test ASA liquidity analysis"""
        test_asset_id = 31566704  # USDC

        with patch.object(liquidity_analyzer, 'algod_client') as mock_algod, \
             patch.object(liquidity_analyzer, '_analyze_trading_metrics') as mock_trading, \
             patch.object(liquidity_analyzer, '_analyze_market_depth') as mock_depth, \
             patch.object(liquidity_analyzer, '_analyze_liquidity_pools') as mock_pools:

            # Mock asset info
            mock_algod.asset_info.return_value = {
                'params': {
                    'name': 'USD Coin',
                    'unit-name': 'USDC'
                }
            }

            # Mock trading metrics
            from core.asa_liquidity import TradingMetrics
            mock_trading.return_value = TradingMetrics(
                volume_24h=5000000.0,
                volume_7d=30000000.0,
                volume_30d=120000000.0,
                trade_count_24h=1000,
                avg_trade_size=5000.0,
                largest_trade_24h=100000.0,
                volume_trend="increasing"
            )

            # Mock market depth
            from core.asa_liquidity import MarketDepth
            mock_depth.return_value = MarketDepth(
                bid_depth_1_percent=50000.0,
                ask_depth_1_percent=50000.0,
                bid_depth_5_percent=200000.0,
                ask_depth_5_percent=200000.0,
                total_depth=500000.0,
                depth_imbalance=1.0
            )

            # Mock liquidity pools
            from core.asa_liquidity import LiquidityPool
            mock_pools.return_value = [
                LiquidityPool(
                    dex_name='tinyman',
                    pool_address='pool_address',
                    asset1_id=test_asset_id,
                    asset2_id=0,
                    asset1_reserves=1000000.0,
                    asset2_reserves=1000000.0,
                    total_liquidity_usd=2000000.0,
                    volume_24h=500000.0,
                    fees_24h=1500.0,
                    apr=0.08
                )
            ]

            result = await liquidity_analyzer.analyze_asa_liquidity(test_asset_id)

            assert isinstance(result, LiquidityMetrics)
            assert result.asset_id == test_asset_id
            assert 0 <= result.overall_liquidity_score <= 1
            assert result.trading_metrics.volume_24h > 0

    def test_calculate_volume_score(self, liquidity_analyzer):
        """Test volume score calculation"""
        from core.asa_liquidity import TradingMetrics

        # High volume trading
        high_volume = TradingMetrics(
            volume_24h=15000000.0,  # $15M - large category
            volume_7d=100000000.0,
            volume_30d=400000000.0,
            trade_count_24h=5000,
            avg_trade_size=3000.0,
            largest_trade_24h=50000.0,
            volume_trend="stable"
        )

        score = liquidity_analyzer._calculate_volume_score(high_volume)
        assert score == 1.0  # Should get max score

        # Low volume trading
        low_volume = TradingMetrics(
            volume_24h=500.0,  # $500 - nano category
            volume_7d=3500.0,
            volume_30d=15000.0,
            trade_count_24h=10,
            avg_trade_size=50.0,
            largest_trade_24h=200.0,
            volume_trend="declining"
        )

        score = liquidity_analyzer._calculate_volume_score(low_volume)
        assert score == 0.2  # Should get low score


class TestSecurityAnalyzer:
    """Test security analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_contract_security(self, security_analyzer):
        """Test contract security analysis"""
        test_asset_id = 31566704  # USDC

        with patch.object(security_analyzer, 'algod_client') as mock_algod:

            # Mock asset info
            mock_algod.asset_info.return_value = {
                'params': {
                    'name': 'USD Coin',
                    'creator': 'CREATOR_ADDRESS_PLACEHOLDER',
                    'total': 1000000000000,  # 1M total supply
                    'decimals': 6,
                    'default-frozen': False,
                    'freeze': None,  # No freeze address
                    'clawback': None,  # No clawback address
                    'manager': None,  # No manager address
                    'url': 'https://centre.io',
                    'metadata-hash': 'metadata_hash'
                },
                'created-at-round': 1000000
            }

            result = await security_analyzer.analyze_contract_security(test_asset_id)

            assert isinstance(result, SecurityMetrics)
            assert result.asset_id == test_asset_id
            assert 0 <= result.overall_security_score <= 1
            assert result.security_risk_level in ['very_low', 'low', 'medium', 'high', 'very_high']

    def test_generate_security_flags(self, security_analyzer):
        """Test security flag generation"""
        from core.smart_contract_security import TechnicalParameters, CreatorAnalysis

        # Safe parameters
        safe_params = TechnicalParameters(
            total_supply=1000000000,
            decimals=6,
            default_frozen=False,
            freeze_enabled=False,
            clawback_enabled=False,
            manager_address=None,
            reserve_address=None,
            freeze_address=None,
            clawback_address=None,
            url='https://example.com',
            metadata_hash='hash'
        )

        safe_creator = CreatorAnalysis(
            creator_address='verified_creator',
            is_verified=True,
            reputation_score=0.9,
            previous_assets=[],
            governance_participation=True,
            community_standing='excellent',
            kyc_status=True,
            social_presence={}
        )

        flags = security_analyzer._generate_security_flags(
            safe_params, safe_creator, {'created-at-round': 500000}
        )

        assert not flags.centralized_control
        assert not flags.freeze_risk
        assert not flags.clawback_risk
        assert not flags.unverified_creator

    def test_calculate_technical_security_score(self, security_analyzer):
        """Test technical security score calculation"""
        from core.smart_contract_security import TechnicalParameters, SecurityFlags

        safe_params = TechnicalParameters(
            total_supply=1000000, decimals=6, default_frozen=False,
            freeze_enabled=False, clawback_enabled=False,
            manager_address=None, reserve_address=None,
            freeze_address=None, clawback_address=None,
            url='https://example.com', metadata_hash='hash'
        )

        safe_flags = SecurityFlags(
            centralized_control=False, unlimited_minting=False,
            freeze_risk=False, clawback_risk=False,
            unverified_creator=False, recent_creation=False,
            suspicious_parameters=False, missing_metadata=False
        )

        score = security_analyzer._calculate_technical_security_score(safe_params, safe_flags)
        assert score == 1.0  # Perfect security score

        # Risky parameters
        risky_flags = SecurityFlags(
            centralized_control=True, unlimited_minting=True,
            freeze_risk=True, clawback_risk=True,
            unverified_creator=True, recent_creation=True,
            suspicious_parameters=True, missing_metadata=True
        )

        risky_score = security_analyzer._calculate_technical_security_score(safe_params, risky_flags)
        assert risky_score < 0.3  # Should be very low score


class TestRiskEngine:
    """Test risk engine integration"""

    @pytest.mark.asyncio
    async def test_assess_asa_risk_integration(self, risk_engine):
        """Test full ASA risk assessment integration"""
        test_asset_id = 31566704  # USDC

        # Mock component analyzers
        mock_volatility = VolatilityMetrics(
            asset_id=test_asset_id,
            asset_name='USD Coin',
            current_price=1.0,
            daily_volatility=0.02,  # Low volatility
            weekly_volatility=0.05,
            monthly_volatility=0.08,
            price_range_7d=0.01,
            price_range_30d=0.03,
            max_drawdown=0.02,
            volume_volatility=0.1,
            avg_daily_volume=5000000.0,
            volume_trend="stable",
            var_95=0.01,
            sharpe_ratio=1.5,
            volatility_score=0.2  # Low risk
        )

        from core.asa_liquidity import TradingMetrics, MarketDepth
        mock_liquidity = LiquidityMetrics(
            asset_id=test_asset_id,
            asset_name='USD Coin',
            trading_metrics=TradingMetrics(
                volume_24h=5000000.0, volume_7d=30000000.0, volume_30d=120000000.0,
                trade_count_24h=1000, avg_trade_size=5000.0, largest_trade_24h=100000.0,
                volume_trend="increasing"
            ),
            market_depth=MarketDepth(
                bid_depth_1_percent=50000.0, ask_depth_1_percent=50000.0,
                bid_depth_5_percent=200000.0, ask_depth_5_percent=200000.0,
                total_depth=500000.0, depth_imbalance=1.0
            ),
            pools=[],
            total_pool_liquidity=2000000.0,
            bid_ask_spread=0.001,
            average_spread_24h=0.001,
            spread_volatility=0.0005,
            active_market_makers=5,
            market_maker_concentration=0.3,
            volume_score=1.0,
            depth_score=0.8,
            spread_score=1.0,
            overall_liquidity_score=0.9,
            liquidity_risk_level="very_low",
            slippage_1_percent=0.001,
            slippage_5_percent=0.005
        )

        from core.smart_contract_security import (
            TechnicalParameters, SecurityFlags, CreatorAnalysis
        )
        mock_security = SecurityMetrics(
            asset_id=test_asset_id,
            asset_name='USD Coin',
            technical_params=TechnicalParameters(
                total_supply=1000000000, decimals=6, default_frozen=False,
                freeze_enabled=False, clawback_enabled=False,
                manager_address=None, reserve_address=None,
                freeze_address=None, clawback_address=None,
                url='https://centre.io', metadata_hash='hash'
            ),
            security_flags=SecurityFlags(
                centralized_control=False, unlimited_minting=False,
                freeze_risk=False, clawback_risk=False,
                unverified_creator=False, recent_creation=False,
                suspicious_parameters=False, missing_metadata=False
            ),
            audits=[],
            latest_audit_score=0.9,
            audit_coverage=0.8,
            creator_analysis=CreatorAnalysis(
                creator_address='centre_io', is_verified=True,
                reputation_score=0.95, previous_assets=[],
                governance_participation=True, community_standing='excellent',
                kyc_status=True, social_presence={}
            ),
            contract_complexity=0.1,
            code_quality_score=0.9,
            upgrade_mechanism='immutable',
            technical_security_score=1.0,
            audit_security_score=0.9,
            creator_security_score=0.95,
            overall_security_score=0.95,
            security_risk_level="very_low",
            recommendations=[]
        )

        with patch.object(risk_engine.volatility_analyzer, 'analyze_asa_volatility',
                         return_value=mock_volatility), \
             patch.object(risk_engine.liquidity_analyzer, 'analyze_asa_liquidity',
                         return_value=mock_liquidity), \
             patch.object(risk_engine.security_analyzer, 'analyze_contract_security',
                         return_value=mock_security):

            result = await risk_engine.assess_asa_risk(test_asset_id)

            assert isinstance(result, ASARiskReport)
            assert result.asset_id == test_asset_id
            assert 0 <= result.overall_risk_score <= 1
            assert result.risk_tier in risk_engine.risk_tiers
            assert 0 <= result.max_ltv <= 1

    def test_calculate_combined_risk_score(self, risk_engine):
        """Test combined risk score calculation"""
        # Create mock metrics
        mock_volatility = Mock()
        mock_volatility.volatility_score = 0.2  # Low volatility risk

        mock_liquidity = Mock()
        mock_liquidity.overall_liquidity_score = 0.8  # Good liquidity

        mock_security = Mock()
        mock_security.overall_security_score = 0.9  # High security

        combined_risk = risk_engine._calculate_combined_risk_score(
            mock_volatility, mock_liquidity, mock_security
        )

        assert 0 <= combined_risk <= 1
        # Should be low risk given good inputs
        assert combined_risk < 0.5

    def test_determine_risk_tier(self, risk_engine):
        """Test risk tier determination"""
        # Low risk (high quality) score
        tier, ltv, adjustment = risk_engine._determine_risk_tier(0.1)  # Low risk
        assert tier == "aaa"
        assert ltv == 0.85
        assert adjustment == -0.2

        # High risk (low quality) score
        tier, ltv, adjustment = risk_engine._determine_risk_tier(0.9)  # High risk
        assert tier == "d"
        assert ltv == 0.0
        assert adjustment is None

    @pytest.mark.asyncio
    async def test_assess_portfolio_risk(self, risk_engine):
        """Test portfolio risk assessment"""
        test_asset_ids = [31566704, 312769]  # USDC, USDt

        # Mock individual assessments
        mock_report = ASARiskReport(
            asset_id=31566704,
            asset_name="USD Coin",
            overall_risk_score=0.2,
            risk_tier="aaa",
            max_ltv=0.85,
            rate_adjustment=-0.2,
            components=None,
            risk_factors=[],
            recommendations=["Excellent asset quality"],
            analysis_timestamp=datetime.utcnow(),
            next_review_date=datetime.utcnow() + timedelta(days=90),
            monitoring_alerts=[]
        )

        with patch.object(risk_engine, 'assess_asa_risk', return_value=mock_report):
            result = await risk_engine.assess_portfolio_risk(test_asset_ids)

            assert len(result.individual_assessments) == len(test_asset_ids)
            assert 0 <= result.portfolio_risk_score <= 1
            assert isinstance(result.risk_distribution, dict)

    def test_export_risk_report(self, risk_engine):
        """Test risk report export"""
        mock_report = ASARiskReport(
            asset_id=31566704,
            asset_name="USD Coin",
            overall_risk_score=0.2,
            risk_tier="aaa",
            max_ltv=0.85,
            rate_adjustment=-0.2,
            components=None,
            risk_factors=["Low volatility"],
            recommendations=["Excellent for lending"],
            analysis_timestamp=datetime.utcnow(),
            next_review_date=datetime.utcnow() + timedelta(days=90),
            monitoring_alerts=[]
        )

        # Test JSON export
        json_export = risk_engine.export_risk_report(mock_report, 'json')
        assert '"asset_id": 31566704' in json_export
        assert '"risk_tier": "aaa"' in json_export

        # Test YAML export
        yaml_export = risk_engine.export_risk_report(mock_report, 'yaml')
        assert 'asset_id: 31566704' in yaml_export
        assert 'risk_tier: aaa' in yaml_export


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])