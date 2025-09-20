# Algorand Lending Business Logic

Simple, vendorable Algorand lending engines for copy-paste integration.

## 30-Second Integration

```python
from algorand_lending_bl import AlgorandLendingService

# Initialize service
service = AlgorandLendingService()

# Evaluate a loan request
loan_request = {
    "borrower_address": "ALGORAND_ADDRESS_HERE",
    "loan_amount": 100000,  # microAlgos
    "collateral_amount": 200000,  # microAlgos
    "duration_days": 30
}

result = service.evaluate_loan(loan_request)
print(f"Loan approved: {result['approved']}")
print(f"Interest rate: {result['interest_rate']}")
```

## Installation

### Option 1: Copy-Paste Vendoring (Recommended)
```bash
# Copy this entire directory into your project
cp -r algorand-lending-business-logic/ your-project/vendor/
```

### Option 2: Pip Install
```bash
pip install -e ./algorand-lending-business-logic
```

## Configuration

Set environment variables:
```bash
export ALGORAND_SERVER="https://testnet-api.algonode.cloud"
export ALGORAND_TOKEN=""  # Optional
export ALGORAND_NETWORK="testnet"
```

## Core API

- `evaluate_loan(request)` - Evaluate loan eligibility
- `calculate_rates(params)` - Calculate interest rates
- `analyze_collateral(assets)` - Analyze collateral value
- `assess_risk(profile)` - Assess borrower risk

## Dependencies

- algorand-sdk>=2.0.0
- pyyaml>=6.0
- httpx>=0.24.0

## License

MIT