import api from './index'
import type { MarketData, Candle, Statistics } from '@/types/market'

// ─── Market API ───────────────────────────────────────────────────────────────

export const marketApi = {
  /** GET /market-data/{symbol} — live price quote */
  async getMarketData(symbol: string): Promise<MarketData> {
    const { data } = await api.get<MarketData>(`/market-data/${symbol}`)
    return data
  },

  /** GET /market-data — bulk quotes for multiple symbols */
  async getBulkMarketData(symbols: string[]): Promise<MarketData[]> {
    const { data } = await api.get<MarketData[]>('/market-data', {
      params: { symbols: symbols.join(',') },
    })
    return data
  },

  /** GET /statistics — dashboard summary statistics */
  async getStatistics(): Promise<Statistics> {
    const { data } = await api.get<Statistics>('/statistics')
    return data
  },

  /** GET /market-data/{symbol}/history — OHLCV candle history */
  async getPriceHistory(symbol: string, days = 90): Promise<Candle[]> {
    const { data } = await api.get<Candle[]>(`/market-data/${symbol}/history`, {
      params: { days },
    })
    return data
  },
}
