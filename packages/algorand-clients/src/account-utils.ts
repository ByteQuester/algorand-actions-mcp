/**
 * Account utility functions
 */
import algosdk from 'algosdk';
import type { AlgorandNetwork } from '@algorand-showcase/types';

/**
 * Generate a new Algorand account
 */
export function generateAccount(): { address: string; mnemonic: string; secretKey: Uint8Array } {
  const account = algosdk.generateAccount();
  const mnemonic = algosdk.secretKeyToMnemonic(account.sk);
  
  return {
    address: account.addr,
    mnemonic,
    secretKey: account.sk
  };
}

/**
 * Recover account from mnemonic
 */
export function accountFromMnemonic(mnemonic: string): { address: string; secretKey: Uint8Array } {
  const account = algosdk.mnemonicToSecretKey(mnemonic);
  
  return {
    address: account.addr,
    secretKey: account.sk
  };
}

/**
 * Validate a mnemonic phrase
 */
export function isValidMnemonic(mnemonic: string): boolean {
  try {
    algosdk.mnemonicToSecretKey(mnemonic);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if an account is opted into an asset
 */
export function isOptedIntoAsset(account: any, assetId: number): boolean {
  if (!account.assets) return false;
  
  return account.assets.some((asset: any) => asset['asset-id'] === assetId);
}

/**
 * Get account asset balance
 */
export function getAssetBalance(account: any, assetId: number): number {
  if (!account.assets) return 0;
  
  const asset = account.assets.find((asset: any) => asset['asset-id'] === assetId);
  return asset ? asset.amount : 0;
}

/**
 * Check if an account is opted into an application
 */
export function isOptedIntoApp(account: any, appId: number): boolean {
  if (!account['apps-local-state']) return false;
  
  return account['apps-local-state'].some((app: any) => app.id === appId);
}

/**
 * Get minimum balance requirement for an account
 */
export function calculateMinimumBalance(account: any): number {
  const baseMinBalance = 100_000; // 0.1 ALGO base requirement
  const assetMinBalance = 100_000; // 0.1 ALGO per asset
  const appMinBalance = 100_000;   // 0.1 ALGO per app opt-in
  
  const assetCount = account.assets ? account.assets.length : 0;
  const appCount = account['apps-local-state'] ? account['apps-local-state'].length : 0;
  
  return baseMinBalance + (assetCount * assetMinBalance) + (appCount * appMinBalance);
}

/**
 * Get available balance (total - minimum required)
 */
export function getAvailableBalance(account: any): number {
  const totalBalance = account.amount || 0;
  const minBalance = calculateMinimumBalance(account);
  
  return Math.max(0, totalBalance - minBalance);
}

/**
 * Format account address for display (shortened with ellipsis)
 */
export function formatAddress(address: string, startChars: number = 6, endChars: number = 4): string {
  if (address.length <= startChars + endChars) {
    return address;
  }
  
  return `${address.slice(0, startChars)}...${address.slice(-endChars)}`;
}

/**
 * Get account type string based on configuration
 */
export function getAccountType(account: any): string {
  const hasAssets = account.assets && account.assets.length > 0;
  const hasApps = account['apps-local-state'] && account['apps-local-state'].length > 0;
  const hasCreatedAssets = account['created-assets'] && account['created-assets'].length > 0;
  const hasCreatedApps = account['created-apps'] && account['created-apps'].length > 0;
  
  if (hasCreatedAssets || hasCreatedApps) {
    return 'creator';
  } else if (hasAssets || hasApps) {
    return 'active';
  } else {
    return 'basic';
  }
}

/**
 * Check if account has sufficient balance for a transaction
 */
export function hasSufficientBalance(
  account: any, 
  amount: number, 
  fee: number = 1000
): boolean {
  const availableBalance = getAvailableBalance(account);
  return availableBalance >= (amount + fee);
}