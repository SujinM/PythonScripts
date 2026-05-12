import api from './index'
import type { Instrument, InstrumentFilter, PaginationParams, PaginatedResponse } from '@/types/instrument'

// ─── Instruments API ──────────────────────────────────────────────────────────

export const instrumentsApi = {
  /** GET /instruments — paginated, filtered list */
  async getInstruments(
    params?: Partial<InstrumentFilter & PaginationParams>,
  ): Promise<PaginatedResponse<Instrument>> {
    const { data } = await api.get<PaginatedResponse<Instrument>>('/instruments', { params })
    return data
  },

  /** GET /instruments/{symbol} — single instrument details */
  async getInstrument(symbol: string): Promise<Instrument> {
    const { data } = await api.get<Instrument>(`/instruments/${symbol}`)
    return data
  },

  /** GET /sync-instruments — trigger a manual sync */
  async syncInstruments(): Promise<{ message: string; taskId?: string }> {
    const { data } = await api.get<{ message: string; taskId?: string }>('/sync-instruments')
    return data
  },
}
