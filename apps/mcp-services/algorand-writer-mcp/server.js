#!/usr/bin/env node

/**
 * Node.js HTTP server wrapper for Actions MCP Worker
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
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

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

// Mock Cloudflare Worker environment
const mockEnv = {
  ALGORAND_NETWORK: process.env.ALGORAND_NETWORK || 'testnet',
  ALGORAND_ALGOD: process.env.ALGORAND_ALGOD,
  READ_ONLY: process.env.READ_ONLY || 'false',
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

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Actions MCP Worker listening on port ${PORT}`);
  console.log(`📊 Health: http://localhost:${PORT}/health`);
  console.log(`📚 Docs: http://localhost:${PORT}/docs`);
  console.log(`🔧 Network: ${mockEnv.ALGORAND_NETWORK}`);
  console.log(`👀 Read-only: ${mockEnv.READ_ONLY}`);
});