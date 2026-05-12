<script setup lang="ts">
import { computed } from 'vue'
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
}

const props = withDefaults(defineProps<Props>(), {
  color: CHART_COLORS[0],
  horizontal: false,
  height: '280px',
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
      : { type: 'category', data: props.categories, axisLine: { lineStyle: { color: gridColor } }, axisLabel: { color: textColor, fontSize: 11, rotate: props.categories.length > 8 ? 30 : 0 }, splitLine: { show: false } },
    yAxis: props.horizontal
      ? { type: 'category', data: props.categories, axisLine: { lineStyle: { color: gridColor } }, axisLabel: { color: textColor, fontSize: 11 } }
      : { type: 'value', axisLine: { lineStyle: { color: gridColor } }, axisLabel: { color: textColor, fontSize: 11 }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } },
    series: [
      {
        type: 'bar',
        data: props.values,
        itemStyle: {
          color: props.color,
          borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0],
        },
        emphasis: { itemStyle: { opacity: 0.8 } },
      },
    ],
  }
})
</script>

<template>
  <VChart :option="option" :style="{ height, width: '100%' }" :theme="settings.theme" autoresize />
</template>
