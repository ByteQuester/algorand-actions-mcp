# ADK Lending Agents

Google Agent Development Kit (ADK) implementation of Algorand lending agents, running in parallel to the existing system.

## Overview

This directory contains ADK-based versions of the lending agents, providing an alternative implementation using Google's Agent Development Kit and Gemini AI. These agents work alongside the existing system without replacing it.

## Architecture

### Agent Structure
```
adk-agents/
├── coordination/          # Master coordinator agent
│   ├── agent.py          # Main coordination agent
│   └── tools.py          # Coordination tools
├── negotiation/          # Loan negotiation agent
│   ├── agent.py          # Negotiation agent
│   └── tools.py          # Negotiation tools
├── liquidity/            # Liquidity discovery agent
│   ├── agent.py          # Liquidity agent
│   └── tools.py          # Liquidity tools
├── execution/            # Transaction execution agent
│   ├── agent.py          # Execution agent
│   └── tools.py          # Execution tools
└── mcp_tools.py          # MCP service integration
```

### Key Features

1. **Coordination Agent** (`lending_coordinator`)
   - Orchestrates the complete lending workflow
   - Manages sub-agents and coordinates their interactions
   - Integrates with MCP services for blockchain operations
   - Uses Gemini-2.5-pro for sophisticated reasoning

2. **Negotiation Agent** (`negotiation_agent`)
   - Analyzes loan requests and assesses risk
   - Calculates competitive interest rates
   - Negotiates terms using AI-powered decision making
   - Generates counter-proposals based on risk assessment

3. **Liquidity Agent** (`liquidity_agent`)
   - Discovers available lenders in the ecosystem
   - Assesses borrower creditworthiness
   - Matches liquidity requirements optimally
   - Calculates comprehensive liquidity costs

4. **Execution Agent** (`execution_agent`)
   - Prepares atomic transaction groups
   - Validates execution requirements
   - Estimates transaction costs and timing
   - Creates smart contracts for complex lending

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export GOOGLE_API_KEY="your_gemini_api_key"
export GOOGLE_GENAI_USE_VERTEXAI="FALSE"
```

## Usage

### Running Tests

Test the complete ADK system:
```bash
python test_adk_agents.py
```

### Using Individual Agents

```python
from coordination import lending_coordinator
from negotiation import negotiation_agent
from liquidity import liquidity_agent
from execution import execution_agent

# Use the coordination agent for complete workflows
result = lending_coordinator.process({
    "loan_request": {
        "borrower_address": "ALGO_ADDRESS_HERE",
        "amount_algos": 100.0,
        "duration_days": 30,
        "max_interest_rate": 8.5
    }
})
```

### MCP Service Integration

The agents integrate with existing MCP services:

```python
from mcp_tools import get_account_balance, submit_transaction

# Get account data
balance = await get_account_balance("ALGO_ADDRESS")

