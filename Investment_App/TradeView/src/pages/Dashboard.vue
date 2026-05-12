<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { usePortfolioStore } from '@/stores/portfolioStore'
import { formatCurrency, formatPercent, formatNumber } from '@/utils/formatters'
import { CHART_COLORS } from '@/utils/constants'
import StatisticCard from '@/components/dashboard/StatisticCard.vue'
import ChartCard from '@/components/charts/ChartCard.vue'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const portfolio = usePortfolioStore()
const currency = computed(() => portfolio.activeBroker === 'etoro' ? 'USD' : 'INR')
const fmt = (v: number) => formatCurrency(v, currency.value)

onMounted(async () => {
  await portfolio.fetchBrokers()
  await Promise.all([
    portfolio.fetchSummary(),
    portfolio.fetchHoldings(),
  ])
})

watch(() => portfolio.activeBroker, async () => {
  await Promise.all([
    portfolio.fetchSummary(),
    portfolio.fetchHoldings(),
  ])
})

const summary = computed(() => portfolio.activeSummary)
const loading = computed(() => portfolio.loading)

// Chart: top gainers vs losers (bar)
const gainersBar = computed(() => ({
  categories: (summary.value?.top_gainers ?? []).map((h) => h.trading_symbol),
  values: (summary.value?.top_gainers ?? []).map((h) => h.return_pct),
}))

const losersBar = computed(() => ({
  categories: (summary.value?.top_losers ?? []).map((h) => h.trading_symbol),
  values: (summary.value?.top_losers ?? []).map((h) => Math.abs(h.return_pct)),
}))

// Chart: holdings breakdown by exchange (pie)
const exchangePieData = computed(() => {
  const map: Record<string, number> = {}
  for (const h of portfolio.activeHoldings) {
    map[h.exchange || 'UNKNOWN'] = (map[h.exchange || 'UNKNOWN'] ?? 0) + h.current_value
  }
  return Object.entries(map).map(([name, value]) => ({ name, value: Math.round(value) }))
})
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header row -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold" style="color: var(--text-primary);">Portfolio Overview</h2>
        <p class="text-sm mt-0.5" style="color: var(--text-muted);">
          {{ portfolio.activeBroker.toUpperCase() }} — {{ summary ? formatNumber(summary.holdings_count) + ' holdings' : 'Loading…' }}
        </p>
      </div>
      <div class="flex items-center gap-3">
        <!-- Broker selector -->
        <select
          class="input text-sm"
          :value="portfolio.activeBroker"
          @change="portfolio.selectBroker(($event.target as HTMLSelectElement).value)"
        >
          <option v-for="b in portfolio.brokers" :key="b.id" :value="b.id">
            {{ b.name ?? b.id }}
          </option>
        </select>
        <div v-if="loading" class="flex items-center gap-2 text-xs" style="color: var(--text-muted);">
          <LoadingSpinner size="sm" />
        </div>
      </div>
    </div>

    <!-- KPI cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatisticCard
        label="Total Invested"
        :value="summary ? fmt(summary.total_invested) : '—'"
        icon="instruments"
        subValue="across all holdings"
        accent="#3b82f6"
        :loading="loading"
      />
      <StatisticCard
        label="Current Value"
        :value="summary ? fmt(summary.total_current_value) : '—'"
        icon="exchanges"
        subValue="mark-to-market"
        accent="#8b5cf6"
        :loading="loading"
      />
      <StatisticCard
        label="Unrealised P&L"
        :value="summary ? fmt(summary.total_unrealised_pnl) : '—'"
        icon="tradable"
        :trend="summary && summary.total_unrealised_pnl >= 0 ? 'up' : 'down'"
        :trendValue="summary ? formatPercent(summary.overall_return_pct) : ''"
        accent="#22c55e"
        :loading="loading"
      />
      <StatisticCard
        label="Overall Return"
        :value="summary ? formatPercent(summary.overall_return_pct) : '—'"
        icon="sync"
        subValue="since inception"
        accent="#f59e0b"
        :loading="loading"
      />
    </div>

    <!-- Charts row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Holdings by exchange (pie) -->
      <ChartCard title="Holdings by Exchange" subtitle="Current value distribution">
        <PieChart
          v-if="exchangePieData.length"
          :data="exchangePieData"
          height="260px"
        />
        <div v-else class="h-[260px] flex items-center justify-center">
          <LoadingSpinner />
        </div>
      </ChartCard>

      <!-- Top gainers (bar) -->
      <ChartCard title="Top Gainers" subtitle="Best performing holdings (return %)">
        <BarChart
          v-if="gainersBar.categories.length"
          :categories="gainersBar.categories"
          :values="gainersBar.values"
          :color="CHART_COLORS[2]"
          height="260px"
        />
        <div v-else class="h-[260px] flex items-center justify-center">
          <LoadingSpinner />
        </div>
      </ChartCard>
    </div>

    <!-- Top gainers / losers tables -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">

      <!-- Gainers -->
      <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b" style="border-color: var(--surface-border);">
          <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Top Gainers</h3>
        </div>
        <table class="w-full text-sm">
          <tbody class="divide-y" style="border-color: var(--surface-border);">
            <tr v-for="h in (summary?.top_gainers ?? [])" :key="h.instrument_key" class="hover:bg-white/5 transition-colors">
              <td class="px-4 py-3 font-mono text-xs font-semibold" style="color: var(--text-primary);">{{ h.trading_symbol }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">{{ fmt(h.current_value) }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs font-semibold text-emerald-400">{{ formatPercent(h.return_pct) }}</td>
            </tr>
            <tr v-if="!(summary?.top_gainers?.length)">
              <td colspan="3" class="px-4 py-6 text-center text-xs" style="color: var(--text-muted);">No data</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Losers -->
      <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b" style="border-color: var(--surface-border);">
          <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Top Losers</h3>
        </div>
        <table class="w-full text-sm">
          <tbody class="divide-y" style="border-color: var(--surface-border);">
            <tr v-for="h in (summary?.top_losers ?? [])" :key="h.instrument_key" class="hover:bg-white/5 transition-colors">
              <td class="px-4 py-3 font-mono text-xs font-semibold" style="color: var(--text-primary);">{{ h.trading_symbol }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">{{ fmt(h.current_value) }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs font-semibold text-red-400">{{ formatPercent(h.return_pct) }}</td>
            </tr>
            <tr v-if="!(summary?.top_losers?.length)">
              <td colspan="3" class="px-4 py-6 text-center text-xs" style="color: var(--text-muted);">No data</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>
