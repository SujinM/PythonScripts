<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useMarketStore } from '@/stores/marketStore'
import { CHART_COLORS } from '@/utils/constants'
import { formatNumber } from '@/utils/formatters'
import ChartCard from '@/components/charts/ChartCard.vue'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const market = useMarketStore()
onMounted(() => market.fetchStatistics())

const stats = computed(() => market.statistics)

const assetTypePie = computed(() =>
  stats.value
    ? Object.entries(stats.value.assetTypeBreakdown).map(([name, value]) => ({ name, value }))
    : [],
)

const exchangeBar = computed(() => ({
  categories: stats.value ? Object.keys(stats.value.exchangeBreakdown) : [],
  values: stats.value ? Object.values(stats.value.exchangeBreakdown) : [],
}))
</script>

<template>
  <div class="space-y-5 animate-fade-in">
    <div>
      <h2 class="text-xl font-bold" style="color: var(--text-primary);">Statistics</h2>
      <p class="text-sm mt-0.5" style="color: var(--text-muted);">Detailed breakdown of financial instruments</p>
    </div>

    <div v-if="market.loading && !stats" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" />
    </div>

    <template v-else>
      <!-- Summary row -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div
          v-for="([type, count], i) in Object.entries(stats?.assetTypeBreakdown ?? {})"
          :key="type"
          class="card p-4 text-center"
        >
          <p
            class="text-2xl font-bold stat-value"
            :style="{ color: CHART_COLORS[i % CHART_COLORS.length] }"
          >
            {{ formatNumber(count) }}
          </p>
          <p class="text-xs mt-1" style="color: var(--text-muted);">{{ type }}</p>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Asset Type Distribution" subtitle="Instruments per asset class">
          <PieChart v-if="assetTypePie.length" :data="assetTypePie" height="300px" legend-position="bottom" />
        </ChartCard>

        <ChartCard title="Exchange Distribution" subtitle="Instruments per exchange">
          <BarChart
            v-if="exchangeBar.categories.length"
            :categories="exchangeBar.categories"
            :values="exchangeBar.values"
            :color="CHART_COLORS[2]"
            :horizontal="true"
            height="300px"
          />
        </ChartCard>
      </div>

      <!-- Top exchanges table -->
      <div class="card overflow-hidden">
        <div class="px-4 py-3 border-b" style="border-color: var(--surface-border);">
          <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Exchange Breakdown</h3>
        </div>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b" style="border-color: var(--surface-border); background-color: var(--surface-secondary);">
              <th class="px-4 py-2.5 text-left text-xs uppercase tracking-wide" style="color: var(--text-muted);">Exchange</th>
              <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Count</th>
              <th class="px-4 py-2.5 text-right text-xs uppercase tracking-wide" style="color: var(--text-muted);">Share</th>
              <th class="px-4 py-2.5"></th>
            </tr>
          </thead>
          <tbody class="divide-y" style="border-color: var(--surface-border);">
            <tr
              v-for="([exchange, count], i) in Object.entries(stats?.exchangeBreakdown ?? {})"
              :key="exchange"
            >
              <td class="px-4 py-3 font-medium text-xs" style="color: var(--text-primary);">{{ exchange }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs" style="color: var(--text-secondary);">{{ formatNumber(count) }}</td>
              <td class="px-4 py-3 text-right text-xs" style="color: var(--text-muted);">
                {{ stats ? ((count / stats.totalInstruments) * 100).toFixed(1) : 0 }}%
              </td>
              <td class="px-4 py-3 w-32">
                <div class="h-1.5 rounded-full overflow-hidden" style="background-color: var(--surface-border);">
                  <div
                    class="h-full rounded-full"
                    :style="{
                      width: (stats ? (count / stats.totalInstruments) * 100 : 0) + '%',
                      backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
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
