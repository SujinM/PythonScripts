import { ref, onUnmounted } from 'vue'
import { WS_EVENTS } from '@/utils/constants'

type WsMessage = {
  event: string
  data: unknown
}

/**
 * Composable for WebSocket connection to the FastAPI backend.
 * Handles reconnection and exposes typed message handlers.
 */
export function useWebSocket(url?: string) {
  const wsUrl       = url ?? import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws'
  const isConnected = ref(false)
  const lastMessage = ref<WsMessage | null>(null)
  let   ws: WebSocket | null = null
  let   reconnectTimer: ReturnType<typeof setTimeout> | null = null
  const handlers   = new Map<string, Set<(data: unknown) => void>>()

  function connect() {
    if (import.meta.env.VITE_MOCK_DATA === 'true') return // Skip WebSocket in mock mode

    ws = new WebSocket(wsUrl)

    ws.onopen = () => { isConnected.value = true }

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data as string)
        lastMessage.value = msg
        handlers.get(msg.event)?.forEach((cb) => cb(msg.data))
      } catch { /* ignore malformed frames */ }
    }

    ws.onclose = () => {
      isConnected.value = false
      // Auto-reconnect after 5 s
      reconnectTimer = setTimeout(connect, 5000)
    }

    ws.onerror = () => { ws?.close() }
  }

  function disconnect() {
    reconnectTimer && clearTimeout(reconnectTimer)
    ws?.close()
    isConnected.value = false
  }

  function on(event: string, handler: (data: unknown) => void) {
    if (!handlers.has(event)) handlers.set(event, new Set())
    handlers.get(event)!.add(handler)
  }

  function off(event: string, handler: (data: unknown) => void) {
    handlers.get(event)?.delete(handler)
  }

  function send(payload: WsMessage) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload))
    }
  }

  onUnmounted(disconnect)

  return { isConnected, lastMessage, connect, disconnect, on, off, send, WS_EVENTS }
}
