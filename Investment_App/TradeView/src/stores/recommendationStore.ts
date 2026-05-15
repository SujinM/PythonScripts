// TradeView/src/stores/recommendationStore.ts
// Pinia store for AI recommendation (Phase 2) + backtest (Phase 3) state

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { BacktestResult, Recommendation, RiskProfile } from '@/types/ai'
import { aiApi } from '@/api/ai'

// ─── Recommendation + Backtest Store ─────────────────────────────────────────
// Caches recommendations and backtest results by composite key `{broker}:{symbol}`.

export const useRecommendationStore = defineStore('recommendation', () => {
  // Keyed by `{broker}:{symbol}` — e.g. "etoro:TSLA"
  const recommendations = ref<Record<string, Recommendation>>({})
  const backtests       = ref<Record<string, BacktestResult>>({})
  const loading         = ref<Record<string, boolean>>({})
  const errors          = ref<Record<string, string | null>>({})
  const btLoading       = ref<Record<string, boolean>>({})
  const btErrors        = ref<Record<string, string | null>>({})

  function _key(broker: string, symbol: string): string {
    return `${broker.toLowerCase()}:${symbol.toUpperCase()}`
  }

  // ── Recommendation ────────────────────────────────────────────────────────

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

  // ── Backtest (Phase 3) ────────────────────────────────────────────────────

  function getBacktest(broker: string, symbol: string): BacktestResult | null {
    return backtests.value[_key(broker, symbol)] ?? null
  }

  function isBacktestLoading(broker: string, symbol: string): boolean {
    return btLoading.value[_key(broker, symbol)] ?? false
  }

  function getBacktestError(broker: string, symbol: string): string | null {
    return btErrors.value[_key(broker, symbol)] ?? null
  }

  async function fetchBacktest(
    broker: string,
    symbol: string,
    riskProfile: RiskProfile = 'moderate',
    forceRefresh = false,
  ): Promise<void> {
    const k = _key(broker, symbol)

    if (!forceRefresh && backtests.value[k]) return

    btLoading.value[k] = true
    btErrors.value[k]  = null

    try {
      const result = await aiApi.getBacktest(broker, symbol, riskProfile)
      backtests.value[k] = result
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to fetch signal analysis'
      btErrors.value[k] = message
    } finally {
      btLoading.value[k] = false
    }
  }

  // ── Shared invalidation ───────────────────────────────────────────────────

  function invalidate(broker: string, symbol: string): void {
    const k = _key(broker, symbol)
    delete recommendations.value[k]
    delete errors.value[k]
    delete backtests.value[k]
    delete btErrors.value[k]
  }

  return {
    recommendations,
    backtests,
    loading,
    errors,
    btLoading,
    btErrors,
    getRecommendation,
    isLoading,
    getError,
    fetchRecommendation,
    getBacktest,
    isBacktestLoading,
    getBacktestError,
    fetchBacktest,
    invalidate,
  }
})
