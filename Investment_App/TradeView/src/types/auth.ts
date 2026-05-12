// ─── Auth Types ───────────────────────────────────────────────────────────────

export type UserRole = 'admin' | 'analyst' | 'viewer'

export interface User {
  id: string
  email: string
  username: string
  role: UserRole
  avatar?: string
  firstName?: string
  lastName?: string
  preferences?: UserPreferences
  createdAt?: string
}

export interface UserPreferences {
  theme: 'dark' | 'light'
  locale: string
  watchlist: string[]
  defaultExchange?: string
  notifications: boolean
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresAt: number
}

export interface LoginCredentials {
  email: string
  password: string
  rememberMe?: boolean
}

export interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
}
