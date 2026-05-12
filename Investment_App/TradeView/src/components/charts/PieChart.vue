<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settingsStore'
import { CHART_COLORS } from '@/utils/constants'
import type { EChartsOption } from 'echarts'

interface PieItem { name: string; value: number }

interface Props {
  data: PieItem[]
  title?: string
  donut?: boolean
  height?: string
  legendPosition?: 'right' | 'bottom'
}

const props = withDefaults(defineProps<Props>(), {
  donut: true,
  height: '280px',
  legendPosition: 'right',
})

const settings = useSettingsStore()

const option = computed((): EChartsOption => {
  const isDark = settings.theme === 'dark'
  const textColor  = isDark ? '#94a3b8' : '#64748b'
  const labelColor = isDark ? '#e2e8f0' : '#1e293b'
  const bgColor    = isDark ? '#141827' : '#ffffff'
  const borderColor = isDark ? '#1e2340' : '#e2e8f0'

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: bgColor,
      borderColor,
      textStyle: { color: labelColor, fontSize: 12 },
    },
    legend: {
      orient: props.legendPosition === 'bottom' ? 'horizontal' : 'vertical',
      [props.legendPosition === 'bottom' ? 'bottom' : 'right']: props.legendPosition === 'bottom' ? 0 : '2%',
      textStyle: { color: textColor, fontSize: 11 },
    },
    series: [
      {
        type: 'pie',
        radius: props.donut ? ['45%', '70%'] : '65%',
        center: props.legendPosition === 'right' ? ['40%', '55%'] : ['50%', '45%'],
        data: props.data.map((d, i) => ({
          ...d,
          itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
        })),
        label: {
          show: false,
        },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' },
          label: { show: true, fontSize: 12, fontWeight: 600, color: labelColor },
        },
      },
    ],
  }
})
</script>

<template>
  <VChart :option="option" :style="{ height, width: '100%' }" :theme="settings.theme" autoresize />
</template>
