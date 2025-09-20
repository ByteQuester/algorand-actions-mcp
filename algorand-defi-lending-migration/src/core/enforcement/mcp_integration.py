"""
MCP Integration for Blockchain Transactions
Connects escrow system with MCP Writer service
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import base64
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MCPConfig:
    """Configuration for MCP services"""
    writer_endpoint: str = "http://localhost:3001"
    reader_endpoint: str = "http://localhost:8002"
    timeout_seconds: int = 30
    max_retries: int = 3

class MCPBlockchainClient:
    """
    Client for interacting with MCP services for blockchain operations
    Handles smart contract deployment and transaction execution
    """

    def __init__(self, config: Optional[MCPConfig] = None):
        """Initialize MCP client with configuration"""
        self.config = config or MCPConfig()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def deploy_smart_contract(
        self,
        approval_program: str,
        clear_program: str,
        global_schema: Dict[str, int],
        local_schema: Dict[str, int],
        creator_address: str,
        app_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Deploy a smart contract using MCP writer service

        Returns:
            Dict with app_id, transaction_id, and contract_address
        """
        try:
            # Encode TEAL programs
            approval_bytes = approval_program.encode('utf-8')
            clear_bytes = clear_program.encode('utf-8')

            payload = {
                "action": "deploy_application",
                "params": {
                    "approval_program": base64.b64encode(approval_bytes).decode('utf-8'),
                    "clear_program": base64.b64encode(clear_bytes).decode('utf-8'),
                    "global_schema": global_schema,
                    "local_schema": local_schema,
                    "creator": creator_address,
                    "app_args": app_args or []
                }
            }

            async with self.session.post(
                f"{self.config.writer_endpoint}/api/v1/transactions/smart-contract",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "app_id": result.get("app_id"),
                        "transaction_id": result.get("transaction_id"),
                        "contract_address": result.get("contract_address")
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Contract deployment failed: {error_text}")
                    return {
                        "success": False,
                        "error": f"Deployment failed: {error_text}"
                    }

        except asyncio.TimeoutError:
            logger.error("Contract deployment timed out")
            return {"success": False, "error": "Deployment timed out"}
        except Exception as e:
            logger.error(f"Contract deployment error: {e}")
            return {"success": False, "error": str(e)}

    async def fund_escrow(
        self,
        escrow_address: str,
        sender_address: str,
        amount: int,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fund an escrow account with collateral

        Returns:
            Transaction result with transaction_id
        """
        try:
            payload = {
                "action": "send_payment",
                "params": {
                    "sender": sender_address,
                    "receiver": escrow_address,
                    "amount": amount,
                    "note": note or f"Escrow funding for {escrow_address}"
                }
            }

            async with self.session.post(
                f"{self.config.writer_endpoint}/api/v1/transactions/payment",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "transaction_id": result.get("transaction_id"),
                        "confirmed_round": result.get("confirmed_round")
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Funding failed: {error_text}"
                    }

        except Exception as e:
            logger.error(f"Escrow funding error: {e}")
            return {"success": False, "error": str(e)}

    async def execute_liquidation(
        self,
        app_id: int,
        escrow_address: str,
        lender_address: str,
        collateral_amount: int,
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute liquidation of escrow collateral

        Returns:
            Liquidation transaction result
        """
        try:
            payload = {
                "action": "call_application",
                "params": {
                    "app_id": app_id,
                    "sender": escrow_address,
                    "app_args": ["liquidate", json.dumps(evidence)],
                    "accounts": [lender_address],
                    "note": f"Liquidation of escrow {app_id}"
                }
            }

            async with self.session.post(
                f"{self.config.writer_endpoint}/api/v1/transactions/app-call",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "transaction_id": result.get("transaction_id"),
                        "distribution": {
                            "lender": collateral_amount,
                            "platform_fee": 0  # Can add platform fee logic
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Liquidation failed: {error_text}"
                    }

        except Exception as e:
            logger.error(f"Liquidation execution error: {e}")
            return {"success": False, "error": str(e)}

    async def release_collateral(
        self,
        app_id: int,
        escrow_address: str,
        borrower_address: str,
        collateral_amount: int,
        proof_of_payment: str
    ) -> Dict[str, Any]:
        """
        Release collateral back to borrower after loan repayment

        Returns:
            Release transaction result
        """
        try:
            payload = {
                "action": "call_application",
                "params": {
                    "app_id": app_id,
                    "sender": escrow_address,
                    "app_args": ["release", proof_of_payment],
                    "accounts": [borrower_address],
                    "note": f"Collateral release for escrow {app_id}"
                }
            }

            async with self.session.post(
                f"{self.config.writer_endpoint}/api/v1/transactions/app-call",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "transaction_id": result.get("transaction_id"),
                        "released_amount": collateral_amount,
                        "recipient": borrower_address
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Release failed: {error_text}"
                    }

        except Exception as e:
            logger.error(f"Collateral release error: {e}")
            return {"success": False, "error": str(e)}

    async def get_escrow_balance(self, escrow_address: str) -> Dict[str, Any]:
        """
        Get the current balance of an escrow account

        Returns:
            Account balance information
        """
        try:
            async with self.session.get(
                f"{self.config.reader_endpoint}/api/v1/accounts/{escrow_address}/balance"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "balance": result.get("balance", 0),
                        "min_balance": result.get("min_balance", 0)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to get balance"
                    }

        except Exception as e:
            logger.error(f"Balance query error: {e}")
            return {"success": False, "error": str(e)}

    async def get_application_state(self, app_id: int) -> Dict[str, Any]:
        """
        Get the global state of a smart contract application

        Returns:
            Application global state
        """
        try:
            async with self.session.get(
                f"{self.config.reader_endpoint}/api/v1/applications/{app_id}/state"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "state": result.get("global_state", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to get application state"
                    }

        except Exception as e:
            logger.error(f"Application state query error: {e}")
            return {"success": False, "error": str(e)}

    async def create_atomic_transaction_group(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create an atomic transaction group for multi-step operations

        Returns:
            Group transaction result
        """
        try:
            payload = {
                "action": "create_atomic_group",
                "params": {
                    "transactions": transactions
                }
            }

            async with self.session.post(
                f"{self.config.writer_endpoint}/api/v1/transactions/atomic-group",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "group_id": result.get("group_id"),
                        "transaction_ids": result.get("transaction_ids", [])
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Atomic group creation failed: {error_text}"
                    }

        except Exception as e:
            logger.error(f"Atomic group creation error: {e}")
            return {"success": False, "error": str(e)}

class MCPTransactionBuilder:
    """
    Builder class for creating complex blockchain transactions
    """

    @staticmethod
    def build_escrow_deployment(
        loan_id: str,
        borrower: str,
        lender: str,
        platform: str,
        collateral_amount: int,
        loan_amount: int,
        duration_days: int
    ) -> Dict[str, Any]:
        """Build transaction parameters for escrow deployment"""
        return {
            "type": "deploy_escrow",
            "params": {
                "loan_id": loan_id,
                "parties": {
                    "borrower": borrower,
                    "lender": lender,
                    "platform": platform
                },
                "terms": {
                    "collateral": collateral_amount,
                    "loan_amount": loan_amount,
                    "duration_days": duration_days
                },
                "global_schema": {
                    "num_uints": 8,
                    "num_bytes": 8
                },
                "local_schema": {
                    "num_uints": 2,
                    "num_bytes": 2
                }
            }
        }

    @staticmethod
    def build_multi_sig_transaction(
        signers: List[str],
        threshold: int,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a multi-signature transaction"""
        return {
            "type": "multi_sig",
            "signers": signers,
            "threshold": threshold,
            "transaction": transaction
        }