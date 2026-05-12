import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SyncStatus, SyncLog } from '@/types/api'
import { syncApi } from '@/api/sync'
import { generateMockSyncLogs } from '@/utils/mockData'
import { useNotificationStore } from './notificationStore'

const useMock = import.meta.env.VITE_MOCK_DATA === 'true'

// ─── Sync Store ───────────────────────────────────────────────────────────────

export const useSyncStore = defineStore('sync', () => {
  const notifications = useNotificationStore()

  const status    = ref<SyncStatus>({ isRunning: false, progress: 0 })
  const logs      = ref<SyncLog[]>([])
  const loading   = ref(false)
  let   pollTimer: ReturnType<typeof setInterval> | null = null

  // ─── Mock sync simulation ──────────────────────────────────────────────────

  async function _runMockSync() {
    status.value = { isRunning: true, progress: 0, startedAt: new Date().toISOString(), totalItems: 791 }
    logs.value = []

    const steps = [
      { msg: 'Connecting to eToro API…', level: 'info' as const },
      { msg: 'Fetching STOCKS (456 items)…', level: 'info' as const },
      { msg: 'Fetching CRYPTO (78 items)…', level: 'info' as const },
      { msg: 'Rate limit warning — throttling requests', level: 'warning' as const },
      { msg: 'Fetching FOREX (47 items)…', level: 'info' as const },
      { msg: 'Fetching INDICES (23 items)…', level: 'info' as const },
      { msg: 'Fetching COMMODITIES (31 items)…', level: 'info' as const },
      { msg: 'Fetching ETFS (156 items)…', level: 'info' as const },
      { msg: 'Upserting records to database…', level: 'info' as const },
      { msg: 'Sync completed successfully — 791 instruments updated', level: 'info' as const },
    ]

    for (let i = 0; i < steps.length; i++) {
      await new Promise((r) => setTimeout(r, 600 + Math.random() * 400))
      const step = steps[i]
      status.value.progress = Math.round(((i + 1) / steps.length) * 100)
      status.value.itemsProcessed = Math.round((status.value.totalItems! * status.value.progress) / 100)
      logs.value.push({
        id: `log-${Date.now()}`,
        timestamp: new Date().toISOString(),
        level: step.level,
        message: step.msg,
      })
    }

    status.value.isRunning = false
    status.value.progress = 100
    status.value.completedAt = new Date().toISOString()
    status.value.lastSyncAt = status.value.completedAt
    notifications.success('Sync complete', '791 instruments updated successfully')
  }

  // ─── Actions ──────────────────────────────────────────────────────────────

  async function triggerSync() {
    if (status.value.isRunning) return

    loading.value = true
    try {
      if (useMock) {
        loading.value = false
        notifications.info('Sync started', 'Synchronising instruments…')
        _runMockSync()
        return
      }
      await syncApi.triggerSync()
      notifications.info('Sync started', 'Synchronising instruments…')
      startPolling()
    } catch (err: unknown) {
      notifications.error('Sync failed', err instanceof Error ? err.message : 'Unknown error')
    } finally {
      loading.value = false
    }
  }

  async function fetchStatus() {
    try {
      if (!useMock) {
        status.value = await syncApi.getSyncStatus()
        if (!status.value.isRunning) stopPolling()
      }
    } catch { /* silent */ }
  }

  async function fetchLogs() {
    try {
      if (useMock) {
        logs.value = generateMockSyncLogs(25)
      } else {
        logs.value = await syncApi.getSyncLogs()
      }
    } catch { /* silent */ }
  }

  function startPolling(intervalMs = 3000) {
    if (pollTimer) return
    pollTimer = setInterval(fetchStatus, intervalMs)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return { status, logs, loading, triggerSync, fetchStatus, fetchLogs, startPolling, stopPolling }
})
