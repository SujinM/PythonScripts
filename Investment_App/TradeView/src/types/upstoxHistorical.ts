// src/types/upstoxHistorical.ts

export interface UpstoxCandleBar {
  timestamp: string
  open:      number
  high:      number
  low:       number
  close:     number
  volume:    number
  oi:        number
}

export interface UpstoxHistoricalResponse {
  instrument_key: string
  unit:           string
  interval:       string
  candles:        UpstoxCandleBar[]
}

// ── Selector config ───────────────────────────────────────────────────────────

export type HistoricalUnit = 'minutes' | 'hours' | 'days' | 'weeks' | 'months'

export interface IntervalOption {
  label:    string
  unit:     HistoricalUnit
  interval: string
}

/** Preset timeframe buttons shown in the toolbar */
export const TIMEFRAME_PRESETS: IntervalOption[] = [
  { label: '1m',   unit: 'minutes', interval: '1'  },
  { label: '5m',   unit: 'minutes', interval: '5'  },
  { label: '15m',  unit: 'minutes', interval: '15' },
  { label: '30m',  unit: 'minutes', interval: '30' },
  { label: '1H',   unit: 'hours',   interval: '1'  },
  { label: '4H',   unit: 'hours',   interval: '4'  },
  { label: '1D',   unit: 'days',    interval: '1'  },
  { label: '1W',   unit: 'weeks',   interval: '1'  },
  { label: '1Mo',  unit: 'months',  interval: '1'  },
]

/** Default from_date offsets (days) per unit for a sensible initial range */
export const DEFAULT_RANGE_DAYS: Record<HistoricalUnit, number> = {
  minutes: 1,
  hours:   7,
  days:    90,
  weeks:   365,
  months:  1825,  // 5 years
}
