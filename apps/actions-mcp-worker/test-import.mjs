#!/usr/bin/env node

// Test importing agents/mcp to see what fails
try {
  console.log('Importing agents/mcp...');
  const agentsMcp = await import('agents/mcp');
  console.log('Success! Imported:', Object.keys(agentsMcp));
} catch (error) {
  console.error('Failed to import agents/mcp:', error.message);
  console.error('Error code:', error.code);
}