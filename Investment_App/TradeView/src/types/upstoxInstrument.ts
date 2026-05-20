// src/types/upstoxInstrument.ts

export interface UpstoxInstrument {
  instrument_key:  string
  trading_symbol:  string
  name:            string
  exchange:        string
  segment:         string
  segment_label:   string | null
  instrument_type: string | null
  isin:            string | null
  lot_size:        number | null
  tick_size:       number | null
  freeze_quantity: number | null
  exchange_token:  string | null
  qty_multiplier:  number | null
  synced_at:       string | null
}

export interface PaginatedUpstoxInstruments {
  data:        UpstoxInstrument[]
  total:       number
  page:        number
  page_size:   number
  total_pages: number
}

export interface UpstoxSyncResult {
  total:    number
  inserted: number
  updated:  number
  message:  string
}

export interface UpstoxInstrumentFilters {
  search?:   string
  segment?:  string | null
  exchange?: string | null
}

export const UPSTOX_SEGMENTS: Record<string, string> = {
  BSE_EQ:           'BSE Equity',
  BSE_FO:           'BSE F&O',
  BSE_INDEX:        'BSE Index',
  NSE_EQ:           'NSE Equity',
  NSE_FO:           'NSE F&O',
  NSE_INDEX:        'NSE Index',
  NSE_COM:          'NSE Commodities',
  MCX_FO:           'MCX F&O',
  NCD_FO:           'NCD F&O',
  BCD_FO:           'BCD F&O',
  GLOBAL_INDEX:     'Global Index',
  GLOBAL_INDICATOR: 'Global Indicator',
}

export const UPSTOX_EXCHANGES = ['BSE', 'NSE', 'MCX', 'GLOBAL']
