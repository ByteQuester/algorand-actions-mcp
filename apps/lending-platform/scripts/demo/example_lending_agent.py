"""
Example Lending Agent Implementation
Demonstrates both software-bug-assistant pattern and ADK native pattern
"""

from google.adk.agents import Agent
from tools import get_current_date, search_tool, get_lending_tools
from lending_tools_adk import get_lending_toolset_adk

# Example 1: Using software-bug-assistant pattern (direct toolbox tools)
def create_lending_agent_software_bug_assistant_pattern():
    """Create agent using the software-bug-assistant pattern"""

    # Note: lending_tools will be loaded from toolbox when service is running
    tools = [get_current_date, search_tool]

    # When service is ready, add: tools.extend(get_lending_tools())

    agent = Agent(
        model="gemini-2.5-flash",
        name="lending_agent_sba_pattern",
        instruction="""
        You are a lending platform specialist using the software-bug-assistant pattern.

        You can help with:
        - Creating loan requests
        - Managing lender information
        - Processing loans
        - Querying loan status

        Use the lending database tools to perform CRUD operations on:
        - loan_requests table
        - lenders table
        - loans table
        """,
        tools=tools
    )

    return agent

# Example 2: Using ADK native pattern (ToolboxToolset)
def create_lending_agent_adk_pattern():
    """Create agent using ADK native ToolboxToolset pattern"""

    agent = Agent(
        model="gemini-2.5-flash",
        name="lending_agent_adk_pattern",
        instruction="""
        You are a lending platform specialist using the ADK native pattern.

        You can help with:
        - Creating loan requests
        - Managing lender information
        - Processing loans
        - Querying loan status

        Use the lending database toolset to perform operations on the database.
        """,
        tools=[get_current_date, search_tool]  # + get_lending_toolset_adk() when service is ready
    )

    return agent

# Test function to verify agents can be created
def test_agent_creation():
    """Test that agents can be created (service connection will be tested separately)"""
    try:
        agent1 = create_lending_agent_software_bug_assistant_pattern()
        print("✓ Software-bug-assistant pattern agent created successfully")

        agent2 = create_lending_agent_adk_pattern()
        print("✓ ADK native pattern agent created successfully")

        return True
    except Exception as e:
        print(f"✗ Agent creation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing lending agent creation...")
    test_agent_creation()
    print("\nNote: Database connections will be tested when MCP Toolbox service is running.")