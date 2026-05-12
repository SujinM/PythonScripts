<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import Sidebar from '@/components/layout/Sidebar.vue'
import Navbar from '@/components/layout/Navbar.vue'

// Ensure auto-refresh starts on layout mount
import { useMarketStore } from '@/stores/marketStore'
import { useSettingsStore } from '@/stores/settingsStore'
import { REFRESH_INTERVALS } from '@/utils/constants'

const market   = useMarketStore()
const settings = useSettingsStore()

let refreshTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await market.fetchStatistics()
  await market.fetchBulkMarketData()

  if (settings.autoRefresh) {
    refreshTimer = setInterval(() => {
      market.fetchBulkMarketData()
    }, REFRESH_INTERVALS.MARKET_DATA)
  }
})
</script>

<template>
  <div class="flex h-screen overflow-hidden" style="background-color: var(--surface-primary);">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Main content area -->
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <Navbar />

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto p-4 sm:p-6">
        <RouterView v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
