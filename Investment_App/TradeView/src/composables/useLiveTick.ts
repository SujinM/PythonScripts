import { ref, onUnmounted } from 'vue'
import type { LiveTickFrame } from '@/types/portfolio'
import { usePortfolioStore } from '@/stores/portfolioStore'

const RECONNECT_DELAY_MS = 3_000

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
  let stopped = false

  function buildUrl(): string {
    const base = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
    const wsBase = base.replace(/^http/, 'ws')
    const path = `/api/v1/${broker}/ws/live`
    const query = instruments.length ? `?instruments=${instruments.join(',')}` : ''
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

    ws.onclose = () => {
      isConnected.value = false
      if (!stopped) {
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS)
      }
    }

    ws.onerror = () => {
      lastError.value = `WebSocket error — broker: ${broker}`
      ws?.close()
    }
  }

  function disconnect() {
    stopped = true
    reconnectTimer && clearTimeout(reconnectTimer)
    ws?.close()
    isConnected.value = false
  }

  onUnmounted(disconnect)

  return { isConnected, lastError, connect, disconnect }
}
