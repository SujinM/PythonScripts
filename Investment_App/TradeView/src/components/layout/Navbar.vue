<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useSettingsStore } from '@/stores/settingsStore'
import { useMarketStore } from '@/stores/marketStore'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import SearchBar from '@/components/common/SearchBar.vue'

const route    = useRoute()
const router   = useRouter()
const auth     = useAuthStore()
const settings = useSettingsStore()
const market   = useMarketStore()

const showUserMenu = ref(false)

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    'dashboard':         'Dashboard',
    'instruments':       'Instruments',
    'instrument-detail': 'Instrument Detail',
    'statistics':        'Statistics',
    'sync':              'Sync Management',
    'settings':          'Settings',
  }
  return map[String(route.name)] ?? 'eToro Dashboard'
})

async function handleLogout() {
  showUserMenu.value = false
  await auth.logout()
  router.push('/login')
}

function handleSearch(query: string) {
  if (query.trim()) {
    router.push({ name: 'instruments', query: { search: query } })
  }
}
</script>

<template>
  <header
    class="sticky top-0 z-30 flex items-center gap-4 px-4 h-16 border-b"
    style="background-color: var(--surface-card); border-color: var(--surface-border);"
  >
    <!-- Mobile sidebar toggle -->
    <button
      class="lg:hidden p-1.5 rounded-md text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors"
      @click="settings.toggleSidebar"
    >
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>

    <!-- Page title -->
    <h1 class="text-base font-semibold hidden sm:block" style="color: var(--text-primary);">
      {{ pageTitle }}
    </h1>

    <!-- Search -->
    <div class="flex-1 max-w-md ml-2 hidden md:block">
      <SearchBar placeholder="Search instruments…" @search="handleSearch" />
    </div>

    <div class="ml-auto flex items-center gap-2">
      <!-- Market refresh indicator -->
      <div class="hidden sm:flex items-center gap-1.5 text-xs text-gray-500">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
        <span>Live</span>
      </div>

      <!-- Theme toggle -->
      <ThemeToggle />

      <!-- Refresh market data -->
      <button
        class="p-1.5 rounded-md text-gray-500 hover:text-white hover:bg-white/5 transition-colors"
        title="Refresh market data"
        @click="market.refreshAll"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>

      <!-- User avatar + dropdown -->
      <div class="relative">
        <button
          class="flex items-center gap-2 p-1 rounded-lg hover:bg-white/5 transition-colors"
          @click="showUserMenu = !showUserMenu"
        >
          <div class="w-7 h-7 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center">
            <span class="text-white text-xs font-bold">A</span>
          </div>
          <span class="hidden sm:block text-xs font-medium" style="color: var(--text-secondary);">
            {{ auth.user?.username ?? 'analyst' }}
          </span>
        </button>

        <!-- Dropdown -->
        <Transition
          enter-active-class="transition ease-out duration-100"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition ease-in duration-75"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="showUserMenu"
            v-click-outside="() => (showUserMenu = false)"
            class="absolute right-0 mt-1 w-40 rounded-lg shadow-xl border z-50 py-1"
            style="background-color: var(--surface-card); border-color: var(--surface-border);"
          >
            <router-link
              to="/settings"
              class="flex items-center gap-2 px-3 py-2 text-sm hover:bg-white/5 transition-colors"
              style="color: var(--text-secondary);"
              @click="showUserMenu = false"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Settings
            </router-link>
            <hr class="my-1" style="border-color: var(--surface-border);" />
            <button
              class="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
              @click="handleLogout"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sign out
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>
