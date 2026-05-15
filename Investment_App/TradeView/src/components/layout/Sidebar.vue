<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settingsStore'
import { useAuthStore } from '@/stores/authStore'

const settings = useSettingsStore()
const auth = useAuthStore()
const route = useRoute()
const collapsed = computed(() => settings.sidebarCollapsed)
const userInitial = computed(() => (auth.user?.username ?? auth.user?.email ?? 'U')[0].toUpperCase())

interface NavItem {
  name: string
  to: string
  icon: string
}

const navItems: NavItem[] = [
  { name: 'Dashboard',     to: '/',                  icon: 'home' },
  { name: 'Holdings',      to: '/holdings',           icon: 'wallet' },
  { name: 'Instruments',   to: '/instruments',        icon: 'chart-bar' },
  { name: 'Analysis',      to: '/statistics',         icon: 'chart-pie' },
  { name: 'eToro Markets', to: '/etoro-instruments',  icon: 'globe' },
  { name: 'Brokers',       to: '/sync',               icon: 'refresh' },
  { name: 'Settings',      to: '/settings',           icon: 'cog' },
]

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <aside
    :class="[
      'flex flex-col h-screen transition-all duration-300 ease-in-out z-40 flex-shrink-0',
      'bg-gray-950 dark:bg-[#0d0f1a] border-r border-gray-800/60',
      collapsed ? 'w-16' : 'w-64',
    ]"
  >
    <!-- ─── Logo / Brand ───────────────────────────────────────── -->
    <div class="flex items-center gap-3 px-4 h-16 border-b border-gray-800/60">
      <div
        class="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-500 flex-shrink-0 shadow-lg shadow-brand-500/30"
      >
        <span class="text-white font-bold text-xs tracking-tight">IP</span>
      </div>
      <Transition
        enter-active-class="transition-opacity duration-200"
        enter-from-class="opacity-0"
        leave-active-class="transition-opacity duration-100"
        leave-to-class="opacity-0"
      >
        <span v-if="!collapsed" class="text-white font-bold text-lg tracking-tight">
          Investment <span class="text-brand-400">Portfolio</span>
        </span>
      </Transition>

      <!-- Toggle button — desktop -->
      <button
        v-if="!collapsed"
        class="ml-auto p-1.5 rounded-md text-gray-500 hover:text-gray-300 hover:bg-gray-800/60 transition-colors"
        aria-label="Collapse sidebar"
        @click="settings.toggleSidebar"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
    </div>

    <!-- ─── Navigation ─────────────────────────────────────────── -->
    <nav class="flex-1 px-2 py-4 overflow-y-auto overflow-x-hidden space-y-0.5">
      <template v-for="item in navItems" :key="item.name">
        <RouterLink
          :to="item.to"
          :title="collapsed ? item.name : undefined"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group',
            isActive(item.to)
              ? 'bg-brand-500/15 text-brand-400 border border-brand-500/25'
              : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent',
          ]"
        >
          <!-- SVG Icons -->
          <svg v-if="item.icon === 'home'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <svg v-else-if="item.icon === 'wallet'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
          <svg v-else-if="item.icon === 'chart-bar'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <svg v-else-if="item.icon === 'chart-pie'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
          </svg>
          <svg v-else-if="item.icon === 'refresh'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <svg v-else-if="item.icon === 'cog'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <svg v-else-if="item.icon === 'globe'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>

          <Transition
            enter-active-class="transition-opacity duration-200"
            enter-from-class="opacity-0"
            leave-active-class="transition-opacity duration-100"
            leave-to-class="opacity-0"
          >
            <span v-if="!collapsed">{{ item.name }}</span>
          </Transition>
        </RouterLink>
      </template>
    </nav>

    <!-- ─── Expand button (collapsed state) ───────────────────── -->
    <div v-if="collapsed" class="px-2 pb-4">
      <button
        class="w-full flex items-center justify-center p-2 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800/60 transition-colors"
        aria-label="Expand sidebar"
        @click="settings.toggleSidebar"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <!-- ─── User Info ──────────────────────────────────────────── -->
    <div v-if="!collapsed" class="px-3 pb-4 border-t border-gray-800/60 pt-3">
      <div class="flex items-center gap-2 px-2 py-1.5">
        <div class="w-7 h-7 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center flex-shrink-0">
          <span class="text-white text-xs font-bold">{{ userInitial }}</span>
        </div>
        <div class="min-w-0">
          <p class="text-xs font-medium text-gray-200 truncate">{{ auth.user?.email ?? 'admin@local.com' }}</p>
          <p class="text-[10px] text-gray-500 truncate capitalize">{{ auth.user?.role ?? 'user' }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>
