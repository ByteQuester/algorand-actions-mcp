/**
 * Shared Algorand-specific types
 */
import { Buffer } from 'buffer';

/**
 * Core Algorand account information
 */
export interface AlgorandAccountInfo {
  address: string;
  amount: number;
  assets?: AlgorandAsset[];
  apps?: AlgorandApplication[];
}

/**
 * Basic asset information
 */
export interface AlgorandAsset {
  id: number;
  amount: number;
  creator?: string;
  decimals?: number;
  name?: string;
  unitName?: string;
  url?: string;
  frozen?: boolean;
}

/**
 * Basic application information
 */
export interface AlgorandApplication {
  id: number;
  params?: {
    'approval-program'?: string;
    'clear-state-program'?: string;
    creator?: string;
    'global-state-schema'?: {
      'num-byte-slice': number;
      'num-uint': number;
    };
    'local-state-schema'?: {
      'num-byte-slice': number;
      'num-uint': number;
    };
  };
}

/**
 * Transaction result interface
 */
export interface AlgorandTransactionResult {
  txId: string;
  confirmedRound?: number;
  poolError?: string;
  explorerUrl?: string;
}

/**
 * Transaction simulation result
 */
export interface AlgorandSimulationResult {
  txnGroups?: Array<{
    txnResults?: Array<{
      txnResult?: {
        txn?: any;
        poolError?: string;
      };
    }>;
  }>;
}

/**
 * Suggested transaction parameters
 */
export interface AlgorandSuggestedParams {
  fee: number;
  firstRound: number;
  lastRound: number;
  genesisHash: string;
  genesisID: string;
}

/**
 * Encoded asset parameters structure
 */
export interface EncodedAssetParams {
  /** assetTotal */
  t: number | bigint;
  /** assetDefaultFrozen */
  df: boolean;
  /** assetDecimals */
  dc: number;
  /** assetManager */
  m?: Buffer;
  /** assetReserve */
  r?: Buffer;
  /** assetFreeze */
  f?: Buffer;
  /** assetClawback */
  c?: Buffer;
  /** assetName */
  an?: string;
  /** assetUnitName */
  un?: string;
  /** assetURL */
  au?: string;
  /** assetMetadataHash */
  am?: Buffer;
}

/**
 * Encoded transaction structure
 */
export interface EncodedTransaction {
  /** fee */
  fee?: number;
  /** firstRound */
  fv?: number;
  /** lastRound */
  lv: number;
  /** note */
  note?: Buffer;
  /** from */
  snd: Buffer;
  /** type */
  type: string;
  /** genesisID */
  gen: string;
  /** genesisHash */
  gh: Buffer;
  /** lease */
  lx?: Buffer;
  /** group */
  grp?: Buffer;
  /** amount */
  amt?: number | bigint;
  /** amount (for asset transfers) */
  aamt?: number | bigint;
  /** closeRemainderTo */
  close?: Buffer;
  /** closeRemainderTo (for asset transfers) */
  aclose?: Buffer;
  /** reKeyTo */
  rekey?: Buffer;
  /** to */
  rcv?: Buffer;
  /** to (for asset transfers) */
  arcv?: Buffer;
  /** assetIndex */
  caid?: number;
  /** assetIndex (for asset transfers) */
  xaid?: number;
  /** assetIndex (for asset freezing/unfreezing) */
  faid?: number;
  /** freezeState */
  afrz?: boolean;
  /** freezeAccount */
  fadd?: Buffer;
  /** assetRevocationTarget */
  asnd?: Buffer;
  /** asset parameters */
  apar?: EncodedAssetParams;
  /** appIndex */
  apid?: number;
  /** appOnComplete */
  apan?: number;
  /** appForeignApps */
  apfa?: number[];
  /** appForeignAssets */
  apas?: number[];
  /** appApprovalProgram */
  apap?: Buffer;
  /** appClearProgram */
  apsu?: Buffer;
  /** appArgs */
  apaa?: Buffer[];
  /** appAccounts */
  apat?: Buffer[];
  /** extraPages */
  apep?: number;
}

/**
 * Encoded signed transaction structure
 */
export interface EncodedSignedTransaction {
  /** Transaction signature */
  sig?: Buffer;
  /** The transaction that was signed */
  txn: EncodedTransaction;
  /** Multisig structure */
  msig?: any;
  /** Logic signature */
  lsig?: any;
  /** The signer */
  sgnr?: Buffer;
}