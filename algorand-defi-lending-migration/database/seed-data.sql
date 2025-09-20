-- Algorand DeFi Lending Platform - Seed Data
-- Initialize with common Algorand assets and basic configuration

-- Common Algorand assets
INSERT INTO asset_definitions (
    asset_id, symbol, name, decimals, asset_type,
    base_collateral_ratio, maintenance_ratio, liquidation_penalty,
    volatility_30d, correlation_with_algo, liquidity_tier
) VALUES
-- Native ALGO
('0', 'ALGO', 'Algorand', 6, 'algo_native', 1.5000, 1.3000, 0.0500, 0.4500, 1.0000, 'high'),

-- USDC (most common stablecoin on Algorand)
('31566704', 'USDC', 'USD Coin', 6, 'stablecoin', 1.1000, 1.0500, 0.0200, 0.0100, 0.0500, 'high'),

-- USDT
('312769', 'USDt', 'Tether USD', 6, 'stablecoin', 1.1500, 1.0800, 0.0250, 0.0150, 0.0300, 'high'),

-- goBTC (wrapped Bitcoin)
('386192725', 'goBTC', 'GoMint Bitcoin', 8, 'asa_token', 1.7500, 1.5000, 0.0750, 0.6000, 0.3500, 'medium'),

-- goETH (wrapped Ethereum)
('386195940', 'goETH', 'GoMint Ethereum', 8, 'asa_token', 1.6500, 1.4000, 0.0650, 0.5500, 0.4000, 'medium'),

-- Governance tokens
('27165954', 'PLANET', 'Planets', 6, 'governance', 2.0000, 1.7500, 0.1000, 0.8000, 0.2000, 'low'),

-- LP tokens (example from Tinyman)
('552635992', 'TM1POOL', 'Tinyman Pool Token', 6, 'lp_token', 2.5000, 2.0000, 0.1250, 0.7000, 0.6000, 'low');

-- Demo user for testing
INSERT INTO users (id, email, email_verified, kyc_status, kyc_tier, status)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'demo@algorand-defi.com',
    true,
    'approved',
    2,
    'active'
);

-- Demo wallet
INSERT INTO wallets (id, user_id, address, wallet_type, is_primary, status)
VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440000',
    'DEMO7RTYUIOPASDFGHJKLZXCVBNMQWERTYUIOPASDFGHJKLZXCVBNM',
    'algorand_mobile',
    true,
    'active'
);

-- Demo wallet assets
INSERT INTO wallet_assets (wallet_id, asset_id, balance, available_balance)
SELECT
    '550e8400-e29b-41d4-a716-446655440001',
    id,
    CASE
        WHEN symbol = 'ALGO' THEN 10000.000000
        WHEN symbol = 'USDC' THEN 5000.000000
        WHEN symbol = 'USDt' THEN 2000.000000
        WHEN symbol = 'goBTC' THEN 0.50000000
        WHEN symbol = 'goETH' THEN 2.00000000
        ELSE 1000.000000
    END,
    CASE
        WHEN symbol = 'ALGO' THEN 10000.000000
        WHEN symbol = 'USDC' THEN 5000.000000
        WHEN symbol = 'USDt' THEN 2000.000000
        WHEN symbol = 'goBTC' THEN 0.50000000
        WHEN symbol = 'goETH' THEN 2.00000000
        ELSE 1000.000000
    END
FROM asset_definitions;

-- Sample price data (recent prices as of migration)
INSERT INTO price_history (asset_id, price_usd, volume_24h, oracle_source, confidence_level, price_timestamp)
SELECT
    id,
    CASE
        WHEN symbol = 'ALGO' THEN 0.1850
        WHEN symbol = 'USDC' THEN 1.0000
        WHEN symbol = 'USDt' THEN 0.9998
        WHEN symbol = 'goBTC' THEN 43250.00
        WHEN symbol = 'goETH' THEN 2350.50
        WHEN symbol = 'PLANET' THEN 0.0025
        WHEN symbol = 'TM1POOL' THEN 1.2500
        ELSE 1.0000
    END,
    CASE
        WHEN symbol = 'ALGO' THEN 125000000.00
        WHEN symbol = 'USDC' THEN 85000000.00
        WHEN symbol = 'USDt' THEN 45000000.00
        WHEN symbol = 'goBTC' THEN 2500000.00
        WHEN symbol = 'goETH' THEN 8500000.00
        WHEN symbol = 'PLANET' THEN 150000.00
        WHEN symbol = 'TM1POOL' THEN 75000.00
        ELSE 100000.00
    END,
    'chainlink',
    0.95,
    CURRENT_TIMESTAMP
