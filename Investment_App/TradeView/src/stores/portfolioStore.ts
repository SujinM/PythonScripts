import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Holding,
  Position,
  Trade,
  PortfolioSummary,
  AnalysisResult,
  Alert,
  BrokerInfo,
  LiveTickFrame,
} from '@/types/portfolio'
import { portfolioApi } from '@/api/portfolio'
import { useNotificationStore } from './notificationStore'

// ─── Portfolio Store ──────────────────────────────────────────────────────────
// Central state for all data from the FastAPI backend.
// Mirrors the ClientConsolApp flow: select broker → fetch holdings/summary/etc.

export const usePortfolioStore = defineStore('portfolio', () => {
  const notifications = useNotificationStore()

  // ── Broker state ────────────────────────────────────────────────────────
  const brokers        = ref<BrokerInfo[]>([])
  const activeBroker   = ref<string>('upstox')

  // ── Portfolio data (keyed by broker id) ─────────────────────────────────
  const holdings   = ref<Record<string, Holding[]>>({})
  const positions  = ref<Record<string, Position[]>>({})
  const trades     = ref<Record<string, Trade[]>>({})
  const summaries  = ref<Record<string, PortfolioSummary>>({})
  const analyses   = ref<Record<string, AnalysisResult>>({})
  const alerts     = ref<Record<string, Alert[]>>({})

  // ── Live tick data ───────────────────────────────────────────────────────
  const liveTicks = ref<Record<string, LiveTickFrame['ticks']>>({})

  // ── Loading / error ──────────────────────────────────────────────────────
  const loading = ref(false)
  const error   = ref<string | null>(null)

  // ── Computed shortcuts (active broker) ──────────────────────────────────
  const activeHoldings  = computed(() => holdings.value[activeBroker.value]  ?? [])
  const activePositions = computed(() => positions.value[activeBroker.value] ?? [])
  const activeTrades    = computed(() => trades.value[activeBroker.value]    ?? [])
  const activeSummary   = computed(() => summaries.value[activeBroker.value] ?? null)
  const activeAnalysis  = computed(() => analyses.value[activeBroker.value]  ?? null)
  const activeAlerts    = computed(() => alerts.value[activeBroker.value]    ?? [])
  const activeLiveTicks = computed(() => liveTicks.value[activeBroker.value] ?? {})
  const activeCurrency  = computed(() => activeBroker.value === 'etoro' ? 'USD' : 'INR')

  // ── Actions ──────────────────────────────────────────────────────────────

  /** Load the list of registered brokers from the backend. */
  async function fetchBrokers() {
    try {
      brokers.value = await portfolioApi.getBrokers()
      if (brokers.value.length && !brokers.value.find((b) => b.id === activeBroker.value)) {
        activeBroker.value = brokers.value[0].id
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load brokers'
      notifications.error('Broker list error', msg)
    }
  }

  /** Set the active broker and pre-load its summary. */
  async function selectBroker(brokerId: string) {
    activeBroker.value = brokerId
    await fetchSummary(brokerId)
  }

  /** GET /api/v1/{broker}/summary */
  async function fetchSummary(broker = activeBroker.value) {
    loading.value = true
    error.value = null
    try {
      summaries.value[broker] = await portfolioApi.getSummary(broker)
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : `Failed to fetch summary for ${broker}`
      notifications.error('Summary error', error.value)
    } finally {
      loading.value = false
    }
  }

  /** GET /api/v1/{broker}/holdings */
  async function fetchHoldings(broker = activeBroker.value) {
    loading.value = true
    error.value = null
    try {
      holdings.value[broker] = await portfolioApi.getHoldings(broker)
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : `Failed to fetch holdings for ${broker}`
      notifications.error('Holdings error', error.value)
    } finally {
      loading.value = false
    }
  }

  /** GET /api/v1/{broker}/positions */
  async function fetchPositions(broker = activeBroker.value) {
    loading.value = true
    error.value = null
    try {
      positions.value[broker] = await portfolioApi.getPositions(broker)
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : `Failed to fetch positions for ${broker}`
      notifications.error('Positions error', error.value)
    } finally {
      loading.value = false
    }
  }

  /** GET /api/v1/{broker}/trades */
  async function fetchTrades(broker = activeBroker.value) {
    loading.value = true
    error.value = null
    try {
      trades.value[broker] = await portfolioApi.getTrades(broker)
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : `Failed to fetch trades for ${broker}`
      notifications.error('Trades error', error.value)
    } finally {
      loading.value = false
    }
  }

  /** GET /api/v1/{broker}/analysis */
  async function fetchAnalysis(broker = activeBroker.value) {
    loading.value = true
    error.value = null
    try {
      analyses.value[broker] = await portfolioApi.getAnalysis(broker)
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : `Failed to fetch analysis for ${broker}`
      notifications.error('Analysis error', error.value)
    } finally {
      loading.value = false
    }
  }

  /** GET /api/v1/{broker}/analysis/alerts */
  async function fetchAlerts(broker = activeBroker.value) {
    try {
      alerts.value[broker] = await portfolioApi.getAlerts(broker)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : `Failed to fetch alerts for ${broker}`
      notifications.error('Alerts error', msg)
    }
  }

  /** POST /api/v1/{broker}/cache/invalidate — then reload summary + holdings */
  async function invalidateCache(broker = activeBroker.value) {
    loading.value = true
    try {
      const result = await portfolioApi.invalidateCache(broker)
      notifications.success('Cache cleared', result.message)
      await Promise.all([fetchSummary(broker), fetchHoldings(broker)])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to invalidate cache'
      notifications.error('Cache error', msg)
    } finally {
      loading.value = false
    }
  }

  /** Push a live tick frame received from the WebSocket. */
  function applyTickFrame(frame: LiveTickFrame) {
    if (frame.ticks) {
      liveTicks.value[frame.broker] = {
        ...(liveTicks.value[frame.broker] ?? {}),
        ...frame.ticks,
      }
    }
  }

  /** Refresh all data for the active broker (used by auto-refresh). */
  async function refreshAll(broker = activeBroker.value) {
    await Promise.all([
      fetchSummary(broker),
      fetchHoldings(broker),
      fetchPositions(broker),
    ])
  }

  return {
    // state
    brokers,
    activeBroker,
    holdings,
    positions,
    trades,
    summaries,
    analyses,
    alerts,
    liveTicks,
    loading,
    error,
    // computed
    activeHoldings,
    activePositions,
    activeTrades,
    activeSummary,
    activeAnalysis,
    activeAlerts,
    activeLiveTicks,
    activeCurrency,
    // actions
    fetchBrokers,
    selectBroker,
    fetchSummary,
    fetchHoldings,
    fetchPositions,
    fetchTrades,
    fetchAnalysis,
    fetchAlerts,
    invalidateCache,
    applyTickFrame,
    refreshAll,
  }
})
