<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useSettingsStore } from '@/stores/settingsStore'
import { formatShortDate } from '@/utils/formatters'
import type { Candle } from '@/types/market'
import type { EChartsOption } from 'echarts'

interface Props {
  candles: Candle[]
  symbol?: string
  height?: string
  showVolume?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  showVolume: true,
})

const settings = useSettingsStore()
const hoverHtml = ref('')

// Direct ref to ECharts instance for data-only updates (preserves tooltip).
const chartRef = ref<{ setOption: (opt: unknown, notMerge?: boolean, lazyUpdate?: boolean) => void } | null>(null)

// Style-only option — does NOT depend on props.candles.
const option = computed((): EChartsOption => {
  const isDark = settings.theme === 'dark'
  const textColor   = isDark ? '#94a3b8' : '#64748b'
  const gridColor   = isDark ? '#1e2340' : '#e2e8f0'
  const labelColor  = isDark ? '#e2e8f0' : '#1e293b'
  const bgColor     = isDark ? '#141827' : '#ffffff'
  const borderColor = isDark ? '#1e2340' : '#e2e8f0'
  const upColor     = '#22c55e'
  const downColor   = '#ef4444'

  const grids = props.showVolume
    ? [{ left: '2%', right: '2%', top: '2%', bottom: '28%', containLabel: true },
       { left: '2%', right: '2%', top: '75%', bottom: '6%', containLabel: true }]
    : [{ left: '2%', right: '2%', top: '2%', bottom: '8%', containLabel: true }]

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      showContent: true,
      axisPointer: { type: 'cross' },
      backgroundColor: bgColor,
      borderColor,
      textStyle: { color: labelColor, fontSize: 11 },
      formatter: (params: any) => {
        const items = Array.isArray(params) ? params : [params]
        const candle = items.find((item: any) => item.seriesType === 'candlestick')
        const volume = items.find((item: any) => item.seriesName === 'Volume')
        const values = Array.isArray(candle?.value) ? candle.value : []
        const html = [
          candle?.axisValueLabel ?? candle?.name ?? '',
          values.length >= 4 ? `Open: ${values[0]}` : '',
          values.length >= 4 ? `Close: ${values[1]}` : '',
          values.length >= 4 ? `Low: ${values[2]}` : '',
          values.length >= 4 ? `High: ${values[3]}` : '',
          volume ? `Volume: ${volume.value}` : '',
        ].filter(Boolean).join('<br/>')
        hoverHtml.value = html
        return html
      },
    },
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      { type: 'slider',  xAxisIndex: [0, 1], start: 50, end: 100, height: 18, bottom: 0, textStyle: { color: textColor, fontSize: 10 } },
    ],
    grid: grids,
    xAxis: [
      {
        type: 'category', boundaryGap: true,
        axisLine: { lineStyle: { color: gridColor } },
        axisLabel: { color: textColor, fontSize: 10 },
        splitLine: { show: false },
      },
      ...(props.showVolume
        ? [{ type: 'category' as const, gridIndex: 1, axisLabel: { show: false }, axisLine: { lineStyle: { color: gridColor } }, splitLine: { show: false } }]
        : []),
    ],
    yAxis: [
      {
        scale: true,
        axisLabel: { color: textColor, fontSize: 10 },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: gridColor, type: 'dashed' } },
      },
      ...(props.showVolume
        ? [{ scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { color: textColor, fontSize: 10 }, axisLine: { show: false }, splitLine: { show: false } }]
        : []),
    ],
    series: [
      {
        id: 'price-series',
        name: props.symbol ?? 'Price',
        type: 'candlestick',
        itemStyle: {
          color: upColor,
          color0: downColor,
          borderColor: upColor,
          borderColor0: downColor,
        },
      },
      ...(props.showVolume
        ? [{
            id: 'volume-series',
            name: 'Volume',
            type: 'bar' as const,
            xAxisIndex: 1,
            yAxisIndex: 1,
          }]
        : []),
    ],
  }
})

function _dates() {
  return props.candles.map((candle) => formatShortDate(candle.timestamp))
}

