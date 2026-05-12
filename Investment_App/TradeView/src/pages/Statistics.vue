<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { usePortfolioStore } from '@/stores/portfolioStore'
import { CHART_COLORS } from '@/utils/constants'
import { formatCurrency, formatPercent, formatNumber } from '@/utils/formatters'
import ChartCard from '@/components/charts/ChartCard.vue'
import BarChart from '@/components/charts/BarChart.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const portfolio = usePortfolioStore()

onMounted(() => {
  portfolio.fetchAnalysis()
  portfolio.fetchAlerts()
})

const analysis = computed(() => portfolio.activeAnalysis)
const alerts   = computed(() => portfolio.activeAlerts)

const gainersBar = computed(() => ({
  categories: (analysis.value?.top_gainers ?? []).map((h) => h.trading_symbol),
  values: (analysis.value?.top_gainers ?? []).map((h) => h.return_pct),
}))

const losersBar = computed(() => ({
  categories: (analysis.value?.top_losers ?? []).map((h) => h.trading_symbol),
  values: (analysis.value?.top_losers ?? []).map((h) => h.return_pct),
}))

function alertSeverityClass(severity?: string): string {
  if (severity === 'high') return 'text-red-400 bg-red-500/10'
  if (severity === 'medium') return 'text-amber-400 bg-amber-500/10'
  return 'text-blue-400 bg-blue-500/10'
}
</script>

<template>
  <div class="space-y-5 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold" style="color: var(--text-primary);">Portfolio Analysis</h2>
        <p class="text-sm mt-0.5" style="color: var(--text-muted);">
          {{ portfolio.activeBroker.toUpperCase() }} — full analysis &amp; alerts
        </p>
      </div>
      <button class="btn-secondary text-xs" @click="portfolio.fetchAnalysis()">Refresh</button>
    </div>

    <div v-if="portfolio.loading && !analysis" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" />
    </div>

    <template v-else>
      <!-- Summary KPI row -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold" style="color: #3b82f6;">{{ formatNumber(analysis?.holdings_count ?? 0) }}</p>
          <p class="text-xs mt-1" style="color: var(--text-muted);">Holdings</p>
        </div>
        <div class="card p-4 text-center">
          <p class="text-lg font-bold font-mono" style="color: #8b5cf6;">{{ analysis ? formatCurrency(analysis.total_invested) : '—' }}</p>
          <p class="text-xs mt-1" style="color: var(--text-muted);">Invested</p>
        </div>
        <div class="card p-4 text-center">
          <p class="text-lg font-bold font-mono" style="color: #f59e0b;">{{ analysis ? formatCurrency(analysis.total_current_value) : '—' }}</p>
          <p class="text-xs mt-1" style="color: var(--text-muted);">Current Value</p>
        </div>
        <div class="card p-4 text-center">
          <p
            class="text-lg font-bold font-mono"
            :style="{ color: (analysis?.total_pnl ?? 0) >= 0 ? '#22c55e' : '#ef4444' }"
          >{{ analysis ? formatCurrency(analysis.total_pnl) : '—' }}</p>
          <p class="text-xs mt-1" style="color: var(--text-muted);">Total P&amp;L</p>
        </div>
        <div class="card p-4 text-center">
          <p
            class="text-2xl font-bold"
            :style="{ color: (analysis?.overall_return_pct ?? 0) >= 0 ? '#22c55e' : '#ef4444' }"
          >{{ analysis ? formatPercent(analysis.overall_return_pct) : '—' }}</p>
          <p class="text-xs mt-1" style="color: var(--text-muted);">Return</p>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Top Gainers" subtitle="Return % of best performing holdings">
          <BarChart
            v-if="gainersBar.categories.length"
            :categories="gainersBar.categories"
            :values="gainersBar.values"
            :color="CHART_COLORS[2]"
            height="260px"
          />
          <div v-else class="h-[260px] flex items-center justify-center text-sm" style="color: var(--text-muted);">No data</div>
        </ChartCard>

        <ChartCard title="Top Losers" subtitle="Return % of worst performing holdings">
          <BarChart
            v-if="losersBar.categories.length"
            :categories="losersBar.categories"
            :values="losersBar.values"
            :color="CHART_COLORS[6]"
            height="260px"
          />
          <div v-else class="h-[260px] flex items-center justify-center text-sm" style="color: var(--text-muted);">No data</div>
        </ChartCard>
      </div>

      <!-- Alerts -->
      <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b flex items-center justify-between" style="border-color: var(--surface-border);">
          <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Alerts</h3>
          <span class="text-xs px-2 py-0.5 rounded-full" style="background-color: var(--surface-secondary); color: var(--text-muted);">
            {{ alerts.length }}
          </span>
        </div>
        <div class="divide-y" style="border-color: var(--surface-border);">
          <div
            v-for="(alert, i) in alerts"
            :key="i"
            class="px-4 py-3 flex items-start gap-3"
          >
            <span
              :class="['text-xs font-semibold px-2 py-0.5 rounded flex-shrink-0', alertSeverityClass(alert.severity)]"
            >{{ alert.type }}</span>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-mono font-semibold" style="color: var(--text-primary);">{{ alert.symbol }}</p>
              <p class="text-xs mt-0.5" style="color: var(--text-muted);">{{ alert.message }}</p>
            </div>
          </div>
          <div v-if="alerts.length === 0" class="px-4 py-8 text-center text-sm" style="color: var(--text-muted);">
            No alerts — portfolio looks healthy
          </div>
        </div>
      </div>

      <!-- Holdings P&L table -->
      <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b" style="border-color: var(--surface-border);">
          <h3 class="text-sm font-semibold" style="color: var(--text-primary);">All Holdings Performance</h3>
        </div>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b" style="border-color: var(--surface-border); background-color: var(--surface-secondary);">
              <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Symbol</th>
              <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Invested</th>
              <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Current</th>
              <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">P&amp;L</th>
              <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Return%</th>
              <th class="px-4 py-2.5 w-28"></th>
            </tr>
          </thead>
          <tbody class="divide-y" style="border-color: var(--surface-border);">
            <tr
              v-for="h in portfolio.activeHoldings"
              :key="h.instrument_key"
              class="hover:bg-white/5 transition-colors"
            >
              <td class="px-4 py-3 font-mono text-xs font-semibold" style="color: var(--text-primary);">{{ h.trading_symbol }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">{{ formatCurrency(h.invested_value) }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">{{ formatCurrency(h.current_value) }}</td>
              <td
                class="px-4 py-3 text-right font-mono text-xs font-semibold"
                :class="h.unrealised_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'"
              >{{ formatCurrency(h.unrealised_pnl) }}</td>
              <td
                class="px-4 py-3 text-right font-mono text-xs"
                :class="h.return_pct >= 0 ? 'text-emerald-400' : 'text-red-400'"
              >{{ formatPercent(h.return_pct) }}</td>
              <td class="px-4 py-3 w-28">
                <div class="h-1.5 rounded-full overflow-hidden" style="background-color: var(--surface-border);">
                  <div
                    class="h-full rounded-full"
                    :style="{
                      width: Math.min(Math.abs(h.return_pct) * 2, 100) + '%',
                      backgroundColor: h.return_pct >= 0 ? '#22c55e' : '#ef4444',
                    }"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
