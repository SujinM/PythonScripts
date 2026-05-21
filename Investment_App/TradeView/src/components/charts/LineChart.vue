<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useSettingsStore } from '@/stores/settingsStore'
import { CHART_COLORS } from '@/utils/constants'
import type { EChartsOption } from 'echarts'

interface Series {
  name: string
  data: number[]
  color?: string
  smooth?: boolean
  areaStyle?: boolean
}

interface Props {
  categories: string[]
  series: Series[]
  title?: string
  height?: string
  showDataZoom?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '280px',
  showDataZoom: false,
})

const settings = useSettingsStore()
const hoverHtml = ref('')

// Direct ref to ECharts instance for data-only updates (preserves tooltip).
const chartRef = ref<{ setOption: (opt: unknown, notMerge?: boolean, lazyUpdate?: boolean) => void } | null>(null)

// Style-only option — does NOT depend on props.categories or props.series data.
const option = computed((): EChartsOption => {
  const isDark = settings.theme === 'dark'
  const textColor  = isDark ? '#94a3b8' : '#64748b'
  const gridColor  = isDark ? '#1e2340' : '#e2e8f0'
  const labelColor = isDark ? '#e2e8f0' : '#1e293b'

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      showContent: true,

      backgroundColor: isDark ? '#141827' : '#ffffff',
      borderColor: isDark ? '#1e2340' : '#e2e8f0',
      textStyle: { color: labelColor, fontSize: 12 },
      formatter: (params: any) => {
        const items = Array.isArray(params) ? params : [params]
        const title = items[0]?.axisValueLabel ?? items[0]?.name ?? ''
        const lines = items.map((item: any) => `${item.marker}${item.seriesName}: ${item.value}`)
        const html = [title, ...lines].filter(Boolean).join('<br/>')
        hoverHtml.value = html
        return html
      },
    },
    legend: props.series.length > 1
      ? { textStyle: { color: textColor, fontSize: 11 }, top: 0 }
      : { show: false },
    grid: {
      left: '2%',
      right: '2%',
      bottom: props.showDataZoom ? '14%' : '8%',
      top: props.series.length > 1 ? '12%' : '4%',
      containLabel: true,
    },
    dataZoom: props.showDataZoom
      ? [{ type: 'inside', start: 60, end: 100 }, { type: 'slider', start: 60, end: 100, height: 20, bottom: 0, textStyle: { color: textColor } }]
      : [],
    xAxis: {
      type: 'category',
      axisLine: { lineStyle: { color: gridColor } },
      axisLabel: { color: textColor, fontSize: 10 },
      splitLine: { show: false },
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: textColor, fontSize: 11 },
      splitLine: { lineStyle: { color: gridColor, type: 'dashed' } },
    },
    series: props.series.map((s, i) => ({
      id: s.name,
      name: s.name,
      type: 'line',
      smooth: s.smooth !== false,
      symbol: 'none',
      lineStyle: { width: 2, color: s.color ?? CHART_COLORS[i % CHART_COLORS.length] },
      itemStyle: { color: s.color ?? CHART_COLORS[i % CHART_COLORS.length] },
      areaStyle: s.areaStyle
        ? { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: (s.color ?? CHART_COLORS[i % CHART_COLORS.length]) + '40' }, { offset: 1, color: 'transparent' }] } }
        : undefined,
    })),
  }
})

// Zrender-level mouse tracking so we can re-dispatch showTip after each
// data update — hover label is computed directly from chart pixels.
let _zrPos: [number, number] | null = null
function _setHoverByIndex(index: number) {
  if (index < 0 || index >= props.categories.length) {
    hoverHtml.value = ''
    return
  }
  const title = props.categories[index] ?? ''
  const lines = props.series.map((series, seriesIndex) => {
    const color = series.color ?? CHART_COLORS[seriesIndex % CHART_COLORS.length]
    return `<span style="display:inline-block;margin-right:6px;border-radius:9999px;width:8px;height:8px;background:${color}"></span>${series.name}: ${series.data[index] ?? ''}`
  })
  hoverHtml.value = [title, ...lines].filter(Boolean).join('<br/>')
}

function _xValueFromPixel(chart: any, x: number, y: number) {
  const rawValue = chart?.convertFromPixel?.({ xAxisIndex: 0 }, [x, y])
  return Array.isArray(rawValue) ? rawValue[0] : rawValue
}

const _onZrMove = (e: any) => {
  _zrPos = [e.zrX, e.zrY]
  const chart = chartRef.value as any
  const axisValue = _xValueFromPixel(chart, e.zrX, e.zrY)
  const index = typeof axisValue === 'number'
    ? Math.round(axisValue)
    : props.categories.findIndex((category) => String(category) === String(axisValue))
  _setHoverByIndex(index)
}
const _onZrOut  = () => {
  _zrPos = null
  hoverHtml.value = ''
}

function _pushData(cats: string[], series: typeof props.series) {
  const c = chartRef.value as any
  if (!c) return
  c.setOption({
    xAxis: { data: cats },
    series: series.map((s) => ({ id: s.name, name: s.name, type: 'line', data: s.data })),
  }, false, false)
  if (_zrPos) {
    c.dispatchAction({ type: 'showTip', x: _zrPos[0], y: _zrPos[1] })
    _onZrMove({ zrX: _zrPos[0], zrY: _zrPos[1] })
  }
}

onMounted(() => nextTick(() => {
  const chart = chartRef.value as any
  const zr = chart?.getZr?.()
  if (zr) { zr.on('mousemove', _onZrMove); zr.on('globalout', _onZrOut) }
  _pushData(props.categories, props.series)
}))

onUnmounted(() => {
  const chart = chartRef.value as any
  const zr = chart?.getZr?.()
  if (zr) { zr.off('mousemove', _onZrMove); zr.off('globalout', _onZrOut) }
})

watch(
  [() => props.categories, () => props.series],
  ([cats, series]) => _pushData(cats, series as typeof props.series),
  { deep: true, flush: 'post' },
)
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
