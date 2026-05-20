<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settingsStore'
import { useNotification } from '@/composables/useNotification'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { upstoxHistoricalApi } from '@/api/upstoxHistorical'
import {
  TIMEFRAME_PRESETS,
  DEFAULT_RANGE_DAYS,
  type UpstoxCandleBar,
  type IntervalOption,
  type HistoricalUnit,
} from '@/types/upstoxHistorical'
import type { EChartsOption } from 'echarts'

// ── Route / init ──────────────────────────────────────────────────────────────
const route  = useRoute()
const router = useRouter()

// instrument_key can contain '|', passed URL-decoded from router params
const instrumentKey = computed(() => decodeURIComponent(route.params.instrumentKey as string))
const instrumentName = computed(() => (route.query.name as string | undefined) ?? instrumentKey.value)

// ── State ─────────────────────────────────────────────────────────────────────
const settings   = useSettingsStore()
const notify     = useNotification()
const candles    = ref<UpstoxCandleBar[]>([])
const loading    = ref(false)
const error      = ref<string | null>(null)

// Timeframe
const selectedPreset = ref<IntervalOption>(TIMEFRAME_PRESETS.find(p => p.label === '1D')!)

// Date range
function today(): string {
  return new Date().toISOString().slice(0, 10)
}
function daysAgo(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

const toDate   = ref(today())
const fromDate = ref(daysAgo(DEFAULT_RANGE_DAYS[selectedPreset.value.unit]))

// ── Fetch ──────────────────────────────────────────────────────────────────────
async function fetchCandles() {
  if (!instrumentKey.value) return
  loading.value = true
  error.value   = null
  try {
    const resp = await upstoxHistoricalApi.getCandles({
      instrumentKey: instrumentKey.value,
      unit:          selectedPreset.value.unit,
      interval:      selectedPreset.value.interval,
      toDate:        toDate.value,
      fromDate:      fromDate.value || undefined,
    })
    candles.value = resp.candles
    if (candles.value.length === 0) {
      notify.info('No candle data returned for the selected range.')
    }
  } catch (err: any) {
    const msg = err?.response?.data?.detail ?? err?.message ?? 'Failed to fetch historical data'
    error.value = msg
    notify.error(msg)
  } finally {
    loading.value = false
  }
}

// When preset changes, auto-adjust from_date
function selectPreset(preset: IntervalOption) {
  selectedPreset.value = preset
  fromDate.value = daysAgo(DEFAULT_RANGE_DAYS[preset.unit])
  toDate.value   = today()
}

watch(selectedPreset, fetchCandles)
onMounted(fetchCandles)

// ── Stats ──────────────────────────────────────────────────────────────────────
const stats = computed(() => {
  if (!candles.value.length) return null
  const last   = candles.value[candles.value.length - 1]
  const first  = candles.value[0]
  const allHigh  = candles.value.map(c => c.high)
  const allLow   = candles.value.map(c => c.low)
  const change   = last.close - first.open
  const changePct = (change / first.open) * 100
  return {
    open:      first.open,
    close:     last.close,
    high:      Math.max(...allHigh),
    low:       Math.min(...allLow),
    volume:    candles.value.reduce((s, c) => s + c.volume, 0),
    change,
    changePct,
    candles:   candles.value.length,
  }
})

// ── ECharts option ─────────────────────────────────────────────────────────────
const chartOption = computed((): EChartsOption => {
  const isDark      = settings.theme === 'dark'
  const textColor   = isDark ? '#94a3b8' : '#64748b'
  const gridColor   = isDark ? '#1e2340' : '#e2e8f0'
  const labelColor  = isDark ? '#e2e8f0' : '#1e293b'
  const bgColor     = isDark ? '#141827' : '#ffffff'
  const borderColor = isDark ? '#1e2340' : '#e2e8f0'
  const upColor     = '#22c55e'
  const downColor   = '#ef4444'

  const isIntraday = selectedPreset.value.unit === 'minutes' || selectedPreset.value.unit === 'hours'

  const dates   = candles.value.map(c => {
    const d = new Date(c.timestamp)
    if (isIntraday) {
      return d.toLocaleString('en-IN', {
        month: 'short', day: '2-digit',
        hour: '2-digit', minute: '2-digit', hour12: false,
      })
    }
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  })

  const ohlc    = candles.value.map(c => [c.open, c.close, c.low, c.high])
  const volumes = candles.value.map((c, i) => ({
    value: c.volume,
    itemStyle: { color: c.close >= c.open ? upColor + '99' : downColor + '99' },
  }))

  const ma20 = candles.value.map((_, i) => {
    if (i < 19) return null
    const slice = candles.value.slice(i - 19, i + 1)
    return +(slice.reduce((s, c) => s + c.close, 0) / 20).toFixed(2)
  })
  const ma50 = candles.value.map((_, i) => {
    if (i < 49) return null
    const slice = candles.value.slice(i - 49, i + 1)
    return +(slice.reduce((s, c) => s + c.close, 0) / 50).toFixed(2)
  })

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: bgColor,
      borderColor,
      borderWidth: 1,
      textStyle: { color: labelColor, fontSize: 11 },
      formatter(params: any) {
        const candle = params.find((p: any) => p.seriesName === 'Price')
        const vol    = params.find((p: any) => p.seriesName === 'Volume')
        if (!candle) return ''
        const [o, c, l, h] = candle.value
        const idx   = candle.dataIndex
        const oi    = candles.value[idx]?.oi ?? 0
        const color = c >= o ? upColor : downColor
        return `
          <div style="font-size:11px;line-height:1.7;min-width:160px">
            <div style="color:${textColor};margin-bottom:4px">${candle.axisValue}</div>
            <div><span style="color:${textColor}">O </span><b style="color:${color}">${o.toFixed(2)}</b>
              &nbsp;<span style="color:${textColor}">H </span><b style="color:${color}">${h.toFixed(2)}</b></div>
            <div><span style="color:${textColor}">L </span><b style="color:${color}">${l.toFixed(2)}</b>
              &nbsp;<span style="color:${textColor}">C </span><b style="color:${color}">${c.toFixed(2)}</b></div>
            ${vol ? `<div><span style="color:${textColor}">Vol </span><b style="color:${labelColor}">${Number(vol.value).toLocaleString('en-IN')}</b></div>` : ''}
            ${oi ? `<div><span style="color:${textColor}">OI </span><b style="color:${labelColor}">${Number(oi).toLocaleString('en-IN')}</b></div>` : ''}
          </div>`
      },
    },
    legend: {
      data: ['Price', 'MA 20', 'MA 50'],
      top: 4,
      right: 8,
      textStyle: { color: textColor, fontSize: 10 },
      itemWidth: 14,
    },
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: candles.value.length > 120 ? 70 : 0, end: 100 },
      { type: 'slider',  xAxisIndex: [0, 1], start: candles.value.length > 120 ? 70 : 0, end: 100,
        height: 22, bottom: 4,
        textStyle: { color: textColor, fontSize: 10 },
        borderColor: gridColor, fillerColor: 'rgba(99,102,241,0.08)',
        handleStyle: { color: '#6366f1' },
      },
    ],
    grid: [
      { left: 60, right: 12, top: 36, bottom: 90, containLabel: false },
      { left: 60, right: 12, top: '76%', bottom: 36, containLabel: false },
    ],
    xAxis: [
      {
        type: 'category', data: dates, gridIndex: 0,
        boundaryGap: true,
        axisLine: { lineStyle: { color: gridColor } },
        axisLabel: { show: false },
        splitLine: { show: false },
      },
      {
        type: 'category', data: dates, gridIndex: 1,
        boundaryGap: true,
        axisLine: { lineStyle: { color: gridColor } },
        axisLabel: { color: textColor, fontSize: 9, rotate: isIntraday ? 20 : 0 },
        splitLine: { show: false },
      },
    ],
    yAxis: [
      {
        scale: true, gridIndex: 0,
        position: 'right',
        axisLabel: { color: textColor, fontSize: 10, formatter: (v: number) => v.toFixed(2) },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: gridColor, type: 'dashed' } },
      },
      {
        scale: true, gridIndex: 1,
        splitNumber: 2,
        position: 'right',
        axisLabel: { color: textColor, fontSize: 9, formatter: (v: number) => {
          if (v >= 1e7) return (v / 1e7).toFixed(1) + 'Cr'
          if (v >= 1e5) return (v / 1e5).toFixed(1) + 'L'
          return v.toLocaleString('en-IN')
        }},
        axisLine: { show: false },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: 'Price',
        type: 'candlestick',
        xAxisIndex: 0, yAxisIndex: 0,
        data: ohlc,
        itemStyle: {
          color: upColor,
          color0: downColor,
          borderColor: upColor,
          borderColor0: downColor,
          borderWidth: 1,
        },
        emphasis: { itemStyle: { borderWidth: 2 } },
      },
      {
        name: 'MA 20',
        type: 'line',
        xAxisIndex: 0, yAxisIndex: 0,
        data: ma20,
        smooth: true,
        lineStyle: { color: '#f59e0b', width: 1.2, opacity: 0.85 },
        showSymbol: false,
        z: 10,
      },
      {
        name: 'MA 50',
        type: 'line',
        xAxisIndex: 0, yAxisIndex: 0,
        data: ma50,
        smooth: true,
        lineStyle: { color: '#8b5cf6', width: 1.2, opacity: 0.85 },
        showSymbol: false,
        z: 10,
      },
      {
        name: 'Volume',
        type: 'bar',
        xAxisIndex: 1, yAxisIndex: 1,
        data: volumes,
        barMaxWidth: 8,
      },
    ],
  }
})

