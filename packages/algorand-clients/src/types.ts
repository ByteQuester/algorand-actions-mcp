/**
 * Types specific to Algorand clients
 */
import type { 
  AlgorandNetwork, 
  AlgorandSuggestedParams,
  AlgorandTransactionResult,
  AlgorandSimulationResult,
  Result
} from '@algorand-showcase/types';

/**
 * Client configuration interface
 */
export interface AlgorandClientConfig {
  network: AlgorandNetwork;
  algodUrl: string;
  indexerUrl?: string;
  token?: string;
  headers?: Record<string, string>;
}

/**
 * Transaction building parameters
 */
export interface PaymentTransactionParams {
  from: string;
  to: string;
  amount: number;
  note?: string | Uint8Array;
  lease?: Uint8Array;
  rekeyTo?: string;
  closeRemainderTo?: string;
}

/**
 * Asset transfer parameters
 */
export interface AssetTransferParams {
  from: string;
  to: string;
  assetIndex: number;
  amount: number;
  note?: string | Uint8Array;
  lease?: Uint8Array;
  rekeyTo?: string;
  closeRemainderTo?: string;
  revocationTarget?: string;
}

/**
 * Transaction simulation options
 */
export interface SimulationOptions {
  allowEmptySignatures?: boolean;
  allowMoreLogging?: boolean;
}

/**
 * Client method results
 */
export type ClientResult<T> = Result<T, Error>;
export type ClientAsyncResult<T> = Promise<ClientResult<T>>;