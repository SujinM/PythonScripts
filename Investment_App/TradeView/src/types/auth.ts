// ─── Auth Types ───────────────────────────────────────────────────────────────

export type UserRole = 'admin' | 'analyst' | 'user' | 'viewer'

export interface User {
  id: string
  email: string
  username: string
  role: UserRole
  avatar?: string
  firstName?: string
  lastName?: string
  createdAt?: string
  preferences?: UserPreferences
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

export interface RegisterCredentials {
  username: string
  email: string
  password: string
  confirmPassword: string
}

export interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
}
