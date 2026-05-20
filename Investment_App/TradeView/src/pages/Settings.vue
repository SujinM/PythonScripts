<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settingsStore'
import { useAuthStore } from '@/stores/authStore'
import { usePortfolioStore } from '@/stores/portfolioStore'
import { useLiveTick } from '@/composables/useLiveTick'
import { useNotification } from '@/composables/useNotification'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import Badge from '@/components/common/Badge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { upstoxAuthApi } from '@/api/upstoxAuth'

const REFRESH_INTERVAL_OPTIONS = [
  { label: '15 seconds', value: 15_000 },
  { label: '30 seconds', value: 30_000 },
  { label: '1 minute',   value: 60_000 },
  { label: '5 minutes',  value: 300_000 },
]

const settings  = useSettingsStore()
const auth      = useAuthStore()
const portfolio = usePortfolioStore()
const notify    = useNotification()
const route     = useRoute()
const router    = useRouter()

type Tab = 'appearance' | 'data' | 'watchlist' | 'brokers' | 'account'
const activeTab = ref<Tab>('appearance')

// â”€â”€ Broker management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const liveTickMap: Record<string, ReturnType<typeof useLiveTick>> = {}

function getLiveTick(brokerId: string) {
  if (!liveTickMap[brokerId]) liveTickMap[brokerId] = useLiveTick(brokerId)
  return liveTickMap[brokerId]
}

function isLiveConnected(brokerId: string) {
  return getLiveTick(brokerId).isConnected.value
}

function toggleLive(brokerId: string) {
  const tick = getLiveTick(brokerId)
  tick.isConnected.value ? tick.disconnect() : tick.connect()
}

async function handleInvalidate(brokerId: string) {
  await portfolio.invalidateCache(brokerId)
}

function removeFromWatchlist(symbol: string) {
  settings.removeFromWatchlist(symbol)
  notify.info(`Removed ${symbol} from watchlist`)
}

// â”€â”€ Upstox authentication â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const upstoxStatus  = ref<{ configured: boolean; token_preview: string | null }>({
  configured: false,
  token_preview: null,
})
const upstoxLoading = ref(false)

async function fetchUpstoxStatus() {
  try {
    upstoxStatus.value = await upstoxAuthApi.getStatus()
  } catch {
    // Backend may not be running â€” ignore silently
  }
}

async function startUpstoxAuth() {
  upstoxLoading.value = true
  try {
    const { url } = await upstoxAuthApi.getAuthUrl()
    window.location.href = url
  } catch (err: any) {
    notify.error(err?.response?.data?.detail ?? 'Failed to get Upstox auth URL')
    upstoxLoading.value = false
  }
}

onMounted(async () => {
  const authResult = route.query.upstox_auth as string | undefined
  if (authResult === 'success') {
    notify.success('Upstox connected successfully!')
    router.replace({ path: '/settings' })
  } else if (authResult === 'error') {
    const msg = (route.query.message as string | undefined) ?? 'Upstox authentication failed'
    notify.error(msg)
    router.replace({ path: '/settings' })
  }
  await Promise.all([fetchUpstoxStatus(), portfolio.fetchBrokers()])
})
</script>

