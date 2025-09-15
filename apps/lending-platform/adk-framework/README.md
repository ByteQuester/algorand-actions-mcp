# ADK Framework System (Agent 8)

**Professional agent development framework for enterprise AI lending**

## Overview

This system uses Google's Agent Development Kit (ADK) for:
- Multi-agent coordination architecture
- Schema-driven agent definitions
- Enterprise-grade workflow management
- Extensible and maintainable design

## Architecture

```
[Coordination Agent] → [Liquidity Agent] → [MCP Services] → [Blockchain]
         ↓                    ↓
[Negotiation Agent]    [Execution Agent]
```

## Agent Modules

- **`coordination/`** - Main workflow orchestrator
- **`liquidity/`** - Liquidity pool management
- **`negotiation/`** - Loan terms negotiation
- **`execution/`** - Transaction execution
- **`schemas-v1/`** - Original agent schemas (Agent 6)

## Key Files

- **`manifest.json`** - ADK configuration
- **`adk_web_config.json`** - Web interface configuration
- **`schemas/`** - Agent and tool definitions
- **`real_mcp_integration_v2.py`** - Blockchain integration

## Quick Start

```bash
# Install ADK dependencies
pip install -r requirements.txt

# Run ADK system
python3 demo_adk_agents.py
```

## Enterprise Features

✅ **Multi-Agent Coordination** - Professional agent orchestration
✅ **Schema-Driven Development** - Structured agent definitions
✅ **Extensible Architecture** - Easy to add new agent types
✅ **Production Monitoring** - Built-in observability
✅ **Enterprise Deployment** - Docker and Kubernetes ready

## Documentation

- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Detailed implementation guide
- **[Production Deployment](PRODUCTION_DEPLOYMENT_GUIDE.md)** - Production setup instructions
- **[Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions
- **[MCP API Documentation](MCP_API_DOCUMENTATION.md)** - MCP service integration

## Status: Production Ready 🏗️

### Recent Fixes (2025-09-15)
✅ **Agent Duplication Error** - Fixed duplicate parent assignment in coordination/agent.py
✅ **Type Annotation Issues** - Resolved 17 type annotation errors across 4 files
✅ **Server Stability** - Clean startup without critical errors