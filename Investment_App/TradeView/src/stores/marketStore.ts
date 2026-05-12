import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MarketData, Candle, Statistics } from '@/types/market'
import { marketApi } from '@/api/market'
import { generateMockMarketData, generatePriceHistory, generateMockStatistics } from '@/utils/mockData'
import { MOCK_INSTRUMENTS } from '@/utils/mockData'
import { useNotificationStore } from './notificationStore'

const useMock = import.meta.env.VITE_MOCK_DATA === 'true'

// ─── Market Store ─────────────────────────────────────────────────────────────

export const useMarketStore = defineStore('market', () => {
  const notifications = useNotificationStore()

  const marketData   = ref<Record<string, MarketData>>({})
  const priceHistory = ref<Record<string, Candle[]>>({})
  const statistics   = ref<Statistics | null>(null)
  const loading      = ref(false)
  const error        = ref<string | null>(null)

  // ─── Actions ──────────────────────────────────────────────────────────────

  async function fetchStatistics() {
    loading.value = true
    error.value = null
    try {
      if (useMock) {
        await new Promise((r) => setTimeout(r, 400))
        statistics.value = generateMockStatistics()
      } else {
        statistics.value = await marketApi.getStatistics()
      }
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch statistics'
      notifications.error('Statistics fetch failed', error.value)
    } finally {
      loading.value = false
    }
  }

  async function fetchMarketData(symbol: string): Promise<MarketData | null> {
    try {
      if (useMock) {
        const [data] = generateMockMarketData([symbol])
        marketData.value[symbol] = data
        return data
      }
      const data = await marketApi.getMarketData(symbol)
      marketData.value[symbol] = data
      return data
    } catch (err: unknown) {
      notifications.error('Market data error', `Failed to fetch ${symbol}`)
      return null
    }
  }

  async function fetchBulkMarketData(symbols?: string[]) {
    const syms = symbols ?? MOCK_INSTRUMENTS.slice(0, 20).map((i) => i.symbol)
    try {
      if (useMock) {
        await new Promise((r) => setTimeout(r, 300))
        const data = generateMockMarketData(syms)
        data.forEach((d) => { marketData.value[d.symbol] = d })
      } else {
        const data = await marketApi.getBulkMarketData(syms)
        data.forEach((d) => { marketData.value[d.symbol] = d })
      }
    } catch (err: unknown) {
      notifications.error('Market data error', 'Failed to fetch bulk market data')
    }
  }

  async function fetchPriceHistory(symbol: string, days = 90) {
    try {
      if (useMock) {
        await new Promise((r) => setTimeout(r, 250))
        priceHistory.value[symbol] = generatePriceHistory(symbol, days)
      } else {
        priceHistory.value[symbol] = await marketApi.getPriceHistory(symbol, days)
      }
    } catch (err: unknown) {
      notifications.error('Chart error', `Failed to load price history for ${symbol}`)
    }
  }

  /** Refresh all market data (used by auto-refresh) */
  async function refreshAll() {
    const symbols = Object.keys(marketData.value)
    if (symbols.length > 0) {
      await fetchBulkMarketData(symbols)
    }
    await fetchStatistics()
  }

  return {
    marketData,
    priceHistory,
    statistics,
    loading,
    error,
    fetchStatistics,
    fetchMarketData,
    fetchBulkMarketData,
    fetchPriceHistory,
    refreshAll,
  }
})
