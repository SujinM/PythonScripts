// TradeView/src/types/ai.ts
// AI recommendation types — matches POST /api/v1/{broker}/ai/recommendation response

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
  dataTimestamp:           string          // ISO-8601 UTC
  isStale:                 boolean
  riskProfile:             RiskProfile
  holdingSnapshot:         HoldingSnapshot | null
}

export interface RecommendationRequest {
  symbol:      string
  riskProfile: RiskProfile
  timeframe?:  string
}
