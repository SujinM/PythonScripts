// src/api/upstoxInstruments.ts

import api from './index'
import type {
  UpstoxInstrument,
  UpstoxInstrumentFilters,
  PaginatedUpstoxInstruments,
  UpstoxSyncResult,
} from '@/types/upstoxInstrument'

export interface UpstoxListParams extends UpstoxInstrumentFilters {
  page?:       number
  page_size?:  number
  sort_by?:    string
  sort_order?: 'asc' | 'desc'
}

export const upstoxInstrumentsApi = {
  /** GET /api/v1/upstox/instruments */
  async getInstruments(params?: UpstoxListParams): Promise<PaginatedUpstoxInstruments> {
    const { data } = await api.get<PaginatedUpstoxInstruments>('/api/v1/upstox/instruments', { params })
    return data
  },

  /** GET /api/v1/upstox/instruments/{key} */
  async getInstrument(instrumentKey: string): Promise<UpstoxInstrument> {
    const { data } = await api.get<UpstoxInstrument>(
      `/api/v1/upstox/instruments/${encodeURIComponent(instrumentKey)}`
    )
    return data
  },

  /** POST /api/v1/upstox/instruments/sync */
  async syncInstruments(): Promise<UpstoxSyncResult> {
    // Large file — allow up to 5 minutes
    const { data } = await api.post<UpstoxSyncResult>('/api/v1/upstox/instruments/sync', null, {
      timeout: 300_000,
    })
    return data
  },
}
