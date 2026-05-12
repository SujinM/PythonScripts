<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePortfolioStore } from '@/stores/portfolioStore'
import { useLiveTick } from '@/composables/useLiveTick'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const portfolio = usePortfolioStore()

// Live tick connections per broker
const liveTickMap: Record<string, ReturnType<typeof useLiveTick>> = {}
const liveStatus = ref<Record<string, boolean>>({})

onMounted(async () => {
  await portfolio.fetchBrokers()
})

function getLiveTick(brokerId: string) {
  if (!liveTickMap[brokerId]) {
    liveTickMap[brokerId] = useLiveTick(brokerId)
  }
  return liveTickMap[brokerId]
}

function isLiveConnected(brokerId: string): boolean {
  return getLiveTick(brokerId).isConnected.value
}

function toggleLive(brokerId: string) {
  const tick = getLiveTick(brokerId)
  if (tick.isConnected.value) {
    tick.disconnect()
  } else {
    tick.connect()
  }
}

async function handleInvalidate(brokerId: string) {
  await portfolio.invalidateCache(brokerId)
}
</script>

<template>
  <div class="space-y-5 animate-fade-in">
    <div>
      <h2 class="text-xl font-bold" style="color: var(--text-primary);">Broker Management</h2>
      <p class="text-sm mt-0.5" style="color: var(--text-muted);">
        Manage connected brokers, invalidate caches, and control live data streams
      </p>
    </div>

    <div v-if="portfolio.loading && portfolio.brokers.length === 0" class="flex justify-center py-20">
      <LoadingSpinner size="lg" />
    </div>

    <!-- Broker cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div
        v-for="broker in portfolio.brokers"
        :key="broker.id"
        class="card p-5 space-y-4"
      >
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold uppercase" style="background-color: var(--surface-secondary); color: var(--text-primary);">
              {{ broker.id.slice(0, 2) }}
            </div>
            <div>
              <p class="text-sm font-semibold capitalize" style="color: var(--text-primary);">
                {{ broker.name ?? broker.id }}
              </p>
              <p class="text-xs" style="color: var(--text-muted);">{{ broker.id }}</p>
            </div>
          </div>
          <!-- Active badge -->
          <span
            v-if="portfolio.activeBroker === broker.id"
            class="text-xs px-2 py-0.5 rounded-full text-brand-400 border border-brand-500/30"
          >Active</span>
          <button
            v-else
            class="btn-secondary text-xs"
            @click="portfolio.selectBroker(broker.id)"
          >Select</button>
        </div>

        <!-- Description -->
        <p v-if="broker.description" class="text-xs" style="color: var(--text-muted);">
          {{ broker.description }}
        </p>

        <!-- Actions row -->
        <div class="flex flex-wrap gap-2 pt-1">
          <!-- Invalidate cache -->
          <button
            class="btn-secondary text-xs flex items-center gap-1.5"
            :disabled="portfolio.loading"
            @click="handleInvalidate(broker.id)"
          >
            <LoadingSpinner v-if="portfolio.loading" size="sm" />
            <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Invalidate Cache
          </button>

          <!-- Live toggle -->
          <button
            :class="[
              'text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-colors',
              isLiveConnected(broker.id)
                ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20'
                : 'text-gray-400 border-gray-600 hover:text-white hover:border-gray-400',
            ]"
            @click="toggleLive(broker.id)"
          >
            <span
              :class="['w-1.5 h-1.5 rounded-full', isLiveConnected(broker.id) ? 'bg-emerald-400 animate-pulse' : 'bg-gray-500']"
            />
            {{ isLiveConnected(broker.id) ? 'Live Connected' : 'Connect Live' }}
          </button>
        </div>

        <!-- Live tick preview -->
        <div
          v-if="isLiveConnected(broker.id)"
          class="rounded-lg p-3 font-mono text-xs space-y-1 overflow-y-auto max-h-32"
          style="background-color: var(--surface-secondary);"
        >
          <p style="color: var(--text-muted);">Live ticks — {{ Object.keys(portfolio.liveTicks[broker.id] ?? {}).length }} instruments</p>
          <div
            v-for="(tick, key) in portfolio.liveTicks[broker.id]"
            :key="key"
            class="flex justify-between"
          >
            <span style="color: var(--text-primary);">{{ key }}</span>
            <span class="text-emerald-400">
              {{ 'ltp' in tick ? tick.ltp : ('bid' in tick ? tick.bid : '') }}
            </span>
          </div>
        </div>
      </div>

      <!-- Fallback if no brokers -->
      <div v-if="portfolio.brokers.length === 0 && !portfolio.loading" class="col-span-full card p-10 text-center">
        <p class="text-sm" style="color: var(--text-muted);">No brokers registered — ensure the FastAPI backend is running</p>
      </div>
    </div>
  </div>
</template>