function _setHoverByIndex(index: number) {
  if (index < 0 || index >= props.candles.length) {
    hoverHtml.value = ''
    return
  }
  const candle = props.candles[index]
  const dates = _dates()
  if (!candle) return
  hoverHtml.value = [
    dates[index],
    `Open: ${candle.open}`,
    `Close: ${candle.close}`,
    `Low: ${candle.low}`,
    `High: ${candle.high}`,
    props.showVolume ? `Volume: ${candle.volume}` : '',
  ].filter(Boolean).join('<br/>')
}

function _xValueFromPixel(chart: any, x: number, y: number) {
  const rawValue = chart?.convertFromPixel?.({ xAxisIndex: 0 }, [x, y])
  return Array.isArray(rawValue) ? rawValue[0] : rawValue
}

// Populate data on mount then watch for subsequent changes.
function _pushData(candles: Candle[]) {
  if (!chartRef.value) return
  const upColor   = '#22c55e'
  const downColor = '#ef4444'
  const dates    = candles.map((c) => formatShortDate(c.timestamp))
  const ohlcData = candles.map((c) => [c.open, c.close, c.low, c.high])
  const volumes  = candles.map((c) => c.volume)
  const seriesUpdate: unknown[] = [
    { id: 'price-series', name: props.symbol ?? 'Price', type: 'candlestick', data: ohlcData },
    ...(props.showVolume
      ? [{
          id: 'volume-series',
          name: 'Volume',
          type: 'bar',
          data: volumes,
          itemStyle: {
            color: (params: { dataIndex: number }) => {
              const c = candles[params.dataIndex]
              return c.close >= c.open ? upColor + '80' : downColor + '80'
            },
          },
        }]
      : []),
  ]
  const c = chartRef.value as any
  c.setOption({
    xAxis: [{ data: dates }, ...(props.showVolume ? [{ data: dates }] : [])],
    series: seriesUpdate,
  }, false, false)
  if (_zrPos) {
    c.dispatchAction({ type: 'showTip', x: _zrPos[0], y: _zrPos[1] })
    _onZrMove({ zrX: _zrPos[0], zrY: _zrPos[1] })
  }
}

// Zrender-level mouse tracking for hover label updates.
let _zrPos: [number, number] | null = null
const _onZrMove = (e: any) => {
  _zrPos = [e.zrX, e.zrY]
  const chart = chartRef.value as any
  const axisValue = _xValueFromPixel(chart, e.zrX, e.zrY)
  const dates = _dates()
  const index = typeof axisValue === 'number'
    ? Math.round(axisValue)
    : dates.findIndex((date) => String(date) === String(axisValue))
  _setHoverByIndex(index)
}
const _onZrOut  = () => {
  _zrPos = null
  hoverHtml.value = ''
}

onMounted(() => nextTick(() => {
  const chart = chartRef.value as any
  const zr = chart?.getZr?.()
  if (zr) { zr.on('mousemove', _onZrMove); zr.on('globalout', _onZrOut) }
  _pushData(props.candles)
}))

onUnmounted(() => {
  const chart = chartRef.value as any
  const zr = chart?.getZr?.()
  if (zr) { zr.off('mousemove', _onZrMove); zr.off('globalout', _onZrOut) }
})

watch(() => props.candles, (candles) => _pushData(candles), { flush: 'post' })
</script>

<template>
  <div class="relative">
    <div
      v-if="hoverHtml"
      class="absolute right-3 top-3 z-10 max-w-[70%] rounded-lg border px-3 py-2 text-xs leading-5 shadow-sm pointer-events-none"
      :style="{
        backgroundColor: settings.theme === 'dark' ? '#141827f2' : '#fffffff2',
        borderColor: settings.theme === 'dark' ? '#1e2340' : '#e2e8f0',
        color: settings.theme === 'dark' ? '#e2e8f0' : '#1e293b',
      }"
      v-html="hoverHtml"
    />
    <VChart ref="chartRef" :option="option" :style="{ height, width: '100%' }" :theme="settings.theme" autoresize />
  </div>
</template>
