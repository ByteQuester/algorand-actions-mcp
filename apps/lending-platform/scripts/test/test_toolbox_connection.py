"""
Test script to verify the lending toolbox connection
Following the software-bug-assistant pattern
"""

import os
from toolbox_core import ToolboxSyncClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_toolbox_connection():
    """Test the toolbox connection following software-bug-assistant pattern"""

    # Use the same pattern as software-bug-assistant
    LENDING_TOOLBOX_URL = os.getenv("LENDING_TOOLBOX_URL", "http://127.0.0.1:5001")

    print(f"Attempting to connect to toolbox at: {LENDING_TOOLBOX_URL}")

    try:
        # Initialize Toolbox client (exact pattern from software-bug-assistant)
        toolbox = ToolboxSyncClient(LENDING_TOOLBOX_URL)
        print("✓ Toolbox client initialized successfully")

        # Attempt to load toolset (exact pattern from software-bug-assistant)
        lending_tools = toolbox.load_toolset("lending_toolset")
        print("✓ Lending toolset loaded successfully")

        print(f"Available tools: {len(lending_tools) if lending_tools else 0}")

        return True

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print(f"Make sure the toolbox service is running on {LENDING_TOOLBOX_URL}")
        print("You may need to start the MCP Toolbox service first")
        return False

if __name__ == "__main__":
    test_toolbox_connection()