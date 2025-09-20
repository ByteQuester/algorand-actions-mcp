import { z } from "zod";

export interface OracleData {
  oracle: string;
  feed_id: string;
  value: string;
  decimals: number;
  timestamp: number;
  network: string;
  confidence_interval?: string;
  heartbeat?: number;
}

export interface OracleProvider {
  name: string;
  getData(feedId: string, network?: string): Promise<OracleData>;
  getSupportedFeeds(): Promise<string[]>;
}

// Chainlink Oracle Provider
export class ChainlinkProvider implements OracleProvider {
  name = "chainlink";
  private apiKey?: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey;
  }

  async getData(feedId: string, network = "mainnet"): Promise<OracleData> {
    try {
      // In a real implementation, this would call Chainlink's Data Feeds API
      // For now, we'll return mock data based on common feed IDs
      const mockData = this.getMockOracleData(feedId, network);

      // Simulate real API call behavior
      if (this.apiKey) {
        // With API key, we could make authenticated requests to premium feeds
        mockData.confidence_interval = "0.005"; // Better accuracy with API key
      }

      return mockData;
    } catch (error) {
      throw new Error(`Chainlink oracle error for feed ${feedId}: ${error}`);
    }
  }

  async getSupportedFeeds(): Promise<string[]> {
    return [
      "ETH/USD",
      "BTC/USD",
      "ALGO/USD",
      "USDC/USD",
      "LINK/USD",
      "AVAX/USD"
    ];
  }

  private getMockOracleData(feedId: string, network: string): OracleData {
    const mockValues: Record<string, string> = {
      "ETH/USD": "300000000000", // $3000 with 8 decimals
      "BTC/USD": "4500000000000", // $45000 with 8 decimals
      "ALGO/USD": "25000000", // $0.25 with 8 decimals
      "USDC/USD": "100000000", // $1.00 with 8 decimals
      "LINK/USD": "1500000000", // $15.00 with 8 decimals
      "AVAX/USD": "4000000000" // $40.00 with 8 decimals
    };

    return {
      oracle: this.name,
      feed_id: feedId,
      value: mockValues[feedId] || "100000000",
      decimals: 8,
      timestamp: Math.floor(Date.now() / 1000),
      network,
      confidence_interval: "0.01",
      heartbeat: 3600 // 1 hour
    };
  }
}

// Pyth Oracle Provider
export class PythProvider implements OracleProvider {
  name = "pyth";
  private baseUrl = "https://hermes.pyth.network";

  async getData(feedId: string, network = "mainnet"): Promise<OracleData> {
    try {
      // In a real implementation, this would call Pyth's Hermes API
      // For now, return mock data
      return this.getMockOracleData(feedId, network);
    } catch (error) {
      throw new Error(`Pyth oracle error for feed ${feedId}: ${error}`);
    }
  }

  async getSupportedFeeds(): Promise<string[]> {
    return [
      "Crypto.ETH/USD",
      "Crypto.BTC/USD",
      "Crypto.ALGO/USD",
      "Crypto.SOL/USD",
      "Crypto.AVAX/USD"
    ];
  }

  private getMockOracleData(feedId: string, network: string): OracleData {
    const mockValues: Record<string, string> = {
      "Crypto.ETH/USD": "3000000000000000000000", // $3000 with 18 decimals (Pyth format)
      "Crypto.BTC/USD": "45000000000000000000000", // $45000 with 18 decimals
      "Crypto.ALGO/USD": "250000000000000000", // $0.25 with 18 decimals
      "Crypto.SOL/USD": "100000000000000000000", // $100 with 18 decimals
      "Crypto.AVAX/USD": "40000000000000000000" // $40 with 18 decimals
    };

    return {
      oracle: this.name,
      feed_id: feedId,
      value: mockValues[feedId] || "1000000000000000000",
      decimals: 18, // Pyth typically uses 18 decimals
      timestamp: Math.floor(Date.now() / 1000),
      network,
      confidence_interval: "0.005",
      heartbeat: 1 // Pyth updates very frequently
    };
  }
}

// Band Protocol Provider
export class BandProvider implements OracleProvider {
  name = "band";
  private baseUrl = "https://laozi1.bandchain.org";

  async getData(feedId: string, network = "mainnet"): Promise<OracleData> {
    try {
      // In a real implementation, this would call Band Protocol's API
      return this.getMockOracleData(feedId, network);
    } catch (error) {
      throw new Error(`Band oracle error for feed ${feedId}: ${error}`);
    }
  }

  async getSupportedFeeds(): Promise<string[]> {
    return [
      "BTC",
      "ETH",
      "ALGO",
      "BAND",
      "ATOM"
    ];
  }

  private getMockOracleData(feedId: string, network: string): OracleData {
    const mockValues: Record<string, string> = {
      "BTC": "4500000000", // $45000 with 6 decimals (Band format)
      "ETH": "3000000000", // $3000 with 6 decimals
      "ALGO": "250000", // $0.25 with 6 decimals
      "BAND": "2500000", // $2.50 with 6 decimals
      "ATOM": "10000000" // $10.00 with 6 decimals
    };

    return {
      oracle: this.name,
      feed_id: feedId,
      value: mockValues[feedId] || "1000000",
      decimals: 6, // Band typically uses 6 decimals
      timestamp: Math.floor(Date.now() / 1000),
      network,
      confidence_interval: "0.02",
      heartbeat: 60 // Band updates every minute
    };
  }
}

// Oracle Provider Factory
export class OracleProviderFactory {
  static createProvider(oracle: string, apiKey?: string): OracleProvider {
    switch (oracle.toLowerCase()) {
      case 'chainlink':
        return new ChainlinkProvider(apiKey);
      case 'pyth':
        return new PythProvider();
      case 'band':
        return new BandProvider();
      default:
        return new ChainlinkProvider(apiKey); // Default to Chainlink
    }
  }

  static getSupportedOracles(): string[] {
    return ['chainlink', 'pyth', 'band'];
  }
}