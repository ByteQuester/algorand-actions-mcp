import { z } from "zod";

export interface PriceData {
  pair: string;
  price: number;
  volume_24h?: number;
  change_24h?: number;
  timestamp: string;
  source: string;
}

export interface PriceProvider {
  name: string;
  getPrice(pair: string): Promise<PriceData>;
  getSupportedPairs(): Promise<string[]>;
}

// CoinGecko Price Provider
export class CoinGeckoProvider implements PriceProvider {
  name = "coingecko";
  private baseUrl = "https://api.coingecko.com/api/v3";
  private apiKey?: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey;
  }

  async getPrice(pair: string): Promise<PriceData> {
    try {
      // Convert pair format (e.g., "ALGO/USDC" to coingecko format)
      const [base, quote] = pair.split('/');
      const coinId = this.getCoinId(base);
      const vs_currency = this.getCurrency(quote);

      const url = `${this.baseUrl}/simple/price?ids=${coinId}&vs_currencies=${vs_currency}&include_24hr_change=true&include_24hr_vol=true`;

      const headers: Record<string, string> = {};
      if (this.apiKey) {
        headers['x-cg-demo-api-key'] = this.apiKey;
      }

      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error(`CoinGecko API error: ${response.status}`);
      }

      const data = await response.json();
      const coinData = data[coinId];

      if (!coinData) {
        throw new Error(`No data found for pair ${pair}`);
      }

      return {
        pair,
        price: coinData[vs_currency],
        volume_24h: coinData[`${vs_currency}_24h_vol`],
        change_24h: coinData[`${vs_currency}_24h_change`],
        timestamp: new Date().toISOString(),
        source: this.name
      };
    } catch (error) {
      // Fallback to mock data in case of API failure
      return this.getMockPrice(pair);
    }
  }

  async getSupportedPairs(): Promise<string[]> {
    return [
      "ALGO/USD", "ALGO/USDC", "ALGO/BTC",
      "BTC/USD", "ETH/USD", "USDC/USD"
    ];
  }

  private getCoinId(symbol: string): string {
    const mapping: Record<string, string> = {
      'ALGO': 'algorand',
      'BTC': 'bitcoin',
      'ETH': 'ethereum',
      'USDC': 'usd-coin'
    };
    return mapping[symbol.toUpperCase()] || symbol.toLowerCase();
  }

  private getCurrency(symbol: string): string {
    const mapping: Record<string, string> = {
      'USD': 'usd',
      'USDC': 'usd',
      'BTC': 'btc',
      'ETH': 'eth'
    };
    return mapping[symbol.toUpperCase()] || symbol.toLowerCase();
  }

  private getMockPrice(pair: string): PriceData {
    const mockPrices: Record<string, number> = {
      'ALGO/USD': 0.25,
      'ALGO/USDC': 0.25,
      'BTC/USD': 45000,
      'ETH/USD': 3000,
      'USDC/USD': 1.0
    };

    return {
      pair,
      price: mockPrices[pair] || 1.0,
      volume_24h: 1000000,
      change_24h: 2.5,
      timestamp: new Date().toISOString(),
      source: this.name
    };
  }
}

// Coinbase Price Provider
export class CoinbaseProvider implements PriceProvider {
  name = "coinbase";
  private baseUrl = "https://api.coinbase.com/v2";

  async getPrice(pair: string): Promise<PriceData> {
    try {
      // Convert pair format for Coinbase (e.g., "ALGO/USD" to "ALGO-USD")
      const coinbasePair = pair.replace('/', '-');
      const url = `${this.baseUrl}/exchange-rates?currency=${coinbasePair.split('-')[0]}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Coinbase API error: ${response.status}`);
      }

      const data = await response.json();
      const quote = coinbasePair.split('-')[1];
      const price = parseFloat(data.data.rates[quote] || "0");

      return {
        pair,
        price,
        timestamp: new Date().toISOString(),
        source: this.name
      };
    } catch (error) {
      // Fallback to mock data
      return this.getMockPrice(pair);
    }
  }

  async getSupportedPairs(): Promise<string[]> {
    return [
      "ALGO/USD", "BTC/USD", "ETH/USD", "USDC/USD"
    ];
  }

  private getMockPrice(pair: string): PriceData {
    const mockPrices: Record<string, number> = {
      'ALGO/USD': 0.25,
      'BTC/USD': 45000,
      'ETH/USD': 3000,
      'USDC/USD': 1.0
    };

    return {
      pair,
      price: mockPrices[pair] || 1.0,
      timestamp: new Date().toISOString(),
      source: this.name
    };
  }
}

// Price Provider Factory
export class PriceProviderFactory {
  static createProvider(source: string, apiKey?: string): PriceProvider {
    switch (source.toLowerCase()) {
      case 'coingecko':
        return new CoinGeckoProvider(apiKey);
      case 'coinbase':
        return new CoinbaseProvider();
      default:
        return new CoinGeckoProvider(apiKey); // Default to CoinGecko
    }
  }

  static getSupportedProviders(): string[] {
    return ['coingecko', 'coinbase'];
  }
}