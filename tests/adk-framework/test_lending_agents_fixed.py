#!/usr/bin/env python3
"""
Fixed Test for Lending Agents with Gemini Integration
"""

import os
import sys
import asyncio
import json

# Add the correct path
sys.path.insert(0, '/home/mpo/algorand-showcase/apps/lending-platform/src')

def test_workflow_import():
    """Test importing the lending workflow using the new package structure"""
    print("💰 Testing Lending Workflow Import...")

    try:
        # Use the new package structure
        from core.lending.src import LendingWorkflow, MCPServiceConfig
        print("✅ Successfully imported from core.lending.src")

        # Test creating workflow
        mcp_config = MCPServiceConfig()
        workflow = LendingWorkflow(mcp_config)
        print("✅ Successfully created LendingWorkflow instance")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def main():
    """Quick workflow test"""
    print("🔧 Testing Fixed Import Paths...")
    print("=" * 40)

    success = test_workflow_import()

    if success:
        print("\n✅ Import paths fixed! Workflow can be imported.")
    else:
        print("\n❌ Import issues persist. Need to check module structure.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())