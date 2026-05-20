<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useHistoryStore } from '@/stores/historyStore'
import { computed } from 'vue'

const history = useHistoryStore()
const recent  = computed(() => history.entries.slice(0, 5))

const categories = [
  { name: 'Price',     to: '/price',    desc: 'Diff, % change, SL, TP, Pivot, SMA',      color: 'text-blue-400',    bg: 'bg-blue-500/10 border-blue-500/20' },
  { name: 'Returns',   to: '/returns',  desc: 'P&L, CAGR, ROI, Dividend Yield, CI',       color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  { name: 'Risk',      to: '/risk',     desc: 'Position size, R/R, Sharpe, Volatility',   color: 'text-orange-400',  bg: 'bg-orange-500/10 border-orange-500/20' },
  { name: 'Position',  to: '/position', desc: 'Avg buy, Allocation, Lot size, P&L',       color: 'text-violet-400',  bg: 'bg-violet-500/10 border-violet-500/20' },
  { name: 'Options',   to: '/options',  desc: 'Intrinsic value, Black-Scholes, Greeks',   color: 'text-rose-400',    bg: 'bg-rose-500/10 border-rose-500/20' },  { name: 'Percent',   to: '/percent', desc: 'Value % up / down — instant result',        color: 'text-cyan-400',    bg: 'bg-cyan-500/10 border-cyan-500/20' },]

function fmt(v: number | string): string {
  if (typeof v === 'number') return Math.abs(v) >= 1000 ? v.toLocaleString() : v.toFixed(4)
  return String(v)
}
</script>

<template>
  <div class="space-y-8 max-w-5xl">
    <!-- Header -->
    <div>
      <h2 class="text-2xl font-bold text-[var(--text-primary)]">Stock Market Calculator</h2>
      <p class="mt-1 text-sm text-[var(--text-secondary)]">
        Professional calculations for price analysis, risk management, position sizing and options.
      </p>
    </div>

    <!-- Category Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <RouterLink
        v-for="cat in categories" :key="cat.name" :to="cat.to"
        :class="['card p-5 border hover:scale-[1.01] transition-transform cursor-pointer', cat.bg]"
      >
        <p :class="['text-lg font-bold mb-1', cat.color]">{{ cat.name }}</p>
        <p class="text-xs text-[var(--text-secondary)]">{{ cat.desc }}</p>
      </RouterLink>
    </div>

    <!-- Recent calculations -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-widest">
          Recent Calculations
        </h3>
        <button
          v-if="recent.length"
          @click="history.clear()"
          class="text-xs text-[var(--text-muted)] hover:text-red-400 transition-colors"
        >Clear</button>
      </div>

      <div v-if="!recent.length" class="card p-6 text-center text-sm text-[var(--text-muted)]">
        No calculations yet. Pick a category above to start.
      </div>

      <div v-else class="card divide-y divide-[var(--surface-border)]">
        <div
          v-for="entry in recent" :key="entry.id"
          class="flex items-center justify-between px-5 py-3 hover:bg-white/[0.02] transition-colors"
        >
          <div>
            <span class="text-xs font-medium text-brand-400">{{ entry.category }}</span>
            <span class="mx-2 text-[var(--text-muted)]">›</span>
            <span class="text-sm text-[var(--text-primary)]">{{ entry.label }}</span>
          </div>
          <div class="text-right">
            <span
              v-for="(v, k) in entry.results" :key="k"
              class="stat-value text-xs ml-4"
              :class="typeof v === 'number' && v < 0 ? 'text-loss' : 'text-profit'"
            >
              {{ k }}: {{ fmt(v) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
