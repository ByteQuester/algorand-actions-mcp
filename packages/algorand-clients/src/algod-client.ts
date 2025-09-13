/**
 * Algorand Algod client wrapper with common functionality
 */
import algosdk from 'algosdk';
import { Buffer } from 'buffer';
import type { 
  AlgorandSuggestedParams,
  AlgorandTransactionResult,
  AlgorandSimulationResult,
  AlgorandAccountInfo
} from '@algorand-showcase/types';
import type { 
  AlgorandClientConfig,
  PaymentTransactionParams,
  SimulationOptions,
  ClientAsyncResult 
} from './types.js';

/**
 * Algod client wrapper with retry logic and common operations
 */
export class AlgodClientWrapper {
  private client: algosdk.Algodv2;
  public readonly config: AlgorandClientConfig;

  constructor(config: AlgorandClientConfig) {
    this.config = config;
    this.client = new algosdk.Algodv2(
      config.token || '',
      config.algodUrl,
      ''
    );
  }

  /**
   * Get suggested transaction parameters
   */
  async getSuggestedParams(): ClientAsyncResult<AlgorandSuggestedParams> {
    try {
      const params = await this.client.getTransactionParams().do();
      return {
        success: true,
        data: {
          fee: params.fee,
          firstRound: params.firstRound,
          lastRound: params.lastRound,
          genesisHash: params.genesisHash,
          genesisID: params.genesisID
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to get suggested params')
      };
    }
  }

  /**
   * Get account information
   */
  async getAccountInfo(address: string): ClientAsyncResult<AlgorandAccountInfo> {
    try {
      if (!algosdk.isValidAddress(address)) {
        return {
          success: false,
          error: new Error('Invalid address')
        };
      }

      const accountInfo = await this.client.accountInformation(address).do();
      
      return {
        success: true,
        data: {
          address: accountInfo.address,
          amount: accountInfo.amount,
          assets: accountInfo.assets?.map((asset: any) => ({
            id: asset['asset-id'],
            amount: asset.amount,
            frozen: asset['is-frozen']
          })),
          apps: accountInfo['apps-local-state']?.map((app: any) => ({
            id: app.id,
            params: app
          }))
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to get account info')
      };
    }
  }

  /**
   * Build payment transaction
   */
  async buildPaymentTransaction(params: PaymentTransactionParams): ClientAsyncResult<string> {
    try {
      if (!algosdk.isValidAddress(params.from) || !algosdk.isValidAddress(params.to)) {
        return {
          success: false,
          error: new Error('Invalid address')
        };
      }

      const suggestedParamsResult = await this.getSuggestedParams();
      if (!suggestedParamsResult.success) {
        return suggestedParamsResult;
      }

      const suggestedParams = suggestedParamsResult.data;
      const noteBytes = typeof params.note === 'string' 
        ? new TextEncoder().encode(params.note.slice(0, 256))
        : params.note;

      const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
        from: params.from,
        to: params.to,
        amount: params.amount,
        note: noteBytes,
        suggestedParams,
        rekeyTo: params.rekeyTo,
        closeRemainderTo: params.closeRemainderTo,
      });

      const unsignedTxnBase64 = Buffer.from(algosdk.encodeUnsignedTransaction(txn)).toString('base64');
      
      return {
        success: true,
        data: unsignedTxnBase64
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to build payment transaction')
      };
    }
  }

  /**
   * Simulate transaction
   */
  async simulateTransaction(unsignedTxnBase64: string): ClientAsyncResult<AlgorandSimulationResult> {
    try {
      const unsignedBytes = Buffer.from(unsignedTxnBase64, 'base64');
      const result = await this.client.simulateRawTransactions(unsignedBytes).do();
      
      return {
        success: true,
        data: result
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to simulate transaction')
      };
    }
  }

  /**
   * Submit signed transaction
   */
  async submitTransaction(signedTxnBase64: string): ClientAsyncResult<AlgorandTransactionResult> {
    try {
      const bytes = Buffer.from(signedTxnBase64, 'base64');
      const response = await this.client.sendRawTransaction(bytes).do();
      
      const txId = response?.txId || response?.txid;
      const explorerBaseUrl = this.config.network === 'testnet' 
        ? 'https://testnet.explorer.perawallet.app/tx/' 
        : 'https://explorer.perawallet.app/tx/';
      
      return {
        success: true,
        data: {
          txId,
          explorerUrl: `${explorerBaseUrl}${txId}`
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to submit transaction')
      };
    }
  }

  /**
   * Compile TEAL code
   */
  async compileTeal(source: string): ClientAsyncResult<{ hash: string; result: string }> {
    try {
      // Ensure proper line endings and add final newline
      let processedSource = source.replace(/\r\n/g, '\n');
      if (!processedSource.endsWith('\n')) {
        processedSource += '\n';
      }

      const sourceBytes = new TextEncoder().encode(processedSource);
      const response = await this.client.compile(sourceBytes).do();

      return {
        success: true,
        data: {
          hash: response.hash,
          result: response.result
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to compile TEAL')
      };
    }
  }

  /**
   * Get block information by round
   */
  async getBlock(round: number): ClientAsyncResult<any> {
    try {
      const block = await this.client.block(round).do();
      return {
        success: true,
        data: block
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to get block')
      };
    }
  }

  /**
   * Get node status
   */
  async getStatus(): ClientAsyncResult<any> {
    try {
      const status = await this.client.status().do();
      return {
        success: true,
        data: status
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Failed to get node status')
      };
    }
  }

  /**
   * Get the underlying algosdk client for advanced operations
   */
  getClient(): algosdk.Algodv2 {
    return this.client;
  }
}