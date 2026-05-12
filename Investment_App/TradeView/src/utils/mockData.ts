import type { Instrument } from '@/types/instrument'
import type { MarketData, Candle, Statistics } from '@/types/market'
import type { SyncLog } from '@/types/api'

// ─── Base Prices ──────────────────────────────────────────────────────────────

const BASE_PRICES: Record<string, number> = {
  AAPL: 189.5, TSLA: 245.8, AMZN: 178.2, GOOGL: 142.5, MSFT: 378.9,
  NVDA: 495.2, META: 358.1, NFLX: 482.3, JPM: 198.4, GS: 387.6,
  BAC: 32.4, DIS: 91.2, UBER: 62.8, PYPL: 58.9, INTC: 43.7,
  AMD: 168.3, CRM: 256.4, ORCL: 118.7, V: 254.3, MA: 412.6,
  BTC: 43250.0, ETH: 2380.5, BNB: 315.2, ADA: 0.58, SOL: 98.4,
  XRP: 0.62, DOT: 7.82, DOGE: 0.089, AVAX: 36.4, MATIC: 0.84,
  EURUSD: 1.0892, GBPUSD: 1.2734, USDJPY: 149.82, AUDUSD: 0.6589,
  USDCAD: 1.3621, USDCHF: 0.8934, NZDUSD: 0.6123, EURJPY: 163.24,
  SPX500: 4782.5, NDX100: 16893.4, DJ30: 37580.2, FTSE100: 7638.9,
  DAX40: 16752.1, NIKK225: 32876.4,
  GOLD: 2035.8, SILVER: 23.45, OIL: 72.38, NATGAS: 2.54, WHEAT: 598.2,
  SPY: 477.8, QQQ: 408.3, VTI: 233.5, GLD: 192.4, IWM: 198.7,
  TLT: 95.2, EFA: 73.8, VWO: 41.2,
}

// ─── Mock Instruments ─────────────────────────────────────────────────────────

