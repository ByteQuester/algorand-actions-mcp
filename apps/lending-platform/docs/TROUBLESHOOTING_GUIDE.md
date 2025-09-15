# ADK Framework Troubleshooting Guide

## Overview

This guide documents common issues and solutions for the ADK Framework lending platform, specifically covering critical fixes applied on 2025-09-15 to resolve agent duplication and type annotation errors.

## Critical Issues Fixed

### Issue 1: Agent Duplication Error ✅ RESOLVED

**Error Symptoms:**
```
Agent `algorand_lending_liquidity_agent` already has a parent agent, current parent: `algorand_lending_coordinator`, trying to add: `algorand_lending_coordinator`
```

**Root Cause:**
The `create_lending_coordinator()` function in `coordination/agent.py` was configuring agents in two conflicting ways:
1. Sub-agents properly declared in the `sub_agents` parameter (lines 83-87)
2. Same agents redundantly wrapped in `AgentTool` instances in the `tools` list (lines 93-95)

**Solution Applied:**
- **File:** `/home/mpo/algorand-showcase/apps/lending-platform/adk-framework/coordination/agent.py`
- **Fix:** Removed redundant `AgentTool` wrappers from tools list (lines 93-95)
- **Fix:** Removed unnecessary `AgentTool` import (line 15)
- **Kept:** Proper sub-agent configuration in `sub_agents` parameter

**Code Changes:**
```python
# BEFORE (causing duplication):
tools=[
    FunctionTool(check_mcp_service_health),
    FunctionTool(get_borrower_data),
    FunctionTool(get_lender_data),
    FunctionTool(coordinate_lending_workflow),
    AgentTool(agent=liquidity_agent),      # ❌ REDUNDANT
    AgentTool(agent=negotiation_agent),    # ❌ REDUNDANT
    AgentTool(agent=execution_agent),      # ❌ REDUNDANT
]

# AFTER (fixed):
tools=[
    FunctionTool(check_mcp_service_health),
    FunctionTool(get_borrower_data),
    FunctionTool(get_lender_data),
    FunctionTool(coordinate_lending_workflow),
    # AgentTool wrappers removed - agents managed via sub_agents parameter
]
```

### Issue 2: Type Annotation Errors ✅ RESOLVED

**Error Symptoms:**
```
ERROR: Default value None of parameter loan_id: str = None of function prepare_transaction_group is not compatible with the parameter annotation <class 'str'>.
```

**Root Cause:**
Multiple files had invalid Python type annotations where parameters were typed as strict types (`str`, `float`, `int`) but had `None` default values.

**Files Fixed:**

1. **`execution/tools.py`** (3 fixes):
   - Line 23: `loan_id: str = None` → `loan_id: Optional[str] = None`
   - Line 151: `borrower_balance_algos: float = None` → `borrower_balance_algos: Optional[float] = None`
   - Line 152: `lender_balance_algos: float = None` → `lender_balance_algos: Optional[float] = None`

2. **`real_mcp_integration_v2.py`** (7 fixes):
   - Line 55: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`
   - Line 221: `note: str = None` → `note: Optional[str] = None`
   - Line 296: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`
   - Line 302: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`
   - Line 309: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`
   - Line 316: `note: str = None, config: MCPServiceConfig = None` → `note: Optional[str] = None, config: Optional[MCPServiceConfig] = None`
   - Line 322: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`

3. **`mock_adk.py`** (2 fixes):
   - Line 24: `tools: List = None` → `tools: Optional[List] = None`
   - Line 25: `sub_agents: List = None` → `sub_agents: Optional[List] = None`

4. **`real_mcp_integration.py`** (5 fixes):
   - Line 66: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`
   - Line 537: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`
   - Line 543: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`
   - Line 549: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`
   - Line 555: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`
   - Line 561: `config: MCPServiceConfig = None` → `config: Optional[MCPServiceConfig] = None`

**Total Fixed:** 17 type annotation errors across 4 files

## Server Restart Procedure

### When to Restart
After making the above fixes, a clean server restart is required to:
- Load updated Python code without type annotation errors
- Clear agent registration cache to prevent duplication
- Ensure all fixes are properly applied

### Restart Steps

1. **Stop Current Server:**
   ```bash
   # Find and kill ADK server processes
   ps aux | grep adk
   kill -TERM <process_id>

   # Or if needed, force kill
   pkill -f "adk web"
   ```

2. **Verify Ports Freed:**
   ```bash
   # Check that port 8091 is free
   lsof -i :8091
   ```

3. **Restart Server:**
   ```bash
   cd /home/mpo/algorand-showcase
   ./venv-adk/bin/adk web apps/lending-platform --port 8091 --host 0.0.0.0
   ```

4. **Verify Clean Startup:**
   - Watch for successful startup message
   - No agent duplication errors
   - No type annotation errors
   - API endpoints responding

### Expected Startup Logs
```
+-----------------------------------------------------------------------------+
| ADK Web Server started                                                      |
|                                                                             |
| For local testing, access at http://0.0.0.0:8091.                         |
+-----------------------------------------------------------------------------+

INFO:     Started server process [406913]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8091 (Press CTRL+C to quit)
```

## Validation Checklist

After applying fixes and restarting, verify:

### ✅ Agent Functionality
- [ ] `algorand_lending_liquidity_agent` loads without duplication errors
- [ ] `algorand_lending_negotiation_agent` tools execute without type errors
- [ ] `algorand_lending_execution_agent` transaction preparation works
- [ ] Coordinator can call all sub-agents successfully

### ✅ Tool Execution
- [ ] `calculate_interest_rate` returns valid rates
- [ ] `assess_loan_risk` produces risk scores
- [ ] `prepare_transaction_group` creates transaction groups
- [ ] `find_available_lenders` discovers lenders

### ✅ End-to-End Workflow
- [ ] Complete lending workflow executes without errors
- [ ] Coordinator → sub-agent communication works
- [ ] MCP service integration remains functional
- [ ] No Python import or syntax errors

## Common Error Patterns

### Type Annotation Issues
**Pattern:** `param: Type = None`
**Fix:** `param: Optional[Type] = None`
**Import Required:** `from typing import Optional`

### Agent Duplication Issues
**Pattern:** Same agent in both `sub_agents` and `tools` as `AgentTool`
**Fix:** Use `sub_agents` parameter only, remove `AgentTool` wrappers

### Import Errors
**Pattern:** Missing or incorrect imports after fixes
**Fix:** Ensure `from typing import Optional` is present in all modified files

## Prevention

### Code Review Checklist
- [ ] All parameters with `None` defaults use `Optional[Type]`
- [ ] No agents configured in both `sub_agents` and `tools` lists
- [ ] Required imports present for all type annotations
- [ ] Python syntax validation passed (`python3 -m py_compile`)

### Testing Protocol
- [ ] Run syntax validation on all modified files
- [ ] Test agent imports individually
- [ ] Verify tool execution with sample data
- [ ] Test complete workflow end-to-end

## Support

For additional support:
- Check server logs for specific error messages
- Verify MCP services are running (ports 8002, 3001)
- Ensure Python environment has all required dependencies
- Review this troubleshooting guide for similar issues

## Change History

- **2025-09-15**: Fixed agent duplication and type annotation errors
- **Applied by**: Automated agent delegation system
- **Status**: ✅ Production Ready