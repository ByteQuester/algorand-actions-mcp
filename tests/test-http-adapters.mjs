#!/usr/bin/env node
import { ActionsHttpAdapter } from './apps/blockchain/algorand-actions-mcp/src/http-adapter.js';
import { RemoteHttpAdapter } from './apps/blockchain/algorand-remote-mcp/src/http-adapter.js';

// Mock environment for testing
const mockActionsEnv = {
  ALGORAND_NETWORK: "testnet",
  ALGORAND_ALGOD: "https://testnet-api.algonode.cloud",
  READ_ONLY: "false"
};

const mockRemoteEnv = {
  ALGORAND_ALGOD: "https://mainnet-api.algonode.cloud", 
  ALGORAND_INDEXER: "https://mainnet-idx.algonode.cloud",
  READ_ONLY: "true"
};

async function testActionsAdapter() {
  console.log("Testing Actions HTTP Adapter...");
  
  const adapter = new ActionsHttpAdapter(mockActionsEnv);
  
  // Test tools list
  const toolsListRequest = new Request("http://localhost:8080/tools/list", {
    method: "GET"
  });
  
  try {
    const response = await adapter.handleRequest(toolsListRequest, mockActionsEnv);
    const data = await response.json();
    console.log("✅ Tools list:", data);
  } catch (error) {
    console.log("❌ Tools list error:", error.message);
  }
  
  // Test health
  const healthRequest = new Request("http://localhost:8080/health", {
    method: "GET"
  });
  
  try {
    const response = await adapter.handleRequest(healthRequest, mockActionsEnv);
    const data = await response.json();
    console.log("✅ Health check:", data);
  } catch (error) {
    console.log("❌ Health check error:", error.message);
  }
  
  // Test OpenAPI spec
  const openapiRequest = new Request("http://localhost:8080/openapi.json", {
    method: "GET"
  });
  
  try {
    const response = await adapter.handleRequest(openapiRequest, mockActionsEnv);
    const data = await response.json();
    console.log("✅ OpenAPI spec generated, title:", data.info.title);
  } catch (error) {
    console.log("❌ OpenAPI spec error:", error.message);
  }
}

async function testRemoteAdapter() {
  console.log("\nTesting Remote HTTP Adapter...");
  
  const adapter = new RemoteHttpAdapter(mockRemoteEnv);
  
  // Test tools list
  const toolsListRequest = new Request("http://localhost:8080/tools/list", {
    method: "GET"
  });
  
  try {
    const response = await adapter.handleRequest(toolsListRequest, mockRemoteEnv);
    const data = await response.json();
    console.log("✅ Tools list:", data);
  } catch (error) {
    console.log("❌ Tools list error:", error.message);
  }
  
  // Test health
  const healthRequest = new Request("http://localhost:8080/health", {
    method: "GET"
  });
  
  try {
    const response = await adapter.handleRequest(healthRequest, mockRemoteEnv);
    const data = await response.json();
    console.log("✅ Health check:", data);
  } catch (error) {
    console.log("❌ Health check error:", error.message);
  }
  
  // Test OpenAPI spec
  const openapiRequest = new Request("http://localhost:8080/openapi.json", {
    method: "GET"  
  });
  
  try {
    const response = await adapter.handleRequest(openapiRequest, mockRemoteEnv);
    const data = await response.json();
    console.log("✅ OpenAPI spec generated, title:", data.info.title);
  } catch (error) {
    console.log("❌ OpenAPI spec error:", error.message);
  }
}

async function main() {
  console.log("🧪 Testing HTTP Adapters for MCP Workers\n");
  
  await testActionsAdapter();
  await testRemoteAdapter();
  
  console.log("\n✨ Testing completed!");
}

main().catch(console.error);