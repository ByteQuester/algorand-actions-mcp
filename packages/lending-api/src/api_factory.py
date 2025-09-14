"""
Clean API Factory - Dependency Injection Pattern
NO production configuration embedded
"""

import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware

# Import the pure lending core package
from algorand_lending_core import LendingEngine, LoanRequest, LoanResult, BlockchainTransactionBuilder
from algorand_lending_core import LoanStatus, CollateralType

class ConfigurableBlockchainProvider:
    """
    Example blockchain provider with dependency injection

    NO hardcoded configurations - everything passed in
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with injected configuration"""
        self.algod_url = config.get('algod_url')
        self.indexer_url = config.get('indexer_url')
        self.network = config.get('network', 'testnet')

        # In real implementation, initialize Algorand SDK clients here
        # self.algod_client = algod.AlgodClient("", self.algod_url)

    async def get_account_balance(self, address: str) -> Dict[str, Any]:
        """Get account balance from blockchain"""
        # This would be real Algorand SDK calls in production
        # For example purposes, return mock data
        return {
            "address": address,
            "algo_balance_micro": 50_000_000,
            "algo_balance": 50.0,
            "usdc_balance_micro": 1_000_000,
            "usdc_balance": 1.0,
            "asa_balances": {}
        }

    async def create_transaction(self, **kwargs) -> Dict[str, Any]:
        """Create blockchain transaction"""
        # Real Algorand transaction creation would go here
        return {
            "transaction_id": f"TX_{kwargs.get('amount', 0)}_MOCK",
            "unsigned_txn": "mock_unsigned_transaction_bytes",
            "estimated_fee": 1000
        }

    async def submit_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Submit transaction to blockchain"""
        # Real transaction submission would go here
        return transaction_data.get("transaction_id", "MOCK_TX_ID")

class LendingAPIFactory:
    """
    Factory for creating lending API instances

    Uses dependency injection pattern - NO hardcoded configs
    """

    @staticmethod
    def create_app(config: Dict[str, Any]) -> FastAPI:
        """
        Factory method to create FastAPI application

        Args:
            config: Complete configuration dictionary, e.g.:
            {
                "api": {
                    "title": "My Lending API",
                    "version": "1.0.0",
                    "cors_origins": ["http://localhost:3000"]
                },
                "blockchain": {
                    "algod_url": "https://testnet-api.algonode.cloud",
                    "indexer_url": "https://testnet-idx.algonode.cloud",
                    "network": "testnet"
                },
                "lending": {
                    "agents": {
                        "negotiation": {"strategy": "conservative"},
                        "liquidity": {"min_threshold": 1000000}
                    }
                }
            }
        """

        # Extract configurations
        api_config = config.get('api', {})
        blockchain_config = config.get('blockchain', {})
        lending_config = config.get('lending', {})

        # Create FastAPI app with injected config
        app = FastAPI(
            title=api_config.get('title', 'Lending API'),
            version=api_config.get('version', '1.0.0'),
            description=api_config.get('description', 'Clean Lending API with dependency injection')
        )

        # Configure CORS with injected origins
        cors_origins = api_config.get('cors_origins', ['http://localhost:3000'])
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Dependency injection setup
        def get_blockchain_provider() -> BlockchainProvider:
            """Create blockchain provider with injected config"""
            return ConfigurableBlockchainProvider(blockchain_config)

        def get_lending_engine(
            blockchain_provider: BlockchainProvider = Depends(get_blockchain_provider)
        ) -> LendingEngine:
            """Create lending engine with injected dependencies"""
            return LendingEngine(blockchain_provider, lending_config)

        # API Routes with dependency injection
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "version": api_config.get('version', '1.0.0'),
                "message": "Lending API operational"
            }

        @app.post("/loans/request")
        async def create_loan_request(
            request: LoanRequest,
            engine: LendingEngine = Depends(get_lending_engine)
        ) -> LoanResult:
            """Create new loan request"""
            try:
                result = await engine.process_loan_request(request)
                return result
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Loan processing failed: {str(e)}"
                )

        @app.get("/loans/{loan_id}/status")
        async def get_loan_status(
            loan_id: str,
            engine: LendingEngine = Depends(get_lending_engine)
        ) -> LoanResult:
            """Get loan status"""
            result = await engine.get_loan_status(loan_id)

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Loan not found"
                )

            return result

        @app.get("/account/{address}/balance")
        async def get_account_balance(
            address: str,
            engine: LendingEngine = Depends(get_lending_engine)
        ):
            """Get account balance"""
            try:
                balance = await engine.get_account_balance(address)
                return balance
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Balance retrieval failed: {str(e)}"
                )

        return app

# Example usage (would be in separate deployment/consumer code)
def create_development_config() -> Dict[str, Any]:
    """Example: Create development configuration"""
    return {
        "api": {
            "title": "Development Lending API",
            "version": "1.0.0-dev",
            "cors_origins": ["http://localhost:3000", "http://localhost:8081"]
        },
        "blockchain": {
            "algod_url": "https://testnet-api.algonode.cloud",
            "indexer_url": "https://testnet-idx.algonode.cloud",
            "network": "testnet"
        },
        "lending": {
            "agents": {
                "negotiation": {"strategy": "development"},
                "liquidity": {"min_threshold": 100000},
                "execution": {"auto_execute": False}
            }
        }
    }

def create_production_config() -> Dict[str, Any]:
    """Example: Create production configuration"""
    return {
        "api": {
            "title": "Production Lending API",
            "version": "1.0.0",
            "cors_origins": [os.getenv("FRONTEND_URL", "https://app.example.com")]
        },
        "blockchain": {
            "algod_url": os.getenv("ALGOD_URL", "https://mainnet-api.algonode.cloud"),
            "indexer_url": os.getenv("INDEXER_URL", "https://mainnet-idx.algonode.cloud"),
            "network": "mainnet"
        },
        "lending": {
            "agents": {
                "negotiation": {"strategy": "conservative"},
                "liquidity": {"min_threshold": 10_000_000},
                "execution": {"auto_execute": False, "require_signatures": True}
            }
        }
    }

# Clean usage pattern (no hardcoded configs!)
if __name__ == "__main__":
    import uvicorn

    # Configuration is INJECTED based on environment
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        config = create_production_config()
    else:
        config = create_development_config()

    # Create app with injected configuration
    app = LendingAPIFactory.create_app(config)

    # Server configuration also injected
    server_config = config.get('server', {})
    uvicorn.run(
        app,
        host=server_config.get('host', '0.0.0.0'),
        port=server_config.get('port', 8003),
        log_level=server_config.get('log_level', 'info')
    )