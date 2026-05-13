import api from './index'
import type { User, AuthTokens, LoginCredentials, RegisterCredentials } from '@/types/auth'

// ─── Auth API ─────────────────────────────────────────────────────────────────
//
// The backend returns snake_case token keys:
//   { access_token, refresh_token, token_type, user }
// We normalise them to camelCase AuthTokens here so the rest of the app stays consistent.

interface BackendLoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

interface BackendTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

function tokensFromBackend(data: BackendTokenResponse, expiresInMs = 3_600_000): AuthTokens {
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresAt: Date.now() + expiresInMs,
  }
}

export const authApi = {
  async login(credentials: LoginCredentials): Promise<{ user: User; tokens: AuthTokens }> {
    const { data } = await api.post<BackendLoginResponse>('/api/v1/auth/login', {
      email: credentials.email,
      password: credentials.password,
    })
    return {
      user: data.user,
      tokens: tokensFromBackend(data),
    }
  },

  async register(credentials: Omit<RegisterCredentials, 'confirmPassword'>): Promise<User> {
    const { data } = await api.post<User>('/api/v1/auth/register', credentials)
    return data
  },

  async logout(): Promise<void> {
    // Backend has no stateful logout; token simply expires client-side.
    // Call is a no-op but kept for symmetry / future token-revocation support.
  },

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const { data } = await api.post<BackendTokenResponse>('/api/v1/auth/refresh', { refreshToken })
    return tokensFromBackend(data)
  },

  async getProfile(): Promise<User> {
    const { data } = await api.get<User>('/api/v1/auth/me')
    return data
  },
}

