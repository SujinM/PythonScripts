<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Badge from '@/components/common/Badge.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import type { Instrument } from '@/types/instrument'

const props = defineProps<{
  instruments: Instrument[]
  loading?: boolean
}>()

const router = useRouter()

function navigate(symbol: string) {
  router.push({ name: 'instrument-detail', params: { symbol } })
}
</script>

<template>
  <div class="card overflow-hidden">
    <div class="px-4 py-3 border-b flex items-center justify-between" style="border-color: var(--surface-border);">
      <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Recently Updated</h3>
      <router-link to="/instruments" class="text-xs text-brand-400 hover:text-brand-300 transition-colors">View all</router-link>
    </div>

    <div v-if="loading" class="p-4 space-y-3">
      <LoadingSkeleton v-for="i in 5" :key="i" height="h-8" />
    </div>

    <div v-else class="divide-y" style="border-color: var(--surface-border);">
      <div
        v-for="inst in instruments.slice(0, 8)"
        :key="inst.instrumentId"
        class="px-4 py-3 flex items-center justify-between hover:bg-white/3 cursor-pointer transition-colors group"
        @click="navigate(inst.symbol)"
      >
        <div class="flex items-center gap-3">
          <!-- Symbol avatar -->
          <div
            class="w-7 h-7 rounded-full bg-brand-500/10 flex items-center justify-center flex-shrink-0 text-brand-400 text-xs font-bold group-hover:bg-brand-500/20 transition-colors"
          >
            {{ inst.symbol.slice(0, 2) }}
          </div>
          <div>
            <p class="text-sm font-medium" style="color: var(--text-primary);">{{ inst.symbol }}</p>
            <p class="text-xs truncate max-w-[140px]" style="color: var(--text-muted);">{{ inst.displayName }}</p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Badge :value="inst.assetType" type="assetType" />
          <svg class="w-3.5 h-3.5 text-gray-600 group-hover:text-brand-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>
