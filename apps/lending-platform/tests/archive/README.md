# Archived Test Files

This directory contains historical test files that are kept for reference purposes only. These tests are not actively maintained and may not work with the current codebase.

## Contents

### Workflow Tests
- `test_complete_workflow.py` - Original comprehensive workflow test (v1)
- `test_complete_workflow_v2.py` - Updated comprehensive workflow test (v2)

### MCP Integration Tests
- `test_real_mcp.py` - Original MCP integration test
- `test_real_mcp_v2.py` - Updated MCP integration test (v2)

## Purpose

These files are kept for:
- Reference patterns and test approaches
- Historical context of the testing evolution
- Code patterns that might be useful for future development

## Warning

⚠️ **These tests are not guaranteed to work with the current codebase.** They use outdated import paths and may reference removed components.

For current, working tests, see:
- `../integration/` - Active integration tests
- `../unit/` - Active unit tests

## Migration

If you need to reference these patterns:
1. Check the current equivalent test in `../integration/`
2. Update import paths to match current structure
3. Verify dependencies and configurations are current