<script setup lang="ts">
import { computed } from 'vue'
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

const option = computed((): EChartsOption => {
  const isDark = settings.theme === 'dark'
  const textColor  = isDark ? '#94a3b8' : '#64748b'
  const gridColor  = isDark ? '#1e2340' : '#e2e8f0'
  const labelColor = isDark ? '#e2e8f0' : '#1e293b'

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? '#141827' : '#ffffff',
      borderColor: isDark ? '#1e2340' : '#e2e8f0',
      textStyle: { color: labelColor, fontSize: 12 },
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
      data: props.categories,
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
      name: s.name,
      type: 'line',
      smooth: s.smooth !== false,
      data: s.data,
      symbol: 'none',
      lineStyle: { width: 2, color: s.color ?? CHART_COLORS[i % CHART_COLORS.length] },
      itemStyle: { color: s.color ?? CHART_COLORS[i % CHART_COLORS.length] },
      areaStyle: s.areaStyle
        ? { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: (s.color ?? CHART_COLORS[i % CHART_COLORS.length]) + '40' }, { offset: 1, color: 'transparent' }] } }
        : undefined,
    })),
  }
})
</script>

<template>
  <VChart :option="option" :style="{ height, width: '100%' }" :theme="settings.theme" autoresize />
</template>