# Submit transactions
result = await submit_transaction(transaction_data)
```

## Agent Capabilities

### Negotiation Agent Tools
- `calculate_interest_rate()` - Risk-based rate calculation
- `calculate_collateral_requirement()` - Collateral assessment
- `assess_loan_risk()` - Comprehensive risk analysis
- `generate_counter_proposal()` - AI-powered negotiation

### Liquidity Agent Tools
- `find_available_lenders()` - Lender discovery
- `assess_borrower_creditworthiness()` - Credit evaluation
- `match_liquidity_requirements()` - Optimal matching
- `calculate_liquidity_costs()` - Cost analysis

### Execution Agent Tools
- `prepare_transaction_group()` - Atomic transaction preparation
- `validate_execution_requirements()` - Pre-execution validation
- `estimate_transaction_costs()` - Cost estimation
- `create_lending_contract()` - Smart contract creation

### Coordination Agent Tools
- `check_mcp_service_health()` - Service monitoring
- `get_borrower_data()` - Borrower data aggregation
- `get_lender_data()` - Lender data collection
- `coordinate_lending_workflow()` - Workflow orchestration

## Integration with Existing System

These ADK agents run **parallel** to the existing system:

- **Existing System**: `packages/lending-core/src/agents.py`
- **ADK System**: `apps/lending-platform/adk-agents/`
- **MCP Services**: Shared between both systems (ports 8002, 3001)
- **Testing**: Both approaches can be tested independently

## Workflow Example

1. **Request Processing**: Coordination agent receives loan request
2. **Data Gathering**: Retrieves borrower/lender data via MCP services
3. **Liquidity Discovery**: Liquidity agent finds suitable lenders
4. **Term Negotiation**: Negotiation agent uses Gemini AI to optimize terms
5. **Execution Planning**: Execution agent prepares blockchain transactions
6. **Coordination**: Master agent orchestrates the complete process

## Configuration

### Model Configuration
Agents use different Gemini models based on complexity:
- **Coordination**: `gemini-2.5-pro` (complex reasoning)
- **Sub-agents**: `gemini-2.5-flash` (fast processing)

### MCP Endpoints
- **Reader Service**: `http://localhost:8002`
- **Writer Service**: `http://localhost:3001`

## Comparison with Existing System

| Feature | Existing System | ADK System |
|---------|----------------|------------|
| Architecture | Pure Python classes | Google ADK agents |
| AI Integration | Manual Gemini calls | Native ADK integration |
| Workflow | Programmatic | AI-driven coordination |
| Scalability | Manual scaling | ADK managed |
| Debugging | Standard Python | ADK debugging tools |
| Deployment | Custom | ADK deployment |

## Benefits of ADK Approach

1. **AI-Native**: Built-in Gemini integration with optimized prompting
2. **Scalability**: ADK handles agent lifecycle and scaling
3. **Reliability**: Built-in error handling and retry logic
4. **Observability**: Native monitoring and debugging
5. **Flexibility**: Easy to add new capabilities and sub-agents
6. **Consistency**: Standardized agent patterns and tools

## Testing

The test suite validates:
- ✅ Agent imports and creation
- ✅ Tool function execution
- ✅ MCP service integration
- ✅ Complete workflow coordination
- ✅ Error handling and recovery

Run tests:
```bash
python test_adk_agents.py
```

## Development

### Adding New Tools
```python
def new_lending_tool(param1: str, param2: int) -> Dict[str, Any]:
    """New tool for lending operations"""
    # Implementation
    return {"result": "success"}

# Add to agent
agent = Agent(
    tools=[FunctionTool(new_lending_tool)]
)
```

### Creating Sub-Agents
```python
sub_agent = Agent(
    name="specialized_agent",
    model="gemini-2.5-flash",
    description="Specialized agent for specific tasks",
    instruction="Agent instructions...",
    tools=[FunctionTool(tool_function)]
)

# Use in main agent
main_agent = Agent(
    sub_agents=[sub_agent],
    tools=[AgentTool(agent=sub_agent)]
)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `google-adk` is installed
2. **API Key**: Set `GOOGLE_API_KEY` environment variable
3. **MCP Services**: Start services on ports 8002 and 3001
4. **Dependencies**: Install all requirements from `requirements.txt`

### Debug Mode
Set environment variable for verbose logging:
```bash
export ADK_DEBUG=1
```

## Next Steps

1. **Deploy MCP Services**: Ensure services are running
2. **Test with Real Data**: Use actual Algorand addresses
3. **Production Deployment**: Deploy using ADK deployment tools
4. **Monitoring**: Set up ADK monitoring and alerting
5. **Scaling**: Configure ADK autoscaling as needed

## Contributing

When extending the ADK agents:
1. Follow ADK patterns and conventions
2. Add comprehensive tools docstrings
3. Update test suite for new functionality
4. Maintain compatibility with existing MCP services
5. Document new capabilities in this README