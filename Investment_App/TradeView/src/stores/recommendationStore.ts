// TradeView/src/stores/recommendationStore.ts
// Pinia store for AI recommendation state, keyed by "broker:symbol"

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Recommendation, RiskProfile } from '@/types/ai'
import { aiApi } from '@/api/ai'

// ─── Recommendation Store ─────────────────────────────────────────────────────
// Caches recommendations in memory by composite key `{broker}:{symbol}`.
// Re-fetches on demand; does not auto-refresh.

export const useRecommendationStore = defineStore('recommendation', () => {
  // Keyed by `{broker}:{symbol}` — e.g. "etoro:TSLA"
  const recommendations = ref<Record<string, Recommendation>>({})
  const loading         = ref<Record<string, boolean>>({})
  const errors          = ref<Record<string, string | null>>({})

  function _key(broker: string, symbol: string): string {
    return `${broker.toLowerCase()}:${symbol.toUpperCase()}`
  }

  function getRecommendation(broker: string, symbol: string): Recommendation | null {
    return recommendations.value[_key(broker, symbol)] ?? null
  }

  function isLoading(broker: string, symbol: string): boolean {
    return loading.value[_key(broker, symbol)] ?? false
  }

  function getError(broker: string, symbol: string): string | null {
    return errors.value[_key(broker, symbol)] ?? null
  }

  async function fetchRecommendation(
    broker: string,
    symbol: string,
    riskProfile: RiskProfile = 'moderate',
    timeframe?: string,
    forceRefresh = false,
  ): Promise<void> {
    const k = _key(broker, symbol)

    // Return cached result unless caller forces a refresh
    if (!forceRefresh && recommendations.value[k]) return

    loading.value[k] = true
    errors.value[k]  = null

    try {
      const result = await aiApi.getRecommendation(broker, {
        symbol,
        riskProfile,
        timeframe,
      })
      recommendations.value[k] = result
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to fetch recommendation'
      errors.value[k] = message
    } finally {
      loading.value[k] = false
    }
  }

  function invalidate(broker: string, symbol: string): void {
    const k = _key(broker, symbol)
    delete recommendations.value[k]
    delete errors.value[k]
  }

  return {
    recommendations,
    loading,
    errors,
    getRecommendation,
    isLoading,
    getError,
    fetchRecommendation,
    invalidate,
  }
})
