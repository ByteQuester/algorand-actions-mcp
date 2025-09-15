"""
Lending Platform Tools Configuration
Following the software-bug-assistant pattern for MCP database integration
"""

from datetime import datetime
import os

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from toolbox_core import ToolboxSyncClient

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ----- Example of a Function tool -----
def get_current_date() -> dict:
    """
    Get the current date in the format YYYY-MM-DD
    """
    return {"current_date": datetime.now().strftime("%Y-%m-%d")}


# ----- Example of a Built-in Tool -----
search_agent = Agent(
    model="gemini-2.5-flash",
    name="search_agent",
    instruction="""
    You're a specialist in Google Search for lending platform research.
    """,
    tools=[google_search],
)

search_tool = AgentTool(search_agent)

# ----- Lending Platform Database Tools (MCP Toolbox) -----
# Following the exact pattern from software-bug-assistant/tools.py lines 60-65
LENDING_TOOLBOX_URL = os.getenv("LENDING_TOOLBOX_URL", "http://127.0.0.1:5001")

# Initialize Toolbox client
toolbox = ToolboxSyncClient(LENDING_TOOLBOX_URL)

# Lazy loading function for lending tools (only loads when service is available)
def get_lending_tools():
    """Load lending tools from toolbox (call only when service is running)"""
    return toolbox.load_toolset("lending_toolset")

# Note: lending_tools will be loaded when get_lending_tools() is called
# This avoids connection errors when service is not running
lending_tools = None  # Will be populated when service is available

# Export all tools for use in agents
__all__ = [
    'get_current_date',
    'search_tool',
    'get_lending_tools',
    'lending_tools',
    'toolbox'
]