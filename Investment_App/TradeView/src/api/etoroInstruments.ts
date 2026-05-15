// src/api/etoroInstruments.ts

import api from './index'
import type {
  EtoroInstrument,
  EtoroInstrumentFilters,
  PaginatedEtoroInstruments,
  SyncResult,
} from '@/types/etoroInstrument'

export interface EtoroListParams extends EtoroInstrumentFilters {
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export const etoroInstrumentsApi = {
  /** GET /api/v1/etoro/instruments */
  async getInstruments(params?: EtoroListParams): Promise<PaginatedEtoroInstruments> {
    const { data } = await api.get<PaginatedEtoroInstruments>('/api/v1/etoro/instruments', { params })
    return data
  },

  /** GET /api/v1/etoro/instruments/{id} */
  async getInstrument(instrumentId: number): Promise<EtoroInstrument> {
    const { data } = await api.get<EtoroInstrument>(`/api/v1/etoro/instruments/${instrumentId}`)
    return data
  },

  /** POST /api/v1/etoro/instruments/sync */
  async syncInstruments(): Promise<SyncResult> {
    const { data } = await api.post<SyncResult>('/api/v1/etoro/instruments/sync')
    return data
  },
}
