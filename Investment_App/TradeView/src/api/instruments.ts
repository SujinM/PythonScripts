import api from './index'
import type { Instrument, InstrumentFilter, PaginationParams, PaginatedResponse } from '@/types/instrument'

// ─── Instruments API ──────────────────────────────────────────────────────────

export const instrumentsApi = {
  /** GET /api/v1/instruments — paginated, filtered list */
  async getInstruments(
    params?: Partial<InstrumentFilter & PaginationParams>,
  ): Promise<PaginatedResponse<Instrument>> {
    const { data } = await api.get<PaginatedResponse<Instrument>>('/api/v1/instruments', { params })
    return data
  },

  /** GET /api/v1/instruments/{symbol} — single instrument details */
  async getInstrument(symbol: string): Promise<Instrument> {
    const { data } = await api.get<Instrument>(`/api/v1/instruments/${symbol}`)
    return data
  },

  /** GET /api/v1/sync-instruments — trigger a manual sync */
  async syncInstruments(): Promise<{ message: string; taskId?: string }> {
    const { data } = await api.get<{ message: string; taskId?: string }>('/api/v1/sync-instruments')
    return data
  },
}
