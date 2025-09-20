"""
Simple configuration for Algorand Lending Business Logic.
"""

import os

# Default configuration
DEFAULT_CONFIG = {
    'algorand': {
        'server': os.getenv('ALGORAND_SERVER', 'https://testnet-api.algonode.cloud'),
        'token': os.getenv('ALGORAND_TOKEN', ''),
        'network': os.getenv('ALGORAND_NETWORK', 'testnet')
    },
    'lending': {
        'max_loan_amount': 1000000,  # microAlgos
        'min_collateral_ratio': 1.5,
        'default_interest_rate': 0.05
    }
}

def get_config():
    """Get configuration dictionary."""
    return DEFAULT_CONFIG.copy()