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

export interface InstrumentPriceChange {
  instrument_id:   number
  current_price:   number | null
  change_1d_value: number | null
  change_1d_pct:   number | null
  change_1m_value: number | null
  change_1m_pct:   number | null
  change_1y_value: number | null
  change_1y_pct:   number | null
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

  /** GET /api/v1/etoro/instruments/price-changes?instrument_ids=1001,9425 */
  async getPriceChanges(instrumentIds: number[]): Promise<InstrumentPriceChange[]> {
    const { data } = await api.get<InstrumentPriceChange[]>(
      '/api/v1/etoro/instruments/price-changes',
      { params: { instrument_ids: instrumentIds.join(',') } },
    )
    return data
  },

  /** POST /api/v1/etoro/instruments/sync */
  async syncInstruments(): Promise<SyncResult> {
    const { data } = await api.post<SyncResult>('/api/v1/etoro/instruments/sync')
    return data
  },
}
