// ─── Instrument Types ────────────────────────────────────────────────────────

export type AssetType = 'STOCKS' | 'CRYPTO' | 'FOREX' | 'INDICES' | 'COMMODITIES' | 'ETFS'

export interface Instrument {
  instrumentId: number
  symbol: string
  displayName: string
  exchange: string
  assetType: AssetType
  currency: string
  isTradable: boolean
  minPositionAmount?: number
  maxPositionAmount?: number
  leverage?: number
  spreadFixed?: number
  spreadPercent?: number
  createdAt?: string
  updatedAt?: string
}

// ─── Filter / Pagination ──────────────────────────────────────────────────────

export interface InstrumentFilter {
  search?: string
  exchange?: string
  assetType?: AssetType | ''
  isTradable?: boolean
}

export type SortOrder = 'asc' | 'desc'

export interface PaginationParams {
  page: number
  pageSize: number
  sortBy?: keyof Instrument
  sortOrder?: SortOrder
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// ─── Table Column ─────────────────────────────────────────────────────────────

export interface TableColumn<T = Instrument> {
  key: keyof T | string
  label: string
  sortable?: boolean
  width?: string
  align?: 'left' | 'center' | 'right'
  formatter?: (value: unknown, row: T) => string
}
