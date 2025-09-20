/**
 * Common utility types used across packages
 */

/**
 * Algorand network type
 */
export type AlgorandNetwork = 'mainnet' | 'testnet' | 'betanet';

/**
 * Standard Result type for error handling
 */
export type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

/**
 * Async version of Result type
 */
export type AsyncResult<T, E = Error> = Promise<Result<T, E>>;

/**
 * Generic API response wrapper
 */
export interface APIResponse<T = unknown> {
  data?: T;
  error?: string;
  success: boolean;
  message?: string;
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: 'ok' | 'error';
  mode?: 'READ-only' | 'full' | 'actions';
  network?: string;
  timestamp?: string;
  version?: string;
}

/**
 * Verification status for assets
 */
export type VerificationTier = 'verified' | 'unverified' | 'suspicious';

/**
 * Asset verification response
 */
export interface AssetVerificationResponse {
  asset_id: number;
  verification_tier: VerificationTier;
  explorer_url: string;
}

/**
 * Generic key-value store interface
 */
export interface KeyValue {
  [key: string]: unknown;
}

/**
 * Environment variable helper types
 */
export type EnvValue = string | boolean | undefined;