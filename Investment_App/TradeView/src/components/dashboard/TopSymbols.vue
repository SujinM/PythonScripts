<script setup lang="ts">
import { useRouter } from 'vue-router'
import { formatPrice, formatChange } from '@/utils/formatters'
import type { MarketData } from '@/types/market'

const props = defineProps<{ symbols: MarketData[]; loading?: boolean }>()
const router = useRouter()
</script>

<template>
  <div class="card overflow-hidden">
    <div class="px-4 py-3 border-b flex items-center justify-between" style="border-color: var(--surface-border);">
      <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Top Active Symbols</h3>
    </div>

    <div class="divide-y" style="border-color: var(--surface-border);">
      <div
        v-for="(item, i) in symbols.slice(0, 8)"
        :key="item.symbol"
        class="px-4 py-3 flex items-center justify-between hover:bg-white/3 cursor-pointer transition-colors"
        @click="router.push({ name: 'instrument-detail', params: { symbol: item.symbol } })"
      >
        <div class="flex items-center gap-3">
          <span class="text-xs font-mono w-4 text-gray-600 text-right">{{ i + 1 }}</span>
          <span class="text-sm font-semibold" style="color: var(--text-primary);">{{ item.symbol }}</span>
        </div>
        <div class="flex items-center gap-4 text-xs font-mono">
          <span style="color: var(--text-secondary);">{{ formatPrice(item.price) }}</span>
          <span :class="item.changePercent >= 0 ? 'text-profit' : 'text-loss'" class="w-16 text-right">
            {{ formatChange(item.changePercent) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
