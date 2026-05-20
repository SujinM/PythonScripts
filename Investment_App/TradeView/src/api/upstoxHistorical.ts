// src/api/upstoxHistorical.ts

import api from './index'
import type { UpstoxHistoricalResponse } from '@/types/upstoxHistorical'

export interface HistoricalParams {
  instrumentKey: string
  unit:          string
  interval:      string
  toDate:        string   // YYYY-MM-DD
  fromDate?:     string   // YYYY-MM-DD optional
}

export const upstoxHistoricalApi = {
  /**
   * Fetch OHLCV candles via the backend proxy.
   * Instrument keys that contain '|' must be passed as-is — the backend handles encoding.
   */
  getCandles(params: HistoricalParams): Promise<UpstoxHistoricalResponse> {
    const { instrumentKey, unit, interval, toDate, fromDate } = params

    // Build path: /api/v1/upstox/historical/{key}/{unit}/{interval}/{to_date}?from_date=...
    const path = `/api/v1/upstox/historical/${encodeURIComponent(instrumentKey)}/${unit}/${interval}/${toDate}`
    return api
      .get<UpstoxHistoricalResponse>(path, {
        params: fromDate ? { from_date: fromDate } : undefined,
        timeout: 30_000,
      })
      .then((r: { data: UpstoxHistoricalResponse }) => r.data)
  },
}
