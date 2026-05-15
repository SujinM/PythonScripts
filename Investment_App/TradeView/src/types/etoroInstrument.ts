// src/types/etoroInstrument.ts

export interface EtoroInstrument {
  instrument_id: number
  symbol: string
  display_name: string
  instrument_type_id: number | null
  instrument_type: string | null
  exchange_id: number | null
  price_source: string | null
  has_expiration_date: boolean
  is_internal: boolean
  distribution_type: number | null
  image_url: string | null
  synced_at: string | null
}

export interface PaginatedEtoroInstruments {
  data: EtoroInstrument[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface SyncResult {
  total: number
  inserted: number
  updated: number
  message: string
}

export interface EtoroInstrumentFilters {
  search?: string
  instrument_type_id?: number | null
  exchange_id?: number | null
}

export const ETORO_INSTRUMENT_TYPES: Record<number, string> = {
  1:  'Forex',
  2:  'Commodities',
  4:  'Indices',
  5:  'Stocks',
  6:  'ETFs',
  10: 'Crypto',
}