<template>
  <div class="animate-fade-in space-y-0">

    <!-- â”€â”€ Page Header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
    <div class="mb-6">
      <h2 class="text-2xl font-bold tracking-tight" style="color: var(--text-primary);">Settings</h2>
      <p class="text-sm mt-1" style="color: var(--text-muted);">Manage preferences, brokers, and your account</p>
    </div>

    <div class="flex flex-col lg:flex-row gap-6">

      <!-- â”€â”€ Left: Tab Nav â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
      <nav class="lg:w-52 flex-shrink-0">
        <div class="card p-2 flex flex-row lg:flex-col gap-1 overflow-x-auto lg:overflow-visible">
          <button
            v-for="tab in [
              { id: 'appearance', label: 'Appearance',   icon: 'palette' },
              { id: 'data',       label: 'Data',         icon: 'refresh' },
              { id: 'watchlist',  label: 'Watchlist',    icon: 'star' },
              { id: 'brokers',    label: 'Brokers',      icon: 'link' },
              { id: 'account',    label: 'Account',      icon: 'user' },
            ]"
            :key="tab.id"
            :class="[
              'flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap w-full text-left',
              activeTab === tab.id
                ? 'bg-brand-500/15 text-brand-400 border border-brand-500/25'
                : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent',
            ]"
            @click="activeTab = tab.id as Tab"
          >
            <!-- Tab icons -->
            <svg v-if="tab.icon === 'palette'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
            </svg>
            <svg v-else-if="tab.icon === 'refresh'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <svg v-else-if="tab.icon === 'star'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
            <svg v-else-if="tab.icon === 'link'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <svg v-else-if="tab.icon === 'user'" class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span class="hidden lg:inline">{{ tab.label }}</span>
            <span class="lg:hidden">{{ tab.label }}</span>
          </button>
        </div>
      </nav>

      <!-- â”€â”€ Right: Tab Content â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
      <div class="flex-1 min-w-0">

        <!-- â•â• Appearance â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
        <div v-if="activeTab === 'appearance'" class="space-y-4">
          <div class="card overflow-hidden">
            <div class="px-5 py-4 border-b" style="border-color: var(--surface-border);">
              <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Appearance</h3>
              <p class="text-xs mt-0.5" style="color: var(--text-muted);">Customise how the app looks</p>
            </div>
            <!-- Row: Dark mode -->
            <div class="px-5 py-4 flex items-center justify-between gap-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-indigo-500/15">
                  <svg class="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-medium" style="color: var(--text-primary);">Dark Mode</p>
                  <p class="text-xs" style="color: var(--text-muted);">Bloomberg-style dark interface</p>
                </div>
              </div>
              <ThemeToggle />
            </div>
            <!-- Row: Language -->
            <div class="px-5 py-4 flex items-center justify-between gap-4 border-t" style="border-color: var(--surface-border);">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-blue-500/15">
                  <svg class="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-medium" style="color: var(--text-primary);">Locale</p>
                  <p class="text-xs" style="color: var(--text-muted);">Number & date formatting</p>
                </div>
              </div>
              <select class="input text-xs w-auto" v-model="settings.locale">
                <option value="en-US">English (US)</option>
                <option value="en-IN">English (IN)</option>
                <option value="en-GB">English (GB)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- â•â• Data Refresh â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
        <div v-if="activeTab === 'data'" class="space-y-4">
          <div class="card overflow-hidden">
            <div class="px-5 py-4 border-b" style="border-color: var(--surface-border);">
              <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Data Refresh</h3>
              <p class="text-xs mt-0.5" style="color: var(--text-muted);">Control how market data is updated</p>
            </div>
            <!-- Auto refresh toggle -->
            <div class="px-5 py-4 flex items-center justify-between gap-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-emerald-500/15">
                  <svg class="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-medium" style="color: var(--text-primary);">Auto Refresh</p>
                  <p class="text-xs" style="color: var(--text-muted);">Automatically update market data in background</p>
                </div>
              </div>
              <label class="relative inline-flex items-center cursor-pointer flex-shrink-0">
                <input type="checkbox" class="sr-only peer" :checked="settings.autoRefresh" @change="settings.autoRefresh = !settings.autoRefresh" />
                <div class="w-11 h-6 rounded-full peer-checked:bg-brand-500 bg-gray-600 peer-focus:ring-2 peer-focus:ring-brand-500/30 after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
              </label>
            </div>
            <!-- Interval (only when enabled) -->
            <Transition
              enter-active-class="transition-all duration-200 overflow-hidden"
              enter-from-class="max-h-0 opacity-0"
              enter-to-class="max-h-32 opacity-100"
              leave-active-class="transition-all duration-150 overflow-hidden"
              leave-from-class="max-h-32 opacity-100"
              leave-to-class="max-h-0 opacity-0"
            >
              <div v-if="settings.autoRefresh" class="px-5 py-4 border-t flex items-center gap-3" style="border-color: var(--surface-border);">
                <div class="flex items-center gap-3 flex-1">
                  <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-amber-500/15">
                    <svg class="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p class="text-sm font-medium" style="color: var(--text-primary);">Refresh Interval</p>
                    <p class="text-xs" style="color: var(--text-muted);">How often to poll for new data</p>
                  </div>
                </div>
                <select class="input text-xs w-auto" v-model="settings.refreshInterval">
                  <option v-for="opt in REFRESH_INTERVAL_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
            </Transition>
            <!-- Notifications toggle -->
            <div class="px-5 py-4 border-t flex items-center justify-between gap-4" style="border-color: var(--surface-border);">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg flex items-center justify-center bg-purple-500/15">
                  <svg class="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-medium" style="color: var(--text-primary);">Notifications</p>
                  <p class="text-xs" style="color: var(--text-muted);">Price alerts and portfolio updates</p>
                </div>
              </div>
              <label class="relative inline-flex items-center cursor-pointer flex-shrink-0">
                <input type="checkbox" class="sr-only peer" :checked="settings.notifications" @change="settings.notifications = !settings.notifications" />
                <div class="w-11 h-6 rounded-full peer-checked:bg-brand-500 bg-gray-600 peer-focus:ring-2 peer-focus:ring-brand-500/30 after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
              </label>
            </div>
          </div>
        </div>

        <!-- â•â• Watchlist â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
        <div v-if="activeTab === 'watchlist'" class="space-y-4">
          <div class="card overflow-hidden">
            <div class="px-5 py-4 border-b flex items-center justify-between" style="border-color: var(--surface-border);">
              <div>
                <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Watchlist</h3>
                <p class="text-xs mt-0.5" style="color: var(--text-muted);">Symbols you are tracking</p>
              </div>
              <span class="text-xs px-2.5 py-1 rounded-full font-medium bg-brand-500/15 text-brand-400">
                {{ settings.watchlist.length }} symbols
              </span>
            </div>
            <div class="px-5 py-4">
              <div v-if="settings.watchlist.length === 0" class="py-10 text-center">
                <svg class="w-10 h-10 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="color: var(--text-muted);">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
                <p class="text-sm font-medium" style="color: var(--text-muted);">Watchlist is empty</p>
                <p class="text-xs mt-1" style="color: var(--text-muted);">Add instruments from the Instrument Detail page</p>
              </div>
              <div v-else class="flex flex-wrap gap-2">
                <div
                  v-for="symbol in settings.watchlist"
                  :key="symbol"
                  class="group flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-lg text-xs font-mono border transition-colors"
                  style="border-color: var(--surface-border); background-color: var(--surface-secondary);"
                >
                  <span class="text-brand-400 font-semibold">{{ symbol }}</span>
                  <button
                    class="w-4 h-4 flex items-center justify-center rounded text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    @click="removeFromWatchlist(symbol)"
                    title="Remove"
                  >âœ•</button>
                </div>
              </div>
              <div v-if="settings.watchlist.length > 0" class="mt-4 pt-4 border-t flex justify-end" style="border-color: var(--surface-border);">
                <button class="text-xs text-red-400 hover:text-red-300 transition-colors flex items-center gap-1.5" @click="settings.clearWatchlist()">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Clear all
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- â•â• Brokers â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
        <div v-if="activeTab === 'brokers'" class="space-y-4">

          <!-- Upstox Auth card -->
          <div class="card overflow-hidden">
            <div class="px-5 py-4 border-b flex items-center justify-between" style="border-color: var(--surface-border);">
              <div>
                <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Upstox Authentication</h3>
                <p class="text-xs mt-0.5" style="color: var(--text-muted);">OAuth2 connection for live portfolio data</p>
              </div>
              <span
                class="text-xs px-2.5 py-1 rounded-full font-medium"
                :class="upstoxStatus.configured ? 'bg-emerald-500/15 text-emerald-400' : 'bg-amber-500/15 text-amber-400'"
              >
                {{ upstoxStatus.configured ? 'â— Connected' : 'â—‹ Not connected' }}
              </span>
            </div>
            <div class="px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-4">
              <div class="flex-1">
                <div v-if="upstoxStatus.configured" class="flex items-center gap-2 text-xs">
                  <svg class="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span style="color: var(--text-muted);">Access token active â€”</span>
                  <code class="font-mono text-brand-400 bg-brand-500/10 px-1.5 py-0.5 rounded">{{ upstoxStatus.token_preview }}</code>
                </div>
                <p v-else class="text-xs" style="color: var(--text-muted);">
                  Connect your Upstox account to enable live portfolio data. You'll be redirected to Upstox and returned here automatically.
                </p>
              </div>
              <button
                class="btn-primary text-xs px-4 py-2 flex items-center gap-1.5 flex-shrink-0"
                :disabled="upstoxLoading"
                @click="startUpstoxAuth"
              >
                <svg v-if="upstoxLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                {{ upstoxStatus.configured ? 'Re-authenticate' : 'Connect Upstox' }}
              </button>
            </div>
          </div>

          <!-- Broker cards -->
          <div class="card overflow-hidden">
            <div class="px-5 py-4 border-b flex items-center justify-between" style="border-color: var(--surface-border);">
              <div>
                <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Connected Brokers</h3>
                <p class="text-xs mt-0.5" style="color: var(--text-muted);">Manage data sources and live streams</p>
              </div>
              <span class="text-xs" style="color: var(--text-muted);">
                Active: <span class="text-brand-400 font-medium capitalize">{{ portfolio.activeBroker }}</span>
              </span>
            </div>
            <div class="p-5">
              <div v-if="portfolio.loading && portfolio.brokers.length === 0" class="flex justify-center py-10">
                <LoadingSpinner size="lg" />
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div
                  v-for="broker in portfolio.brokers"
                  :key="broker.id"
                  class="relative rounded-xl p-4 space-y-4 border transition-all"
                  :class="portfolio.activeBroker === broker.id ? 'border-brand-500/40 shadow-brand-500/10 shadow-lg' : 'border-gray-700/50'"
                  style="background-color: var(--surface-secondary);"
                >
                  <!-- Active glow -->
                  <div v-if="portfolio.activeBroker === broker.id" class="absolute inset-0 rounded-xl bg-brand-500/5 pointer-events-none" />

                  <!-- Header -->
                  <div class="flex items-start justify-between gap-2">
                    <div class="flex items-center gap-3">
                      <div class="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold uppercase bg-gradient-to-br from-brand-500/30 to-brand-600/20 text-brand-300 border border-brand-500/20">
                        {{ broker.id.slice(0, 2).toUpperCase() }}
                      </div>
                      <div>
                        <p class="text-sm font-semibold capitalize" style="color: var(--text-primary);">{{ broker.name ?? broker.id }}</p>
                        <p class="text-xs font-mono" style="color: var(--text-muted);">{{ broker.id }}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-2 flex-shrink-0">
                      <span
                        v-if="portfolio.activeBroker === broker.id"
                        class="text-[10px] px-2 py-0.5 rounded-full font-medium bg-brand-500/15 text-brand-400 border border-brand-500/30"
                      >Active</span>
                      <button
                        v-else
                        class="text-xs px-3 py-1 rounded-lg border border-gray-600 text-gray-300 hover:border-brand-500/50 hover:text-brand-400 transition-colors"
                        @click="portfolio.selectBroker(broker.id)"
                      >Select</button>
                    </div>
                  </div>

                  <p v-if="broker.description" class="text-xs leading-relaxed" style="color: var(--text-muted);">{{ broker.description }}</p>

                  <!-- Status + actions -->
                  <div class="flex items-center justify-between pt-1 border-t" style="border-color: var(--surface-border);">
                    <!-- Live status -->
                    <div class="flex items-center gap-1.5 text-xs" :class="isLiveConnected(broker.id) ? 'text-emerald-400' : 'text-gray-500'">
                      <span :class="['w-1.5 h-1.5 rounded-full', isLiveConnected(broker.id) ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600']" />
                      {{ isLiveConnected(broker.id) ? 'Live connected' : 'Live off' }}
                    </div>
                    <!-- Action buttons -->
                    <div class="flex items-center gap-1.5">
                      <button
                        class="p-1.5 rounded-lg border border-transparent hover:border-gray-600 hover:bg-gray-800/60 transition-colors"
                        title="Invalidate cache"
                        :disabled="portfolio.loading"
                        @click="handleInvalidate(broker.id)"
                      >
                        <LoadingSpinner v-if="portfolio.loading" size="sm" />
                        <svg v-else class="w-3.5 h-3.5" style="color: var(--text-muted);" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </button>
                      <button
                        class="p-1.5 rounded-lg border transition-colors"
                        :class="isLiveConnected(broker.id)
                          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
                          : 'border-gray-600 text-gray-400 hover:text-white hover:border-gray-400'"
                        :title="isLiveConnected(broker.id) ? 'Disconnect live' : 'Connect live'"
                        @click="toggleLive(broker.id)"
                      >
                        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                <div v-if="portfolio.brokers.length === 0 && !portfolio.loading" class="col-span-full py-10 text-center">
                  <p class="text-sm" style="color: var(--text-muted);">No brokers found â€” ensure the backend is running</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- â•â• Account â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• -->
        <div v-if="activeTab === 'account'" class="space-y-4">
          <div class="card overflow-hidden">
            <div class="px-5 py-4 border-b" style="border-color: var(--surface-border);">
              <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Account</h3>
              <p class="text-xs mt-0.5" style="color: var(--text-muted);">Your profile and session</p>
            </div>
            <!-- Avatar + info -->
            <div class="px-5 py-5 flex items-center gap-4">
              <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-brand-500/25 flex-shrink-0">
                {{ auth.user?.username?.charAt(0)?.toUpperCase() ?? 'U' }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-base font-semibold truncate" style="color: var(--text-primary);">
                  {{ auth.user?.firstName && auth.user?.lastName
                    ? `${auth.user.firstName} ${auth.user.lastName}`
                    : auth.user?.username ?? 'Unknown' }}
                </p>
                <p class="text-xs truncate mt-0.5" style="color: var(--text-muted);">{{ auth.user?.email }}</p>
                <div class="mt-2">
                  <Badge :value="auth.user?.role ?? 'user'" type="assetType" />
                </div>
              </div>
            </div>
            <!-- Info rows -->
            <div class="border-t" style="border-color: var(--surface-border);">
              <div class="px-5 py-3 flex items-center gap-3">
                <svg class="w-4 h-4 text-gray-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span class="text-xs" style="color: var(--text-muted);">Email</span>
                <span class="text-xs ml-auto font-mono" style="color: var(--text-primary);">{{ auth.user?.email ?? 'â€”' }}</span>
              </div>
              <div class="px-5 py-3 flex items-center gap-3 border-t" style="border-color: var(--surface-border);">
                <svg class="w-4 h-4 text-gray-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span class="text-xs" style="color: var(--text-muted);">Username</span>
                <span class="text-xs ml-auto font-mono" style="color: var(--text-primary);">{{ auth.user?.username ?? 'â€”' }}</span>
              </div>
            </div>
            <!-- Sign out -->
            <div class="px-5 py-4 border-t" style="border-color: var(--surface-border);">
              <button
                class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-red-400 border border-red-500/20 bg-red-500/5 hover:bg-red-500/10 transition-colors"
                @click="auth.logout"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Sign out
              </button>
            </div>
          </div>
        </div>

      </div><!-- end right panel -->
    </div><!-- end flex layout -->
  </div>
</template>
