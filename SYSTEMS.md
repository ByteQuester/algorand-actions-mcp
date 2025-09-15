# 🎯 Production Systems Overview

The Algorand Showcase contains **two working AI lending systems**, each with different architectures and capabilities.

## 🚀 System 1: Direct Integration (Agent 5)
**Location:** `apps/lending-platform/direct-integration/`
**Approach:** Direct Gemini + MCP integration with custom workflow
**Status:** ✅ Production Ready

### Features
- Direct Google Gemini 1.5 Flash integration
- Custom MCP blockchain connectivity
- Real-time risk assessment with fallback mechanisms
- Simple, streamlined architecture
- Fast loan processing (4.8s end-to-end)

### Key Files
- `real_mcp_integration_v2.py` - MCP blockchain client
- Agent coordination and workflow scripts
- Test suite with real blockchain verification

## 🏗️ System 2: ADK Framework (Agent 8)
**Location:** `apps/lending-platform/src/agents/`
**Approach:** Google ADK (Agent Development Kit) professional framework
**Status:** ✅ Production Ready

### Features
- Professional ADK agent architecture
- Multi-agent coordination (liquidity, negotiation, execution)
- Schema-driven agent definitions
- Enterprise-grade workflow management
- Extensible and maintainable design

### Key Files
- `coordination/`, `liquidity/`, `negotiation/`, `execution/` agent modules
- `manifest.json` - ADK configuration
- `schemas/` - Agent and tool definitions
- Professional deployment configuration

## 🔗 Shared Infrastructure

### MCP Services
- **Reader Service (Port 8002):** Account info, transaction history
- **Writer Service (Port 3001):** Transaction building, simulation, submission

### Core Libraries
- **`packages/lending-core/`** - Shared business logic
- **`packages/lending-api/`** - API components
- **`packages/mcp-core/`** - MCP protocol helpers

### Test Infrastructure
- Funded testnet wallets (10 ALGO each)
- Comprehensive test suites
- Real blockchain connectivity verification

## 🎯 Choosing a System

**Use Direct Integration (System 1) if:**
- You want a simple, straightforward implementation
- You need quick deployment and testing
- You prefer minimal dependencies

**Use ADK Framework (System 2) if:**
- You're building for enterprise production
- You need extensible, maintainable architecture
- You want professional agent coordination
- You plan to scale with multiple agent types

Both systems use the same MCP blockchain services and can run simultaneously.