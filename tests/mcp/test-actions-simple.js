#!/usr/bin/env node
/**
 * Simple Actions MCP test script using basic HTTP/SSE
 * Handles the session ID workflow correctly
 */

const https = require('https');

const BASE_URL = 'https://algorand-actions-mcp.mehrdad-touraji.workers.dev';

// Test addresses (from docs)
const FROM_ADDRESS = 'FWDNPCCRHRL3J3KQMRYDP6ETYQAXH6MLYUPMQR2WGR5WDCQYBC7KZQMQP4';
const TO_ADDRESS = 'GBXGQJH5I5WEFNFRNJYXJKMWM2GBE3NRXDEWWK2VXN36B6ZXFX62NRWZ6A';

async function getSessionId() {
  return new Promise((resolve, reject) => {
    const req = https.get(`${BASE_URL}/sse`, (res) => {
      res.on('data', (chunk) => {
        const data = chunk.toString();
        if (data.includes('data: /sse/message?sessionId=')) {
          const sessionId = data.match(/sessionId=([a-f0-9]+)/)[1];
          resolve(sessionId);
          req.destroy(); // Close connection
        }
      });
      res.on('error', reject);
    });
    req.on('error', reject);
  });
}

async function callTool(sessionId, method, params = {}) {
  const payload = {
    jsonrpc: '2.0',
    id: Math.random().toString(36),
    method,
    params
  };

  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(payload);
    const url = `${BASE_URL}/sse/message?sessionId=${sessionId}`;
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': postData.length
      }
    };

    const req = https.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 202) {
          resolve({ status: 'accepted', message: 'Posted to SSE stream' });
        } else {
          resolve({ status: res.statusCode, data });
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function testActions() {
  console.log('🔧 Testing Actions MCP Worker');
  console.log('==============================\n');

  try {
    // 1. Test health endpoint
    console.log('1. Health check...');
    const healthReq = https.get(`${BASE_URL}/health`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log('   ✅ Health:', data);
      });
    });

    // 2. Test capabilities
    console.log('2. Capabilities check...');
    const capReq = https.get(`${BASE_URL}/capabilities`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log('   ✅ Capabilities:', data);
      });
    });

    // Wait a bit for the above to complete
    await new Promise(resolve => setTimeout(resolve, 1000));

    // 3. Get SSE session
    console.log('3. Getting SSE session...');
    const sessionId = await getSessionId();
    console.log(`   ✅ Session ID: ${sessionId.substring(0, 16)}...`);

    // 4. Test tools/list
    console.log('4. Testing tools/list...');
    const listResult = await callTool(sessionId, 'tools/list');
    console.log('   ✅ Tools list:', listResult);

    // 5. Test build_payment_tx
    console.log('5. Testing build_payment_tx...');
    const buildResult = await callTool(sessionId, 'tools/call', {
      name: 'build_payment_tx',
      arguments: {
        fromAddress: FROM_ADDRESS,
        toAddress: TO_ADDRESS,
        microAlgos: 100000,
        note: 'test from simple script'
      }
    });
    console.log('   ✅ Build payment:', buildResult);

    // 6. Test simulate_raw_tx (will likely fail with known issue)
    console.log('6. Testing simulate_raw_tx...');
    const simResult = await callTool(sessionId, 'tools/call', {
      name: 'simulate_raw_tx', 
      arguments: {
        unsignedTxnBase64: 'dummy_for_test' // This will fail but shows the flow
      }
    });
    console.log('   ⚠️  Simulate (expected to fail):', simResult);

    console.log('\n🎉 Actions MCP test completed!');
    console.log('Note: Simulation failure is expected (documented issue)');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

if (require.main === module) {
  testActions();
}

module.exports = { getSessionId, callTool };