FROM asset_definitions;

-- Sample volatility data
INSERT INTO volatility_metrics (
    asset_id, calculation_date,
    volatility_1d, volatility_7d, volatility_30d,
    value_at_risk_95, max_drawdown,
    stress_test_scenarios
)
SELECT
    id,
    CURRENT_DATE,
    CASE
        WHEN symbol = 'ALGO' THEN 0.0850
        WHEN symbol IN ('USDC', 'USDt') THEN 0.0025
        WHEN symbol = 'goBTC' THEN 0.0450
        WHEN symbol = 'goETH' THEN 0.0650
        ELSE 0.1200
    END,
    CASE
        WHEN symbol = 'ALGO' THEN 0.2150
        WHEN symbol IN ('USDC', 'USDt') THEN 0.0050
        WHEN symbol = 'goBTC' THEN 0.1850
        WHEN symbol = 'goETH' THEN 0.2250
        ELSE 0.3500
    END,
    volatility_30d,
    CASE
        WHEN symbol = 'ALGO' THEN 0.1250
        WHEN symbol IN ('USDC', 'USDt') THEN 0.0100
        WHEN symbol = 'goBTC' THEN 0.2250
        WHEN symbol = 'goETH' THEN 0.1850
        ELSE 0.3000
    END,
    CASE
        WHEN symbol = 'ALGO' THEN 0.2850
        WHEN symbol IN ('USDC', 'USDt') THEN 0.0200
        WHEN symbol = 'goBTC' THEN 0.4250
        WHEN symbol = 'goETH' THEN 0.3850
        ELSE 0.5500
    END,
    '{"crypto_crash_50": -0.5, "algo_depegging": -0.3, "liquidity_crisis": -0.4}'::jsonb
FROM asset_definitions;

-- Sample configuration for interest rate calculation
-- This would typically be in a separate configuration table
-- For now, we'll add some audit log entries to show system initialization

INSERT INTO audit_logs (
    correlation_id, event_type, event_category, action,
    event_data, success, created_at
) VALUES
(
    uuid_generate_v4(),
    'system_initialization',
    'system',
    'seed_data_loaded',
    '{"assets_loaded": 7, "demo_user_created": true, "price_data_loaded": true}'::jsonb,
    true,
    CURRENT_TIMESTAMP
),
(
    uuid_generate_v4(),
    'configuration_loaded',
    'system',
    'risk_parameters_set',
    '{"default_collateral_ratios": true, "volatility_thresholds": true, "liquidation_penalties": true}'::jsonb,
    true,
    CURRENT_TIMESTAMP
);

-- Create a view for current asset prices (latest price from each oracle)
CREATE VIEW current_asset_prices AS
SELECT DISTINCT ON (asset_id, oracle_source)
    ad.symbol,
    ad.name,
    ph.asset_id,
    ph.price_usd,
    ph.oracle_source,
    ph.confidence_level,
    ph.price_timestamp
FROM price_history ph
JOIN asset_definitions ad ON ph.asset_id = ad.id
ORDER BY asset_id, oracle_source, price_timestamp DESC;

-- Create a view for wallet portfolio values
CREATE VIEW wallet_portfolio_values AS
SELECT
    w.address,
    w.user_id,
    SUM(wa.balance * COALESCE(cap.price_usd, 0)) as total_value_usd,
    COUNT(wa.asset_id) as asset_count,
    MAX(wa.last_updated) as last_updated
FROM wallets w
JOIN wallet_assets wa ON w.id = wa.wallet_id
JOIN asset_definitions ad ON wa.asset_id = ad.id
LEFT JOIN current_asset_prices cap ON ad.id = cap.asset_id AND cap.oracle_source = 'chainlink'
WHERE w.status = 'active' AND ad.is_active = true
GROUP BY w.address, w.user_id;

-- Grant necessary permissions (adjust based on your user management)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO defi_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO defi_app_user;