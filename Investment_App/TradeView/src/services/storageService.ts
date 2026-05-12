import { STORAGE_KEYS } from '@/utils/constants'

// ─── Storage Service ──────────────────────────────────────────────────────────

export const storageService = {
  get<T>(key: string, fallback?: T): T | undefined {
    try {
      const raw = localStorage.getItem(key)
      if (raw === null) return fallback
      return JSON.parse(raw) as T
    } catch {
      return fallback
    }
  },

  set(key: string, value: unknown): void {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch { /* quota exceeded — silently fail */ }
  },

  remove(key: string): void {
    localStorage.removeItem(key)
  },

  clear(): void {
    Object.values(STORAGE_KEYS).forEach((k) => localStorage.removeItem(k))
  },
}
