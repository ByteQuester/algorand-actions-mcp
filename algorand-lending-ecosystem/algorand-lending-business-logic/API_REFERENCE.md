# Algorand Lending Business Logic - API Reference

This document provides a comprehensive reference for the Algorand Lending Business Logic package, including all working methods, real example inputs and outputs, error conditions, and configuration options.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Engines](#core-engines)
3. [Data Models](#data-models)
4. [Configuration](#configuration)
5. [Service Interface](#service-interface)
6. [Error Handling](#error-handling)
7. [Performance Guidelines](#performance-guidelines)
8. [Examples](#examples)

## Quick Start

### Installation

```bash
pip install ./algorand-lending-business-logic
```

### Basic Usage

```python
import asyncio
from decimal import Decimal
from algorand_lending_bl import (
    CollateralAnalyzer,
    InterestRateEngine,
    ASAToken,
    AlgorandAddress,
    create_lending_engines
)

async def basic_example():
    # Create engines
    collateral_analyzer, rate_engine = create_lending_engines()

    # Create test asset
    algo_token = ASAToken(
        asset_id="0",
        symbol="ALGO",
        name="Algorand",
        decimals=6,
        total_supply=Decimal("10000000000"),
        circulating_supply=Decimal("8000000000"),
        creator_address="ALGORAND_FOUNDATION"
    )

    # Analyze collateral
    analysis = await collateral_analyzer.analyze_collateral(
        assets=[algo_token],
        quantities=[Decimal("10000")],
        loan_amount_usd=Decimal("2000")
    )

    print(f"Collateral value: ${analysis.total_collateral_value:.2f}")
    print(f"Sufficient: {analysis.is_sufficient}")

asyncio.run(basic_example())
```

## Core Engines

### CollateralAnalyzer

Analyzes collateral portfolios and calculates loan-to-value ratios.

#### Constructor

```python
CollateralAnalyzer(config: CollateralConfig = None)
```

- **config**: Optional configuration object. If None, uses defaults from environment.

#### Methods

##### analyze_collateral()

```python
async def analyze_collateral(
    assets: List[ASAToken],
    quantities: List[Decimal],
    loan_amount_usd: Decimal,
    market_condition: str = "normal"
) -> CollateralAnalysis
```

**Parameters:**
- `assets`: List of ASA tokens representing collateral assets
- `quantities`: List of quantities for each asset (same order as assets)
- `loan_amount_usd`: Requested loan amount in USD
- `market_condition`: Market condition ("normal", "volatile", "stressed")

**Returns:** `CollateralAnalysis` object with comprehensive analysis

**Example:**

```python
from decimal import Decimal
from algorand_lending_bl import CollateralAnalyzer, ASAToken

analyzer = CollateralAnalyzer()

# Create ALGO token
algo_token = ASAToken(
    asset_id="0",
    symbol="ALGO",
    name="Algorand",
    decimals=6,
    total_supply=Decimal("10000000000"),
    circulating_supply=Decimal("8000000000"),
    creator_address="ALGORAND_FOUNDATION"
)

# Analyze 15,000 ALGO as collateral for $5,000 loan
analysis = await analyzer.analyze_collateral(
    assets=[algo_token],
    quantities=[Decimal("15000")],
    loan_amount_usd=Decimal("5000")
)

# Example output:
print(analysis.total_collateral_value)     # 3000.00 (example)
print(analysis.total_adjusted_value)       # 2610.00 (after haircuts)
print(analysis.current_collateral_ratio)   # 0.522 (52.2%)
print(analysis.is_sufficient)              # False
print(analysis.additional_collateral_needed) # 4587.09
```

**Possible Errors:**
- `ValueError`: Invalid asset data, negative quantities, zero loan amount
- `TypeError`: Incorrect parameter types
- `AssertionError`: Asset/quantity list length mismatch

### InterestRateEngine

Calculates interest rates based on borrower profile and market conditions.

#### Constructor

```python
InterestRateEngine(config: InterestRateConfig = None)
```

#### Methods

##### calculate_rate()

```python
async def calculate_rate(
    borrower: AlgorandAddress,
    loan_amount_usd: Decimal,
    loan_duration_days: int,
    collateral_assets: List[str],
    collateral_value_usd: Decimal,
    market_condition: str = "normal"
) -> RateCalculation
```

**Parameters:**
- `borrower`: Algorand address of the borrower
- `loan_amount_usd`: Loan amount in USD
- `loan_duration_days`: Loan duration in days
- `collateral_assets`: List of collateral asset symbols
- `collateral_value_usd`: Total collateral value in USD
- `market_condition`: Market condition

**Returns:** `RateCalculation` object with rate details

**Example:**

```python
from algorand_lending_bl import InterestRateEngine, AlgorandAddress

engine = InterestRateEngine()

borrower = AlgorandAddress(
    address="BORROWER123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCD",
    is_valid=True,
    creation_round=25000000,
    last_activity_round=35000000
)

rate_calc = await engine.calculate_rate(
    borrower=borrower,
    loan_amount_usd=Decimal("5000"),
    loan_duration_days=180,
    collateral_assets=["ALGO"],
    collateral_value_usd=Decimal("7500")
)

# Example output:
print(rate_calc.final_interest_rate)    # 0.0842 (8.42%)
print(rate_calc.effective_apr)          # 0.0876 (8.76%)
print(rate_calc.borrower_risk_tier)     # RiskTier.STANDARD
print(rate_calc.confidence_interval)    # 0.125 (±12.5%)
```

## Data Models

### ASAToken

Represents an Algorand Standard Asset.

```python
@dataclass
class ASAToken:
    asset_id: str
    symbol: str
    name: str
    decimals: int
    total_supply: Decimal
    circulating_supply: Decimal
    creator_address: str
    unit_name: Optional[str] = None
    url: Optional[str] = None
    metadata_hash: Optional[bytes] = None
    freeze_address: Optional[str] = None
    clawback_address: Optional[str] = None
```

### AlgorandAddress

Represents an Algorand account address.

```python
@dataclass
class AlgorandAddress:
    address: str
    is_valid: bool
    creation_round: Optional[int] = None
    last_activity_round: Optional[int] = None
```

### CollateralAnalysis

Result of collateral analysis.

```python
@dataclass
class CollateralAnalysis:
    total_collateral_value: Decimal
    total_adjusted_value: Decimal
    loan_amount_usd: Decimal
    current_collateral_ratio: Decimal
    required_collateral_ratio: Decimal
    is_sufficient: bool
    additional_collateral_needed: Decimal
    positions: List[CollateralPosition]
    portfolio_risk: PortfolioRisk
    recommendations: List[str]
    market_condition: str
    timestamp: datetime

    def safety_margin(self) -> Decimal:
        """Calculate safety margin percentage."""
        return (self.current_collateral_ratio - self.required_collateral_ratio) / self.required_collateral_ratio
```

### RateCalculation

Result of interest rate calculation.

```python
@dataclass
class RateCalculation:
    final_interest_rate: Decimal
    effective_apr: Decimal
    borrower_risk_tier: RiskTier
    loan_risk_score: Decimal
    confidence_interval: Decimal
    staking_metrics: StakingMetrics
    reputation_score: ReputationScore
    market_factors: Dict[str, Any]
    calculation_timestamp: datetime

    def rate_breakdown(self) -> Dict[str, Decimal]:
        """Get detailed rate component breakdown."""
        return {
            'base_rate': self.staking_metrics.current_apy,
            'risk_premium': self.loan_risk_score * Decimal('0.01'),
            'market_adjustment': self.market_factors.get('volatility_premium', Decimal('0')),
            'total_rate': self.final_interest_rate
        }
```

## Configuration

### CollateralConfig

Configuration for collateral analysis.

```python
@dataclass
class CollateralConfig:
    min_collateral_ratio: Decimal = Decimal('1.35')  # 135%
    liquidation_threshold: Decimal = Decimal('1.15')  # 115%
    safety_margin: Decimal = Decimal('0.10')  # 10%
    max_concentration: Decimal = Decimal('0.70')  # 70%
    volatility_window_days: int = 30
    price_staleness_threshold: int = 3600  # seconds

    @classmethod
    def from_env(cls) -> 'CollateralConfig':
        """Create config from environment variables."""
        return cls(
            min_collateral_ratio=Decimal(os.getenv('COLLATERAL_MIN_RATIO', '1.35')),
            liquidation_threshold=Decimal(os.getenv('COLLATERAL_LIQ_THRESHOLD', '1.15')),
            safety_margin=Decimal(os.getenv('COLLATERAL_SAFETY_MARGIN', '0.10'))
        )
```

### InterestRateConfig

Configuration for interest rate calculation.

```python
@dataclass
class InterestRateConfig:
    base_rate: Decimal = Decimal('0.04')  # 4%
    risk_premium_multiplier: Decimal = Decimal('1.5')
    max_rate: Decimal = Decimal('0.25')  # 25%
    min_rate: Decimal = Decimal('0.01')  # 1%
    confidence_threshold: Decimal = Decimal('0.20')  # 20%

    @classmethod
    def from_env(cls) -> 'InterestRateConfig':
        """Create config from environment variables."""
        return cls(
            base_rate=Decimal(os.getenv('RATE_BASE', '0.04')),
            risk_premium_multiplier=Decimal(os.getenv('RATE_RISK_MULTIPLIER', '1.5')),
            max_rate=Decimal(os.getenv('RATE_MAX', '0.25'))
        )
```

## Service Interface

### AlgorandLendingService

Unified service interface providing simplified access to all functionality.

#### Methods

##### get_service_info()

```python
def get_service_info() -> Dict[str, Any]:
    """Get service information."""
    return {
        'service_name': 'Algorand Lending Business Logic',
        'version': '1.0.0',
        'capabilities': ['collateral_analysis', 'interest_rate_calculation', 'risk_assessment']
    }
```

##### evaluate_loan()

```python
def evaluate_loan(
    borrower_address: str,
    loan_amount: float,
    collateral_assets: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Evaluate a complete loan application."""
    # Returns: {'decision': bool, 'approved_amount': float, 'interest_rate': float, ...}
```

**Example:**

```python
from algorand_lending_bl import AlgorandLendingService

service = AlgorandLendingService()

result = service.evaluate_loan(
    borrower_address="ALGORAND_ADDRESS_HERE",
    loan_amount=50000,
    collateral_assets=[
        {"asset_id": "0", "amount": 100000},      # 100k ALGO
        {"asset_id": "31566704", "amount": 25000} # 25k USDC
    ]
)

print(result)
# Output:
# {
#     'decision': True,
#     'approved_amount': 45000.0,
#     'interest_rate': 0.0825,
#     'collateral_analysis': {...},
#     'risk_assessment': {...}
# }
```

## Error Handling

### Common Exceptions

#### ValueError
Raised for invalid input parameters:
- Negative loan amounts
- Invalid asset quantities
- Malformed addresses

```python
try:
    analysis = await analyzer.analyze_collateral(
        assets=[algo_token],
        quantities=[Decimal("-1000")],  # Negative quantity
        loan_amount_usd=Decimal("5000")
    )
except ValueError as e:
    print(f"Invalid input: {e}")
```

#### TypeError
Raised for incorrect parameter types:
- Non-Decimal numeric values
- Wrong object types

#### AssertionError
Raised for logical inconsistencies:
- Mismatched asset/quantity list lengths
- Invalid configuration combinations

### Error Response Format

```python
{
    'error': True,
    'error_type': 'ValueError',
    'message': 'Loan amount must be positive',
    'details': {
        'parameter': 'loan_amount_usd',
        'value': '0',
        'constraint': 'must be > 0'
    }
}
```

## Performance Guidelines

### Recommended Usage Patterns

1. **Batch Processing**: Process multiple loans concurrently
```python
tasks = [analyzer.analyze_collateral(...) for _ in loan_requests]
results = await asyncio.gather(*tasks)
```

2. **Engine Reuse**: Create engines once, reuse for multiple calculations
```python
analyzer, engine = create_lending_engines()
# Reuse these instances for multiple calculations
```

3. **Configuration Caching**: Load configuration once
```python
config = CollateralConfig.from_env()
analyzer = CollateralAnalyzer(config)
```

### Performance Expectations

- **Collateral Analysis**: ~100-300ms per analysis
- **Interest Rate Calculation**: ~50-150ms per calculation
- **Concurrent Processing**: 5-10x speedup for batch operations
- **Memory Usage**: ~50-100MB per engine instance

## Examples

### Complete Loan Evaluation

```python
import asyncio
from decimal import Decimal
from algorand_lending_bl import *

async def complete_loan_evaluation():
    # Create engines
    analyzer, engine = create_lending_engines()

    # Borrower
    borrower = AlgorandAddress(
        address="BORROWER_ADDRESS_EXAMPLE_123456789012345678901234567890",
        is_valid=True
    )

    # Collateral assets
    assets = [
        ASAToken(
            asset_id="0", symbol="ALGO", name="Algorand",
            decimals=6, total_supply=Decimal("10000000000"),
            circulating_supply=Decimal("8000000000"),
            creator_address="ALGORAND"
        ),
        ASAToken(
            asset_id="31566704", symbol="USDC", name="USD Coin",
            decimals=6, total_supply=Decimal("1000000000"),
            circulating_supply=Decimal("800000000"),
            creator_address="CENTRE"
        )
    ]

    quantities = [Decimal("50000"), Decimal("25000")]  # 50k ALGO, 25k USDC
    loan_amount = Decimal("15000")  # $15k loan

    # Step 1: Analyze collateral
    collateral_analysis = await analyzer.analyze_collateral(
        assets=assets,
        quantities=quantities,
        loan_amount_usd=loan_amount
    )

    print(f"Collateral sufficient: {collateral_analysis.is_sufficient}")

    if collateral_analysis.is_sufficient:
        # Step 2: Calculate interest rate
        rate_calc = await engine.calculate_rate(
            borrower=borrower,
            loan_amount_usd=loan_amount,
            loan_duration_days=180,
            collateral_assets=[asset.symbol for asset in assets],
            collateral_value_usd=collateral_analysis.total_adjusted_value
        )

        # Step 3: Make decision
        safety_margin = collateral_analysis.safety_margin()
        approved = (
            collateral_analysis.is_sufficient and
            safety_margin >= Decimal('0.15') and
            rate_calc.confidence_interval <= Decimal('0.25')
        )

        print(f"Interest rate: {rate_calc.final_interest_rate:.3%}")
        print(f"Safety margin: {safety_margin:.2%}")
        print(f"Decision: {'APPROVED' if approved else 'NEEDS_REVIEW'}")
    else:
        print(f"Additional collateral needed: ${collateral_analysis.additional_collateral_needed:,.2f}")

# Run the example
asyncio.run(complete_loan_evaluation())
```

### Multi-Asset Portfolio Analysis

```python
async def multi_asset_analysis():
    analyzer = CollateralAnalyzer()

    # Create diverse portfolio
    portfolio = [
        (ASAToken(asset_id="0", symbol="ALGO", name="Algorand", ...), Decimal("75000")),
        (ASAToken(asset_id="31566704", symbol="USDC", name="USD Coin", ...), Decimal("30000")),
        (ASAToken(asset_id="386192725", symbol="goBTC", name="Wrapped Bitcoin", ...), Decimal("0.5"))
    ]

    assets, quantities = zip(*portfolio)

    analysis = await analyzer.analyze_collateral(
        assets=list(assets),
        quantities=list(quantities),
        loan_amount_usd=Decimal("25000")
    )

    # Analyze portfolio risk
    print(f"Portfolio diversity: {analysis.portfolio_risk.diversification_score:.2%}")
    print(f"Concentration risk: {analysis.portfolio_risk.concentration_risk:.2%}")

    # Individual position analysis
    for i, position in enumerate(analysis.positions):
        print(f"{position.asset.symbol}: {position.risk_level.value} risk")

asyncio.run(multi_asset_analysis())
```

### Custom Configuration

```python
# Create custom configuration
custom_config = CollateralConfig(
    min_collateral_ratio=Decimal('1.50'),  # Require 150% collateral
    liquidation_threshold=Decimal('1.25'),  # Liquidate at 125%
    safety_margin=Decimal('0.15')          # 15% safety margin
)

# Use with analyzer
analyzer = CollateralAnalyzer(custom_config)

# Analysis will use custom thresholds
analysis = await analyzer.analyze_collateral(...)
```

---

## Version Information

- **Package Version**: 1.0.0
- **API Version**: 1.0
- **Last Updated**: 2025-09-20
- **Compatibility**: Python 3.9+

For more examples and advanced usage, see the included `example.py` and test files.