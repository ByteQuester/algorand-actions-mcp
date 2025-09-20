#!/usr/bin/env node

/**
 * Simple Market Data MCP Service
 * Provides basic health check and price endpoints for testing
 */

import { createServer } from 'http';

const PORT = process.env.PORT || 8003;

const server = createServer((req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);

  // Health check endpoint
  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      service: 'market-data-mcp',
      version: '1.0.0',
      timestamp: new Date().toISOString()
    }));
    return;
  }

  // Price endpoint (mock)
  if (url.pathname === '/price' || url.pathname.startsWith('/api/price')) {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      ALGO: 0.2337,
      USDC: 1.00,
      USDT: 1.00,
      timestamp: new Date().toISOString(),
      source: 'mock-market-data'
    }));
    return;
  }

  // Root endpoint
  if (url.pathname === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <h1>Market Data MCP Service</h1>
      <p>Status: Running</p>
      <p>Port: ${PORT}</p>
      <p>Endpoints:</p>
      <ul>
        <li><a href="/health">/health</a> - Health check</li>
        <li><a href="/price">/price</a> - Price data</li>
      </ul>
    `);
    return;
  }

  // 404 for other paths
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, () => {
  console.log(`🚀 Market Data MCP Service listening on port ${PORT}`);
  console.log(`📊 Health: http://localhost:${PORT}/health`);
  console.log(`💰 Prices: http://localhost:${PORT}/price`);
  console.log(`🌐 Mode: Mock Data`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('Shutting down Market Data MCP Service...');
  server.close(() => {
    process.exit(0);
  });
});