// ── Formatters ─────────────────────────────────────────────────────────────────
const fmt = (n: number) => n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fmtVol = (n: number) => {
  if (n >= 1e7) return (n / 1e7).toFixed(2) + ' Cr'
  if (n >= 1e5) return (n / 1e5).toFixed(2) + ' L'
  if (n >= 1000) return (n / 1000).toFixed(1) + ' K'
  return n.toLocaleString('en-IN')
}
</script>

<template>
  <div class="animate-fade-in flex flex-col gap-4 h-full">

    <!-- ── Header ──────────────────────────────────────────────────────────── -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-3 min-w-0">
        <button
          class="p-1.5 rounded-lg border border-gray-700 text-gray-400 hover:text-white hover:bg-gray-800/60 transition-colors flex-shrink-0"
          @click="router.back()"
          title="Go back"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div class="min-w-0">
          <h2 class="text-lg font-bold truncate" style="color: var(--text-primary);">{{ instrumentName }}</h2>
          <p class="text-xs font-mono truncate" style="color: var(--text-muted);">{{ instrumentKey }}</p>
        </div>
      </div>

      <!-- Stat chips -->
      <div v-if="stats" class="flex flex-wrap items-center gap-2 text-xs">
        <span class="px-2 py-1 rounded border" style="border-color: var(--surface-border); color: var(--text-muted);">
          O <span class="font-mono font-semibold" style="color: var(--text-primary);">{{ fmt(stats.open) }}</span>
        </span>
        <span class="px-2 py-1 rounded border" style="border-color: var(--surface-border); color: var(--text-muted);">
          H <span class="font-mono font-semibold text-emerald-400">{{ fmt(stats.high) }}</span>
        </span>
        <span class="px-2 py-1 rounded border" style="border-color: var(--surface-border); color: var(--text-muted);">
          L <span class="font-mono font-semibold text-red-400">{{ fmt(stats.low) }}</span>
        </span>
        <span class="px-2 py-1 rounded border" style="border-color: var(--surface-border); color: var(--text-muted);">
          C <span class="font-mono font-semibold" style="color: var(--text-primary);">{{ fmt(stats.close) }}</span>
        </span>
        <span
          class="px-2 py-1 rounded border font-mono font-semibold"
          :class="stats.change >= 0 ? 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5' : 'text-red-400 border-red-500/20 bg-red-500/5'"
          style="border-color: transparent;"
        >
          {{ stats.change >= 0 ? '+' : '' }}{{ fmt(stats.change) }} ({{ stats.changePct >= 0 ? '+' : '' }}{{ stats.changePct.toFixed(2) }}%)
        </span>
        <span class="px-2 py-1 rounded border" style="border-color: var(--surface-border); color: var(--text-muted);">
          Vol <span class="font-mono font-semibold" style="color: var(--text-primary);">{{ fmtVol(stats.volume) }}</span>
        </span>
      </div>
    </div>

    <!-- ── Toolbar ──────────────────────────────────────────────────────────── -->
    <div class="card px-4 py-3 flex flex-wrap items-center gap-3">

      <!-- Timeframe presets -->
      <div class="flex items-center gap-1 flex-wrap">
        <button
          v-for="preset in TIMEFRAME_PRESETS"
          :key="preset.label"
          :class="[
            'px-2.5 py-1 rounded text-xs font-medium transition-all',
            selectedPreset.label === preset.label
              ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/30'
              : 'text-gray-400 hover:text-white hover:bg-gray-700/60 border border-transparent',
          ]"
          @click="selectPreset(preset)"
        >{{ preset.label }}</button>
      </div>

      <div class="flex-1 border-l pl-3 flex flex-wrap items-center gap-3" style="border-color: var(--surface-border);">
        <!-- From date -->
        <div class="flex items-center gap-1.5 text-xs" style="color: var(--text-muted);">
          <span>From</span>
          <input type="date" class="input text-xs py-1 px-2 w-36" v-model="fromDate" :max="toDate" />
        </div>
        <!-- To date -->
        <div class="flex items-center gap-1.5 text-xs" style="color: var(--text-muted);">
          <span>To</span>
          <input type="date" class="input text-xs py-1 px-2 w-36" v-model="toDate" :max="today()" />
        </div>
        <!-- Apply -->
        <button
          class="btn-primary text-xs px-3 py-1.5 flex items-center gap-1.5"
          :disabled="loading"
          @click="fetchCandles"
        >
          <svg v-if="loading" class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Apply
        </button>
      </div>

      <!-- Candle count badge -->
      <span v-if="candles.length" class="text-xs ml-auto" style="color: var(--text-muted);">
        {{ candles.length.toLocaleString() }} candles
      </span>
    </div>

    <!-- ── Chart area ───────────────────────────────────────────────────────── -->
    <div class="card flex-1 min-h-0 p-3 flex flex-col" style="min-height: 480px;">

      <!-- Loading -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="text-center space-y-3">
          <LoadingSpinner size="lg" />
          <p class="text-xs" style="color: var(--text-muted);">Fetching candle data…</p>
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="flex-1 flex items-center justify-center">
        <div class="text-center space-y-3 max-w-sm">
          <div class="w-12 h-12 mx-auto rounded-xl bg-red-500/10 flex items-center justify-center">
            <svg class="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 9v2m0 4h.01M12 3a9 9 0 100 18A9 9 0 0012 3z" />
            </svg>
          </div>
          <p class="text-sm font-medium text-red-400">Failed to load data</p>
          <p class="text-xs" style="color: var(--text-muted);">{{ error }}</p>
          <button class="btn-primary text-xs px-4 py-1.5" @click="fetchCandles">Retry</button>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="!candles.length" class="flex-1 flex items-center justify-center">
        <div class="text-center space-y-3">
          <svg class="w-12 h-12 mx-auto opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="color: var(--text-muted);">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p class="text-sm" style="color: var(--text-muted);">No data available for this range</p>
          <p class="text-xs" style="color: var(--text-muted);">Try a different timeframe or date range</p>
        </div>
      </div>

      <!-- Chart -->
      <VChart
        v-else
        :option="chartOption"
        autoresize
        class="flex-1"
        style="min-height: 440px;"
      />
    </div>

    <!-- ── Data table (last 20 candles) ────────────────────────────────────── -->
    <div v-if="candles.length" class="card overflow-hidden">
      <div class="px-4 py-3 border-b flex items-center justify-between" style="border-color: var(--surface-border);">
        <h3 class="text-sm font-semibold" style="color: var(--text-primary);">Recent Candles</h3>
        <span class="text-xs" style="color: var(--text-muted);">Last 20 of {{ candles.length.toLocaleString() }}</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b" style="border-color: var(--surface-border); background-color: var(--surface-secondary);">
              <th class="px-3 py-2 text-left font-medium" style="color: var(--text-muted);">Time</th>
              <th class="px-3 py-2 text-right font-medium" style="color: var(--text-muted);">Open</th>
              <th class="px-3 py-2 text-right font-medium" style="color: var(--text-muted);">High</th>
              <th class="px-3 py-2 text-right font-medium" style="color: var(--text-muted);">Low</th>
              <th class="px-3 py-2 text-right font-medium" style="color: var(--text-muted);">Close</th>
              <th class="px-3 py-2 text-right font-medium" style="color: var(--text-muted);">Volume</th>
              <th class="px-3 py-2 text-right font-medium" style="color: var(--text-muted);">Change</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in candles.slice(-20).reverse()"
              :key="c.timestamp"
              class="border-b transition-colors hover:bg-white/2"
              style="border-color: var(--surface-border);"
            >
              <td class="px-3 py-2 font-mono" style="color: var(--text-muted);">
                {{ new Date(c.timestamp).toLocaleString('en-IN', {
                    day: '2-digit', month: 'short',
                    hour: '2-digit', minute: '2-digit', hour12: false,
                  }) }}
              </td>
              <td class="px-3 py-2 text-right font-mono" style="color: var(--text-primary);">{{ fmt(c.open) }}</td>
              <td class="px-3 py-2 text-right font-mono text-emerald-400">{{ fmt(c.high) }}</td>
              <td class="px-3 py-2 text-right font-mono text-red-400">{{ fmt(c.low) }}</td>
              <td
                class="px-3 py-2 text-right font-mono font-semibold"
                :class="c.close >= c.open ? 'text-emerald-400' : 'text-red-400'"
              >{{ fmt(c.close) }}</td>
              <td class="px-3 py-2 text-right font-mono" style="color: var(--text-secondary);">{{ fmtVol(c.volume) }}</td>
              <td
                class="px-3 py-2 text-right font-mono text-xs"
                :class="c.close >= c.open ? 'text-emerald-400' : 'text-red-400'"
              >
                {{ c.close >= c.open ? '+' : '' }}{{ ((c.close - c.open) / c.open * 100).toFixed(2) }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>
