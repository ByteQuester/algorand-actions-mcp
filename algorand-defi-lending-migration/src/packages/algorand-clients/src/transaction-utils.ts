/**
 * Transaction utility functions
 */
import algosdk from 'algosdk';
import { Buffer } from 'buffer';
import * as msgpack from 'algo-msgpack-with-bigint';
import type { 
  AlgorandNetwork,
  EncodedTransaction,
  EncodedSignedTransaction 
} from '@algorand-showcase/types';

/**
 * Format microAlgos to Algos with proper decimal places
 */
export function formatAmount(microAlgos: number | bigint): string {
  const algos = Number(microAlgos) / 1_000_000;
  return algos.toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 6
  });
}

/**
 * Parse amount from Algos to microAlgos
 */
export function parseAmount(algos: string | number): number {
  const amount = typeof algos === 'string' ? parseFloat(algos) : algos;
  return Math.round(amount * 1_000_000);
}

/**
 * Validate an Algorand address
 */
export function isValidAddress(address: string): boolean {
  try {
    return algosdk.isValidAddress(address);
  } catch {
    return false;
  }
}

/**
 * Get transaction ID from unsigned transaction
 */
export function getTransactionId(unsignedTxnBase64: string): string | null {
  try {
    const txnBytes = Buffer.from(unsignedTxnBase64, 'base64');
    const txnObj = msgpack.decode(txnBytes) as any;
    const txn = algosdk.Transaction.from_obj_for_encoding(txnObj);
    return txn.txID();
  } catch {
    return null;
  }
}

/**
 * Parse transaction from encoded bytes
 */
export function parseTransaction(encodedTxn: string): EncodedTransaction | null {
  try {
    const bytes = Buffer.from(encodedTxn, 'base64');
    return msgpack.decode(bytes) as EncodedTransaction;
  } catch {
    return null;
  }
}

/**
 * Parse signed transaction from encoded bytes
 */
export function parseSignedTransaction(encodedSignedTxn: string): EncodedSignedTransaction | null {
  try {
    const bytes = Buffer.from(encodedSignedTxn, 'base64');
    return msgpack.decode(bytes) as EncodedSignedTransaction;
  } catch {
    return null;
  }
}

/**
 * Get explorer URL for a transaction
 */
export function getTransactionExplorerUrl(txId: string, network: AlgorandNetwork): string {
  const baseUrl = network === 'testnet' 
    ? 'https://testnet.explorer.perawallet.app'
    : 'https://explorer.perawallet.app';
  
  return `${baseUrl}/tx/${txId}`;
}

/**
 * Get explorer URL for an account
 */
export function getAccountExplorerUrl(address: string, network: AlgorandNetwork): string {
  const baseUrl = network === 'testnet' 
    ? 'https://testnet.explorer.perawallet.app'
    : 'https://explorer.perawallet.app';
  
  return `${baseUrl}/account/${address}`;
}

/**
 * Get explorer URL for an asset
 */
export function getAssetExplorerUrl(assetId: number, network: AlgorandNetwork): string {
  const baseUrl = network === 'testnet' 
    ? 'https://testnet.explorer.perawallet.app'
    : 'https://explorer.perawallet.app';
  
  return `${baseUrl}/asset/${assetId}`;
}

/**
 * Get explorer URL for an application
 */
export function getApplicationExplorerUrl(appId: number, network: AlgorandNetwork): string {
  const baseUrl = network === 'testnet' 
    ? 'https://testnet.explorer.perawallet.app'
    : 'https://explorer.perawallet.app';
  
  return `${baseUrl}/application/${appId}`;
}

/**
 * Convert note string to Uint8Array with length limit
 */
export function prepareNote(note?: string, maxLength: number = 1024): Uint8Array | undefined {
  if (!note) return undefined;
  
  const truncated = note.slice(0, maxLength);
  return new TextEncoder().encode(truncated);
}

/**
 * Convert note Uint8Array to string
 */
export function decodeNote(noteBytes?: Uint8Array): string | undefined {
  if (!noteBytes || noteBytes.length === 0) return undefined;
  
  try {
    return new TextDecoder().decode(noteBytes);
  } catch {
    // If not valid UTF-8, return base64
    return Buffer.from(noteBytes).toString('base64');
  }
}