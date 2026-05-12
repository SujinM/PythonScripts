<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useMarketStore } from '@/stores/marketStore'
import { useSettingsStore } from '@/stores/settingsStore'
import { formatNumber, timeAgo } from '@/utils/formatters'
import { CHART_COLORS } from '@/utils/constants'
import StatisticCard from '@/components/dashboard/StatisticCard.vue'
import MarketSummaryCard from '@/components/dashboard/MarketSummaryCard.vue'
import RecentInstruments from '@/components/dashboard/RecentInstruments.vue'
import TopSymbols from '@/components/dashboard/TopSymbols.vue'
import ChartCard from '@/components/charts/ChartCard.vue'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import LineChart from '@/components/charts/LineChart.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import type { EChartsOption } from 'echarts'

const market   = useMarketStore()
const settings = useSettingsStore()

onMounted(async () => {
  await market.fetchStatistics()
})

const stats = computed(() => market.statistics)
const loading = computed(() => market.loading)

// Chart: instruments by asset type (pie)
const assetTypePieData = computed(() =>
  stats.value
    ? Object.entries(stats.value.assetTypeBreakdown).map(([name, value]) => ({ name, value }))
    : [],
)

// Chart: instruments by exchange (bar)
const exchangeBarData = computed(() => ({
  categories: stats.value ? Object.keys(stats.value.exchangeBreakdown) : [],
  values: stats.value ? Object.values(stats.value.exchangeBreakdown) : [],
}))

// Chart: mock monthly growth line
const monthlyGrowth = computed(() => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const base = 580
  let cur = base
  const data = months.map(() => {
    cur += Math.floor(Math.random() * 30 + 5)
    return cur
  })
  return { categories: months, data }
})
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header row -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold" style="color: var(--text-primary);">Overview</h2>
        <p class="text-sm mt-0.5" style="color: var(--text-muted);">
          Last sync: {{ stats ? timeAgo(stats.lastSyncAt) : '—' }}
        </p>
      </div>
      <div v-if="loading" class="flex items-center gap-2 text-xs" style="color: var(--text-muted);">
        <LoadingSpinner size="sm" />
        <span>Loading…</span>
      </div>
    </div>

    <!-- KPI cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatisticCard
        label="Total Instruments"
        :value="stats ? formatNumber(stats.totalInstruments) : '—'"
        icon="instruments"
        subValue="across all exchanges"
        accent="#3b82f6"
        :loading="loading"
      />
      <StatisticCard
        label="Exchanges"
        :value="stats ? formatNumber(stats.totalExchanges) : '—'"
        icon="exchanges"
        subValue="active markets"
        accent="#8b5cf6"
        :loading="loading"
      />
      <StatisticCard
        label="Tradable"
        :value="stats ? formatNumber(stats.totalTradable) : '—'"
        icon="tradable"
        trend="up"
        trendValue="+12 today"
        accent="#22c55e"
        :loading="loading"
      />
      <StatisticCard
        label="Last Synced"
        :value="stats ? timeAgo(stats.lastSyncAt) : '—'"
        icon="sync"
        subValue="instruments updated"
        accent="#f59e0b"
        :loading="loading"
      />
    </div>

    <!-- Charts row 1 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Asset type pie -->
      <ChartCard title="Instruments by Asset Type" subtitle="Distribution across all categories">
        <PieChart
          v-if="assetTypePieData.length"
          :data="assetTypePieData"
          height="260px"
        />
        <div v-else class="h-[260px] flex items-center justify-center">
          <LoadingSpinner />
        </div>
      </ChartCard>

      <!-- Exchange bar -->
      <ChartCard title="Instruments by Exchange" subtitle="Top exchanges by instrument count">
        <BarChart
          v-if="exchangeBarData.categories.length"
          :categories="exchangeBarData.categories"
          :values="exchangeBarData.values"
          :color="CHART_COLORS[1]"
          height="260px"
        />
        <div v-else class="h-[260px] flex items-center justify-center">
          <LoadingSpinner />
        </div>
      </ChartCard>
    </div>

    <!-- Charts row 2 -->
    <div class="grid grid-cols-1 gap-4">
      <ChartCard title="Instrument Growth" subtitle="Total instruments tracked over the year">
        <LineChart
          :categories="monthlyGrowth.categories"
          :series="[{ name: 'Instruments', data: monthlyGrowth.data, areaStyle: true }]"
          height="200px"
        />
      </ChartCard>
    </div>

    <!-- Tables row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <RecentInstruments :instruments="stats?.recentlyUpdated ?? []" :loading="loading" />
      <TopSymbols :symbols="stats?.topActiveSymbols ?? []" :loading="loading" />
    </div>

    <!-- Market summary cards (top active symbols) -->
    <div>
      <h3 class="text-sm font-semibold mb-3" style="color: var(--text-primary);">Market Snapshot</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
        <MarketSummaryCard
          v-for="item in (stats?.topActiveSymbols ?? []).slice(0, 10)"
          :key="item.symbol"
          :data="item"
        />
      </div>
    </div>
  </div>
</template>
