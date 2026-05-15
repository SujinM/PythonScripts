// TradeView/src/api/ai.ts
// Client for POST /api/v1/{broker}/ai/recommendation

import api from './index'
import type { ApiEnvelope } from '@/types/portfolio'
import type { Recommendation, RecommendationRequest } from '@/types/ai'

export const aiApi = {
  /**
   * Fetch a deterministic BUY / SELL / HOLD recommendation for the given symbol
   * within the context of the specified broker's live portfolio holdings.
   *
   * The endpoint requires a valid JWT — the shared `api` Axios instance
   * automatically attaches the Bearer token from localStorage.
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
}
