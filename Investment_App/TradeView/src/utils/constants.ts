import type { AssetType } from '@/types/instrument'

// ─── Asset Types ──────────────────────────────────────────────────────────────

export const ASSET_TYPES: { value: AssetType; label: string; color: string; bgColor: string }[] = [
  { value: 'STOCKS', label: 'Stocks', color: '#3b82f6', bgColor: 'bg-blue-500/10 text-blue-400' },
  { value: 'CRYPTO', label: 'Crypto', color: '#f59e0b', bgColor: 'bg-amber-500/10 text-amber-400' },
  { value: 'FOREX', label: 'Forex', color: '#10b981', bgColor: 'bg-emerald-500/10 text-emerald-400' },
  { value: 'INDICES', label: 'Indices', color: '#8b5cf6', bgColor: 'bg-violet-500/10 text-violet-400' },
  { value: 'COMMODITIES', label: 'Commodities', color: '#f97316', bgColor: 'bg-orange-500/10 text-orange-400' },
  { value: 'ETFS', label: 'ETFs', color: '#06b6d4', bgColor: 'bg-cyan-500/10 text-cyan-400' },
]

// ─── Exchanges ────────────────────────────────────────────────────────────────

export const EXCHANGES = [
  'NASDAQ',
  'NYSE',
  'CRYPTO',
  'FOREX',
  'INDICES',
  'COMMODITIES',
  'LSE',
  'EURONEXT',
  'TSX',
  'ASX',
] as const

export type Exchange = (typeof EXCHANGES)[number]

// ─── Pagination ───────────────────────────────────────────────────────────────

export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]
export const DEFAULT_PAGE_SIZE = 20

// ─── Chart Timeframes ─────────────────────────────────────────────────────────

export const CHART_TIMEFRAMES = [
  { value: '1D', label: '1 Day', days: 1 },
  { value: '1W', label: '1 Week', days: 7 },
  { value: '1M', label: '1 Month', days: 30 },
  { value: '3M', label: '3 Months', days: 90 },
  { value: '6M', label: '6 Months', days: 180 },
  { value: '1Y', label: '1 Year', days: 365 },
] as const

// ─── Colors for Charts ────────────────────────────────────────────────────────

export const CHART_COLORS = [
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#10b981', // emerald
  '#8b5cf6', // violet
  '#f97316', // orange
  '#06b6d4', // cyan
  '#ec4899', // pink
  '#84cc16', // lime
]

// ─── Local Storage Keys ───────────────────────────────────────────────────────

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'etoro_access_token',
  REFRESH_TOKEN: 'etoro_refresh_token',
  USER: 'etoro_user',
  THEME: 'etoro_theme',
  WATCHLIST: 'etoro_watchlist',
  SIDEBAR_COLLAPSED: 'etoro_sidebar_collapsed',
  LOCALE: 'etoro_locale',
} as const

// ─── WebSocket Events ─────────────────────────────────────────────────────────

export const WS_EVENTS = {
  PRICE_UPDATE: 'price_update',
  SYNC_PROGRESS: 'sync_progress',
  SYNC_COMPLETE: 'sync_complete',
  SYNC_ERROR: 'sync_error',
} as const

// ─── Auto-refresh Intervals ───────────────────────────────────────────────────

export const REFRESH_INTERVALS = {
  MARKET_DATA: 30_000,  // 30 seconds
  STATISTICS: 60_000,   // 1 minute
  SYNC_STATUS: 5_000,   // 5 seconds
} as const
