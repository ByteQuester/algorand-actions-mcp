# Algorand Lending Business Logic - Vendor Integration Guide

## Overview

The `algorand-lending-business-logic` package is designed for easy vendoring into any Algorand-based project. This guide demonstrates how to integrate the lending engines with minimal setup, taking less than 5 minutes instead of hours.

## Quick Start (3-Line Integration)

```python
from algorand_lending_bl import create_lending_service
lending_service = create_lending_service()
# Ready to use! All engines available in lending_service
```

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Basic Integration](#basic-integration)
3. [Configuration Options](#configuration-options)
4. [Engine Usage Examples](#engine-usage-examples)
5. [Integration Patterns](#integration-patterns)
6. [Troubleshooting](#troubleshooting)
7. [Performance Notes](#performance-notes)
8. [Advanced Usage](#advanced-usage)

## Installation & Setup

### Method 1: Copy-Paste Vendoring (Recommended)

1. **Copy the package directory**:
   ```bash
   cp -r /path/to/algorand-lending-business-logic/algorand_lending_bl ./your_project/
   ```

2. **Install minimal dependencies**:
   ```bash
   pip install algorand-sdk pyyaml httpx
   ```

3. **Start using immediately**:
   ```python
   from algorand_lending_bl import create_lending_service
   service = create_lending_service()
   ```

### Method 2: Git Submodule

```bash
git submodule add /path/to/algorand-lending-business-logic vendor/lending
```

### Method 3: Package Installation

```bash
cd /path/to/algorand-lending-business-logic
pip install -e .
```

## Basic Integration

### Simple Service Creation

```python
from algorand_lending_bl import create_lending_service

# Create service with default configuration
lending_service = create_lending_service()

# Access individual engines
collateral_engine = lending_service["collateral"]
interest_rate_engine = lending_service["interest_rates"]
loan_approval_engine = lending_service["loan_approval"]
risk_assessment_engine = lending_service["risk_assessment"]
```

### Individual Engine Creation

```python
from algorand_lending_bl import (
    CollateralAnalyzer,
    InterestRateEngine,
    LoanApprovalEngine,
    RiskAssessmentEngine,
    DEFAULT_CONFIG
)

# Create engines individually
collateral_analyzer = CollateralAnalyzer(DEFAULT_CONFIG.collateral)
interest_rate_engine = InterestRateEngine(DEFAULT_CONFIG.interest_rates)
loan_approval_engine = LoanApprovalEngine(DEFAULT_CONFIG.loan_approval)
risk_assessment_engine = RiskAssessmentEngine(DEFAULT_CONFIG.risk_assessment)
```

## Configuration Options

### Using Default Configuration

```python
from algorand_lending_bl import DEFAULT_CONFIG, create_lending_service

# Use default configuration (works out of the box)
service = create_lending_service(DEFAULT_CONFIG)
```

### Custom Configuration

```python
from algorand_lending_bl import (
    AlgorandLendingConfig,
    NetworkConfig,
    create_testnet_config,
    create_mainnet_config
)

# For TestNet
testnet_config = create_testnet_config()
service = create_lending_service(testnet_config)

# For MainNet
mainnet_config = create_mainnet_config()
service = create_lending_service(mainnet_config)

# Custom configuration
custom_config = AlgorandLendingConfig(
    network=NetworkConfig(
        algod_token="your-token",
        algod_server="your-server",
        network_name="custom"
    )
)
service = create_lending_service(custom_config)
```

### Environment-Based Configuration

```python
from algorand_lending_bl import create_config_from_env

# Automatically load from environment variables
config = create_config_from_env()
service = create_lending_service(config)
```

Environment variables:
- `ALGOD_TOKEN`: Algorand node token
- `ALGOD_SERVER`: Algorand node server URL
- `NETWORK_NAME`: Network name (testnet/mainnet)

## Engine Usage Examples

### Collateral Analysis

```python
from algorand_lending_bl import create_lending_service, ASAToken, AlgorandAddress

service = create_lending_service()
collateral_engine = service["collateral"]

# Define collateral assets
collateral_assets = [
    ASAToken(asset_id=0, amount=1000000),      # 1 ALGO
    ASAToken(asset_id=31566704, amount=5000000) # 5 USDC
]

borrower_address = AlgorandAddress("YOUR_ALGORAND_ADDRESS_HERE")

# Analyze collateral
analysis = collateral_engine.analyze_collateral(collateral_assets, borrower_address)

print(f"Total collateral value: ${analysis.total_value:.2f}")
print(f"Liquidity tier: {analysis.liquidity_tier}")
print(f"Portfolio risk: {analysis.portfolio_risk}")
```

### Interest Rate Calculation

```python
from algorand_lending_bl import LoanRequest

# Create loan request
loan_request = LoanRequest(
    borrower=AlgorandAddress("YOUR_ADDRESS"),
    requested_amount=500000,  # 0.5 ALGO in microALGOs
    collateral_assets=collateral_assets,
    loan_duration_days=30
)

# Calculate interest rate
rate_calculation = service["interest_rates"].calculate_interest_rate(loan_request)

print(f"Base rate: {rate_calculation.base_rate:.2%}")
print(f"Final rate: {rate_calculation.final_rate:.2%}")
print(f"Risk premium: {rate_calculation.risk_premium:.2%}")
```

### Loan Approval

```python
# Evaluate loan application
loan_decision = service["loan_approval"].evaluate_loan(loan_request)

print(f"Decision: {loan_decision.decision}")
print(f"Confidence: {loan_decision.confidence}")
print(f"Approved amount: {loan_decision.approved_amount}")

if loan_decision.terms:
    print(f"Interest rate: {loan_decision.terms.interest_rate:.2%}")
    print(f"Duration: {loan_decision.terms.duration_days} days")
```

### Risk Assessment

```python
# Assess loan risk
risk_assessment = service["risk_assessment"].assess_risk(loan_request)

print(f"Overall risk score: {risk_assessment.overall_score:.2f}")
print(f"Risk level: {risk_assessment.risk_level}")
print(f"Borrower risk: {risk_assessment.borrower_risk:.2f}")
print(f"Collateral risk: {risk_assessment.collateral_risk:.2f}")
```

## Integration Patterns

### Pattern 1: Microservice Integration

```python
# microservice.py
from algorand_lending_bl import create_lending_service
from flask import Flask, request, jsonify

app = Flask(__name__)
lending_service = create_lending_service()

@app.route('/analyze-loan', methods=['POST'])
def analyze_loan():
    data = request.json

    # Create loan request from API data
    loan_request = LoanRequest(**data)

    # Get all analyses
    collateral_analysis = lending_service["collateral"].analyze_collateral(
        loan_request.collateral_assets,
        loan_request.borrower
    )

    rate_calculation = lending_service["interest_rates"].calculate_interest_rate(loan_request)
    loan_decision = lending_service["loan_approval"].evaluate_loan(loan_request)
    risk_assessment = lending_service["risk_assessment"].assess_risk(loan_request)

    return jsonify({
        "collateral": collateral_analysis.to_dict(),
        "interest_rate": rate_calculation.to_dict(),
        "approval": loan_decision.to_dict(),
        "risk": risk_assessment.to_dict()
    })
```

### Pattern 2: CLI Tool Integration

```python
# loan_cli.py
import click
from algorand_lending_bl import create_lending_service, LoanRequest, AlgorandAddress, ASAToken

@click.command()
@click.option('--borrower', required=True, help='Borrower address')
@click.option('--amount', required=True, type=int, help='Loan amount in microALGOs')
@click.option('--collateral', required=True, help='Collateral assets (JSON)')
def evaluate_loan(borrower, amount, collateral):
    """Evaluate a loan application using Algorand lending engines."""

    service = create_lending_service()

    # Parse collateral JSON and create loan request
    collateral_assets = [ASAToken(**asset) for asset in json.loads(collateral)]
    loan_request = LoanRequest(
        borrower=AlgorandAddress(borrower),
        requested_amount=amount,
        collateral_assets=collateral_assets,
        loan_duration_days=30
    )

    # Run analysis
    decision = service["loan_approval"].evaluate_loan(loan_request)

    click.echo(f"Loan Decision: {decision.decision}")
    click.echo(f"Approved Amount: {decision.approved_amount}")

if __name__ == '__main__':
    evaluate_loan()
```

### Pattern 3: Background Service Integration

```python
# background_service.py
import asyncio
from algorand_lending_bl import create_lending_service

class LendingAnalysisService:
    def __init__(self):
        self.lending_service = create_lending_service()
        self.analysis_queue = asyncio.Queue()

    async def analyze_loan_async(self, loan_request):
        """Async loan analysis."""
        # Run CPU-bound analysis in thread pool
        loop = asyncio.get_event_loop()

        collateral_task = loop.run_in_executor(
            None,
            self.lending_service["collateral"].analyze_collateral,
            loan_request.collateral_assets,
            loan_request.borrower
        )

        rate_task = loop.run_in_executor(
            None,
            self.lending_service["interest_rates"].calculate_interest_rate,
            loan_request
        )

        # Run analyses concurrently
        collateral_result, rate_result = await asyncio.gather(
            collateral_task, rate_task
        )

        return {
            "collateral": collateral_result,
            "interest_rate": rate_result
        }

    async def start_processing(self):
        """Start processing loan requests from queue."""
        while True:
            loan_request = await self.analysis_queue.get()
            result = await self.analyze_loan_async(loan_request)
            # Process result...
            self.analysis_queue.task_done()
```

### Pattern 4: Batch Processing Integration

```python
# batch_processor.py
from algorand_lending_bl import create_lending_service
import pandas as pd

class LoanBatchProcessor:
    def __init__(self):
        self.lending_service = create_lending_service()

    def process_loan_batch(self, loan_requests_df):
        """Process multiple loan requests efficiently."""
        results = []

        for _, row in loan_requests_df.iterrows():
            loan_request = LoanRequest(
                borrower=AlgorandAddress(row['borrower']),
                requested_amount=row['amount'],
                collateral_assets=[ASAToken(asset_id=0, amount=row['collateral_algo'])],
                loan_duration_days=row['duration']
            )

            # Quick approval check
            decision = self.lending_service["loan_approval"].evaluate_loan(loan_request)

            results.append({
                'borrower': row['borrower'],
                'decision': decision.decision.value,
                'approved_amount': decision.approved_amount,
                'confidence': decision.confidence.value
            })

        return pd.DataFrame(results)

# Usage
processor = LoanBatchProcessor()
loan_df = pd.read_csv('loan_applications.csv')
results_df = processor.process_loan_batch(loan_df)
results_df.to_csv('loan_decisions.csv', index=False)
```

## Troubleshooting

### Common Issues

#### Import Errors

```python
# Problem: ModuleNotFoundError: No module named 'algorand_lending_bl'
# Solution: Ensure the package is in your Python path
import sys
sys.path.insert(0, '/path/to/algorand_lending_bl')
```

#### Configuration Errors

```python
# Problem: Invalid configuration
# Solution: Use default config first
from algorand_lending_bl import DEFAULT_CONFIG, validate_config

# Validate your configuration
try:
    validate_config(your_config)
except Exception as e:
    print(f"Configuration error: {e}")
    # Fall back to default
    config = DEFAULT_CONFIG
```

#### Network Connection Issues

```python
# Problem: Unable to connect to Algorand node
# Solution: Use mock mode for development
from algorand_lending_bl import create_testnet_config

config = create_testnet_config()
config.network.mock_mode = True  # Enable mock mode
service = create_lending_service(config)
```

#### Memory Issues with Large Datasets

```python
# Problem: Memory usage too high with large collateral portfolios
# Solution: Use batch processing
def analyze_large_portfolio(assets, batch_size=100):
    results = []
    for i in range(0, len(assets), batch_size):
        batch = assets[i:i+batch_size]
        batch_result = collateral_engine.analyze_collateral(batch, borrower)
        results.append(batch_result)
    return results
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

from algorand_lending_bl import create_lending_service

# Service will now log detailed information
service = create_lending_service()
```

### Validation

```python
# Validate your setup
from algorand_lending_bl import VENDOR_INFO

print(f"Package: {VENDOR_INFO['name']} v{VENDOR_INFO['version']}")
print(f"Dependencies: {VENDOR_INFO['dependencies']}")
print(f"Engines: {list(VENDOR_INFO['engines'].keys())}")

# Test basic functionality
try:
    service = create_lending_service()
    print("✓ Service creation successful")

    if len(service) >= 4:
        print("✓ All engines available")
    else:
        print("✗ Missing engines")

except Exception as e:
    print(f"✗ Setup failed: {e}")
```

## Performance Notes

### Optimization Tips

1. **Reuse Service Instance**: Create the service once and reuse it
   ```python
   # Good
   service = create_lending_service()
   for loan in loans:
       result = service["loan_approval"].evaluate_loan(loan)

   # Bad - creates new service each time
   for loan in loans:
       service = create_lending_service()
       result = service["loan_approval"].evaluate_loan(loan)
   ```

2. **Batch Operations**: Process multiple requests together when possible
   ```python
   # Analyze multiple collateral positions together
   all_analyses = []
   for collateral_set in collateral_sets:
       analysis = collateral_engine.analyze_collateral(collateral_set, borrower)
       all_analyses.append(analysis)
   ```

3. **Configuration Caching**: Cache configuration objects
   ```python
   # Cache expensive configuration
   _config_cache = {}

   def get_config(network_type):
       if network_type not in _config_cache:
           if network_type == "testnet":
               _config_cache[network_type] = create_testnet_config()
           else:
               _config_cache[network_type] = create_mainnet_config()
       return _config_cache[network_type]
   ```

### Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Service Creation | <0.1s | One-time setup |
| Collateral Analysis | <0.05s | Per analysis |
| Interest Rate Calculation | <0.02s | Per calculation |
| Loan Approval | <0.03s | Per evaluation |
| Risk Assessment | <0.04s | Per assessment |

## Advanced Usage

### Custom Engine Configuration

```python
from algorand_lending_bl import (
    CollateralConfig,
    InterestRateConfig,
    AlgorandLendingConfig
)

# Custom collateral configuration
collateral_config = CollateralConfig(
    min_collateral_ratio=1.5,  # 150% collateralization
    liquidation_threshold=1.2,  # 120% liquidation threshold
    supported_assets=[0, 31566704]  # ALGO and USDC only
)

# Custom interest rate configuration
interest_config = InterestRateConfig(
    base_rate=0.05,  # 5% base rate
    risk_multiplier=2.0,  # 2x risk premium
    max_rate=0.25  # 25% maximum rate
)

# Create custom configuration
custom_config = AlgorandLendingConfig(
    collateral=collateral_config,
    interest_rates=interest_config
)

service = create_lending_service(custom_config)
```

### Plugin Architecture

```python
# Extend functionality with custom plugins
class CustomRiskAssessmentEngine(RiskAssessmentEngine):
    def assess_risk(self, loan_request):
        # Call parent implementation
        base_assessment = super().assess_risk(loan_request)

        # Add custom risk factors
        custom_risk = self._calculate_custom_risk(loan_request)

        # Combine assessments
        base_assessment.overall_score = (
            base_assessment.overall_score * 0.8 +
            custom_risk * 0.2
        )

        return base_assessment

    def _calculate_custom_risk(self, loan_request):
        # Your custom risk calculation
        return 0.1

# Use custom engine
from algorand_lending_bl import DEFAULT_CONFIG
custom_engine = CustomRiskAssessmentEngine(DEFAULT_CONFIG.risk_assessment)
```

### Data Export and Integration

```python
# Export analysis results for external systems
def export_analysis_results(loan_request, output_format='json'):
    service = create_lending_service()

    # Get all analyses
    results = {
        'collateral': service["collateral"].analyze_collateral(
            loan_request.collateral_assets,
            loan_request.borrower
        ).to_dict(),
        'interest_rate': service["interest_rates"].calculate_interest_rate(
            loan_request
        ).to_dict(),
        'approval': service["loan_approval"].evaluate_loan(
            loan_request
        ).to_dict(),
        'risk': service["risk_assessment"].assess_risk(
            loan_request
        ).to_dict()
    }

    if output_format == 'json':
        return json.dumps(results, indent=2)
    elif output_format == 'csv':
        df = pd.json_normalize(results)
        return df.to_csv(index=False)
    elif output_format == 'xml':
        # Convert to XML format
        return dict_to_xml(results)
```

## Conclusion

The `algorand-lending-business-logic` package is designed for maximum ease of integration. With just 3 lines of code, you can have a full lending analysis system running in your project. The package handles all the complexity internally while exposing clean, simple interfaces for your application.

### Key Benefits

- **5-minute integration** vs. hours of custom development
- **Minimal dependencies** (3 packages vs. 36+ for full platform)
- **Production-ready** engines with comprehensive analysis
- **Flexible configuration** for different use cases
- **Copy-paste vendoring** with no complex setup

### Next Steps

1. Run the vendor validation test: `python scripts/vendor_test.py`
2. Try the example integration patterns
3. Customize configuration for your use case
4. Build your lending application!

For additional support or questions, refer to the troubleshooting section or check the example integration patterns in the `examples/vendor_integration/` directory.