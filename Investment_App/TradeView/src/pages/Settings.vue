<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settingsStore'
import { useAuthStore } from '@/stores/authStore'
import { useNotification } from '@/composables/useNotification'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import Badge from '@/components/common/Badge.vue'
import { upstoxAuthApi } from '@/api/upstoxAuth'

const REFRESH_INTERVAL_OPTIONS = [
  { label: '15 seconds', value: 15_000 },
  { label: '30 seconds', value: 30_000 },
  { label: '1 minute',   value: 60_000 },
  { label: '5 minutes',  value: 300_000 },
]

const settings = useSettingsStore()
const auth     = useAuthStore()
const notify   = useNotification()

function removeFromWatchlist(symbol: string) {
  settings.removeFromWatchlist(symbol)
  notify.info(`Removed ${symbol} from watchlist`)
}

// ── Upstox authentication ─────────────────────────────────────────────────────

const upstoxStatus = ref<{ configured: boolean; token_preview: string | null }>({
  configured: false,
  token_preview: null,
})
const upstoxAuthUrl  = ref<string | null>(null)
const upstoxCode     = ref('')
const upstoxLoading  = ref(false)
const upstoxStep     = ref<'idle' | 'awaiting-code'>('idle')

async function fetchUpstoxStatus() {
  try {
    upstoxStatus.value = await upstoxAuthApi.getStatus()
  } catch {
    // Backend may not be running — ignore silently
  }
}

async function startUpstoxAuth() {
  upstoxLoading.value = true
  try {
    const { url } = await upstoxAuthApi.getAuthUrl()
    upstoxAuthUrl.value = url
    window.open(url, '_blank', 'noopener,noreferrer')
    upstoxStep.value = 'awaiting-code'
  } catch (err: any) {
    notify.error(err?.response?.data?.detail ?? 'Failed to get Upstox auth URL')
  } finally {
    upstoxLoading.value = false
  }
}

async function submitUpstoxCode() {
  if (!upstoxCode.value.trim()) {
    notify.error('Please paste the authorization code first.')
    return
  }
  upstoxLoading.value = true
  try {
    const result = await upstoxAuthApi.submitCode(upstoxCode.value.trim())
    notify.success(result.message)
    upstoxStatus.value = { configured: true, token_preview: result.token_preview }
    upstoxStep.value = 'idle'
    upstoxCode.value = ''
    upstoxAuthUrl.value = null
  } catch (err: any) {
    notify.error(err?.response?.data?.detail ?? 'Token exchange failed')
  } finally {
    upstoxLoading.value = false
  }
}

function cancelUpstoxAuth() {
  upstoxStep.value = 'idle'
  upstoxCode.value = ''
  upstoxAuthUrl.value = null
}

onMounted(fetchUpstoxStatus)
</script>

