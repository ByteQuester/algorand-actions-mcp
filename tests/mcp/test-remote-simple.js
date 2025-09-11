#!/usr/bin/env node
/**
 * Simple Remote MCP test script using basic HTTP
 * Tests read-only functionality
 */

const https = require('https');

const BASE_URL = 'https://algorand-remote-mcp.mehrdad-touraji.workers.dev';

async function testRemote() {
  console.log('🌐 Testing Remote MCP Worker');
  console.log('=============================\n');

  try {
    // 1. Test health endpoint
    console.log('1. Health check...');
    const healthReq = https.get(`${BASE_URL}/health`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log('   ✅ Health:', data);
        
        const health = JSON.parse(data);
        if (health.mode === 'READ_ONLY') {
          console.log('   ✅ Confirmed: Worker in READ_ONLY mode');
        } else {
          console.log('   ⚠️  Unexpected mode:', health.mode);
        }
      });
    });

    // 2. Test SSE endpoint accessibility  
    console.log('2. SSE endpoint check...');
    const sseReq = https.get(`${BASE_URL}/sse`, (res) => {
      console.log(`   ✅ SSE Status: ${res.statusCode}`);
      console.log(`   ✅ Content-Type: ${res.headers['content-type']}`);
      
      if (res.statusCode === 200 && res.headers['content-type']?.includes('text/event-stream')) {
        console.log('   ✅ SSE endpoint is active');
      }
      
      res.on('data', (chunk) => {
        const data = chunk.toString();
        if (data.includes('sessionId=')) {
          console.log('   ✅ SSE providing session IDs');
          console.log(`   📡 Sample data: ${data.substring(0, 100)}...`);
        }
      });
      
      // Close after getting some data
      setTimeout(() => {
        sseReq.destroy();
      }, 2000);
    });

    // 3. Test capabilities endpoint (might not exist)
    console.log('3. Capabilities check...');
    const capReq = https.get(`${BASE_URL}/capabilities`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('   ✅ Capabilities:', data);
        } else {
          console.log('   ℹ️  No capabilities endpoint (expected for remote worker)');
        }
      });
    });

    // 4. Test with MCP client approach (if available)
    console.log('4. MCP protocol test...');
    console.log('   ℹ️  For full MCP testing, use:');
    console.log('   📝 npx mcp-remote https://algorand-remote-mcp.mehrdad-touraji.workers.dev/sse');
    console.log('   📝 Then try: tools, call api_nfd_get_nfd {"name":"emg110.algo","view":"brief"}');

    console.log('\n🎉 Remote MCP basic test completed!');
    console.log('Note: Full tool testing requires proper MCP client');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

if (require.main === module) {
  testRemote();
}

module.exports = { testRemote };