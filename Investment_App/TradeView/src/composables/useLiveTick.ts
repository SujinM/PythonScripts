import { ref, onUnmounted } from 'vue'
import type { LiveTickFrame } from '@/types/portfolio'
import { usePortfolioStore } from '@/stores/portfolioStore'

const RECONNECT_BASE_MS = 3_000      // first retry after 3 s
const RECONNECT_MAX_MS  = 300_000    // cap at 5 min

/**
 * Composable that opens a WebSocket to:
 *   ws://<host>/api/v1/{broker}/ws/live[?instruments=KEY1,KEY2,...]
 *
 * Mirrors ClientConsolApp/Services/LiveTickService.cs — automatically
 * reconnects on disconnect and pushes frames into the portfolio store.
 *
 * Usage:
 *   const { isConnected, connect, disconnect } = useLiveTick('upstox')
 *   connect()
 */
export function useLiveTick(broker: string, instruments: string[] = []) {
  const portfolio    = usePortfolioStore()
  const isConnected  = ref(false)
  const lastError    = ref<string | null>(null)
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let stableTimer: ReturnType<typeof setTimeout> | null = null   // resets backoff after sustained connection
  let stopped = false
  let reconnectAttempts = 0          // tracks consecutive failures for backoff
  let refreshTimer: ReturnType<typeof setTimeout> | null = null  // debounce refreshAll

  function resolveInstruments(): string[] {
    if (instruments.length) return instruments
    const holdings = portfolio.holdings[broker] ?? []
    return [...new Set(holdings.map((holding) => holding.instrument_key).filter(Boolean))]
  }

  function buildUrl(): string {
    const base = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
    const wsBase = base.replace(/^http/, 'ws')
    const path = `/api/v1/${broker}/ws/live`
    const resolvedInstruments = resolveInstruments()
    const query = resolvedInstruments.length ? `?instruments=${resolvedInstruments.join(',')}` : ''
    return `${wsBase}${path}${query}`
  }

  function connect() {
    stopped = false // allow re-connect after an explicit disconnect()
    if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) return

    const url = buildUrl()
    ws = new WebSocket(url)

    ws.onopen = () => {
      isConnected.value = true
      lastError.value = null

      // Only reset backoff after staying connected for 10 s.
      // If the server accepts then immediately closes (e.g. auth 401),
      // onopen fires BEFORE onclose — so resetting here would defeat backoff.
      stableTimer = setTimeout(() => { reconnectAttempts = 0 }, 10_000)

      // Debounced refreshAll — only fires once per 10 s even if WS reconnects
      // rapidly (e.g. backend restart). Prevents flooding the server with
      // repeated holdings/summary/positions calls during auth-error loops.
      if (!refreshTimer) {
        refreshTimer = setTimeout(() => {
          refreshTimer = null
          portfolio.refreshAll(broker).catch(() => { /* ignore — WS tick will keep updating */ })
        }, 500)
      }
    }

    ws.onmessage = (event) => {
      try {
        const frame: LiveTickFrame = JSON.parse(event.data as string)
        if (frame.error) {
          lastError.value = frame.error
        } else {
          lastError.value = null
          portfolio.applyTickFrame(frame)
        }
      } catch { /* ignore malformed frames */ }
    }

    ws.onclose = (event) => {
      isConnected.value = false
      stableTimer && clearTimeout(stableTimer)
      stableTimer = null

      // 4004 = broker not supported — fatal, never reconnect
      if (stopped || event.code === 4004) return

      // Exponential backoff: 3 s → 6 s → 12 s → 24 s → … → 5 min cap
      // This prevents flooding the backend when auth is failing (code 4000)
      // or the server is temporarily unavailable.
      const delay = Math.min(RECONNECT_BASE_MS * 2 ** reconnectAttempts, RECONNECT_MAX_MS)
      reconnectAttempts++
      reconnectTimer = setTimeout(connect, delay)
    }

    ws.onerror = () => {
      lastError.value = `WebSocket error — broker: ${broker}`
      ws?.close()
    }
  }

  function disconnect() {
    stopped = true
    reconnectTimer && clearTimeout(reconnectTimer)
    stableTimer    && clearTimeout(stableTimer)
    refreshTimer   && clearTimeout(refreshTimer)
    ws?.close()
    isConnected.value = false
  }

  onUnmounted(disconnect)

  return { isConnected, lastError, connect, disconnect }
}
