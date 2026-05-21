// src/api/etoroWatchlists.ts

import api from './index'
import type { Watchlist, WatchlistsParams, WatchlistsResponse } from '@/types/etoroWatchlist'

export const etoroWatchlistsApi = {
  /** GET /api/v1/etoro/watchlists */
  async getWatchlists(params?: WatchlistsParams): Promise<WatchlistsResponse> {
    const { data } = await api.get<WatchlistsResponse>('/api/v1/etoro/watchlists', { params })
    return data
  },

  /** GET /api/v1/etoro/watchlists/{id} */
  async getWatchlist(watchlistId: string, params?: WatchlistsParams): Promise<Watchlist> {
    const { data } = await api.get<Watchlist>(`/api/v1/etoro/watchlists/${watchlistId}`, { params })
    return data
  },
}
