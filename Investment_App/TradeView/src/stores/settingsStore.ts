import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { STORAGE_KEYS } from '@/utils/constants'

// ─── Settings Store ───────────────────────────────────────────────────────────

export const useSettingsStore = defineStore(
  'settings',
  () => {
    const theme           = ref<'dark' | 'light'>('dark')
    const locale          = ref('en-US')
    const sidebarCollapsed = ref(false)
    const watchlist        = ref<string[]>(['AAPL', 'BTC', 'EURUSD', 'GOLD'])
    const autoRefresh      = ref(true)
    const notifications    = ref(true)
    const refreshInterval  = ref(30000)

    /** Apply the current theme to the <html> element */
    function applyTheme() {
      const html = document.documentElement
      if (theme.value === 'dark') {
        html.classList.add('dark')
      } else {
        html.classList.remove('dark')
      }
      localStorage.setItem(STORAGE_KEYS.THEME, theme.value)
    }

    function toggleTheme() {
      theme.value = theme.value === 'dark' ? 'light' : 'dark'
    }

    function toggleSidebar() {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }

    function addToWatchlist(symbol: string) {
      if (!watchlist.value.includes(symbol)) {
        watchlist.value.push(symbol)
      }
    }

    function removeFromWatchlist(symbol: string) {
      watchlist.value = watchlist.value.filter((s) => s !== symbol)
    }

    function isInWatchlist(symbol: string): boolean {
      return watchlist.value.includes(symbol)
    }

    function clearWatchlist() {
      watchlist.value = []
    }

    // Keep DOM in sync with theme state
    watch(theme, applyTheme, { immediate: true })

    return {
      theme,
      locale,
      sidebarCollapsed,
      watchlist,
      autoRefresh,
      notifications,
      refreshInterval,
      clearWatchlist,
      applyTheme,
      toggleTheme,
      toggleSidebar,
      addToWatchlist,
      removeFromWatchlist,
      isInWatchlist,
    }
  },
  { persist: true },
)
