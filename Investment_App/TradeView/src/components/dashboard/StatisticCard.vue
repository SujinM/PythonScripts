<script setup lang="ts">
interface Props {
  label: string
  value: string | number
  subValue?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  loading?: boolean
  icon?: 'instruments' | 'exchanges' | 'tradable' | 'sync'
  accent?: string
}

withDefaults(defineProps<Props>(), {
  loading: false,
  trend: 'neutral',
  accent: '#3b82f6',
})
</script>

<template>
  <div class="card p-5 flex flex-col gap-3">
    <div class="flex items-start justify-between">
      <p class="text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted);">{{ label }}</p>

      <!-- Icon slot -->
      <div
        class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 opacity-80"
        :style="{ backgroundColor: accent + '20' }"
      >
        <svg class="w-4 h-4" :style="{ color: accent }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path v-if="icon === 'instruments'" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          <path v-else-if="icon === 'exchanges'" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
          <path v-else-if="icon === 'tradable'" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          <path v-else-if="icon === 'sync'" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
    </div>

    <!-- Value -->
    <div v-if="loading" class="space-y-1.5">
      <div class="skeleton h-7 w-24 rounded" />
      <div class="skeleton h-3 w-16 rounded" />
    </div>
    <div v-else>
      <p class="text-2xl font-bold stat-value" style="color: var(--text-primary);">{{ value }}</p>
      <div v-if="trendValue || subValue" class="flex items-center gap-2 mt-1">
        <span
          v-if="trendValue"
          :class="[
            'text-xs font-medium flex items-center gap-0.5',
            trend === 'up' ? 'text-profit' : trend === 'down' ? 'text-loss' : 'text-gray-500',
          ]"
        >
          <svg v-if="trend !== 'neutral'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="trend === 'up' ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'" />
          </svg>
          {{ trendValue }}
        </span>
        <span v-if="subValue" class="text-xs" style="color: var(--text-muted);">{{ subValue }}</span>
      </div>
    </div>
  </div>
</template>
