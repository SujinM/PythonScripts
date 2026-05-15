import api from './index'
import type { MarketData, Candle, Statistics } from '@/types/market'

// ─── Market API ───────────────────────────────────────────────────────────────

export const marketApi = {
  /** GET /api/v1/market-data/{symbol} — live price quote */
  async getMarketData(symbol: string): Promise<MarketData> {
    const { data } = await api.get<MarketData>(`/api/v1/market-data/${symbol}`)
    return data
  },

  /** GET /api/v1/market-data — bulk quotes for multiple symbols */
  async getBulkMarketData(symbols: string[]): Promise<MarketData[]> {
    const { data } = await api.get<MarketData[]>('/api/v1/market-data', {
      params: { symbols: symbols.join(',') },
    })
    return data
  },

  /** GET /api/v1/statistics — dashboard summary statistics */
  async getStatistics(): Promise<Statistics> {
    const { data } = await api.get<Statistics>('/api/v1/statistics')
    return data
  },

  /** GET /api/v1/market-data/{symbol}/history — OHLCV candle history */
  async getPriceHistory(symbol: string, days = 90): Promise<Candle[]> {
    const { data } = await api.get<Candle[]>(`/api/v1/market-data/${symbol}/history`, {
      params: { days },
    })
    return data
  },
}
