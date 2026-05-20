// ── Price calculations ────────────────────────────────────────────────────────

export function priceDifference(oldP: number, newP: number) {
  return { label: 'Price Difference', value: round(newP - oldP, 4), unit: '' }
}

export function percentageChange(oldP: number, newP: number) {
  if (oldP === 0) throw new Error('Old price cannot be zero.')
  const pct = ((newP - oldP) / oldP) * 100
  return { label: pct >= 0 ? 'Percentage UP' : 'Percentage DOWN', value: round(pct, 4), unit: '%' }
}

export function targetPriceFromPct(current: number, targetPct: number) {
  return { label: 'Target Price', value: round(current * (1 + targetPct / 100), 4), unit: '' }
}

export function stopLossPrice(buy: number, slPct: number) {
  return { label: 'Stop Loss Price', value: round(buy * (1 - Math.abs(slPct) / 100), 4), unit: '' }
}

export function takeProfitPrice(buy: number, tpPct: number) {
  return { label: 'Take Profit Price', value: round(buy * (1 + Math.abs(tpPct) / 100), 4), unit: '' }
}

export function pivotPoints(high: number, low: number, close: number) {
  const pp = (high + low + close) / 3
  return {
    PP: round(pp, 4),
    R1: round(2 * pp - low, 4),
    R2: round(pp + (high - low), 4),
    R3: round(high + 2 * (pp - low), 4),
    S1: round(2 * pp - high, 4),
    S2: round(pp - (high - low), 4),
    S3: round(low - 2 * (high - pp), 4),
  }
}

export function movingAverage(prices: number[], period?: number) {
  const data = period ? prices.slice(-period) : prices
  if (!data.length) throw new Error('Price list is empty.')
  return round(data.reduce((a, b) => a + b, 0) / data.length, 4)
}

// ── Returns & P&L ─────────────────────────────────────────────────────────────

export function profitLoss(buy: number, sell: number, qty: number) {
  const invested = buy * qty
  const current  = sell * qty
  const pnl      = current - invested
  return {
    'Invested':      round(invested, 2),
    'Current Value': round(current, 2),
    'P&L':           round(pnl, 2),
    'P&L %':         round(invested ? (pnl / invested) * 100 : 0, 4),
  }
}

export function cagr(initial: number, final: number, years: number) {
  if (initial <= 0 || years <= 0) throw new Error('Initial value and years must be positive.')
  return { label: 'CAGR', value: round(((final / initial) ** (1 / years) - 1) * 100, 4), unit: '%' }
}

export function roi(cost: number, gain: number) {
  if (cost === 0) throw new Error('Cost cannot be zero.')
  return { label: 'ROI', value: round(((gain - cost) / cost) * 100, 4), unit: '%' }
}

export function breakevenPrice(buy: number, feePct: number) {
  return { label: 'Breakeven Price', value: round(buy * (1 + feePct / 100), 4), unit: '' }
}

export function dividendYield(div: number, price: number) {
  if (price === 0) throw new Error('Stock price cannot be zero.')
  return { label: 'Dividend Yield', value: round((div / price) * 100, 4), unit: '%' }
}

export function compoundInterest(principal: number, rate: number, years: number, n: number) {
  const amount   = principal * (1 + rate / (100 * n)) ** (n * years)
  const interest = amount - principal
  return {
    'Principal': round(principal, 2),
    'Amount':    round(amount, 2),
    'Interest':  round(interest, 2),
    'Rate':      `${rate}% / ${years}y (n=${n})`,
  }
}

// ── Risk ──────────────────────────────────────────────────────────────────────

export function positionSizeByRisk(account: number, riskPct: number, buy: number, sl: number) {
  const riskAmount = account * riskPct / 100
  const riskPerShare = Math.abs(buy - sl)
  if (riskPerShare === 0) throw new Error('Buy price and stop loss cannot be equal.')
  const shares = Math.floor(riskAmount / riskPerShare)
  return {
    'Risk Amount':    round(riskAmount, 2),
    'Risk Per Share': round(riskPerShare, 4),
    'Shares to Buy':  shares,
    'Total Cost':     round(shares * buy, 2),
  }
}

export function riskRewardRatio(buy: number, sl: number, target: number) {
  const risk   = Math.abs(buy - sl)
  const reward = Math.abs(target - buy)
  if (risk === 0) throw new Error('Risk cannot be zero.')
  return { label: 'Risk / Reward Ratio', value: round(reward / risk, 4), unit: '' }
}

export function sharpeRatio(avgReturn: number, riskFree: number, stdDev: number) {
  if (stdDev === 0) throw new Error('Standard deviation cannot be zero.')
  return { label: 'Sharpe Ratio', value: round((avgReturn - riskFree) / stdDev, 4), unit: '' }
}

export function historicalVolatility(prices: number[]) {
  if (prices.length < 2) throw new Error('Need at least 2 prices.')
  const returns = prices.slice(1).map((p, i) => ((p - prices[i]) / prices[i]) * 100)
  const mean    = returns.reduce((a, b) => a + b, 0) / returns.length
  const variance = returns.reduce((a, r) => a + (r - mean) ** 2, 0) / returns.length
  return { label: 'Volatility (Daily)', value: round(Math.sqrt(variance), 4), unit: '%' }
}

