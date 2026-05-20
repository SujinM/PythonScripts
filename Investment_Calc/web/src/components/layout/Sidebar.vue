<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const collapsed = ref(false)
const route = useRoute()

const nav = [
  { name: 'Dashboard',  to: '/',         icon: 'grid' },
  { name: 'Price',      to: '/price',    icon: 'trending-up' },
  { name: 'Returns',    to: '/returns',  icon: 'percent' },
  { name: 'Risk',       to: '/risk',     icon: 'shield' },
  { name: 'Position',   to: '/position', icon: 'layers' },
  { name: 'Options',    to: '/options',  icon: 'activity' },  { name: 'Percent',    to: '/percent',  icon: 'percent-calc' },  { name: 'History',    to: '/history',  icon: 'clock' },
]

function isActive(to: string) {
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}

const icons: Record<string, string> = {
  grid: `<path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/>`,
  'trending-up': `<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>`,
  percent: `<line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>`,
  shield: `<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>`,
  layers: `<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>`,
  activity: `<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>`,
  clock: `<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>`,
  'percent-calc': `<line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/><line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/>`,
}
</script>

<template>
  <aside
    :class="[
      'flex flex-col h-screen transition-all duration-300 z-40 flex-shrink-0',
      'bg-[var(--surface-sidebar)] border-r border-[var(--surface-border)]',
      collapsed ? 'w-16' : 'w-60',
    ]"
  >
    <!-- Brand -->
    <div class="flex items-center gap-3 px-4 h-16 border-b border-[var(--surface-border)] flex-shrink-0">
      <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600 flex-shrink-0 shadow-lg shadow-brand-600/30">
        <span class="text-white font-bold text-xs">IC</span>
      </div>
      <Transition enter-active-class="transition-opacity duration-200" enter-from-class="opacity-0"
                  leave-active-class="transition-opacity duration-100" leave-to-class="opacity-0">
        <span v-if="!collapsed" class="text-white font-bold text-base tracking-tight whitespace-nowrap">
          Invest<span class="text-brand-400">Calc</span>
        </span>
      </Transition>
      <button v-if="!collapsed" @click="collapsed = true"
        class="ml-auto p-1.5 rounded text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
        </svg>
      </button>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
      <RouterLink
        v-for="item in nav" :key="item.name" :to="item.to"
        :title="collapsed ? item.name : undefined"
        :class="[
          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
          isActive(item.to)
            ? 'bg-brand-600/20 text-brand-400 border border-brand-600/30'
            : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/5',
        ]"
      >
        <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
             v-html="icons[item.icon]" />
        <Transition enter-active-class="transition-opacity duration-200" enter-from-class="opacity-0"
                    leave-active-class="transition-opacity duration-100" leave-to-class="opacity-0">
          <span v-if="!collapsed" class="truncate">{{ item.name }}</span>
        </Transition>
      </RouterLink>
    </nav>

    <!-- Expand button when collapsed -->
    <div v-if="collapsed" class="p-2 border-t border-[var(--surface-border)]">
      <button @click="collapsed = false"
        class="w-full p-2 rounded text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors flex justify-center">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7"/>
        </svg>
      </button>
    </div>

    <!-- Version -->
    <div v-if="!collapsed" class="px-4 py-3 border-t border-[var(--surface-border)]">
      <p class="text-xs text-[var(--text-muted)]">InvestCalc v1.0.0</p>
    </div>
  </aside>
</template>
