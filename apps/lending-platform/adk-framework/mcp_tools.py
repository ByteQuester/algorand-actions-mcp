# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
MCP Service integration tools for ADK agents
Connects to existing Algorand MCP services
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
import httpx


async def get_account_balance(address: str, endpoint: str = "http://localhost:8002") -> Dict[str, Any]:
    """
    Get account balance using Algorand Reader MCP service

    Args:
        address: Algorand address to query
        endpoint: MCP service endpoint

    Returns:
        Dict containing balance information
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{endpoint}/mcp/call",
                json={
                    "method": "get_account_balance",
                    "params": {"address": address}
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

    except Exception as e:
        return {
            "success": False,
            "error": f"MCP call failed: {str(e)}"
        }


async def get_account_transactions(address: str, limit: int = 10, endpoint: str = "http://localhost:8002") -> Dict[str, Any]:
    """
    Get account transaction history using Algorand Reader MCP service

    Args:
        address: Algorand address to query
        limit: Number of recent transactions to fetch
        endpoint: MCP service endpoint

    Returns:
        Dict containing transaction history
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{endpoint}/mcp/call",
                json={
                    "method": "get_account_transactions",
                    "params": {
                        "address": address,
                        "limit": limit
                    }
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

    except Exception as e:
        return {
            "success": False,
            "error": f"MCP call failed: {str(e)}"
        }


async def submit_transaction(transaction_data: Dict[str, Any], endpoint: str = "http://localhost:3001") -> Dict[str, Any]:
    """
    Submit transaction using Algorand Writer MCP service

    Args:
        transaction_data: Transaction data to submit
        endpoint: MCP service endpoint

    Returns:
        Dict containing transaction result
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{endpoint}/mcp/call",
                json={
                    "method": "submit_transaction",
                    "params": transaction_data
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

    except Exception as e:
        return {
            "success": False,
            "error": f"MCP call failed: {str(e)}"
        }


async def prepare_lending_transaction(
    borrower: str,
    lender: str,
    amount: int,
    collateral_amount: int,
    endpoint: str = "http://localhost:3001"
) -> Dict[str, Any]:
    """
    Prepare lending transaction group using Algorand Writer MCP service

    Args:
        borrower: Borrower address
        lender: Lender address
        amount: Loan amount in microAlgos
        collateral_amount: Collateral amount in microAlgos
        endpoint: MCP service endpoint

    Returns:
        Dict containing prepared transaction group
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{endpoint}/mcp/call",
                json={
                    "method": "prepare_lending_transaction",
                    "params": {
                        "borrower": borrower,
                        "lender": lender,
                        "amount": amount,
                        "collateral_amount": collateral_amount
                    }
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

    except Exception as e:
        return {
            "success": False,
            "error": f"MCP call failed: {str(e)}"
        }


async def check_mcp_services() -> Dict[str, Any]:
    """
    Check health of MCP services

    Returns:
        Dict containing service status
    """
    services = {
        "algorand_reader": "http://localhost:8002/health",
        "algorand_writer": "http://localhost:3001/health"
    }

    results = {}

    for service_name, health_url in services.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(health_url, timeout=5.0)
                results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response": response.text if response.status_code == 200 else f"HTTP {response.status_code}"
                }
        except Exception as e:
            results[service_name] = {
                "status": "unavailable",
                "error": str(e)
            }

    return results