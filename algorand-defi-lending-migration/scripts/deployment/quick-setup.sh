#!/bin/bash
# Quick Setup Script for Algorand Lending Demo Testing
# This script helps verify the testing infrastructure setup

echo "🚀 Algorand Lending Demo - Quick Setup Verification"
echo "=================================================="

# Check if services are running
echo ""
echo "📡 Checking MCP Services..."
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✅ Remote MCP (Port 8002): Running"
else
    echo "❌ Remote MCP (Port 8002): Not accessible"
fi

if curl -s http://localhost:3001/health > /dev/null; then
    echo "✅ Actions MCP (Port 3001): Running"
else
    echo "❌ Actions MCP (Port 3001): Not accessible"
fi

# Check if wallet files exist
echo ""
echo "💰 Checking Test Wallets..."
if [ -f "test-wallets.json" ]; then
    echo "✅ Wallet addresses file: Found"
    LENDER=$(jq -r '.lender.address' test-wallets.json)
    BORROWER=$(jq -r '.borrower.address' test-wallets.json)
    LIQUIDITY=$(jq -r '.liquidity_provider.address' test-wallets.json)
    echo "   Lender:    $LENDER"
    echo "   Borrower:  $BORROWER"
    echo "   Liquidity: $LIQUIDITY"
else
    echo "❌ test-wallets.json not found. Run: python generate_test_wallets.py"
fi

if [ -f ".env.testnet" ]; then
    echo "✅ Private keys file: Found (secure)"
else
    echo "❌ .env.testnet not found. Run: python generate_test_wallets.py"
fi

# Check Python environment
echo ""
echo "🐍 Checking Python Environment..."
if [ -d "venv-adk" ]; then
    echo "✅ Virtual environment: Found"
    source venv-adk/bin/activate
    if python -c "import algosdk" 2>/dev/null; then
        echo "✅ Algorand SDK: Installed"
    else
        echo "❌ Algorand SDK: Not installed. Run: pip install py-algorand-sdk"
    fi
else
    echo "❌ Virtual environment not found"
fi

# Manual funding instructions
echo ""
echo "💸 MANUAL FUNDING REQUIRED"
echo "=========================="
echo "Before running full tests, fund these wallets at:"
echo "👉 https://bank.testnet.algorand.network/"
echo ""
if [ -f "test-wallets.json" ]; then
    echo "Addresses to fund (10 ALGO each):"
    echo "1. Lender:    $LENDER"
    echo "2. Borrower:  $BORROWER"
    echo "3. Liquidity: $LIQUIDITY"
fi

echo ""
echo "🧪 Running Integration Tests..."
echo "==============================="
echo "After funding wallets, run:"
echo "  source venv-adk/bin/activate"
echo "  python test-integration.py"
echo ""
echo "Expected: All 9 tests should pass"

echo ""
echo "📚 Documentation Available:"
echo "============================"
echo "  • MCP-API-REFERENCE.md - Complete API documentation"
echo "  • TESTING_INFRASTRUCTURE_REPORT.md - Detailed status report"
echo "  • http://localhost:8002/docs - Remote MCP Swagger UI"
echo "  • http://localhost:3001/docs - Actions MCP Swagger UI"

echo ""
echo "✨ Setup verification complete!"
echo "Next: Fund wallets → Run tests → Ready for lending demo!"