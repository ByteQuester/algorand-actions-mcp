#!/usr/bin/env node

/**
 * Node.js HTTP server wrapper for Remote MCP Worker
 * Converts Cloudflare Worker to standard HTTP server
 */

// Add WebSocket polyfill for partyserver
import { WebSocket } from 'ws';
global.WebSocket = WebSocket;

// Register cloudflare: polyfill loader
import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
register(pathToFileURL('./cloudflare-polyfill-loader.mjs'), import.meta.url);

import { createServer } from 'http';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Import the worker
let worker;
try {
  const workerModule = await import('./dist/index.js');
  worker = workerModule.default;
} catch (error) {
  console.error('Failed to load worker:', error);
  process.exit(1);
}

const PORT = process.env.PORT || 8080;

// Mock Cloudflare Worker environment with extended properties
const mockEnv = {
  ALGORAND_NETWORK: process.env.ALGORAND_NETWORK || 'mainnet',
  ALGORAND_ALGOD: process.env.ALGORAND_ALGOD || 'https://mainnet-api.algonode.cloud',
  ALGORAND_INDEXER: process.env.ALGORAND_INDEXER || 'https://mainnet-idx.algonode.cloud',
  ALGORAND_TOKEN: process.env.ALGORAND_TOKEN || '',
  READ_ONLY: process.env.READ_ONLY || 'true',
  
  // OAuth/Vault settings (typically missing in containerized deployments, triggering read-only mode)
  HCV_WORKER: process.env.HCV_WORKER,
  HCV_WORKER_URL: process.env.HCV_WORKER_URL,
  VAULT_ENTITIES: process.env.VAULT_ENTITIES,
  VAULT_OIDC_ACCESSOR: process.env.VAULT_OIDC_ACCESSOR,
  GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID,
  GOOGLE_CLIENT_SECRET: process.env.GOOGLE_CLIENT_SECRET,
  COOKIE_ENCRYPTION_KEY: process.env.COOKIE_ENCRYPTION_KEY,
  
  ...process.env
};

// Mock execution context
const mockCtx = {
  waitUntil: (promise) => promise,
  passThroughOnException: () => {}
};

const server = createServer(async (req, res) => {
  try {
    // Build full URL
    const protocol = req.headers['x-forwarded-proto'] || 'http';
    const host = req.headers.host || `localhost:${PORT}`;
    const url = `${protocol}://${host}${req.url}`;

    // Collect request body for POST requests
    let body = '';
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      for await (const chunk of req) {
        body += chunk;
      }
    }

    // Create Request object
    const request = new Request(url, {
      method: req.method,
      headers: req.headers,
      body: body || undefined,
    });

    // Call worker
    const response = await worker.fetch(request, mockEnv, mockCtx);

    // Set response headers
    response.headers.forEach((value, key) => {
      res.setHeader(key, value);
    });

    // Set status and send response
    res.statusCode = response.status;
    
    if (response.body) {
      const reader = response.body.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        res.write(value);
      }
    }
    
    res.end();
  } catch (error) {
    console.error('Request error:', error);
    res.statusCode = 500;
    res.setHeader('content-type', 'application/json');
    res.end(JSON.stringify({ error: 'Internal Server Error' }));
  }
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('Received SIGTERM, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('Received SIGINT, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

// Determine if running in read-only mode
const isReadOnly = mockEnv.READ_ONLY === 'true' || !mockEnv.HCV_WORKER;

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Remote MCP Worker listening on port ${PORT}`);
  console.log(`📊 Health: http://localhost:${PORT}/health`);
  console.log(`📚 Docs: http://localhost:${PORT}/docs`);
  console.log(`🌐 Network: ${mockEnv.ALGORAND_NETWORK}`);
  console.log(`👀 Mode: ${isReadOnly ? 'Read-Only' : 'Full OAuth'}`);
  console.log(`📡 Algod: ${mockEnv.ALGORAND_ALGOD}`);
  console.log(`📊 Indexer: ${mockEnv.ALGORAND_INDEXER}`);
});