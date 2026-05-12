import api from './index'
import type { User, AuthTokens, LoginCredentials } from '@/types/auth'

// ─── Auth API ─────────────────────────────────────────────────────────────────

export const authApi = {
  async login(credentials: LoginCredentials): Promise<{ user: User; tokens: AuthTokens }> {
    const { data } = await api.post<{ user: User; tokens: AuthTokens }>('/auth/login', credentials)
    return data
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const { data } = await api.post<AuthTokens>('/auth/refresh', { refreshToken })
    return data
  },

  async getProfile(): Promise<User> {
    const { data } = await api.get<User>('/auth/me')
    return data
  },

  async updateProfile(updates: Partial<User>): Promise<User> {
    const { data } = await api.patch<User>('/auth/me', updates)
    return data
  },
}