<template>
  <div class="space-y-5 max-w-2xl animate-fade-in">
    <div>
      <h2 class="text-xl font-bold" style="color: var(--text-primary);">Settings</h2>
      <p class="text-sm mt-0.5" style="color: var(--text-muted);">Manage your preferences and account</p>
    </div>

    <!-- Appearance -->
    <div class="card p-5 space-y-4">
      <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Appearance</h3>
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm" style="color: var(--text-primary);">Dark Mode</p>
          <p class="text-xs mt-0.5" style="color: var(--text-muted);">Bloomberg-style dark interface</p>
        </div>
        <ThemeToggle />
      </div>
    </div>

    <!-- Auto refresh -->
    <div class="card p-5 space-y-4">
      <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Data Refresh</h3>
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm" style="color: var(--text-primary);">Auto Refresh</p>
          <p class="text-xs mt-0.5" style="color: var(--text-muted);">Automatically update market data</p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            class="sr-only peer"
            :checked="settings.autoRefresh"
            @change="settings.autoRefresh = !settings.autoRefresh"
          />
          <div class="w-11 h-6 rounded-full peer-checked:bg-brand-500 bg-gray-600 peer-focus:ring-2 peer-focus:ring-brand-500/30 after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5"></div>
        </label>
      </div>
      <div v-if="settings.autoRefresh" class="flex items-center gap-3">
        <p class="text-xs" style="color: var(--text-muted);">Refresh interval:</p>
        <select class="input text-xs w-auto" v-model="settings.refreshInterval">
          <option v-for="opt in REFRESH_INTERVAL_OPTIONS" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
      </div>
    </div>

    <!-- Watchlist -->
    <div class="card p-5 space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Watchlist</h3>
        <span class="text-xs" style="color: var(--text-muted);">{{ settings.watchlist.length }} symbols</span>
      </div>
      <div v-if="settings.watchlist.length === 0" class="text-xs py-4 text-center" style="color: var(--text-muted);">
        Your watchlist is empty. Add instruments from the instrument detail page.
      </div>
      <div v-else class="flex flex-wrap gap-2">
        <div
          v-for="symbol in settings.watchlist"
          :key="symbol"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono border"
          style="border-color: var(--surface-border); color: var(--text-primary);"
        >
          <span class="text-brand-400">{{ symbol }}</span>
          <button
            class="text-gray-500 hover:text-red-400 transition-colors ml-1"
            @click="removeFromWatchlist(symbol)"
          >
            ✕
          </button>
        </div>
      </div>
      <button
        v-if="settings.watchlist.length > 0"
        class="btn-ghost text-xs text-red-400 hover:text-red-300"
        @click="settings.clearWatchlist()"
      >
        Clear all
      </button>
    </div>

    <!-- Upstox Authentication -->
    <div class="card p-5 space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Upstox Authentication</h3>
        <span
          class="text-xs px-2 py-0.5 rounded-full font-medium"
          :class="upstoxStatus.configured
            ? 'bg-green-500/15 text-green-400'
            : 'bg-yellow-500/15 text-yellow-400'"
        >
          {{ upstoxStatus.configured ? 'Connected' : 'Not connected' }}
        </span>
      </div>

      <!-- Status row -->
      <div v-if="upstoxStatus.configured" class="flex items-center gap-2 text-xs" style="color: var(--text-muted);">
        <svg class="w-3.5 h-3.5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        Access token active
        <span class="font-mono text-brand-400">{{ upstoxStatus.token_preview }}</span>
      </div>
      <p v-else class="text-xs" style="color: var(--text-muted);">
        Connect your Upstox account to enable live portfolio data.
      </p>

      <!-- Step 1: trigger OAuth -->
      <div v-if="upstoxStep === 'idle'" class="flex gap-2">
        <button
          class="btn-primary text-xs px-4 py-1.5 flex items-center gap-1.5"
          :disabled="upstoxLoading"
          @click="startUpstoxAuth"
        >
          <svg v-if="upstoxLoading" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          {{ upstoxStatus.configured ? 'Re-authenticate' : 'Connect Upstox' }}
        </button>
      </div>

      <!-- Step 2: paste the code -->
      <div v-if="upstoxStep === 'awaiting-code'" class="space-y-3">
        <p class="text-xs" style="color: var(--text-muted);">
          A browser tab opened with the Upstox login page. After authorising, copy the
          <span class="font-mono text-brand-400">code</span> from the redirect URL and paste it below.
        </p>
        <div v-if="upstoxAuthUrl" class="text-xs break-all" style="color: var(--text-muted);">
          <span class="font-medium" style="color: var(--text-primary);">Auth URL: </span>
          <a :href="upstoxAuthUrl" target="_blank" rel="noopener noreferrer" class="text-brand-400 underline">
            Open again
          </a>
        </div>
        <input
          v-model="upstoxCode"
          type="text"
          class="input text-xs w-full font-mono"
          placeholder="Paste authorization code here…"
          @keyup.enter="submitUpstoxCode"
        />
        <div class="flex gap-2">
          <button
            class="btn-primary text-xs px-4 py-1.5 flex items-center gap-1.5"
            :disabled="upstoxLoading || !upstoxCode.trim()"
            @click="submitUpstoxCode"
          >
            <svg v-if="upstoxLoading" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            Submit Code
          </button>
          <button class="btn-ghost text-xs" @click="cancelUpstoxAuth">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Account -->
    <div class="card p-5 space-y-4">
      <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Account</h3>
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400 font-bold">
          {{ auth.user?.username?.charAt(0)?.toUpperCase() ?? 'U' }}
        </div>
        <div>
          <p class="text-sm font-medium" style="color: var(--text-primary);">{{ auth.user?.firstName && auth.user?.lastName ? `${auth.user.firstName} ${auth.user.lastName}` : auth.user?.username ?? 'Unknown' }}</p>
          <p class="text-xs" style="color: var(--text-muted);">{{ auth.user?.email }}</p>
        </div>
        <Badge :value="auth.user?.role ?? 'user'" type="assetType" class="ml-auto" />
      </div>
      <button class="btn-ghost text-xs text-red-400 hover:text-red-300" @click="auth.logout">
        Sign out
      </button>
    </div>
  </div>
</template>
