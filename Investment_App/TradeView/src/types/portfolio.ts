// ─── Portfolio Types ─────────────────────────────────────────────────────────
// Mirrors app/models/portfolio.py and app/models/responses.py in the FastAPI backend.
// Endpoint pattern: GET /api/v1/{broker}/<resource>

export interface Holding {
  broker: string
  instrument_key: string
  trading_symbol: string
  exchange: string
  isin: string | null
  quantity: number
  average_price: number
  last_price: number
  close_price: number
  // computed fields returned by backend
  invested_value: number
  current_value: number
  unrealised_pnl: number
  return_pct: number
}

export interface Position {
  broker: string
  instrument_key: string
  trading_symbol: string
  exchange: string
  product: string
  quantity: number
  buy_price: number
  sell_price: number
  last_price: number
  realised_pnl: number
  unrealised_pnl: number
  total_pnl: number
}

export interface Trade {
  broker: string
  instrument_key: string
  trading_symbol: string
  exchange: string
  product: string
  transaction_type: 'BUY' | 'SELL'
  quantity: number
  price: number
  trade_date: string | null
  trade_value: number
}

export interface PortfolioSummary {
  broker: string
  holdings_count: number
  positions_count: number
  total_invested: number
  total_current_value: number
  total_unrealised_pnl: number
  total_realised_pnl: number
  overall_return_pct: number
  top_gainers: Holding[]
  top_losers: Holding[]
}

export interface Alert {
  symbol: string
  type: string
  message: string
  severity?: 'low' | 'medium' | 'high'
}

export interface AnalysisResult {
  broker: string
  holdings_count: number
  total_invested: number
  total_current_value: number
  total_pnl: number
  overall_return_pct: number
  top_gainers: Holding[]
  top_losers: Holding[]
  alerts: Alert[]
}

export interface BrokerInfo {
  id: string
  name: string
  description?: string
}

// ─── Live Tick Types (WS /api/v1/{broker}/ws/live) ───────────────────────────

export interface UpstoxTick {
  ltp: number
  close: number
  ts: number
}

export interface EToroTick {
  name: string
  bid: number | null
  ask: number | null
  /** Pre-computed mid price from the backend — always use this, never (bid+ask)/2.
   *  When eToro pushes only one side, ask or bid may be null, which would
   *  silently halve the price in JS arithmetic. The backend null-checks both. */
  mid: number | null
  ts: number
}

export type Tick = UpstoxTick | EToroTick

export interface LiveTickFrame {
  broker: string
  ticks?: Record<string, Tick>
  error?: string
  ts: number
}

// ─── API Response Envelope ───────────────────────────────────────────────────
// Matches: { "status": "success", "data": <payload> }

export interface ApiEnvelope<T> {
  status: 'success' | 'error'
  data: T
}