export const MOCK_INSTRUMENTS: Instrument[] = [
  // Stocks — NASDAQ
  { instrumentId: 1,  symbol: 'AAPL',    displayName: 'Apple Inc.',                  exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 2,  symbol: 'TSLA',    displayName: 'Tesla, Inc.',                 exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 3,  symbol: 'AMZN',    displayName: 'Amazon.com Inc.',             exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 4,  symbol: 'GOOGL',   displayName: 'Alphabet Inc.',               exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 5,  symbol: 'MSFT',    displayName: 'Microsoft Corporation',       exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 6,  symbol: 'NVDA',    displayName: 'NVIDIA Corporation',          exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 7,  symbol: 'META',    displayName: 'Meta Platforms Inc.',         exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 8,  symbol: 'NFLX',    displayName: 'Netflix Inc.',                exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 9,  symbol: 'INTC',    displayName: 'Intel Corporation',           exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 10, symbol: 'AMD',     displayName: 'Advanced Micro Devices',      exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 11, symbol: 'CRM',     displayName: 'Salesforce Inc.',             exchange: 'NYSE',        assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 12, symbol: 'ORCL',    displayName: 'Oracle Corporation',          exchange: 'NYSE',        assetType: 'STOCKS', currency: 'USD', isTradable: true },
  // Stocks — NYSE
  { instrumentId: 13, symbol: 'JPM',     displayName: 'JPMorgan Chase & Co.',        exchange: 'NYSE',        assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 14, symbol: 'GS',      displayName: 'Goldman Sachs Group Inc.',    exchange: 'NYSE',        assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 15, symbol: 'BAC',     displayName: 'Bank of America Corp.',       exchange: 'NYSE',        assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 16, symbol: 'DIS',     displayName: 'The Walt Disney Company',     exchange: 'NYSE',        assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 17, symbol: 'UBER',    displayName: 'Uber Technologies Inc.',      exchange: 'NYSE',        assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 18, symbol: 'V',       displayName: 'Visa Inc.',                   exchange: 'NYSE',        assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 19, symbol: 'MA',      displayName: 'Mastercard Incorporated',     exchange: 'NYSE',        assetType: 'STOCKS', currency: 'USD', isTradable: true },
  { instrumentId: 20, symbol: 'PYPL',    displayName: 'PayPal Holdings Inc.',        exchange: 'NASDAQ',      assetType: 'STOCKS', currency: 'USD', isTradable: false },
  // Crypto
  { instrumentId: 21, symbol: 'BTC',     displayName: 'Bitcoin',                     exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  { instrumentId: 22, symbol: 'ETH',     displayName: 'Ethereum',                    exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  { instrumentId: 23, symbol: 'BNB',     displayName: 'Binance Coin',                exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  { instrumentId: 24, symbol: 'ADA',     displayName: 'Cardano',                     exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  { instrumentId: 25, symbol: 'SOL',     displayName: 'Solana',                      exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  { instrumentId: 26, symbol: 'XRP',     displayName: 'Ripple',                      exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  { instrumentId: 27, symbol: 'DOT',     displayName: 'Polkadot',                    exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  { instrumentId: 28, symbol: 'DOGE',    displayName: 'Dogecoin',                    exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  { instrumentId: 29, symbol: 'AVAX',    displayName: 'Avalanche',                   exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  { instrumentId: 30, symbol: 'MATIC',   displayName: 'Polygon',                     exchange: 'CRYPTO',      assetType: 'CRYPTO', currency: 'USD', isTradable: true },
  // Forex
  { instrumentId: 31, symbol: 'EURUSD',  displayName: 'EUR/USD',                     exchange: 'FOREX',       assetType: 'FOREX',  currency: 'USD', isTradable: true },
  { instrumentId: 32, symbol: 'GBPUSD',  displayName: 'GBP/USD',                     exchange: 'FOREX',       assetType: 'FOREX',  currency: 'USD', isTradable: true },
  { instrumentId: 33, symbol: 'USDJPY',  displayName: 'USD/JPY',                     exchange: 'FOREX',       assetType: 'FOREX',  currency: 'JPY', isTradable: true },
  { instrumentId: 34, symbol: 'AUDUSD',  displayName: 'AUD/USD',                     exchange: 'FOREX',       assetType: 'FOREX',  currency: 'USD', isTradable: true },
  { instrumentId: 35, symbol: 'USDCAD',  displayName: 'USD/CAD',                     exchange: 'FOREX',       assetType: 'FOREX',  currency: 'CAD', isTradable: true },
  { instrumentId: 36, symbol: 'USDCHF',  displayName: 'USD/CHF',                     exchange: 'FOREX',       assetType: 'FOREX',  currency: 'CHF', isTradable: true },
  { instrumentId: 37, symbol: 'NZDUSD',  displayName: 'NZD/USD',                     exchange: 'FOREX',       assetType: 'FOREX',  currency: 'USD', isTradable: true },
  { instrumentId: 38, symbol: 'EURJPY',  displayName: 'EUR/JPY',                     exchange: 'FOREX',       assetType: 'FOREX',  currency: 'JPY', isTradable: true },
  // Indices
  { instrumentId: 39, symbol: 'SPX500',  displayName: 'S&P 500',                     exchange: 'INDICES',     assetType: 'INDICES', currency: 'USD', isTradable: true },
  { instrumentId: 40, symbol: 'NDX100',  displayName: 'NASDAQ 100',                  exchange: 'INDICES',     assetType: 'INDICES', currency: 'USD', isTradable: true },
  { instrumentId: 41, symbol: 'DJ30',    displayName: 'Dow Jones 30',                exchange: 'INDICES',     assetType: 'INDICES', currency: 'USD', isTradable: true },
  { instrumentId: 42, symbol: 'FTSE100', displayName: 'FTSE 100',                    exchange: 'INDICES',     assetType: 'INDICES', currency: 'GBP', isTradable: true },
  { instrumentId: 43, symbol: 'DAX40',   displayName: 'DAX 40',                      exchange: 'INDICES',     assetType: 'INDICES', currency: 'EUR', isTradable: true },
  { instrumentId: 44, symbol: 'NIKK225', displayName: 'Nikkei 225',                  exchange: 'INDICES',     assetType: 'INDICES', currency: 'JPY', isTradable: true },
  // Commodities
  { instrumentId: 45, symbol: 'GOLD',    displayName: 'Gold',                        exchange: 'COMMODITIES', assetType: 'COMMODITIES', currency: 'USD', isTradable: true },
  { instrumentId: 46, symbol: 'SILVER',  displayName: 'Silver',                      exchange: 'COMMODITIES', assetType: 'COMMODITIES', currency: 'USD', isTradable: true },
  { instrumentId: 47, symbol: 'OIL',     displayName: 'Crude Oil WTI',               exchange: 'COMMODITIES', assetType: 'COMMODITIES', currency: 'USD', isTradable: true },
  { instrumentId: 48, symbol: 'NATGAS',  displayName: 'Natural Gas',                 exchange: 'COMMODITIES', assetType: 'COMMODITIES', currency: 'USD', isTradable: true },
  { instrumentId: 49, symbol: 'WHEAT',   displayName: 'Wheat',                       exchange: 'COMMODITIES', assetType: 'COMMODITIES', currency: 'USD', isTradable: false },
  // ETFs
  { instrumentId: 50, symbol: 'SPY',     displayName: 'SPDR S&P 500 ETF Trust',      exchange: 'NYSE',        assetType: 'ETFS',   currency: 'USD', isTradable: true },
  { instrumentId: 51, symbol: 'QQQ',     displayName: 'Invesco QQQ Trust',           exchange: 'NASDAQ',      assetType: 'ETFS',   currency: 'USD', isTradable: true },
  { instrumentId: 52, symbol: 'VTI',     displayName: 'Vanguard Total Stock Market', exchange: 'NYSE',        assetType: 'ETFS',   currency: 'USD', isTradable: true },
  { instrumentId: 53, symbol: 'GLD',     displayName: 'SPDR Gold Shares',            exchange: 'NYSE',        assetType: 'ETFS',   currency: 'USD', isTradable: true },
  { instrumentId: 54, symbol: 'IWM',     displayName: 'iShares Russell 2000 ETF',    exchange: 'NYSE',        assetType: 'ETFS',   currency: 'USD', isTradable: true },
  { instrumentId: 55, symbol: 'TLT',     displayName: 'iShares 20+ Year Treasury',   exchange: 'NASDAQ',      assetType: 'ETFS',   currency: 'USD', isTradable: true },
  { instrumentId: 56, symbol: 'EFA',     displayName: 'iShares MSCI EAFE ETF',       exchange: 'NYSE',        assetType: 'ETFS',   currency: 'USD', isTradable: true },
  { instrumentId: 57, symbol: 'VWO',     displayName: 'Vanguard FTSE Emerging Mkts', exchange: 'NYSE',        assetType: 'ETFS',   currency: 'USD', isTradable: true },
]

// ─── Helpers ──────────────────────────────────────────────────────────────────

function randomPrice(base: number, variance = 0.04): number {
  return +(base * (1 + (Math.random() - 0.5) * variance * 2)).toFixed(
    base >= 1000 ? 2 : base >= 1 ? 4 : 6,
  )
}

function randomChange(price: number): { change: number; changePercent: number } {
  const pct = (Math.random() - 0.5) * 8 // ±4 %
  return { change: +(price * pct / 100).toFixed(4), changePercent: +pct.toFixed(2) }
}

// ─── Market Data Generator ────────────────────────────────────────────────────

export function generateMockMarketData(
  symbols: string[] = Object.keys(BASE_PRICES),
): MarketData[] {
  return symbols.map((symbol) => {
    const base = BASE_PRICES[symbol] ?? 100
    const price = randomPrice(base)
    const { change, changePercent } = randomChange(price)
    return {
      symbol,
      price,
      change,
      changePercent,
      volume: Math.floor(Math.random() * 20_000_000) + 100_000,
      high24h: +(price * (1 + Math.random() * 0.025)).toFixed(4),
      low24h: +(price * (1 - Math.random() * 0.025)).toFixed(4),
      open: +(price - change).toFixed(4),
      previousClose: +(price - change * 0.95).toFixed(4),
      timestamp: new Date().toISOString(),
    }
  })
}

// ─── Candle / OHLCV Generator ─────────────────────────────────────────────────

export function generatePriceHistory(symbol: string, days = 90): Candle[] {
  const base = BASE_PRICES[symbol] ?? 100
  const candles: Candle[] = []
  let price = base * 0.82 // start below to show appreciation trend

  for (let i = days; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    const open = price
    // Slight upward drift to mimic realistic markets
    const drift = (Math.random() - 0.46) * open * 0.025
    const close = Math.max(open + drift, open * 0.9)
    const high = Math.max(open, close) * (1 + Math.random() * 0.015)
    const low = Math.min(open, close) * (1 - Math.random() * 0.015)

    candles.push({
      timestamp: date.toISOString(),
      open: +open.toFixed(4),
      high: +high.toFixed(4),
      low: +low.toFixed(4),
      close: +close.toFixed(4),
      volume: Math.floor(Math.random() * 8_000_000) + 200_000,
    })
    price = close
  }
  return candles
}

// ─── Statistics Generator ────────────────────────────────────────────────────

export function generateMockStatistics(): Statistics {
  const assetTypeBreakdown: Record<string, number> = {
    STOCKS: 456,
    CRYPTO: 78,
    FOREX: 47,
    INDICES: 23,
    COMMODITIES: 31,
    ETFS: 156,
  }
  const exchangeBreakdown: Record<string, number> = {
    NASDAQ: 289,
    NYSE: 234,
    CRYPTO: 78,
    FOREX: 47,
    INDICES: 23,
    COMMODITIES: 31,
    LSE: 89,
  }
  return {
    totalInstruments: Object.values(assetTypeBreakdown).reduce((a, b) => a + b, 0),
    totalExchanges: Object.keys(exchangeBreakdown).length,
    totalTradable: 748,
    assetTypeBreakdown,
    exchangeBreakdown,
    recentlyUpdated: MOCK_INSTRUMENTS.slice(0, 8),
    topActiveSymbols: generateMockMarketData([
      'AAPL', 'TSLA', 'BTC', 'ETH', 'NVDA', 'META', 'AMZN', 'GOOGL',
    ]),
    lastSyncAt: new Date(Date.now() - 1000 * 60 * 14).toISOString(),
  }
}

// ─── Sync Logs Generator ──────────────────────────────────────────────────────

export function generateMockSyncLogs(count = 20): SyncLog[] {
  const levels: SyncLog['level'][] = ['info', 'info', 'info', 'warning', 'error']
  const messages = [
    'Fetching instrument list from eToro API',
    'Processing STOCKS category — 456 items',
    'Processing CRYPTO category — 78 items',
    'Rate limit warning: slowing down requests',
    'Instrument PYPL flagged as non-tradable',
    'Processing FOREX category — 47 items',
    'Database upsert complete for batch 1/5',
    'Connection timeout on retry 1 — retrying',
    'Processing INDICES category — 23 items',
    'Sync completed successfully',
  ]
  return Array.from({ length: count }, (_, i) => ({
    id: `log-${i}`,
    timestamp: new Date(Date.now() - (count - i) * 12_000).toISOString(),
    level: levels[Math.floor(Math.random() * levels.length)],
    message: messages[i % messages.length],
    symbol: Math.random() > 0.6 ? MOCK_INSTRUMENTS[i % MOCK_INSTRUMENTS.length].symbol : undefined,
  }))
}