export function maxDrawdown(prices: number[]) {
  if (!prices.length) throw new Error('Price list is empty.')
  let peak = prices[0], maxDD = 0
  for (const p of prices) {
    if (p > peak) peak = p
    const dd = ((peak - p) / peak) * 100
    if (dd > maxDD) maxDD = dd
  }
  return { label: 'Max Drawdown', value: round(maxDD, 4), unit: '%' }
}

// ── Position & Portfolio ──────────────────────────────────────────────────────

export function averageBuyPrice(purchases: { price: number; qty: number }[]) {
  const totalQty  = purchases.reduce((a, b) => a + b.qty, 0)
  const totalCost = purchases.reduce((a, b) => a + b.price * b.qty, 0)
  if (totalQty === 0) throw new Error('Total quantity cannot be zero.')
  return {
    'Average Buy Price': round(totalCost / totalQty, 4),
    'Total Quantity':    round(totalQty, 4),
    'Total Cost':        round(totalCost, 2),
  }
}

export function portfolioAllocation(holdings: { symbol: string; value: number }[]) {
  const total = holdings.reduce((a, b) => a + b.value, 0)
  if (total === 0) throw new Error('Total value cannot be zero.')
  return holdings.map(h => ({ symbol: h.symbol, pct: round((h.value / total) * 100, 2) }))
}

export function lotSizeCalculator(capital: number, price: number, allocPct: number) {
  const allocated  = capital * allocPct / 100
  const shares     = Math.floor(allocated / price)
  const actualCost = shares * price
  return {
    'Allocated Amount': round(allocated, 2),
    'Shares':           shares,
    'Actual Cost':      round(actualCost, 2),
    'Remaining Cash':   round(allocated - actualCost, 2),
  }
}

export function unrealisedPnl(avgBuy: number, current: number, qty: number) {
  const invested = avgBuy * qty
  const cur      = current * qty
  const pnl      = cur - invested
  return {
    'Invested':       round(invested, 2),
    'Current Value':  round(cur, 2),
    'Unrealised P&L': round(pnl, 2),
    'P&L %':          round(invested ? (pnl / invested) * 100 : 0, 4),
  }
}

// ── Options ───────────────────────────────────────────────────────────────────

export function intrinsicValue(type: 'call' | 'put', spot: number, strike: number) {
  const iv = type === 'call' ? Math.max(spot - strike, 0) : Math.max(strike - spot, 0)
  return {
    'Option Type':     type.toUpperCase(),
    'Spot Price':      spot,
    'Strike Price':    strike,
    'Intrinsic Value': round(iv, 4),
    'In The Money':    iv > 0 ? 'Yes' : 'No',
  }
}

export function blackScholes(
  type: 'call' | 'put', S: number, K: number, T: number, r: number, sigma: number
) {
  if (T <= 0 || sigma <= 0) throw new Error('T and sigma must be positive.')
  const d1 = (Math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * Math.sqrt(T))
  const d2 = d1 - sigma * Math.sqrt(T)

  const normCdf = (x: number) => {
    const a1=0.254829592, a2=-0.284496736, a3=1.421413741, a4=-1.453152027, a5=1.061405429, p=0.3275911
    const sign = x < 0 ? -1 : 1
    const t = 1 / (1 + p * Math.abs(x))
    const poly = t * (a1 + t * (a2 + t * (a3 + t * (a4 + t * a5))))
    return 0.5 * (1 + sign * (1 - poly * Math.exp(-x * x / 2)))
  }

  let price: number, delta: number
  if (type === 'call') {
    price = S * normCdf(d1) - K * Math.exp(-r * T) * normCdf(d2)
    delta = normCdf(d1)
  } else {
    price = K * Math.exp(-r * T) * normCdf(-d2) - S * normCdf(-d1)
    delta = normCdf(d1) - 1
  }
  const gamma = Math.exp(-0.5 * d1 ** 2) / (S * sigma * Math.sqrt(T) * Math.sqrt(2 * Math.PI))
  const theta = (
    -(S * sigma * Math.exp(-0.5 * d1 ** 2)) / (2 * Math.sqrt(T) * Math.sqrt(2 * Math.PI))
    - r * K * Math.exp(-r * T) * normCdf(type === 'call' ? d2 : -d2)
  ) / 365

  return {
    'Option Type': type.toUpperCase(),
    'Price':  round(price, 4),
    'Delta':  round(delta, 4),
    'Gamma':  round(gamma, 6),
    'Theta':  round(theta, 6),
    'd1':     round(d1, 4),
    'd2':     round(d2, 4),
  }
}

// ── Percentage Up / Down ──────────────────────────────────────────────────────

export function percentageUpDown(value: number, pct: number) {
  if (value === 0) throw new Error('Value cannot be zero.')
  if (pct < 0)     throw new Error('Percentage must be a positive number.')
  const delta = round(value * pct / 100, 4)
  return {
    'Original Value':  round(value, 4),
    'Percentage':      `${pct}%`,
    'Value UP':        round(value + delta, 4),
    'Amount UP':       `+${delta}`,
    'Value DOWN':      round(value - delta, 4),
    'Amount DOWN':     `-${delta}`,
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function round(n: number, dp: number) {
  return Math.round(n * 10 ** dp) / 10 ** dp
}
