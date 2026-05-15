import api from './index'

// ─── Upstox Auth API ──────────────────────────────────────────────────────────

export interface UpstoxAuthUrlResponse {
  url: string
}

export interface UpstoxCallbackResponse {
  message: string
  token_preview: string
}

export interface UpstoxAuthStatusResponse {
  configured: boolean
  token_preview: string | null
}

export const upstoxAuthApi = {
  /** Fetch the Upstox OAuth2 authorization URL from the backend. */
  async getAuthUrl(): Promise<UpstoxAuthUrlResponse> {
    const { data } = await api.get<UpstoxAuthUrlResponse>('/api/v1/upstox/auth/url')
    return data
  },

  /**
   * Send the authorization code (pasted from the redirect URL) to the backend.
   * The backend will exchange it for an access token and persist it.
   */
  async submitCode(code: string): Promise<UpstoxCallbackResponse> {
    const { data } = await api.post<UpstoxCallbackResponse>('/api/v1/upstox/auth/callback', {
      code,
    })
    return data
  },

  /** Check whether an Upstox access token is already configured on the server. */
  async getStatus(): Promise<UpstoxAuthStatusResponse> {
    const { data } = await api.get<UpstoxAuthStatusResponse>('/api/v1/upstox/auth/status')
    return data
  },
}
