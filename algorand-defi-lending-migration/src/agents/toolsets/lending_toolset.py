"""
Lending Platform MCP Toolset Configuration
Following the software-bug-assistant pattern for database integration
"""

import os
from toolbox_core import ToolboxSyncClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ----- Example of a Google Cloud Tool (MCP Toolbox for Databases) -----
# Following the exact pattern from software-bug-assistant
LENDING_TOOLBOX_URL = os.getenv("LENDING_TOOLBOX_URL", "http://127.0.0.1:5001")

# Initialize Toolbox client (same pattern as software-bug-assistant)
toolbox = ToolboxSyncClient(LENDING_TOOLBOX_URL)

# Load all the tools from lending toolset
lending_tools = toolbox.load_toolset("lending_toolset")