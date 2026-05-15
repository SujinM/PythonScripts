// TradeView/src/api/ai.ts
// Client for AI endpoints: recommendation (Phase 2) + backtest (Phase 3)

import api from './index'
import type { ApiEnvelope } from '@/types/portfolio'
import type { BacktestResult, Recommendation, RecommendationRequest, RiskProfile } from '@/types/ai'

export const aiApi = {
  /**
   * Fetch a deterministic BUY / SELL / HOLD recommendation for the given symbol
   * within the context of the specified broker's live portfolio holdings.
   */
  async getRecommendation(
    broker: string,
    request: RecommendationRequest,
  ): Promise<Recommendation> {
    const { data: envelope } = await api.post<ApiEnvelope<Recommendation>>(
      `/api/v1/${broker}/ai/recommendation`,
      {
        symbol:       request.symbol,
        risk_profile: request.riskProfile,
        timeframe:    request.timeframe,
      },
    )
    return envelope.data
  },

  /**
   * Fetch a scenario-based signal sensitivity analysis for the given symbol.
   * Sweeps return-percentage from −25% to +30% and returns signal zones,
   * flip points, hit rate, and model notes.
   */
  async getBacktest(
    broker: string,
    symbol: string,
    riskProfile: RiskProfile = 'moderate',
  ): Promise<BacktestResult> {
    const { data: envelope } = await api.get<ApiEnvelope<BacktestResult>>(
      `/api/v1/${broker}/ai/backtest/${encodeURIComponent(symbol)}`,
      { params: { risk_profile: riskProfile } },
    )
    return envelope.data
  },
}

