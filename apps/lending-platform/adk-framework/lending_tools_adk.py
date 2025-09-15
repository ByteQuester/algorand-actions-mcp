"""
Lending Platform Tools - ADK Native Approach
Alternative to the software-bug-assistant pattern using ADK's ToolboxToolset
"""

import os
from google.adk.tools.toolbox_toolset import ToolboxToolset
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ADK Native approach using ToolboxToolset
LENDING_TOOLBOX_URL = os.getenv("LENDING_TOOLBOX_URL", "http://127.0.0.1:5001")

# Lazy loading function for ADK toolset
def get_lending_toolset_adk():
    """Create ADK-native toolbox toolset (call only when service is running)"""
    return ToolboxToolset(
        server_url=LENDING_TOOLBOX_URL,
        toolset_name="lending_toolset"
    )

# Note: lending_toolset_adk will be created when get_lending_toolset_adk() is called
lending_toolset_adk = None  # Will be populated when service is available

# Export for use in agents
__all__ = ['get_lending_toolset_adk', 'lending_toolset_adk']