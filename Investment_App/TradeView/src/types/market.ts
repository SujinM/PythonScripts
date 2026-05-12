import type { Instrument } from './instrument'

// ─── Market Data ──────────────────────────────────────────────────────────────

export interface MarketData {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  high24h: number
  low24h: number
  marketCap?: number
  open?: number
  previousClose?: number
  timestamp: string
}

// ─── OHLCV Candle ─────────────────────────────────────────────────────────────

export interface Candle {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// ─── Statistics ───────────────────────────────────────────────────────────────

export interface Statistics {
  totalInstruments: number
  totalExchanges: number
  totalTradable: number
  assetTypeBreakdown: Record<string, number>
  exchangeBreakdown: Record<string, number>
  recentlyUpdated: Instrument[]
  topActiveSymbols: MarketData[]
  lastSyncAt: string
}

// ─── Watchlist ────────────────────────────────────────────────────────────────

export interface WatchlistItem {
  symbol: string
  addedAt: string
  notes?: string
}
