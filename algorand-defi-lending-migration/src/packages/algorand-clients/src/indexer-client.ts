/**
 * Algorand Indexer client wrapper with common functionality
 */
import algosdk from 'algosdk';
import type { AlgorandAccountInfo } from '@algorand-showcase/types';
import type { AlgorandClientConfig, ClientAsyncResult } from './types.js';

/**
 * Search parameters for transactions
 */
export interface TransactionSearchParams {
  address?: string;
  assetId?: number;
  limit?: number;
  nextToken?: string;
  minRound?: number;
  maxRound?: number;
  txType?: string;
}

/**
 * Search parameters for assets
 */
export interface AssetSearchParams {
  assetId?: number;
  name?: string;
  unit?: string;
  creator?: string;
  limit?: number;
  nextToken?: string;
}

/**
 * Search parameters for applications
 */
export interface ApplicationSearchParams {
  applicationId?: number;
  creator?: string;
  limit?: number;
  nextToken?: string;
}

/**
 * Indexer client wrapper with pagination and common operations
 */
export class IndexerClientWrapper {
  private client: algosdk.Indexer;
  public readonly config: AlgorandClientConfig;

  constructor(config: AlgorandClientConfig) {
    this.config = config;
    this.client = new algosdk.Indexer(
      config.token || '',
      config.indexerUrl || config.algodUrl.replace('algod', 'indexer'),
      ''
    );
  }

  /**
   * Get account information from Indexer
   */
  async getAccountInfo(address: string): ClientAsyncResult<AlgorandAccountInfo> {
    try {
      if (!algosdk.isValidAddress(address)) {
        return {
          success: false,
          error: new Error('Invalid address')
        };
      }

      const accountInfo = await this.client.lookupAccountByID(address).do();
      const account = accountInfo.account;
      
      return {
        success: true,
        data: {
          address: account.address,
          amount: account.amount,
          assets: account.assets?.map((asset: any) => ({
            id: asset['asset-id'],
            amount: asset.amount,
            frozen: asset['is-frozen']
          })),
          apps: account['apps-local-state']?.map((app: any) => ({
            id: app.id,
            params: app
          }))
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to get account info from indexer')
      };
    }
  }

  /**
   * Search transactions
   */
  async searchTransactions(params: TransactionSearchParams): ClientAsyncResult<any> {
    try {
      let query = this.client.searchForTransactions();

      if (params.address) query = query.address(params.address);
      if (params.assetId) query = query.assetID(params.assetId);
      if (params.minRound) query = query.minRound(params.minRound);
      if (params.maxRound) query = query.maxRound(params.maxRound);
      if (params.txType) query = query.txType(params.txType);
      if (params.limit) query = query.limit(params.limit);
      if (params.nextToken) query = query.nextToken(params.nextToken);

      const response = await query.do();
      
      return {
        success: true,
        data: response
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to search transactions')
      };
    }
  }

  /**
   * Search assets
   */
  async searchAssets(params: AssetSearchParams): ClientAsyncResult<any> {
    try {
      let query = this.client.searchForAssets();

      if (params.assetId) query = query.index(params.assetId);
      if (params.name) query = query.name(params.name);
      if (params.unit) query = query.unit(params.unit);
      if (params.creator) query = query.creator(params.creator);
      if (params.limit) query = query.limit(params.limit);
      if (params.nextToken) query = query.nextToken(params.nextToken);

      const response = await query.do();
      
      return {
        success: true,
        data: response
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to search assets')
      };
    }
  }

  /**
   * Search applications
   */
  async searchApplications(params: ApplicationSearchParams): ClientAsyncResult<any> {
    try {
      let query = this.client.searchForApplications();

      if (params.applicationId) query = query.index(params.applicationId);
      if (params.creator) query = query.creator(params.creator);
      if (params.limit) query = query.limit(params.limit);
      if (params.nextToken) query = query.nextToken(params.nextToken);

      const response = await query.do();
      
      return {
        success: true,
        data: response
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to search applications')
      };
    }
  }

  /**
   * Lookup transaction by ID
   */
  async lookupTransaction(txId: string): ClientAsyncResult<any> {
    try {
      const response = await this.client.lookupTransactionByID(txId).do();
      
      return {
        success: true,
        data: response
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to lookup transaction')
      };
    }
  }

  /**
   * Lookup asset by ID
   */
  async lookupAsset(assetId: number): ClientAsyncResult<any> {
    try {
      const response = await this.client.lookupAssetByID(assetId).do();
      
      return {
        success: true,
        data: response
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to lookup asset')
      };
    }
  }

  /**
   * Lookup application by ID
   */
  async lookupApplication(appId: number): ClientAsyncResult<any> {
    try {
      const response = await this.client.lookupApplications(appId).do();
      
      return {
        success: true,
        data: response
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to lookup application')
      };
    }
  }

  /**
   * Get the underlying algosdk indexer client for advanced operations
   */
  getClient(): algosdk.Indexer {
    return this.client;
  }
}