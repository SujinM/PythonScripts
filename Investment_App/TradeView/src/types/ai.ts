// TradeView/src/types/ai.ts
// AI recommendation + backtest types — matches /api/v1/{broker}/ai/* responses

export type RecommendationAction = 'BUY' | 'SELL' | 'HOLD'
export type RiskProfile = 'conservative' | 'moderate' | 'aggressive'

export interface RecommendationFeatures {
  trend:      number  // 0-100 normalised trend score
  momentum:   number  // 0-100 relative momentum vs portfolio average
  valuation:  number  // 0-100 concentration-based valuation proxy
  risk:       number  // 0-100 drawdown / downside exposure (higher = less risky)
}

export interface HoldingSnapshot {
  returnPct:           number
  currentValue:        number
  portfolioWeightPct:  number
}

export interface Recommendation {
  symbol:                  string
  action:                  RecommendationAction
  score:                   number          // Composite 0-100
  confidence:              number          // 0-100
  features:                RecommendationFeatures
  featureWeights:          Record<string, number>
  riskFlags:               string[]
  reasonBullets:           string[]
  invalidationConditions:  string[]
  narrative:               string          // Phase 3 — natural language explanation
  dataTimestamp:           string          // ISO-8601 UTC
  isStale:                 boolean
  riskProfile:             RiskProfile
  holdingSnapshot:         HoldingSnapshot | null
  isPortfolioInstrument:   boolean         // false = not held; score uses market trend proxy
}

export interface RecommendationRequest {
  symbol:      string
  riskProfile: RiskProfile
  timeframe?:  string
}

// ─── Phase 3: Backtest / scenario analysis ────────────────────────────────────

export interface ScenarioPoint {
  returnPct:   number
  score:       number
  action:      RecommendationAction
  label:       string
  isCurrent:   boolean
  features:    Record<string, number>
}

export interface FlipInfo {
  direction:     string          // "downward" | "upward"
  targetAction:  RecommendationAction
  atReturnPct:   number
  marginPct:     number
}

export interface SignalZone {
  action:     RecommendationAction
  minReturn:  number | null
  maxReturn:  number | null
  width:      number
}

export interface BacktestResult {
  symbol:             string
  riskProfile:        RiskProfile
  currentReturnPct:   number
  currentAction:      RecommendationAction
  currentScore:       number
  scenarioAnalysis:   ScenarioPoint[]
  hitRatePct:         number | null      // null when < 2 directional signals
  buySignalCount:     number
  sellSignalCount:    number
  holdSignalCount:    number
  flipDownward:       FlipInfo | null
  flipUpward:         FlipInfo | null
  signalZones:        SignalZone[]
  modelNotes:         string[]
  methodology:        string
}

