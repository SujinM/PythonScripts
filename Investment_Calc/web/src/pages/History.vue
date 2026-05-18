<script setup lang="ts">
import { useHistoryStore } from '@/stores/historyStore'
import { computed } from 'vue'

const history = useHistoryStore()
const entries = computed(() => history.entries)

function fmt(v: number | string): string {
  if (typeof v === 'number') {
    return Math.abs(v) >= 1000
      ? v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })
      : v.toFixed(4)
  }
  return String(v)
}

function relTime(ts: number): string {
  const d = Date.now() - ts
  if (d < 60_000)  return 'just now'
  if (d < 3_600_000) return `${Math.floor(d / 60_000)}m ago`
  if (d < 86_400_000) return `${Math.floor(d / 3_600_000)}h ago`
  return new Date(ts).toLocaleDateString()
}

const catColor: Record<string, string> = {
  Price:    'text-blue-400 bg-blue-500/10 border-blue-500/20',
  Returns:  'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  Risk:     'text-orange-400 bg-orange-500/10 border-orange-500/20',
  Position: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
  Options:  'text-rose-400 bg-rose-500/10 border-rose-500/20',
}
</script>

<template>
  <div class="space-y-6 max-w-4xl">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-[var(--text-primary)]">Calculation History</h2>
        <p class="text-sm text-[var(--text-secondary)] mt-0.5">Last {{ entries.length }} calculations (persisted locally)</p>
      </div>
      <button v-if="entries.length" @click="history.clear()"
        class="text-sm text-red-400 hover:text-red-300 border border-red-500/30 hover:border-red-400/50 px-3 py-1.5 rounded-lg transition-colors">
        Clear All
      </button>
    </div>

    <div v-if="!entries.length" class="card p-12 text-center text-[var(--text-muted)]">
      No calculations saved yet. Use any calculator and the results will appear here.
    </div>

    <div v-else class="card divide-y divide-[var(--surface-border)]">
      <div
        v-for="entry in entries" :key="entry.id"
        class="px-5 py-4 hover:bg-white/[0.02] transition-colors"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex items-center gap-3 flex-wrap">
            <span :class="['badge border text-xs', catColor[entry.category] ?? 'text-gray-400']">
              {{ entry.category }}
            </span>
            <span class="text-sm font-medium text-[var(--text-primary)]">{{ entry.label }}</span>
          </div>
          <span class="text-xs text-[var(--text-muted)] flex-shrink-0">{{ relTime(entry.timestamp) }}</span>
        </div>

        <div class="mt-2 flex flex-wrap gap-x-6 gap-y-1">
          <div v-for="(v, k) in entry.results" :key="k" class="flex items-center gap-1.5">
            <span class="text-xs text-[var(--text-muted)]">{{ k }}</span>
            <span
              class="stat-value text-xs"
              :class="typeof v === 'number' && v < 0 ? 'text-loss' : 'text-[var(--text-primary)]'"
            >{{ fmt(v) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
