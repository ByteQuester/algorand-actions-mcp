# Lending Platform Database Setup

## Overview
This implementation follows the **exact pattern** used by `software-bug-assistant` for MCP Toolbox integration.

## Research Findings

### Software-Bug-Assistant Pattern Analysis
From `/home/mpo/algorand-showcase/apps/core/adk-samples/python/agents/software-bug-assistant/software_bug_assistant/tools/tools.py`:

**Key Pattern (Lines 60-65):**
```python
# ----- Example of a Google Cloud Tool (MCP Toolbox for Databases) -----
TOOLBOX_URL = os.getenv("MCP_TOOLBOX_URL", "http://127.0.0.1:5000")

# Initialize Toolbox client
toolbox = ToolboxSyncClient(TOOLBOX_URL)
# Load all the tools from toolset
toolbox_tools = toolbox.load_toolset("tickets_toolset")
```

**Dependencies Used:**
- `toolbox-core==0.1.0`
- `google-adk==1.3.0` (already installed)
- `python-dotenv==1.1.0`

## Implementation

### 1. Installed Components ✅
```bash
pip install toolbox-core==0.1.0
```

### 2. Created Files ✅

#### Database Schema
- **File**: `/home/mpo/algorand-showcase/apps/lending-platform/config/development/lending_database.sql`
- **Content**: Complete schema for loan_requests, lenders, and loans tables

#### MCP Toolset Configuration
- **File**: `/home/mpo/algorand-showcase/apps/lending-platform/src/agents/lending_toolset.py`
- **Pattern**: Exact copy of software-bug-assistant pattern with lending-specific naming
```python
LENDING_TOOLBOX_URL = os.getenv("LENDING_TOOLBOX_URL", "http://127.0.0.1:5001")
toolbox = ToolboxSyncClient(LENDING_TOOLBOX_URL)
lending_tools = toolbox.load_toolset("lending_toolset")
```

#### Main Tools Configuration
- **File**: `/home/mpo/algorand-showcase/apps/lending-platform/src/agents/tools.py`
- **Pattern**: Following software-bug-assistant structure exactly

#### Connection Test
- **File**: `/home/mpo/algorand-showcase/apps/lending-platform/scripts/test/test_toolbox_connection.py`
- **Status**: ✅ Client initializes correctly, awaiting service

## Next Steps

### To Complete the Setup:

1. **Start MCP Toolbox Service**
   - The service needs to run on `http://127.0.0.1:5001`
   - Configure it to serve the `lending_toolset`
   - Load the database schema from `lending_database.sql`

2. **Environment Variables**
   ```bash
   export LENDING_TOOLBOX_URL="http://127.0.0.1:5001"
   ```

3. **Test Connection**
   ```bash
   python test_toolbox_connection.py
   ```

## Usage Patterns

### Option 1: Software-Bug-Assistant Pattern (Direct ToolboxSyncClient)
Once the service is running, use in your agents exactly like software-bug-assistant:

```python
from tools import lending_tools

# lending_tools will contain all database operations
# for loan_requests, lenders, and loans tables
```

### Option 2: ADK Native Pattern (ToolboxToolset)
Alternative approach using ADK's native ToolboxToolset class:

```python
from lending_tools_adk import lending_toolset_adk

# Use in agent
agent = Agent(
    model="gemini-2.5-flash",
    name="lending_agent",
    tools=[lending_toolset_adk],
    instruction="You are a lending platform specialist..."
)
```

## Service Status
- ✅ Pattern researched and documented
- ✅ Dependencies installed (toolbox-core==0.1.0)
- ✅ Database schema created
- ✅ MCP toolset configuration implemented
- ✅ Connection test confirms client works
- ⏳ **Need to start MCP Toolbox service on port 5001**

The implementation exactly follows the software-bug-assistant pattern and is ready for the MCP Toolbox service to be started.