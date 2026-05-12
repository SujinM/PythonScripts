<script setup lang="ts">
import { useSettingsStore } from '@/stores/settingsStore'
import { useAuthStore } from '@/stores/authStore'
import { useNotification } from '@/composables/useNotification'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import Badge from '@/components/common/Badge.vue'
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

    <!-- Account -->
    <div class="card p-5 space-y-4">
      <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Account</h3>
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400 font-bold">
          {{ auth.user?.name?.charAt(0) ?? 'U' }}
        </div>
        <div>
          <p class="text-sm font-medium" style="color: var(--text-primary);">{{ auth.user?.name ?? 'Unknown' }}</p>
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
