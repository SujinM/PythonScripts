<script setup lang="ts">
import { formatPrice, formatChange, changeColor, changeArrow } from '@/utils/formatters'
import type { MarketData } from '@/types/market'

defineProps<{ data: MarketData }>()
</script>

<template>
  <div
    class="card p-4 hover:border-brand-500/30 transition-colors cursor-pointer group"
  >
    <div class="flex items-start justify-between mb-2">
      <div>
        <p class="text-sm font-bold" style="color: var(--text-primary);">{{ data.symbol }}</p>
        <p class="text-xs" style="color: var(--text-muted);">24h change</p>
      </div>
      <span
        :class="['text-xs font-semibold px-2 py-0.5 rounded-full', data.changePercent >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400']"
      >
        {{ changeArrow(data.changePercent) }} {{ formatChange(data.changePercent) }}
      </span>
    </div>

    <p class="text-lg font-bold stat-value" style="color: var(--text-primary);">
      {{ formatPrice(data.price) }}
    </p>

    <div class="flex items-center justify-between mt-2 text-xs" style="color: var(--text-muted);">
      <span>H: {{ formatPrice(data.high24h) }}</span>
      <span>L: {{ formatPrice(data.low24h) }}</span>
    </div>

    <!-- Thin progress bar showing range position -->
    <div class="mt-2 h-0.5 rounded-full overflow-hidden" style="background-color: var(--surface-border);">
      <div
        class="h-full rounded-full"
        :class="data.changePercent >= 0 ? 'bg-emerald-500' : 'bg-red-500'"
        :style="{
          width: Math.min(100, Math.max(5,
            ((data.price - data.low24h) / Math.max(data.high24h - data.low24h, 0.0001)) * 100
          )) + '%'
        }"
      />
    </div>
  </div>
</template>
