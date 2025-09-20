#!/usr/bin/env node

/**
 * Demo Real Writer MCP Service
 * A simplified service that demonstrates real transaction building on Algorand testnet
 */

const http = require('http');
// Note: Run `pnpm install` to get algosdk dependency
const algosdk = require('algosdk');

const PORT = process.env.PORT || 8788;
const ALGOD_URL = 'https://testnet-api.algonode.cloud';
const ALGOD_TOKEN = '';

// Initialize Algorand client
const algodClient = new algosdk.Algodv2(ALGOD_TOKEN, ALGOD_URL, '');

// CORS headers
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
};

function sendResponse(res, data, status = 200) {
    res.writeHead(status, corsHeaders);
    res.end(JSON.stringify(data, null, 2));
}

async function buildPaymentTransaction(params) {
    try {
        const { fromAddress, toAddress, microAlgos, note } = params;

        if (!fromAddress || !toAddress || !microAlgos) {
            return {
                success: false,
                error: 'Missing required parameters: fromAddress, toAddress, microAlgos'
            };
        }

        // Get network parameters
        const suggestedParams = await algodClient.getTransactionParams().do();

        // Build payment transaction
        const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
            from: fromAddress,
            to: toAddress,
            amount: parseInt(microAlgos),
            note: note ? new Uint8Array(Buffer.from(note)) : undefined,
            suggestedParams
        });

        // Encode transaction
        const txnBase64 = Buffer.from(algosdk.encodeUnsignedTransaction(txn)).toString('base64');

        return {
            success: true,
            unsignedTxnBase64: txnBase64,
            txId: txn.txID(),
            fee: txn.fee,
            firstRound: txn.firstRound,
            lastRound: txn.lastRound,
            genesisHash: Buffer.from(txn.genesisHash).toString('base64'),
            message: 'Transaction built successfully! Ready for signing and submission.',
            note: 'This is a REAL testnet transaction. It will execute if signed and submitted.'
        };
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
}

// Create HTTP server
const server = http.createServer(async (req, res) => {
    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
        res.writeHead(200, corsHeaders);
        res.end();
        return;
    }

    // Parse URL
    const url = new URL(req.url, `http://localhost:${PORT}`);

    // Health check
    if (url.pathname === '/health') {
        sendResponse(res, {
            status: 'ok',
            mode: 'LIVE_WRITER',
            service: 'Demo Real Writer MCP',
            network: 'testnet',
            timestamp: new Date().toISOString()
        });
        return;
    }

    // Handle POST requests
    if (req.method === 'POST' && url.pathname === '/tools/build_payment_transaction') {
        let body = '';
        req.on('data', chunk => body += chunk.toString());
        req.on('end', async () => {
            try {
                const data = JSON.parse(body);
                const result = await buildPaymentTransaction(data);
                sendResponse(res, result);
            } catch (error) {
                sendResponse(res, { success: false, error: 'Invalid JSON' }, 400);
            }
        });
        return;
    }

    // 404 for other requests
    sendResponse(res, { error: 'Not found' }, 404);
});

server.listen(PORT, () => {
    console.log(`🚀 Demo Real Writer MCP Service running on port ${PORT}`);
    console.log(`📖 Health: http://localhost:${PORT}/health`);
    console.log(`⚠️  WARNING: This builds REAL Algorand testnet transactions!`);
    console.log(`🌐 Network: Algorand Testnet`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\\n🛑 Shutting down Demo Writer MCP Service...');
    server.close(() => {
        console.log('✅ Server stopped');
        process.exit(0);
    });
});