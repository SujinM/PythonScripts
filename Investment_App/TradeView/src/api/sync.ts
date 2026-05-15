import api from './index'
import type { SyncStatus, SyncLog } from '@/types/api'

// ─── Sync API ─────────────────────────────────────────────────────────────────

export const syncApi = {
  /** GET /api/v1/sync-instruments — kick off an instrument sync */
  async triggerSync(): Promise<{ message: string; taskId?: string }> {
    const { data } = await api.get<{ message: string; taskId?: string }>('/api/v1/sync-instruments')
    return data
  },

  /** GET /api/v1/sync-status — current sync progress */
  async getSyncStatus(): Promise<SyncStatus> {
    const { data } = await api.get<SyncStatus>('/api/v1/sync-status')
    return data
  },

  /** GET /api/v1/sync-logs — recent sync log entries */
  async getSyncLogs(limit = 50): Promise<SyncLog[]> {
    const { data } = await api.get<SyncLog[]>('/api/v1/sync-logs', { params: { limit } })
    return data
  },
}
