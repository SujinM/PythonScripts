import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, AuthTokens, LoginCredentials, RegisterCredentials } from '@/types/auth'
import { authApi } from '@/api/auth'
import { STORAGE_KEYS } from '@/utils/constants'
import { useNotificationStore } from './notificationStore'

// ─── Auth Store ───────────────────────────────────────────────────────────────

export const useAuthStore = defineStore(
  'auth',
  () => {
    const user    = ref<User | null>(null)
    const tokens  = ref<AuthTokens | null>(null)
    const loading = ref(false)

    const isAuthenticated = computed(() => !!user.value)
    const isAdmin         = computed(() => user.value?.role === 'admin')

    // ── Login ──────────────────────────────────────────────────────────────
    async function login(credentials: LoginCredentials): Promise<boolean> {
      const notifications = useNotificationStore()
      loading.value = true
      try {
        const response = await authApi.login(credentials)
        user.value   = response.user
        tokens.value = response.tokens
        localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN,  response.tokens.accessToken)
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

    // ── Register ───────────────────────────────────────────────────────────
    async function register(credentials: RegisterCredentials): Promise<boolean> {
      const notifications = useNotificationStore()
      loading.value = true
      try {
        await authApi.register({
          username: credentials.username,
          email:    credentials.email,
          password: credentials.password,
        })
        notifications.success('Account created!', 'You can now sign in with your credentials.')
        return true
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Registration failed'
        notifications.error('Registration failed', msg)
        return false
      } finally {
        loading.value = false
      }
    }

    // ── Logout ─────────────────────────────────────────────────────────────
    async function logout() {
      const notifications = useNotificationStore()
      user.value   = null
      tokens.value = null
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
      notifications.info('Signed out successfully')
    }

    // ── Restore session on page reload ────────────────────────────────────
    /**
     * Called once by the router on first navigation.
     * Validates the stored access token against the backend.
     * Also purges any leftover mock tokens from a previous dev session.
     */
    async function checkAuth(): Promise<boolean> {
      const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)

      // Discard stale mock tokens or missing tokens without a round-trip
      if (!token || token.startsWith('mock-')) {
        user.value   = null
        tokens.value = null
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
        localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
        return false
      }
      try {
        user.value = await authApi.getProfile()
        return true
      } catch {
        user.value   = null
        tokens.value = null
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
        localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
        return false
      }
    }

    return {
      user,
      tokens,
      loading,
      isAuthenticated,
      isAdmin,
      login,
      register,
      logout,
      checkAuth,
    }
  },
  { persist: true },
)
