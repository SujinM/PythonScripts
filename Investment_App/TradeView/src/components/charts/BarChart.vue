<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useSettingsStore } from '@/stores/settingsStore'
import { CHART_COLORS } from '@/utils/constants'
import type { EChartsOption } from 'echarts'

interface Props {
  categories: string[]
  values: number[]
  title?: string
  color?: string
  horizontal?: boolean
  height?: string
  formatter?: (v: number) => string
}

const props = withDefaults(defineProps<Props>(), {
  color: CHART_COLORS[0],
  horizontal: false,
  height: '280px',
})

const settings = useSettingsStore()
const hoverHtml = ref('')

// Direct ref to the ECharts instance so data-only updates bypass the full
// option re-render (which would dismiss any open tooltip).
const chartRef = ref<{ setOption: (opt: unknown, notMerge?: boolean, lazyUpdate?: boolean) => void } | null>(null)

// Style-only option — intentionally does NOT read props.categories or
// props.values so it only recomputes when theme / style props change.
const option = computed((): EChartsOption => {
  const isDark = settings.theme === 'dark'
  const textColor  = isDark ? '#94a3b8' : '#64748b'
  const gridColor  = isDark ? '#1e2340' : '#e2e8f0'
  const labelColor = isDark ? '#e2e8f0' : '#1e293b'
  const longestCategory = props.categories.reduce((longest, current) => Math.max(longest, current.length), 0)
  const shouldRotate = !props.horizontal && (props.categories.length > 6 || longestCategory > 8)
  const shortenLabel = (value: string) => value.length > 10 ? `${value.slice(0, 10)}...` : value

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      showContent: true,
      backgroundColor: isDark ? '#141827' : '#ffffff',
      borderColor: isDark ? '#1e2340' : '#e2e8f0',
      textStyle: { color: labelColor, fontSize: 12 },
      enterable: true,
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        const value = props.formatter ? props.formatter(p.value) : p.value
        const html = `${p.name}<br/>${p.marker}${value}`
        hoverHtml.value = html
        return html
      },
    },
    grid: {
      left: props.horizontal ? '12%' : '2%',
      right: '2%',
      bottom: '8%',
      top: props.title ? '12%' : '4%',
      containLabel: true,
    },
    title: props.title
      ? { text: props.title, textStyle: { color: labelColor, fontSize: 13, fontWeight: 600 } }
      : undefined,
    xAxis: props.horizontal
      ? { type: 'value', axisLine: { lineStyle: { color: gridColor } }, axisLabel: { color: textColor, fontSize: 11 }, splitLine: { lineStyle: { color: gridColor } } }
      : {
          type: 'category',
          axisLine: { lineStyle: { color: gridColor } },
          axisLabel: {
            color: textColor,
            fontSize: 11,
            interval: 0,
            rotate: shouldRotate ? 35 : 0,
            hideOverlap: true,
            margin: shouldRotate ? 14 : 8,
            formatter: (value: string) => shortenLabel(String(value)),
          },
          splitLine: { show: false },
        },
    yAxis: props.horizontal
      ? {
          type: 'category',
          axisLine: { lineStyle: { color: gridColor } },
          axisLabel: {
            color: textColor,
            fontSize: 11,
            width: 90,
            overflow: 'truncate',
            formatter: (value: string) => shortenLabel(String(value)),
          },
        }
      : { type: 'value', axisLine: { lineStyle: { color: gridColor } }, axisLabel: { color: textColor, fontSize: 11, ...(props.formatter ? { formatter: (v: number) => props.formatter!(v) } : {}) }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } },
    series: [
      {
        id: 'bar-series',
        name: props.title ?? 'Value',
        type: 'bar',
        itemStyle: {
          color: props.color,
          borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0],
        },
        emphasis: { itemStyle: { opacity: 0.8 } },
      },
    ],
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
  const value = props.values[index]
  const displayValue = props.formatter ? props.formatter(value) : value
  hoverHtml.value = `${props.categories[index]}<br/><span style="display:inline-block;margin-right:6px;border-radius:9999px;width:8px;height:8px;background:${props.color}"></span>${displayValue}`
}

function _axisValueFromPixel(chart: any, x: number, y: number) {
  const finder = props.horizontal ? { yAxisIndex: 0 } : { xAxisIndex: 0 }
  const rawValue = chart?.convertFromPixel?.(finder, [x, y])
  if (!Array.isArray(rawValue)) return rawValue
  return props.horizontal ? rawValue[1] : rawValue[0]
}

const _onZrMove = (e: any) => {
  _zrPos = [e.zrX, e.zrY]
  const chart = chartRef.value as any
  const axisValue = _axisValueFromPixel(chart, e.zrX, e.zrY)
  const index = typeof axisValue === 'number'
    ? Math.round(axisValue)
    : props.categories.findIndex((category) => String(category) === String(axisValue))
  _setHoverByIndex(index)
}
const _onZrOut  = () => {
  _zrPos = null
  hoverHtml.value = ''
}

function _pushData(cats: string[], vals: number[]) {
  const c = chartRef.value as any
  if (!c) return
  const upd: Record<string, unknown> = {
    series: [{ id: 'bar-series', name: props.title ?? 'Value', type: 'bar', data: vals }],
  }
  if (props.horizontal) upd.yAxis = { data: cats }
  else upd.xAxis = { data: cats }
  c.setOption(upd, false, false)
  if (_zrPos) {
    c.dispatchAction({ type: 'showTip', x: _zrPos[0], y: _zrPos[1] })
    _onZrMove({ zrX: _zrPos[0], zrY: _zrPos[1] })
  }
}

onMounted(() => nextTick(() => {
  const chart = chartRef.value as any
  const zr = chart?.getZr?.()
  if (zr) { zr.on('mousemove', _onZrMove); zr.on('globalout', _onZrOut) }
  _pushData(props.categories, props.values)
}))

onUnmounted(() => {
  const chart = chartRef.value as any
  const zr = chart?.getZr?.()
  if (zr) { zr.off('mousemove', _onZrMove); zr.off('globalout', _onZrOut) }
})

watch(
  [() => props.categories, () => props.values],
  ([cats, vals]) => _pushData(cats, vals),
  { flush: 'post' },
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
