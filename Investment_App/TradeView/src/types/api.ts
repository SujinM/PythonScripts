// ─── Generic API Response ─────────────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  data: T
  message?: string
  status: number
}

export interface ApiError {
  message: string
  status: number
  code?: string
  details?: Record<string, string[]>
}

// ─── Sync ─────────────────────────────────────────────────────────────────────

export interface SyncStatus {
  isRunning: boolean
  progress: number // 0-100
  startedAt?: string
  completedAt?: string
  itemsProcessed?: number
  totalItems?: number
  errors?: string[]
  lastSyncAt?: string
  lastSyncDuration?: number // seconds
}

export interface SyncLog {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error'
  message: string
  symbol?: string
}

// ─── Notification ─────────────────────────────────────────────────────────────

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message?: string
  duration?: number // ms; 0 = persist until dismissed
  timestamp: number
}
