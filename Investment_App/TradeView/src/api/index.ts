import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { STORAGE_KEYS } from '@/utils/constants'

// ─── Axios Instance ───────────────────────────────────────────────────────────

const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 10_000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── Request Interceptor ──────────────────────────────────────────────────────
// Attach JWT access token to every outgoing request

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ─── Response Interceptor ────────────────────────────────────────────────────
// Handle 401 — attempt token refresh before failing

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)
        if (refreshToken) {
          const { data } = await axios.post(
            `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/auth/refresh`,
            { refreshToken },
          )
          localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access_token)
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          }
          return api(originalRequest)
        }
      } catch {
        // Refresh failed — clear tokens and redirect to login
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
        localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  },
)

export default api
