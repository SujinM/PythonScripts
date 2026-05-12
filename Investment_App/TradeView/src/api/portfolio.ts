import api from './index'
import type {
  ApiEnvelope,
  Holding,
  Position,
  Trade,
  PortfolioSummary,
  AnalysisResult,
  Alert,
  BrokerInfo,
} from '@/types/portfolio'

// ─── Portfolio API ────────────────────────────────────────────────────────────
// Mirrors ClientConsolApp/Services/PortfolioService.cs — each method maps 1:1
// to a FastAPI endpoint under /api/v1/{broker}/...

export const portfolioApi = {
  /** GET /api/v1/brokers — list all registered broker adapters (etoro, upstox) */
  async getBrokers(): Promise<BrokerInfo[]> {
    const { data } = await api.get<ApiEnvelope<BrokerInfo[]>>('/api/v1/brokers')
    return data.data
  },

  /** GET /api/v1/{broker}/holdings */
  async getHoldings(broker: string): Promise<Holding[]> {
    const { data } = await api.get<ApiEnvelope<Holding[]>>(`/api/v1/${broker}/holdings`)
    return data.data
  },

  /** GET /api/v1/{broker}/positions */
  async getPositions(broker: string): Promise<Position[]> {
    const { data } = await api.get<ApiEnvelope<Position[]>>(`/api/v1/${broker}/positions`)
    return data.data
  },

  /** GET /api/v1/{broker}/trades */
  async getTrades(broker: string): Promise<Trade[]> {
    const { data } = await api.get<ApiEnvelope<Trade[]>>(`/api/v1/${broker}/trades`)
    return data.data
  },

  /** GET /api/v1/{broker}/summary */
  async getSummary(broker: string): Promise<PortfolioSummary> {
    const { data } = await api.get<ApiEnvelope<PortfolioSummary>>(`/api/v1/${broker}/summary`)
    return data.data
  },

  /** GET /api/v1/{broker}/analysis */
  async getAnalysis(broker: string): Promise<AnalysisResult> {
    const { data } = await api.get<ApiEnvelope<AnalysisResult>>(`/api/v1/${broker}/analysis`)
    return data.data
  },

  /** GET /api/v1/{broker}/analysis/alerts */
  async getAlerts(broker: string): Promise<Alert[]> {
    const { data } = await api.get<ApiEnvelope<Alert[]>>(`/api/v1/${broker}/analysis/alerts`)
    return data.data
  },

  /** POST /api/v1/{broker}/cache/invalidate — force fresh data fetch from broker */
  async invalidateCache(broker: string): Promise<{ message: string }> {
    const { data } = await api.post<ApiEnvelope<{ message: string }>>(
      `/api/v1/${broker}/cache/invalidate`,
    )
    return data.data
  },
}
