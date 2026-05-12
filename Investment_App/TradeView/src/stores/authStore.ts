import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, AuthTokens, LoginCredentials } from '@/types/auth'
import { authApi } from '@/api/auth'
import { STORAGE_KEYS } from '@/utils/constants'
import { useNotificationStore } from './notificationStore'

// ─── Auth Store ───────────────────────────────────────────────────────────────

const MOCK_USER: User = {
  id: 'user-1',
  email: 'analyst@etoro.com',
  username: 'analyst',
  role: 'analyst',
  firstName: 'Alex',
  lastName: 'Morgan',
  preferences: {
    theme: 'dark',
    locale: 'en-US',
    watchlist: ['AAPL', 'BTC', 'EURUSD'],
    notifications: true,
  },
}

export const useAuthStore = defineStore(
  'auth',
  () => {
    const user       = ref<User | null>(null)
    const tokens     = ref<AuthTokens | null>(null)
    const loading    = ref(false)
    const useMock    = import.meta.env.VITE_MOCK_DATA === 'true'

    const isAuthenticated = computed(() => !!user.value)
    const isAdmin         = computed(() => user.value?.role === 'admin')

    async function login(credentials: LoginCredentials): Promise<boolean> {
      const notifications = useNotificationStore()
      loading.value = true
      try {
        if (useMock) {
          // Mock authentication — accept any credentials
          await new Promise((r) => setTimeout(r, 600))
          user.value = MOCK_USER
          tokens.value = {
            accessToken: 'mock-access-token',
            refreshToken: 'mock-refresh-token',
            expiresAt: Date.now() + 3_600_000,
          }
          notifications.success('Welcome back!', `Signed in as ${MOCK_USER.username}`)
          return true
        }

        const response = await authApi.login(credentials)
        user.value = response.user
        tokens.value = response.tokens
        localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.tokens.accessToken)
        localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.tokens.refreshToken)
        notifications.success('Welcome back!', `Signed in as ${response.user.username}`)
        return true
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Invalid credentials'
        notifications.error('Login failed', msg)
        return false
      } finally {
        loading.value = false
      }
    }

    async function logout() {
      const notifications = useNotificationStore()
      try {
        if (!useMock) await authApi.logout()
      } catch {
        // Ignore logout errors
      } finally {
        user.value = null
        tokens.value = null
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
        localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
        notifications.info('Signed out successfully')
      }
    }

    /** Restore session from persisted state (called on app init) */
    function restoreSession() {
      if (useMock && !user.value) {
        user.value = MOCK_USER
      }
    }

    return { user, tokens, loading, isAuthenticated, isAdmin, login, logout, restoreSession }
  },
  { persist: true },
)
